#!/usr/bin/env python3
"""Prepared local identity exercise. Export metadata, never credentials."""
import argparse
import datetime
import json
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import httpx
from jose import jwt
from src.core.security import create_jwt_token

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('checkpoint',choices=['initial','completed'])
a=p.parse_args()
cfg=json.loads((Path(__file__).parent/'checkpoints'/a.checkpoint/'identity.json').read_text())
token=create_jwt_token(cfg['subject'],cfg['audience'],cfg['source_scopes'],cfg['role'],300)
r=httpx.post(os.getenv('W4_URL','http://127.0.0.1:9080')+'/oauth/token',data={'grant_type':'urn:ietf:params:oauth:grant-type:token-exchange','subject_token':token,'subject_token_type':'urn:ietf:params:oauth:token-type:access_token','audience':cfg['target_audience'],'scope':cfg['requested_scope']},timeout=15)
body=r.json()
metadata={k:v for k,v in body.items() if k!='access_token'}
if body.get('access_token'):
    claims=jwt.get_unverified_claims(body['access_token'])
    metadata['identity']={k:claims.get(k) for k in ('sub','aud','scope','role','delegated_by','act')}
result={'checkpoint':a.checkpoint,'config':cfg,'status_code':r.status_code,'response':metadata}
expected=200 if cfg['role']=='viewer' and cfg['requested_scope']=='api:accounts:read' else 403
assert r.status_code==expected,result
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')
path=Path(__file__).parent/'evidence'/f'identity-{a.checkpoint}-{stamp}.json'
path.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2));print('Evidence:',path)
