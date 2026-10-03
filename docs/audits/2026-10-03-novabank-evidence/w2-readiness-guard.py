import runpy,time,httpx,sys
ns=runpy.run_path("workshops/w2/rehearsal_w2.py",run_name="audit_harness")
main=ns["main"]; original=main.__globals__["run_cmd"]
def guarded(cmd):
 result=original(cmd)
 if cmd=="./scripts/workshop switch w2":
  if result.returncode:raise RuntimeError(result.stderr)
  for i in range(60):
   try:
    r=httpx.get("http://127.0.0.1:9080/api/v1/accounts/acc-101",headers={"X-API-Key":"gate3-secret-token"},timeout=2)
    if r.status_code==200:break
   except Exception:pass
   time.sleep(0.5)
  else:raise RuntimeError("API startup timeout")
 return result
main.__globals__["run_cmd"]=guarded
sys.exit(main())
