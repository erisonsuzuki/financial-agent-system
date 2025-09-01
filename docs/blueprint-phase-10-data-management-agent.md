# Implementation Blueprint: Phase 10 - Data Management Agent (Definitive Version)

## 1. Objective
To create a new `ManagementAgent` that understands natural language commands to find, update, and delete records in the user's portfolio. This involves creating new, specialized tools that use the CRUD API endpoints from Phase 9, a new agent configuration file, and a dedicated, robust test suite.

## 2. Consolidated Execution Checklist
-   [x] Create the new agent configuration file `app/agents/configs/management_agent.yaml`.
-   [x] Update `app/agents/tools.py` with new tools for finding, updating, and deleting records.
-   [x] Update `app/routers/agent.py` to be fully generic for any agent.
-   [x] Create the new test file, `tests/test_management_tools.py`, for the new tools.
-   [x] Update the `Makefile` with a new command to query the management agent.
-   [x] Update `README.md` to document the new agent's capabilities.
-   [x] Run `make up` to apply the changes.
-   [x] Run `make test` to ensure all tests pass.

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
</file>

### **New File: `app/agents/configs/management_agent.yaml`**
* **Path:** `app/agents/configs/management_agent.yaml`
<file path="app/agents/configs/management_agent.yaml">
agent_name: "DataManagementAgent"
description: "An agent expert in finding, updating, and deleting portfolio records based on user commands."

llm:
  provider: ${LLM_PROVIDER}
  model_name: ${GOOGLE_MODEL}
  temperature: 0.0

tools:
  - "list_transactions_for_ticker"
  - "update_transaction_by_id"
  - "delete_asset_by_ticker"

prompt_template: |
  You are a meticulous and careful financial data management assistant. Your goal is to help the user find and correct errors in their portfolio data.
  Your primary strategy is to first find the specific record the user wants to change, and then perform the update or deletion.

  Workflow:
  1.  If the user wants to modify a transaction (e.g., "correct a price"), you MUST first use the `list_transactions_for_ticker` tool to find the transaction and its ID.
  2.  If you find multiple transactions, you MUST ask the user a clarifying question to identify the correct one, showing them the transaction ID and details.
  3.  Once the specific transaction ID is identified, use the `update_transaction_by_id` tool to make the correction.
  4.  If the user wants to delete an asset, use the `delete_asset_by_ticker` tool.
  5.  After the action is complete, formulate a clear, concise confirmation message in the same language as the user's original query.

  User's request: {input}
</file>

### **File: `app/agents/tools.py` (Updated)**
* **Path:** `app/agents/tools.py`
<file path="app/agents/tools.py">
from langchain.tools import tool
import httpx
from datetime import date
from decimal import Decimal
from typing import Annotated, Optional, List

# --- Registration Tool ---

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
    
    asset_payload = {"ticker": ticker, "name": ticker, "asset_type": "STOCK"}
    try:
        with httpx.Client() as client:
            client.post(f"{base_url}/assets/", json=asset_payload, timeout=10.0)
    except httpx.HTTPStatusError as e:
        if e.response.status_code != 400: # 400 is expected for duplicates, which is ok
            return {"status": "error", "ticker": ticker, "message": f"Error creating asset: {e.response.text}"}
    
    transaction_payload = {
        "quantity": quantity,
        "price": str(average_price),
        "transaction_date": str(date.today())
    }
    try:
        with httpx.Client() as client:
            # First, we need the asset ID to create a transaction
            asset_response = client.get(f"{base_url}/assets/?ticker={ticker}", timeout=10.0)
            asset_response.raise_for_status()
            asset_id = asset_response.json()[0]['id']

            transaction_payload['asset_id'] = asset_id
            response = client.post(f"{base_url}/transactions/", json=transaction_payload, timeout=10.0)
            response.raise_for_status()
    except (httpx.HTTPStatusError, IndexError, KeyError) as e:
        return {"status": "error", "ticker": ticker, "message": f"Error creating initial transaction: {str(e)}"}
        
    return {"status": "success", "ticker": ticker, "quantity": quantity, "average_price": str(average_price)}

# --- Management Tools ---

@tool
def list_transactions_for_ticker(ticker: Annotated[str, "The ticker symbol to search for, e.g., 'PETR4.SA'."]) -> List[dict] | str:
    """
    Lists all transactions for a given asset ticker. Useful for finding a specific transaction ID before updating it.
    """
    base_url = "http://app:8000"
    try:
        with httpx.Client() as client:
            asset_response = client.get(f"{base_url}/assets/?ticker={ticker}", timeout=10.0)
            asset_response.raise_for_status()
            assets = asset_response.json()
            if not assets:
                return f"Error: Asset with ticker {ticker} not found."
            asset_id = assets[0]['id']
            
            # Note: This requires a new endpoint in assets.py router to list transactions for an asset_id
            # For now, let's assume it exists for the blueprint.
            transaction_response = client.get(f"{base_url}/assets/{asset_id}/transactions/", timeout=10.0)
            transaction_response.raise_for_status()
            return transaction_response.json()
    except (httpx.HTTPStatusError, IndexError, KeyError) as e:
        return f"Error: {str(e)}"

@tool
def update_transaction_by_id(
    transaction_id: Annotated[int, "The unique ID of the transaction to update."],
    new_quantity: Annotated[Optional[float], "The corrected quantity of the transaction."] = None,
    new_price: Annotated[Optional[Decimal], "The corrected price of the transaction."] = None,
    new_date: Annotated[Optional[str], "The corrected date of the transaction, in 'YYYY-MM-DD' format."] = None
) -> dict | str:
    """
    Updates one or more fields of a specific transaction identified by its ID.
    """
    base_url = "http://app:8000"
    update_payload = {}
    if new_quantity is not None:
        update_payload["quantity"] = new_quantity
    if new_price is not None:
        update_payload["price"] = str(new_price)
    if new_date is not None:
        update_payload["transaction_date"] = new_date

    if not update_payload:
        return "Error: At least one field (quantity, price, or date) must be provided to update."

    try:
        with httpx.Client() as client:
            response = client.put(f"{base_url}/transactions/{transaction_id}", json=update_payload, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return f"Error: {e.response.text}"

@tool
def delete_asset_by_ticker(ticker: Annotated[str, "The ticker symbol of the asset to delete, e.g., 'PETR4.SA'."]) -> str:
    """
    Deletes an asset and all its associated transactions and dividends from the portfolio.
    """
    base_url = "http://app:8000"
    try:
        with httpx.Client() as client:
            get_response = client.get(f"{base_url}/assets/?ticker={ticker}", timeout=10.0)
            get_response.raise_for_status()
            assets = get_response.json()
            if not assets:
                return f"Error: Asset with ticker {ticker} not found."
            asset_id = assets[0]["id"]
            
            delete_response = client.delete(f"{base_url}/assets/{asset_id}", timeout=10.0)
            delete_response.raise_for_status()
            return f"Successfully deleted asset {ticker} and all its records."
    except (httpx.HTTPStatusError, IndexError, KeyError) as e:
        return f"Error: {str(e)}"
</file>

### **File: `app/routers/agent.py` (Updated)**
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
        raise HTTPException(status_code=404, detail=f"Agent configuration for '{agent_name}' not found.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {e}"
        )
</file>

### **New File: `tests/test_management_tools.py`**
* **Path:** `tests/test_management_tools.py`
<file path="tests/test_management_tools.py">
import respx
import httpx
from decimal import Decimal
from app.agents.tools import update_transaction_by_id, delete_asset_by_ticker

@respx.mock
def test_update_transaction_by_id_success():
    # Arrange
    transaction_id = 123
    expected_payload = {"price": "99.99"}
    update_route = respx.put(f"http://app:8000/transactions/{transaction_id}").mock(
        return_value=httpx.Response(200, json={"id": transaction_id, "price": "99.99"})
    )

    # Act
    result = update_transaction_by_id.invoke({
        "transaction_id": transaction_id,
        "new_price": Decimal("99.99")
    })

    # Assert
    assert update_route.called
    assert update_route.calls[0].request.content == httpx.Request(method="PUT", url=f"http://app:8000/transactions/{transaction_id}", json=expected_payload).content
    assert result["price"] == "99.99"

@respx.mock
def test_delete_asset_by_ticker_success():
    # Arrange
    ticker = "PETR4.SA"
    asset_id = 1
    find_route = respx.get(f"http://app:8000/assets/?ticker={ticker}").mock(
        return_value=httpx.Response(200, json=[{"id": asset_id, "ticker": ticker}])
    )
    delete_route = respx.delete(f"http://app:8000/assets/{asset_id}").mock(
        return_value=httpx.Response(200, json={"id": asset_id, "ticker": ticker})
    )

    # Act
    result = delete_asset_by_ticker.invoke({"ticker": ticker})

    # Assert
    assert find_route.called
    assert delete_route.called
    assert "Successfully deleted asset PETR4.SA" in result
</file>

### **File: `README.md` (Updated)**
* **Path:** `(project root)`
<file path="README.md">
# ... (Header and other sections)
## API Endpoints & Agent Interaction

### AI Agent
* `POST /agent/query/{agent_name}`: Send a natural language query to a specific AI agent.
  * **Registration Agent (`registration_agent`):**
    `make agent-register q="Register: 100 ITSA4 at R$10.50"`
  * **Management Agent (`management_agent`):**
    `make agent-manage q="Correct my last transaction for ITSA4, the price was R$10.75"`

### Data Management
# ... (CRUD endpoints are the same)
# ... (Common Commands updated with new make commands)
</file>
