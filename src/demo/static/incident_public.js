'use strict';

const $ = id => document.getElementById(id);
const API = '/demo-api/workshop-4';

const chapters = [
  [0, 8, 'The bank has already paid', 'What did we authorize?', 'Vote: identity, model, tool policy or approval.'],
  [8, 20, 'Follow the money', 'Where did untrusted data become authority?', 'Inspect the ticket and handoff. Review the isolated recorded ₹90 lakh replay.'],
  [20, 33, 'Contain the reasoning loop', 'Does inference denial block a direct tool request?', 'Inspect Gate 1 budget denial and inference headroom limits.'],
  [33, 53, 'Control the capability', 'Which actual arguments should the policy permit?', 'Compare prohibited beneficiary, excessive amount, and permitted payment.'],
  [53, 60, 'The attacker changes routes', 'What stops a direct API bypass?', 'Inspect caller audience and scopes. Review wrong audience and insufficient scope.'],
  [60, 67, 'Break & recovery', 'Can the payment agent approve itself?', 'Notice self-approval rejection and independent authorization enforcement.'],
  [67, 85, 'Restrict the identity', 'Which scopes may cross the boundary?', 'Compare permitted token exchange against unauthorized scope escalation.'],
  [85, 103, 'Approval attaches to a transaction', 'Who independently approves these exact arguments?', 'Examine independent review, rejected tampering, and idempotent retry.'],
  [103, 119, 'A second trust boundary', 'Who may read, execute, approve and complete?', 'Review legitimate A2A delegation, task binding, and settlement.'],
  [119, 130, 'Prove the repair', 'Can you reconstruct both denial and settlement?', 'Review assembled request, identity, response, task, payment, and trace evidence.'],
  [130, 135, 'Incident review', 'Which control owner owns the repair?', 'Complete the control-owner analysis and participant worksheet questions.'],
];

let currentRun = null;
let allRuns = [];
let chapter = Number(localStorage.getItem('w4-public-chapter') || 0);

const fmt = v => JSON.stringify(v, null, 2);

function error(e) {
  const errEl = $('error');
  if (!errEl) return;
  errEl.hidden = !e;
  errEl.textContent = e?.message || '';
}

async function api(path, body, method) {
  const r = await fetch(path, {
    method: method || (body ? 'POST' : 'GET'),
    credentials: 'same-origin',
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    throw new Error(typeof data.detail === 'string' ? data.detail : `Service returned HTTP ${r.status}`);
  }
  return data;
}

function setChapter(val) {
  chapter = Math.max(0, Math.min(chapters.length - 1, val));
  localStorage.setItem('w4-public-chapter', chapter);
  const [start, end, title, question, cue] = chapters[chapter];
  $('chapter-question').textContent = question;
  $('chapter-context').textContent = `${start}–${end}m · ${cue}`;
  $('cue').textContent = `${title}: ${cue}`;

  const nav = $('chapters');
  if (nav) {
    [...nav.children].forEach((el, idx) => el.classList.toggle('active', idx === chapter));
  }
  $('ticket-panel').hidden = false;
}

function initChaptersNav() {
  const nav = $('chapters');
  if (!nav) return;
  nav.replaceChildren();
  chapters.forEach(([start, end, title], idx) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = `${idx + 1}. ${title}`;
    btn.onclick = () => setChapter(idx);
    nav.append(btn);
  });
}

function render(run) {
  if (!run) return;
  currentRun = run;
  localStorage.setItem('w4-public-run', run.run_id);

  $('state').textContent = (run.state || 'unknown').replaceAll('_', ' ');
  $('mode').textContent = `${run.inference_mode || 'recorded'} · ${run.run_id}`;
  $('reason').textContent = run.reason || (run.state === 'awaiting_review' ? 'No debit yet. Independent review is required.' : 'Inspect the service responses and measured ledger observations.');

  const delta = run.effects?.balance_delta;
  if (delta == null) {
    $('delta').textContent = '—';
  } else {
    $('delta').textContent = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(delta / 100);
  }

  $('count').textContent = run.effects?.payment_count_delta ?? '—';
  $('sandbox-effect').textContent = run.sandbox?.effects
    ? `Isolated vulnerable ledger: ₹90 lakh loss, ${run.sandbox.effects.payment_count_delta} payment. Protected ledger observations shown above.`
    : '';

  $('identities').textContent = fmt(run.identities || []);
  $('evidence').textContent = fmt({
    run_id: run.run_id,
    scenario: run.scenario,
    state: run.state,
    arguments: run.arguments,
    events: run.events,
    effects: run.effects,
    sandbox: run.sandbox,
    task: run.task,
    payment: run.payment,
  });

  $('proposal').textContent = run.proposal
    ? fmt({
        proposal: run.proposal,
        decision: run.approval,
        payment: run.payment,
        task_id: run.task?.task_id,
      })
    : 'No proposal in this scenario.';

  $('ticket').textContent = fmt(run.ticket || {});

  // Timeline
  const timeline = $('timeline');
  timeline.replaceChildren();
  const entries = [
    'Incident: ₹90 lakh · 900,000,000 paise',
    'Ticket: untrusted settlement instructions',
    'Recorded handoff: NegotiatorBot → PaymentsAgent',
    ...(run.events || [])
      .filter(e => e.boundary !== 'Evidence')
      .map(e => `${e.label} · ${e.status_code ?? 'denied'} · ${e.outcome}`),
  ];
  for (const text of entries) {
    const li = document.createElement('li');
    li.textContent = text;
    timeline.append(li);
  }

  // Boundaries
  const boundaries = $('boundaries');
  boundaries.replaceChildren();
  for (const boundary of ['Gate 1', 'Gate 2', 'Gate 3', 'Approval', 'A2A', 'Settlement', 'Isolated sandbox']) {
    const events = (run.events || []).filter(e => e.boundary === boundary);
    if (!events.length) continue;
    for (const event of events) {
      const el = document.createElement('article');
      el.className = event.outcome || 'allowed';
      const label = document.createElement('strong');
      label.textContent = `${boundary} · ${event.label}`;
      const state = document.createElement('span');
      state.textContent = `${event.status_code ?? '?'} ${event.outcome}`;
      el.append(label, state);
      boundaries.append(el);
    }
  }

  // Traces
  $('trace-id').textContent = run.trace_id || 'n/a';
  $('trace-status').textContent = `Trace collection: ${run.trace_status || 'observed'} (${(run.trace_services || []).join(', ')})`;

  // Enable download
  $('download').disabled = false;
  $('download').onclick = () => {
    const blob = new Blob([fmt(run)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `evidence-${run.scenario}-${run.run_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };
}

async function loadRuns() {
  allRuns = await api(API + '/runs');
  const sel = $('runs');
  sel.replaceChildren();

  for (const r of allRuns) {
    const opt = document.createElement('option');
    opt.value = r.run_id;
    opt.textContent = `${r.scenario} · ${r.state.toUpperCase()}`;
    sel.append(opt);
  }

  const savedId = currentRun?.run_id || localStorage.getItem('w4-public-run');
  const selected = allRuns.find(r => r.run_id === savedId) || allRuns[0];
  if (selected) {
    sel.value = selected.run_id;
    render(selected);
  }
}

async function enterWorkspace() {
  const readiness = await api(API + '/readiness');
  $('readiness').textContent = `Recording available (${readiness.recording?.run_count || 11} runs) · Verified: ${readiness.recording?.capture_timestamp || ''}`;

  initChaptersNav();
  setChapter(chapter);

  await loadRuns();

  const predKey = 'w4-public-predict-' + (currentRun?.scenario || 'default');
  $('prediction').value = localStorage.getItem(predKey) || '';

  $('signin').hidden = true;
  $('workspace').hidden = false;
}

// Event Listeners
$('signin-form').onsubmit = async e => {
  e.preventDefault();
  error(null);
  const code = $('access-code').value.trim();
  try {
    await api('/demo-api/login', { access_code: code });
    await enterWorkspace();
  } catch (err) {
    error(err);
  }
};

$('runs').onchange = () => {
  const selected = allRuns.find(r => r.run_id === $('runs').value);
  if (selected) {
    render(selected);
    const predKey = 'w4-public-predict-' + selected.scenario;
    $('prediction').value = localStorage.getItem(predKey) || '';
  }
};

$('prediction').oninput = () => {
  if (currentRun) {
    const predKey = 'w4-public-predict-' + currentRun.scenario;
    localStorage.setItem(predKey, $('prediction').value);
  }
};

$('refresh').onclick = async () => {
  try {
    error(null);
    await loadRuns();
  } catch (err) {
    error(err);
  }
};

$('signout').onclick = async () => {
  try {
    await api('/demo-api/logout', {});
  } catch (_) {}
  location.reload();
};

// Auto-check on page load if existing session cookie is still valid
window.addEventListener('DOMContentLoaded', async () => {
  try {
    await enterWorkspace();
  } catch (_) {
    // Needs login
    $('signin').hidden = false;
    $('workspace').hidden = true;
  }
});
