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
