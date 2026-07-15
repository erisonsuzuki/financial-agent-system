import logging
import os
from dataclasses import dataclass
from typing import Any, Optional, cast

import httpx
from dotenv import load_dotenv
from langchain_core.load.load import Reviver

from . import tools, config_loader

load_dotenv()

logger = logging.getLogger(__name__)

PROVIDER_MODEL_ENV = {
    "groq": "MAIN_MODEL",
}


@dataclass(frozen=True)
class AgentInvocationResult:
    answer: str
    tool_names: list[str]


def configure_langgraph_reviver() -> None:
    from langgraph.checkpoint.serde import jsonplus

    jsonplus.LC_REVIVER = Reviver(allowed_objects="core")

def resolve_model_name(provider: str, default_model: Optional[str] = None) -> str:
    env_key = PROVIDER_MODEL_ENV.get(provider)
    if env_key is None:
        raise ValueError(f"Unsupported LLM provider: {provider}")
    model_name = os.getenv(env_key) or default_model
    if not model_name:
        raise ValueError(f"Environment variable '{env_key}' not found and is required for provider '{provider}'.")
    return model_name

def get_llm(llm_config: dict):
    provider = llm_config.get("provider", "").lower()
    model_name = resolve_model_name(provider, llm_config.get("model_name"))
    temperature = llm_config.get("temperature", 0.0)

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=model_name,
            temperature=temperature,
        )
    raise ValueError(f"Unsupported LLM provider: {provider}")

def create_agent_executor(
    agent_name: str,
    config: Optional[dict] = None,
    provider_override: Optional[str] = None,
    model_name_override: Optional[str] = None,
):
    configure_langgraph_reviver()
    from langchain.agents import create_agent

    if config is None:
        config = config_loader.load_config(agent_name)
    
    available_tools = [getattr(tools, tool_name) for tool_name in config.get("tools", [])]

    llm_config = dict(config.get("llm", {}))
    if provider_override:
        provider_override = provider_override.lower()
        llm_config["provider"] = provider_override
        llm_config["model_name"] = resolve_model_name(provider_override, llm_config.get("model_name"))
    if model_name_override:
        llm_config["model_name"] = model_name_override

    llm = get_llm(llm_config)

    logger.info(
        "Agent LLM selected",
        extra={
            "agent_name": agent_name,
            "provider": llm_config.get("provider"),
            "model_name": llm_config.get("model_name"),
        },
    )

    agent = create_agent(
        model=llm,
        tools=available_tools,
        system_prompt=config.get("prompt_template", "You are a helpful assistant."),
        debug=True,
    )

    return agent

def is_transient_llm_error(exc: Exception) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        return status_code == 429 or 500 <= status_code <= 599

    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError, httpx.WriteError)):
        return True

    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None)
    if status_code is not None:
        return status_code == 429 or 500 <= status_code <= 599

    message = str(exc).lower()
    transient_markers = [
        "rate limit",
        "timeout",
        "timed out",
        "connection",
        "temporarily unavailable",
        "service unavailable",
        "gateway",
    ]
    return any(marker in message for marker in transient_markers)

def _build_invocation_result(response: dict[str, Any], allowed_tool_names: set[str]) -> AgentInvocationResult:
    messages = response.get("messages", [])
    if not messages:
        return AgentInvocationResult(answer="Could not process the request.", tool_names=[])

    tool_names = [
        message.name
        for message in messages
        if getattr(message, "type", None) == "tool"
        and isinstance(getattr(message, "name", None), str)
        and message.name in allowed_tool_names
    ]
    return AgentInvocationResult(answer=messages[-1].content, tool_names=tool_names)


def invoke_agent_with_result(agent_name: str, query: str, context: dict | None = None) -> AgentInvocationResult:
    config = config_loader.load_config(agent_name)
    primary_provider = config.get("llm", {}).get("provider", "").lower()
    allowed_tool_names = set(config.get("tools", []))
    agent_executor = create_agent_executor(agent_name, config=config)

    try:
        payload = {"messages": [{"role": "user", "content": query}]}
        if context is not None:
            payload["context"] = context
        response = agent_executor.invoke(payload)
        return _build_invocation_result(response, allowed_tool_names)
    except Exception as exc:
        fallback_model = os.getenv("FALLBACK_MODEL", "").strip()
        primary_model = str(config.get("llm", {}).get("model_name", "")).strip()
        if (
            fallback_model
            and fallback_model != primary_model
            and is_transient_llm_error(exc)
        ):
            fallback_executor = create_agent_executor(
                agent_name,
                config=config,
                provider_override=primary_provider,
                model_name_override=fallback_model,
            )
            payload = {"messages": [{"role": "user", "content": query}]}
            if context is not None:
                payload["context"] = context
            response = fallback_executor.invoke(payload)
            return _build_invocation_result(response, allowed_tool_names)
        raise


def invoke_agent(agent_name: str, query: str, context: dict | None = None) -> str:
    return invoke_agent_with_result(agent_name, query, context).answer
