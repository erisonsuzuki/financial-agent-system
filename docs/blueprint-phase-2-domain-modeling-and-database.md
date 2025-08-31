# Implementation Blueprint: Phase 2 - Domain Modeling and Database (with Unit Tests)

## 1. Objective
To have a running application that successfully connects to a database, creates its tables on startup, and reports a healthy status via a `/health` endpoint. This baseline will be validated by a new, automated unit test suite.

## 2. Consolidated Execution Checklist
-   [x] Update the `pyproject.toml` and `Makefile` with the new testing configurations.
-   [x] Create the new `tests/` directory at the project root.
-   [x] Create the new testing files: `tests/conftest.py` and `tests/test_main.py`.
-   [x] Update the `app/Dockerfile` to ensure testing dependencies are installed.
-   [x] Run `make clean` and `make up` to ensure the new dependencies are installed and the application starts.
-   [x] Run `make test` to execute the unit tests and confirm they pass.
-   [x] Manually verify the `/health` endpoint at `http://localhost:8000/health`.

---
## 3. File Contents

### **File: `Makefile`**
* **Path:** `(project root)`
<file path="Makefile">
# Makefile
up:
	docker compose up -d --build

down:
	docker compose down

# STOPS containers, REMOVES persistent volumes, and REMOVES images for this project.
clean:
	docker compose down --volumes --rmi all

logs:
	docker compose logs -f

shell:
	docker compose exec app bash

test:
	docker compose exec app pytest
</file>

### **File: `docker-compose.yml`**
* **Path:** `(project root)`
<file path="docker-compose.yml">
services:
  app:
    build:
      context: .
      dockerfile: app/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./app:/code/app
      - ./tests:/code/tests
    depends_on:
      db:
        condition: service_healthy
    env_file:
      - .env

  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    env_file:
      - .env
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
</file>

### **File: `app/Dockerfile`**
* **Path:** `app/Dockerfile`
<file path="app/Dockerfile">
FROM python:3.11-slim

# Set a new working directory that is the PARENT of our app code
WORKDIR /code

# Install poetry
RUN pip install poetry

# Copy only dependency files to leverage Docker layer caching
COPY app/pyproject.toml app/poetry.lock* /code/app/

# Set the working directory to our app's location
WORKDIR /code/app

# Configure poetry, regenerate lock file, and install ALL dependencies (including dev for testing)
RUN poetry config virtualenvs.create false && poetry lock && poetry install --no-root

# Copy the rest of the application code
COPY ./app /code/app

# Set the working directory back to the parent
WORKDIR /code

# Command to run the application as a module
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
</file>

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

[tool.poetry.group.dev.dependencies]
pytest = "^8.2.2"
httpx = "^0.27.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
</file>

### **File: `app/database.py`**
* **Path:** `app/database.py`
<file path="app/database.py">
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

# Read database configuration from environment variables
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_HOST = "db" # This is the service name in docker-compose.yml

# Construct the database URL with the new psycopg3 dialect
DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get a DB session for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
</file>

### **File: `app/models.py`**
* **Path:** `app/models.py`
<file path="app/models.py">
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Enum as SQLAlchemyEnum
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
    price = Column(Float, nullable=False)
    transaction_date = Column(Date, nullable=False)
    asset = relationship("Asset", back_populates="transactions")

class Dividend(Base):
    __tablename__ = "dividends"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    amount_per_share = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=False)
    asset = relationship("Asset", back_populates="dividends")
</file>

### **File: `app/main.py`**
* **Path:** `app/main.py`
<file path="app/main.py">
from fastapi import FastAPI, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app import models
from app.database import engine, SessionLocal

# This line creates the tables on startup.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Financial Agent System",
    description="API for managing financial assets with LLM agents.",
    version="0.1.0"
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Financial Agent System is running!"}

@app.get("/health", status_code=status.HTTP_200_OK, tags=["Monitoring"])
def health_check(response: Response):
    db_status = "ok"
    db = SessionLocal()
    try:
        # Execute a simple query to check the database connection
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

### **File: `tests/conftest.py`**
* **Path:** `tests/conftest.py`
<file path="tests/conftest.py">
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Fixture to set up and tear down the database for each test function
@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

# Fixture to override the get_db dependency and provide a test client
@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]
</file>

### **File: `tests/test_main.py`**
* **Path:** `tests/test_main.py`
<file path="tests/test_main.py">
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


def test_read_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Financial Agent System is running!"}


def test_health_check_success(client: TestClient):
    with patch("app.main.SessionLocal") as mock_session_local:
        mock_db = MagicMock()
        mock_db.execute.return_value = None
        mock_session_local.return_value = mock_db
        
        response = client.get("/health")
        
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "details": {
            "database": {
                "status": "ok"
            }
        }
    }

def test_health_check_failure(client: TestClient):
    # Use patch to simulate a database connection error
    with patch("app.main.SessionLocal") as mock_session_local:
        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("Database connection failed")
        mock_session_local.return_value = mock_db
        response = client.get("/health")
    assert response.status_code == 503
    assert response.json() == {
        "status": "error",
        "details": {
            "database": {
                "status": "error"
            }
        }
    }
</file>
