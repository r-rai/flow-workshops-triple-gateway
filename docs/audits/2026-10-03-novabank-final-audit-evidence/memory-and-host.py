import pathlib,json,re,subprocess,datetime,urllib.request,urllib.error
out=pathlib.Path(__file__).parent
units={'B':1,'kB':1000,'KB':1000,'MB':1000**2,'GB':1000**3,'KiB':1024,'MiB':1024**2,'GiB':1024**3}
def size(s):
    m=re.fullmatch(r'\s*([\d.]+)\s*(\w+)\s*',s); return float(m[1])*units[m[2]]
def summary(paths):
    samples=[]
    for path in paths:
        for line in path.read_text().splitlines():
            r=json.loads(line)
            if not r.get('stats'):continue
            total=sum(size(s['MemUsage'].split('/')[0]) for s in r['stats'])
            host=r.get('host',''); avail=None
            for row in host.splitlines():
                if row.startswith('Mem:'):avail=int(row.split()[-1])
            samples.append({'time':r['time'],'containers':len(r['stats']),'bytes':round(total),'MB':round(total/1e6,2),'MiB':round(total/1024**2,2),'host_available_bytes':avail,'source':str(path),'stats':r['stats']})
    return {'samples':len(samples),'peak':max(samples,key=lambda s:s['bytes']),'minimum_host_available_bytes':min(s['host_available_bytes'] for s in samples if s['host_available_bytes']),'peak_nine_containers':max((s for s in samples if s['containers']==9),key=lambda s:s['bytes'])}
report={'fresh':summary([out/'memory-samples.jsonl',out/'confirmation-run/memory-samples.jsonl'])}
# Previous samples use the same schema but may name time differently.
old=out.parent/'2026-10-03-novabank-evidence/memory-samples.jsonl'
old_rows=[]
for line in old.read_text().splitlines():
    r=json.loads(line)
    stats=r.get('stats') or r.get('docker_stats')
    if r.get('containers'):
        total=sum(c['active_bytes'] for c in r['containers']); assert total==r['total_active_bytes']; old_rows.append(total)
    elif stats:
        total=sum(size(s['MemUsage'].split('/')[0]) for s in stats)
        old_rows.append(total)
report['historical_recomputed']={'samples':len(old_rows),'peak_bytes':round(max(old_rows)),'MB':round(max(old_rows)/1e6,2),'MiB':round(max(old_rows)/1024**2,2)} if old_rows else {'schema_unrecognized':True}
containers=json.loads(subprocess.check_output(['docker','inspect',*subprocess.check_output(['docker','compose','ps','-q'],text=True).split()],text=True))
report['runtime']=[{'name':c['Name'],'memory_limit_bytes':c['HostConfig']['Memory'],'running':c['State']['Running'],'oom_killed':c['State']['OOMKilled'],'ports':c['NetworkSettings']['Ports'],'networks':list(c['NetworkSettings']['Networks'])} for c in containers]
report['total_memory_limits_bytes']=sum(c['HostConfig']['Memory'] for c in containers)
report['protected_comparison']={}
before=json.loads((out/'protected-before.json').read_text()); after=json.loads((out/'confirmation-run/protected-after.json').read_text())
report['protected_comparison']={'identical':before==after,'before':before,'after':after}
protected=json.loads(subprocess.check_output(['docker','inspect','caddy','portainer','uptime-kuma','dozzle'],text=True)); checks=[]
for c in protected:
    name=c['Name'].lstrip('/'); ip=next(n['IPAddress'] for n in c['NetworkSettings']['Networks'].values() if n.get('IPAddress'))
    port,path={'caddy':(80,'/'),'portainer':(9000,'/api/status'),'uptime-kuma':(3001,'/'),'dozzle':(8080,'/')}[name]
    url=f'http://{ip}:{port}{path}'
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args): return None
    opener=urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(url,timeout=5) as res: status=res.status
    except urllib.error.HTTPError as e:status=e.code
    except Exception as e:status=type(e).__name__
    checks.append({'name':name,'url':url,'status':status})
report['protected_http']=checks
(out/'memory-and-host.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'fresh_peak':report['fresh']['peak'],'historical':report['historical_recomputed'],'protected_identical':before==after,'protected_http':checks,'memory_caps':report['total_memory_limits_bytes']},indent=2))
