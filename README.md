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

### Development Workflow 
This project is configured for hot reloading. Thanks to the `docker-compose.override.yml` file, when you run `make up`, the application server will automatically restart whenever you save changes to a Python file in the `app/` directory. You can view the reloading messages by running `make logs`.

## Testing
This project uses `pytest` for unit testing. The tests are located in the `tests/` directory.

To run the complete test suite, use the following command:
```sh
make test
```

The tests run against a separate, in-memory SQLite database for speed and isolation, ensuring they do not affect the main PostgreSQL database.

## Common Commands

  - `make up`: Build and start all services (with hot reloading).
  - `make down`: Stop and remove all services.
  - `make clean`: Stop services, remove containers, volumes, and images for this project.
  - `make logs`: View the logs from all running services.
  - `make shell`: Access the shell of the running application container.
  - `make db-shell`: Connect to the PostgreSQL shell inside the database container.
  - `make test`: Run the unit test suite.
