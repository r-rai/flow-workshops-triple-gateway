import asyncio, json, pathlib, sys, subprocess, time
sys.path.insert(0,str(pathlib.Path.cwd()))
import httpx
from temporalio.client import Client
from src.worker.workflow import DisputeResolutionWorkflow, DisputeInput
out=pathlib.Path(__file__).parent
async def main():
    client=await Client.connect('localhost:7233')
    snapshots={}
    for case in ['case-501','case-502']:
        h=client.get_workflow_handle('dispute-case-'+case)
        history=await h.fetch_history()
        (out/(case+'-temporal-history.json')).write_text(history.to_json())
        snapshots[case]={'result':await h.result(),'status':str((await h.describe()).status)}
    h=await client.start_workflow(DisputeResolutionWorkflow.run,DisputeInput(case_id='case-502',customer_id='audit'),id='audit-hard-crash-'+str(int(time.time())),task_queue='dispute-resolution-queue')
    for _ in range(40):
        try:
            before=await asyncio.wait_for(h.query('get_status'),3)
            if before['current_phase']=='WAITING_FOR_APPROVAL': break
        except Exception: pass
        await asyncio.sleep(.5)
    else: raise RuntimeError('Supplemental workflow did not reach approval wait')
    subprocess.run(['docker','kill','--signal','SIGKILL','novabank-workshops-worker-1'],check=True)
    # unless-stopped may already restart the worker after SIGKILL.
    subprocess.run(['docker','start','novabank-workshops-worker-1'],check=True)
    for _ in range(40):
        try:
            after=await asyncio.wait_for(h.query('get_status'),3)
            if after['current_phase']=='WAITING_FOR_APPROVAL': break
        except Exception: pass
        await asyncio.sleep(.5)
    else: raise RuntimeError('Worker did not recover durable wait after SIGKILL')
    await h.signal('human_approval',{'approved':False,'reviewer':'audit-risk-lead','comments':'Supplemental crash recovery'})
    result=await asyncio.wait_for(h.result(),60)
    assert result['phase']=='COMPLETED' and result['result']['status']=='REJECTED'
    async with httpx.AsyncClient() as http:
        hdr={'X-API-Key':'gate3-secret-token'}
        case=(await http.get('http://127.0.0.1:9080/api/v1/cases/case-502',headers=hdr)).json()
        payments=(await http.get('http://127.0.0.1:9080/api/v1/payments',headers=hdr)).json()
    assert case['status']=='closed'
    assert len(payments)==1
    snapshots['hard_crash']={'signal':'SIGKILL','before':before,'after':after,'result':result,'case_502_status':case['status'],'total_payments':len(payments)}
    (out/'w3-supplement.json').write_text(json.dumps(snapshots,indent=2)); print(json.dumps(snapshots,indent=2))
asyncio.run(main())
