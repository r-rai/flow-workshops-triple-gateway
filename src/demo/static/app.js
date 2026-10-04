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

async function sendMessage(text) {
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
    const result = await api("chat", { message: text.trim() });
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
    showDashboard(data);
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
    sendMessage(message);
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
    if (generation === restorationGeneration) showDashboard(data);
  } catch (error) {
    if (generation !== restorationGeneration) return;
    showLogin();
    if (error.status !== 401)
      showToast("The demo server is unavailable. Try signing in again.");
  }
})();
