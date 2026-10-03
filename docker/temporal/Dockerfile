FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir temporalio>=1.6.0

RUN mkdir -p /data

EXPOSE 7233

COPY src/worker/temporal_server.py /app/temporal_server.py

CMD ["python", "/app/temporal_server.py"]
