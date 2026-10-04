import sys,pathlib,json,secrets,time,httpx
sys.path.insert(0,str(pathlib.Path.cwd()))
from src.core.security import create_jwt_token
out=pathlib.Path(__file__).parent
tid=secrets.token_hex(16)
hdr={'Authorization':'Bearer '+create_jwt_token('audit-trace-support','novabank-mcp',['mcp:tools'],role='support_agent'),'traceparent':'00-'+tid+'-'+secrets.token_hex(8)+'-01'}
with httpx.Client(timeout=10) as c:
    r=c.post('http://127.0.0.1:9080/mcp',headers=hdr,json={'jsonrpc':'2.0','id':510,'method':'tools/call','params':{'name':'get_account','arguments':{'id':'acc-101'}}})
    body=r.json(); assert r.status_code==200 and body['result']['isError'] is False
    for _ in range(12):
        time.sleep(1)
        trace=c.get('http://127.0.0.1:16686/api/traces/'+tid)
        if trace.status_code==200 and trace.json().get('data'):break
    services=c.get('http://127.0.0.1:16686/api/services')
    alltraces=c.get('http://127.0.0.1:16686/api/traces',params={'service':'novabank-api','limit':10})
result={'trace_id':tid,'authorized_call':{'status':r.status_code,'response':body},'trace_query':{'status':trace.status_code,'response':trace.json()},'services':services.json(),'recent_api_traces':alltraces.json()}
(out/'trace-readonly.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))
