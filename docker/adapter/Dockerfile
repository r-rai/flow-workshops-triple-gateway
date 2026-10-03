FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY docker/adapter/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/src

EXPOSE 8080

CMD ["uvicorn", "src.adapter.server:app", "--host", "0.0.0.0", "--port", "8080"]
