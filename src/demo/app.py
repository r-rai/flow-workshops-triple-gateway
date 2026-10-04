"""Standalone customer simulation, isolated from enterprise credentials and data.

Run: uvicorn src.demo.app:app --host 127.0.0.1 --port 8000
Also mounted by the core API. Supports live hosted LLM chat via Gate 1 and scripted fallback.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
from dataclasses import dataclass, field
import logging
import os
from pathlib import Path
import secrets
import time
from typing import Any

from fastapi import Cookie, Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from src.demo.tools import (
    DEMO,
    StagedDemoState,
    rupees,
    scripted_reply,
)
from src.demo.llm import (
    LLMError,
    LLMConfigError,
    LLMLimitExceededError,
    LLMProviderError,
    check_gateway_status,
    run_demo_chat_turn,
)

logger = logging.getLogger("flobank.demo")

STATIC = Path(__file__).parent / 'static'
SESSION_TTL = 1800
MAX_SESSIONS = 128
COOKIE = 'flo_demo_session'


def get_chat_mode() -> str:
    """Resolve active chat mode (live vs scripted)."""
    explicit = os.getenv('DEMO_CHAT_MODE')
    if explicit:
        return explicit.lower().strip()
    if os.getenv('ACTIVE_PROFILE') == 'w1':
        return 'scripted'
    return 'live'


@dataclass
class DemoSession:
    expires_at: float
    card_locked: bool = False
    cases: dict[str, dict[str, Any]] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


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


def snapshot(session: DemoSession) -> dict[str, Any]:
    data = deepcopy(DEMO)
    data['card']['locked'] = session.card_locked
    data['cases'] = list(session.cases.values())
    data['chat_mode'] = get_chat_mode()
    return data


@demo_api.middleware('http')
async def private_responses(request: Request, call_next):
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    return response


@demo_api.get('/status')
async def chat_status():
    mode = get_chat_mode()
    if mode == 'scripted':
        return {
            'chat_mode': 'scripted',
            'mode': 'simulation',
            'configured': True,
            'available': True,
            'model': None,
        }
    gw_status = await check_gateway_status()
    return {
        'chat_mode': 'live',
        'mode': 'simulation',
        'configured': gw_status.get('configured', False),
        'available': gw_status.get('available', False),
        'model': gw_status.get('model', 'MiniMax-M2.7'),
        'headroom_tokens': gw_status.get('headroom_tokens'),
    }


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
    token = request.cookies.get(COOKIE)
    session = sessions.pop(token, None)
    if session:
        session.expires_at = 0
        session.history.clear()
    response.delete_cookie(COOKIE, path='/demo-api')
    return {'status': 'signed_out'}


@demo_api.get('/dashboard')
async def dashboard(session: DemoSession = Depends(current_session)):
    return snapshot(session)


@demo_api.post('/chat')
async def chat(payload: ChatRequest, session: DemoSession = Depends(current_session)):
    mode = get_chat_mode()

    # Per-session lock serializes concurrent turns for the same session
    async with session.lock:
        now = time.time()
        if session.expires_at <= now:
            raise HTTPException(401, 'Your demo session ended. Please sign in again.')

        if mode == 'scripted':
            reply, new_locked, new_cases = scripted_reply(payload.message, session.card_locked, session.cases)
            session.card_locked = new_locked
            session.cases = new_cases
            session.history.append({'role': 'user', 'content': payload.message})
            session.history.append({'role': 'assistant', 'content': reply})
            return {
                'reply': reply,
                'mode': 'simulation',
                'chat_mode': 'scripted',
                'dashboard': snapshot(session),
            }

        # Live LLM Turn with staged session changes
        staged = StagedDemoState(card_locked=session.card_locked, cases=deepcopy(session.cases))

        try:
            reply, updated_history, metadata = await run_demo_chat_turn(
                user_message=payload.message,
                history=session.history,
                staged_state=staged,
            )
        except LLMConfigError as e:
            logger.warning(f"Demo chat config error: {e.message}")
            raise HTTPException(status_code=503, detail=e.message)
        except LLMLimitExceededError as e:
            logger.warning(f"Demo chat limit error: {e.message}")
            raise HTTPException(status_code=429, detail=e.message)
        except LLMProviderError as e:
            logger.error(f"Demo chat provider error ({e.status_code}): {e.message}")
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except LLMError as e:
            logger.error(f"Demo chat error: {e.message}")
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            logger.error(f"Demo chat unexpected error: {str(e)}", exc_info=True)
            raise HTTPException(status_code=502, detail=f"Flo chat encountered an unexpected error: {str(e)}")

        # Revalidate session validity after awaited I/O
        if session.expires_at <= time.time():
            raise HTTPException(401, 'Your demo session ended. Please sign in again.')

        # Atomically commit staged changes and updated history
        session.card_locked = staged.card_locked
        session.cases = staged.cases
        session.history = updated_history

        return {
            'reply': reply,
            'mode': 'simulation',
            'chat_mode': 'live',
            'model': metadata.get('model'),
            'dashboard': snapshot(session),
        }


app.mount('/demo-api', demo_api)
app.mount('/demo-assets', StaticFiles(directory=STATIC), name='demo-assets')


@app.get('/', include_in_schema=False)
async def index():
    return FileResponse(STATIC / 'index.html', headers={'Cache-Control': 'no-cache'})
