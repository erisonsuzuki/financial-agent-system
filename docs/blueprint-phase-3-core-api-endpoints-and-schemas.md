# Implementation Blueprint: Phase 3 - Core API Endpoints and Schemas

## 1. Objective
To implement API endpoints for creating and retrieving `Assets`. This involves defining Pydantic schemas for data validation, separating database logic into a CRUD layer, creating an API Router to organize the endpoints, and writing a full suite of unit tests for the new functionality.

## 2. Consolidated Execution Checklist
-   [x] Create the new directory `app/routers/` and an empty `app/routers/__init__.py`.
-   [x] Create the new file `app/crud.py`.
-   [x] Create the new file `app/routers/assets.py`.
-   [x] Populate the `app/schemas.py` file with the required Pydantic classes.
-   [x] Update the `app/main.py` file to include the new assets router.
-   [x] Create the new test file `tests/test_assets.py` with tests for the new endpoints.
-   [x] Run `make up` to apply the changes (it will rebuild if necessary).
-   [x] Run `make test` to ensure all new and existing tests pass.

---
## 3. File Contents

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
</file>

### **File: `app/crud.py`**
* **Path:** `app/crud.py`
<file path="app/crud.py">
from sqlalchemy.orm import Session
from . import models, schemas

def get_asset_by_ticker(db: Session, ticker: str) -> models.Asset | None:
    return db.query(models.Asset).filter(models.Asset.ticker == ticker).first()

def create_asset(db: Session, asset: schemas.AssetCreate) -> models.Asset:
    db_asset = models.Asset(**asset.model_dump())
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset
</file>

### **File: `app/routers/assets.py`**
* **Path:** `app/routers/assets.py`
<file path="app/routers/assets.py">
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, schemas
from app.database import get_db

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
</file>

### **File: `app/main.py` (Updated for Phase 3)**
* **Path:** `app/main.py`
<file path="app/main.py">
from fastapi import FastAPI, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app import models
from app.database import engine, SessionLocal
from app.routers import assets

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Financial Agent System",
    description="API for managing financial assets with LLM agents.",
    version="0.1.0"
)

app.include_router(assets.router)

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

### **New File: `tests/test_assets.py`**
* **Path:** `tests/test_assets.py`
<file path="tests/test_assets.py">
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

def test_create_asset_success(client: TestClient):
    response = client.post(
        "/assets/",
        json={"ticker": "ITSA4", "name": "ITAU SA", "asset_type": "STOCK", "sector": "Financial"},
    )
    data = response.json()
    assert response.status_code == 201
    assert data["ticker"] == "ITSA4"
    assert data["name"] == "ITAU SA"
    assert "id" in data

def test_create_asset_duplicate_ticker(client: TestClient):
    # First, create an initial asset
    asset_data = {"ticker": "WEGE3", "name": "WEG SA", "asset_type": "STOCK", "sector": "Industrial"}
    response_1 = client.post("/assets/", json=asset_data)
    assert response_1.status_code == 201

    # Now, try to create it again
    response_2 = client.post("/assets/", json=asset_data)
    assert response_2.status_code == 400
    assert response_2.json() == {"detail": "Asset with this ticker already exists"}

def test_read_asset_success(client: TestClient):
    # First, create an asset to read
    asset_data = {"ticker": "MGLU3", "name": "MAGAZINE LUIZA", "asset_type": "STOCK"}
    client.post("/assets/", json=asset_data)

    # Now, read it
    response = client.get("/assets/MGLU3")
    data = response.json()
    assert response.status_code == 200
    assert data["ticker"] == "MGLU3"
    assert data["name"] == "MAGAZINE LUIZA"
    assert "id" in data

def test_read_asset_not_found(client: TestClient):
    response = client.get("/assets/NONEXISTENT")
    assert response.status_code == 404
    assert response.json() == {"detail": "Asset not found"}
</file>
