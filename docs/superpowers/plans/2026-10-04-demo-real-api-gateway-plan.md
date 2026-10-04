# Flo Bank Demo Dual-Mode Real API Gateway Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable Flo Bank customer demo to interact in real time with the Core Banking API via APISIX Gate 3 in `DEMO_BACKEND_MODE=enterprise` mode while preserving the single-command zero-dependency standalone simulated demo (`DEMO_BACKEND_MODE=simulated`).

**Architecture:** Flo Bank customer demo supports dual backend modes: `simulated` (in-memory fixtures for standalone laptop use) and `enterprise` (real HTTP requests to APISIX Gate 3 `:9080/api/v1` for accounts, cards, and cases). In enterprise mode, login mints/exchanges a scoped customer JWT, and Flo's tool calls (`get_demo_accounts`, `set_demo_card_state`, `create_demo_dispute`) execute against the real database through APISIX with W3C distributed trace propagation into Jaeger.

**Tech Stack:** FastAPI, SQLAlchemy, APISIX 3.19.0 (Gate 3), Jose JWT, HTTPX, Docker Compose.

## Global Constraints

- Preserve single Compose startup command for standalone demo: `docker compose --profile demo up -d --build`.
- Keep `DEMO_BACKEND_MODE=simulated` as default for profile `demo`.
- Dedicated demo accounts (`demo-checking`, `demo-savings`) in `seed/v1_seed.json` must be isolated from workshop rehearsal accounts (`acc-101`, `case-501`).
- All currency calculations remain in integer minor units (paise).
- Gate 3 requests must require valid cryptographic JWT tokens with `aud="flobank-api"`.
- Workshop profiles (`w1`–`w4`) and preflight checks must remain 100% passing.

---

### Task 1: Database Model & Seed Data Extension for Cards and Demo Accounts

**Files:**
- Modify: `src/models/db_models.py`
- Modify: `src/services/seed.py`
- Modify: `seed/v1_seed.json`
- Test: `tests/test_api_foundation.py`

**Interfaces:**
- Consumes: `Base` from `src.core.database`
- Produces: `CardRecord` model (`cards` table), seeded `demo-checking` and `demo-savings` accounts, and seeded `card-2048`.

- [ ] **Step 1: Write failing test in `tests/test_api_foundation.py` verifying CardRecord model and demo seed data**

```python
def test_seed_contains_demo_accounts_and_card(db_session):
    from src.models.db_models import Account, CardRecord
    checking = db_session.query(Account).filter(Account.id == "demo-checking").first()
    assert checking is not None
    assert checking.balance == 12485000
    assert checking.currency == "INR"

    card = db_session.query(CardRecord).filter(CardRecord.id == "card-2048").first()
    assert card is not None
    assert card.last_four == "2048"
    assert card.locked is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_api_foundation.py::test_seed_contains_demo_accounts_and_card -v`
Expected: FAIL with `ImportError: cannot import name 'CardRecord'`

- [ ] **Step 3: Implement `CardRecord` in `src/models/db_models.py` and update `seed/v1_seed.json` and `src/services/seed.py`**

In `src/models/db_models.py`:
```python
class CardRecord(Base):
    __tablename__ = "cards"

    id = Column(String(64), primary_key=True, index=True)
    account_id = Column(String(64), nullable=False, index=True)
    customer_id = Column(String(64), nullable=False, index=True)
    last_four = Column(String(4), nullable=False)
    holder_name = Column(String(128), nullable=False)
    expiry = Column(String(8), nullable=False)
    locked = Column(Boolean, nullable=False, default=False)
    updated_at = Column(Float, default=time.time, onupdate=time.time)
```

In `seed/v1_seed.json`, add demo accounts to `"accounts"`:
```json
    {
      "id": "demo-checking",
      "name": "Everyday account",
      "balance": 12485000,
      "currency": "INR",
      "status": "active"
    },
    {
      "id": "demo-savings",
      "name": "Savings pocket",
      "balance": 35000000,
      "currency": "INR",
      "status": "active"
    }
```
And add `"cards"` array:
```json
  "cards": [
    {
      "id": "card-2048",
      "account_id": "demo-checking",
      "customer_id": "cust-maya",
      "last_four": "2048",
      "holder_name": "MAYA SHAH",
      "expiry": "09/29",
      "locked": false
    }
  ]
```

In `src/services/seed.py`, insert cards during `reset_and_seed_db`:
```python
    for c in data.get("cards", []):
        db.add(CardRecord(
            id=c["id"],
            account_id=c["account_id"],
            customer_id=c.get("customer_id", "cust-maya"),
            last_four=c["last_four"],
            holder_name=c["holder_name"],
            expiry=c["expiry"],
            locked=c.get("locked", False),
            updated_at=time.time(),
        ))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_api_foundation.py::test_seed_contains_demo_accounts_and_card -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add src/models/db_models.py src/services/seed.py seed/v1_seed.json tests/test_api_foundation.py
git commit -m "feat(api): add CardRecord model and seed demo accounts and cards"
```

---

### Task 2: Core API Endpoints for Cards & Support Case Creation

**Files:**
- Create: `src/api/routes/cards.py`
- Modify: `src/api/routes/cases.py`
- Modify: `src/api/main.py`
- Modify: `src/models/schemas.py`
- Test: `tests/test_api_foundation.py`

**Interfaces:**
- Consumes: `require_scope("api:cards:read")`, `require_scope("api:cards:write")`, `require_scope("api:cases:write")`
- Produces: `GET /api/v1/cards/{id}`, `POST /api/v1/cards/{id}/state`, and `POST /api/v1/cases`.

- [ ] **Step 1: Write failing test for card read/mutation and case creation**

In `tests/test_api_foundation.py`:
```python
def test_cards_and_case_creation_endpoints(client):
    from src.core.security import create_jwt_token
    token = create_jwt_token("cust-maya", audience="flobank-api", scopes=["api:cards:read", "api:cards:write", "api:cases:write"], role="customer")
    headers = {"Authorization": f"Bearer {token}", "X-API-Key": "gate3-secret-token"}

    # Read card
    r_card = client.get("/api/v1/cards/card-2048", headers=headers)
    assert r_card.status_code == 200
    assert r_card.json()["last_four"] == "2048"
    assert r_card.json()["locked"] is False

    # Freeze card
    r_freeze = client.post("/api/v1/cards/card-2048/state", headers=headers, json={"locked": True})
    assert r_freeze.status_code == 200
    assert r_freeze.json()["locked"] is True

    # Create dispute case
    r_case = client.post("/api/v1/cases", headers=headers, json={
        "id": "DEMO-CASE-1001",
        "customer_id": "cust-maya",
        "issue_type": "disputed_transaction",
        "description": "Simulated dispute for Stream+ charge tx-1004"
    })
    assert r_case.status_code == 201
    assert r_case.json()["id"] == "DEMO-CASE-1001"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_api_foundation.py::test_cards_and_case_creation_endpoints -v`
Expected: FAIL (404 on `/api/v1/cards/card-2048`)

- [ ] **Step 3: Implement cards schema, router, and cases POST endpoint**

Create `src/api/routes/cards.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.db_models import CardRecord
from src.core.security import require_scope, Principal

router = APIRouter(prefix="/api/v1/cards", tags=["Cards"])

class CardStateRequest(BaseModel):
    locked: bool

@router.get("/{id}")
def read_card(
    id: str = Path(...),
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_scope("api:cards:read")),
):
    card = db.query(CardRecord).filter(CardRecord.id == id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return {
        "id": card.id,
        "account_id": card.account_id,
        "customer_id": card.customer_id,
        "last_four": card.last_four,
        "holder_name": card.holder_name,
        "expiry": card.expiry,
        "locked": card.locked,
    }

@router.post("/{id}/state")
def set_card_state(
    payload: CardStateRequest,
    id: str = Path(...),
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_scope("api:cards:write")),
):
    card = db.query(CardRecord).filter(CardRecord.id == id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    card.locked = payload.locked
    db.commit()
    db.refresh(card)
    return {
        "id": card.id,
        "locked": card.locked,
        "status": "frozen" if card.locked else "active",
    }
```

In `src/api/routes/cases.py`, add `POST /api/v1/cases`:
```python
class CreateCaseRequest(BaseModel):
    id: str | None = None
    customer_id: str
    issue_type: str = "disputed_transaction"
    description: str
    priority: str = "medium"

@router.post("", status_code=status.HTTP_201_CREATED)
def create_case_endpoint(
    payload: CreateCaseRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_scope("api:cases:write")),
):
    case_id = payload.id or f"case-{int(time.time()*1000)}"
    new_case = SupportCase(
        id=case_id,
        customer_id=payload.customer_id,
        issue_type=payload.issue_type,
        description=payload.description,
        priority=payload.priority,
        status="open",
        updated_at=time.time(),
    )
    db.add(new_case)
    db.commit()
    db.refresh(new_case)
    return SupportCaseResponse(
        id=new_case.id,
        customer_id=new_case.customer_id,
        issue_type=new_case.issue_type,
        description=new_case.description,
        priority=new_case.priority,
        status=new_case.status,
    )
```

In `src/api/main.py`:
Include `cards.router` and ensure `ROLE_ENTITLED_SCOPES` in `src/api/routes/oauth.py` and `security.py` permit `customer` role to access `api:cards:read`, `api:cards:write`, `api:cases:read`, `api:cases:write`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_api_foundation.py::test_cards_and_case_creation_endpoints -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add src/api/routes/cards.py src/api/routes/cases.py src/api/main.py tests/test_api_foundation.py
git commit -m "feat(api): add card state management and case creation endpoints"
```

---

### Task 3: Enterprise Mode in Demo Tools (`src/demo/tools.py`)

**Files:**
- Modify: `src/demo/tools.py`
- Test: `tests/test_demo_live_llm.py`

**Interfaces:**
- Consumes: APISIX Gate 3 URL (`http://apisix:9080/api/v1`), JWT Bearer token
- Produces: `execute_demo_tool(name, args, state, backend_mode, gate3_url, api_token)`

- [ ] **Step 1: Write failing test in `tests/test_demo_live_llm.py` for enterprise tool execution**

```python
def test_enterprise_mode_tool_calls_gate3(monkeypatch):
    from src.demo.tools import execute_demo_tool, StagedDemoState
    staged = StagedDemoState(card_locked=False)
    
    mock_calls = []
    def mock_request(method, url, headers=None, json=None):
        mock_calls.append((method, url, headers, json))
        if "/accounts/demo-checking" in url:
            return httpx.Response(200, json={"id": "demo-checking", "name": "Everyday account", "balance": 12485000, "currency": "INR"})
        elif "/cards/card-2048/state" in url:
            return httpx.Response(200, json={"id": "card-2048", "locked": True, "status": "frozen"})
        return httpx.Response(404)

    monkeypatch.setattr(httpx, "request", mock_request)

    # 1. Accounts read via Gate 3
    res_acc = execute_demo_tool("get_demo_accounts", {}, staged, backend_mode="enterprise", gate3_url="http://apisix:9080/api/v1", api_token="test-token")
    assert res_acc["accounts"][0]["balance_paise"] == 12485000

    # 2. Card freeze via Gate 3
    res_card = execute_demo_tool("set_demo_card_state", {"locked": True}, staged, backend_mode="enterprise", gate3_url="http://apisix:9080/api/v1", api_token="test-token")
    assert res_card["card_locked"] is True
    assert staged.card_locked is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_demo_live_llm.py::test_enterprise_mode_tool_calls_gate3 -v`
Expected: FAIL (argument mismatch or simulated response returned)

- [ ] **Step 3: Implement enterprise backend mode in `src/demo/tools.py`**

In `execute_demo_tool`, accept `backend_mode: str = "simulated"`, `gate3_url: str | None = None`, `api_token: str | None = None`:
When `backend_mode == "enterprise"`:
- `get_demo_accounts`: performs HTTP `GET {gate3_url}/accounts/demo-checking` and `demo-savings` using `Authorization: Bearer {api_token}`. Formats balance with integer minor units.
- `get_demo_card`: performs HTTP `GET {gate3_url}/cards/card-2048`.
- `set_demo_card_state`: performs HTTP `POST {gate3_url}/cards/card-2048/state` with `{"locked": locked}`. Updates `state.card_locked`.
- `create_demo_dispute`: performs HTTP `POST {gate3_url}/cases` with case description and customer ID.
- `get_demo_disputes`: performs HTTP `GET {gate3_url}/cases` and filters for Maya's cases.
- All HTTP calls include `traceparent` distributed trace headers when OpenTelemetry is enabled or present.
When `backend_mode == "simulated"`, preserve existing deterministic in-memory execution unchanged!

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_demo_live_llm.py::test_enterprise_mode_tool_calls_gate3 -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add src/demo/tools.py tests/test_demo_live_llm.py
git commit -m "feat(demo): add enterprise mode tool execution via APISIX Gate 3"
```

---

### Task 4: Demo App Dual-Mode Configuration & Token Management (`src/demo/app.py`, `src/demo/llm.py`)

**Files:**
- Modify: `src/demo/app.py`
- Modify: `src/demo/llm.py`
- Test: `tests/test_demo_live_llm.py`

**Interfaces:**
- Consumes: `DEMO_BACKEND_MODE` env var (`simulated` vs `enterprise`)
- Produces: Customer session with scoped `api_token` in enterprise mode, forwarded to tool calls.

- [ ] **Step 1: Write failing test in `tests/test_demo_live_llm.py` verifying enterprise login and dashboard execution**

```python
def test_enterprise_mode_login_and_dashboard(live_client, monkeypatch):
    monkeypatch.setenv("DEMO_BACKEND_MODE", "enterprise")
    monkeypatch.setenv("GATE3_URL", "http://mock-apisix:9080/api/v1")
    
    def mock_get(url, headers=None, timeout=None):
        if "/accounts/demo-checking" in url:
            return httpx.Response(200, json={"id": "demo-checking", "name": "Everyday account", "balance": 12485000, "currency": "INR", "status": "active"})
        elif "/accounts/demo-savings" in url:
            return httpx.Response(200, json={"id": "demo-savings", "name": "Savings pocket", "balance": 35000000, "currency": "INR", "status": "active"})
        elif "/cards/card-2048" in url:
            return httpx.Response(200, json={"id": "card-2048", "locked": False})
        return httpx.Response(404)

    monkeypatch.setattr(httpx, "get", mock_get)
    res = live_client.post("/demo-api/login", json={"email": "maya@flobank.demo", "password": "flo-demo"})
    assert res.status_code == 200
    assert res.json()["backend_mode"] == "enterprise"
    assert res.json()["accounts"][0]["balance"] == 12485000
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_demo_live_llm.py::test_enterprise_mode_login_and_dashboard -v`
Expected: FAIL (`backend_mode` not present or not set to enterprise)

- [ ] **Step 3: Update `src/demo/app.py` and `src/demo/llm.py`**

- In `DemoSession`, add `api_token: str | None = None` and `backend_mode: str = "simulated"`.
- Add `get_backend_mode()`: defaults to `os.getenv("DEMO_BACKEND_MODE", "simulated").lower()`.
- On login in enterprise mode, generate an authentic JWT token for customer Maya (`sub="cust-maya"`, `aud="flobank-api"`, `scopes=["api:accounts:read", "api:cards:read", "api:cards:write", "api:cases:read", "api:cases:write"]`).
- In `snapshot()`, return `backend_mode: get_backend_mode()`.
- In `run_demo_chat_turn`, pass `backend_mode`, `gate3_url`, and `session.api_token` to `execute_demo_tool`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_demo_live_llm.py::test_enterprise_mode_login_and_dashboard -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add src/demo/app.py src/demo/llm.py tests/test_demo_live_llm.py
git commit -m "feat(demo): add dual-mode backend configuration and JWT handling to demo app"
```

---

### Task 5: Docker Compose Profiles & APISIX Routing for Enterprise Demo

**Files:**
- Modify: `docker-compose.yml`
- Modify: `docker/apisix/apisix-w2.yaml`, `apisix-w3.yaml`, `apisix-w4.yaml`
- Test: CLI validation via `docker compose config`

**Interfaces:**
- Produces: `docker compose --profile demo up -d --build` (standalone simulated) and `docker compose --profile demo-enterprise up -d --build` (full enterprise gateway demo).

- [ ] **Step 1: Update APISIX workshop configs to expose card routes**

In `docker/apisix/apisix-w2.yaml`, `apisix-w3.yaml`, `apisix-w4.yaml`:
Verify that `uri: /api/v1/*` forwards to `api:8000`, which already covers `/api/v1/cards/*` and `/api/v1/cases`.

- [ ] **Step 2: Add `demo-enterprise` profile in `docker-compose.yml`**

In `docker-compose.yml`:
Allow `demo` service to participate in profiles `["demo", "demo-enterprise"]`.
When profile is `demo-enterprise`, configure `demo` environment:
```yaml
      - DEMO_BACKEND_MODE=${DEMO_BACKEND_MODE:-enterprise}
      - GATE3_URL=http://apisix:9080/api/v1
```
And connect `demo` to `edge`, `capability`, and `backend` networks so it can talk to APISIX Gate 3 directly.

- [ ] **Step 3: Validate compose configurations for all profiles**

Run:
```bash
docker compose --profile demo config >/dev/null
docker compose --profile demo-enterprise config >/dev/null
docker compose --profile w1 config >/dev/null
docker compose --profile w2 config >/dev/null
docker compose --profile w3 config >/dev/null
docker compose --profile w4 config >/dev/null
```
Expected: All exit with code 0.

- [ ] **Step 4: Commit changes**

```bash
git add docker-compose.yml docker/apisix/
git commit -m "feat(compose): add demo-enterprise profile and network wiring for real gateway demo"
```

---

### Task 6: Full Verification, Documentation & Manifest Update

**Files:**
- Modify: `README.md`
- Modify: `config/manifest.json`
- Modify: `docs/implementation/agent-handoff.md`
- Test: Full pytest suite, preflight, and browser test

- [ ] **Step 1: Run complete automated test suite**

Run: `.venv/bin/pytest`
Expected: 100% passing tests.

- [ ] **Step 2: Run preflight check**

Run: `./scripts/workshop preflight`
Expected: Preflight PASSED.

- [ ] **Step 3: Update documentation and manifest**

- In `README.md`, document `DEMO_BACKEND_MODE=simulated|enterprise`.
- In `config/manifest.json`, document the dual-mode enterprise capability.
- In `docs/implementation/agent-handoff.md`, document the architecture and testing evidence.

- [ ] **Step 4: Commit documentation**

```bash
git add README.md config/manifest.json docs/implementation/agent-handoff.md
git commit -m "docs: document dual-mode real API gateway integration for Flo Bank demo"
```
