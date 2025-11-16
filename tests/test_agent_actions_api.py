from fastapi import status


def test_create_and_list_agent_actions(client, auth_headers):
    create_payload = {
        "agent_name": "registration_agent",
        "question": "Register 10 shares of ITUB4",
        "tool_calls": {"agent_name": "registration_agent"},
        "response": "Registered",
    }
    create_response = client.post("/agent-actions/", json=create_payload, headers=auth_headers)
    assert create_response.status_code == status.HTTP_201_CREATED
    created = create_response.json()
    assert created["agent_name"] == "registration_agent"
    assert created["question"].startswith("Register 10")

    list_response = client.get("/agent-actions/", headers=auth_headers)
    assert list_response.status_code == status.HTTP_200_OK
    entries = list_response.json()
    assert len(entries) == 1
    assert entries[0]["id"] == created["id"]


def test_limit_validation(client, auth_headers):
    response = client.get("/agent-actions/?limit=0", headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
