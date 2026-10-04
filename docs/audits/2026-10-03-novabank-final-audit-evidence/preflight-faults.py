import tempfile,pathlib,subprocess,json,os,shutil
root=pathlib.Path.cwd(); out=pathlib.Path(__file__).parent
with tempfile.TemporaryDirectory(prefix='novabank-preflight-audit-') as td:
    tmp=pathlib.Path(td); (tmp/'scripts').mkdir(); (tmp/'config').mkdir(); (tmp/'bin').mkdir()
    shutil.copy2(root/'scripts/workshop',tmp/'scripts/workshop')
    shutil.copy2(root/'config/manifest.json',tmp/'config/manifest.json')
    (tmp/'.active_profile').write_text('w4')
    real=shutil.which('docker')
    fake=tmp/'bin/docker'
    fake.write_text('#!/bin/bash\nif [[ "$1" == "image" && "$2" == "inspect" ]]; then exit 1; fi\nexec '+real+' "$@"\n'); fake.chmod(0o755)
    env={**os.environ,'PATH':str(tmp/'bin')+':'+os.environ['PATH']}
    results=[]
    for mode in ['missing_image_inspection','malformed_manifest']:
        if mode=='malformed_manifest': (tmp/'config/manifest.json').write_text('{not valid json')
        r=subprocess.run([str(tmp/'scripts/workshop'),'preflight'],env=env,text=True,capture_output=True)
        results.append({'mode':mode,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
(out/'preflight-faults.json').write_text(json.dumps(results,indent=2)); print(json.dumps(results,indent=2))
