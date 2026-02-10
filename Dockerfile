# ==========================================
# ETAPA 1: Builder (Resolución Fresca de CPU)
# ==========================================
FROM python:3.12-slim-bookworm as builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Variables para optimización
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# 1. COPIAMOS SOLO pyproject.toml
# CRÍTICO: NO copiamos uv.lock. Queremos que Docker olvide lo que tienes instalado localmente.
COPY pyproject.toml ./

# 2. Creamos el venv
RUN uv venv /app/.venv

# 3. GENERAMOS UN NUEVO requirements.txt FORZANDO CPU
# Usamos 'uv pip compile' para resolver las dependencias 'en el momento'
# buscando específicamente en el repositorio de CPU.
RUN uv pip compile pyproject.toml \
    --output-file requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    --index-strategy unsafe-best-match

# 4. INSTALAMOS DESDE ESE ARCHIVO LIMPIO
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

RUN uv pip install \
    --no-cache \
    -r requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    --index-strategy unsafe-best-match

# ==========================================
# ETAPA 2: Runtime (Igual que antes)
# ==========================================
FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/app/cache/huggingface \
    MPLCONFIGDIR=/app/cache/matplotlib \
    PATH="/app/.venv/bin:$PATH"

RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    mkdir -p /app/cache/huggingface /app/cache/matplotlib && \
    chown -R appuser:appuser /app

# Copiamos el entorno virtual LIMPIO (Solo CPU)
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --chown=appuser:appuser src/ src/

USER appuser

CMD ["python", "-m", "src.execution.bot"]