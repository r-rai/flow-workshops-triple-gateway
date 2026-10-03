import os,pathlib,json,time,threading,concurrent.futures
out=pathlib.Path('/tmp/novabank-audit-20261003');dbfile=out/'concurrency.sqlite'
if dbfile.exists():dbfile.unlink()
os.environ['DATABASE_URL']='sqlite:///'+str(dbfile)
from src.core.database import Base,engine,SessionLocal
from src.services.seed import reset_and_seed_db
from src.services.approvals import create_proposal_service,approve_proposal_service
from src.services.banking import execute_payment_service
from src.core.security import Principal
from src.models.schemas import PaymentProposalRequest,PaymentExecuteRequest
from src.models.db_models import PaymentProposal,PaymentRecord,Account
from sqlalchemy import event,select
Base.metadata.create_all(engine);db=SessionLocal();reset_and_seed_db(db)
p=Principal('audit-pay','agent',['api:payments:write']);mgr=Principal('audit-manager','manager',['api:payments:write'])
req={'account_id':'acc-102','amount':150000,'beneficiary':'acc-101','currency':'INR'}
prop=create_proposal_service(db,p,PaymentProposalRequest(**req)).proposal_id;approve_proposal_service(db,mgr,prop);db.close()
barrier=threading.Barrier(2)
@event.listens_for(engine,'after_cursor_execute')
def synchronize(conn,cursor,statement,params,ctx,many):
 if threading.current_thread().name.startswith('race') and statement.lstrip().startswith('SELECT') and 'FROM payment_proposals' in statement:
  barrier.wait(timeout=10)
def run(i):
 db=SessionLocal()
 try:
  res=execute_payment_service(db,p,PaymentExecuteRequest(**req,proposal_id=prop),idempotency_key=f'concurrent-{i}')
  return {'success':True,'response':res.model_dump()}
 except Exception as e:return {'success':False,'error':str(e)}
 finally:db.close()
with concurrent.futures.ThreadPoolExecutor(max_workers=2,thread_name_prefix='race') as pool:
 result=list(pool.map(run,[1,2]))
db=SessionLocal();summary={'sqlite_for_update_sql':str(select(PaymentProposal).with_for_update().compile(engine)),'concurrent_calls':result,'payment_record_count':db.query(PaymentRecord).filter_by(proposal_id=prop).count(),'proposal_status':db.get(PaymentProposal,prop).status,'remaining_balance':db.get(Account,'acc-102').balance};db.close()
print('CONCURRENT SINGLE-USE',json.dumps(summary,indent=2))
from unittest.mock import patch
from fastapi.testclient import TestClient
import httpx
from src.adapter import server
backend_calls=[]
def handler(request):
 if 'opa:' in str(request.url):return httpx.Response(200,json={'result':{'decision':'unexpected','reason':'bad-policy-output'}})
 backend_calls.append(str(request.url));return httpx.Response(200,json={'payment_id':'mock-only','status':'COMPLETED'})
real_client=httpx.Client
def fake_client(*args,**kwargs):return real_client(transport=httpx.MockTransport(handler),**kwargs)
client=TestClient(server.app)
with patch.object(server.httpx,'Client',fake_client):
 r=client.post('/mcp',headers={'X-API-Key':server.GATE3_KEY},json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'create_payment','arguments':{'account_id':'acc-101','amount':1000,'currency':'INR','beneficiary':'vendor-alpha'}}})
summary['unexpected_opa_decision']={'response':r.json(),'downstream_calls':backend_calls}
print('OPA UNKNOWN DECISION',json.dumps(summary['unexpected_opa_decision'],indent=2))
(out/'isolated-probes.json').write_text(json.dumps(summary,indent=2))
