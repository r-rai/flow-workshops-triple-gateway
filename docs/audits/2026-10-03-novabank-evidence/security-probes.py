import json,pathlib,time,httpx
from src.core.security import create_jwt_token
from jose import jwt
from src.core.config import settings
out=pathlib.Path('/tmp/novabank-audit-20261003'); base='http://127.0.0.1:9080';results={}
def headers(sub,scopes,role='agent',aud='novabank-api'):
 return {'X-API-Key':'gate3-secret-token','Authorization':'Bearer '+create_jwt_token(sub,aud,scopes,role)}
def record(name,r):
 results[name]={'status':r.status_code,'body':r.json() if 'json' in r.headers.get('content-type','') else r.text[:300]};print(name,results[name]);return r
with httpx.Client(timeout=10) as c:
 owner=headers('audit-owner',['api:a2a:tasks']); rogue=headers('audit-rogue',['api:payments:write']);viewer=headers('audit-viewer',[],'viewer');pay=headers('audit-pay-agent',['api:payments:write']);mgr=headers('audit-manager',['api:payments:write'],'manager')
 t=record('owner_task_create',c.post(base+'/api/v1/a2a/tasks',headers=owner,json={'task_type':'propose_payment','input':{'amount':100}})).json()['task_id']
 record('foreign_task_read',c.get(base+'/api/v1/a2a/tasks/'+t,headers=rogue))
 record('foreign_task_complete',c.post(base+'/api/v1/a2a/tasks/'+t+'/complete',headers=rogue,json={'audit':'foreign principal overwrote task'}))
 record('owner_task_after_foreign_completion',c.get(base+'/api/v1/a2a/tasks/'+t,headers=owner))
 record('task_create_without_scope',c.post(base+'/api/v1/a2a/tasks',headers=viewer,json={'task_type':'propose_payment','input':{}}))
 mcp=headers('audit-support',['mcp:tools'],'support_agent','novabank-mcp')
 r=record('mcp_approval_required',c.post(base+'/mcp',headers=mcp,json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'create_payment','arguments':{'account_id':'acc-101','amount':500000,'currency':'INR','beneficiary':'vendor-alpha'}}}))
 prop=json.loads(r.json()['result']['content'][0]['text'])['proposal_id']
 record('mcp_proposal_lookup',c.get(base+'/api/v1/approvals/'+prop,headers=pay))
 body={'account_id':'acc-102','amount':150000,'currency':'INR','beneficiary':'acc-101'}
 prop=record('api_proposal_create',c.post(base+'/api/v1/payments/proposals',headers=pay,json=body)).json()['proposal_id']
 record('self_approval',c.post(base+'/api/v1/approvals/'+prop+'/approve',headers=pay))
 record('manager_approval',c.post(base+'/api/v1/approvals/'+prop+'/approve',headers=mgr))
 record('tamper_above_threshold',c.post(base+'/api/v1/payments',headers=pay,json={**body,'amount':200000,'proposal_id':prop}))
 record('tamper_below_threshold',c.post(base+'/api/v1/payments',headers={**pay,'Idempotency-Key':'audit-low-tamper'},json={**body,'amount':1000,'beneficiary':'fraud-account-66','proposal_id':prop}))
 record('proposal_after_low_tamper',c.get(base+'/api/v1/approvals/'+prop,headers=pay))
 prop2=c.post(base+'/api/v1/payments/proposals',headers=pay,json=body).json()['proposal_id']
 record('viewer_rejects_other_proposal',c.post(base+'/api/v1/approvals/'+prop2+'/reject',headers=viewer))
 claims={'sub':'audit-wrong-issuer','aud':'novabank-api','iss':'https://untrusted.invalid','exp':int(time.time())+120,'scope':'api:accounts:read','role':'viewer'}
 token=jwt.encode(claims,settings.JWT_SECRET_KEY,algorithm=settings.JWT_ALGORITHM)
 record('wrong_issuer_api',c.get(base+'/api/v1/accounts/acc-101',headers={'X-API-Key':'gate3-secret-token','Authorization':'Bearer '+token}))
 record('bearer_without_static_key',c.get(base+'/api/v1/accounts/acc-101',headers={'Authorization':pay['Authorization']}))
 record('missing_mcp_scope_read',c.post(base+'/mcp',headers=headers('audit-no-mcp-scope',[],'support_agent','novabank-mcp'),json={'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'get_account','arguments':{'id':'acc-101'}}}))
 record('oauth_token_endpoint',c.post(base+'/oauth/token',data={'grant_type':'urn:ietf:params:oauth:grant-type:token-exchange'}))
 record('jaeger_services',c.get('http://127.0.0.1:16686/api/services'))
(out/'security-probes.json').write_text(json.dumps(results,indent=2))
