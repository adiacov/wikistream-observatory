FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/services/processor:/app/src

WORKDIR /app

COPY pyproject.toml README.md* ./
COPY src ./src
COPY services/processor ./services/processor

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e .

CMD ["python", "-m", "wikistream_processor.main"]
