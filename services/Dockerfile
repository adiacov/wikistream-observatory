# syntax=docker/dockerfile:1.7

ARG PYTHON_IMAGE=python:3.12-slim
ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.9.13

FROM ${UV_IMAGE} AS uv
FROM ${PYTHON_IMAGE} AS deps

COPY --from=uv /uv /uvx /usr/local/bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/tmp/uv-cache \
    UV_PROJECT_ENVIRONMENT=/usr/local \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Keep this dependency layer independent from source/docs changes. BuildKit's
# cache mount reuses downloaded wheels across cold dependency-layer rebuilds.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/tmp/uv-cache \
    uv sync --frozen --no-dev --no-install-project \
    && rm -f /usr/local/bin/uv /usr/local/bin/uvx

FROM ${PYTHON_IMAGE} AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=deps /usr/local /usr/local
COPY src ./src

FROM runtime AS ingestor
ENV PYTHONPATH=/app/services/ingestor:/app/src
COPY services/ingestor ./services/ingestor
CMD ["python", "-m", "wikistream_ingestor.main"]

FROM runtime AS processor
ENV PYTHONPATH=/app/services/processor:/app/src
COPY services/processor ./services/processor
CMD ["python", "-m", "wikistream_processor.main"]

FROM runtime AS dashboard
ENV PYTHONPATH=/app/services/dashboard:/app/src \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501
COPY services/dashboard ./services/dashboard
EXPOSE 8501
CMD ["streamlit", "run", "services/dashboard/app/main.py", "--server.address=0.0.0.0", "--server.port=8501"]
