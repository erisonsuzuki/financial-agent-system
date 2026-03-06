import logging
import os
from typing import Optional, cast

import httpx
from dotenv import load_dotenv
from langchain.agents import create_agent

from . import tools, config_loader

load_dotenv()

logger = logging.getLogger(__name__)

PROVIDER_MODEL_ENV = {
    "groq": "GROQ_MODEL",
    "nvidia": "NVIDIA_MODEL",
}

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
    if provider == "nvidia":
        from langchain_nvidia_ai_endpoints import ChatNVIDIA
        return ChatNVIDIA(
            model=model_name,
            temperature=temperature,
        )
    raise ValueError(f"Unsupported LLM provider: {provider}")

def create_agent_executor(agent_name: str, config: Optional[dict] = None, provider_override: Optional[str] = None):
    if config is None:
        config = config_loader.load_config(agent_name)
    
    available_tools = [getattr(tools, tool_name) for tool_name in config.get("tools", [])]

    llm_config = dict(config.get("llm", {}))
    if provider_override:
        provider_override = provider_override.lower()
        llm_config["provider"] = provider_override
        llm_config["model_name"] = resolve_model_name(provider_override, llm_config.get("model_name"))

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

def invoke_agent(agent_name: str, query: str) -> str:
    config = config_loader.load_config(agent_name)
    primary_provider = config.get("llm", {}).get("provider", "").lower()
    agent_executor = create_agent_executor(agent_name, config=config)

    try:
        response = agent_executor.invoke({"messages": [{"role": "user", "content": query}]})
        messages = response.get("messages", [])
        if not messages:
            return "Could not process the request."
        return messages[-1].content
    except Exception as exc:
        fallback_provider = os.getenv("LLM_FALLBACK_PROVIDER", "nvidia").lower()
        if (
            fallback_provider
            and fallback_provider != primary_provider
            and is_transient_llm_error(exc)
        ):
            fallback_executor = create_agent_executor(
                agent_name,
                config=config,
                provider_override=fallback_provider,
            )
            response = fallback_executor.invoke({"messages": [{"role": "user", "content": query}]})
            messages = response.get("messages", [])
            if not messages:
                return "Could not process the request."
            return messages[-1].content
        raise
