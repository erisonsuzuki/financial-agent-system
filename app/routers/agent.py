from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.agents import orchestrator_agent

router = APIRouter(
    prefix="/agent",
    tags=["AI Agent"],
)

class AgentQuery(BaseModel):
    question: str

class AgentResponse(BaseModel):
    answer: str

@router.post("/query/{agent_name}", response_model=AgentResponse)
def handle_agent_query(agent_name: str, query: AgentQuery):
    try:
        answer = orchestrator_agent.invoke_agent(agent_name, query.question)
        return AgentResponse(answer=answer)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {e}"
        )
