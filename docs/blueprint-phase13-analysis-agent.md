# Implementation Blueprint: Phase 13 - The Analysis Agent

## 1. Objective
To create the final `AnalysisAgent`, a new LLM agent that understands natural language queries about investment strategy. This agent will use a new tool, `get_full_portfolio_analysis`, to call our existing analysis API, find the most "discounted" asset, and provide a clear recommendation to the user.

## 2. Consolidated Execution Checklist
-   [x] Create the new agent configuration file `app/agents/configs/analysis_agent.yaml`.
-   [x] Update `app/agents/tools.py` to add the new `get_full_portfolio_analysis` tool.
-   [x] Create the new test file `tests/test_analysis_tools.py` to test the new tool.
-   [x] Update the `Makefile` with a new command: `agent-analyze`.
-   [x] Update `README.md` to document the new agent's capabilities.
-   [x] Run `make up` to apply the changes.
-   [x] Run `make test` to ensure all new and existing tests pass.
-   [x] Test the final functionality with `make agent-analyze q="Where should I invest this month?"`

---
## 3. File Contents

### **New File: `app/agents/configs/analysis_agent.yaml`**
* **Path:** `app/agents/configs/analysis_agent.yaml`
<file path="app/agents/configs/analysis_agent.yaml">
agent_name: "AnalysisAgent"
description: "An agent that analyzes the user's portfolio and provides investment recommendations based on their strategy."

llm:
  provider: ${LLM_PROVIDER}
  model_name: ${GOOGLE_MODEL}
  temperature: 0.0

tools:
  - "get_full_portfolio_analysis"

prompt_template: |
  You are an expert financial analyst agent. Your goal is to help the user decide where to invest their money based on their stated strategy.
  
  You have access to the following tools:
  {tools}

  Use the following format:

  Question: the input question you must answer
  Thought: The user wants an investment recommendation. First, I must get a complete overview of their current portfolio. I will use the `get_full_portfolio_analysis` tool for this.
  Action: get_full_portfolio_analysis
  Action Input: {{}}
  Observation: A list of analysis data for each asset in the portfolio.
  Thought: I have the analysis for all assets. The user's strategy is to invest in the most "discounted" asset. This means I must find the asset with the lowest (most negative) `financial_return_percent` from the list I just received. I will iterate through the list to find the asset with the minimum `financial_return_percent`.
  ... (Internal thought process of finding the minimum)
  Thought: I have identified the best asset for a new contribution. It is [Asset Ticker] with a return of [Return Percentage]. I now have the final answer.
  Final Answer: A clear, concise recommendation in the user's original language, explaining which asset is the best choice and why (mentioning the asset ticker and its negative return percentage).

  Begin!

  Question: {input}
  Thought:{agent_scratchpad}
</file>

### **File: `app/agents/tools.py` (Updated)**
* **Path:** `app/agents/tools.py`
<file path="app/agents/tools.py">
from langchain.tools import tool
import httpx
from datetime import date
from decimal import Decimal
from typing import Annotated, Optional, List, Any
from pydantic import BaseModel, Field

# --- Input Schemas for Tools ---
# ... (RegisterAssetInput, TickerInput, UpdateTransactionInput remain the same)

class ListAllTransactionsInput(BaseModel):
    limit: Optional[int] = Field(default=100, description="The maximum number of recent transactions to return.")

# --- Tool Definitions ---

# ... (register_asset_position, list_all_transactions, list_transactions_for_ticker, update_transaction_by_id, delete_asset_by_ticker remain the same)

# --- NEW ANALYSIS TOOL ---

@tool
def get_full_portfolio_analysis() -> List[dict] | str:
    """
    Analyzes all assets in the portfolio and returns a list of their financial metrics.
    This should be the primary tool to get an overview of the entire portfolio before making a recommendation.
    """
    base_url = "http://app:8000"
    try:
        with httpx.Client() as client:
            # 1. Get all assets
            asset_response = client.get(f"{base_url}/assets/", timeout=10.0)
            asset_response.raise_for_status()
            assets = asset_response.json()
            if not assets:
                return "Error: No assets found in the portfolio to analyze."
            
            # 2. For each asset, get its detailed analysis
            full_analysis = []
            for asset in assets:
                ticker = asset.get("ticker")
                if not ticker:
                    continue
                
                analysis_response = client.get(f"{base_url}/assets/{ticker}/analysis", timeout=10.0)
                analysis_response.raise_for_status() # Will raise for 404s etc.
                full_analysis.append(analysis_response.json())
            
            return full_analysis
    except (httpx.HTTPStatusError, IndexError, KeyError) as e:
        return f"An unexpected error occurred during portfolio analysis: {str(e)}"
</file>

### **New File: `tests/test_analysis_tools.py`**
* **Path:** `tests/test_analysis_tools.py`
<file path="tests/test_analysis_tools.py">
import respx
import httpx
from app.agents.tools import get_full_portfolio_analysis

@respx.mock
def test_get_full_portfolio_analysis_success():
    # Arrange: Mock all the API calls this tool will make
    
    # 1. Mock the call to get all assets
    respx.get("http://app:8000/assets/").mock(
        return_value=httpx.Response(200, json=[
            {"id": 1, "ticker": "PETR4.SA"},
            {"id": 2, "ticker": "VALE3.SA"}
        ])
    )
    
    # 2. Mock the analysis call for the first asset
    respx.get("http://app:8000/assets/PETR4.SA/analysis").mock(
        return_value=httpx.Response(200, json={
            "ticker": "PETR4.SA", 
            "financial_return_percent": "10.50"
        })
    )
    
    # 3. Mock the analysis call for the second asset
    respx.get("http://app:8000/assets/VALE3.SA/analysis").mock(
        return_value=httpx.Response(200, json={
            "ticker": "VALE3.SA",
            "financial_return_percent": "-5.20"
        })
    )

    # Act
    result = get_full_portfolio_analysis.invoke({})

    # Assert
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["ticker"] == "PETR4.SA"
    assert result[1]["ticker"] == "VALE3.SA"
    assert result[1]["financial_return_percent"] == "-5.20"

@respx.mock
def test_get_full_portfolio_analysis_no_assets():
    # Arrange
    respx.get("http://app:8000/assets/").mock(return_value=httpx.Response(200, json=[]))

    # Act
    result = get_full_portfolio_analysis.invoke({})

    # Assert
    assert "Error: No assets found" in result
</file>

### **File: `Makefile` (Updated)**
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

# Send a query to the registration agent
agent-register:
	@curl -s -X POST http://localhost:8000/agent/query/registration_agent \
	-H "Content-Type: application/json" \
	-d '{"question": "$(q)"}' | python -c "import sys, json; print(json.dumps(json.load(sys.stdin), ensure_ascii=False, indent=4))"

# Send a query to the management agent
agent-manage:
	@curl -s -X POST http://localhost:8000/agent/query/management_agent \
	-H "Content-Type: application/json" \
	-d '{"question": "$(q)"}' | python -c "import sys, json; print(json.dumps(json.load(sys.stdin), ensure_ascii=False, indent=4))"

# Send a query to the analysis agent
agent-analyze:
	@curl -s -X POST http://localhost:8000/agent/query/analysis_agent \
	-H "Content-Type: application/json" \
	-d '{"question": "$(q)"}' | python -c "import sys, json; print(json.dumps(json.load(sys.stdin), ensure_ascii=False, indent=4))"

# Debug agent queries to see raw output
agent-debug:
	@curl -X POST http://localhost:8000/agent/query/management_agent \
	-H "Content-Type: application/json" \
	-d '{"question": "$(q)"}'
</file>

### **File: `README.md` (Updated)**
* **Path:** `(project root)`
<file path="README.md">
# ... (Header and other sections remain the same)
## API Endpoints & Agent Interaction

### AI Agent
* `POST /agent/query/{agent_name}`: Send a natural language query to a specific AI agent.
  * **Registration Agent (`registration_agent`):**
    `make agent-register q="Register: 100 ITSA4 at R$10.50"`
  * **Management Agent (`management_agent`):**
    `make agent-manage q="Correct my last transaction for ITSA4, the price was R$10.75"`
  * **Analysis Agent (`analysis_agent`):**
    `make agent-analyze q="Where should I invest R$1000 this month?"`

### Data Management
# ... (Data Management endpoints remain the same)

### Analysis Endpoints
* `GET /assets/{ticker}/price`: Retrieve the current market price for an asset.
* `GET /assets/{ticker}/analysis`: Retrieve a complete financial analysis for an asset.

## Common Commands
# ... (Makefile commands remain the same, but now include agent-analyze)
- `make agent-register q="..."`: Send a query to the registration agent.
- `make agent-manage q="..."`: Send a query to the management agent.
- `make agent-analyze q="..."`: Send a query to the analysis agent.
</file>
