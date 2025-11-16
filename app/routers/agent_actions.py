from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, schemas
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/agent-actions",
    tags=["Agent Actions"],
    dependencies=[Depends(get_current_user)],
)

@router.post("/", response_model=schemas.AgentAction, status_code=status.HTTP_201_CREATED)
def create_agent_action(
    action_in: schemas.AgentActionCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return crud.create_agent_action(db, user_id=user.id, payload=action_in)

@router.get("/", response_model=list[schemas.AgentAction])
def list_agent_actions(
    limit: int = 100,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if limit <= 0:
        raise HTTPException(status_code=400, detail="limit must be positive")
    return crud.get_agent_actions(db, user_id=user.id, limit=min(limit, 500))
