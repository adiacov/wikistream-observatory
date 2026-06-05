FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/services/dashboard:/app/src \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501

WORKDIR /app

COPY pyproject.toml README.md* ./
COPY src ./src
COPY services/dashboard ./services/dashboard

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e .

EXPOSE 8501

CMD ["streamlit", "run", "services/dashboard/app/main.py", "--server.address=0.0.0.0", "--server.port=8501"]
