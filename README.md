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

4.  **Run Tests (Recommended):**
    Verify that the initial setup is correct by running the test suite.
    ```sh
    make test
    ```

## Testing
This project uses `pytest` for unit testing. The tests are located in the `tests/` directory.

To run the complete test suite, use the following command:
```sh
make test
```

The tests run against a separate, in-memory SQLite database for speed and isolation, ensuring they do not affect the main PostgreSQL database.

## Common Commands

  - `make up`: Build and start all services.
  - `make down`: Stop and remove all services.
  - `make clean`: Stop services, remove containers, volumes, and images for this project.
  - `make logs`: View the logs from all running services.
  - `make shell`: Access the shell of the running application container.
  - `make db-shell`: Connect to the PostgreSQL shell inside the database container.
  - `make test`: Run the unit test suite.
