from fastapi import FastAPI, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app import models
from app.database import engine, SessionLocal
from app.routers import assets, transactions, dividends

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Financial Agent System",
    description="API for managing financial assets with LLM agents.",
    version="0.1.0"
)

app.include_router(assets.router)
app.include_router(transactions.router)
app.include_router(dividends.router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Financial Agent System is running!"}

@app.get("/health", status_code=status.HTTP_200_OK, tags=["Monitoring"])
def health_check(response: Response):
    db_status = "ok"
    db = SessionLocal()
    try:
        db.execute(text('SELECT 1'))
    except Exception:
        db_status = "error"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    finally:
        db.close()
    
    health_details = {
        "status": "ok" if db_status == "ok" else "error",
        "details": {"database": {"status": db_status}}
    }

    if health_details["status"] == "error":
        return JSONResponse(status_code=response.status_code, content=health_details)
    
    return health_details
