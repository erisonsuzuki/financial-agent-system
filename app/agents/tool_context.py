from contextvars import ContextVar
from dataclasses import dataclass

from sqlalchemy.orm import Session


@dataclass
class ToolContext:
    user_id: int
    portfolio_id: int
    db_session: Session


_tool_context: ContextVar[ToolContext | None] = ContextVar("tool_context", default=None)


def set_tool_context(context: ToolContext):
    return _tool_context.set(context)


def get_tool_context() -> ToolContext | None:
    return _tool_context.get()


def reset_tool_context(token) -> None:
    _tool_context.reset(token)
