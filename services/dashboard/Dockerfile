FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.13 /uv /uvx /usr/local/bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/services/dashboard:/app/src \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501 \
    UV_CACHE_DIR=/tmp/uv-cache

WORKDIR /app

COPY pyproject.toml uv.lock README.md* ./
COPY src ./src
COPY services/dashboard ./services/dashboard

RUN uv export --frozen --no-dev --no-emit-project --format requirements.txt --output-file /tmp/requirements.txt >/dev/null \
    && uv pip install --system --no-cache -r /tmp/requirements.txt \
    && uv pip install --system --no-cache --no-deps -e . \
    && rm -rf /tmp/requirements.txt /tmp/uv-cache \
    && rm -f /usr/local/bin/uv /usr/local/bin/uvx

EXPOSE 8501

CMD ["streamlit", "run", "services/dashboard/app/main.py", "--server.address=0.0.0.0", "--server.port=8501"]
