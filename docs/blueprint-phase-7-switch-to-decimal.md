# Implementation Blueprint: Phase 7 - Refactoring for Financial Precision

## 1. Objective
To refactor the application to use Python's `Decimal` type for all monetary values and financial calculations, and SQLAlchemy's `Numeric` type for database storage. This eliminates floating-point inaccuracies and ensures all financial math is precise. This blueprint includes the final, correct versions of all tests affected by this change.

## 2. Consolidated Execution Checklist
-   [x] Update `app/models.py` to use `Numeric` instead of `Float`.
-   [x] Update `app/schemas.py` to use `Decimal` instead of `float`.
-   [x] Update `app/agents/portfolio_analyzer_agent.py` to perform all calculations using `Decimal`.
-   [x] Update or create all necessary test files (`test_transactions.py`, `test_dividends.py`, `test_portfolio_analyzer_agent.py`) to correctly handle and assert `Decimal` values (as strings in JSON responses).
-   [x] Run `make clean` to destroy the old database schema.
-   [x] Run `make up` to start the services and create the new, correct schema.
-   [x] Run `make test` to confirm that all calculations are correct and all tests pass.

---
## 3. File Contents

### **File: `app/models.py`**
* **Path:** `app/models.py`
<file path="app/models.py">
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Enum as SQLAlchemyEnum, Numeric
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class AssetType(str, enum.Enum):
    STOCK = "STOCK"
    REIT = "REIT"

class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    asset_type = Column(SQLAlchemyEnum(AssetType), nullable=False)
    sector = Column(String)
    transactions = relationship("Transaction", back_populates="asset")
    dividends = relationship("Dividend", back_populates="asset")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    transaction_date = Column(Date, nullable=False)
    asset = relationship("Asset", back_populates="transactions")

class Dividend(Base):
    __tablename__ = "dividends"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    amount_per_share = Column(Numeric(10, 4), nullable=False)
    payment_date = Column(Date, nullable=False)
    asset = relationship("Asset", back_populates="dividends")
</file>

### **File: `app/schemas.py`**
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

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    id: int
    asset_id: int
    model_config = ConfigDict(from_attributes=True)

# --- Dividend Schemas ---
class DividendBase(BaseModel):
    amount_per_share: Decimal
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
    average_price: Decimal
    total_invested: Decimal
    current_market_price: Decimal | None
    current_market_value: Decimal | None
    financial_return_value: Decimal | None
    financial_return_percent: Decimal | None
    total_dividends_received: Decimal
</file>

### **File: `app/agents/portfolio_analyzer_agent.py`**
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
    transactions = crud.get_transactions_for_asset(db=db, asset_id=asset.id, limit=10000)
    dividends = crud.get_dividends_for_asset(db=db, asset_id=asset.id, limit=10000)

    # Calculate portfolio state from transactions
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

    # Calculate total dividends
    total_dividends_received = sum(d.amount_per_share * total_quantity for d in dividends).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Fetch current market data
    price_float = market_data_agent.get_current_price(ticker=asset.ticker)
    current_market_price = Decimal(str(price_float)) if price_float is not None else None

    # Calculate metrics that depend on market data
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

### **File: `tests/test_transactions.py` (Updated for Decimal)**
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
        json={"quantity": 100, "price": "61.50", "transaction_date": str(date.today())}
    )
    data = response.json()
    assert response.status_code == 201
    assert data["quantity"] == 100
    assert data["price"] == "61.50"

def test_create_transaction_for_nonexistent_asset(client: TestClient):
    response = client.post(
        "/assets/NONEXISTENT/transactions/",
        json={"quantity": 100, "price": "10.00", "transaction_date": str(date.today())}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Asset not found"}

def test_list_transactions_for_asset(client: TestClient):
    # Create an asset and some transactions
    client.post("/assets/", json={"ticker": "BBDC4", "name": "BRADESCO", "asset_type": "STOCK"})
    client.post("/assets/BBDC4/transactions/", json={"quantity": 50, "price": "13.00", "transaction_date": "2025-01-15"})
    client.post("/assets/BBDC4/transactions/", json={"quantity": 25, "price": "13.50", "transaction_date": "2025-02-20"})

    # List the transactions
    response = client.get("/assets/BBDC4/transactions/")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 2
    assert data[0]["quantity"] == 50
    assert data[1]["price"] == "13.50"
</file>

### **File: `tests/test_dividends.py` (Updated for Decimal)**
* **Path:** `tests/test_dividends.py`
<file path="tests/test_dividends.py">
from fastapi.testclient import TestClient
from datetime import date

def test_create_dividend_for_asset(client: TestClient):
    # First, create an asset
    client.post("/assets/", json={"ticker": "ITUB4", "name": "ITAÚ UNIBANCO", "asset_type": "STOCK"})

    # Create a dividend for that asset
    response = client.post(
        "/assets/ITUB4/dividends/",
        json={"amount_per_share": "0.5120", "payment_date": str(date.today())}
    )
    data = response.json()
    assert response.status_code == 201
    assert data["amount_per_share"] == "0.5120"

def test_create_dividend_for_nonexistent_asset(client: TestClient):
    response = client.post(
        "/assets/NONEXISTENT/dividends/",
        json={"amount_per_share": "1.00", "payment_date": str(date.today())}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Asset not found"}

def test_list_dividends_for_asset(client: TestClient):
    # Create an asset and some dividends
    client.post("/assets/", json={"ticker": "PETR4", "name": "PETROBRAS", "asset_type": "STOCK"})
    client.post("/assets/PETR4/dividends/", json={"amount_per_share": "0.25", "payment_date": "2025-03-01"})
    client.post("/assets/PETR4/dividends/", json={"amount_per_share": "0.30", "payment_date": "2025-06-01"})

    # List the dividends
    response = client.get("/assets/PETR4/dividends/")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 2
    assert data[0]["amount_per_share"] == "0.2500"
    assert data[1]["amount_per_share"] == "0.3000"
</file>

### **File: `tests/test_portfolio_analyzer_agent.py`**
* **Path:** `tests/test_portfolio_analyzer_agent.py`
<file path="tests/test_portfolio_analyzer_agent.py">
from sqlalchemy.orm import Session
from unittest.mock import patch
from datetime import date
from decimal import Decimal

from app.agents import portfolio_analyzer_agent
from app import crud, schemas

def test_analyze_asset_full_scenario_with_decimal(db_session: Session):
    # Arrange: Create the asset, transactions, and dividends
    asset_schema = schemas.AssetCreate(ticker="TEST4.SA", name="Test Asset", asset_type="STOCK", sector="Testing")
    asset = crud.create_asset(db=db_session, asset=asset_schema)

    trans1_schema = schemas.TransactionCreate(quantity=100, price=Decimal("10.00"), transaction_date=date(2025, 1, 15))
    crud.create_asset_transaction(db=db_session, transaction=trans1_schema, asset_id=asset.id)
    
    trans2_schema = schemas.TransactionCreate(quantity=50, price=Decimal("12.00"), transaction_date=date(2025, 2, 20))
    crud.create_asset_transaction(db=db_session, transaction=trans2_schema, asset_id=asset.id)

    div1_schema = schemas.DividendCreate(amount_per_share=Decimal("0.50"), payment_date=date(2025, 3, 10))
    crud.create_asset_dividend(db=db_session, dividend=div1_schema, asset_id=asset.id)

    # Mock the external price agent
    with patch('app.agents.market_data_agent.get_current_price') as mock_get_price:
        mock_get_price.return_value = 15.00  # Returns a float, our agent will convert to Decimal

        # Act: Run the analysis
        analysis = portfolio_analyzer_agent.analyze_asset(db=db_session, asset=asset)

        # Assert: Check all calculations using Decimal
        assert analysis.ticker == "TEST4.SA"
        assert analysis.total_quantity == 150.0
        assert analysis.average_price == Decimal("10.67")
        assert analysis.total_invested == Decimal("1600.50")
        assert analysis.total_dividends_received == Decimal("75.00")
        assert analysis.current_market_price == Decimal("15.00")
        assert analysis.current_market_value == Decimal("2250.00")
        assert analysis.financial_return_value == Decimal("649.50")
        assert analysis.financial_return_percent == Decimal("40.58")
</file>
