FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.13 /uv /uvx /usr/local/bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/services/processor:/app/src \
    UV_CACHE_DIR=/tmp/uv-cache

WORKDIR /app

COPY pyproject.toml uv.lock README.md* ./
COPY src ./src
COPY services/processor ./services/processor

RUN uv export --frozen --no-dev --no-emit-project --format requirements.txt --output-file /tmp/requirements.txt >/dev/null \
    && uv pip install --system --no-cache -r /tmp/requirements.txt \
    && uv pip install --system --no-cache --no-deps -e . \
    && rm -rf /tmp/requirements.txt /tmp/uv-cache \
    && rm -f /usr/local/bin/uv /usr/local/bin/uvx

CMD ["python", "-m", "wikistream_processor.main"]
