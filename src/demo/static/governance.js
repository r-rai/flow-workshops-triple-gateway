"use strict";
const $ = (id) => document.getElementById(id);
let latest = null;
let busy = false;
const money = (minor) =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(
    minor / 100,
  );
const outcomes = {
  denied: "Execution denied",
  executed: "Payment executed",
  approval_required: "Waiting for approval",
  no_tool_proposed: "No tool proposed",
  execution_error: "Execution error",
};

async function api(path, body) {
  const response = await fetch("/demo-api" + path, {
    method: body === undefined ? "GET" : "POST",
    headers: { "Content-Type": "application/json" },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  const result = await response.json();
  if (!response.ok) {
    if (response.status === 401) {
      $("signin").hidden = false;
      $("workspace").hidden = true;
    }
    throw new Error(
      typeof result.detail === "string"
        ? result.detail
        : "The request could not be completed.",
    );
  }
  return result;
}

function showError(error) {
  $("error").textContent = error.message;
  $("error").hidden = false;
}
function bubble(label, text, type = "flo") {
  const article = document.createElement("article");
  article.className = "bubble " + type;
  const title = document.createElement("strong");
  title.textContent = label;
  const content = document.createElement("p");
  content.textContent = text;
  article.append(title, content);
  $("transcript").append(article);
  $("transcript").scrollTop = $("transcript").scrollHeight;
}

function render(result) {
  latest = result;
  $("empty-evidence").hidden = true;
  $("evidence").hidden = false;
  $("mode").textContent =
    result.mode === "live" ? "Live model" : "Recorded proposal";
  $("decision-card").className = "decision-card " + result.outcome;
  $("outcome").textContent = outcomes[result.outcome] || result.outcome;
  $("reason").textContent =
    result.reason ||
    (result.outcome === "no_tool_proposed"
      ? "The model did not request a payment. Gate 2 payment policy was not exercised."
      : "The banking service returned a payment record.");
  $("principal").textContent = result.principal.id;
  $("role").textContent = result.principal.role;
  $("model").textContent = result.model || "Recorded fixture · no inference";
  $("balance-delta").textContent = money(result.effects.balance_delta);
  $("payment-delta").textContent = result.effects.payment_count_delta;
  $("balance-detail").textContent =
    "acc-101: " +
    money(result.effects.before.balance) +
    " → " +
    money(result.effects.after.balance) +
    " · " +
    result.elapsed_ms +
    " ms";
  $("approval-card").hidden = !result.approval;
  $("approval-detail").textContent = result.approval
    ? result.approval.proposal_id + "\nStatus: " + result.approval.status
    : "";
  $("proposal").textContent = result.proposal
    ? JSON.stringify(
        { tool: "create_payment", arguments: result.proposal },
        null,
        2,
      )
    : "No tool proposed.";
  $("events").textContent = JSON.stringify(result.events, null, 2);
  $("trace").textContent = result.trace_id;
  $("gate1").textContent =
    result.mode === "live"
      ? "Live model response received"
      : "Recorded request · Gate 1 not called";
  $("gate2").textContent = result.proposal
    ? result.reason || "Tool response received"
    : "Case read only · no payment request";
  $("gate3").textContent =
    result.effects.payment_count_delta + " new payment(s) observed";
  if (result.case)
    bubble(
      "UNTRUSTED SUPPORT CASE · case-502",
      result.case.description || JSON.stringify(result.case),
      "case",
    );
  bubble(
    result.mode === "live"
      ? "Flo · live model response (untrusted)"
      : "Recorded scenario",
    result.assistant || "The model proposed a tool call.",
  );
  bubble(
    "Governance result · running services",
    outcomes[result.outcome] +
      ". " +
      (result.reason || "") +
      "\nBalance change: " +
      money(result.effects.balance_delta) +
      ". New payments: " +
      result.effects.payment_count_delta +
      ".",
  );
}

async function run(scenario) {
  if (busy) return;
  busy = true;
  $("error").hidden = true;
  $("running").hidden = false;
  document
    .querySelectorAll(".scenario, #signout")
    .forEach((b) => (b.disabled = true));
  latest = null;
  $("evidence").hidden = true;
  $("empty-evidence").hidden = false;
  $("mode").textContent = "Running";
  $("gate1").textContent =
    scenario.id === "live_review"
      ? "Live review requested"
      : "Recorded request selected";
  $("gate2").textContent = "Awaiting result";
  $("gate3").textContent = "Awaiting ledger evidence";
  bubble("Presenter", scenario.title, "user");
  try {
    render(await api("/governance/run", { scenario: scenario.id }));
  } catch (error) {
    $("mode").textContent = "Run failed";
    showError(error);
    bubble("Workshop service error", error.message);
  } finally {
    busy = false;
    $("running").hidden = true;
    document
      .querySelectorAll(".scenario, #signout")
      .forEach((b) => (b.disabled = false));
  }
}

async function openWorkspace() {
  const config = await api("/governance/config");
  $("scenarios").replaceChildren();
  for (const scenario of config.scenarios) {
    const button = document.createElement("button");
    button.className = "scenario";
    button.type = "button";
    button.textContent = scenario.title;
    button.title = scenario.description;
    button.dataset.scenario = scenario.id;
    const label = document.createElement("small");
    label.textContent =
      scenario.id === "live_review"
        ? "LIVE INFERENCE · PROVIDER KEY REQUIRED"
        : "RECORDED REQUEST · REAL ENFORCEMENT";
    button.append(label);
    button.addEventListener("click", () => run(scenario));
    $("scenarios").append(button);
  }
  $("signin").hidden = true;
  $("workspace").hidden = false;
}

$("signin-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  $("error").hidden = true;
  const submit = event.submitter;
  submit.disabled = true;
  try {
    await api("/login", {
      email: $("email").value,
      password: $("password").value,
    });
    await openWorkspace();
  } catch (error) {
    showError(error);
  } finally {
    submit.disabled = false;
  }
});
$("signout").addEventListener("click", async () => {
  try {
    await api("/logout", {});
    location.reload();
  } catch (error) {
    showError(error);
  }
});
$("download").addEventListener("click", () => {
  if (!latest) return;
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(latest, null, 2)], { type: "application/json" }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download = "w2-" + latest.scenario + "-" + latest.trace_id + ".json";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
openWorkspace().catch((error) => {
  if (!error.message.includes("sign in")) showError(error);
});
