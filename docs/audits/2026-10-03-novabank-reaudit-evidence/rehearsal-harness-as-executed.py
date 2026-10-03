import subprocess, json, pathlib, threading, time, shutil, datetime, sqlite3
root=pathlib.Path.cwd(); out=root/'docs/audits/2026-10-03-novabank-reaudit-evidence'; backup=pathlib.Path('/tmp/novabank-reaudit-backup')
def protected():
    data=json.loads(subprocess.check_output(['docker','inspect','caddy','portainer','uptime-kuma','dozzle']))
    return [{'name':c['Name'],'id':c['Id'],'started':c['State']['StartedAt'],'running':c['State']['Running'],'restarts':c['RestartCount'],'health':c['State'].get('Health',{}).get('Status')} for c in data]
(out/'protected-before.json').write_text(json.dumps(protected(),indent=2))
for w in range(1,5): shutil.copy2(root/f'workshops/w{w}/evidence/rehearsal-evidence.json',backup/f'w{w}-evidence.json')
stop=threading.Event()
def sample():
    with (out/'memory-samples.jsonl').open('w') as f:
        while not stop.is_set():
            try:
                ids=subprocess.check_output(['docker','compose','ps','-q'],text=True).split()
                if ids:
                    r=subprocess.run(['docker','stats','--no-stream','--format','{{json .}}',*ids],capture_output=True,text=True,timeout=10)
                    f.write(json.dumps({'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stats':[json.loads(l) for l in r.stdout.splitlines() if l],'host':subprocess.check_output(['free','-b'],text=True)})+'\n'); f.flush()
            except Exception as e: f.write(json.dumps({'error':str(e)})+'\n')
            stop.wait(2)
t=threading.Thread(target=sample); t.start(); results=[]
def run(name,cmd,timeout=180):
    begin=time.time()
    with (out/f'{name}.log').open('w') as f:
        try: code=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=timeout).returncode
        except subprocess.TimeoutExpired: code=124
    item={'name':name,'command':cmd,'exit_code':code,'seconds':round(time.time()-begin,2)}; results.append(item)
    (out/'results.json').write_text(json.dumps(results,indent=2)); print(json.dumps(item),flush=True)
    return code
try:
    run('preflight',['./scripts/workshop','preflight'])
    for w in range(1,5):
        p=f'w{w}'
        if run(f'{p}-switch',['./scripts/workshop','switch',p]): continue
        run(f'{p}-reset',['./scripts/workshop','reset',p,'--yes'])
        run(f'{p}-verify',['./scripts/workshop','verify',p])
        run(f'{p}-rehearsal',['.venv/bin/python',f'workshops/{p}/rehearsal_{p}.py'],300)
        e=root/f'workshops/{p}/evidence/rehearsal-evidence.json'; shutil.copy2(e,out/f'{p}-rehearsal-evidence.json')
    # Preserve post-rehearsal database evidence before restoring the original state.
    subprocess.run(['docker','exec','novabank-workshops-api-1','python','-c','import sqlite3; s=sqlite3.connect("/app/data/novabank.sqlite"); d=sqlite3.connect("/tmp/reaudit-result.sqlite"); s.backup(d); d.close(); s.close()'],check=True)
    subprocess.run(['docker','cp','novabank-workshops-api-1:/tmp/reaudit-result.sqlite',str(backup/'post-rehearsals.sqlite')],check=True)
finally:
    # Restore the two backed-up SQLite databases with all writer services stopped.
    run('restore-stop',['docker','compose','--profile','w4','stop','worker','temporal','api','adapter'])
    for service,dbfile,backupfile in [('api','novabank.sqlite','api.sqlite'),('temporal','temporal.sqlite','temporal.sqlite')]:
        volume=json.loads(subprocess.check_output(['docker','volume','inspect',f'novabank-workshops_novabank_{service}_data']))[0]
        dest=pathlib.Path(volume['Mountpoint'])/dbfile
        for suffix in ('-wal','-shm'):
            pathlib.Path(str(dest)+suffix).unlink(missing_ok=True)
        shutil.copyfile(backup/backupfile,dest)
        assert sqlite3.connect(dest).execute('pragma integrity_check').fetchone()[0]=='ok'
    run('restore-start',['docker','compose','--profile','w4','start','api','temporal','adapter','worker'])
    stop.set(); t.join()
    (out/'protected-after-rehearsals.json').write_text(json.dumps(protected(),indent=2))
    for w in range(1,5): shutil.copy2(backup/f'w{w}-evidence.json',root/f'workshops/w{w}/evidence/rehearsal-evidence.json')
