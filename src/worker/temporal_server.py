import asyncio
import signal
import os
from temporalio.testing import WorkflowEnvironment

async def main():
    db_file = os.getenv("TEMPORAL_DB_FILE", "/data/temporal.sqlite")
    port = int(os.getenv("TEMPORAL_PORT", "7233"))
    print(f"[Temporal Server] Starting on 0.0.0.0:{port} with persistence at {db_file}...", flush=True)
    
    # Ensure directory exists
    if db_file and db_file != "memory":
        os.makedirs(os.path.dirname(os.path.abspath(db_file)), exist_ok=True)
        
    env = await WorkflowEnvironment.start_local(
        ip="0.0.0.0",
        port=port,
        dev_server_database_filename=db_file if db_file != "memory" else None
    )
    print(f"[Temporal Server] Running and ready on 0.0.0.0:{port}", flush=True)
    
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except (NotImplementedError, RuntimeError):
            pass

    await stop_event.wait()
    print("[Temporal Server] Shutting down...", flush=True)
    await env.shutdown()
    print("[Temporal Server] Stopped cleanly.", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
