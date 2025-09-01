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
    asset_id: int
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
