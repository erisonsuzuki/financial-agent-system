import json
from fastapi import status


def test_router_endpoint_logs_action(client, auth_headers, monkeypatch):
    responses = iter([
        json.dumps({"agent_name": "registration_agent", "confidence": 0.87, "reasoning": "keywords"}),
        "Registered asset successfully",
    ])

    def fake_invoke(agent_name, question, timeout=None):
        return next(responses)

    monkeypatch.setattr("app.routers.agent.orchestrator_agent.invoke_agent", fake_invoke)

    payload = {"question": "Register 20 ITSA4 shares"}
    response = client.post("/agent/query/router", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["agent"] == "registration_agent"
    assert data["answer"] == "Registered asset successfully"

    logs = client.get("/agent-actions/", headers=auth_headers).json()
    assert len(logs) == 1
    assert logs[0]["agent_name"] == "registration_agent"


def test_router_endpoint_fallbacks_to_analysis(client, auth_headers, monkeypatch):
    responses = iter([
        "not-json-output",
        "Analysis response",
    ])

    def fake_invoke(agent_name, question, timeout=None):
        return next(responses)

    monkeypatch.setattr("app.routers.agent.orchestrator_agent.invoke_agent", fake_invoke)

    payload = {"question": "Where should I invest this month?"}
    response = client.post("/agent/query/router", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["agent"] == "analysis_agent"
    assert data["answer"] == "Analysis response"
