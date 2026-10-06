"use strict";
const $ = (selector) => document.querySelector(selector);
const currency = (paise) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  }).format(paise / 100);
let sending = false;
let generation = 0;
let toastTimer;
let currentDashboard;

async function api(path, body) {
  const response = await fetch(`/demo-api/${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers: body === undefined ? {} : { "Content-Type": "application/json" },
    credentials: "same-origin",
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(
      typeof data.detail === "string"
        ? data.detail
        : "Please check your message and try again.",
    );
    error.status = response.status;
    throw error;
  }
  return data;
}

// The browser sees each real REST operation; the session proxy keeps Gate 3
// credentials server-side and forwards calls through the API gateway.
async function bankingDashboard(data) {
  if (data.backend_mode !== "enterprise") return data;
  const [checking, savings, card, cases] = await Promise.all([
    api("banking/accounts/demo-checking"),
    api("banking/accounts/demo-savings"),
    api("banking/cards/card-2048"),
    api("banking/cases"),
  ]);
  return {
    ...data,
    accounts: [checking, savings].map((account, index) => ({
      ...data.accounts[index], ...account,
    })),
    card: {...data.card, locked: card.locked},
    cases: cases.map((item) => {
      const tx = data.transactions.find(tx => item.description?.includes(`tx: ${tx.id}`));
      return {...item, transaction_id: tx?.id, merchant: tx?.merchant || "Dispute"};
    }),
  };
}

async function bankingReply(text) {
  const words = new Set(text.toLowerCase().match(/[a-z]+/g) || []);
  const has = (...terms) => terms.some(term => words.has(term));
  if (has("transfer", "send", "pay", "payment")) return null;
  if (has("unfreeze", "unlock", "freeze", "lock")) {
    const locked = !has("unfreeze", "unlock");
    const card = await api("banking/cards/card-2048/state", {locked});
    return `Your card ending 2048 is now ${card.locked ? "frozen" : "active"}. The change is saved in core banking.`;
  }
  if (has("status", "cases") && !has("card")) {
    const cases = await api("banking/cases");
    return cases.length ? cases.map(item => `${item.id}: ${item.status}`).join("\n") : "You have no disputes yet.";
  }
  if (has("dispute", "unrecognized", "unrecognised", "unauthorized", "unauthorised")) {
    const transaction_id = text.toLowerCase().match(/\btx-\d+\b/)?.[0];
    if (!transaction_id) return "Choose a debit transaction from recent activity to dispute.";
    const item = await api("banking/cases", {transaction_id});
    return `Dispute ${item.id} is ${item.status}. The case is saved in core banking; no refund has been issued.`;
  }
  if (has("balance", "account", "accounts", "savings")) {
    const data = await bankingDashboard(currentDashboard);
    return data.accounts.map(account => `${account.name}: ${currency(account.balance)}`).join("\n");
  }
  if (has("card")) {
    const card = await api("banking/cards/card-2048");
    return `Your card ending 2048 is ${card.locked ? "frozen" : "active"}.`;
  }
  return null;
}

function showToast(message) {
  $("#toast").textContent = message;
  $("#toast").hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    $("#toast").hidden = true;
  }, 4500);
}

function showLogin() {
  generation++;
  sending = false;
  $("#send-message").disabled = false;
  $("#message").value = "";
  $("#messages").replaceChildren();
  $("#dashboard-view").hidden = true;
  $("#login-view").hidden = false;
  document.title = "Flo Bank — A little more flow.";
}

function addMessage(text, role = "bot", isError = false) {
  const message = document.createElement("div");
  message.className = `message ${role}${isError ? " error-message" : ""}`;
  if (role === "bot") {
    const name = document.createElement("span");
    name.className = "message-name";
    name.textContent = "FLO";
    message.append(name);
  }
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  message.append(bubble);
  $("#messages").append(message);
  $("#messages").scrollTop = $("#messages").scrollHeight;
  return message;
}

function renderDashboard(data) {
  currentDashboard = data;
  $(".workspace-note").textContent = data.backend_mode === "enterprise"
    ? "You’re exploring fictional accounts. Card controls and disputes are saved in core banking. Transaction activity is sample data."
    : "You’re exploring fictional accounts. Card controls and disputes apply to this demo session only.";
  $("#governance-link").hidden = data.workshop_profile !== "w2";
  $("#incident-link").hidden = data.workshop_profile !== "w4";
  $("#checking-balance").textContent = currency(data.accounts[0].balance);
  $("#savings-balance").textContent = currency(data.accounts[1].balance);
  $("#spending-total").textContent = currency(
    data.transactions
      .filter((t) => t.direction === "debit")
      .reduce((total, t) => total + t.amount, 0),
  );
  $("#card-status").textContent = data.card.locked ? "Frozen" : "Active";
  const cardToggle = $("#card-toggle");
  cardToggle.textContent = data.card.locked
    ? "Unfreeze demo card  ☀"
    : "Freeze demo card  ❄";
  cardToggle.dataset.prompt = data.card.locked
    ? "Unfreeze my card"
    : "Freeze my card";
  const rows = data.transactions.map((transaction) => {
    const row = document.createElement("tr");
    const details = document.createElement("td");
    const cell = document.createElement("div");
    cell.className = "transaction-cell";
    const icon = document.createElement("span");
    icon.className = "transaction-icon";
    icon.textContent = transaction.icon;
    icon.setAttribute("aria-hidden", "true");
    const label = document.createElement("div");
    const merchant = document.createElement("strong");
    merchant.textContent = transaction.merchant;
    const category = document.createElement("small");
    category.textContent = transaction.category;
    label.append(merchant, category);
    cell.append(icon, label);
    details.append(cell);
    const date = document.createElement("td");
    date.className = "transaction-date";
    date.textContent = new Intl.DateTimeFormat("en-IN", {
      day: "numeric",
      month: "short",
      timeZone: "UTC",
    }).format(new Date(`${transaction.date}T00:00:00Z`));
    const amount = document.createElement("td");
    amount.className = `transaction-amount ${transaction.direction === "credit" ? "credit" : ""}`;
    amount.textContent = `${transaction.direction === "credit" ? "+" : "−"}${currency(transaction.amount)}`;
    const action = document.createElement("td");
    if (transaction.direction === "debit") {
      const button = document.createElement("button");
      const disputed = data.cases.some(
        (item) => item.transaction_id === transaction.id,
      );
      button.className = "dispute-button";
      button.textContent = disputed ? "Track" : "Dispute";
      button.setAttribute(
        "aria-label",
        `${disputed ? "Track dispute for" : "Dispute"} ${transaction.merchant}`,
      );
      button.dataset.prompt = disputed
        ? "Check dispute status"
        : `Dispute ${transaction.id}`;
      action.append(button);
    }
    row.append(details, date, amount, action);
    return row;
  });
  $("#transactions").replaceChildren(...rows);
}

function showDashboard(data) {
  renderDashboard(data);
  $("#login-view").hidden = true;
  $("#dashboard-view").hidden = false;
  $("#messages").replaceChildren();
  const badge = $("#chat-mode-badge");
  const desc = $("#chat-mode-desc");
  if (data && data.chat_mode === "live") {
    if (badge) badge.textContent = "LIVE AI";
    if (desc) desc.textContent = "Real model · Fictional data";
    addMessage(
      "Hey Maya, I’m Flo. ✳\n\nI’m powered by live AI to assist with your everyday banking. You can ask naturally about your balance, spending, card controls, or disputes.\n\nAll accounts and money here are fictional simulation data. Let’s explore.",
    );
    api("status")
      .then((status) => {
        if (!badge || !desc) return;
        if (status.configured && status.available) {
          const enterpriseSuffix = status.backend_mode === "enterprise" ? " · GATEWAY" : "";
          badge.textContent = `LIVE AI · ${(status.model || "MINIMAX-M2.7").toUpperCase()}${enterpriseSuffix}`;
          desc.textContent = status.backend_mode === "enterprise"
            ? "Real model · APISIX Gate 3 Core Banking"
            : "Real model · Fictional data";
        } else {
          badge.textContent = "SETUP NEEDED";
          desc.textContent = "Configure MINIMAX_API_KEY in .env";
        }
      })
      .catch(() => {});
  } else {
    if (badge) badge.textContent = data && data.backend_mode === "enterprise" ? "SCRIPTED · GATEWAY" : "SCRIPTED DEMO";
    if (desc) desc.textContent = data && data.backend_mode === "enterprise" ? "APISIX Gate 3 Core Banking" : "Always here to help";
    addMessage(
      "Hey Maya, I’m Flo. ✳\n\nThink of me as a little help with your everyday banking. Want to check your balance, talk through a charge, or try freezing your card?\n\nEverything here is a simulation. Let’s explore.",
    );
  }
  document.title = "Your overview — Flo Bank";
  window.scrollTo(0, 0);
}

async function sendMessage(text, directAction = false) {
  if (!text.trim() || sending) return;
  if (text.trim().length > 2000) {
    showToast("Keep your message under 2,000 characters.");
    return;
  }
  sending = true;
  const requestGeneration = generation;
  $("#send-message").disabled = true;
  $("#message").value = "";
  addMessage(text.trim(), "user");
  const pending = addMessage("Flo is thinking…");
  try {
    let reply = null;
    if (currentDashboard.backend_mode === "enterprise" &&
        (directAction || currentDashboard.chat_mode === "scripted")) {
      reply = await bankingReply(text.trim());
    }
    const result = reply === null
      ? await api("chat", {message: text.trim()})
      : {reply, dashboard: currentDashboard};
    result.dashboard = await bankingDashboard(result.dashboard);
    if (generation !== requestGeneration) return;
    pending.remove();
    addMessage(result.reply);
    renderDashboard(result.dashboard);
  } catch (error) {
    if (generation !== requestGeneration) return;
    pending.remove();
    if (error.status === 401) {
      showLogin();
      showToast(error.message);
    } else {
      addMessage(
        error.message + " You can try your message again.",
        "bot",
        true,
      );
      if (!$("#message").value) $("#message").value = text;
    }
  } finally {
    if (generation === requestGeneration) {
      sending = false;
      $("#send-message").disabled = false;
    }
  }
}

$("#login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = $(".login-submit");
  button.disabled = true;
  $("#login-error").hidden = true;
  try {
    const data = await api("login", {
      email: $("#email").value,
      password: $("#password").value,
    });
    generation++;
    const loginGeneration = generation;
    const dashboard = await bankingDashboard(data);
    if (generation === loginGeneration) showDashboard(dashboard);
  } catch (error) {
    $("#login-error").textContent = error.message;
    $("#login-error").hidden = false;
  } finally {
    button.disabled = false;
  }
});

$("#password-toggle").addEventListener("click", () => {
  const input = $("#password");
  const show = input.type === "password";
  input.type = show ? "text" : "password";
  $("#password-toggle").textContent = show ? "Hide" : "Show";
  $("#password-toggle").setAttribute(
    "aria-label",
    show ? "Hide password" : "Show password",
  );
});

$("#logout").addEventListener("click", async () => {
  $("#logout").disabled = true;
  try {
    await api("logout", {});
    showLogin();
  } catch {
    showToast("Could not sign out. Please try again.");
  } finally {
    $("#logout").disabled = false;
  }
});

$("#chat-form").addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage($("#message").value);
});

document.addEventListener("click", (event) => {
  const prompt = event.target.closest("[data-prompt]");
  if (prompt) {
    const message = prompt.dataset.prompt;
    // Buttons open the same chat flow as typed messages.
    $("#chat-section").scrollIntoView({ block: "nearest", behavior: "auto" });
    sendMessage(message, true);
    return;
  }
  const navigation = event.target.closest("[data-section]");
  if (navigation) {
    document
      .querySelectorAll(".nav-item")
      .forEach((item) => item.classList.toggle("active", item === navigation));
    $("#section-title").textContent = {
      overview: "Overview",
      activity: "Transactions",
      card: "My card",
      chat: "Chat with Flo",
    }[navigation.dataset.section];
    $(`#${navigation.dataset.section}-section`).scrollIntoView({
      block: "start",
      behavior: "auto",
    });
  }
});

(async () => {
  const restorationGeneration = generation;
  try {
    const data = await api("dashboard");
    if (generation !== restorationGeneration) return;
    const dashboard = await bankingDashboard(data);
    if (generation === restorationGeneration) showDashboard(dashboard);
  } catch (error) {
    if (generation !== restorationGeneration) return;
    showLogin();
    if (error.status !== 401)
      showToast("The demo server is unavailable. Try signing in again.");
  }
})();
