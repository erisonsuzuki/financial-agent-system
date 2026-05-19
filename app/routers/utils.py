from fastapi import HTTPException


def require_found(entity, detail: str):
    if entity is None:
        raise HTTPException(status_code=404, detail=detail)
    return entity
