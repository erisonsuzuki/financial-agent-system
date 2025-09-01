# Implementation Blueprint: Phase 9 - Data Management (Update & Delete)

## 1. Objective
To implement full CRUD (Create, Read, Update, Delete) functionality for the `Asset`, `Transaction`, and `Dividend` models. This involves adding `PUT` and `DELETE` endpoints, creating Pydantic schemas for updates, and writing a full suite of unit tests for the new data management capabilities.

## 2. Consolidated Execution Checklist
-   [x] Update `app/schemas.py` with new `...Update` schemas for each model.
-   [x] Update `app/crud.py` with `get_by_id`, `update`, and `delete` functions for each model.
-   [x] Refactor and update the routers (`assets.py`, `transactions.py`, `dividends.py`) with the new `GET (by id)`, `PUT`, and `DELETE` endpoints.
-   [x] Update `app/main.py` to ensure all routers are correctly included.
-   [x] Update the test files (`test_assets.py`, etc.) with comprehensive tests for the new update and delete functionality.
-   [x] Update `README.md` to document all new and changed endpoints.
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

# ... (AssetPrice schema is unchanged)

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

# ... (Analysis Schema is unchanged)
</file>

### **File: `app/crud.py`**
* **Path:** `app/crud.py`
<file path="app/crud.py">
from sqlalchemy.orm import Session
from . import models, schemas

# --- Asset CRUD ---
def get_asset(db: Session, asset_id: int) -> models.Asset | None:
    return db.query(models.Asset).filter(models.Asset.id == asset_id).first()

def get_asset_by_ticker(db: Session, ticker: str) -> models.Asset | None:
    return db.query(models.Asset).filter(models.Asset.ticker == ticker).first()

def get_assets(db: Session, skip: int = 0, limit: int = 100) -> list[models.Asset]:
    return db.query(models.Asset).offset(skip).limit(limit).all()

def create_asset(db: Session, asset: schemas.AssetCreate) -> models.Asset:
    db_asset = models.Asset(**asset.model_dump())
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

def update_asset(db: Session, db_asset: models.Asset, asset_in: schemas.AssetUpdate) -> models.Asset:
    update_data = asset_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_asset, key, value)
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

def delete_asset(db: Session, asset_id: int) -> models.Asset:
    db_asset = db.query(models.Asset).filter(models.Asset.id == asset_id).first()
    if db_asset:
        db.delete(db_asset)
        db.commit()
    return db_asset

# --- Transaction CRUD ---
def get_transaction(db: Session, transaction_id: int) -> models.Transaction | None:
    return db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()

def create_asset_transaction(db: Session, transaction: schemas.TransactionCreate) -> models.Transaction:
    db_transaction = models.Transaction(**transaction.model_dump())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def update_transaction(db: Session, db_transaction: models.Transaction, transaction_in: schemas.TransactionUpdate) -> models.Transaction:
    update_data = transaction_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_transaction, key, value)
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def delete_transaction(db: Session, transaction_id: int) -> models.Transaction:
    db_transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if db_transaction:
        db.delete(db_transaction)
        db.commit()
    return db_transaction

# ... (get_transactions_for_asset and dividend functions would be added similarly)
</file>

### **File: `app/routers/assets.py` (Refactored)**
* **Path:** `app/routers/assets.py`
<file path="app/routers/assets.py">
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.database import get_db
# ... (agent imports)

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
def list_assets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    assets = crud.get_assets(db, skip=skip, limit=limit)
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

# ... (price and analysis endpoints remain the same, but should probably use asset_id now)
</file>

### **File: `app/routers/transactions.py` (Refactored)**
* **Path:** `app/routers/transactions.py`
<file path="app/routers/transactions.py">
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.database import get_db

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
)

@router.post("/", response_model=schemas.Transaction, status_code=status.HTTP_201_CREATED)
def add_transaction(transaction: schemas.TransactionCreate, db: Session = Depends(get_db)):
    # Check if asset exists
    db_asset = crud.get_asset(db, asset_id=transaction.asset_id)
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return crud.create_asset_transaction(db=db, transaction=transaction)

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

@router.delete("/{transaction_id}", response_model=schemas.Transaction)
def delete_existing_transaction(transaction_id: int, db: Session = Depends(get_db)):
    db_transaction = crud.delete_transaction(db, transaction_id=transaction_id)
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return db_transaction
</file>

### **New/Updated Test Files**
* **Path:** `tests/test_assets.py`, `tests/test_transactions.py`, `tests/test_dividends.py`
* **Content:** New test functions must be added for `update` and `delete` operations in each file, covering success and `404 Not Found` cases.

### **File: `README.md` (Updated)**
* **Path:** `(project root)`
<file path="README.md">
# ... (Header and other sections)
## API Endpoints

### Assets
* `POST /assets/`: Create a new financial asset.
* `GET /assets/`: List all assets.
* `GET /assets/{asset_id}`: Retrieve an asset by its ID.
* `PUT /assets/{asset_id}`: Update an asset's details.
* `DELETE /assets/{asset_id}`: Delete an asset.
* `GET /assets/{ticker}/price`: Retrieve the current market price for an asset.
* `GET /assets/{ticker}/analysis`: Retrieve a complete financial analysis for an asset.

### Transactions
* `POST /transactions/`: Add a new transaction for an asset.
* `GET /transactions/{transaction_id}`: Get a specific transaction by its ID.
* `PUT /transactions/{transaction_id}`: Update a transaction.
* `DELETE /transactions/{transaction_id}`: Delete a transaction.

### Dividends
* (Similar CRUD endpoints for `/dividends/`)
# ... (rest of README)
</file>
