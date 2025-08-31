# Implementation Blueprint: Phase 4 - MarketDataAgent and Price Fetching

## 1. Objective
To create a `MarketDataAgent` responsible for fetching real-time price data for financial assets from an external source (Yahoo Finance). This functionality will be exposed via a new API endpoint (`/assets/{ticker}/price`), will include a simple caching mechanism to improve performance, and will be fully covered by unit tests.

## 2. Consolidated Execution Checklist
-   [x] Update `app/pyproject.toml` to add the `yfinance` dependency.
-   [x] Create the new directory `app/agents/` and a new file `app/agents/market_data_agent.py`.
-   [x] Create an empty `app/agents/__init__.py` file.
-   [x] Update `app/schemas.py` with a new `AssetPrice` schema for the response.
-   [x] Update `app/routers/assets.py` with the new endpoint to get the asset price.
-   [x] Create a new test file `tests/test_market_data_agent.py` to test the agent's logic in isolation.
-   [x] Update `README.md` to document the new API endpoint.
-   [x] Run `make up` to install the new dependency and apply changes.
-   [x] Run `make test` to ensure all tests pass.

---
## 3. File Contents

### **File: `app/pyproject.toml`**
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
yfinance = "^0.2.38"

[tool.poetry.group.dev.dependencies]
pytest = "^8.2.2"
httpx = "^0.27.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
</file>

### **New File: `app/agents/market_data_agent.py`**
* **Path:** `app/agents/market_data_agent.py`
<file path="app/agents/market_data_agent.py">
import yfinance as yf
import time
from typing import Dict, Any

# Simple in-memory cache to avoid excessive API calls
# In a production system, this would be replaced by Redis, Memcached, etc.
_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 60 * 15  # 15 minutes

def get_current_price(ticker: str) -> float | None:
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
        
        # Update cache
        _cache[ticker] = {"price": price, "timestamp": current_time}
        
        return price
    except Exception:
        # Could be a network error or invalid ticker
        return None
</file>

### **File: `app/schemas.py`**
* **Path:** `app/schemas.py`
<file path="app/schemas.py">
from pydantic import BaseModel, ConfigDict
from app.models import AssetType
    
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
</file>

### **File: `app/routers/assets.py`**
* **Path:** `app/routers/assets.py`
<file path="app/routers/assets.py">
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, schemas
from app.database import get_db
from app.agents import market_data_agent

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
</file>

### **New File: `tests/test_market_data_agent.py`**
* **Path:** `tests/test_market_data_agent.py`
<file path="tests/test_market_data_agent.py">
import time
from unittest.mock import patch, MagicMock
from app.agents import market_data_agent

# Helper to create a mock yfinance history object
def create_mock_history(price: float):
    import pandas as pd
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
    assert price == 150.75
    mock_yf_ticker.assert_called_with("AAPL")
    mock_instance.history.assert_called_with(period="1d")

@patch('yfinance.Ticker')
def test_get_current_price_not_found(mock_yf_ticker):
    # Arrange
    market_data_agent._cache.clear()
    mock_instance = MagicMock()
    mock_instance.history.return_value = create_mock_history(None).dropna() # Empty DataFrame
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
    assert price1 == 200.0
    assert price2 == 200.0
    # The yfinance Ticker should only have been called ONCE due to caching
    mock_yf_ticker.assert_called_once_with("GOOG")
</file>

### **File: `README.md` (Corrected)**
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

### Prerequisites
- Docker and Docker Compose (or Docker Desktop)
- Make (optional, but recommended for using the provided commands)

### Setup
1.  **Clone the repository:** `git clone https://github.com/erisonsuzuki/financial_agent_system.git` and `cd financial_agent_system`

2.  **Create the environment file:** Copy the sample environment file with `cp .env.sample .env` and fill in your secrets.

3.  **Build and Run the Application:** Use the `make up` command to build the Docker images and start the services. The API will be available at `http://localhost:8000`.

4.  **Run Tests (Recommended):** Verify that the initial setup is correct by running `make test`.

## API Endpoints

### Assets
* `POST /assets/`: Create a new financial asset.
* `GET /assets/{ticker}`: Retrieve an asset by its ticker symbol.
* `GET /assets/{ticker}/price`: Retrieve the current market price for an asset.

## Testing
This project uses `pytest` for unit testing. The tests are located in the `tests/` directory.

To run the complete test suite, use the `make test` command.

The tests run against a separate, in-memory SQLite database for speed and isolation, ensuring they do not affect the main PostgreSQL database.

## Common Commands
- `make up`: Build and start all services (with hot reloading).
- `make down`: Stop and remove all services.
- `make clean`: Stop services, remove containers, volumes, and images for this project.
- `make logs`: View the logs from all running services.
- `make shell`: Access the shell of the running application container.
- `make db-shell`: Connect to a PostgreSQL shell inside the database container.
- `make test`: Run the unit test suite.
</file>
