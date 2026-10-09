'use strict';

const $ = id => document.getElementById(id);
const API = '/demo-api/workshop-4';

// Nonfatal browser storage helper
const storage = {
  get: (k, def = null) => {
    try {
      return localStorage.getItem(k) ?? def;
    } catch (_) {
      return def;
    }
  },
  set: (k, v) => {
    try {
      localStorage.setItem(k, v);
    } catch (_) {}
  },
  remove: k => {
    try {
      localStorage.removeItem(k);
    } catch (_) {}
  },
  clearNotes: () => {
    try {
      const toRemove = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && (key.startsWith('w4-public-predict-') || key.startsWith('w4-predict-'))) {
          toRemove.push(key);
        }
      }
      toRemove.forEach(k => localStorage.removeItem(k));
    } catch (_) {}
  },
};

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
let chapter = Number(storage.get('w4-public-chapter', 0));

const fmt = v => JSON.stringify(v, null, 2);

function formatPaise(paise) {
  if (typeof paise !== 'number') return String(paise ?? '—');
  const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(paise / 100);
  return `${paise.toLocaleString('en-IN')} paise (${inr})`;
}

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
  storage.set('w4-public-chapter', chapter);
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

function renderScenarioExplanation(run) {
  const title = $('scenario-explainer-title');
  const body = $('scenario-explainer-body');
  if (!title || !body) return;

  const sc = run.scenario;
  if (sc === 'legitimate_delegation') {
    title.textContent = 'A2A Delegation & Independent ₹1,500 Settlement Flow';
    body.innerHTML = `
      <p><strong>1. Task Delegation:</strong> <code>negotiator-bot-agent</code> creates A2A task <code>${run.task?.task_id || 'task-...'}</code> with ₹1,500 amount bound to <code>case-501</code>.</p>
      <p><strong>2. Foreign Access & Completion Blocked:</strong> Foreign agents and unauthorized completions are rejected (HTTP 403).</p>
      <p><strong>3. Self-Approval Rejected:</strong> <code>payments-agent-executor</code> attempts to self-approve proposal <code>${run.proposal?.proposal_id || 'prop-...'}</code>; server strictly rejects self-approval with HTTP 403.</p>
      <p><strong>4. Independent Authorization:</strong> Human reviewer (<code>w4-independent-reviewer</code>) authorizes the exact proposal record (HTTP 200).</p>
      <p><strong>5. Tampering Rejected:</strong> An altered proposal (+1 paisa) is rejected by settlement engine (HTTP 400).</p>
      <p><strong>6. Exact Settlement & Idempotent Retry:</strong> Payment <code>${run.payment?.payment_id || 'pay-...'}</code> is settled; a repeat retry produces exactly 0 new debits.</p>
      <p><strong>7. Task-Payment Binding:</strong> Payment ID is cryptographically bound to task <code>${run.task?.task_id || 'task-...'}</code>, completing the lifecycle with verified ledger change of -₹1,500.00.</p>
    `;
  } else if (sc === 'vulnerable_replay') {
    title.textContent = 'Recorded Incident: Isolated ₹90 Lakh Replay';
    body.innerHTML = `
      <p><strong>Exploit Trajectory:</strong> Untrusted customer ticket instructions were forwarded directly into execution without boundary validation.</p>
      <p><strong>Observed Impact:</strong> The isolated sandbox ledger incurred a -900,000,000 paise (-₹90 lakh) loss.</p>
      <p><strong>Protected Ledger Status:</strong> The real bank ledger remained completely untouched (₹0 change, 0 payments), proving the sandbox boundary was isolated.</p>
    `;
  } else if (sc === 'budget_denial') {
    title.textContent = 'Gate 1: Inference Headroom Denial';
    body.innerHTML = `
      <p><strong>Execution Stopping Point:</strong> Halted at Gate 1 (Inference Gateway).</p>
      <p><strong>Reason:</strong> Accumulated tokens (35) plus requested prompt exceeded available headroom (99,965 tokens). Returned HTTP 429 Rate Limit Exceeded.</p>
      <p><strong>Safety Outcome:</strong> No tool calls or payments were dispatched. Ledger balance delta: 0 paise.</p>
    `;
  } else if (sc === 'prohibited_beneficiary') {
    title.textContent = 'Gate 2: OPA Policy Beneficiary Denial';
    body.innerHTML = `
      <p><strong>Execution Stopping Point:</strong> Halted at Gate 2 (Tool Call Policy via OPA).</p>
      <p><strong>Reason:</strong> Beneficiary <code>fraud-account-66</code> is on the prohibited entity blacklist. OPA returned <code>POLICY_DENIED: prohibited beneficiary</code>.</p>
      <p><strong>Safety Outcome:</strong> Payment was never sent to core banking. Ledger delta: 0 paise.</p>
    `;
  } else if (sc === 'excessive_amount') {
    title.textContent = 'Gate 2: OPA Amount Ceiling Denial';
    body.innerHTML = `
      <p><strong>Execution Stopping Point:</strong> Halted at Gate 2 (OPA Policy Transfer Ceiling).</p>
      <p><strong>Reason:</strong> Amount 900,000,000 paise (₹90 lakh) exceeds the permitted autonomous agent threshold.</p>
      <p><strong>Safety Outcome:</strong> Core API was not invoked. Ledger delta: 0 paise.</p>
    `;
  } else if (sc === 'permitted_payment') {
    title.textContent = 'Gate 2: Permitted ₹250 Legitimate Payment';
    body.innerHTML = `
      <p><strong>Execution Result:</strong> Permitted by OPA policy.</p>
      <p><strong>Details:</strong> Valid beneficiary <code>vendor-alpha</code>, amount 25,000 paise (₹250). Settled as 1 new payment with -₹250.00 delta.</p>
    `;
  } else if (sc === 'wrong_audience') {
    title.textContent = 'Gate 3: APISIX Audience Restriction Denial';
    body.innerHTML = `
      <p><strong>Execution Stopping Point:</strong> Halted at Gate 3 (API Gateway JWT Verification).</p>
      <p><strong>Reason:</strong> Token with MCP tool audience (<code>flobank-mcp</code>) presented directly to core banking API (<code>flobank-api</code>). Rejected with HTTP 401 Unauthorized.</p>
      <p><strong>Safety Outcome:</strong> API bypass prevented. Ledger delta: 0 paise.</p>
    `;
  } else if (sc === 'insufficient_scope') {
    title.textContent = 'Gate 3: APISIX Scope Restriction Denial';
    body.innerHTML = `
      <p><strong>Execution Stopping Point:</strong> Halted at Gate 3 (Scope Enforcement).</p>
      <p><strong>Reason:</strong> Token possessed only <code>api:accounts:read</code>, but attempted <code>api:payments:write</code>. Rejected with HTTP 403 Forbidden.</p>
      <p><strong>Safety Outcome:</strong> Direct write attempt blocked. Ledger delta: 0 paise.</p>
    `;
  } else if (sc === 'scope_escalation') {
    title.textContent = 'Gate 3: Unauthorized Token Exchange Denial';
    body.innerHTML = `
      <p><strong>Execution Stopping Point:</strong> Halted at OAuth Token Exchange endpoint.</p>
      <p><strong>Reason:</strong> Agent with viewer privileges attempted to exchange token for <code>api:payments:write</code>. RFC 8693 exchange rejected with HTTP 403.</p>
    `;
  } else if (sc === 'valid_exchange') {
    title.textContent = 'Gate 3: Permitted RFC 8693 Token Exchange';
    body.innerHTML = `
      <p><strong>Execution Result:</strong> Token exchange succeeded.</p>
      <p><strong>Details:</strong> Support agent exchanged MCP token for permitted <code>api:accounts:read</code> scope on core API. Claims sanitized and verified.</p>
    `;
  } else if (sc === 'policy_outage') {
    title.textContent = 'Gate 2: Fail-Closed Policy Outage Response';
    body.innerHTML = `
      <p><strong>Execution Stopping Point:</strong> Halted at Gate 2 during policy service unavailability.</p>
      <p><strong>Reason:</strong> OPA policy service was simulated as stopped. System failed closed with <code>POLICY_DENIED: policy service unavailable</code>.</p>
      <p><strong>Safety Outcome:</strong> Zero transactions executed during policy outage.</p>
    `;
  } else {
    title.textContent = `Scenario: ${sc}`;
    body.innerHTML = `<p>State: <strong>${(run.state || '').toUpperCase()}</strong>. Ledger delta: ${formatPaise(run.effects?.balance_delta || 0)}.</p>`;
  }
}

function renderExecutionSteps(run) {
  const container = $('execution-steps');
  const countPill = $('step-count-pill');
  if (!container) return;

  const events = run.events || [];
  if (countPill) countPill.textContent = `${events.length} step${events.length === 1 ? '' : 's'}`;
  container.replaceChildren();

  if (!events.length) {
    const empty = document.createElement('p');
    empty.className = 'caption';
    empty.textContent = 'No recorded events in this run.';
    container.append(empty);
    return;
  }

  events.forEach((ev, idx) => {
    const card = document.createElement('div');
    const outcome = ev.outcome || (ev.status_code && ev.status_code < 400 ? 'allowed' : 'denied');
    card.className = `step-card ${outcome}`;

    // Header: Step #, boundary, outcome tag, status code
    const header = document.createElement('div');
    header.className = 'step-header';

    const left = document.createElement('div');
    left.innerHTML = `<strong>Step ${idx + 1}</strong> · <span style="color:#93c5fd;">${ev.boundary || 'System'}</span> · <em>${ev.label || ''}</em>`;

    const tag = document.createElement('span');
    tag.className = `step-tag ${outcome}`;
    tag.textContent = `${(outcome || '').toUpperCase()} (${ev.status_code ?? 'no response'})`;

    header.append(left, tag);

    // Identity
    const ident = document.createElement('div');
    ident.className = 'step-identity';
    const subj = ev.identity?.subject || 'anonymous/system';
    const role = ev.identity?.role ? ` [${ev.identity.role}]` : '';
    const scopes = ev.identity?.scopes ? ` · Scopes: ${ev.identity.scopes.join(', ')}` : '';
    ident.textContent = `Caller: ${subj}${role}${scopes}`;

    // Route
    const route = document.createElement('div');
    route.className = 'step-route';
    route.textContent = `${ev.method || 'CALL'} ${ev.path || ''}`;

    // Arguments / Response Details
    const details = document.createElement('div');
    details.className = 'step-details';

    let argsSummary = '';
    if (ev.arguments) {
      if (typeof ev.arguments.amount === 'number') {
        argsSummary += `Amount: ${formatPaise(ev.arguments.amount)}; `;
      }
      if (ev.arguments.beneficiary) {
        argsSummary += `Beneficiary: ${ev.arguments.beneficiary}; `;
      }
      if (ev.arguments.account_id) {
        argsSummary += `Account: ${ev.arguments.account_id}; `;
      }
      if (ev.arguments.task_type) {
        argsSummary += `Task Type: ${ev.arguments.task_type}; `;
      }
    }

    let respSummary = '';
    if (ev.response) {
      if (typeof ev.response.text === 'string') {
        respSummary = ev.response.text;
      } else if (ev.response.detail) {
        respSummary = typeof ev.response.detail === 'string' ? ev.response.detail : JSON.stringify(ev.response.detail);
      } else if (ev.response.status_code) {
        respSummary = `HTTP ${ev.response.status_code}`;
      }
    }

    details.innerHTML = `
      ${argsSummary ? `<div><strong>Arguments:</strong> ${argsSummary}</div>` : ''}
      ${respSummary ? `<div><strong>Response:</strong> ${respSummary}</div>` : ''}
    `;

    card.append(header, ident, route, details);
    container.append(card);
  });
}

function render(run) {
  if (!run) return;
  currentRun = run;
  storage.set('w4-public-run', run.run_id);

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

  // Render Step-by-Step Trajectory
  renderExecutionSteps(run);

  // Render Walkthrough & Stopping Point Card
  renderScenarioExplanation(run);

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

  const savedId = currentRun?.run_id || storage.get('w4-public-run');
  const selected = allRuns.find(r => r.run_id === savedId) || allRuns[0];
  if (selected) {
    sel.value = selected.run_id;
    render(selected);
  }
}

async function enterWorkspace() {
  const readiness = await api(API + '/readiness');
  $('readiness').textContent = `Recording available (${readiness.recording?.run_count || 11} runs) · Rehearsal snapshot: ${readiness.recording?.capture_timestamp || ''}`;

  initChaptersNav();
  setChapter(chapter);

  await loadRuns();

  const predKey = 'w4-public-predict-' + (currentRun?.scenario || 'default');
  $('prediction').value = storage.get(predKey, '');

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
    $('prediction').value = storage.get(predKey, '');
  }
};

$('prediction').oninput = () => {
  if (currentRun) {
    const predKey = 'w4-public-predict-' + currentRun.scenario;
    storage.set(predKey, $('prediction').value);
  }
};

const clearNotesBtn = $('clear-notes-btn');
if (clearNotesBtn) {
  clearNotesBtn.onclick = () => {
    storage.clearNotes();
    $('prediction').value = '';
    const orig = clearNotesBtn.textContent;
    clearNotesBtn.textContent = 'Notes cleared!';
    setTimeout(() => {
      clearNotesBtn.textContent = orig;
    }, 1500);
  };
}

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
