import asyncio,json,pathlib,types
from unittest.mock import patch
from src.worker import kafka_consumer as mod
out=pathlib.Path('/tmp/novabank-audit-20261003');real_event=asyncio.Event;event=real_event();records=[];started=[];committed=[]
class FakeConsumer:
 def __init__(self,*a,**kw):self.messages=[types.SimpleNamespace(offset=10,value={'case_id':'first-fails'}),types.SimpleNamespace(offset=11,value={'case_id':'second-succeeds'})];self.position=10
 async def start(self):pass
 async def stop(self):pass
 async def getone(self):
  m=self.messages.pop(0);self.position=m.offset+1;records.append(m.offset);return m
 async def commit(self):committed.append(self.position);event.set()
class FakeTemporal:
 async def start_workflow(self,*args,**kwargs):
  if kwargs['id']=='dispute-case-first-fails':raise RuntimeError('Injected transient Temporal failure')
  started.append(kwargs['id']);return types.SimpleNamespace(run_id='audit-run')
async def connect(*a,**kw):return FakeTemporal()
async def main():
 with patch.object(mod,'AIOKafkaConsumer',FakeConsumer),patch.object(mod.Client,'connect',connect),patch.object(mod.asyncio,'Event',return_value=event):
  await mod.run_consumer()
 result={'read_offsets':records,'started_workflows':started,'committed_next_offsets':committed,'failed_offset_10_skipped_by_commit_12':committed==[12] and started==['dispute-case-second-succeeds']}
 (out/'kafka-offset-probe.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
asyncio.run(main())
