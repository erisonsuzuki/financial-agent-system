# Implementation Blueprint: Phase 1 - Foundation and Environment Setup

*This document is the action plan and implementation proposal that I should generate when starting a new task.*

---

### **1. Task Analysis and Implementation Phases**

* **Objective:** To create the project's skeleton, configure a secure development environment with Docker, create a `Makefile` for command automation, and establish initial project documentation with a `README.md`.
* **Phases:**
    1.  **Define Project Structure:** Organize the project into logical folders.
    2.  **Configure Environment and Orchestration:** Create `.env`, `.env.sample`, `.gitignore`, and `docker-compose.yml`.
    3.  **Create Command Automation:** Create a `Makefile` with common development commands.
    4.  **Create the Application `Dockerfile`:** Define the build instructions for the Python application.
    5.  **Configure Initial Dependencies:** Create the `pyproject.toml` file for Poetry.
    6.  **Create the Application Entrypoint:** Develop a minimal `main.py` to validate the setup.
    7.  **Create Initial Project Documentation:** Create the `README.md` file.

---

### **2. Code Proposal for Each Phase (Functional Code)**

#### **Phase 1: Define Project Structure**
* **Proposed Structure:**
    ```
    financial_agent_system/
    ├── app/
    │   ├── Dockerfile
    │   ├── pyproject.toml
    │   └── main.py
    ├── docs/
    │   ├── prd-core.md
    │   └── blueprint-phase-1-foundation-and-setup.md
    ├── .env
    ├── .env.sample
    ├── .gitignore
    ├── docker-compose.yml
    ├── Makefile
    └── README.md
    ```

#### **Phase 2: Configure Environment and Orchestration**
* **`.gitignore`**
    ```gitignore
    # Environment variables
    .env

    # Python artifacts
    __pycache__/
    *.pyc

    # Docker
    .dockerignore
    ```
* **`.env.sample`**
    ```env
    # PostgreSQL DB Connection
    POSTGRES_DB=financialdb
    POSTGRES_USER=user
    POSTGRES_PASSWORD=

    # Application DB URL
    DATABASE_URL=postgresql://user:password@db:5432/financialdb
    ```
* **`docker-compose.yml`**
    ```yaml
    version: '3.8'

    services:
      app:
        build: ./app
        ports:
          - "8000:8000"
        volumes:
          - ./app:/app
        depends_on:
          - db
        env_file:
          - .env

      db:
        image: postgres:15-alpine
        volumes:
          - postgres_data:/var/lib/postgresql/data/
        env_file:
          - .env

    volumes:
      postgres_data:
    ```

#### **Phase 3: Create Command Automation (`Makefile`)**
* **Proposed Code:**
    ```makefile
    # Makefile

    # Build and start the services in detached mode
    up:
        docker compose up -d --build

    # Stop and remove the services
    down:
        docker compose down

    # Show logs for all services
    logs:
        docker compose logs -f

    # Access the application container's shell
    shell:
        docker compose exec app bash
    ```

#### **Phase 4: Create the Application `Dockerfile`**
* **Proposed Code:**
    ```Dockerfile
    # app/Dockerfile
    FROM python:3.11-slim

    WORKDIR /app

    # Install poetry
    RUN pip install poetry

    # Copy dependency files to leverage Docker caching
    COPY pyproject.toml poetry.lock* ./

    # Install dependencies
    RUN poetry config virtualenvs.create false && poetry install --no-root --only main

    # Copy the rest of the application code
    COPY . .

    CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
    ```

#### **Phase 5: Configure Initial Dependencies (`pyproject.toml`)**
* **Proposed Code:**
    ```toml
    # app/pyproject.toml
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
    psycopg2-binary = "^2.9.9"

    [build-system]
    requires = ["poetry-core"]
    build-backend = "poetry.core.masonry.api"
    ```

#### **Phase 6: Create the Application Entrypoint (`main.py`)**
* **Proposed Code:**
    ```python
    # app/main.py
    from fastapi import FastAPI

    app = FastAPI(
        title="Financial Agent System",
        description="API for managing financial assets with LLM agents.",
        version="0.1.0"
    )

    @app.get("/")
    def read_root():
        return {"status": "ok", "message": "Financial Agent System is running!"}
    ```

#### **Phase 7: Create Initial Project Documentation (`README.md`)**
* **Proposed Code:**
    ```markdown
    # Financial Agent System

    This project is an investment management system that uses an architecture of AI agents to perform financial calculations, data retrieval, and reporting.

    ## Tech Stack

    - **Language:** Python 3.11+
    - **Framework:** FastAPI
    - **Database:** PostgreSQL
    - **Containerization:** Docker
    - **Dependency Management:** Poetry
    - **AI:** LangChain, LangGraph

    ## Getting Started

    ### Prerequisites

    - Docker and Docker Compose (or Docker Desktop)
    - Make (optional, but recommended for using the provided commands)

    ### Setup

    1.  **Clone the repository:**
        ```sh
        git clone https://github.com/erisonsuzuki/financial_agent_system.git
        cd financial_agent_system
        ```

    2.  **Create the environment file:**
        Copy the sample environment file and fill in your secrets (e.g., database password).
        ```sh
        cp .env.sample .env
        ```

    3.  **Build and Run the Application:**
        Use the `make` command to build the Docker images and start the services in the background.
        ```sh
        make up
        ```
        The API will be available at `http://localhost:8000`.

    ## Common Commands

    - `make up`: Build and start all services.
    - `make down`: Stop and remove all services.
    - `make logs`: View the logs from all running services.
    - `make shell`: Access the shell of the running application container.
    ```
---

### **4. Consolidated Execution Checklist**

* **Checklist:**
    - [x] Create `.gitignore`, `.env.sample`, and a filled `.env` file.
    - [x] Create the `docker-compose.yml` file.
    - [x] Create the `Makefile`.
    - [x] At the project root, create the `README.md` file.
    - [x] Create the `app/` subdirectory.
    - [x] Inside `app/`, create the `Dockerfile`.
    - [x] Inside `app/`, create the `pyproject.toml` file.
    - [x] Inside `app/`, run `poetry lock` to generate the `poetry.lock` file.
    - [x] Inside `app/`, create the `main.py` file.
    - [x] From the root, execute the validation scenario (run `make up`).
