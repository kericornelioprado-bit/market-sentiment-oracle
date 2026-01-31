FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set environment variables
ENV UV_SYSTEM_PYTHON=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/app/cache/huggingface
ENV MPLCONFIGDIR=/app/cache/matplotlib

# Set the working directory
WORKDIR /app

# Copy dependency files and install dependencies to leverage Docker layer caching
COPY pyproject.toml uv.lock ./ 
RUN uv sync

# Create a non-root user and cache directories
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/cache/huggingface /app/cache/matplotlib && \
    chown -R appuser:appuser /app

# Copy the rest of the application code with ownership
COPY --chown=appuser:appuser src/ src/

# Switch to the non-root user
USER appuser

# Command to run the bot
CMD ["python", "-m", "src.execution.bot"]
