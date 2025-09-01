# Financial Agent System

This project is an investment management system that uses an architecture of AI agents to perform financial calculations, data retrieval, and reporting.

## Architecture Overview
This project utilizes an AI-driven, tool-based agent architecture powered by LangChain. The core idea is to separate the agent's logic, configuration, and capabilities.

### Core Components
* **Orchestrator Agent (`orchestrator_agent.py`):** This is the generic "engine". It's responsible for loading an agent's configuration, interpreting the user's natural language query, and managing the execution flow.
* **Agent Configurations (`app/agents/configs/*.yaml`):** These YAML files define the "personality" and capabilities of each agent. They specify the prompt (the agent's instructions), the tools it's allowed to use, and the LLM model it should connect to.
* **Tools (`tools.py`):** These are the specific Python functions that the LLM can decide to call. They act as the agent's "hands and eyes," allowing it to interact with our API, databases, or external services.

### Execution Flow
1.  A user sends a query to a named agent (e.g., `registration_agent`).
2.  The Orchestrator loads the corresponding `.yaml` config file.
3.  It combines the user's query with the prompt and tool definitions and sends them to the LLM.
4.  The LLM analyzes the request and decides which tool(s) to call and with which arguments.
5.  The Orchestrator executes the chosen tools (e.g., calls our own API to save data).
6.  The LLM receives the results from the tools and formulates a final, natural language answer for the user.

## Tech Stack
- **Language:** Python 3.11+
- **Framework:** FastAPI
- **Database:** PostgreSQL
- **Containerization:** Docker
- **Dependency Management:** Poetry
- **Testing:** Pytest
- **AI:** LangChain, PyYAML
- **Data Fetching:** yfinance

## Getting Started

### Environment Variables
Before running the application, copy `.env.sample` to `.env` and fill in the values:
* `POSTGRES_...`: Your database credentials.
* `LLM_PROVIDER`: The AI provider to use. Can be `google` or `ollama`.
* `GOOGLE_API_KEY`: Your API key if using Google Gemini.
* `GOOGLE_MODEL`: The Gemini model to use (e.g., `gemini-1.5-flash`, `gemini-1.5-pro`).
* `OLLAMA_BASE_URL`: The URL for your local Ollama server (e.g., `http://host.docker.internal:11434`).
* `OLLAMA_MODEL`: The name of the Ollama model to use (e.g., `llama3`).

### Setup and Running
1.  **Build and Run the Application:** Use `make up`. The API will be available at `http://localhost:8000`.
2.  **Run Tests (Recommended):** Verify the setup with `make test`.

## API Endpoints & Agent Interaction

### AI Agent
* `POST /agent/query/{agent_name}`: Send a natural language query to a specific AI agent.
  * **Registration Agent (`registration_agent`):**
    `make agent-register q="Register: 100 ITSA4 at R$10.50"`
  * **Management Agent (`management_agent`):**
    `make agent-manage q="Correct my last transaction for ITSA4, the price was R$10.75"`

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
* `POST /dividends/`: Add a new dividend for an asset.
* `GET /dividends/{dividend_id}`: Get a specific dividend by its ID.
* `PUT /dividends/{dividend_id}`: Update a dividend.
* `DELETE /dividends/{dividend_id}`: Delete a dividend.

## Common Commands
- `make up`: Build and start all services (with hot reloading).
- `make down`: Stop and remove all services.
- `make clean`: Stop services, remove containers, volumes, and images for this project.
- `make logs`: View the logs from all running services.
- `make shell`: Access the shell of the running application container.
- `make db-shell`: Connect to a PostgreSQL shell inside the database container.
- `make test`: Run the unit test suite.
- `make agent-register q="..."`: Send a query to the registration agent.
- `make agent-manage q="..."`: Send a query to the management agent.
