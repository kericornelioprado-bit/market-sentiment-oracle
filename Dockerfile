FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set environment variable for uv to install dependencies directly into the system environment
ENV UV_SYSTEM_PYTHON=1

# Set the working directory
WORKDIR /app

# Copy dependency files and install dependencies to leverage Docker layer caching
COPY pyproject.toml uv.lock ./ 
RUN uv sync

# Copy the rest of the application code
COPY src/ src/

# Command to run the bot
CMD ["python", "-m", "src.execution.bot"]
