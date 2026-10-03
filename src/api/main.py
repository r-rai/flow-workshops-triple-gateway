import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.core.config import settings
from src.core.database import engine, Base, SessionLocal
from src.services.seed import reset_and_seed_db
from src.models.db_models import Account
from src.api.routes import health, accounts, cases, payments, approvals, incidents, admin, a2a, oauth


# Optional OpenTelemetry instrumentation
if settings.ENABLE_TELEMETRY:
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        res = Resource.create({"service.name": "novabank-api"})
        provider = TracerProvider(resource=res)
        exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
    except Exception as e:
        print(f"OTel setup skipped or failed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    # Check if DB needs initial seed
    db = SessionLocal()
    try:
        count = db.query(Account).count()
        if count == 0:
            print("Database empty. Seeding initial workshop data...")
            reset_and_seed_db(db)
    except Exception as e:
        print(f"Initial seed check warning: {e}")
    finally:
        db.close()
    yield

app = FastAPI(
    title="NovaBank Core API",
    version="1.0.0",
    description="NovaBank Multi-Workshop Enterprise Banking API with Gate 3 Enforced Security",
    lifespan=lifespan,
)

if settings.ENABLE_TELEMETRY:
    try:
        FastAPIInstrumentor.instrument_app(app)
    except Exception as e:
        print(f"FastAPIInstrumentor failed: {e}")

# Include Routers
app.include_router(health.router)
app.include_router(accounts.router)
app.include_router(cases.router)
app.include_router(payments.router)
app.include_router(approvals.router)
app.include_router(incidents.router)
app.include_router(admin.router)
app.include_router(a2a.router)
app.include_router(oauth.router)


@app.get("/.well-known/agent.json")
def well_known_agent():
    return a2a.AGENT_CARD

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
