# Implementation Blueprint: Phase 6 - Portfolio Analyzer Agent & Calculations

## 1. Objective
To create a `PortfolioAnalyzerAgent` that performs key financial calculations for a given asset, including average price, total invested, financial return, and dividend yield. This logic will be exposed via a new `/analysis` API endpoint and will be fully covered by unit tests.

## 2. Consolidated Execution Checklist
-   [x] Update `app/schemas.py` to include the new `AssetAnalysis` response model.
-   [x] Create the new file `app/agents/portfolio_analyzer_agent.py` containing all the calculation logic.
-   [x] Update `app/routers/assets.py` to add the new `/analysis` endpoint.
-   [x] Create the new test file `tests/test_portfolio_analyzer_agent.py` to rigorously test the financial calculations.
-   [x] Update `README.md` to document the new analysis endpoint.
-   [x] Run `make up` to apply the changes.
-   [x] Run `make test` to ensure all new and existing tests pass.

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

# --- Analysis Schemas ---
class AssetAnalysis(BaseModel):
    ticker: str
    total_quantity: float
    average_price: float
    total_invested: float
    current_market_price: float | None
    current_market_value: float | None
    financial_return_value: float | None
    financial_return_percent: float | None
    total_dividends_received: float
</file>

### **File: `app/agents/portfolio_analyzer_agent.py`**
* **Path:** `app/agents/portfolio_analyzer_agent.py`
<file path="app/agents/portfolio_analyzer_agent.py">
from sqlalchemy.orm import Session
from app import models, schemas, crud
from app.agents import market_data_agent

def analyze_asset(db: Session, asset: models.Asset) -> schemas.AssetAnalysis:
    """
    Performs a complete financial analysis for a single asset.
    """
    transactions = crud.get_transactions_for_asset(db=db, asset_id=asset.id, limit=1000)
    dividends = crud.get_dividends_for_asset(db=db, asset_id=asset.id, limit=1000)

    # Calculate portfolio state from transactions
    total_quantity = 0.0
    total_invested = 0.0
    for t in transactions:
        total_quantity += t.quantity # Assuming buys are positive, sells are negative
    
    if total_quantity > 0:
        # Calculate weighted average price only for buy transactions
        buy_transactions = [t for t in transactions if t.quantity > 0]
        total_cost = sum(t.quantity * t.price for t in buy_transactions)
        total_shares_bought = sum(t.quantity for t in buy_transactions)
        average_price = total_cost / total_shares_bought if total_shares_bought > 0 else 0.0
        # Total invested reflects the cost of the currently held shares
        total_invested = total_quantity * average_price
    else:
        average_price = 0.0
        total_invested = 0.0

    # Calculate total dividends
    total_dividends_received = sum(d.amount_per_share * total_quantity for d in dividends) # Simplified for now

    # Fetch current market data
    current_market_price = market_data_agent.get_current_price(ticker=asset.ticker)

    # Calculate metrics that depend on market data
    current_market_value = None
    financial_return_value = None
    financial_return_percent = None

    if current_market_price is not None:
        current_market_value = total_quantity * current_market_price
        if total_invested > 0:
            financial_return_value = current_market_value - total_invested
            financial_return_percent = (financial_return_value / total_invested) * 100

    return schemas.AssetAnalysis(
        ticker=asset.ticker,
        total_quantity=total_quantity,
        average_price=average_price,
        total_invested=total_invested,
        current_market_price=current_market_price,
        current_market_value=current_market_value,
        financial_return_value=financial_return_value,
        financial_return_percent=financial_return_percent,
        total_dividends_received=total_dividends_received,
    )
</file>

### **File: `app/routers/assets.py`**
* **Path:** `app/routers/assets.py`
<file path="app/routers/assets.py">
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, schemas
from app.database import get_db
from app.agents import market_data_agent, portfolio_analyzer_agent

router = APIRouter(
    prefix="/assets",
    tags=["Assets"],
)

@router.post("/", response_model=schemas.Asset, status_code=status.HTTP_201_CREATED)
def create_new_asset(asset: schemas.AssetCreate, db: Session = Depends(get_db)):
    db_asset = crud.get_asset_by_ticker(db, ticker=asset.ticker)
    if db_asset:
        raise HTTPException(status_code=400, detail="Asset with this ticker already exists")
    return crud.create_asset(db=db, asset=asset)

@router.get("/{ticker}", response_model=schemas.Asset)
def read_asset(ticker: str, db: Session = Depends(get_db)):
    db_asset = crud.get_asset_by_ticker(db, ticker=ticker)
    if db_asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return db_asset

@router.get("/{ticker}/price", response_model=schemas.AssetPrice)
def get_asset_price(ticker: str):
    price = market_data_agent.get_current_price(ticker=ticker)
    if price is None:
        raise HTTPException(status_code=404, detail=f"Could not retrieve price for ticker {ticker}")
    return schemas.AssetPrice(ticker=ticker, price=price)

@router.get("/{ticker}/analysis", response_model=schemas.AssetAnalysis)
def get_asset_analysis(ticker: str, db: Session = Depends(get_db)):
    db_asset = crud.get_asset_by_ticker(db, ticker=ticker)
    if db_asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    analysis = portfolio_analyzer_agent.analyze_asset(db=db, asset=db_asset)
    return analysis
</file>

### **New File: `tests/test_portfolio_analyzer_agent.py`**
* **Path:** `tests/test_portfolio_analyzer_agent.py`
<file path="tests/test_portfolio_analyzer_agent.py">
from sqlalchemy.orm import Session
from unittest.mock import patch
from datetime import date

from app.agents import portfolio_analyzer_agent
from app import crud, schemas

def test_analyze_asset_full_scenario(db_session: Session):
    # Arrange: Create the asset, transactions, and dividends in the test DB
    asset_schema = schemas.AssetCreate(ticker="TEST4.SA", name="Test Asset", asset_type="STOCK", sector="Testing")
    asset = crud.create_asset(db=db_session, asset=asset_schema)

    # Two buy transactions
    trans1_schema = schemas.TransactionCreate(quantity=100, price=10.00, transaction_date=date(2025, 1, 15))
    crud.create_asset_transaction(db=db_session, transaction=trans1_schema, asset_id=asset.id)
    
    trans2_schema = schemas.TransactionCreate(quantity=50, price=12.00, transaction_date=date(2025, 2, 20))
    crud.create_asset_transaction(db=db_session, transaction=trans2_schema, asset_id=asset.id)

    # One dividend payment
    div1_schema = schemas.DividendCreate(amount_per_share=0.50, payment_date=date(2025, 3, 10))
    crud.create_asset_dividend(db=db_session, dividend=div1_schema, asset_id=asset.id)

    # Mock the external price agent
    with patch('app.agents.market_data_agent.get_current_price') as mock_get_price:
        mock_get_price.return_value = 15.00  # Set a mock current market price

        # Act: Run the analysis
        analysis = portfolio_analyzer_agent.analyze_asset(db=db_session, asset=asset)

        # Assert: Check all calculations
        assert analysis.ticker == "TEST4.SA"
        assert analysis.total_quantity == 150.0 # 100 + 50
        
        # total_cost = (100 * 10) + (50 * 12) = 1000 + 600 = 1600
        # total_shares_bought = 100 + 50 = 150
        # average_price = 1600 / 150 = 10.666...
        assert round(analysis.average_price, 2) == 10.67
        
        # total_invested = total_quantity * average_price = 150 * 10.666... = 1600
        assert round(analysis.total_invested, 2) == 1600.00

        # total_dividends = amount_per_share * total_quantity = 0.50 * 150 = 75
        assert analysis.total_dividends_received == 75.0

        assert analysis.current_market_price == 15.00
        
        # current_market_value = total_quantity * current_price = 150 * 15 = 2250
        assert analysis.current_market_value == 2250.0

        # financial_return = market_value - total_invested = 2250 - 1600 = 650
        assert analysis.financial_return_value == 650.0
        
        # return_percent = (return_value / total_invested) * 100 = (650 / 1600) * 100 = 40.625
        assert round(analysis.financial_return_percent, 2) == 40.63
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
* `GET /assets/{ticker}/analysis`: Retrieve a complete financial analysis for an asset.

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
