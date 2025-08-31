# Financial Agent System

This project is an investment management system that uses an architecture of AI agents to perform financial calculations, data retrieval, and reporting.

## Tech Stack
- **Language:** Python 3.11+
- **Framework:** FastAPI
- **Database:** PostgreSQL
- **Containerization:** Docker
- **Dependency Management:** Poetry
- **Testing:** Pytest
- **AI:** LangChain, LangGraph

## Getting Started

### Prerequisites
- Docker and Docker Compose (or Docker Desktop)
- Make (optional, but recommended for using the provided commands)

### Setup
1.  **Clone the repository:** `git clone https://github.com/erisonsuzuki/financial_agent_system.git` and `cd financial_agent_system`

2.  **Create the environment file:** Copy the sample environment file with `cp .env.sample .env` and fill in your secrets.

3.  **Build and Run the Application:** Use the `make up` command to build the Docker images and start the services. The API will be available at `http://localhost:8000`.

4.  **Run Tests (Recommended):** Verify that the initial setup is correct by running `make test`.

## API Endpoints

### Assets
* `POST /assets/`: Create a new financial asset.
* `GET /assets/{ticker}`: Retrieve an asset by its ticker symbol.
* `GET /assets/{ticker}/price`: Retrieve the current market price for an asset.

## Testing
This project uses `pytest` for unit testing. The tests are located in the `tests/` directory.

To run the complete test suite, use the `make test` command.

The tests run against a separate, in-memory SQLite database for speed and isolation, ensuring they do not affect the main PostgreSQL database.

## Common Commands
- `make up`: Build and start all services (with hot reloading).
- `make down`: Stop and remove all services.
- `make clean`: Stop services, remove containers, volumes, and images for this project.
- `make logs`: View the logs from all running services.
- `make shell`: Access the shell of the running application container.
- `make db-shell`: Connect to a PostgreSQL shell inside the database container.
- `make test`: Run the unit test suite.
