FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set environment variable for uv to install dependencies directly into the system environment
ENV UV_SYSTEM_PYTHON=1
ENV MPLCONFIGDIR=/app/cache/matplotlib

# Set the working directory
WORKDIR /app

# Create a non-root user and setup directories
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/cache/matplotlib && \
    chown -R appuser:appuser /app

# Copy dependency files and install dependencies to leverage Docker layer caching
COPY --chown=appuser:appuser pyproject.toml uv.lock ./
RUN uv sync

# Copy the rest of the application code
COPY --chown=appuser:appuser src/ src/

# Switch to the non-root user
USER appuser

# Command to run the bot
CMD ["python", "-m", "src.execution.bot"]
