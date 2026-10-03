import asyncio
import logging
import os
import signal
from temporalio.client import Client
from temporalio.worker import Worker
from src.worker.workflow import DisputeResolutionWorkflow
from src.worker.activities import (
    read_dispute_ticket,
    diagnose_and_propose_resolution,
    execute_settlement_and_notify
)
from src.worker.kafka_consumer import run_consumer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [Worker] %(message)s")
logger = logging.getLogger("worker_main")

async def run_worker():
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "dispute-resolution-queue")
    enable_kafka = os.getenv("ENABLE_KAFKA_CONSUMER", "true").lower() == "true"

    logger.info(f"Connecting Temporal worker to {temporal_host}...")
    
    # Wait for temporal to become available
    client = None
    for attempt in range(30):
        try:
            client = await Client.connect(temporal_host)
            logger.info("Connected to Temporal server successfully.")
            break
        except Exception as e:
            logger.info(f"Waiting for Temporal server ({e})... attempt {attempt + 1}/30")
            await asyncio.sleep(2)
            
    if not client:
        raise RuntimeError("Could not connect to Temporal server.")

    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[DisputeResolutionWorkflow],
        activities=[
            read_dispute_ticket,
            diagnose_and_propose_resolution,
            execute_settlement_and_notify
        ]
    )

    logger.info(f"Temporal worker initialized on task queue '{task_queue}'.")

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except (NotImplementedError, RuntimeError):
            pass

    tasks = [asyncio.create_task(worker.run())]
    if enable_kafka:
        logger.info("Starting background Kafka consumer task...")
        tasks.append(asyncio.create_task(run_consumer()))

    logger.info("Worker is running. Awaiting shutdown signal or termination...")
    await stop_event.wait()
    logger.info("Shutdown signal received. Cancelling worker tasks...")
    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("Worker shutdown complete.")

if __name__ == "__main__":
    asyncio.run(run_worker())
