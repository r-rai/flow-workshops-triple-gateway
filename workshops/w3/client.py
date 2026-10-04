import argparse
import asyncio
import json
import os
import sys
from aiokafka import AIOKafkaProducer
from temporalio.client import Client

async def emit_dispute(kafka_servers: str, case_id: str, customer_id: str = ""):
    print(f"[Kafka] Emitting dispute event for case '{case_id}' to topic 'novabank.disputes'...")
    producer = AIOKafkaProducer(bootstrap_servers=kafka_servers)
    await producer.start()
    try:
        payload = {
            "case_id": case_id,
            "customer_id": customer_id or "cust-101",
            "timestamp": "2026-10-03T10:14:00Z"
        }
        await producer.send_and_wait("novabank.disputes", json.dumps(payload).encode("utf-8"))
        print(f"[Kafka] Successfully emitted dispute event for '{case_id}'.")
    finally:
        await producer.stop()

async def query_workflow(temporal_host: str, case_id: str):
    workflow_id = f"dispute-case-{case_id}"
    print(f"[Temporal] Querying status of workflow '{workflow_id}'...")
    client = await Client.connect(temporal_host)
    handle = client.get_workflow_handle(workflow_id)
    try:
        status = await handle.query("get_status")
        print(f"[Temporal] Workflow '{workflow_id}' Status:")
        print(json.dumps(status, indent=2))
        return status
    except Exception as e:
        print(f"[Temporal] Error querying workflow '{workflow_id}': {e}")
        return None

async def signal_approval(temporal_host: str, case_id: str, approved: bool, reviewer: str, comments: str):
    workflow_id = f"dispute-case-{case_id}"
    decision_str = "APPROVE" if approved else "REJECT"
    print(f"[Temporal] Sending {decision_str} signal to workflow '{workflow_id}' by {reviewer}...")
    client = await Client.connect(temporal_host)
    handle = client.get_workflow_handle(workflow_id)
    decision = {
        "approved": approved,
        "reviewer": reviewer,
        "comments": comments
    }
    await handle.signal("human_approval", decision)
    print(f"[Temporal] Signal delivered. Awaiting completion...")
    result = await handle.result()
    print(f"[Temporal] Workflow '{workflow_id}' completed with result:")
    print(json.dumps(result, indent=2))
    return result

def main():
    parser = argparse.ArgumentParser(description="Flo Bank Workshop 3 CLI Client")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # emit
    emit_parser = subparsers.add_parser("emit", help="Emit dispute event to Kafka")
    emit_parser.add_argument("--case-id", required=True, help="Dispute case ID (e.g. case-501)")
    emit_parser.add_argument("--customer-id", default="cust-101", help="Customer ID")
    emit_parser.add_argument("--kafka", default="localhost:9092", help="Kafka broker address")

    # query
    query_parser = subparsers.add_parser("query", help="Query Temporal workflow state")
    query_parser.add_argument("--case-id", required=True, help="Dispute case ID")
    query_parser.add_argument("--temporal", default="localhost:7233", help="Temporal server address")

    # approve
    approve_parser = subparsers.add_parser("approve", help="Send human approval signal")
    approve_parser.add_argument("--case-id", required=True, help="Dispute case ID")
    approve_parser.add_argument("--reviewer", default="ops-lead", help="Reviewer identity")
    approve_parser.add_argument("--comments", default="Approved after reviewing audit log", help="Comments")
    approve_parser.add_argument("--temporal", default="localhost:7233", help="Temporal server address")

    # reject
    reject_parser = subparsers.add_parser("reject", help="Send human rejection signal")
    reject_parser.add_argument("--case-id", required=True, help="Dispute case ID")
    reject_parser.add_argument("--reviewer", default="ops-lead", help="Reviewer identity")
    reject_parser.add_argument("--comments", default="Rejected: insufficient documentation", help="Comments")
    reject_parser.add_argument("--temporal", default="localhost:7233", help="Temporal server address")

    args = parser.parse_args()

    if args.command == "emit":
        asyncio.run(emit_dispute(args.kafka, args.case_id, args.customer_id))
    elif args.command == "query":
        asyncio.run(query_workflow(args.temporal, args.case_id))
    elif args.command == "approve":
        asyncio.run(signal_approval(args.temporal, args.case_id, True, args.reviewer, args.comments))
    elif args.command == "reject":
        asyncio.run(signal_approval(args.temporal, args.case_id, False, args.reviewer, args.comments))

if __name__ == "__main__":
    main()
