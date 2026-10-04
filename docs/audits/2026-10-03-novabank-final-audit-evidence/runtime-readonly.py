import subprocess,json,pathlib
out=pathlib.Path(__file__).parent
ids=subprocess.check_output(['docker','compose','ps','-q'],text=True).split()
cs=json.loads(subprocess.check_output(['docker','inspect',*ids],text=True)); results=[]
for c in cs:
    img=json.loads(subprocess.check_output(['docker','image','inspect',c['Config']['Image']],text=True))[0]
    results.append({'name':c['Name'],'configured_image':c['Config']['Image'],'running_image_id':c['Image'],'reference_image_id':img['Id'],'matches':img['Id']==c['Image']})
probe='''import socket,json,urllib.request,os
r={}
try:
    socket.create_connection(("api",8000),timeout=2).close(); r["direct_api_access"]="connected"
except Exception as e:r["direct_api_access"]=type(e).__name__
try:
    req=urllib.request.Request("http://apisix:9080/api/v1/accounts/acc-101",headers={"X-API-Key":os.getenv("GATE3_API_KEY","gate3-secret-token")})
    with urllib.request.urlopen(req,timeout=5) as response:r["gate3_status"]=response.status
except Exception as e:r["gate3_error"]=type(e).__name__
print(json.dumps(r))'''
network=[]
for name in ['adapter','worker']:
    r=subprocess.run(['docker','exec',f'novabank-workshops-{name}-1','python','-c',probe],capture_output=True,text=True)
    network.append({'service':name,'exit_code':r.returncode,'result':json.loads(r.stdout) if r.returncode==0 else {'error':r.stderr}})
api=json.loads(subprocess.check_output(['docker','inspect','novabank-workshops-api-1'],text=True))[0]
telemetry={s.split('=',1)[0]:s.split('=',1)[1] for s in api['Config']['Env'] if s.startswith(('ENABLE_TELEMETRY=','OTEL_EXPORTER_OTLP_ENDPOINT='))}
data={'runtime_images':results,'network_probes':network,'api_telemetry_configuration':telemetry}
(out/'runtime-readonly.json').write_text(json.dumps(data,indent=2)); print(json.dumps(data,indent=2))
