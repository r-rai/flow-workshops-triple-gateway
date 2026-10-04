import asyncio
import json
import logging
import os
import signal
from aiokafka import AIOKafkaConsumer
from temporalio.client import Client
from temporalio.exceptions import WorkflowAlreadyStartedError
from temporalio.common import WorkflowIDReusePolicy
from src.worker.workflow import DisputeResolutionWorkflow, DisputeInput

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [KafkaConsumer] %(message)s")
logger = logging.getLogger("kafka_consumer")

async def run_consumer():
    kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    topic = os.getenv("DISPUTES_TOPIC", "flobank.disputes")
    group_id = os.getenv("KAFKA_GROUP_ID", "flobank-dispute-workers")
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    
    logger.info(f"Connecting to Temporal at {temporal_host}...")
    temporal_client = await Client.connect(temporal_host)
    logger.info("Connected to Temporal.")

    logger.info(f"Connecting to Kafka at {kafka_servers}, topic: {topic}...")
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=kafka_servers,
        group_id=group_id,
        enable_auto_commit=False, # Crucial: manual commit after workflow start
        auto_offset_reset="earliest",
        value_deserializer=lambda m: json.loads(m.decode("utf-8"))
    )

    connected = False
    for attempt in range(30):
        try:
            await consumer.start()
            logger.info(f"Kafka consumer started successfully on topic '{topic}'.")
            connected = True
            break
        except Exception as e:
            logger.info(f"Waiting for Kafka broker ({e})... attempt {attempt + 1}/30")
            await asyncio.sleep(2)

    if not connected:
        logger.error("Could not connect to Kafka after 30 attempts. Exiting.")
        return

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except (NotImplementedError, RuntimeError):
            pass

    try:
        while not stop_event.is_set():
            try:
                msg = await asyncio.wait_for(consumer.getone(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            from aiokafka import TopicPartition
            tp = TopicPartition(msg.topic, msg.partition)

            event_data = msg.value
            case_id = event_data.get("case_id")
            if not case_id:
                logger.error(f"Malformed event missing case_id: {event_data}")
                await consumer.commit({tp: msg.offset + 1})
                continue

            workflow_id = f"dispute-case-{case_id}"
            logger.info(f"Received dispute event for {case_id} (offset {msg.offset}). Initiating workflow '{workflow_id}'...")

            started = False
            for retry in range(10):
                if stop_event.is_set():
                    break
                try:
                    # Start workflow with REJECT_DUPLICATE policy to enforce idempotency
                    handle = await temporal_client.start_workflow(
                        DisputeResolutionWorkflow.run,
                        DisputeInput(case_id=case_id),
                        id=workflow_id,
                        task_queue="dispute-resolution-queue",
                        id_reuse_policy=WorkflowIDReusePolicy.ALLOW_DUPLICATE_FAILED_ONLY
                    )
                    logger.info(f"Started new workflow run: {handle.run_id} for {workflow_id}")
                    started = True
                    break
                except WorkflowAlreadyStartedError:
                    logger.info(f"Workflow '{workflow_id}' is already running or completed. Reusing existing workflow.")
                    started = True
                    break
                except Exception as e:
                    logger.error(f"Failed to start workflow for {workflow_id} (attempt {retry + 1}/10): {e}")
                    await asyncio.sleep(min(0.5 * (2 ** retry), 5.0))

            if not started:
                logger.error(f"Unrecoverable or interrupted workflow start for offset {msg.offset}. Seeking back partition {tp} to offset {msg.offset} to prevent event loss.")
                consumer.seek(tp, msg.offset)
                await asyncio.sleep(2)
                continue

            # Invariant: Commit explicit Kafka offset ONLY after workflow start is accepted or existing confirmed
            await consumer.commit({tp: msg.offset + 1})
            logger.info(f"Committed Kafka offset {msg.offset + 1} for topic {topic}.")


    finally:
        logger.info("Stopping Kafka consumer...")
        await consumer.stop()
        logger.info("Kafka consumer stopped.")

if __name__ == "__main__":
    asyncio.run(run_consumer())
