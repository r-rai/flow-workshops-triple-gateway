import asyncio,json,pathlib,subprocess,time,httpx
from temporalio.client import Client
from temporalio.common import WorkflowIDReusePolicy
from temporalio.exceptions import WorkflowAlreadyStartedError
from src.worker.workflow import DisputeResolutionWorkflow,DisputeInput
from workshops.w3.client import emit_dispute
out=pathlib.Path('/tmp/novabank-audit-20261003')
async def main():
 client=await Client.connect('localhost:7233'); original=client.get_workflow_handle('dispute-case-case-501'); before_desc=await original.describe()
 wid='audit-recovery-'+str(int(time.time()));h=await client.start_workflow(DisputeResolutionWorkflow.run,DisputeInput(case_id='case-501'),id=wid,task_queue='dispute-resolution-queue',id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE)
 for i in range(60):
  status=await h.query('get_status')
  if status['current_phase']=='WAITING_FOR_APPROVAL':break
  await asyncio.sleep(1)
 else:raise RuntimeError('Not waiting before restart')
 print('Before kill/restart',status,flush=True)
 r=subprocess.run(['docker','kill','novabank-workshops-worker-1'],capture_output=True,text=True);r.check_returncode()
 r=subprocess.run(['docker','compose','--profile','w4','restart','temporal'],capture_output=True,text=True);r.check_returncode()
 subprocess.run(['docker','start','novabank-workshops-worker-1'],capture_output=True,text=True,check=True)
 recovered=None
 for i in range(60):
  try:
   client=await Client.connect('localhost:7233');h=client.get_workflow_handle(wid);recovered=await asyncio.wait_for(h.query('get_status'),timeout=4)
   if recovered['current_phase']=='WAITING_FOR_APPROVAL':break
  except Exception:pass
  await asyncio.sleep(1)
 assert recovered and recovered['current_phase']=='WAITING_FOR_APPROVAL',recovered
 print('After SIGKILL and Temporal server restart',recovered,flush=True)
 before=len(httpx.get('http://127.0.0.1:9080/api/v1/payments',headers={'X-API-Key':'gate3-secret-token'}).json())
 await h.signal('human_approval',{'approved':False,'reviewer':'audit-reviewer','comments':'test rejection after recovery'})
 result=await asyncio.wait_for(h.result(),timeout=30)
 assert result['result']['status']=='REJECTED',result
 after=len(httpx.get('http://127.0.0.1:9080/api/v1/payments',headers={'X-API-Key':'gate3-secret-token'}).json());assert before==after
 await emit_dispute('localhost:9092','case-501','cust-101');await asyncio.sleep(5)
 desc=await client.get_workflow_handle('dispute-case-case-501').describe();assert desc.run_id==before_desc.run_id
 latest=len(httpx.get('http://127.0.0.1:9080/api/v1/payments',headers={'X-API-Key':'gate3-secret-token'}).json());assert latest==after
 history=await h.fetch_history()
 evidence={'workflow_id':wid,'before_crash':status,'after_worker_sigkill_and_temporal_restart':recovered,'rejection_result':result,'payment_counts':[before,after,latest],'original_workflow_run_id_before':before_desc.run_id,'original_workflow_run_id_after_redelivery':desc.run_id,'history_event_count':len(history.events),'recovery_verified':True,'rejection_no_payment_verified':True,'completed_kafka_redelivery_no_duplicate_verified':True}
 (out/'durability-probe.json').write_text(json.dumps(evidence,indent=2));(out/'durability-history.json').write_text(history.to_json());print(json.dumps(evidence,indent=2),flush=True)
asyncio.run(main())
