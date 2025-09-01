# Implementation Blueprint: Phase 5 - Transaction and Dividend Endpoints

## 1. Objective
To implement API endpoints for creating and listing financial `Transactions` (buys/sells) and `Dividends` associated with each asset. This will enable the system to store a user's complete portfolio history. The new functionality will be fully tested.

## 2. Consolidated Execution Checklist
-   [x] Update `app/schemas.py` to include schemas for `Transaction` and `Dividend`.
-   [x] Update `app/crud.py` with functions to create and retrieve transactions and dividends.
-   [x] Create a new router file for transaction endpoints: `app/routers/transactions.py`.
-   [x] (Optional but recommended) Create a new router file for dividend endpoints: `app/routers/dividends.py`.
-   [x] Update `app/main.py` to include the new router(s).
-   [x] Create new test files (`tests/test_transactions.py`, `tests/test_dividends.py`) for the new endpoints.
-   [x] Update `README.md` to document the new API endpoints.
-   [x] Run `make up` to apply the changes.
-   [x] Run `make test` to ensure all tests pass.

---
## 3. File Contents

### **File: `app/schemas.py`**
* **Path:** `app/schemas.py`
<file path="app/schemas.py">
from pydantic import BaseModel, ConfigDict
from app.models import AssetType
from datetime import date

# --- Asset Schemas ---
class AssetBase(BaseModel):
    ticker: str
    name: str
    asset_type: AssetType
    sector: str | None = None

class AssetCreate(AssetBase):
    pass

class Asset(AssetBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class AssetPrice(BaseModel):
    ticker: str
    price: float
    source: str = "yfinance"

# --- Transaction Schemas ---
class TransactionBase(BaseModel):
    quantity: float
    price: float
    transaction_date: date

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    id: int
    asset_id: int
    model_config = ConfigDict(from_attributes=True)

# --- Dividend Schemas ---
class DividendBase(BaseModel):
    amount_per_share: float
    payment_date: date

class DividendCreate(DividendBase):
    pass

class Dividend(DividendBase):
    id: int
    asset_id: int
    model_config = ConfigDict(from_attributes=True)
</file>

### **File: `app/crud.py`**
* **Path:** `app/crud.py`
<file path="app/crud.py">
from sqlalchemy.orm import Session
from . import models, schemas

# --- Asset CRUD ---
def get_asset_by_ticker(db: Session, ticker: str) -> models.Asset | None:
    return db.query(models.Asset).filter(models.Asset.ticker == ticker).first()

def create_asset(db: Session, asset: schemas.AssetCreate) -> models.Asset:
    db_asset = models.Asset(**asset.model_dump())
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

# --- Transaction CRUD ---
def create_asset_transaction(db: Session, transaction: schemas.TransactionCreate, asset_id: int) -> models.Transaction:
    db_transaction = models.Transaction(**transaction.model_dump(), asset_id=asset_id)
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def get_transactions_for_asset(db: Session, asset_id: int, skip: int = 0, limit: int = 100) -> list[models.Transaction]:
    return db.query(models.Transaction).filter(models.Transaction.asset_id == asset_id).offset(skip).limit(limit).all()

# --- Dividend CRUD ---
def create_asset_dividend(db: Session, dividend: schemas.DividendCreate, asset_id: int) -> models.Dividend:
    db_dividend = models.Dividend(**dividend.model_dump(), asset_id=asset_id)
    db.add(db_dividend)
    db.commit()
    db.refresh(db_dividend)
    return db_dividend

def get_dividends_for_asset(db: Session, asset_id: int, skip: int = 0, limit: int = 100) -> list[models.Dividend]:
    return db.query(models.Dividend).filter(models.Dividend.asset_id == asset_id).offset(skip).limit(limit).all()
</file>

### **New File: `app/routers/transactions.py`**
* **Path:** `app/routers/transactions.py`
<file path="app/routers/transactions.py">
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.database import get_db

router = APIRouter(
    prefix="/assets/{ticker}/transactions",
    tags=["Transactions"],
)

@router.post("/", response_model=schemas.Transaction, status_code=status.HTTP_201_CREATED)
def add_transaction_for_asset(ticker: str, transaction: schemas.TransactionCreate, db: Session = Depends(get_db)):
    db_asset = crud.get_asset_by_ticker(db, ticker=ticker)
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return crud.create_asset_transaction(db=db, transaction=transaction, asset_id=db_asset.id)

@router.get("/", response_model=List[schemas.Transaction])
def list_transactions_for_asset(ticker: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_asset = crud.get_asset_by_ticker(db, ticker=ticker)
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    transactions = crud.get_transactions_for_asset(db=db, asset_id=db_asset.id, skip=skip, limit=limit)
    return transactions
</file>

### **New File: `app/routers/dividends.py`**
* **Path:** `app/routers/dividends.py`
<file path="app/routers/dividends.py">
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.database import get_db

router = APIRouter(
    prefix="/assets/{ticker}/dividends",
    tags=["Dividends"],
)

@router.post("/", response_model=schemas.Dividend, status_code=status.HTTP_201_CREATED)
def add_dividend_for_asset(ticker: str, dividend: schemas.DividendCreate, db: Session = Depends(get_db)):
    db_asset = crud.get_asset_by_ticker(db, ticker=ticker)
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return crud.create_asset_dividend(db=db, dividend=dividend, asset_id=db_asset.id)

@router.get("/", response_model=List[schemas.Dividend])
def list_dividends_for_asset(ticker: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_asset = crud.get_asset_by_ticker(db, ticker=ticker)
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    dividends = crud.get_dividends_for_asset(db=db, asset_id=db_asset.id, skip=skip, limit=limit)
    return dividends
</file>

### **File: `app/main.py` (Updated for Phase 5)**
* **Path:** `app/main.py`
<file path="app/main.py">
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
</file>

### **New File: `tests/test_transactions.py`**
* **Path:** `tests/test_transactions.py`
<file path="tests/test_transactions.py">
from fastapi.testclient import TestClient
from datetime import date

def test_create_transaction_for_asset(client: TestClient):
    # First, create an asset
    client.post("/assets/", json={"ticker": "VALE3", "name": "VALE", "asset_type": "STOCK"})

    # Create a transaction for that asset
    response = client.post(
        "/assets/VALE3/transactions/",
        json={"quantity": 100, "price": 61.50, "transaction_date": str(date.today())}
    )
    data = response.json()
    assert response.status_code == 201
    assert data["quantity"] == 100
    assert data["price"] == 61.50

def test_create_transaction_for_nonexistent_asset(client: TestClient):
    response = client.post(
        "/assets/NONEXISTENT/transactions/",
        json={"quantity": 100, "price": 10.0, "transaction_date": str(date.today())}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Asset not found"}

def test_list_transactions_for_asset(client: TestClient):
    # Create an asset and some transactions
    client.post("/assets/", json={"ticker": "BBDC4", "name": "BRADESCO", "asset_type": "STOCK"})
    client.post("/assets/BBDC4/transactions/", json={"quantity": 50, "price": 13.00, "transaction_date": "2025-01-15"})
    client.post("/assets/BBDC4/transactions/", json={"quantity": 25, "price": 13.50, "transaction_date": "2025-02-20"})

    # List the transactions
    response = client.get("/assets/BBDC4/transactions/")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 2
    assert data[0]["quantity"] == 50
    assert data[1]["quantity"] == 25
</file>

### **File: `README.md` (Updated)**
* **Path:** `(project root)`
<file path="README.md">
# Financial Agent System

This project is an investment management system that uses an architecture of AI agents to perform financial calculations, data retrieval, and reporting.

## Tech Stack
- **Language:** Python 3.11+
- **Framework:** FastAPI
- **Database:** PostgreSQL
- **Containerization:** Docker
- **Dependency Management:** Poetry
- **Testing:** Pytest
- **AI:** LangChain, LangGraph

## Getting Started
(Unchanged)

## API Endpoints

### Assets
* `POST /assets/`: Create a new financial asset.
* `GET /assets/{ticker}`: Retrieve an asset by its ticker symbol.
* `GET /assets/{ticker}/price`: Retrieve the current market price for an asset.

### Transactions
* `POST /assets/{ticker}/transactions/`: Add a new transaction (buy/sell) for an asset.
* `GET /assets/{ticker}/transactions/`: List all transactions for an asset.

### Dividends
* `POST /assets/{ticker}/dividends/`: Add a new dividend payment for an asset.
* `GET /assets/{ticker}/dividends/`: List all dividend payments for an asset.

## Testing
(Unchanged)

## Common Commands
(Unchanged)
</file>
