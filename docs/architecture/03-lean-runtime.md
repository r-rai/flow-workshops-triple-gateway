# Lean Workshop Runtime

## Hardware Constraint

Target participants: Windows 11, 16 GB RAM, Docker Desktop/WSL2, browser
and IDE.

Engineering target: normal exercises should fit comfortably within
roughly **3--5 GB total WSL2/Docker headroom**. Per-container figures
remain estimates until benchmarked.

## Lean Choices

-   APISIX standalone/declarative mode if required plugins pass POC.
-   Temporal development server.
-   Single-node Kafka KRaft with bounded JVM heap.
-   OTel Collector + Jaeger instead of a full LGTM stack.
-   SQLite in Workshops 1--2 where possible.
-   PostgreSQL only when persistence behavior matters.
-   Redis only where shared transient state/idempotency is required.
-   Pre-built workshop-owned container images.

## Target Profiles

  Component               W1         W2         W3      W4
  ------------------- ---------- ---------- ---------- ----
  APISIX Standalone       ✓          ✓          ✓       ✓
  FastAPI                 ✓          ✓          ✓       ✓
  LangGraph               ✓          ✓          ✓       ✓
  SQLite                  ✓          ✓                 
  OPA                                ✓                  ✓
  Keycloak                           ✓                  ✓
  PostgreSQL                                    ✓       ✓
  Redis                                         ✓       ✓
  Kafka KRaft                                   ✓       ✓
  Temporal Dev                                  ✓       ✓
  OTel Collector       optional   optional   optional   ✓
  Jaeger               optional   optional   optional   ✓

Target UX:

``` bash
docker compose --profile w1 up -d
```

The presenter VPS hosts a stable fallback/reference environment, not a
shared high-concurrency runtime for all attendees.
