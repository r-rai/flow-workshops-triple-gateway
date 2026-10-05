// Run against W2. Installs no dependencies; use the existing temporary Playwright setup.
// Creates one fictional INR 250 payment and one pending proposal.
const { chromium } = require("playwright");
const assert = require("node:assert/strict");
const baseURL = process.env.W2_URL || "http://127.0.0.1:9080";

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({
      viewport: { width: 1440, height: 1100 },
    });
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.goto(baseURL + "/workshop-2");
    await page.locator("#signin-form button").click();
    await page.locator("#workspace").waitFor({ state: "visible" });
    for (const [scenario, outcome, count] of [
      ["injection", "Execution denied", "0"],
      ["small_payment", "Payment executed", "1"],
      ["approval", "Waiting for approval", "0"],
      ["ceiling", "Execution denied", "0"],
      ["identity", "Execution denied", "0"],
    ]) {
      await page.locator('[data-scenario="' + scenario + '"]').click();
      await page.locator("#running").waitFor({ state: "hidden" });
      assert.equal(await page.locator("#error").isVisible(), false);
      assert.equal(await page.locator("#outcome").innerText(), outcome);
      assert.equal(await page.locator("#payment-delta").innerText(), count);
      assert.equal(
        await page.locator("#mode").innerText(),
        "Recorded proposal",
      );
    }
    const downloadPromise = page.waitForEvent("download");
    await page.locator("#download").click();
    const download = await downloadPromise;
    assert.match(download.suggestedFilename(), /^w2-identity-.*\.json$/);
    await page.screenshot({
      path: "/tmp/w2-governance-desktop.png",
      fullPage: true,
    });
    for (const width of [320, 390, 700, 768, 1024, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      assert.equal(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
        true,
        "Overflow at " + width,
      );
    }
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({
      path: "/tmp/w2-governance-mobile.png",
      fullPage: true,
    });
    // A failed live request must clear old evidence and render error text literally.
    await page.route("**/demo-api/governance/run", (route) =>
      route.fulfill({
        status: 502,
        contentType: "application/json",
        body: JSON.stringify({
          detail:
            '<img src=x onerror="window.injected=true"> Provider unavailable.',
        }),
      }),
    );
    await page.locator('[data-scenario="live_review"]').click();
    await page.locator("#running").waitFor({ state: "hidden" });
    assert.equal(await page.locator("#evidence").isVisible(), false);
    assert.equal(await page.locator("#mode").innerText(), "Run failed");
    assert.equal(await page.evaluate(() => window.injected), undefined);
    await page.unroute("**/demo-api/governance/run");
    await page.goto(baseURL);
    await page.locator("#governance-link").waitFor({ state: "visible" });
    await page.locator("#governance-link").click();
    await page.locator("#workspace").waitFor({ state: "visible" });
    await page.locator("#signout").click();
    await page.locator("#signin").waitFor({ state: "visible" });
    assert.deepEqual(errors, []);
    console.log(
      "W2 browser checks passed: scenarios, evidence export, responsive layouts, failure rendering, dashboard link and logout.",
    );
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
