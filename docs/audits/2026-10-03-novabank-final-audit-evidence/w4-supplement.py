import json,pathlib,sys,httpx,secrets,asyncio
sys.path.insert(0,str(pathlib.Path.cwd()))
from src.core.security import create_jwt_token
out=pathlib.Path(__file__).parent
base='http://127.0.0.1:9080'
token=create_jwt_token('audit-task-owner',audience='novabank-api',scopes=['api:a2a:tasks'],role='agent')
hdr={'Authorization':'Bearer '+token,'X-API-Key':'gate3-secret-token'}
data={}
with httpx.Client(timeout=10) as c:
    r=c.post(base+'/api/v1/a2a/tasks',headers=hdr,json={'task_type':'propose_payment','input':{'amount':77777,'destination_account':'acc-101','case_id':'case-501'}})
    r.raise_for_status(); task=r.json()
    r=c.post(base+'/api/v1/a2a/tasks/'+task['task_id']+'/complete',headers=hdr,json={'payment_id':'nonexistent-audit-payment','status':'SETTLED'})
    data['fabricated_completion']={'status':r.status_code,'task':r.json()}
    p=c.get(base+'/api/v1/payments',headers={'X-API-Key':'gate3-secret-token'}); data['payments']=p.json()
    evidence=json.loads((out/'w4-rehearsal-evidence.json').read_text())
    prop=evidence['segments']['segment7']['proposal_id']
    data['consumed_proposal']=c.get(base+'/api/v1/approvals/'+prop,headers={'X-API-Key':'gate3-secret-token'}).json()
    data['account_102']=c.get(base+'/api/v1/accounts/acc-102',headers={'X-API-Key':'gate3-secret-token'}).json()
    trace_id=secrets.token_hex(16); parent=secrets.token_hex(8)
    mcp_token=create_jwt_token('audit-trace-agent',audience='novabank-mcp',scopes=['mcp:tools'],role='agent')
    r=c.post(base+'/mcp',headers={'Authorization':'Bearer '+mcp_token,'traceparent':f'00-{trace_id}-{parent}-01'},json={'jsonrpc':'2.0','id':503,'method':'tools/call','params':{'name':'get_account','arguments':{'id':'acc-101'}}})
    data['trace_call']={'status':r.status_code,'response':r.json(),'trace_id':trace_id}
    import time
    for _ in range(12):
        time.sleep(1)
        r=c.get('http://127.0.0.1:16686/api/traces/'+trace_id)
        if r.status_code==200 and r.json().get('data'): break
    trace=r.json(); (out/'jaeger-trace.json').write_text(json.dumps(trace,indent=2))
    data['trace_services']=list({p['serviceName'] for t in (trace.get('data') or []) for p in t.get('processes',{}).values()})
    data['trace_spans']=[s['operationName'] for t in (trace.get('data') or []) for s in t.get('spans',[])]
(out/'w4-supplement.json').write_text(json.dumps(data,indent=2)); print(json.dumps(data,indent=2))
