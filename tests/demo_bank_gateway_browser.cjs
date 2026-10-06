// Run against the active enterprise workshop stack at APISIX.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const baseURL = process.env.FLO_DEMO_URL || 'http://127.0.0.1:9080';
(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    const errors = [];
    const requests = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('request', request => requests.push({method: request.method(), path: new URL(request.url()).pathname}));
    await page.goto(baseURL);
    await page.locator('.login-submit').click();
    await page.locator('#dashboard-view').waitFor({state: 'visible'});
    for (const path of ['/accounts/demo-checking', '/accounts/demo-savings', '/cards/card-2048', '/cases']) {
      assert(requests.some(r => r.path === '/demo-api/banking' + path), `No browser banking request for ${path}`);
    }
    const signedIn = page.request;
    const card = await (await signedIn.get(baseURL + '/demo-api/banking/cards/card-2048')).json();
    await page.locator('#card-toggle').click();
    await page.waitForFunction(locked => document.querySelector('#card-status').textContent === (locked ? 'Frozen' : 'Active'), !card.locked);
    assert.equal((await (await signedIn.get(baseURL + '/demo-api/banking/cards/card-2048')).json()).locked, !card.locked);
    await page.locator('#card-toggle').click();
    await page.waitForFunction(locked => document.querySelector('#card-status').textContent === (locked ? 'Frozen' : 'Active'), card.locked);
    const dispute = page.getByRole('button', {name: /^(Dispute Stream\+|Track dispute for Stream\+)$/});
    await dispute.click();
    await page.waitForFunction(() => !document.querySelector('#send-message').disabled);
    assert.equal(await page.getByRole('button', {name: 'Track dispute for Stream+', exact: true}).count(), 1);
    const cases = await (await signedIn.get(baseURL + '/demo-api/banking/cases')).json();
    assert(cases.some(c => c.description.includes('tx: tx-1004')));
    await page.reload();
    await page.locator('#dashboard-view').waitFor({state: 'visible'});
    assert.equal(await page.getByRole('button', {name: 'Track dispute for Stream+', exact: true}).count(), 1);
    // Gateway failure must stay visible rather than substituting fixture balances.
    await page.route('**/demo-api/banking/accounts/demo-checking', route => route.fulfill({status: 502, contentType: 'application/json', body: JSON.stringify({detail: 'Banking gateway unavailable'})}));
    await page.locator('#message').fill('What is my balance?');
    await page.locator('#send-message').click();
    await page.waitForFunction(() => document.querySelector('#messages').textContent.includes('Banking gateway unavailable'));
    await page.locator('#logout').click();
    await page.locator('#login-view').waitFor({state: 'visible'});
    assert.equal((await signedIn.get(baseURL + '/demo-api/banking/accounts/demo-checking')).status(), 401);
    assert.deepEqual(errors, []);
    console.log('Gateway browser checks passed: visible account/card/case REST requests, persisted mutations, reload, upstream error, logout.');
    console.log(JSON.stringify(requests.filter(r => r.path.startsWith('/demo-api/banking')), null, 2));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
