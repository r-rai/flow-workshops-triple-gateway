import subprocess,pathlib,json,os,time,runpy,httpx,shutil
out=pathlib.Path('/tmp/novabank-audit-20261003');results=json.loads((out/"startup-results.json").read_text())
def run(label,cmd,timeout=180):
 start=time.time()
 with (out/f'{label}.log').open('w') as f:
  try:rc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'PYTHONPATH':'.','PYTHONUNBUFFERED':'1'},timeout=timeout).returncode
  except subprocess.TimeoutExpired:rc=124
 result={'label':label,'command':cmd,'exit_code':rc,'seconds':round(time.time()-start,2)};results.append(result);(out/'startup-results.json').write_text(json.dumps(results,indent=2));print(json.dumps(result),flush=True);print((out/f'{label}.log').read_text()[-1300:],flush=True);return rc
def diagnostics(profile):
 for name,cmd in [('apisix-errors',['docker','logs','--tail','60','novabank-workshops-apisix-1']),('api-log',['docker','logs','--tail','35','novabank-workshops-api-1'])]:
  r=subprocess.run(cmd,capture_output=True,text=True);(out/f'{profile}-{name}.log').write_text(r.stdout+r.stderr)
def wait_api():
 for i in range(60):
  try:
   if httpx.get('http://127.0.0.1:9080/api/v1/accounts/acc-101',headers={'X-API-Key':'gate3-secret-token'},timeout=2).status_code==200:return
  except Exception:pass
  time.sleep(0.5)
 raise RuntimeError('API never ready')
diagnostics('w1')
rc=run('w2-rehearsal-recheck',['.venv/bin/python','workshops/w2/rehearsal_w2.py']);diagnostics('w2')
if rc==0:shutil.copy2('workshops/w2/evidence/rehearsal-evidence.json',out/'w2-rehearsal-evidence.json')
else:
 script=out/'w2-readiness-guard.py'
 script.write_text('''import runpy,time,httpx,sys\nns=runpy.run_path("workshops/w2/rehearsal_w2.py",run_name="audit_harness")\nmain=ns["main"]; original=main.__globals__["run_cmd"]\ndef guarded(cmd):\n result=original(cmd)\n if cmd=="./scripts/workshop switch w2":\n  if result.returncode:raise RuntimeError(result.stderr)\n  for i in range(60):\n   try:\n    r=httpx.get("http://127.0.0.1:9080/api/v1/accounts/acc-101",headers={"X-API-Key":"gate3-secret-token"},timeout=2)\n    if r.status_code==200:break\n   except Exception:pass\n   time.sleep(0.5)\n  else:raise RuntimeError("API startup timeout")\n return result\nmain.__globals__["run_cmd"]=guarded\nsys.exit(main())\n''')
 rc2=run('w2-rehearsal-readiness-guard',['.venv/bin/python',str(script)])
 if rc2==0:shutil.copy2('workshops/w2/evidence/rehearsal-evidence.json',out/'w2-readiness-guard-evidence.json')
run('w2-verify-recheck',['./scripts/workshop','verify','w2'])
run('w4-restore',['./scripts/workshop','switch','w4']);wait_api();run('w4-final-verify',['./scripts/workshop','verify','w4'])
