from sqlalchemy.orm import Session

from app import models, schemas


def create_agent_action(db: Session, user_id: int, payload: schemas.AgentActionCreate) -> models.AgentAction:
    db_action = models.AgentAction(user_id=user_id, **payload.model_dump())
    db.add(db_action)
    db.commit()
    db.refresh(db_action)
    return db_action


def get_agent_actions(db: Session, user_id: int, limit: int = 100) -> list[models.AgentAction]:
    return (
        db.query(models.AgentAction)
        .filter(models.AgentAction.user_id == user_id)
        .order_by(models.AgentAction.created_at.desc())
        .limit(limit)
        .all()
    )
