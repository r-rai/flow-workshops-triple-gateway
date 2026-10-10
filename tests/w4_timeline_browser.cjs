// Recorded fixtures and intercepted API calls; no scenarios or payments execute.
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.join(__dirname, '..');
const runs = JSON.parse(fs.readFileSync(path.join(root, 'workshops/w4/evidence/incident-2026-10-05T170259Z.json'), 'utf8')).runs;

(async () => {
  const browser = await chromium.launch({headless:true, args:['--no-sandbox']});
  try {
    for (const observer of [false, true]) {
      const page = await browser.newPage();
      const errors = [], mutations = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.route('**/*', route => {
        const request = route.request(), pathname = new URL(request.url()).pathname;
        if (request.method() !== 'GET') mutations.push(pathname);
        const prefix = observer ? 'incident_public' : 'incident';
        const file = pathname === '/workshop-4' ? prefix+'.html' : pathname === '/demo-assets/'+prefix+'.js' ? prefix+'.js' : null;
        if (file) return route.fulfill({contentType:file.endsWith('.js')?'application/javascript':'text/html',body:fs.readFileSync(path.join(root,'src/demo/static',file),'utf8')});
        const data = pathname.endsWith('/readiness') ? {checks:{},scenarios:runs.map(run=>({id:run.scenario,title:run.scenario})),recording:{run_count:runs.length}} : pathname.endsWith('/runs') ? runs : runs.find(run => pathname.endsWith('/runs/'+run.run_id)) || {};
        return route.fulfill({contentType:'application/json',body:JSON.stringify(data)});
      });
      await page.goto('http://workshop.test/workshop-4?view=presenter');
      await page.locator('#workspace').waitFor({state:'visible'});
      if (!observer) await page.locator('#chapters button').nth(1).click();
      // Switching away from replay must remove its narrative from the run timeline.
      for (const scenario of ['vulnerable_replay','budget_denial','prohibited_beneficiary','legitimate_delegation','vulnerable_replay']) {
        const run = runs.find(run => run.scenario === scenario);
        await page.selectOption('#runs',run.run_id);
        await page.waitForFunction(id => document.getElementById('mode').textContent.includes(id),run.run_id);
        const expected = run.events.filter(event=>event.boundary!=='Evidence').map(event=>`${event.label} · ${event.status_code ?? 'no response'} · ${event.outcome}`);
        assert.deepEqual(await page.locator('#timeline li').allTextContents(),expected,'Timeline must contain only selected run events');
        assert.match(await page.locator('#mode').textContent(),new RegExp(scenario.replaceAll('_',' ')));
        assert.match(await page.locator('#ticket-panel summary').textContent(),/Original incident context/);
        assert.match(await page.locator('#ticket-panel p').textContent(),/current run/);
        const evidence = JSON.parse(await page.locator('#evidence').textContent());
        assert.equal(evidence.run_id,run.run_id);
        if (scenario === 'prohibited_beneficiary') assert.equal(evidence.arguments.amount,25000);
      }
      assert.deepEqual(errors,[]);
      assert.deepEqual(mutations,[]);
      await page.close();
    }
    console.log('W4 presenter and observer timelines show only selected run events; original ticket context is labeled separately. No payments executed.');
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
