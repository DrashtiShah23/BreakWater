FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENABLE_TEST_CONTROLS=false

COPY pyproject.toml README.md ./
COPY app ./app

RUN pip install --no-cache-dir .

EXPOSE 8000

# SURFACE and UPSTREAM_INSTANCE_ID are provided by compose/runtime.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
