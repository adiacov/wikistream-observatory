FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.13 /uv /uvx /usr/local/bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/services/dashboard:/app/src \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501 \
    UV_CACHE_DIR=/tmp/uv-cache \
    UV_PROJECT_ENVIRONMENT=/usr/local \
    UV_COMPILE_BYTECODE=1

WORKDIR /app

COPY pyproject.toml uv.lock README.md* ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
COPY services/dashboard ./services/dashboard

RUN uv sync --frozen --no-dev --no-editable \
    && rm -rf /tmp/uv-cache \
    && rm -f /usr/local/bin/uv /usr/local/bin/uvx

EXPOSE 8501

CMD ["streamlit", "run", "services/dashboard/app/main.py", "--server.address=0.0.0.0", "--server.port=8501"]
