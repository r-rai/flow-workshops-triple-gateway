"""Browser banking requests preserve Gate 3 and never expose its credentials."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
import pytest
import yaml
from fastapi.testclient import TestClient
from src.demo.app import app


@pytest.fixture
def banking(monkeypatch):
    monkeypatch.setenv('DEMO_BACKEND_MODE', 'enterprise')
    monkeypatch.setenv('DEMO_CHAT_MODE', 'scripted')
    monkeypatch.setenv('GATE3_API_KEY', 'private-gateway-key')
    requests = []
    status = [200]
    real_client = httpx.AsyncClient

    def upstream(request):
        requests.append(request)
        if status[0] != 200:
            return httpx.Response(status[0], json={'detail': 'Upstream denied'})
        if request.url.path.endswith('/cases'):
            return httpx.Response(200, json=[{'id': 'maya-case', 'customer_id': 'cust-maya'}, {'id': 'other-case', 'customer_id': 'other'}])
        return httpx.Response(200, json={'id': 'demo-checking', 'name': 'Live account', 'balance': 123, 'currency': 'INR', 'locked': False})

    monkeypatch.setattr('src.demo.app.httpx.AsyncClient', lambda **kw: real_client(transport=httpx.MockTransport(upstream)))
    with TestClient(app) as client:
        yield client, requests, status
        client.post('/demo-api/logout')


def sign_in(client):
    assert client.post('/demo-api/login', json={'email': 'maya@flobank.demo', 'password': 'flo-demo'}).status_code == 200


def test_banking_requires_session(banking):
    client, requests, _ = banking
    assert client.get('/demo-api/banking/accounts/demo-checking').status_code == 401
    assert not requests


def test_live_account_response_and_server_only_credentials(banking):
    client, requests, _ = banking
    sign_in(client)
    requests.clear()
    result = client.get('/demo-api/banking/accounts/demo-checking')
    assert result.status_code == 200
    assert result.json()['balance'] == 123
    assert requests[0].url.path == '/api/v1/accounts/demo-checking'
    assert requests[0].headers['x-api-key'] == 'private-gateway-key'
    assert requests[0].headers['authorization'].startswith('Bearer ')
    assert 'private-gateway-key' not in result.text
    assert result.headers['cache-control'] == 'no-store'


def test_proxy_denial_and_allowlist(banking):
    client, requests, status = banking
    sign_in(client)
    requests.clear()
    assert client.get('/demo-api/banking/accounts/acc-101').status_code == 422
    assert client.post('/demo-api/banking/admin/reset').status_code == 404
    assert client.post('/demo-api/banking/payments', json={}).status_code == 404
    assert not requests
    status[0] = 401
    assert client.get('/demo-api/banking/accounts/demo-checking').status_code == 401


def test_cases_are_customer_scoped(banking):
    client, _, _ = banking
    sign_in(client)
    assert client.get('/demo-api/banking/cases').json() == [{'id': 'maya-case', 'customer_id': 'cust-maya'}]
    assert client.post('/demo-api/banking/cases', json={'customer_id': 'other', 'description': 'bad'}).status_code == 422


def test_docs_gateway_routes():
    config = yaml.safe_load(Path('docker/apisix/apisix-w1.yaml').read_text())
    route = next((r for r in config['routes'] if r['id'] == 'w1_api_docs'), None)
    assert route is not None
    assert set(route['uris']) == {'/docs', '/docs/oauth2-redirect', '/openapi.json'}
    assert route['upstream']['nodes'] == {'api:8000': 1}


def test_logout_during_dispute_read_prevents_write(banking, monkeypatch):
    from src.demo.app import sessions
    client, requests, _ = banking
    sign_in(client)
    session = sessions[client.cookies.get('flo_demo_session')]
    # The fixture patched the client factory; use the actual class directly.
    from httpx import _client
    def upstream(request):
        requests.append(request)
        session.expires_at = 0
        return httpx.Response(200, json=[] if request.method == 'GET' else {'id': 'late-case'})
    monkeypatch.setattr('src.demo.app.httpx.AsyncClient', lambda **kw: _client.AsyncClient(transport=httpx.MockTransport(upstream)))
    requests.clear()
    response = client.post('/demo-api/banking/cases', json={'transaction_id': 'tx-1004'})
    assert response.status_code == 401
    assert all(request.method != 'POST' for request in requests)


def test_concurrent_logins_create_one_dispute(monkeypatch):
    import asyncio
    import json
    import time
    from src.demo.app import DemoSession, sessions
    from httpx import _client
    real_client = _client.AsyncClient
    stored = []

    async def upstream(request):
        if request.method == 'GET':
            result = list(stored)
            await asyncio.sleep(0.02)
            return httpx.Response(200, json=result)
        case = {'id': f'case-{len(stored)}', **json.loads(request.content)}
        stored.append(case)
        return httpx.Response(201, json=case)

    monkeypatch.setattr('src.demo.app.httpx.AsyncClient', lambda **kw: real_client(transport=httpx.MockTransport(upstream)))
    tokens = ['concurrent-demo-one', 'concurrent-demo-two']
    for token in tokens:
        sessions[token] = DemoSession(expires_at=time.time() + 60, backend_mode='enterprise', api_token='customer-token')

    async def scenario():
        async with real_client(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            responses = await asyncio.gather(*[
                client.post('/demo-api/banking/cases', json={'transaction_id': 'tx-1004'}, headers={'Cookie': f'flo_demo_session={token}'})
                for token in tokens
            ])
            assert all(response.status_code in (200, 201) for response in responses)
    try:
        asyncio.run(scenario())
        assert len(stored) == 1
    finally:
        for token in tokens:
            sessions.pop(token, None)
