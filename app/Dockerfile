FROM python:3.11-slim

# Set a new working directory that is the PARENT of our app code
WORKDIR /code

# Install patched bootstrap tooling and the reviewed Poetry release.
RUN pip install --no-cache-dir pip==26.2.1 setuptools==83.0.0 poetry==2.4.2

# Copy only dependency files to leverage Docker layer caching
COPY app/pyproject.toml app/poetry.lock /code/app/

# Set the working directory to our app's location
WORKDIR /code/app

# Install the committed dependency graph, including development dependencies used by tests.
RUN poetry config virtualenvs.create false && poetry install --no-root

# Copy the rest of the application code
COPY ./app /code/app
RUN chmod +x /code/app/scripts/start-api.sh

# Set the working directory back to the parent
WORKDIR /code

# Run migrations before starting API
CMD ["/code/app/scripts/start-api.sh"]
