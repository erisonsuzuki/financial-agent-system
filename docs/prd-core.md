# AI Operational Guide (PRD) - Core

## This document contains the central guidelines, workflows, and standards for this project.

## 1. Guideline: The Knowledge Base

### 1.1. Project Overview and Architecture

The project is an investment management system focused on Stocks and Real Estate Investment Trusts (REITs). The system's core is an AI agent architecture, designed to be modular and scalable.

* **Project Repository:** https://github.com/erisonsuzuki/financial_agent_system
* **Core Architecture:** The business logic is distributed among specialized agents, each with a unique responsibility (Market Data Fetching, Financial Calculations, Database Persistence, Report Generation).
* **Orchestration:** An orchestrator agent, implemented with LangGraph, manages the communication flow and the sequence of tasks among the other agents to fulfill user requests.
* **LLM Models:** The system is designed to be LLM-agnostic, allowing integration with cloud APIs (like Google Gemini) and local models (via Ollama) through LangChain's abstractions.

### 1.2. Code Standards and Tech Stack

This section outlines the technical standards and foundational principles for all development.

#### 1.2.1. Principle of Modern Stability

All technological choices—from language versions to libraries and architectural patterns—must prioritize the latest stable releases that are widely adopted and considered best practices by expert developers. We avoid bleeding-edge, beta, or deprecated technologies in favor of modern, proven, and secure solutions. This ensures our project is both current and maintainable.

#### 1.2.2. Core Technologies and Practices

* **Programming Language:** Python (latest stable release, e.g., 3.11+)
* **Dependency Management:** Poetry
* **Backend Framework:** FastAPI (for exposing APIs)
* **Database:** PostgreSQL (latest stable release, e.g., 15+)
* **Containerization:** Docker and Docker Compose
* **AI Libraries:** LangChain and LangGraph
* **Code Principles:** All development must follow industry best practices, including SOLID principles and Clean Code.
* **Comprehensive Testing:** All business logic (e.g., CRUD functions) and API endpoints must be accompanied by corresponding unit and integration tests. We will use the `pytest` framework for implementation. Tests will be isolated and run against a separate, in-memory test database to ensure they are fast and do not depend on external services. A `make test` command will be available to run the entire test suite.

### 1.3. Principle of Conciseness:
    - My objective is to be efficient. I must always prioritize clarity and simplicity.
    - The code proposed in Blueprints should focus on the essential logic.
    - My responses and documentation must be direct and without unnecessary verbosity.

## 2. Workflow: Our Mode of Operation

### 2.1. Task Lifecycle: Blueprint -> Internal Review -> Human Approval -> Implementation -> Learning
    
### 2.2. Internal Code Review & Verification
    - Before presenting any blueprint or code fix, I will perform a rigorous internal analysis to verify correctness, check for import errors, and ensure all parts of the code are consistent with our established architecture.
    - This proactive quality control step is designed to prevent errors and ensure that all proposals are functional and follow best practices.

### 2.3. Feedback and Learning Loop
    - After implementation, I must actively process all feedback, corrections, or suggestions.
    - Based on this feedback, I must identify learning opportunities and suggest updates to this `prd-core.md` to improve my future performance.

### 2.4. Living Documentation
    - At the conclusion of each implemented phase, the project's `README.md` file must be updated to reflect any new setup instructions, environment variables, or architectural decisions.

## 3. Output: Process Documentation Standard

### 3.1. Structure of the Final Implementation Report
### 3.2. Points to Include: Blueprint, Final Code, Tests, and Decisions Made

## 4. Lessons Learned 

### Lessons Learned from Phase 2

The implementation of the `/health` endpoint and its corresponding tests revealed important lessons about the interaction between FastAPI's dependency injection system and SQLAlchemy's session management.

* **Dependency Injection vs. Direct Instantiation:** While FastAPI's `Depends` system is powerful for managing dependencies in regular API endpoints, it can introduce complexity in specific scenarios like a health check. The initial implementation used `Depends(get_db)`, which made it difficult to correctly mock database failures in tests. The final solution was to instantiate the `SessionLocal` directly within the `health_check` function, giving us more granular control over the session's lifecycle and simplifying the testing of failure scenarios.

* **Mocking Strategy:** The test failures highlighted the importance of choosing the correct object to mock. Initially, the tests attempted to patch `sqlalchemy.orm.session.Session.execute`, which was too deep and did not correctly simulate a connection failure. The final, successful approach was to patch `app.main.SessionLocal` to control the behavior of the session creation itself.

* **SQLAlchemy 2.0 Deprecation:** The `declarative_base()` function has been moved from `sqlalchemy.ext.declarative` to `sqlalchemy.orm`. This is a simple but important change to keep the codebase up-to-date and avoid deprecation warnings.

These lessons will be applied to future development to ensure more robust and testable code.

### Lessons Learned from Phase 6 
The implementation of the `PortfolioAnalyzerAgent` revealed a critical issue regarding the precision of financial calculations in Python.

* **Floating-Point Imprecision:** Unit tests failed due to subtle inaccuracies in calculations using the standard `float` type and Python's default rounding behavior. For example, `round(40.625, 2)` results in `40.62`, not `40.63`. This level of imprecision is unacceptable for financial applications.
* **The `Decimal` Standard:** The correct solution, adopted as a new standard for this project, is to use Python's `Decimal` type for all monetary values and calculations. For database storage, the corresponding `Numeric` type from SQLAlchemy will be used. This ensures mathematical precision and predictable rounding, which are non-negotiable requirements for financial data. This led to the creation of a dedicated refactoring phase (Phase 7) to apply this standard across the entire application.

### Lessons Learned from Refactoring/Testing 

* **JSON Serialization of Decimals:** When FastAPI serializes Pydantic models containing `Decimal` types into JSON, it converts them to strings to preserve precision. Consequently, API tests that check these values in a JSON response must assert against the **string representation** of the decimal number (e.g., `assert data["price"] == "150.75"`), not the float or Decimal object itself.

### Lessons Learned from Phase 8
* **Modern Tool Definition in LangChain:** Initial deprecation warnings from LangChain's use of Pydantic V1 methods (`.parse_obj`, `.dict`) were observed. The root cause was the use of the `args_schema` parameter in the `@tool` decorator. The modern, correct, and Pydantic V2-compliant solution is to define tool arguments directly in the function signature using `typing.Annotated`. This approach is cleaner, more pythonic, and resolves the deprecation warnings. This is the standard for all tool definitions going forward.

* **Managing Log Noise from Third-Party Libraries:** Harmless but verbose warnings (e.g., `Key 'title' is not supported...`) were being emitted by internal LangChain loggers. The most robust and precise solution, rather than using broad filters or global log level changes, is to **identify the specific logger by its full name** (e.g., `langchain_google_genai._function_utils`) and **surgically set its log level** to a higher threshold (e.g., `logging.ERROR`). This is best managed in a centralized `app/logging_config.py` module, providing precise control over log noise without affecting desired application logs.
