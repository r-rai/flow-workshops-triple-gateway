import json,os,tempfile,pathlib,sys,time,asyncio
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path.cwd()))
scratch=tempfile.TemporaryDirectory(prefix='novabank-final-controls-')
os.environ['DATABASE_URL']='sqlite:///'+scratch.name+'/audit.sqlite'
os.environ['ENABLE_TELEMETRY']='false'
import httpx
from fastapi.testclient import TestClient
from src.adapter import server
from src.api.main import app
from src.core.security import create_jwt_token
from jose import jwt
from src.core.config import settings
from src.core.database import engine
out=pathlib.Path(__file__).parent
results={}
real_client=httpx.Client
with TestClient(server.app) as client:
    failures=[]
    for mode in ['503','timeout','missing_id','invalid_json']:
        def handler(req):
            if str(req.url)==server.OPA_URL: return httpx.Response(200,json={'result':{'decision':'approval_required','reason':'audit'}})
            if mode=='503': return httpx.Response(503,json={'detail':'Injected backend failure'})
            if mode=='timeout': raise httpx.ReadTimeout('Injected proposal write timeout',request=req)
            if mode=='missing_id': return httpx.Response(201,json={})
            return httpx.Response(201,content='invalid json')
        def fake(*args,**kwargs): return real_client(transport=httpx.MockTransport(handler),**kwargs)
        with patch.object(server.httpx,'Client',fake):
            r=client.post('/mcp',headers={'X-API-Key':server.GATE3_KEY},json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'create_payment','arguments':{'account_id':'acc-101','amount':500000,'currency':'INR','beneficiary':'vendor-beta'}}})
        body=r.json(); text=json.loads(body['result']['content'][0]['text'])
        assert body['result']['isError'] is True and text['error']=='PROPOSAL_PERSISTENCE_FAILED' and 'proposal_id' not in text
        failures.append({'mode':mode,'response':body})
    results['proposal_persistence_failures']=failures
    opa=[]
    for decision in ['allow','deny','unexpected',None,'ALLOW','',{},[]]:
        calls=[]
        def handler(req):
            if str(req.url)==server.OPA_URL: return httpx.Response(200,json={'result':{'decision':decision,'reason':'audit'}})
            calls.append(str(req.url)); return httpx.Response(200,json={'id':'acc-101'})
        def fake(*args,**kwargs): return real_client(transport=httpx.MockTransport(handler),**kwargs)
        with patch.object(server.httpx,'Client',fake):
            r=client.post('/mcp',headers={'X-API-Key':server.GATE3_KEY},json={'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'get_account','arguments':{'id':'acc-101'}}})
        assert bool(calls)==(decision=='allow')
        opa.append({'decision':decision,'response':r.json(),'downstream_calls':calls})
    results['opa_allowlist']=opa
    bearer=create_jwt_token('audit-agent','novabank-mcp',['mcp:tools'],role='agent')
    def handler(req): return httpx.Response(503,json={'detail':'Injected exchange failure'})
    def fake(*args,**kwargs): return real_client(transport=httpx.MockTransport(handler),**kwargs)
    with patch.object(server.httpx,'Client',fake),patch.object(server,'evaluate_opa_policy',return_value=('allow','audit')):
        r=client.post('/mcp',headers={'Authorization':'Bearer '+bearer},json={'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'get_account','arguments':{'id':'acc-101'}}})
    results['exchange_failure_no_fallback']={'status':r.status_code,'response':r.json()}; assert r.status_code==503
    # Replay toggle and budget are isolated from the deployed instance.
    with patch.dict(os.environ,{'USE_REPLAY_FIXTURES':'false'}):
        r=client.post('/ai/chat/completions',json={'messages':[{'role':'user','content':'audit'}]})
    results['replay_false']=r.json()
    with patch.object(server,'_accumulated_tokens',server.INFERENCE_BUDGET_TOKENS):
        r=client.post('/ai/chat/completions',json={'messages':[]})
    results['budget_exhaustion']={'status':r.status_code,'response':r.json()}; assert r.status_code==429
with TestClient(app) as client:
    key={'X-API-Key':settings.API_KEY_SECRET}
    requester='audit-requester'
    agent=create_jwt_token(requester,'novabank-api',['api:payments:write'],role='agent')
    p=client.post('/api/v1/payments/proposals',headers={'Authorization':'Bearer '+agent},json={'account_id':'acc-102','amount':150000,'beneficiary':'acc-101','currency':'INR'}).json()['proposal_id']
    manager=create_jwt_token('audit-delegated-manager','novabank-api',['api:payments:write','api:accounts:read'],role='manager',delegated_by=requester)
    r=client.post('/api/v1/approvals/'+p+'/approve',headers={'Authorization':'Bearer '+manager})
    before={'status':r.status_code,'response':r.json()}; assert r.status_code==403
    r=client.post('/oauth/token',data={'grant_type':'urn:ietf:params:oauth:grant-type:token-exchange','subject_token':manager,'subject_token_type':'urn:ietf:params:oauth:token-type:access_token','audience':'novabank-api','scope':'api:payments:write'})
    assert r.status_code==200
    exchanged=r.json()['access_token']
    claims=jwt.decode(exchanged,settings.JWT_SECRET_KEY,algorithms=[settings.JWT_ALGORITHM],audience='novabank-api')
    r=client.post('/api/v1/approvals/'+p+'/approve',headers={'Authorization':'Bearer '+exchanged})
    results['delegation_approval_after_exchange']={'before_exchange':before,'exchanged_act':claims['act'],'after_exchange':{'status':r.status_code,'response':r.json()}}
    # Expired or malformed tokens should not be trusted; exercise missing exp signed by the lab issuer.
    bare={'iss':settings.JWT_ISSUER,'sub':'audit-no-exp','aud':'novabank-mcp','role':'agent','scope':'mcp:tools'}
    tok=jwt.encode(bare,settings.JWT_SECRET_KEY,algorithm=settings.JWT_ALGORITHM)
    r=client.post('/oauth/token',data={'grant_type':'urn:ietf:params:oauth:grant-type:token-exchange','subject_token':tok,'subject_token_type':'urn:ietf:params:oauth:token-type:access_token','scope':'api:payments:write'})
    results['missing_exp_token']={'status':r.status_code,'issued_scope':r.json().get('scope')}
(out/'isolated-controls.json').write_text(json.dumps(results,indent=2)); print(json.dumps(results,indent=2))
engine.dispose(); scratch.cleanup()
