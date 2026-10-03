import json,pathlib,httpx,subprocess
from src.core.security import create_jwt_token
out=pathlib.Path('/tmp/novabank-audit-20261003');base='http://127.0.0.1:9080';key={'X-API-Key':'gate3-secret-token'};results={}
def save(name,r):results[name]={'status':r.status_code,'body':r.json()};print(name,results[name]);return r
with httpx.Client(timeout=10) as c:
 restricted={**key,'Authorization':'Bearer '+create_jwt_token('audit-payment-agent','novabank-api',['api:payments:write'],'agent')}
 prop=c.post(base+'/api/v1/payments/proposals',headers=restricted,json={'account_id':'acc-102','amount':150000,'currency':'INR','beneficiary':'acc-101'}).json()['proposal_id']
 save('agent_self_approval_with_bearer',c.post(base+'/api/v1/approvals/'+prop+'/approve',headers=restricted))
 save('same_agent_key_without_bearer_approves',c.post(base+'/api/v1/approvals/'+prop+'/approve',headers=key))
 save('proposal_approved_by_fallback_admin',c.get(base+'/api/v1/approvals/'+prop,headers=restricted))
 mcp={**key,'Authorization':'Bearer '+create_jwt_token('audit-opa-outage','novabank-mcp',['mcp:tools'],'support_agent')}
 before=c.get(base+'/api/v1/accounts/acc-101',headers=key).json()['balance'];before_count=len(c.get(base+'/api/v1/payments',headers=key).json())
 subprocess.run(['docker','pause','novabank-workshops-opa-1'],check=True,capture_output=True)
 try:
  r=save('payment_during_opa_timeout',c.post(base+'/mcp',headers=mcp,json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'create_payment','arguments':{'account_id':'acc-101','amount':1000,'currency':'INR','beneficiary':'vendor-alpha'}}}))
  assert r.json()['result']['isError'] is True and 'FAIL_CLOSED' in r.json()['result']['content'][0]['text']
 finally:subprocess.run(['docker','unpause','novabank-workshops-opa-1'],check=True,capture_output=True)
 after=c.get(base+'/api/v1/accounts/acc-101',headers=key).json()['balance'];after_count=len(c.get(base+'/api/v1/payments',headers=key).json());assert before==after and before_count==after_count
 results['opa_outage_no_mutation']={'balances':[before,after],'payment_counts':[before_count,after_count],'verified':True}
(out/'final-security-probes.json').write_text(json.dumps(results,indent=2))
