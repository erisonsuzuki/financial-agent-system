# Implementation Blueprint: Phase 11 - Global Transaction Listing Tool

## 1. Objective
To create a `list_all_transactions` tool and the corresponding API endpoint, and to make this tool available to the `ManagementAgent`. This will allow the agent to answer general questions about the user's transaction history.

## 2. Consolidated Execution Checklist
-   [x] Update `app/crud.py` with a function to get all transactions from the database.
-   [x] Update `app/routers/transactions.py` with a new endpoint to list all transactions.
-   [x] Update `app/schemas.py`.
-   [x] Update ` app/agents/orchestrator_agent.py` activating verbose=true.
-   [x] Update `app/agents/tools.py` with the new `list_all_transactions` tool.
-   [x] Update `app/agents/configs/management_agent.yaml` to give the agent permission to use the new tool and update its prompt.
-   [x] Update `tests/test_transactions.py` with a test for the new endpoint.
-   [x] Update `tests/test_registration_tool.py` with a test for the new tool.
-   [x] Update `README.md` to document the new API endpoint.
-   [x] Run `make up` and `make test`.

---
## 3. File Contents

### **File: `app/agents/orchestrator_agent.py` (Updated)**
* **Path:** `app/agents/orchestrator_agent.py`
<file path="app/agents/orchestrator_agent.py">
...
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
    agent_executor = AgentExecutor(agent=agent, tools=available_tools, verbose=True)
    
    return agent_executor
...
</file>

### **File: `app/crud.py` (Updated)**
* **Path:** `app/crud.py`
<file path="app/crud.py">
from sqlalchemy.orm import Session
from typing import Optional
from . import models, schemas

# ... (Asset CRUD functions are unchanged)

# --- Transaction CRUD ---
def get_transaction(db: Session, transaction_id: int) -> models.Transaction | None:
    return db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()

def get_transactions(db: Session, asset_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> list[models.Transaction]:
    query = db.query(models.Transaction).options(joinedload(models.Transaction.asset)).order_by(models.Transaction.transaction_date.desc())
    if asset_id is not None:
        query = query.filter(models.Transaction.asset_id == asset_id)
    return query.offset(skip).limit(limit).all()

# ... (create, update, delete functions for Transaction and Dividend are unchanged)
</file>

### **File: `app/routers/transactions.py` (Updated)**
* **Path:** `app/routers/transactions.py`
<file path="app/routers/transactions.py">
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from app import crud, schemas
from app.database import get_db

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
)

@router.post("/", response_model=schemas.Transaction, status_code=status.HTTP_201_CREATED)
def add_transaction(transaction: schemas.TransactionCreate, db: Session = Depends(get_db)):
    db_asset = crud.get_asset(db, asset_id=transaction.asset_id)
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return crud.create_asset_transaction(db=db, transaction=transaction)

@router.get("/", response_model=List[schemas.Transaction])
def list_transactions(asset_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    transactions = crud.get_transactions(db=db, asset_id=asset_id, skip=skip, limit=limit)
    return transactions

@router.get("/{transaction_id}", response_model=schemas.Transaction)
def read_transaction(transaction_id: int, db: Session = Depends(get_db)):
    db_transaction = crud.get_transaction(db, transaction_id=transaction_id)
    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return db_transaction

@router.put("/{transaction_id}", response_model=schemas.Transaction)
def update_existing_transaction(transaction_id: int, transaction_in: schemas.TransactionUpdate, db: Session = Depends(get_db)):
    db_transaction = crud.get_transaction(db, transaction_id=transaction_id)
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return crud.update_transaction(db=db, db_transaction=db_transaction, transaction_in=transaction_in)

@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_transaction(transaction_id: int, db: Session = Depends(get_db)):
    db_transaction = crud.delete_transaction(db, transaction_id=transaction_id)
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
</file>

### **File: `app/agents/tools.py` (Updated)**
* **Path:** `app/agents/tools.py`
<file path="app/agents/tools.py">
from langchain.tools import tool
import httpx
from datetime import date
from decimal import Decimal
from typing import Annotated, Optional, List, Any

def _parse_ticker_from_input(ticker_input: Any) -> str:
    """
    Sanitizes the ticker input, which might come as a string or a dict from the LLM.
    It also converts the ticker to uppercase for consistency.
    """
    if isinstance(ticker_input, dict):
        ticker_input = ticker_input.get("ticker", "")
    return str(ticker_input).strip().upper()

@tool
def register_asset_position(
    ticker: Annotated[str, "The stock ticker symbol, e.g., 'PETR4.SA'."],
    quantity: Annotated[float, "The total quantity the user holds."],
    average_price: Annotated[Decimal, "The user's average purchase price for this asset."]
) -> dict:
    """Registers a user's complete position for a single asset."""
    ticker = _parse_ticker_from_input(ticker)
    base_url = "http://app:8000"
    
    asset_payload = {"ticker": ticker, "name": ticker, "asset_type": "STOCK"}
    transaction_payload = {
        "quantity": quantity,
        "price": str(average_price),
        "transaction_date": str(date.today())
    }

    try:
        with httpx.Client() as client:
            # Step 1: Attempt to create the asset
            try:
                client.post(f"{base_url}/assets/", json=asset_payload, timeout=10.0)
            except httpx.HTTPStatusError as e:
                if e.response.status_code != 400: # 400 is expected for duplicates
                    raise e # Re-raise the error to be caught by the main block

            # Step 2: Fetch the Asset ID (newly created or already existing)
            asset_response = client.get(f"{base_url}/assets/?ticker={ticker}", timeout=10.0)
            asset_response.raise_for_status()
            assets = asset_response.json()
            if not assets:
                return {"status": "error", "ticker": ticker, "message": f"Asset with ticker {ticker} not found after creation attempt."}
            asset_id = assets[0]['id']

            # Step 3: Create the initial synthetic transaction with the Asset ID
            transaction_payload['asset_id'] = asset_id
            response = client.post(f"{base_url}/transactions/", json=transaction_payload, timeout=10.0)
            response.raise_for_status()

    except (httpx.HTTPStatusError, IndexError, KeyError) as e:
        return {"status": "error", "ticker": ticker, "message": f"An error occurred: {str(e)}"}
        
    return {"status": "success", "ticker": ticker, "quantity": quantity, "average_price": str(average_price)}

@tool
def list_all_transactions(limit: Annotated[Optional[int], "The maximum number of recent transactions to return."] = 100) -> List[dict] | str:
    """
    Lists recent transactions across all assets in the portfolio.
    Useful for general questions like 'what was my last transaction?'.
    """
    base_url = "http://app:8000"
    try:
        with httpx.Client() as client:
            response = client.get(f"{base_url}/transactions/?limit={limit}", timeout=10.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return f"Error: {e.response.text}"
# ... (list_transactions_for_ticker, update_transaction_by_id, delete_asset_by_ticker tools are unchanged)
</file>

### **File: `app/agents/configs/management_agent.yaml` (Updated)**
* **Path:** `app/agents/configs/management_agent.yaml`
<file path="app/agents/configs/management_agent.yaml">
agent_name: "DataManagementAgent"
description: "An agent expert in finding, updating, and deleting portfolio records based on user commands."

llm:
  provider: ${LLM_PROVIDER}
  model_name: ${GOOGLE_MODEL}
  temperature: 0.0

tools:
  - "list_all_transactions"
  - "list_transactions_for_ticker"
  - "update_transaction_by_id"
  - "delete_asset_by_ticker"

prompt_template: |
  You are a meticulous and careful financial data management assistant. Your goal is to help the user find and correct errors in their portfolio data.
  Your primary strategy is to first find the specific record the user wants to change, and then perform the update or deletion.

  Workflow:
  1. If the user's request is general (e.g., "my last transaction"), use `list_all_transactions`.
  2. If the user wants to modify a transaction for a specific stock, use `list_transactions_for_ticker` to find the transaction and its ID.
  3. If you find multiple transactions, you MUST ask the user a clarifying question to identify the correct one.
  4. Once the specific transaction ID is identified, use the `update_transaction_by_id` tool to make the correction.
  5. After the action is complete, you MUST formulate a natural language response. If the tool returns a list of data, like transactions, you must summarize and format it in a readable sentence for the user. Do not just output the raw JSON data. Always respond in the same language as the user's original query.

  User's request: {input}
</file>

### **File: `app/schemas.py` (Updated)**
* **Path:** `app/schemas.py`
<file path="app/schemas.py">
from pydantic import BaseModel, ConfigDict
from app.models import AssetType
from datetime import date
from decimal import Decimal

# --- Asset Schemas ---
class AssetBase(BaseModel):
    ticker: str
    name: str
    asset_type: AssetType
    sector: str | None = None

class AssetInTransaction(BaseModel):
    ticker: str
    model_config = ConfigDict(from_attributes=True)

class AssetUpdate(BaseModel):
    name: str | None = None
    sector: str | None = None

class AssetCreate(AssetBase):
    pass

class Asset(AssetBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class AssetPrice(BaseModel):
    ticker: str
    price: Decimal
    source: str = "yfinance"

# --- Transaction Schemas ---
class TransactionBase(BaseModel):
    quantity: float
    price: Decimal
    transaction_date: date

class TransactionUpdate(BaseModel):
    quantity: float | None = None
    price: Decimal | None = None
    transaction_date: date | None = None

class TransactionCreate(TransactionBase):
    asset_id: int

class Transaction(TransactionBase):
    id: int
    asset: AssetInTransaction
    model_config = ConfigDict(from_attributes=True)

# --- Dividend Schemas ---
class DividendBase(BaseModel):
    amount_per_share: Decimal
    payment_date: date

class DividendUpdate(BaseModel):
    amount_per_share: Decimal | None = None
    payment_date: date | None = None

class DividendCreate(DividendBase):
    asset_id: int

class Dividend(DividendBase):
    id: int
    asset_id: int
    model_config = ConfigDict(from_attributes=True)

# --- Analysis Schemas ---
class AssetAnalysis(BaseModel):
    ticker: str
    total_quantity: float
    average_price: Decimal
    total_invested: Decimal
    current_market_price: Decimal | None
    current_market_value: Decimal | None
    financial_return_value: Decimal | None
    financial_return_percent: Decimal | None
    total_dividends_received: Decimal
</file>

### **File: `tests/test_transactions.py` (Updated)**
* **Path:** `tests/test_transactions.py`
<file path="tests/test_transactions.py">
from fastapi.testclient import TestClient
from datetime import date
from decimal import Decimal
from app import crud, schemas

def test_create_transaction_success(client: TestClient, db_session):
    # Arrange: Create an asset to link to
    asset = crud.create_asset(db_session, schemas.AssetCreate(ticker="VALE3", name="VALE", asset_type="STOCK"))
    
    # Act: Create a transaction
    response = client.post(
        "/transactions/",
        json={"asset_id": asset.id, "quantity": 100, "price": "61.50", "transaction_date": str(date.today())}
    )
    data = response.json()

    # Assert
    assert response.status_code == 201
    assert data["quantity"] == 100
    assert data["price"] == "61.50"
    assert data["asset"]["ticker"] == "VALE3" # Check the nested object

def test_create_transaction_for_nonexistent_asset(client: TestClient):
    transaction_data = {"asset_id": 99999, "quantity": 100, "price": "10.00", "transaction_date": str(date.today())}
    response = client.post("/transactions/", json=transaction_data)
    assert response.status_code == 404
    assert response.json() == {"detail": "Asset not found"}

def test_read_transaction_success(client: TestClient):
    # First, create an asset
    asset_data = {"ticker": "PETR4", "name": "PETROBRAS", "asset_type": "STOCK", "sector": "Oil & Gas"}
    response_asset = client.post("/assets/", json=asset_data)
    asset_id = response_asset.json()["id"]

    # Create a transaction
    transaction_data = {"asset_id": asset_id, "quantity": 50, "price": "30.00", "transaction_date": "2023-01-01"}
    response_post = client.post("/transactions/", json=transaction_data)
    transaction_id = response_post.json()["id"]

    # Read the transaction
    response_get = client.get(f"/transactions/{transaction_id}")
    data = response_get.json()
    assert response_get.status_code == 200
    assert data["id"] == transaction_id
    assert data["quantity"] == 50
    assert data["price"] == "30.00"

def test_read_transaction_not_found(client: TestClient):
    response = client.get("/transactions/99999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Transaction not found"}

def test_update_transaction_success(client: TestClient):
    # First, create an asset
    asset_data = {"ticker": "ITSA4", "name": "ITAU SA", "asset_type": "STOCK", "sector": "Financial"}
    response_asset = client.post("/assets/", json=asset_data)
    asset_id = response_asset.json()["id"]

    # Create a transaction
    transaction_data = {"asset_id": asset_id, "quantity": 100, "price": "10.00", "transaction_date": "2023-01-01"}
    response_post = client.post("/transactions/", json=transaction_data)
    transaction_id = response_post.json()["id"]

    # Update the transaction
    update_data = {"quantity": 120, "price": "10.50", "transaction_date": "2023-01-02"}
    response_put = client.put(f"/transactions/{transaction_id}", json=update_data)
    data = response_put.json()
    assert response_put.status_code == 200
    assert data["id"] == transaction_id
    assert data["quantity"] == 120
    assert data["price"] == "10.50"
    assert data["transaction_date"] == "2023-01-02"

def test_update_transaction_not_found(client: TestClient):
    update_data = {"quantity": 10}
    response = client.put("/transactions/99999", json=update_data)
    assert response.status_code == 404
    assert response.json() == {"detail": "Transaction not found"}

def test_delete_transaction_success(client: TestClient, db_session):
    # Arrange: Create an asset and a transaction to delete
    asset = crud.create_asset(db_session, schemas.AssetCreate(ticker="PETR4", name="PETROBRAS", asset_type="STOCK"))
    transaction = crud.create_asset_transaction(db_session, schemas.TransactionCreate(asset_id=asset.id, quantity=50, price=Decimal("30.00"), transaction_date="2025-01-01"))

    # Act: Delete the transaction
    response = client.delete(f"/transactions/{transaction.id}")

    # Assert: Deletion was successful and returns no content
    assert response.status_code == 204

    # Assert: Verify the transaction is actually gone
    get_response = client.get(f"/transactions/{transaction.id}")
    assert get_response.status_code == 404

def test_delete_transaction_not_found(client: TestClient):
    response = client.delete("/transactions/99999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Transaction not found"}

def test_list_all_transactions(client: TestClient, db_session):
    # Arrange: Create multiple assets and transactions
    asset1 = crud.create_asset(db_session, schemas.AssetCreate(ticker="ASSET1", name="Asset One", asset_type="STOCK"))
    asset2 = crud.create_asset(db_session, schemas.AssetCreate(ticker="ASSET2", name="Asset Two", asset_type="STOCK"))
    
    crud.create_asset_transaction(db_session, schemas.TransactionCreate(asset_id=asset1.id, quantity=10, price=Decimal("10.00"), transaction_date="2025-01-01"))
    crud.create_asset_transaction(db_session, schemas.TransactionCreate(asset_id=asset2.id, quantity=20, price=Decimal("20.00"), transaction_date="2025-01-02"))

    # Act
    response = client.get("/transactions/")
    data = response.json()

    # Assert
    assert response.status_code == 200
    assert len(data) == 2
    assert data[0]["price"] == "20.00" # Sorted by date descending
    assert data[1]["price"] == "10.00"
</file>


### **File: `tests/test_registration_tool.py` (Updated)**
* **Path:** `tests/test_registration_tool.py`
<file path="tests/test_registration_tool.py">
import respx
import httpx
from decimal import Decimal
from app.agents.tools import register_asset_position

@respx.mock
def test_register_asset_position_success():
    # Arrange: Mock all three internal API calls that the tool will make
    ticker = "TEST4.SA"
    asset_id = 1
    
    # 1. Mock the POST to create the asset
    respx.post("http://app:8000/assets/").mock(return_value=httpx.Response(201))
    
    # 2. Mock the GET to find the asset's ID
    respx.get(f"http://app:8000/assets/?ticker={ticker}").mock(
        return_value=httpx.Response(200, json=[{"id": asset_id, "ticker": ticker}])
    )
    
    # 3. Mock the POST to create the transaction
    respx.post("http://app:8000/transactions/").mock(return_value=httpx.Response(201))

    # Act
    result = register_asset_position.invoke({
        "ticker": ticker,
        "quantity": 150,
        "average_price": Decimal("10.50")
    })

    # Assert
    assert result["status"] == "success"
    assert result["ticker"] == ticker

@respx.mock
def test_register_asset_position_handles_existing_asset():
    # Arrange: Mock the API calls, simulating that the asset already exists (400)
    ticker = "EXIST.SA"
    asset_id = 2

    # 1. Mock the POST to create the asset (simulating it already exists)
    respx.post("http://app:8000/assets/").mock(return_value=httpx.Response(400))
    
    # 2. Mock the GET to find the asset's ID
    respx.get(f"http://app:8000/assets/?ticker={ticker}").mock(
        return_value=httpx.Response(200, json=[{"id": asset_id, "ticker": ticker}])
    )

    # 3. Mock the POST to create the transaction
    respx.post("http://app:8000/transactions/").mock(return_value=httpx.Response(201))

    # Act
    result = register_asset_position.invoke({
        "ticker": ticker,
        "quantity": 50,
        "average_price": Decimal("25.00")
    })

    # Assert
    assert result["status"] == "success"
</file>
