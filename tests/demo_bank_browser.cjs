// Optional browser verification. Install Playwright in a temporary directory; see README.
const { chromium } = require("playwright");
const baseURL = process.env.FLO_DEMO_URL || "http://127.0.0.1:8000";
const assert = require("node:assert/strict");
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1100 },
  });
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto(baseURL);
  await page.locator("#login-view").waitFor({ state: "visible" });
  await page.screenshot({ path: "/tmp/flo-bank-login.png", fullPage: true });
  await page.locator("#password").fill("wrong");
  await page.locator(".login-submit").click();
  await page.locator("#login-error").waitFor({ state: "visible" });
  await page.locator("#password").fill("flo-demo");
  await page.locator(".login-submit").click();
  await page.locator("#dashboard-view").waitFor({ state: "visible" });
  assert.match(await page.locator("#checking-balance").innerText(), /1,24,850/);
  await page.locator("#message").fill("What is my balance?");
  await page.locator("#send-message").click();
  await page.waitForFunction(() =>
    document.querySelector("#messages").textContent.includes("1,24,850"),
  );
  await page.locator("#card-toggle").click();
  await page.waitForFunction(
    () => document.querySelector("#card-status").textContent === "Frozen",
  );
  await page.locator("#card-toggle").click();
  await page.waitForFunction(
    () => document.querySelector("#card-status").textContent === "Active",
  );
  await page
    .getByRole("button", { name: "Dispute Stream+", exact: true })
    .click();
  await page.waitForFunction(() =>
    document.querySelector("#messages").textContent.includes("DEMO-1001"),
  );
  assert.equal(
    await page
      .getByRole("button", { name: "Track dispute for Stream+", exact: true })
      .count(),
    1,
  );
  await page.screenshot({
    path: "/tmp/flo-bank-dashboard.png",
    fullPage: true,
  });
  // Text is always rendered literally, including HTML entered by a user.
  await page
    .locator("#message")
    .fill('<img src=x onerror="window.floInjected=true">');
  await page.locator("#send-message").click();
  await page.waitForFunction(
    () => !document.querySelector("#send-message").disabled,
  );
  assert.equal(await page.evaluate(() => window.floInjected), undefined);
  await page.reload();
  await page.locator("#dashboard-view").waitFor({ state: "visible" });
  assert.equal(
    await page
      .getByRole("button", { name: "Track dispute for Stream+", exact: true })
      .count(),
    1,
  );
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: "/tmp/flo-bank-mobile.png", fullPage: true });
  assert.equal(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
    true,
  );
  await page
    .getByRole("button", { name: "Chat with Flo", exact: true })
    .click();
  await page.locator("#message").fill("Check dispute status");
  await page.locator("#send-message").click();
  await page.waitForFunction(() =>
    document.querySelector("#messages").textContent.includes("DEMO-1001"),
  );
  await page.locator("#logout").click();
  await page.locator("#login-view").waitFor({ state: "visible" });
  await page.locator(".login-submit").click();
  await page.locator("#dashboard-view").waitFor({ state: "visible" });
  assert.equal(
    await page
      .getByRole("button", { name: "Dispute Stream+", exact: true })
      .count(),
    1,
  );
  assert.deepEqual(errors, []);
  for (const width of [320, 390, 700, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    assert.equal(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      true,
      `overflow at ${width}px`,
    );
  }
  // An old page-load response must not overwrite a new signed-in session.
  const delayed = await browser.newPage();
  let startupRoute;
  let signalStartup;
  const startupSeen = new Promise((resolve) => {
    signalStartup = resolve;
  });
  await delayed.route("**/demo-api/dashboard", (route) => {
    startupRoute = route;
    signalStartup();
  });
  await delayed.goto(baseURL);
  await startupSeen;
  await delayed.locator(".login-submit").click();
  await delayed.locator("#dashboard-view").waitFor({ state: "visible" });
  const staleResponse = delayed.waitForResponse((response) =>
    response.url().endsWith("/demo-api/dashboard"),
  );
  await startupRoute.fulfill({
    status: 401,
    contentType: "application/json",
    body: JSON.stringify({ detail: "Old session expired" }),
  });
  await staleResponse;
  await delayed.evaluate(
    () =>
      new Promise((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(resolve)),
      ),
  );
  assert.equal(
    await delayed.locator("#dashboard-view").isVisible(),
    true,
    "stale startup response undid login",
  );
  await delayed.close();
  // A stale successful restore must also leave a newer sign-out intact.
  const oldSnapshot = await (
    await page.request.get(`${baseURL}/demo-api/dashboard`)
  ).json();
  const signingOut = await browser.newPage();
  let oldRoute;
  let signalOld;
  const oldSeen = new Promise((resolve) => {
    signalOld = resolve;
  });
  await signingOut.route("**/demo-api/dashboard", (route) => {
    oldRoute = route;
    signalOld();
  });
  await signingOut.goto(baseURL);
  await oldSeen;
  await signingOut.locator(".login-submit").click();
  await signingOut.locator("#dashboard-view").waitFor({ state: "visible" });
  await signingOut.locator("#logout").click();
  await signingOut.locator("#login-view").waitFor({ state: "visible" });
  const oldResponse = signingOut.waitForResponse((response) =>
    response.url().endsWith("/demo-api/dashboard"),
  );
  await oldRoute.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify(oldSnapshot),
  });
  await oldResponse;
  await signingOut.evaluate(
    () =>
      new Promise((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(resolve)),
      ),
  );
  assert.equal(
    await signingOut.locator("#login-view").isVisible(),
    true,
    "stale startup response undid sign-out",
  );
  await signingOut.close();
  const drafting = await browser.newPage();
  await drafting.goto(baseURL);
  await drafting.locator(".login-submit").click();
  await drafting.locator("#dashboard-view").waitFor({ state: "visible" });
  let chatRoute;
  let signalChat;
  const chatSeen = new Promise((resolve) => {
    signalChat = resolve;
  });
  await drafting.route("**/demo-api/chat", (route) => {
    chatRoute = route;
    signalChat();
  });
  await drafting.locator("#message").fill("What is my balance?");
  await drafting.locator("#send-message").click();
  await chatSeen;
  await drafting.locator("#message").fill("My next question");
  await chatRoute.fulfill({
    status: 503,
    contentType: "application/json",
    body: JSON.stringify({ detail: "Temporarily unavailable" }),
  });
  await drafting.waitForFunction(
    () => !document.querySelector("#send-message").disabled,
  );
  assert.equal(
    await drafting.locator("#message").inputValue(),
    "My next question",
    "failed chat overwrote a new draft",
  );
  await drafting.close();
  console.log(
    "Browser smoke passed: login validation, balances, chat, card controls, disputes, refresh, responsive layouts, XSS text handling, logout/reset, stale responses, draft preservation.",
  );
  await browser.close();
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
