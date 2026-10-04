import json,pathlib,subprocess,hashlib,re,urllib.parse
root=pathlib.Path.cwd(); out=pathlib.Path(__file__).parent
def cap(*args):return subprocess.check_output(args,text=True)
commits=cap('git','rev-list','--reverse','2bcc587..HEAD').split(); history=[]; scanned=0; matches=[]
patterns={'github':r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})','openai':r'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{35,}','aws':r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b','private_key':r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----','slack':r'\bxox[baprs]-[A-Za-z0-9-]{20,}'}
for commit in commits:
    fields=cap('git','show','-s','--format=%H%n%s%n%aI%n%P',commit).splitlines()
    files=cap('git','diff-tree','--no-commit-id','--name-only','-r',commit).splitlines()
    history.append({'hash':fields[0],'subject':fields[1],'authored':fields[2],'parents':fields[3].split(),'files':files})
    for path in files:
        res=subprocess.run(['git','show',commit+':'+path],capture_output=True)
        if res.returncode:continue
        try: content=res.stdout.decode()
        except UnicodeError:continue
        scanned+=1
        for label,pat in patterns.items():
            if re.search(pat,content):matches.append({'commit':commit,'path':path,'type':label})
remote=cap('git','config','--get','remote.origin.url').strip(); parsed=urllib.parse.urlparse(remote)
data={'head':cap('git','rev-parse','HEAD').strip(),'local_origin':cap('git','rev-parse','origin/feat/implement-novabank-platform').strip(),'main':cap('git','rev-parse','main').strip(),'commits':history,'scanned_file_versions':scanned,'credential_pattern_hits':matches,'remote_embedded_credentials':bool(parsed.password or parsed.username if parsed.scheme in ['http','https'] else False),'live_remote_fetched':False}
(out/'history-audit.json').write_text(json.dumps(data,indent=2))
manifest=json.loads((root/'config/manifest.json').read_text()); compose=json.loads(cap('docker','compose','--profile','w4','config','--format','json'))
images=[]
for service,details in manifest['pinned_images'].items():
    image=json.loads(cap('docker','image','inspect',details['image']))[0]
    deployed=compose['services'][service]['image']
    images.append({'service':service,'manifest_digest':details['digest'],'installed_repository_digests':image.get('RepoDigests'),'compose_reference':deployed,'digest_matches':any(s.endswith('@'+details['digest']) for s in image.get('RepoDigests',[])),'deployment_pinned':deployed.endswith('@'+details['digest'])})
source=[]
for service,paths in {'api':['src/api/routes/oauth.py','src/api/routes/a2a.py','src/core/security.py','src/services/banking.py','src/services/approvals.py','src/api/main.py'],'adapter':['src/adapter/server.py'],'worker':['src/worker/activities.py','src/worker/workflow.py','src/worker/kafka_consumer.py'],'temporal':['src/worker/temporal_server.py']}.items():
    for path in paths:
        container_path='/app/temporal_server.py' if service=='temporal' else '/app/'+path
        code='import hashlib,pathlib; print(hashlib.sha256(pathlib.Path('+repr(container_path)+').read_bytes()).hexdigest())'
        actual=cap('docker','run','--rm','--network','none','--read-only','--entrypoint','python',manifest['built_images'][service]['tag'],'-c',code).strip()
        expected=hashlib.sha256((root/path).read_bytes()).hexdigest()
        source.append({'service':service,'path':path,'image_sha256':actual,'checkout_sha256':expected,'matches':expected==actual})
(out/'images-and-sources.json').write_text(json.dumps({'third_party':images,'built_image_sources':source,'built_images':manifest['built_images']},indent=2))
print(json.dumps({'commits':len(commits),'scanned_file_versions':scanned,'credential_pattern_hits':matches,'third_party':images,'source_matches':all(p['matches'] for p in source)},indent=2))
