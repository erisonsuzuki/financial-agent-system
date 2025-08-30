FROM python:3.11-slim

WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy dependency files to leverage Docker caching
COPY pyproject.toml poetry.lock* ./

# Install dependencies
# DEFINITIVE FIX: Explicitly install *only* the main dependency group.
RUN poetry config virtualenvs.create false && poetry install --no-root --only main

# Copy the rest of the application code
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
