import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.agents import orchestrator_agent
from app.agents.tools import classify_agent_request
from app import crud, schemas
from app.database import get_db
from app.dependencies import get_current_user
from app.agents.tool_context import ToolContext, set_tool_context, reset_tool_context

logger = logging.getLogger(__name__)

ALLOWED_ROUTER_AGENTS = {"registration_agent", "management_agent", "analysis_agent"}

router = APIRouter(
    prefix="/agent",
    tags=["AI Agent"],
)

def _normalize_router_classification(classification: dict) -> dict:
    agent_name = classification.get("agent_name")
    confidence = classification.get("confidence")
    reasoning = classification.get("reasoning")

    if agent_name not in ALLOWED_ROUTER_AGENTS:
        return {
            "agent_name": "analysis_agent",
            "confidence": None,
            "reasoning": "Router output had invalid agent_name; defaulted to analysis_agent.",
        }

    if confidence is not None and not isinstance(confidence, (int, float)):
        confidence = None

    if not isinstance(reasoning, str) or not reasoning.strip():
        reasoning = "Router output missing reasoning; preserved selected agent."

    return {
        "agent_name": agent_name,
        "confidence": confidence,
        "reasoning": reasoning,
    }

@router.post("/query/router", response_model=schemas.AgentResponseWithMetadata)
def handle_router_query(
    query: schemas.AgentQuery,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    portfolio = crud.get_or_create_default_portfolio(db, user.id)
    token = set_tool_context(
        ToolContext(user_id=user.id, portfolio_id=portfolio.id, db_session=db)
    )
    try:
        classification = _normalize_router_classification(
            classify_agent_request.invoke({"question": query.question})
        )

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
    except Exception as e:
        logger.exception("Router agent query failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    finally:
        reset_tool_context(token)

@router.post("/query/{agent_name}", response_model=schemas.AgentResponse)
def handle_agent_query(
    agent_name: str,
    query: schemas.AgentQuery,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    logger.warning("/agent/query/{agent_name} is transitional; migrate to /agent/query/router")
    portfolio = crud.get_or_create_default_portfolio(db, user.id)
    token = set_tool_context(
        ToolContext(user_id=user.id, portfolio_id=portfolio.id, db_session=db)
    )
    try:
        # The agent executor will handle the "not found" case if the YAML file doesn't exist.
        answer = orchestrator_agent.invoke_agent(agent_name, query.question)
        return schemas.AgentResponse(answer=answer)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Agent configuration for '{agent_name}' not found.")
    except Exception as e:
        logger.exception("Direct agent query failed", extra={"agent_name": agent_name})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    finally:
        reset_tool_context(token)
