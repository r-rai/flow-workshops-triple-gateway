import json, pathlib, sys, httpx
sys.path.insert(0,str(pathlib.Path.cwd()))
from workshops.w1.rehearsal_w1 import parse_sse
out=pathlib.Path(__file__).parent
hdr={'Content-Type':'application/json','Accept':'application/json, text/event-stream','X-API-Key':'gate3-secret-token'}
with httpx.Client(timeout=10) as c:
    r=c.post('http://127.0.0.1:9080/mcp',headers=hdr,json={'jsonrpc':'2.0','id':501,'method':'tools/list','params':{}})
    tools=parse_sse(r.text)['result']['tools']
    name=next(t['name'] for t in tools if t['name'].startswith('list_payments'))
    r=c.post('http://127.0.0.1:9080/mcp',headers=hdr,json={'jsonrpc':'2.0','id':502,'method':'tools/call','params':{'name':name,'arguments':{}}})
    data={'catalog_count':len(tools),'curated_paths':list(json.loads(pathlib.Path('workshops/w1/checkpoints/completed/openapi-curated.json').read_text())['paths']),'uncurated_read_tool':name,'status':r.status_code,'response':parse_sse(r.text)}
(out/'w1-supplement.json').write_text(json.dumps(data,indent=2)); print(json.dumps(data,indent=2))
