// End-to-end mobile usability and security test for W4 public participant deployment using Playwright.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const base = process.env.W4_URL || 'https://w4.ravirai.in';
const defaultCodeFile = path.join(os.homedir(), '.flo-w4', 'access_code.txt');
const rotatedCode =
  process.env.W4_ACCESS_CODE ||
  (fs.existsSync(defaultCodeFile) ? fs.readFileSync(defaultCodeFile, 'utf8').trim() : '');
const oldDisclosedCode = 'FLO-W4-2026';

const mobileViewports = [
  { name: 'iPhone SE (320px)', width: 320, height: 667 },
  { name: 'Android Standard (360px)', width: 360, height: 780 },
  { name: 'iPhone 14 (390px)', width: 390, height: 844 },
  { name: 'Android Large Pixel (412px)', width: 412, height: 915 },
];

(async () => {
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  try {
    for (const vp of mobileViewports) {
      console.log(`\nTesting viewport: ${vp.name} (${vp.width}x${vp.height})...`);
      const context = await browser.newContext({
        viewport: { width: vp.width, height: vp.height },
        isMobile: true,
        hasTouch: true,
        userAgent:
          'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
      });
      // Exercise the previously broken storage-blocked phone on the first width.
      if (vp.width === 320) {
        await context.addInitScript(() => {
          Storage.prototype.getItem = () => { throw new DOMException('Storage blocked', 'SecurityError'); };
          Storage.prototype.setItem = () => { throw new DOMException('Storage blocked', 'SecurityError'); };
        });
      }
      const page = await context.newPage();

      const errors = [];
      page.on('pageerror', err => errors.push(err.message));

      // 1. Load workshop-4
      await page.goto(base + '/workshop-4', { waitUntil: 'domcontentloaded' });
      await page.waitForSelector('#signin', { state: 'visible' });

      // Check no horizontal page overflow on signin
      const overflowSignin = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      assert.equal(overflowSignin, false, `Page must not horizontally scroll on ${vp.name}`);

      // 2. Verify rotated code: old disclosed code must fail!
      await page.fill('#access-code', oldDisclosedCode);
      await page.click('#signin-form button');
      await page.waitForSelector('#error', { state: 'visible', timeout: 5000 });
      const errText = await page.$eval('#error', el => el.textContent);
      assert(errText.includes('Invalid event access code'), 'Old disclosed code must be rejected');

      // 3. Submit valid rotated access code
      await page.fill('#access-code', rotatedCode);
      await page.click('#signin-form button');

      // 4. Wait for workspace
      await page.waitForSelector('#workspace', { state: 'visible', timeout: 5000 });

      // Check no horizontal page overflow on workspace
      const overflowWorkspace = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      assert.equal(overflowWorkspace, false, `Workspace must not horizontally scroll on ${vp.name}`);

      // 5. Verify readiness and 11 runs in dropdown
      await page.waitForFunction(() => {
        const sel = document.getElementById('runs');
        return sel && sel.options.length === 11;
      }, { timeout: 5000 });

      const runsCount = await page.$eval('#runs', el => el.options.length);
      assert.equal(runsCount, 11, 'Must have exactly 11 recorded runs available');

      // 6. Test scenario: vulnerable_replay
      await page.selectOption('#runs', 'run-b27f461502750964fef9442e');
      await page.waitForFunction(() => document.getElementById('state').textContent.includes('completed'));
      const sandboxEffect = await page.$eval('#sandbox-effect', el => el.textContent);
      assert(sandboxEffect.includes('₹90 lakh loss'), 'Vulnerable replay must show ₹90 lakh loss');

      // Verify scenario explainer card
      const explainerText = await page.$eval('#scenario-explanation', el => el.textContent);
      assert(explainerText.includes('Recorded Incident'), 'Explainer must explain vulnerable incident');

      // Verify step cards exist
      const stepCards = await page.$$('.step-card');
      assert(stepCards.length > 0, 'Must render step cards');

      // 7. Test scenario: legitimate_delegation
      await page.selectOption('#runs', 'run-80da28d28e79d48b8799529a');
      await page.waitForFunction(() => document.getElementById('proposal').textContent.includes('acc-101'));
      const legExplainer = await page.$eval('#scenario-explanation', el => el.textContent);
      assert(legExplainer.includes('A2A Delegation'), 'Must explain A2A delegation flow');
      assert(legExplainer.includes('Self-Approval Rejected'), 'Must highlight self-approval rejection');
      assert(legExplainer.includes('Independent Authorization'), 'Must highlight independent reviewer');

      // 8. Test notes and clear notes button
      await page.fill('#prediction', 'Test note on shared phone');
      assert.equal(await page.$eval('#prediction', el => el.value), 'Test note on shared phone');
      await page.click('#clear-notes-btn');
      await page.waitForFunction(() => document.getElementById('prediction').value === '');
      assert.equal(await page.$eval('#prediction', el => el.value), '', 'Clear notes must reset input field');

      // 9. Verify touch target heights
      const buttonHeight = await page.$eval('#download', el => el.getBoundingClientRect().height);
      assert(buttonHeight >= 40, `Touch target height (${buttonHeight}px) should be >= 40px for mobile`);

      const downloadPromise = page.waitForEvent('download');
      await page.click('#download');
      const download = await downloadPromise;
      const stream = await download.createReadStream();
      const chunks = [];
      for await (const chunk of stream) chunks.push(chunk);
      const evidence = JSON.parse(Buffer.concat(chunks).toString());
      assert.equal(evidence.scenario, 'legitimate_delegation');
      assert.equal(evidence.effects.balance_delta, -150000);
      assert.equal(evidence.task.output.payment_id, evidence.payment.payment_id);

      await page.click('#signout');
      await page.waitForSelector('#signin', { state: 'visible' });
      assert.deepEqual(errors, [], 'No browser console errors expected');
      console.log(`✓ ${vp.name} verified successfully.`);
      await context.close();
    }

    console.log('\nAll mobile viewports verified cleanly without layout bugs or errors!');
  } finally {
    await browser.close();
  }
})().catch(err => {
  console.error('Mobile test failed:', err);
  process.exitCode = 1;
});
