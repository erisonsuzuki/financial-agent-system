from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


def test_read_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Financial Agent System is running!"}


def test_health_check_success(client: TestClient):
    with patch("app.main.SessionLocal") as mock_session_local:
        mock_db = MagicMock()
        mock_db.execute.return_value = None
        mock_session_local.return_value = mock_db
        
        response = client.get("/health")
        
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "details": {
            "database": {
                "status": "ok"
            }
        }
    }

def test_health_check_failure(client: TestClient):
    # Use patch to simulate a database connection error
    with patch("app.main.SessionLocal") as mock_session_local:
        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("Database connection failed")
        mock_session_local.return_value = mock_db
        response = client.get("/health")
    assert response.status_code == 503
    assert response.json() == {
        "status": "error",
        "details": {
            "database": {
                "status": "error"
            }
        }
    }
