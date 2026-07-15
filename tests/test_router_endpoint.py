from types import SimpleNamespace

from fastapi import status


def test_router_endpoint_logs_action(client, auth_headers, monkeypatch):
    classification = {"agent_name": "registration_agent", "confidence": 0.87, "reasoning": "keywords"}
    agent_calls = []

    def fake_classify(payload):
        return classification

    def fake_invoke(agent_name, question, timeout=None):
        agent_calls.append((agent_name, question))
        return SimpleNamespace(answer="Registered asset successfully", tool_names=["register_asset_position"])

    monkeypatch.setattr("app.routers.agent.classify_agent_request", SimpleNamespace(invoke=fake_classify))
    monkeypatch.setattr("app.routers.agent.orchestrator_agent.invoke_agent_with_result", fake_invoke)

    payload = {"question": "Register 20 ITSA4 shares"}
    response = client.post("/agent/query/router", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["agent"] == "registration_agent"
    assert data["answer"] == "Registered asset successfully"
    assert data["routing_metadata"]["executed_tool_names"] == ["register_asset_position"]
    assert agent_calls == [("registration_agent", "Register 20 ITSA4 shares")]

    logs = client.get("/agent-actions/", headers=auth_headers).json()
    assert len(logs) == 1
    assert logs[0]["agent_name"] == "registration_agent"
    assert logs[0]["tool_calls"]["executed_tool_names"] == ["register_asset_position"]


def test_router_endpoint_fallbacks_to_analysis(client, auth_headers, monkeypatch):
    def fake_classify(payload):
        return {"agent_name": "analysis_agent", "confidence": 0.7, "reasoning": "fallback"}

    def fake_invoke(agent_name, question, timeout=None):
        return SimpleNamespace(answer="Analysis response", tool_names=["get_full_portfolio_analysis"])

    monkeypatch.setattr("app.routers.agent.classify_agent_request", SimpleNamespace(invoke=fake_classify))
    monkeypatch.setattr("app.routers.agent.orchestrator_agent.invoke_agent_with_result", fake_invoke)

    payload = {"question": "Where should I invest this month?"}
    response = client.post("/agent/query/router", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["agent"] == "analysis_agent"
    assert data["answer"] == "Analysis response"


def test_router_endpoint_routes_portuguese_registration(client, auth_headers, monkeypatch):
    def fake_classify(payload):
        return {"agent_name": "registration_agent", "confidence": 0.97, "reasoning": "keyword match"}

    def fake_invoke(agent_name, question, timeout=None):
        return SimpleNamespace(answer="Registro concluido", tool_names=["register_asset_position"])

    monkeypatch.setattr("app.routers.agent.classify_agent_request", SimpleNamespace(invoke=fake_classify))
    monkeypatch.setattr("app.routers.agent.orchestrator_agent.invoke_agent_with_result", fake_invoke)

    payload = {"question": "registre 400 itsa4 com PM R$ 9,32"}
    response = client.post("/agent/query/router", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["agent"] == "registration_agent"
    assert data["answer"] == "Registro concluido"


def test_router_endpoint_invalid_agent_defaults_to_analysis(client, auth_headers, monkeypatch):
    def fake_classify(payload):
        return {"agent_name": "invalid_agent", "confidence": 0.9, "reasoning": "invalid"}

    def fake_invoke(agent_name, question, timeout=None):
        return SimpleNamespace(answer="Analysis response", tool_names=[])

    monkeypatch.setattr("app.routers.agent.classify_agent_request", SimpleNamespace(invoke=fake_classify))
    monkeypatch.setattr("app.routers.agent.orchestrator_agent.invoke_agent_with_result", fake_invoke)

    payload = {"question": "Any question"}
    response = client.post("/agent/query/router", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["agent"] == "analysis_agent"
    assert data["answer"] == "Analysis response"
