import pytest
import os
from unittest.mock import patch
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
    assert "Agent 'nonexistent_agent' not found" in response.json()["detail"]
