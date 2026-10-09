'use strict';
const $ = id => document.getElementById(id);
const API = '/demo-api/workshop-4';
const chapters = [
  [0,8,'The bank has already paid','What did we authorize?','Vote: identity, model, tool policy or approval. Withhold the ticket.'],
  [8,20,'Follow the money','Where did untrusted data become authority?','Reveal the ticket and handoff. Execute the isolated recorded replay; inspect both ledgers.'],
  [20,33,'Contain the reasoning loop','Does inference denial block a direct tool request?','Predict → budget denial → inspect → test the tool boundary. Optional live comparison has no payment capability.'],
  [33,53,'Control the capability','Which actual arguments should the policy permit?','Pairs change the prepared local policy; test beneficiary and amount separately, then a permitted payment.'],
  [53,60,'The attacker changes routes','What stops a direct API bypass?','Inspect the caller audience and scopes. Run wrong audience and insufficient scope.'],
  [60,67,'Break & recovery','Can the payment agent approve itself?','Rest for seven minutes. Restore stalled local labs from the completed checkpoint.'],
  [67,85,'Restrict the identity','Which scopes may cross the boundary?','Compare valid exchange and scope escalation. Change the prepared identity checkpoint.'],
  [85,103,'Approval attaches to a transaction','Who independently approves these exact arguments?','Create proposals immediately before review. Reject self approval and changed arguments; inspect one-effect retries.'],
  [103,119,'A second trust boundary','Who may read, execute, approve and complete?','Run legitimate delegation. Inspect foreign access, unauthorized completion and mismatched binding denials.'],
  [119,130,'Prove the repair','Can you reconstruct both denial and settlement?','Run the attack suite and business path; assemble request, identity, response, task, payment and trace evidence.'],
  [130,135,'Incident review','Which control owner owns the repair?','Revisit the opening vote. Complete the control-owner and production-readiness worksheet.'],
];
let current = null, busy = false, reviewer = false, chapter = Number(localStorage.getItem('w4-chapter') || 0);
let clickKey = null, observation = false;
const fmt = v => JSON.stringify(v, null, 2);
function error(e) { $('error').hidden = !e; $('error').textContent = e?.message || ''; }
async function api(path, body, method) {
  const r = await fetch(path, {method:method || (body ? 'POST':'GET'), credentials:'same-origin', headers:body?{'Content-Type':'application/json'}:{}, body:body?JSON.stringify(body):undefined});
  const data = await r.json();
  if (!r.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `Service returned HTTP ${r.status}`);
  return data;
}
function setBusy(value) {
  busy=value; $('run').disabled=value || observation; $('running').hidden=!value;
  $('approve').disabled=value || observation || !reviewer || current?.state!=='awaiting_review';
  $('reject').disabled=$('approve').disabled;
  $('reconcile').disabled=value || observation || !current || !['running','unresolved','approved'].includes(current.state);
}
function setChapter(value, record=true) {
  chapter=Math.max(0,Math.min(chapters.length-1,value)); localStorage.setItem('w4-chapter',chapter);
  const [start,end,title,question,cue]=chapters[chapter];
  $('chapter-question').textContent=question; $('chapter-context').textContent=cue; $('cue').textContent=`${start}–${end} minutes · ${title}. ${cue}`;
  [...$('chapters').children].forEach((el,i)=>el.classList.toggle('active',i===chapter));
  $('ticket-panel').hidden=chapter<1;
  if (current) render(current);
  if(record && localStorage.getItem('w4-clock')) {
    const observed=JSON.parse(localStorage.getItem('w4-delivery') || '[]');
    observed.push({chapter:title,observed_at:new Date().toISOString(),elapsed_seconds:Math.round((Date.now()-Number(localStorage.getItem('w4-clock')))/1000)});
    localStorage.setItem('w4-delivery',fmt(observed));
  }
}
function setView() {
  const view=['participant','presenter','reviewer'].includes($('view').value)?$('view').value:'participant';
  $('view').value=view; localStorage.setItem('w4-view',view);
  $('presenter').hidden=view!=='presenter'; $('reviewer-form').hidden=view!=='reviewer';
  document.body.classList.toggle('presenter',view==='presenter');
  const url=new URL(location.href); url.searchParams.set('view',view);
  history.replaceState(null,'',url);
}
function render(run) {
  current=run; localStorage.setItem('w4-run',run.run_id);
  $('state').textContent=run.state.replaceAll('_',' ');
  $('mode').textContent=`${run.inference_mode} · ${run.run_id}`;
  $('reason').textContent=run.reason || (run.state==='awaiting_review'?'No debit yet. Independent review is required.':'Inspect the service responses and measured ledger observations.');
  $('delta').textContent=run.effects.balance_delta==null?'Unresolved':new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR'}).format(run.effects.balance_delta/100);
  $('count').textContent=run.effects.payment_count_delta ?? 'Unresolved';
  $('sandbox-effect').textContent=run.sandbox?.effects ? `Isolated vulnerable ledger: ₹90 lakh loss, ${run.sandbox.effects.payment_count_delta} payment. Protected ledger observations shown above.`:'';
  $('identities').textContent=fmt(run.identities);
  $('evidence').textContent=fmt({run_id:run.run_id,scenario:run.scenario,arguments:run.arguments,events:run.events,effects:run.effects,sandbox:run.sandbox,task:run.task,payment:run.payment});
  $('proposal').textContent=run.proposal?fmt({proposal:run.proposal,decision:run.approval,payment:run.payment,task_id:run.task?.task_id}):'No pending proposal.';
  $('ticket').textContent=fmt(run.ticket);
  $('timeline').replaceChildren();
  const entries=['Incident: ₹90 lakh · 900,000,000 paise',...(chapter>=1?['Ticket: untrusted settlement instructions','Recorded handoff: NegotiatorBot → PaymentsAgent']:[]),...run.events.filter(e=>e.boundary!=='Evidence').map(e=>`${e.label} · ${e.status_code ?? 'no response'} · ${e.outcome}`)];
  for(const text of entries) {const li=document.createElement('li');li.textContent=text;$('timeline').append(li);}
  $('boundaries').replaceChildren();
  for(const boundary of ['Gate 1','Gate 2','Gate 3','Approval','A2A','Settlement','Isolated sandbox']) {
    const events=run.events.filter(e=>e.boundary===boundary); if(!events.length)continue;
    for(const event of events){const el=document.createElement('article');el.className=event.outcome;const label=document.createElement('strong');label.textContent=`${boundary} · ${event.label}`;const state=document.createElement('span');state.textContent=`${event.status_code ?? '?'} ${event.outcome}`;el.append(label,state);$('boundaries').append(el);}
  }
  $('trace-id').textContent=run.trace_id; $('trace-status').textContent=`Trace collection: ${run.trace_status}`;
  $('trace-link').href=`${location.protocol}//${location.hostname}:16686/trace/${encodeURIComponent(run.trace_id)}`;
  $('download').disabled=false; setBusy(busy);
}
async function reloadRuns() {
  const runs=await api(API+'/runs'); $('runs').replaceChildren();
  for(const run of runs){const opt=document.createElement('option');opt.value=run.run_id;opt.textContent=`${run.scenario} · ${run.state} · ${run.run_id}`;$('runs').append(opt);}
  const id=current?.run_id || localStorage.getItem('w4-run');
  const selected=runs.find(r=>r.run_id===id) || runs[0];
  if(selected){$('runs').value=selected.run_id;render(selected);}
}
async function enter() {
  const config=await api(API+'/readiness'); reviewer=config.reviewer_authenticated===true; observation=config.observation_only===true;
  $('readiness').textContent=Object.entries(config.checks).map(([k,v])=>`${k}: ${v.reachable?'reachable':'unavailable'}`).join(' · ');
  $('scenario').replaceChildren(); for(const scenario of config.scenarios){const opt=document.createElement('option');opt.value=scenario.id;opt.textContent=scenario.title;$('scenario').append(opt);}
  await reloadRuns();
  $('prediction').value=localStorage.getItem('w4-predict-'+$('scenario').value)||'';
  $('signin').hidden=true; $('workspace').hidden=false; setBusy(false);
  if(observation) $('readiness').textContent+=' · Observation only';
}
$('signin-form').onsubmit=async e=>{e.preventDefault();error(null);try{await api('/demo-api/login',{email:$('email').value,password:$('password').value});await enter();}catch(e){error(e);}};
$('run').onclick=async()=>{if(busy)return;error(null);setBusy(true);clickKey ||= crypto.randomUUID();try{const run=await api(API+'/runs',{scenario:$('scenario').value,request_id:clickKey});render(run);clickKey=null;await reloadRuns();}catch(e){error(e);}finally{setBusy(false);}};
$('scenario').onchange=()=>{clickKey=null;$('prediction').value=localStorage.getItem('w4-predict-'+$('scenario').value)||'';};
$('prediction').oninput=()=>localStorage.setItem('w4-predict-'+$('scenario').value,$('prediction').value);
$('runs').onchange=async()=>{try{render(await api(API+'/runs/'+$('runs').value));}catch(e){error(e);}};
$('check-traces').onclick=async()=>{if(!current)return;try{render(await api(API+'/runs/'+current.run_id+'/traces',{}));}catch(e){error(e);}};
$('refresh').onclick=async()=>{try{error(null);await reloadRuns();}catch(e){error(e);}};
$('reviewer-form').onsubmit=async e=>{e.preventDefault();try{await api(API+'/reviewer-session',{password:$('reviewer-password').value});$('reviewer-password').value='';reviewer=true;$('reviewer-status').textContent='Independent reviewer session opened. Requester sessions still cannot approve.';await reloadRuns();}catch(e){error(e);}};
for(const decision of ['approve','reject']) $(''+decision).onclick=async()=>{if(!current||busy)return;setBusy(true);try{render(await api(API+'/runs/'+current.run_id+'/decision',{decision}));await reloadRuns();}catch(e){error(e);}finally{setBusy(false);}};
$('reconcile').onclick=async()=>{if(!current||busy)return;setBusy(true);try{render(await api(API+'/runs/'+current.run_id+'/reconcile',{}));}catch(e){error(e);}finally{setBusy(false);}};
function download(data,name){const url=URL.createObjectURL(new Blob([fmt(data)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=name;a.click();URL.revokeObjectURL(url);}
$('download').onclick=async()=>{try{download(await api(API+'/runs/'+current.run_id+'/evidence'),current.run_id+'.json');}catch(e){error(e);}};
$('start-clock').onclick=()=>{localStorage.setItem('w4-clock',Date.now());localStorage.setItem('w4-delivery','[]');setChapter(0);};
$('delivery-export').onclick=()=>download({kind:'observed_delivery_timing',started_at:Number(localStorage.getItem('w4-clock'))||null,exported_at:new Date().toISOString(),elapsed_seconds:localStorage.getItem('w4-clock')?Math.round((Date.now()-Number(localStorage.getItem('w4-clock')))/1000):null,chapters:JSON.parse(localStorage.getItem('w4-delivery')||'[]'),human_acceptance:'Facilitator must record break, exercise recovery and projected readability; this export alone does not certify delivery.'},'w4-delivery-timing.json');
$('signout').onclick=async()=>{await api('/demo-api/logout',{});location.reload();};
$('view').onchange=setView;
chapters.forEach(([start,end,title],i)=>{const b=document.createElement('button');b.textContent=`${start}–${end} ${title}`;b.onclick=()=>setChapter(i);$('chapters').append(b);});
$('view').value=new URLSearchParams(location.search).get('view')||localStorage.getItem('w4-view')||'participant';setView();setChapter(chapter,false);
setInterval(()=>{const start=Number(localStorage.getItem('w4-clock'));if(start)$('clock').textContent=`${Math.floor((Date.now()-start)/60000)} / 135 min elapsed`;},1000);
enter().catch(e=>{if(!e.message.includes('session'))error(e);});
