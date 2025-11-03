# Implementation Blueprint: Phase 12 - Portfolio Analyzer & Market Data

## 1. Objective
To build the core financial calculation engine of the application. This involves creating two new service modules (worker agents) and exposing their logic via new API endpoints. This phase provides the necessary tools for a future "AnalysisAgent" (LLM) to use.

The new modules are:
1.  **MarketDataAgent:** Fetches real-time prices from an external source (yfinance) with caching.
2.  **PortfolioAnalyzerAgent:** Uses all available data to calculate metrics like average price, total invested, and financial return.

## 2. Consolidated Execution Checklist
-   [ ] Update `app/pyproject.toml` to add the `yfinance` dependency.
-   [ ] Update `app/schemas.py` to add the new `AssetPrice` and `AssetAnalysis` response models.
-   [ ] Create the new file `app/agents/market_data_agent.py` to handle price fetching.
-   [ ] Create the new file `app/agents/portfolio_analyzer_agent.py` to handle financial calculations.
-   [ ] Update `app/routers/assets.py` to add two new endpoints: `/{ticker}/price` and `/{ticker}/analysis`.
-   [ ] Create the new test file `tests/test_market_data_agent.py` to test the price fetching logic.
-   [ ] Create the new test file `tests/test_portfolio_analyzer_agent.py` to test the financial calculations.
-   [ ] Update `README.md` to document the new analysis endpoints.
-   [ ] Run `make up` to install the new dependency.
-   [ ] Run `make test` to ensure all new and existing tests pass.

---
## 3. File Contents

### **File: `app/pyproject.toml` (Updated)**
* **Path:** `app/pyproject.toml`
<file path="app/pyproject.toml">
[tool.poetry]
name = "financial-agent-system"
version = "0.1.0"
description = ""
authors = ["erisonsuzuki"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.110.0"
uvicorn = {extras = ["standard"], version = "^0.29.0"}
sqlalchemy = "^2.0.29"
psycopg = {extras = ["binary"], version = "^3.1.18"}
yfinance = "^0.2.40"
langchain = "^0.2.1"
langchain-google-genai = "^1.0.4"
langchain-community = "^0.2.1"
python-dotenv = "^1.0.1"
httpx = "^0.27.0"
pyyaml = "^6.0.1"
pandas = "^2.2.2"

[tool.poetry.group.dev.dependencies]
pytest = "^8.2.2"
respx = "^0.21.0"
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

### **New File: `app/agents/market_data_agent.py`**
* **Path:** `app/agents/market_data_agent.py`
<file path="app/agents/market_data_agent.py">
import yfinance as yf
import time
from typing import Dict, Any
from decimal import Decimal

# Simple in-memory cache to avoid excessive API calls
_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 60 * 15  # 15 minutes

def get_current_price(ticker: str) -> Decimal | None:
    """
    Fetches the current price for a given ticker, using a time-based cache.
    """
    current_time = time.time()
    
    # Check cache first
    if ticker in _cache:
        cached_data = _cache[ticker]
        if current_time - cached_data["timestamp"] < CACHE_TTL_SECONDS:
            return cached_data["price"]

    # If not in cache or expired, fetch from yfinance
    try:
        stock = yf.Ticker(ticker)
        # Fetch the most recent price data
        hist = stock.history(period="1d")
        if hist.empty:
            return None
            
        price = hist['Close'].iloc[-1]
        price_decimal = Decimal(str(price)).quantize(Decimal("0.01"))
        
        # Update cache
        _cache[ticker] = {"price": price_decimal, "timestamp": current_time}
        
        return price_decimal
    except Exception:
        # Could be a network error or invalid ticker
        return None
</file>

### **New File: `app/agents/portfolio_analyzer_agent.py`**
* **Path:** `app/agents/portfolio_analyzer_agent.py`
<file path="app/agents/portfolio_analyzer_agent.py">
from sqlalchemy.orm import Session
from decimal import Decimal, ROUND_HALF_UP
from app import models, schemas, crud
from app.agents import market_data_agent

def analyze_asset(db: Session, asset: models.Asset) -> schemas.AssetAnalysis:
    """
    Performs a complete financial analysis for a single asset using Decimal for precision.
    """
    transactions = crud.get_transactions(db=db, asset_id=asset.id, limit=10000)
    dividends = crud.get_dividends_for_asset(db=db, asset_id=asset.id, limit=10000)

    total_quantity = sum(Decimal(str(t.quantity)) for t in transactions)
    
    average_price = Decimal("0.00")
    total_invested = Decimal("0.00")

    if total_quantity > 0:
        buy_transactions = [t for t in transactions if t.quantity > 0]
        total_cost = sum(Decimal(str(t.quantity)) * t.price for t in buy_transactions)
        total_shares_bought = sum(Decimal(str(t.quantity)) for t in buy_transactions)
        
        if total_shares_bought > 0:
            average_price = (total_cost / total_shares_bought).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
        total_invested = (total_quantity * average_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Note: This is a simplification. A more complex model would consider the quantity at the time of each dividend payment.
    total_dividends_received = sum(d.amount_per_share * total_quantity for d in dividends).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    current_market_price = market_data_agent.get_current_price(ticker=asset.ticker)

    current_market_value = None
    financial_return_value = None
    financial_return_percent = None

    if current_market_price is not None:
        current_market_value = (total_quantity * current_market_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if total_invested > 0:
            financial_return_value = current_market_value - total_invested
            financial_return_percent = ((financial_return_value / total_invested) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return schemas.AssetAnalysis(
        ticker=asset.ticker,
        total_quantity=float(total_quantity),
        average_price=average_price,
        total_invested=total_invested,
        current_market_price=current_market_price,
        current_market_value=current_market_value,
        financial_return_value=financial_return_value,
        financial_return_percent=financial_return_percent,
        total_dividends_received=total_dividends_received,
    )
</file>

### **File: `app/routers/assets.py` (Updated)**
* **Path:** `app/routers/assets.py`
<file path="app/routers/assets.py">
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app import crud, schemas, models
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

@router.get("/", response_model=List[schemas.Asset])
def list_assets(ticker: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    assets = crud.get_assets(db, ticker=ticker, skip=skip, limit=limit)
    return assets

@router.get("/{asset_id}", response_model=schemas.Asset)
def read_asset(asset_id: int, db: Session = Depends(get_db)):
    db_asset = crud.get_asset(db, asset_id=asset_id)
    if db_asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return db_asset

@router.put("/{asset_id}", response_model=schemas.Asset)
def update_existing_asset(asset_id: int, asset_in: schemas.AssetUpdate, db: Session = Depends(get_db)):
    db_asset = crud.get_asset(db, asset_id=asset_id)
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return crud.update_asset(db=db, db_asset=db_asset, asset_in=asset_in)

@router.delete("/{asset_id}", response_model=schemas.Asset)
def delete_existing_asset(asset_id: int, db: Session = Depends(get_db)):
    db_asset = crud.delete_asset(db, asset_id=asset_id)
    if not db_asset:
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

@router.get("/{asset_id}/transactions", response_model=List[schemas.Transaction])
def list_transactions_for_asset(asset_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_asset = crud.get_asset(db, asset_id=asset_id)
    if db_asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    transactions = crud.get_transactions(db=db, asset_id=asset_id, skip=skip, limit=limit)
    return transactions
</file>

### **New File: `tests/test_market_data_agent.py`**
* **Path:** `tests/test_market_data_agent.py`
<file path="tests/test_market_data_agent.py">
from unittest.mock import patch, MagicMock
from app.agents import market_data_agent
from decimal import Decimal

# Helper to create a mock yfinance history object
def create_mock_history(price: float | None):
    import pandas as pd
    if price is None:
        return pd.DataFrame({'Close': []})
    return pd.DataFrame({'Close': [price]})

@patch('yfinance.Ticker')
def test_get_current_price_success(mock_yf_ticker):
    # Arrange
    market_data_agent._cache.clear()
    mock_instance = MagicMock()
    mock_instance.history.return_value = create_mock_history(150.75)
    mock_yf_ticker.return_value = mock_instance
    
    # Act
    price = market_data_agent.get_current_price("AAPL")
    
    # Assert
    assert price == Decimal("150.75")
    mock_yf_ticker.assert_called_with("AAPL")
    mock_instance.history.assert_called_with(period="1d")

@patch('yfinance.Ticker')
def test_get_current_price_not_found(mock_yf_ticker):
    # Arrange
    market_data_agent._cache.clear()
    mock_instance = MagicMock()
    mock_instance.history.return_value = create_mock_history(None) # Empty DataFrame
    mock_yf_ticker.return_value = mock_instance
    
    # Act
    price = market_data_agent.get_current_price("INVALIDTICKER")
    
    # Assert
    assert price is None

@patch('yfinance.Ticker')
def test_get_current_price_caching(mock_yf_ticker):
    # Arrange
    market_data_agent._cache.clear()
    mock_instance = MagicMock()
    mock_instance.history.return_value = create_mock_history(200.0)
    mock_yf_ticker.return_value = mock_instance
    
    # Act: Call the function twice
    price1 = market_data_agent.get_current_price("GOOG")
    price2 = market_data_agent.get_current_price("GOOG")
    
    # Assert
    assert price1 == Decimal("200.00")
    assert price2 == Decimal("200.00")
    # The yfinance Ticker should only have been called ONCE due to caching
    mock_yf_ticker.assert_called_once_with("GOOG")
</file>

### **New File: `tests/test_portfolio_analyzer_agent.py`**
* **Path:** `tests/test_portfolio_analyzer_agent.py`
<file path="tests/test_portfolio_analyzer_agent.py">
from sqlalchemy.orm import Session
from unittest.mock import patch
from datetime import date
from decimal import Decimal

from app.agents import portfolio_analyzer_agent
from app import crud, schemas

def test_analyze_asset_full_scenario(db_session: Session):
    # Arrange: Create the asset, transactions, and dividends in the test DB
    asset_schema = schemas.AssetCreate(ticker="TEST4.SA", name="Test Asset", asset_type="STOCK", sector="Testing")
    asset = crud.create_asset(db=db_session, asset=asset_schema)

    trans1_schema = schemas.TransactionCreate(asset_id=asset.id, quantity=100, price=Decimal("10.00"), transaction_date=date(2025, 1, 15))
    crud.create_asset_transaction(db=db_session, transaction=trans1_schema)
    
    trans2_schema = schemas.TransactionCreate(asset_id=asset.id, quantity=50, price=Decimal("12.00"), transaction_date=date(2025, 2, 20))
    crud.create_asset_transaction(db=db_session, transaction=trans2_schema)

    div1_schema = schemas.DividendCreate(asset_id=asset.id, amount_per_share=Decimal("0.50"), payment_date=date(2025, 3, 10))
    crud.create_asset_dividend(db=db_session, dividend=div1_schema)

    # Mock the external price agent
    with patch('app.agents.market_data_agent.get_current_price') as mock_get_price:
        mock_get_price.return_value = Decimal("15.00")  # Set a mock current market price

        # Act: Run the analysis
        analysis = portfolio_analyzer_agent.analyze_asset(db=db_session, asset=asset)

        # Assert: Check all calculations
        assert analysis.ticker == "TEST4.SA"
        assert analysis.total_quantity == 150.0
        
        # total_cost = (100 * 10) + (50 * 12) = 1600
        # total_shares_bought = 150
        # average_price = 1600 / 150 = 10.666... -> rounded to 10.67
        assert analysis.average_price == Decimal("10.67")
        
        # total_invested = 150 * 10.67 = 1600.50
        assert analysis.total_invested == Decimal("1600.50")

        # total_dividends = 0.50 * 150 = 75
        assert analysis.total_dividends_received == Decimal("75.00")

        assert analysis.current_market_price == Decimal("15.00")
        
        # current_market_value = 150 * 15.00 = 2250.00
        assert analysis.current_market_value == Decimal("2250.00")

        # financial_return_value = 2250.00 - 1600.50 = 649.50
        assert analysis.financial_return_value == Decimal("649.50")
        
        # return_percent = (649.50 / 1600.50) * 100 = 40.581... -> rounded to 40.58
        assert analysis.financial_return_percent == Decimal("40.58")
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
* `POST /assets/`: Create a new financial asset.
* `GET /assets/`: List all assets (can filter by `ticker`).
* `GET /assets/{asset_id}`: Retrieve an asset by its ID.
* `PUT /assets/{asset_id}`: Update an asset's details.
* `DELETE /assets/{asset_id}`: Delete an asset.
* `GET /assets/{asset_id}/transactions`: List all transactions for a specific asset.
* `POST /transactions/`: Add a new transaction for an asset (requires `asset_id`).
* `GET /transactions/`: List all transactions in the system.
* `GET /transactions/{transaction_id}`: Get a specific transaction by its ID.
* `PUT /transactions/{transaction_id}`: Update a transaction.
* `DELETE /transactions/{transaction_id}`: Delete a transaction.
* `POST /dividends/`: Add a new dividend payment (requires `asset_id`).
* `GET /dividends/{dividend_id}`: Get a specific dividend payment.
* `PUT /dividends/{dividend_id}`: Update a dividend payment.
* `DELETE /dividends/{dividend_id}`: Delete a dividend payment.

### Analysis Endpoints
* `GET /assets/{ticker}/price`: Retrieve the current market price for an asset.
* `GET /assets/{ticker}/analysis`: Retrieve a complete financial analysis for an asset.

## Common Commands
# ... (rest of README is the same)
</file>
