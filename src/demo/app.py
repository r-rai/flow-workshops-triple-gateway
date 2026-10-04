"""Standalone customer simulation, isolated from enterprise credentials and data.

Run: uvicorn src.demo.app:app --host 127.0.0.1 --port 8000
Also mounted by the core API; no LLM/provider dependencies are needed.
"""
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
import re
import secrets
import time

from fastapi import Cookie, Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

STATIC = Path(__file__).parent / 'static'
SESSION_TTL = 1800
MAX_SESSIONS = 128
COOKIE = 'flo_demo_session'

DEMO = {
    'mode': 'simulation',
    'customer': {'name': 'Maya Shah', 'email': 'maya@flobank.demo'},
    'accounts': [
        {'id': 'demo-checking', 'name': 'Everyday account', 'number': '•••• 2048', 'balance': 12485000, 'currency': 'INR'},
        {'id': 'demo-savings', 'name': 'Savings pocket', 'number': '•••• 8821', 'balance': 35000000, 'currency': 'INR'},
    ],
    'card': {'last_four': '2048', 'holder': 'MAYA SHAH', 'expiry': '09/29', 'locked': False},
    'transactions': [
        {'id': 'tx-1001', 'merchant': 'Acme Studio', 'category': 'Salary', 'date': '2026-10-03', 'amount': 8500000, 'direction': 'credit', 'icon': '↙'},
        {'id': 'tx-1002', 'merchant': 'Blue Tokai', 'category': 'Food & drink', 'date': '2026-10-03', 'amount': 48000, 'direction': 'debit', 'icon': '☕'},
        {'id': 'tx-1003', 'merchant': 'Fresh Basket', 'category': 'Groceries', 'date': '2026-10-02', 'amount': 186000, 'direction': 'debit', 'icon': '↗'},
        {'id': 'tx-1004', 'merchant': 'Stream+', 'category': 'Subscription', 'date': '2026-10-01', 'amount': 249900, 'direction': 'debit', 'icon': '▷'},
        {'id': 'tx-1005', 'merchant': 'Metro Transit', 'category': 'Travel', 'date': '2026-09-30', 'amount': 65000, 'direction': 'debit', 'icon': '↗'},
    ],
}


@dataclass
class DemoSession:
    expires_at: float
    card_locked: bool = False
    cases: dict = field(default_factory=dict)


# One process is sufficient for this small workshop demo. Restarting resets it.
sessions: dict[str, DemoSession] = {}
app = FastAPI(title='Flo Bank Customer Demo', docs_url=None, redoc_url=None, openapi_url=None)
demo_api = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


class LoginRequest(BaseModel):
    email: str = Field(max_length=120)
    password: str = Field(max_length=120)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)

    @field_validator('message')
    @classmethod
    def trim_message(cls, value: str) -> str:
        if not value.strip():
            raise ValueError('Please enter a message.')
        return value.strip()


def current_session(flo_demo_session: str | None = Cookie(default=None)) -> DemoSession:
    session = sessions.get(flo_demo_session or '')
    if session is None or session.expires_at <= time.time():
        sessions.pop(flo_demo_session or '', None)
        raise HTTPException(401, 'Your demo session ended. Please sign in again.')
    return session


def snapshot(session: DemoSession) -> dict:
    data = deepcopy(DEMO)
    data['card']['locked'] = session.card_locked
    data['cases'] = list(session.cases.values())
    return data


def rupees(amount: int) -> str:
    # Fixtures and monetary calculations use integer paise throughout.
    whole, paise = divmod(amount, 100)
    digits = str(whole)
    prefix = digits[:-3]
    groups = []
    while prefix:
        groups.insert(0, prefix[-2:])
        prefix = prefix[:-2]
    groups.append(digits[-3:])
    return '₹' + ','.join(groups) + f'.{paise:02d}'


@demo_api.middleware('http')
async def private_responses(request: Request, call_next):
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    return response


@demo_api.post('/login')
async def login(payload: LoginRequest, request: Request, response: Response):
    if payload.email.strip().lower() != 'maya@flobank.demo' or payload.password != 'flo-demo':
        raise HTTPException(401, 'Use the sample login: maya@flobank.demo / flo-demo.')
    now = time.time()
    for token in list(sessions):
        if sessions[token].expires_at <= now:
            sessions.pop(token, None)
    old_token = request.cookies.get(COOKIE)
    sessions.pop(old_token, None)
    if len(sessions) >= MAX_SESSIONS:
        raise HTTPException(503, 'The demo is busy. Please try again shortly.')
    token = secrets.token_urlsafe(32)
    session = DemoSession(expires_at=now + SESSION_TTL)
    sessions[token] = session
    response.set_cookie(COOKIE, token, max_age=SESSION_TTL, httponly=True,
                        samesite='strict', secure=request.url.scheme == 'https', path='/demo-api')
    return snapshot(session)


@demo_api.post('/logout')
async def logout(request: Request, response: Response):
    sessions.pop(request.cookies.get(COOKIE), None)
    response.delete_cookie(COOKIE, path='/demo-api')
    return {'status': 'signed_out'}


@demo_api.get('/dashboard')
async def dashboard(session: DemoSession = Depends(current_session)):
    return snapshot(session)


@demo_api.post('/chat')
async def chat(payload: ChatRequest, session: DemoSession = Depends(current_session)):
    message = payload.message.lower()
    words = set(re.findall(r'[a-z]+', message))
    transactions = DEMO['transactions']
    if words & {'transfer', 'send', 'pay', 'payment'}:
        reply = 'This demo cannot move money. You can explore your balance, transactions, card controls, and a simulated dispute.'
    elif words & {'unfreeze', 'unlock'}:
        session.card_locked = False
        reply = 'Your demo card ending 2048 is active again. This only changes your simulation.'
    elif words & {'freeze', 'lock'}:
        session.card_locked = True
        reply = 'Your demo card ending 2048 is now frozen. You can say “unfreeze my card” to reactivate it. This only changes your simulation.'
    elif words & {'status', 'cases'} and 'card' not in words:
        if session.cases:
            reply = '\n'.join(f"{case['id']}: {case['merchant']} — under review. This is a simulated case; no real investigation has started." for case in session.cases.values())
        else:
            reply = 'You have no demo disputes yet. Try “Dispute tx-1004” to walk through the Stream+ charge.'
    elif words & {'dispute', 'unrecognized', 'unrecognised', 'unauthorized', 'unauthorised'}:
        match = re.search(r'\btx-\d+\b', message)
        transaction_id = match.group(0) if match else None
        transaction = next((item for item in transactions if item['id'] == transaction_id), None)
        if transaction_id and transaction is None:
            reply = 'I could not find that transaction in your demo account. Choose a transaction from recent activity.'
        elif transaction is None:
            reply = 'Which transaction would you like to dispute? Choose “Dispute” beside a charge in recent activity, or try “Dispute tx-1004”.'
        elif transaction['direction'] == 'credit':
            reply = 'Please choose a debit charge to simulate a dispute.'
        else:
            if transaction_id not in session.cases:
                session.cases[transaction_id] = {
                    'id': f'DEMO-{1001 + len(session.cases)}', 'transaction_id': transaction_id,
                    'merchant': transaction['merchant'], 'status': 'under review',
                }
            case = session.cases[transaction_id]
            reply = f"Simulated dispute {case['id']} for {transaction['merchant']} ({rupees(transaction['amount'])}) is under review. You can ask for its status. No real case or refund was created."
    elif words & {'balance', 'account', 'accounts', 'savings'}:
        reply = '\n'.join(f"{account['name']}: {rupees(account['balance'])}" for account in DEMO['accounts']) + '\nThese balances are fictional demo data.'
    elif words & {'transactions', 'transaction', 'activity', 'recent'}:
        reply = 'Your recent demo activity:\n' + '\n'.join(
            f"{item['merchant']} · {'+' if item['direction'] == 'credit' else '−'}{rupees(item['amount'])} · {item['id']}" for item in transactions)
    elif words & {'spend', 'spent', 'spending'}:
        total = sum(item['amount'] for item in transactions if item['direction'] == 'debit')
        reply = f"You spent {rupees(total)} across the charges in your demo activity. Your largest charge is Stream+ at ₹2,499.00."
    elif 'card' in words:
        reply = f"Your demo card ending 2048 is {'frozen' if session.card_locked else 'active'}. Try “freeze my card” or “unfreeze my card”."
    else:
        reply = 'Hi! I’m Flo, your demo banking assistant. I can show your balance, recent transactions and spending, freeze or unfreeze your demo card, and simulate a transaction dispute. What would you like to try?'
    return {'reply': reply, 'mode': 'simulation', 'dashboard': snapshot(session)}


app.mount('/demo-api', demo_api)
app.mount('/demo-assets', StaticFiles(directory=STATIC), name='demo-assets')


@app.get('/', include_in_schema=False)
async def index():
    return FileResponse(STATIC / 'index.html', headers={'Cache-Control': 'no-cache'})
