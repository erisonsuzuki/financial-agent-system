from fastapi import FastAPI

app = FastAPI(
    title="Financial Agent System",
    description="API for managing financial assets with LLM agents.",
    version="0.1.0"
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Financial Agent System is running!"}
