// Browser regression using intercepted API responses; creates no payments.
// Run with Playwright available through NODE_PATH.
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

(async () => {
  const browser = await chromium.launch({headless:true, args:['--no-sandbox']});
  try {
    for (const origin of ['http://workshop.test', 'http://localhost']) {
      const page = await browser.newPage();
      const errors = [], requests = [];
      page.on('pageerror', error => errors.push(error.message));
      const run = {run_id:'run-browser-test', scenario:'vulnerable_replay', state:'completed', inference_mode:'recorded', effects:{balance_delta:0,payment_count_delta:0}, identities:[], events:[], ticket:{}, sandbox:{effects:{payment_count_delta:1}}, trace_id:'test', trace_status:'incomplete'};
      await page.route('**/*', async route => {
        const request = route.request(), pathname = new URL(request.url()).pathname;
        const file = pathname === '/workshop-4' ? 'incident.html' : pathname === '/demo-assets/incident.js' ? 'incident.js' : null;
        if (file) return route.fulfill({contentType:file.endsWith('.js')?'application/javascript':'text/html',body:fs.readFileSync(path.join(__dirname,'../src/demo/static',file),'utf8')});
        let data = {};
        if (pathname.endsWith('/readiness')) data = {checks:{},scenarios:[{id:'vulnerable_replay',title:'Replay the isolated ₹90 lakh incident'}]};
        if (pathname.endsWith('/runs')) {
          if (request.method() === 'POST') {
            requests.push(request.postDataJSON());
            // A lost/error response must leave the same request ID available for retry.
            if (requests.length === 1) return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Temporary response failure'})});
            data = run;
          } else data = requests.length >= 2 ? [run] : [];
        }
        return route.fulfill({contentType:'application/json',body:JSON.stringify(data)});
      });
      await page.goto(origin+'/workshop-4?view=presenter');
      await page.locator('#workspace').waitFor({state:'visible'});
      if (origin === 'http://workshop.test') {
        assert.equal(await page.evaluate(() => window.isSecureContext), false);
        assert.equal(await page.evaluate(() => typeof crypto.randomUUID), 'undefined');
      }
      await page.locator('#run').click();
      await page.waitForTimeout(150);
      assert.equal(requests.length, 1, 'Click must dispatch even when randomUUID is unavailable');
      assert.equal(await page.locator('#run').isDisabled(), false, 'Error must release the busy state');
      assert.equal(await page.locator('#error').innerText(), 'Temporary response failure');
      await page.locator('#run').click();
      await page.waitForFunction(() => document.getElementById('state').textContent === 'completed');
      assert.equal(requests.length, 2);
      assert.equal(requests[0].request_id, requests[1].request_id, 'Retry must keep the original request ID');
      assert.match(requests[0].request_id, /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i);
      assert.equal(await page.locator('#count').innerText(), '0');
      assert.match(await page.locator('#sandbox-effect').innerText(), /₹90 lakh/);
      assert.equal(await page.locator('#error').isVisible(), false);
      assert.deepEqual(errors, []);
      await page.close();
    }
    console.log('W4 replay passed on HTTP hostname and localhost; errors release busy state and retries preserve request IDs. No payments executed.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
