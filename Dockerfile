# ETAPA 1: Builder (Usa la imagen oficial de astral-sh/uv con Python 3.12)
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 
ENV UV_LINK_MODE=copy
# Forzamos a uv a usar Python 3.12 para cumplir con tu pyproject.toml
ENV UV_PYTHON=python3.12

WORKDIR /app

# Copiamos dependencias
COPY pyproject.toml uv.lock ./

# Instalamos dependencias
RUN uv sync --frozen --no-install-project --no-dev

# Copiamos código fuente
COPY . .

# Instalamos el proyecto
RUN uv sync --frozen --no-dev

# ETAPA 2: Runtime (Actualizado a Python 3.12)
FROM python:3.12-slim-bookworm

# Copiamos el entorno virtual desde el builder
COPY --from=builder /app/.venv /app/.venv

# Agregamos el venv al PATH
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Crear usuario no-root
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/data && \
    chown -R appuser:appuser /app

# Copiamos el código fuente limpio con permisos
COPY --chown=appuser:appuser src/ src/
COPY --chown=appuser:appuser infra/ infra/

# Cambiar al usuario no-root
USER appuser

# Comando por defecto
CMD ["python", "src/data/ingest_news.py"]
