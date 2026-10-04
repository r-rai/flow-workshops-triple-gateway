import subprocess, json, pathlib, threading, time, shutil, datetime, sqlite3, hashlib, os
root=pathlib.Path.cwd(); out=root/os.getenv('NOVABANK_AUDIT_EVIDENCE_DIR','docs/audits/2026-10-03-novabank-final-audit-evidence'); backup=pathlib.Path('/tmp/novabank-final-audit-backup-20261003')
backup.mkdir(exist_ok=True)
def capture(cmd): return subprocess.check_output(cmd,text=True)
def save(name,data): (out/name).write_text(json.dumps(data,indent=2))
def protected():
    data=json.loads(capture(['docker','inspect','caddy','portainer','uptime-kuma','dozzle']))
    return [{'name':c['Name'],'id':c['Id'],'started':c['State']['StartedAt'],'running':c['State']['Running'],'restarts':c['RestartCount'],'health':c['State'].get('Health',{}).get('Status'),'ports':c['NetworkSettings']['Ports']} for c in data]
save('protected-before.json',protected())
save('metadata.json',{'head':capture(['git','rev-parse','HEAD']).strip(),'branch':capture(['git','branch','--show-current']).strip(),'started':datetime.datetime.now(datetime.timezone.utc).isoformat(),'host':capture(['hostname']).strip(),'original_profile':(root/'.active_profile').read_text().strip()})
for w in range(1,5): shutil.copy2(root/f'workshops/w{w}/evidence/rehearsal-evidence.json',backup/f'w{w}-evidence.json')
for service,path in [('api','/app/data/novabank.sqlite'),('temporal','/data/temporal.sqlite')]:
    code=f'import sqlite3; s=sqlite3.connect({path!r}); d=sqlite3.connect("/tmp/final-audit-backup.sqlite"); s.backup(d); d.close(); s.close()'
    subprocess.run(['docker','exec',f'novabank-workshops-{service}-1','python','-c',code],check=True)
    subprocess.run(['docker','cp',f'novabank-workshops-{service}-1:/tmp/final-audit-backup.sqlite',str(backup/f'{service}.sqlite')],check=True)
    assert sqlite3.connect(backup/f'{service}.sqlite').execute('pragma integrity_check').fetchone()[0]=='ok'
stop=threading.Event()
def sample():
    with (out/'memory-samples.jsonl').open('w') as f:
        while not stop.is_set():
            try:
                ids=capture(['docker','compose','ps','-q']).split()
                if ids:
                    r=subprocess.run(['docker','stats','--no-stream','--format','{{json .}}',*ids],capture_output=True,text=True,timeout=12)
                    f.write(json.dumps({'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stats':[json.loads(l) for l in r.stdout.splitlines() if l],'host':capture(['free','-b'])})+'\n'); f.flush()
            except Exception as e: f.write(json.dumps({'error':str(e)})+'\n')
            stop.wait(1)
t=threading.Thread(target=sample); t.start(); results=[]
def run(name,cmd,timeout=300):
    begin=time.time()
    with (out/f'{name}.log').open('w') as f:
        try: code=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=timeout).returncode
        except subprocess.TimeoutExpired: code=124
    item={'name':name,'command':cmd,'exit_code':code,'seconds':round(time.time()-begin,2)}; results.append(item)
    save('results.json',results); print(json.dumps(item),flush=True)
    return code
try:
    run('preflight',['./scripts/workshop','preflight'])
    if not os.getenv('NOVABANK_SKIP_FOUNDATION'): run('foundation-tests',['.venv/bin/python','-m','pytest','-q','tests/test_api_foundation.py'])
    for w in range(1,5):
        p=f'w{w}'
        if run(f'{p}-switch',['./scripts/workshop','switch',p]): continue
        run(f'{p}-reset',['./scripts/workshop','reset',p,'--yes'])
        verify_code=run(f'{p}-verify',['./scripts/workshop','verify',p])
        if verify_code: run(f'{p}-gateway-errors',['docker','logs','--tail','100','novabank-workshops-apisix-1'])
        begin=time.time()
        code=run(f'{p}-rehearsal',['.venv/bin/python',f'workshops/{p}/rehearsal_{p}.py'])
        e=root/f'workshops/{p}/evidence/rehearsal-evidence.json'
        fresh=e.stat().st_mtime>=begin
        save(f'{p}-freshness.json',{'fresh':fresh,'exit_code':code,'mtime':e.stat().st_mtime,'started':begin})
        if fresh: shutil.copy2(e,out/f'{p}-rehearsal-evidence.json')
        if verify_code: run(f'{p}-verify-recheck',['./scripts/workshop','verify',p])
        probe=out/f'{p}-supplement.py'
        if probe.exists(): run(f'{p}-supplement',['.venv/bin/python',str(probe)])
        if p=='w4': run('w4-api-logs',['docker','logs','--tail','150','novabank-workshops-api-1'])
finally:
    subprocess.run(['docker','unpause','novabank-workshops-opa-1'],capture_output=True)
    run('restore-stop',['docker','compose','--profile','w4','stop','worker','temporal','api','adapter'])
    restorations=[]
    for service,dbfile in [('api','novabank.sqlite'),('temporal','temporal.sqlite')]:
        code='import pathlib, shutil, sqlite3, hashlib, json; dest=pathlib.Path("/restore/'+dbfile+'"); src=pathlib.Path("/backup/'+service+'.sqlite"); [pathlib.Path(str(dest)+s).unlink(missing_ok=True) for s in ("-wal","-shm")]; shutil.copyfile(src,dest); result={"service":"'+service+'","integrity":sqlite3.connect(dest).execute("pragma integrity_check").fetchone()[0],"hash_matches":hashlib.sha256(src.read_bytes()).hexdigest()==hashlib.sha256(dest.read_bytes()).hexdigest()}; print(json.dumps(result)); assert result["integrity"]=="ok" and result["hash_matches"]'
        res=capture(['docker','run','--rm','--network','none','--mount',f'type=volume,src=novabank-workshops_novabank_{service}_data,dst=/restore','--mount',f'type=bind,src={backup},dst=/backup,readonly','novabank/api:1.0.0','python','-c',code])
        restorations.append(json.loads(res))
    save('database-restoration.json',restorations)
    run('restore-w4',['./scripts/workshop','start','w4'])
    for w in range(1,5): shutil.copy2(backup/f'w{w}-evidence.json',root/f'workshops/w{w}/evidence/rehearsal-evidence.json')
    run('w4-final-verify',['./scripts/workshop','verify','w4'])
    stop.set(); t.join()
    save('protected-after.json',protected())
    print('AUDIT HARNESS COMPLETE',flush=True)
