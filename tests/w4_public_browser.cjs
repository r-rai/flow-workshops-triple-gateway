// End-to-end mobile usability and security test for W4 public participant deployment using Playwright.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');

const base = process.env.W4_URL || 'https://w4.ravirai.in';
const accessCode = process.env.W4_ACCESS_CODE || 'FLO-W4-2026';

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
      const page = await context.newPage();

      const errors = [];
      page.on('pageerror', err => errors.push(err.message));

      // 1. Load workshop-4
      await page.goto(base + '/workshop-4', { waitUntil: 'domcontentloaded' });
      await page.waitForSelector('#signin', { state: 'visible' });

      // Check no horizontal page overflow on signin
      const overflowSignin = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      assert.equal(overflowSignin, false, `Page must not horizontally scroll on ${vp.name}`);

      // 2. Submit access code
      await page.fill('#access-code', accessCode);
      await page.click('#signin-form button');

      // 3. Wait for workspace
      await page.waitForSelector('#workspace', { state: 'visible', timeout: 5000 });

      // Check no horizontal page overflow on workspace
      const overflowWorkspace = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      assert.equal(overflowWorkspace, false, `Workspace must not horizontally scroll on ${vp.name}`);

      // 4. Verify readiness and 11 runs in dropdown
      await page.waitForFunction(() => {
        const sel = document.getElementById('runs');
        return sel && sel.options.length === 11;
      }, { timeout: 5000 });

      const runsCount = await page.$eval('#runs', el => el.options.length);
      assert.equal(runsCount, 11, 'Must have exactly 11 recorded runs available');

      // 5. Test switching scenario: vulnerable_replay
      await page.selectOption('#runs', 'run-b27f461502750964fef9442e');
      await page.waitForFunction(() => document.getElementById('state').textContent.includes('completed'));
      const sandboxEffect = await page.$eval('#sandbox-effect', el => el.textContent);
      assert(sandboxEffect.includes('₹90 lakh loss'), 'Vulnerable replay must show ₹90 lakh loss');

      // 6. Test switching scenario: legitimate_delegation
      await page.selectOption('#runs', 'run-80da28d28e79d48b8799529a');
      await page.waitForFunction(() => document.getElementById('proposal').textContent.includes('acc-101'));
      const proposalText = await page.$eval('#proposal', el => el.textContent);
      assert(proposalText.includes('vendor-alpha'), 'Legitimate delegation must show proposal');

      // 7. Verify no mutating buttons exist
      assert.equal(await page.$('#run'), null, 'Run execution button must not exist');
      assert.equal(await page.$('#approve'), null, 'Approve button must not exist');
      assert.equal(await page.$('#reject'), null, 'Reject button must not exist');

      // 8. Verify primary touch targets >= 40px
      const buttonHeight = await page.$eval('#download', el => el.getBoundingClientRect().height);
      assert(buttonHeight >= 40, `Touch target height (${buttonHeight}px) should be >= 40px for mobile`);

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
