"""Session-authenticated browser access to the demo customer's Gate 3 APIs."""
from __future__ import annotations

import asyncio
import os
import time
from typing import Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from src.demo.tools import DEMO, rupees


class CardState(BaseModel):
    locked: bool


class Dispute(BaseModel):
    transaction_id: str


async def request_bank(session, gate3_url, method, path, payload=None):
    if session.expires_at <= time.time():
        raise HTTPException(401, 'Your demo session ended. Please sign in again.')
    if session.backend_mode != 'enterprise' or not session.api_token:
        raise HTTPException(409, 'Real banking is unavailable in simulation mode.')
    headers = {
        'X-API-Key': os.getenv('GATE3_API_KEY', 'gate3-secret-token'),
        'Authorization': f'Bearer {session.api_token}',
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            result = await client.request(method, f'{gate3_url()}/{path}', headers=headers, json=payload)
    except httpx.RequestError as exc:
        raise HTTPException(502, 'The banking gateway is unavailable.') from exc
    if not result.is_success:
        raise HTTPException(result.status_code, 'The banking API rejected this request.')
    return result.json()


def create_router(current_session, gate3_url):
    router = APIRouter(prefix='/banking', tags=['Customer banking'])
    # This demo has one customer and runs in one API worker. Serialize its
    # mutations across logins, while also retaining chat's per-session lock.
    customer_mutations = asyncio.Lock()

    @router.get('/accounts/{account_id}')
    async def account(account_id: Literal['demo-checking', 'demo-savings'], session=Depends(current_session)):
        return await request_bank(session, gate3_url, 'GET', f'accounts/{account_id}')

    @router.get('/cards/card-2048')
    async def card(session=Depends(current_session)):
        return await request_bank(session, gate3_url, 'GET', 'cards/card-2048')

    @router.post('/cards/card-2048/state')
    async def set_card(payload: CardState, session=Depends(current_session)):
        async with session.lock, customer_mutations:
            result = await request_bank(session, gate3_url, 'POST', 'cards/card-2048/state', payload.model_dump())
            session.card_locked = result['locked']
            return result

    @router.get('/cases')
    async def cases(session=Depends(current_session)):
        result = await request_bank(session, gate3_url, 'GET', 'cases')
        return [case for case in result if case.get('customer_id') == 'cust-maya']

    @router.post('/cases', status_code=201)
    async def dispute(payload: Dispute, response: Response, session=Depends(current_session)):
        tx = next((tx for tx in DEMO['transactions'] if tx['id'] == payload.transaction_id and tx['direction'] == 'debit'), None)
        if tx is None:
            raise HTTPException(422, 'Choose a debit transaction from recent activity.')
        async with session.lock, customer_mutations:
            existing = await request_bank(session, gate3_url, 'GET', 'cases')
            description = f"Dispute for {tx['merchant']} ({rupees(tx['amount'])}) tx: {tx['id']}"
            case = next((case for case in existing if case.get('customer_id') == 'cust-maya' and case.get('description') == description), None)
            if case:
                response.status_code = 200
            else:
                case = await request_bank(session, gate3_url, 'POST', 'cases', {
                    'customer_id': 'cust-maya', 'issue_type': 'disputed_transaction',
                    'description': description, 'priority': 'medium',
                })
            session.cases[tx['id']] = {**case, 'transaction_id': tx['id'], 'merchant': tx['merchant']}
            return case

    # Unknown paths cannot turn this session into a general enterprise proxy.
    @router.api_route('/{path:path}', methods=['GET', 'POST', 'PATCH', 'DELETE', 'PUT'])
    async def unavailable(path: str, session=Depends(current_session)):
        raise HTTPException(404, 'This banking operation is unavailable.')

    return router
