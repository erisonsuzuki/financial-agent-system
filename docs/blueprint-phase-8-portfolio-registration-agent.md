# Implementation Blueprint: Phase 8 - Config-Driven AI Agent

## 1. Objective
To implement a configuration-driven AI agent that can parse natural language to register a user's portfolio. This architecture is scalable, configurable via YAML files, fully tested, includes a clean logging setup, and has a convenient `make` command for interaction.

## 2. Consolidated Execution Checklist
-   [x] Create the new file `app/logging_config.py` to manage log output.
-   [x] Update `app/main.py` to activate the new logging configuration.
-   [x] Update `.env.sample` with new environment variables for LLM configuration.
-   [x] Update `pyproject.toml` with the new dependencies (`langchain`, `pyyaml`, etc.).
-   [x] Create the `docker-compose.override.yml` file for development hot-reloading.
-   [x] Create the new agent configuration directory `app/agents/configs/` and the `registration_agent.yaml` file.
-   [x] Create the new helper module `app/agents/config_loader.py`.
-   [x] Create the new tools module `app/agents/tools.py` using the `Annotated` syntax.
-   [x] Refactor `app/agents/orchestrator_agent.py` into a generic, config-driven agent executor with `verbose=False`.
-   [x] Create a new router `app/routers/agent.py`.
-   [x] Create the new test files `tests/test_agent_system.py` and `tests/test_registration_tools.py`.
-   [x] Update the `Makefile` with the new `agent-query` and `update-deps` commands.
-   [x] Update `README.md` to explain all the new features.
-   [x] Run `make clean` and `make up` to apply all changes.
-   [x] Run `make test` to ensure all tests pass cleanly.
-   [x] Test the agent functionality with `make agent-query q="..."`.

---
## 3. File Contents

### **File: `Makefile`**
* **Path:** `(project root)`
<file path="Makefile">
# Makefile
up:
	docker compose up -d --build

down:
	docker compose down

# STOPS containers, REMOVES persistent volumes, and REMOVES images for this project.
clean:
	docker compose down --volumes --rmi all

# Updates all Python dependencies to their latest compatible versions
update-deps:
	docker compose exec --workdir /code/app app poetry update

logs:
	docker compose logs -f

shell:
	docker compose exec app bash

# Connect to the PostgreSQL shell inside the DB container
db-shell:
	docker compose exec db psql -U user -d financialdb

test:
	docker compose exec app pytest

# Send a query to the registration agent. Usage: make agent-query q="your question"
agent-query:
	@curl -s -X POST http://localhost:8000/agent/query/registration_agent \
	-H "Content-Type: application/json" \
	-d '{"question": "$(q)"}' | python -c "import sys, json; print(json.dumps(json.load(sys.stdin), ensure_ascii=False, indent=4))"
</file>

### **File: `.env.sample`**
* **Path:** `(project root)`
<file path=".env.sample">
# PostgreSQL DB Connection
POSTGRES_DB=financialdb
POSTGRES_USER=user
POSTGRES_PASSWORD=

# LLM Configuration
LLM_PROVIDER="google" # Can be "google" or "ollama"

# For Google Gemini
GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
GOOGLE_MODEL="gemini-1.5-flash"

# For local Ollama
OLLAMA_BASE_URL="http://host.docker.internal:11434"
OLLAMA_MODEL="llama3"
</file>

### **File: `docker-compose.override.yml`**
* **Path:** `(project root)`
<file path="docker-compose.override.yml">
services:
  app:
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
</file>

### **File: `app/pyproject.toml`**
* **Path:** `app/pyproject.toml`
<file path="app/pyproject.toml">
[tool.poetry]
name = "financial-agent-system"
version = "0.1.0"
description = "A financial management system with AI agents"
authors = ["erisonsuzuki"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.110.0"
uvicorn = {extras = ["standard"], version = "^0.29.0"}
sqlalchemy = "^2.0.29"
psycopg = {extras = ["binary"], version = "^3.1.18"}
yfinance = "^0.2.38"
langchain = "^0.2.1"
langchain-google-genai = "^1.0.4"
langchain-community = "^0.2.1"
python-dotenv = "^1.0.1"
httpx = "^0.27.0"
pyyaml = "^6.0.1"

[tool.poetry.group.dev.dependencies]
pytest = "^8.2.2"
respx = "^0.21.0"
</file>

### **File: `app/logging_config.py`**
* **Path:** `app/logging_config.py`
<file path="app/logging_config.py">
import logging

def setup_logging():
    """
    Silences a specific, noisy logger from a third-party library
    by setting its log level to a higher threshold (ERROR).
    """
    logging.getLogger("langchain_google_genai._function_utils").setLevel(logging.ERROR)
</file>

### **File: `app/main.py`**
* **Path:** `app/main.py`
<file path="app/main.py">
from fastapi import FastAPI, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

# Import and execute the logging configuration AT THE VERY TOP
from app.logging_config import setup_logging
setup_logging()

from app import models
from app.database import engine, SessionLocal
from app.routers import assets, transactions, dividends, agent

# This line creates the tables on startup.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Financial Agent System",
    description="API for managing financial assets with LLM agents.",
    version="0.1.0"
)

# Include all the API routers
app.include_router(assets.router)
app.include_router(transactions.router)
app.include_router(dividends.router)
app.include_router(agent.router)

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
</file>

### **File: `app/agents/configs/registration_agent.yaml`**
* **Path:** `app/agents/configs/registration_agent.yaml`
<file path="app/agents/configs/registration_agent.yaml">
agent_name: "PortfolioRegistrationAgent"
description: "An agent that extracts portfolio data from user text and registers it."

llm:
  provider: ${LLM_PROVIDER}
  model_name: ${GOOGLE_MODEL}
  temperature: 0.0

tools:
  - "register_asset_position"

prompt_template: |
  You are an expert financial assistant. Your task is to extract all asset positions from the user's message and register them using the available tools.
  For each distinct asset found in the user's text, you must call the `register_asset_position` tool with the correctly extracted ticker, quantity, and average_price.
  
  IMPORTANT: After all tools have been called successfully, you MUST synthesize a new, final answer. DO NOT simply repeat the tool's output. Your final answer must be a single, natural sentence confirming the action to the user **in the same language as their original input query**.

  User's request: {input}
</file>

### **File: `app/agents/config_loader.py`**
* **Path:** `app/agents/config_loader.py`
<file path="app/agents/config_loader.py">
import yaml
import os
import re
from pathlib import Path
from typing import Optional

def load_config(agent_name: str, base_path: Optional[Path] = None) -> dict:
    """
    Loads a YAML configuration file for an agent, substituting environment variables.
    An optional base_path can be provided for testing purposes.
    """
    if base_path is None:
        base_path = Path(__file__).parent

    config_path = base_path / "configs" / f"{agent_name}.yaml"
    
    if not config_path.is_file():
        raise FileNotFoundError(f"Agent configuration file not found at {config_path}")

    env_var_pattern = re.compile(r'\$\{(.*?)\}')
    
    with open(config_path, 'r') as f:
        raw_content = f.read()

    placeholders = env_var_pattern.findall(raw_content)
    for placeholder in placeholders:
        env_value = os.getenv(placeholder)
        if env_value is None:
            if placeholder == "GOOGLE_MODEL" and os.getenv("LLM_PROVIDER", "").lower() == "ollama":
                env_value = os.getenv("OLLAMA_MODEL")
            
            if env_value is None:
                raise ValueError(f"Environment variable '{placeholder}' not found and is required.")
        
        raw_content = raw_content.replace(f'${{{placeholder}}}', env_value)
            
    loaded_yaml = yaml.safe_load(raw_content)
    if loaded_yaml is None:
        return {}
    return loaded_yaml
</file>

### **File: `app/agents/tools.py`**
* **Path:** `app/agents/tools.py`
<file path="app/agents/tools.py">
from langchain.tools import tool
import httpx
from datetime import date
from decimal import Decimal
from typing import Annotated

@tool
def register_asset_position(
    ticker: Annotated[str, "The stock ticker symbol of the asset, for example, 'PETR4.SA'."],
    quantity: Annotated[float, "The total quantity of the asset the user currently holds."],
    average_price: Annotated[Decimal, "The user's average purchase price for this asset."]
) -> dict:
    """
    Registers a user's complete position for a single asset.
    It first creates the asset if it doesn't exist, then creates a single,
    synthetic initial transaction representing the user's provided average price and quantity.
    This tool should be called for each asset identified in the user's query.
    """
    base_url = "http://app:8000"
    
    # Step 1: Create the Asset
    asset_payload = {"ticker": ticker, "name": ticker, "asset_type": "STOCK"}
    try:
        with httpx.Client() as client:
            client.post(f"{base_url}/assets/", json=asset_payload, timeout=10.0)
    except httpx.HTTPStatusError as e:
        if e.response.status_code != 400: # 400 is expected for duplicates, which is ok
            return {"status": "error", "ticker": ticker, "message": f"Error creating asset: {e.response.text}"}
    
    # Step 2: Create the initial synthetic transaction
    transaction_payload = {
        "quantity": quantity,
        "price": str(average_price),
        "transaction_date": str(date.today())
    }
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{base_url}/assets/{ticker}/transactions/",
                json=transaction_payload,
                timeout=10.0
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        return {"status": "error", "ticker": ticker, "message": f"Error creating transaction: {e.response.text}"}
        
    return {"status": "success", "ticker": ticker, "quantity": quantity, "average_price": str(average_price)}
</file>

### **File: `app/agents/orchestrator_agent.py`**
* **Path:** `app/agents/orchestrator_agent.py`
<file path="app/agents/orchestrator_agent.py">
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from . import tools, config_loader

load_dotenv()

def get_llm(llm_config: dict):
    provider = llm_config.get("provider", "").lower()
    model_name = llm_config.get("model_name")
    temperature = llm_config.get("temperature", 0.0)

    if provider == "google":
        return ChatGoogleGenerativeAI(model=model_name, temperature=temperature)
    elif provider == "ollama":
        return ChatOllama(
            base_url=os.getenv("OLLAMA_BASE_URL"),
            model=model_name,
            temperature=temperature
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

def create_agent_executor(agent_name: str):
    config = config_loader.load_config(agent_name)
    
    available_tools = [getattr(tools, tool_name) for tool_name in config.get("tools", [])]

    llm = get_llm(config.get("llm", {}))
    llm_with_tools = llm.bind_tools(tools=available_tools)

    prompt = ChatPromptTemplate.from_messages([
        ("system", config.get("prompt_template", "You are a helpful assistant.")),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    
    agent = create_tool_calling_agent(llm_with_tools, available_tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=available_tools, verbose=False)
    
    return agent_executor

def invoke_agent(agent_name: str, query: str) -> str:
    agent_executor = create_agent_executor(agent_name)
    response = agent_executor.invoke({"input": query})
    return response.get("output", "Could not process the request.")
</file>

### **File: `app/routers/agent.py`**
* **Path:** `app/routers/agent.py`
<file path="app/routers/agent.py">
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
</file>

### **File: `tests/test_agent_system.py`**
* **Path:** `tests/test_agent_system.py`
<file path="tests/test_agent_system.py">
import pytest
import os
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.agents import config_loader

def test_load_config_success(tmp_path):
    # Arrange
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    config_file = config_dir / "test_agent.yaml"
    config_file.write_text("key: ${MY_TEST_VAR}")
    os.environ["MY_TEST_VAR"] = "value"
    
    # Act
    config = config_loader.load_config("test_agent", base_path=tmp_path)
    
    # Assert
    assert config["key"] == "value"
    
    del os.environ["MY_TEST_VAR"]

def test_load_config_missing_env_var(tmp_path):
    # Arrange
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    config_file = config_dir / "test_agent.yaml"
    config_file.write_text("key: ${A_VAR_THAT_DOES_NOT_EXIST}")
    
    # Act & Assert
    with pytest.raises(ValueError, match="Environment variable 'A_VAR_THAT_DOES_NOT_EXIST' not found"):
        config_loader.load_config("test_agent", base_path=tmp_path)

def test_agent_query_success(client: TestClient):
    with patch("app.agents.orchestrator_agent.invoke_agent") as mock_invoke:
        mock_invoke.return_value = "Success!"
        
        response = client.post(
            "/agent/query/registration_agent",
            json={"question": "test question"}
        )
        
        assert response.status_code == 200
        assert response.json() == {"answer": "Success!"}
        mock_invoke.assert_called_with("registration_agent", "test question")

def test_agent_query_agent_not_found(client: TestClient):
    response = client.post(
        "/agent/query/nonexistent_agent",
        json={"question": "test question"}
    )
    
    assert response.status_code == 404
    assert "Agent 'nonexistent_agent' not found" in response.json()["detail"]
</file>

### **File: `README.md`**
* **Path:** `(project root)`
<file path="README.md">
# Financial Agent System

This project is an investment management system that uses an architecture of AI agents to perform financial calculations, data retrieval, and reporting.

## Architecture Overview
This project utilizes an AI-driven, tool-based agent architecture powered by LangChain. The core idea is to separate the agent's logic, configuration, and capabilities.

### Core Components
* **Orchestrator Agent (`orchestrator_agent.py`):** This is the generic "engine". It's responsible for loading an agent's configuration, interpreting the user's natural language query, and managing the execution flow.
* **Agent Configurations (`app/agents/configs/*.yaml`):** These YAML files define the "personality" and capabilities of each agent. They specify the prompt (the agent's instructions), the tools it's allowed to use, and the LLM model it should connect to.
* **Tools (`tools.py`):** These are the specific Python functions that the LLM can decide to call. They act as the agent's "hands and eyes," allowing it to interact with our API, databases, or external services.

### Execution Flow
1.  A user sends a query to a named agent (e.g., `registration_agent`).
2.  The Orchestrator loads the corresponding `.yaml` config file.
3.  It combines the user's query with the prompt and tool definitions and sends them to the LLM.
4.  The LLM analyzes the request and decides which tool(s) to call and with which arguments.
5.  The Orchestrator executes the chosen tools (e.g., calls our own API to save data).
6.  The LLM receives the results from the tools and formulates a final, natural language answer for the user.

## Tech Stack
- **Language:** Python 3.11+
- **Framework:** FastAPI
- **Database:** PostgreSQL
- **Containerization:** Docker
- **Dependency Management:** Poetry
- **Testing:** Pytest
- **AI:** LangChain, PyYAML
- **Data Fetching:** yfinance

## Getting Started

### Environment Variables
Before running the application, copy `.env.sample` to `.env` and fill in the values:
* `POSTGRES_...`: Your database credentials.
* `LLM_PROVIDER`: The AI provider to use. Can be `google` or `ollama`.
* `GOOGLE_API_KEY`: Your API key if using Google Gemini.
* `GOOGLE_MODEL`: The Gemini model to use (e.g., `gemini-1.5-flash`, `gemini-1.5-pro`).
* `OLLAMA_BASE_URL`: The URL for your local Ollama server (e.g., `http://host.docker.internal:11434`).
* `OLLAMA_MODEL`: The name of the Ollama model to use (e.g., `llama3`).

### Setup and Running
1.  **Build and Run the Application:** Use `make up`. The API will be available at `http://localhost:8000`.
2.  **Run Tests (Recommended):** Verify the setup with `make test`.

## API Endpoints & Agent Interaction

### AI Agent
* `POST /agent/query/{agent_name}`: Send a natural language query to a specific AI agent.
  * **Example (`registration_agent`):** `make agent-query q="Register my portfolio: 100 ITSA4 at R$10.50"`

### Data Management
* `POST /assets/`: Create a new financial asset.
* `GET /assets/{ticker}`: Retrieve an asset by its ticker symbol.
* `POST /assets/{ticker}/transactions/`: Add a new transaction for an asset.
* `GET /assets/{ticker}/transactions/`: List all transactions for an asset.

## Common Commands
- `make up`: Build and start all services (with hot reloading).
- `make down`: Stop and remove all services.
- `make clean`: Stop services, remove containers, volumes, and images for this project.
- `make logs`: View the logs from all running services.
- `make shell`: Access the shell of the running application container.
- `make db-shell`: Connect to a PostgreSQL shell inside the database container.
- `make test`: Run the unit test suite.
- `make agent-query q="..."`: Send a query to the registration agent.
</file>
