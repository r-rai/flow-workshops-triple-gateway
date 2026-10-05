"""Incident Room contracts. Financial/identity/A2A boundaries use the real API on an isolated DB."""
import asyncio
import json
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.core.database import Base, get_db
from src.services.seed import reset_and_seed_db

@pytest.fixture
def lab(tmp_path, monkeypatch):
    monkeypatch.setenv('ACTIVE_PROFILE', 'w4')
    monkeypatch.setenv('DEMO_CHAT_MODE', 'scripted')
    monkeypatch.setenv('DEMO_BACKEND_MODE', 'simulated')
    monkeypatch.setenv('W4_STORE_PATH', str(tmp_path / 'runs.sqlite'))
    monkeypatch.setenv('W4_REVIEWER_PASSWORD', 'test-independent-reviewer')
    from src.demo.app import app
    from src.demo import incident
    from src.api.main import app as bank
    engine = create_engine('sqlite:///' + str(tmp_path / 'protected.sqlite'), connect_args={'check_same_thread': False})
    Base.metadata.create_all(engine)
    import src.services.seed as seed_service
    monkeypatch.setattr(seed_service, 'engine', engine)
    factory = sessionmaker(bind=engine)
    with factory() as db:
        reset_and_seed_db(db, 'seed/v1_seed.json')
    def db_override():
        with factory() as db:
            yield db
    bank.dependency_overrides[get_db] = db_override
    original = httpx.AsyncClient
    monkeypatch.setattr(incident, 'gateway_client', lambda: original(transport=httpx.ASGITransport(app=bank), base_url='http://bank'))
    with TestClient(app) as client, TestClient(app) as reviewer:
        for c in (client, reviewer):
            assert c.post('/demo-api/login', json={'email':'maya@flobank.demo', 'password':'flo-demo'}).status_code == 200
        assert reviewer.post('/demo-api/workshop-4/reviewer-session', json={'password':'test-independent-reviewer'}).status_code == 200
        yield client, reviewer, factory
    bank.dependency_overrides.clear()
    engine.dispose()


def start(client, scenario, key='click-1'):
    r = client.post('/demo-api/workshop-4/runs', json={'scenario':scenario, 'request_id':key})
    assert r.status_code == 200, r.text
    return r.json()


def test_profile_and_allowlist(monkeypatch):
    from src.demo.app import app
    with TestClient(app) as c:
        monkeypatch.setenv('ACTIVE_PROFILE', 'w4')
        assert c.get('/workshop-4').status_code == 200
        assert c.get('/demo-api/workshop-4/readiness').status_code == 401
        c.post('/demo-api/login', json={'email':'maya@flobank.demo','password':'flo-demo'})
        assert c.post('/demo-api/workshop-4/runs', json={'scenario':'wrong_audience','request_id':'a','token':'evil'}).status_code == 422
        for profile in ('w1','w2','w3','demo'):
            monkeypatch.setenv('ACTIVE_PROFILE', profile)
            assert c.get('/workshop-4').status_code == 404
            assert c.get('/demo-api/workshop-4/readiness').status_code == 404

@pytest.mark.parametrize(('scenario', 'status'), [('wrong_audience',401), ('insufficient_scope',403), ('scope_escalation',403), ('valid_exchange',200)])
def test_identity_results_from_services(lab, scenario, status):
    c, _, _ = lab
    run = start(c, scenario)
    assert [e for e in run['events'] if e['boundary']=='Gate 3'][-1]['status_code'] == status
    assert run['effects']['balance_delta'] == 0
    assert 'Bearer ' not in json.dumps(run)
    assert '"access_token":' not in json.dumps(run)


def test_refresh_doubleclick_and_foreign_run(lab):
    c, reviewer, _ = lab
    first = start(c, 'wrong_audience')
    assert start(c, 'wrong_audience')['run_id'] == first['run_id']
    assert c.get('/demo-api/workshop-4/runs/' + first['run_id']).json() == first
    reviewer.cookies.delete('w4_reviewer')
    assert reviewer.get('/demo-api/workshop-4/runs/' + first['run_id']).status_code == 403
    assert c.get('/demo-api/workshop-4/runs/' + first['run_id'] + '/evidence').json() == first


def test_independent_approval_exact_execution_and_retry(lab):
    c, reviewer, factory = lab
    run = start(c, 'legitimate_delegation')
    assert run['state'] == 'awaiting_review'
    assert run['effects']['balance_delta'] == 0
    assert any(e['label'] == 'Self approval' and e['status_code'] == 403 for e in run['events'])
    path = '/demo-api/workshop-4/runs/' + run['run_id']
    assert c.post(path + '/decision', json={'decision':'approve'}).status_code == 403
    reviewed = reviewer.post(path + '/decision', json={'decision':'approve'})
    assert reviewed.status_code == 200, reviewed.text
    result = reviewed.json()
    assert result['state'] == 'completed'
    assert result['effects']['balance_delta'] == -150000
    assert result['effects']['payment_count_delta'] == 1
    assert result['task']['output']['payment_id'] == result['payment']['payment_id']
    assert any(e['label'] == 'Changed arguments' and e['status_code'] == 400 for e in result['events'])
    assert reviewer.post(path + '/decision', json={'decision':'approve'}).json()['payment'] == result['payment']
    assert 'test-independent-reviewer' not in reviewer.get(path + '/evidence').text


def test_rejection_and_expiry(lab):
    c, reviewer, factory = lab
    run = start(c, 'legitimate_delegation')
    path = '/demo-api/workshop-4/runs/' + run['run_id']
    assert reviewer.post(path + '/decision', json={'decision':'reject'}).json()['state'] == 'rejected'
    run = start(c, 'legitimate_delegation', 'second')
    from src.models.db_models import PaymentProposal
    with factory() as db:
        db.query(PaymentProposal).filter_by(id=run['proposal']['proposal_id']).update({'expires_at':time.time()-1})
        db.commit()
    result = reviewer.post('/demo-api/workshop-4/runs/' + run['run_id'] + '/decision', json={'decision':'approve'}).json()
    assert result['state'] == 'expired'
    assert result['effects']['payment_count_delta'] == 0


def test_vulnerable_disabled_on_protected_instance(lab):
    c, _, _ = lab
    assert c.post('/demo-api/workshop-4/runs', json={'scenario':'vulnerable_replay','request_id':'x'}).status_code == 403


def test_isolated_replay_exact_loss_and_idempotency(tmp_path):
    from src.demo.incident_sandbox import replay
    path = tmp_path / 'isolated.sqlite'
    first = replay(path, 'recorded-incident')
    assert first['effects']['balance_delta'] == -900000000
    assert first['effects']['payment_count_delta'] == 1
    assert first['arguments']['amount'] == 900000000
    assert replay(path, 'recorded-incident') == first


def test_gate1_reserves_requested_output_before_dispatch(monkeypatch):
    from src.adapter import server
    monkeypatch.setattr(server, 'INFERENCE_BUDGET_TOKENS', 100)
    monkeypatch.setattr(server, '_accumulated_tokens', 0)
    with TestClient(server.app) as c:
        r = c.post('/ai/chat/completions', headers={'x-use-replay-fixtures':'true'}, json={'messages':[{'role':'user','content':'hello'}], 'max_tokens':1000})
        assert r.status_code == 429
        assert server._accumulated_tokens == 0


def test_uncertain_execution_reconciles_actual_payment(lab, monkeypatch):
    from src.demo import incident
    c, reviewer, _ = lab
    run = start(c, 'legitimate_delegation')
    original = incident.gateway_client
    class LostResponse:
        async def __aenter__(self):
            self.client = await original().__aenter__()
            return self
        async def __aexit__(self,*args):
            await self.client.__aexit__(*args)
        async def request(self,method,url,**kwargs):
            response = await self.client.request(method,url,**kwargs)
            if method=='POST' and url.endswith('/api/v1/payments') and 'Idempotency-Key' in kwargs.get('headers',{}):
                raise httpx.ReadTimeout('lost after commit')
            return response
    monkeypatch.setattr(incident, 'gateway_client', LostResponse)
    response = reviewer.post('/demo-api/workshop-4/runs/'+run['run_id']+'/decision',json={'decision':'approve'})
    result = response.json()
    assert result['state']=='completed'
    assert result['effects']['payment_count_delta']==1
    assert any(e['label']=='Execute exact payment' and e['outcome']=='unresolved' for e in result['events'])


def test_task_cannot_bind_payment_from_wrong_source(lab):
    from src.core.security import create_jwt_token
    from src.api.main import app as bank
    _, _, _ = lab
    c = TestClient(bank)
    h={'Authorization':'Bearer '+create_jwt_token('payments-agent-executor','flobank-api',['api:payments:write','api:a2a:tasks'],'agent')}
    task=c.post('/api/v1/a2a/tasks',headers=h,json={'task_type':'propose_payment','input':{'source_account':'acc-102','amount':1000,'beneficiary':'vendor-alpha','currency':'INR'}}).json()
    payment=c.post('/api/v1/payments',headers=h,json={'account_id':'acc-101','amount':1000,'beneficiary':'vendor-alpha','currency':'INR'}).json()
    result=c.post('/api/v1/a2a/tasks/'+task['task_id']+'/complete',headers=h,json={'payment_id':payment['payment_id'],'status':'SETTLED'})
    assert result.status_code==400
    assert 'source' in result.text.lower()


def test_w4_session_spans_delivery(monkeypatch):
    from src.demo.app import app
    monkeypatch.setenv('ACTIVE_PROFILE','w4')
    monkeypatch.setenv('DEMO_BACKEND_MODE','simulated')
    with TestClient(app) as c:
        response=c.post('/demo-api/login',json={'email':'maya@flobank.demo','password':'flo-demo'})
        assert 'Max-Age=10800' in response.headers['set-cookie']


def test_mcp_forwards_financial_idempotency_key(monkeypatch):
    from src.adapter import server
    from src.core.security import create_jwt_token
    calls=[]
    class Downstream:
        def __init__(self,**kwargs): pass
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def post(self,url,**kwargs):
            calls.append(kwargs)
            return httpx.Response(200,json={'payment_id':'test'})
    monkeypatch.setattr(server,'evaluate_opa_policy',lambda *args:('allow','test'))
    monkeypatch.setattr(server,'get_exchanged_api_token',lambda *args:'test-token')
    monkeypatch.setattr(server.httpx,'Client',Downstream)
    token=create_jwt_token('support','flobank-mcp',['mcp:tools'],'support_agent')
    # ASGI transport avoids replacing TestClient's own httpx client.
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=server.app),base_url='http://adapter') as c:
            return await c.post('/mcp',headers={'Authorization':'Bearer '+token,'Idempotency-Key':'incident-retry'},json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'create_payment','arguments':{'account_id':'acc-101','beneficiary':'vendor-alpha','amount':1000,'currency':'INR'}}})
    assert asyncio.run(run()).status_code==200
    assert calls[0]['headers']['Idempotency-Key']=='incident-retry'


def test_lost_approval_response_recovers_from_authoritative_proposal(lab,monkeypatch):
    from src.demo import incident
    c,reviewer,_=lab
    run=start(c,'legitimate_delegation')
    original=incident.gateway_client
    class LostApproval:
        async def __aenter__(self):
            self.client=await original().__aenter__()
            return self
        async def __aexit__(self,*args): await self.client.__aexit__(*args)
        async def request(self,method,url,**kwargs):
            response=await self.client.request(method,url,**kwargs)
            if method=='POST' and url.endswith('/approve'):
                raise httpx.ReadTimeout('approval response lost')
            return response
    monkeypatch.setattr(incident,'gateway_client',LostApproval)
    path='/demo-api/workshop-4/runs/'+run['run_id']
    assert reviewer.post(path+'/decision',json={'decision':'approve'}).json()['state']=='unresolved'
    recovered=reviewer.post(path+'/reconcile',json={}).json()
    assert recovered['state']=='completed'
    assert recovered['effects']['payment_count_delta']==1


def test_requester_refresh_after_process_restart(lab):
    from src.demo.app import sessions
    c,_,_=lab
    run=start(c,'wrong_audience')
    sessions.clear()
    assert c.get('/demo-api/workshop-4/runs/'+run['run_id']).status_code==200
    c.post('/demo-api/logout')
    assert c.get('/demo-api/workshop-4/runs/'+run['run_id']).status_code==401


def test_reviewer_status_survives_refresh(lab):
    _,reviewer,_=lab
    assert reviewer.get('/demo-api/workshop-4/readiness').json()['reviewer_authenticated'] is True


@pytest.mark.parametrize('body',[{}, {'max_completion_tokens':1000}])
def test_gate1_default_and_alias_output_reserved(monkeypatch,body):
    from src.adapter import server
    monkeypatch.setattr(server,'INFERENCE_BUDGET_TOKENS',100)
    monkeypatch.setattr(server,'_accumulated_tokens',0)
    with TestClient(server.app) as c:
        r=c.post('/ai/chat/completions',headers={'x-use-replay-fixtures':'true'},json={'messages':[{'role':'user','content':'hello'}],**body})
        assert r.status_code==429
        assert server._accumulated_tokens==0


def test_agent_classes_support_high_value_approved_task(lab,monkeypatch):
    from src.agents.payments_agent import PaymentsAgent
    from src.agents.negotiator_bot import NegotiatorBot
    from src.api.main import app as bank
    from src.core.security import create_jwt_token
    c,_,_=lab
    original=httpx.AsyncClient
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.ASGITransport(app=bank),**kwargs))
    async def run():
        negotiator=NegotiatorBot(base_url='http://bank')
        executor=PaymentsAgent(base_url='http://bank')
        task=await negotiator.delegate_payment_task('case-501',150000,'acc-101')
        proposal=await executor.submit_proposal('acc-102','acc-101',150000)
        async with original(transport=httpx.ASGITransport(app=bank),base_url='http://bank') as client:
            token=create_jwt_token('separate-reviewer','flobank-api',['api:payments:write'],'manager')
            assert (await client.post('/api/v1/approvals/'+proposal['proposal_id']+'/approve',headers={'Authorization':'Bearer '+token})).status_code==200
        result=await executor.dispatch_payment_task(task['task_id'],proposal_id=proposal['proposal_id'])
        assert result['status']=='completed'
        assert result['output']['payment_id']
    asyncio.run(run())


def test_sandbox_deployment_has_no_protected_credentials_or_persistence():
    import yaml
    services=yaml.safe_load(Path('docker-compose.yml').read_text())['services']
    sandbox=services['incident-sandbox']
    assert sandbox['networks']==['incident']
    assert not sandbox.get('ports') and not sandbox.get('volumes')
    assert sandbox['environment']==['W4_SANDBOX_KEY=${W4_SANDBOX_KEY:-}']
    assert sandbox['read_only'] and sandbox['cap_drop']==['ALL']


@pytest.mark.parametrize(('scenario','amount','beneficiary'), [('prohibited_beneficiary',25000,'fraud-account-66'),('excessive_amount',900000000,'vendor-alpha')])
def test_recovery_preserves_attack_args_before_dispatch(lab,monkeypatch,scenario,amount,beneficiary):
    from src.demo import incident
    c,_,_=lab
    run=start(c,'wrong_audience')
    run.update(scenario=scenario,state='running')
    run.pop('arguments',None)
    incident.save(run)
    seen=[]
    original=incident.gateway_client
    class Tools:
        async def __aenter__(self):
            self.client=await original().__aenter__();return self
        async def __aexit__(self,*args):await self.client.__aexit__(*args)
        async def request(self,method,url,**kwargs):
            if url.endswith('/mcp'):
                seen.append(kwargs['json']['params']['arguments'])
                return httpx.Response(200,json={'result':{'isError':True,'content':[{'type':'text','text':'POLICY_DENIED: fixed scenario'}]}})
            return await self.client.request(method,url,**kwargs)
    monkeypatch.setattr(incident,'gateway_client',Tools)
    result=c.post('/demo-api/workshop-4/runs/'+run['run_id']+'/reconcile',json={}).json()
    assert seen[0]['amount']==amount and seen[0]['beneficiary']==beneficiary
    assert result['state']=='denied' and result['effects']['payment_count_delta']==0


def test_live_failure_stays_labelled_without_replay(lab):
    c,_,_=lab
    result=start(c,'live_comparison')
    assert result['inference_mode']=='live' and result['state']=='live_failed'
    assert result['effects']['payment_count_delta']==0
    assert not result.get('sandbox')


def test_live_private_reasoning_never_persists(lab,monkeypatch):
    from src.demo import incident
    c,_,_=lab
    original=incident.gateway_client
    class Live:
        async def __aenter__(self):self.client=await original().__aenter__();return self
        async def __aexit__(self,*args):await self.client.__aexit__(*args)
        async def request(self,method,url,**kwargs):
            if url.endswith('/ai/chat/completions'):
                return httpx.Response(200,json={'model':'live-test','choices':[{'message':{'reasoning_content':'PRIVATE_MODEL_REASONING','content':'<think>PRIVATE_MODEL_REASONING</think>Decline this injected payment.'}}]})
            return await self.client.request(method,url,**kwargs)
    monkeypatch.setattr(incident,'gateway_client',Live)
    result=start(c,'live_comparison')
    assert result['state']=='completed'
    assert 'PRIVATE_MODEL_REASONING' not in json.dumps(result)
    assert 'PRIVATE_MODEL_REASONING' not in incident.load(result['run_id'])[1].__str__()


def test_shared_host_observation_cannot_execute(lab,monkeypatch):
    c,_,_=lab
    monkeypatch.setenv('W4_OBSERVATION_ONLY','true')
    assert c.post('/demo-api/workshop-4/runs',json={'scenario':'permitted_payment','request_id':'hosted'}).status_code==403


def test_profile_lifecycle_stops_presenter_sandbox():
    script=Path('scripts/workshop').read_text()
    teardown=[line for line in script.splitlines() if 'docker compose' in line and ' down ' in line]
    assert len(teardown)==2
    assert all('--profile w4-presenter' in line for line in teardown)
