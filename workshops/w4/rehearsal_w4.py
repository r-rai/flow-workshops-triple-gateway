#!/usr/bin/env python3
"""Technical rehearsal of W4. This is NOT a measured 135-minute human delivery.

Uses fixed Incident Room APIs and independent browser-equivalent sessions. No
reset by default. --outage stops only local OPA and restores it in finally.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import time
import uuid
import httpx


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',default=os.getenv('W4_URL','http://127.0.0.1:9080'))
    parser.add_argument('--outage',action='store_true')
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--vulnerable',action='store_true')
    args=parser.parse_args()
    password=os.getenv('W4_REVIEWER_PASSWORD')
    if not password:
        parser.error('Set W4_REVIEWER_PASSWORD to the configured independent reviewer secret.')
    started=time.monotonic()
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')
    evidence={'kind':'technical_rehearsal','timestamp':stamp,'runs':[],'human_delivery_status':'not_measured'}
    prefix=args.url.rstrip('/')+'/demo-api/workshop-4'
    def request(client,method,path,**kwargs):
        r=client.request(method,prefix+path,**kwargs)
        assert r.status_code==200,f'{path}: HTTP {r.status_code}: {r.text}'
        return r.json()
    with httpx.Client(timeout=90) as requester,httpx.Client(timeout=90) as reviewer:
        for client in (requester,reviewer):
            r=client.post(args.url+'/demo-api/login',json={'email':'maya@flobank.demo','password':'flo-demo'})
            assert r.status_code==200
        request(reviewer,'POST','/reviewer-session',json={'password':password})
        readiness=request(requester,'GET','/readiness')
        assert all(c['reachable'] for c in readiness['checks'].values()),readiness
        evidence['readiness']=readiness
        scenarios=[('budget_denial','denied'),('prohibited_beneficiary','denied'),('excessive_amount','denied'),('wrong_audience','denied'),('insufficient_scope','denied'),('scope_escalation','denied'),('valid_exchange','completed'),('permitted_payment','completed')]
        if args.vulnerable:
            scenarios.insert(0,('vulnerable_replay','completed'))
        if args.live:
            scenarios.append(('live_comparison',None))
        for scenario,expected in scenarios:
            key=uuid.uuid4().hex
            run=request(requester,'POST','/runs',json={'scenario':scenario,'request_id':key})
            if expected:
                assert run['state']==expected,run
            else:
                assert run['state'] in ('completed','live_failed'),run
                assert run['inference_mode']=='live'
            assert run['effects']['payment_count_delta']==(1 if scenario=='permitted_payment' else 0),run
            if scenario=='vulnerable_replay':
                assert run['sandbox']['effects']['balance_delta']==-900000000
            assert request(requester,'POST','/runs',json={'scenario':scenario,'request_id':key})['run_id']==run['run_id']
            assert request(requester,'GET','/runs/'+run['run_id'])==run
            evidence['runs'].append(run)
            print(scenario,run['state'],run['effects']['balance_delta'])
        if args.outage:
            subprocess.run(['docker','compose','stop','opa'],check=True)
            try:
                run=request(requester,'POST','/runs',json={'scenario':'policy_outage','request_id':uuid.uuid4().hex})
                assert run['state']=='denied' and run['outage_verified'],run
                assert run['effects']['payment_count_delta']==0
                evidence['runs'].append(run)
            finally:
                subprocess.run(['docker','compose','start','opa'],check=True)
        run=request(requester,'POST','/runs',json={'scenario':'legitimate_delegation','request_id':uuid.uuid4().hex})
        assert run['state']=='awaiting_review'
        path='/runs/'+run['run_id']
        assert requester.post(prefix+path+'/decision',json={'decision':'approve'}).status_code==403
        result=request(reviewer,'POST',path+'/decision',json={'decision':'approve'})
        assert result['state']=='completed',result
        assert result['effects']['payment_count_delta']==1 and result['effects']['balance_delta']==-150000
        assert result['task']['output']['payment_id']==result['payment']['payment_id']
        for label,code in [('Self approval',403),('Foreign task access',403),('Unauthorized completion',403),('Changed arguments',400),('Mismatched payment binding',400)]:
            assert any(e['label']==label and e['status_code']==code for e in result['events']),(label,result)
        assert request(reviewer,'POST',path+'/decision',json={'decision':'approve'})==result
        evidence['runs'].append(result)
        for run in evidence['runs']:
            for _ in range(8):
                checked=request(requester,'POST','/runs/'+run['run_id']+'/traces',json={})
                if checked['trace_status']=='observed':
                    break
                time.sleep(.5)
            run.update(trace_status=checked['trace_status'],trace_services=checked.get('trace_services',[]))
        evidence['elapsed_seconds']=round(time.monotonic()-started,2)
        evidence['trace_status']='observed' if all(r['trace_status']=='observed' for r in evidence['runs']) else 'incomplete'
    path=Path('workshops/w4/evidence')/('incident-'+stamp+'.json')
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(evidence,indent=2)+'\n')
    print('Technical evidence:',path,'elapsed seconds:',evidence['elapsed_seconds'],'traces:',evidence['trace_status'])

if __name__=='__main__':
    main()
