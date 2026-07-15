import os
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.agents import config_loader

def test_load_config_success(tmp_path):
    # Arrange
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    config_file = config_dir / "test_agent.yaml"
    config_file.write_text("key: ${MY_TEST_VAR}")
    os.environ["MY_TEST_VAR"] = "value"
    
    # Act
    config = config_loader.load_config("test_agent", base_path=tmp_path)
    
    # Assert
    assert config["key"] == "value"
    
    del os.environ["MY_TEST_VAR"]

def test_load_config_missing_env_var(tmp_path):
    # Arrange
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    config_file = config_dir / "test_agent.yaml"
    config_file.write_text("key: ${A_VAR_THAT_DOES_NOT_EXIST}")
    
    # Act & Assert
    with pytest.raises(ValueError, match="Environment variable 'A_VAR_THAT_DOES_NOT_EXIST' not found"):
        config_loader.load_config("test_agent", base_path=tmp_path)

def test_load_config_llm_model_resolution(tmp_path, monkeypatch):
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    config_file = config_dir / "test_agent.yaml"
    config_file.write_text("model_name: ${LLM_MODEL}\n")

    monkeypatch.setenv("MAIN_MODEL", "openai/gpt-oss-120b")

    config = config_loader.load_config("test_agent", base_path=tmp_path)

    assert config["model_name"] == "openai/gpt-oss-120b"

def test_invoke_agent_fallback_on_transient_error(monkeypatch):
    from app.agents import orchestrator_agent

    config = {
        "llm": {
            "provider": "groq",
            "model_name": "openai/gpt-oss-120b",
            "temperature": 0.0,
        },
        "tools": [],
    }

    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("MAIN_MODEL", "openai/gpt-oss-120b")
    monkeypatch.setenv("FALLBACK_MODEL", "openai/gpt-oss-20b")

    monkeypatch.setattr(orchestrator_agent.config_loader, "load_config", lambda _: config)

    request = httpx.Request("POST", "https://example.com")
    response = httpx.Response(429, request=request)

    class PrimaryExecutor:
        def invoke(self, payload):
            raise httpx.HTTPStatusError("rate limit", request=request, response=response)

    class FallbackExecutor:
        def invoke(self, payload):
            class Message:
                def __init__(self, content):
                    self.content = content

            return {"messages": [Message("fallback")]}

    calls = []

    def fake_create_agent_executor(agent_name, config=None, provider_override=None, model_name_override=None):
        calls.append(provider_override)
        if provider_override is None:
            return PrimaryExecutor()
        return FallbackExecutor()

    monkeypatch.setattr(orchestrator_agent, "create_agent_executor", fake_create_agent_executor)

    result = orchestrator_agent.invoke_agent("test_agent", "hello")

    assert result == "fallback"
    assert calls == [None, "groq"]


def test_invocation_result_records_only_completed_allowed_tools():
    from app.agents import orchestrator_agent

    messages = [
        type("Message", (), {"type": "ai", "tool_calls": [{"name": "register_asset_position", "args": {"ticker": "ITSA4"}}]})(),
        type("Message", (), {"type": "tool", "name": "register_asset_position", "content": "sensitive tool output"})(),
        type("Message", (), {"type": "tool", "name": "unregistered_tool", "content": "ignored"})(),
        type("Message", (), {"type": "ai", "content": "Registered asset"})(),
    ]

    result = orchestrator_agent._build_invocation_result({"messages": messages}, {"register_asset_position"})

    assert result.answer == "Registered asset"
    assert result.tool_names == ["register_asset_position"]

def test_invoke_agent_no_fallback_on_non_transient_error(monkeypatch):
    from app.agents import orchestrator_agent

    config = {
        "llm": {
            "provider": "groq",
            "model_name": "openai/gpt-oss-120b",
            "temperature": 0.0,
        },
        "tools": [],
    }

    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("MAIN_MODEL", "openai/gpt-oss-120b")
    monkeypatch.setenv("FALLBACK_MODEL", "openai/gpt-oss-20b")

    monkeypatch.setattr(orchestrator_agent.config_loader, "load_config", lambda _: config)

    class PrimaryExecutor:
        def invoke(self, payload):
            raise ValueError("non transient")

    calls = []

    def fake_create_agent_executor(agent_name, config=None, provider_override=None, model_name_override=None):
        calls.append(provider_override)
        return PrimaryExecutor()

    monkeypatch.setattr(orchestrator_agent, "create_agent_executor", fake_create_agent_executor)

    with pytest.raises(ValueError, match="non transient"):
        orchestrator_agent.invoke_agent("test_agent", "hello")

    assert calls == [None]

def test_agent_query_success(client: TestClient):
    with patch("app.agents.orchestrator_agent.invoke_agent") as mock_invoke:
        mock_invoke.return_value = "Success!"
        
        response = client.post(
            "/agent/query/registration_agent",
            json={"question": "test question"}
        )
        
        assert response.status_code == 200
        assert response.json() == {"answer": "Success!"}
        mock_invoke.assert_called_with("registration_agent", "test question")

def test_agent_query_agent_not_found(client: TestClient):
    response = client.post(
        "/agent/query/nonexistent_agent",
        json={"question": "test question"}
    )
    
    assert response.status_code == 404
    assert "Agent configuration for 'nonexistent_agent' not found." in response.json()["detail"]


def test_agent_query_requires_authentication(no_auth_client: TestClient):
    response = no_auth_client.post(
        "/agent/query/registration_agent",
        json={"question": "test question"},
    )
    assert response.status_code == 401
def test_agent_query_internal_error_is_generic(client: TestClient):
    with patch("app.agents.orchestrator_agent.invoke_agent", side_effect=RuntimeError("secret details")):
        response = client.post(
            "/agent/query/registration_agent",
            json={"question": "test question"},
        )

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
