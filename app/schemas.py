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
