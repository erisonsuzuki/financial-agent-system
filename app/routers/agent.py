import json
import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.agents import orchestrator_agent
from app import crud, schemas
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/agent",
    tags=["AI Agent"],
)

def _parse_router_classification(raw_output: str) -> dict:
    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        for match in re.finditer(r"\{[\s\S]*?\}", raw_output):
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                continue
        return {
            "agent_name": "analysis_agent",
            "confidence": None,
            "reasoning": "Router output was not valid JSON; defaulted to analysis_agent.",
        }

@router.post("/query/router", response_model=schemas.AgentResponseWithMetadata)
def handle_router_query(
    query: schemas.AgentQuery,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    raw_classification = orchestrator_agent.invoke_agent("router_agent", query.question)
    classification = _parse_router_classification(raw_classification)

    agent_name = classification.get("agent_name") or "analysis_agent"
    agent_answer = orchestrator_agent.invoke_agent(agent_name, query.question)

    crud.create_agent_action(
        db,
        user_id=user.id,
        payload=schemas.AgentActionCreate(
            agent_name=agent_name,
            question=query.question,
            tool_calls=classification,
            response=agent_answer,
        ),
    )

    return schemas.AgentResponseWithMetadata(
        agent=agent_name,
        confidence=classification.get("confidence"),
        answer=agent_answer,
        routing_metadata=classification,
    )

@router.post("/query/{agent_name}", response_model=schemas.AgentResponse)
def handle_agent_query(agent_name: str, query: schemas.AgentQuery):
    try:
        # The agent executor will handle the "not found" case if the YAML file doesn't exist.
        answer = orchestrator_agent.invoke_agent(agent_name, query.question)
        return schemas.AgentResponse(answer=answer)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Agent configuration for '{agent_name}' not found.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {e}"
        )
