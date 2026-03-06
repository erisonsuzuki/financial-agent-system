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

def test_load_config_llm_model_resolution_groq(tmp_path, monkeypatch):
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    config_file = config_dir / "test_agent.yaml"
    config_file.write_text("model_name: ${LLM_MODEL}\n")

    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-20b")

    config = config_loader.load_config("test_agent", base_path=tmp_path)

    assert config["model_name"] == "openai/gpt-oss-20b"

def test_load_config_llm_model_resolution_nvidia(tmp_path, monkeypatch):
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    config_file = config_dir / "test_agent.yaml"
    config_file.write_text("model_name: ${LLM_MODEL}\n")

    monkeypatch.setenv("LLM_PROVIDER", "nvidia")
    monkeypatch.setenv("NVIDIA_MODEL", "nvidia/nemotron-3-nano-30b-a3b")

    config = config_loader.load_config("test_agent", base_path=tmp_path)

    assert config["model_name"] == "nvidia/nemotron-3-nano-30b-a3b"

def test_invoke_agent_fallback_on_transient_error(monkeypatch):
    from app.agents import orchestrator_agent

    config = {
        "llm": {
            "provider": "groq",
            "model_name": "openai/gpt-oss-20b",
            "temperature": 0.0,
        },
        "tools": [],
    }

    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("LLM_FALLBACK_PROVIDER", "nvidia")
    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-20b")
    monkeypatch.setenv("NVIDIA_MODEL", "nvidia/nemotron-3-nano-30b-a3b")

    monkeypatch.setattr(orchestrator_agent.config_loader, "load_config", lambda _: config)

    request = httpx.Request("POST", "https://example.com")
    response = httpx.Response(429, request=request)

    class PrimaryExecutor:
        def invoke(self, payload):
            raise httpx.HTTPStatusError("rate limit", request=request, response=response)

    class FallbackExecutor:
        def invoke(self, payload):
            return {"output": "fallback"}

    calls = []

    def fake_create_agent_executor(agent_name, config=None, provider_override=None):
        calls.append(provider_override)
        if provider_override is None:
            return PrimaryExecutor()
        return FallbackExecutor()

    monkeypatch.setattr(orchestrator_agent, "create_agent_executor", fake_create_agent_executor)

    result = orchestrator_agent.invoke_agent("test_agent", "hello")

    assert result == "fallback"
    assert calls == [None, "nvidia"]

def test_invoke_agent_no_fallback_on_non_transient_error(monkeypatch):
    from app.agents import orchestrator_agent

    config = {
        "llm": {
            "provider": "groq",
            "model_name": "openai/gpt-oss-20b",
            "temperature": 0.0,
        },
        "tools": [],
    }

    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("LLM_FALLBACK_PROVIDER", "nvidia")
    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-20b")
    monkeypatch.setenv("NVIDIA_MODEL", "nvidia/nemotron-3-nano-30b-a3b")

    monkeypatch.setattr(orchestrator_agent.config_loader, "load_config", lambda _: config)

    class PrimaryExecutor:
        def invoke(self, payload):
            raise ValueError("non transient")

    calls = []

    def fake_create_agent_executor(agent_name, config=None, provider_override=None):
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
