# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Core Concepts

- **AI Agents as Controllers**: The system uses AI agents defined in YAML configuration files (`app/agents/configs/`) to drive its core logic. These agents are exposed via a FastAPI router (`app/routers/agent.py`).
- **Dynamic Tool Binding**: The `OrchestratorAgent` (`app/agents/orchestrator_agent.py`) dynamically binds tools to an agent based on its YAML configuration. This means an agent's capabilities are not hardcoded but are determined at runtime.
- **"Synthetic" Transactions**: When a user registers an asset position, the `register_asset_position` tool (`app/agents/tools.py`) creates a single "synthetic" transaction to represent the user's entire holding. This is a non-obvious pattern; the system does not import the user's full transaction history.

## Commands

- **Run the System**: `make up`
- **Run Tests**: `make test`
- **Query an Agent**: `make agent-register q="your question"` or `make agent-manage q="your question"`

## Testing

- **In-Memory Database**: Tests use an in-memory SQLite database, not Postgres. See `tests/conftest.py`.
- **Mocked Services**: Tests mock external services like the market data agent. When writing new tests, you must mock any external dependencies.
