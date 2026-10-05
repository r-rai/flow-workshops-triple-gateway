// Real W4 console smoke. Independent reviewer context; one fictional INR 1,500 settlement.
const { chromium }=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const base=process.env.W4_URL || 'http://127.0.0.1:9080';
(async()=>{
  assert(process.env.W4_REVIEWER_PASSWORD,'Set the configured reviewer secret');
  const browser=await chromium.launch({headless:true});
  const context=await browser.newContext({viewport:{width:1920,height:1080}});
  const reviewerContext=await browser.newContext({viewport:{width:1440,height:1100}});
  const page=await context.newPage(), review=await reviewerContext.newPage();
  const errors=[];for(const p of [page,review])p.on('pageerror',e=>errors.push(e.message));
  const stamp=new Date().toISOString().replace(/[:.]/g,'-');
  try {
    await page.goto(base+'/workshop-4?view=presenter');
    await page.locator('#signin-form button').click();
    await page.locator('#workspace').waitFor({state:'visible'});
    assert.match(await page.locator('#readiness').innerText(),/api: reachable/);
    await page.locator('#prediction').fill('Identity is valid; authority is wrong.');
    for(const scenario of ['budget_denial','prohibited_beneficiary','excessive_amount','wrong_audience','insufficient_scope','scope_escalation']) {
      await page.locator('#scenario').selectOption(scenario);
      await page.locator('#run').click();
      await page.locator('#running').waitFor({state:'hidden'});
      assert.equal(await page.locator('#error').isVisible(),false,await page.locator('#error').textContent());
      assert.equal(await page.locator('#state').innerText(),'denied');
      assert.equal(await page.locator('#count').innerText(),'0');
    }
    await page.reload();await page.locator('#workspace').waitFor({state:'visible'});
    assert.equal(await page.locator('#state').innerText(),'denied');
    await page.locator('#chapters button').nth(1).click();
    await page.locator('#scenario').selectOption('vulnerable_replay');
    await page.locator('#run').click();await page.locator('#running').waitFor({state:'hidden'});
    assert.equal(await page.locator('#state').innerText(),'completed');
    assert.match(await page.locator('#sandbox-effect').innerText(),/₹90 lakh/);
    assert.equal(await page.locator('#count').innerText(),'0');
    await page.screenshot({path:`workshops/w4/evidence/incident-presenter-${stamp}.png`,fullPage:true});
    await page.locator('#scenario').selectOption('legitimate_delegation');
    await page.locator('#run').click();await page.locator('#running').waitFor({state:'hidden'});
    assert.equal(await page.locator('#state').innerText(),'awaiting review');
    assert.equal(await page.locator('#approve').isDisabled(),true);
    await review.goto(base+'/workshop-4?view=reviewer');
    await review.locator('#signin-form button').click();await review.locator('#workspace').waitFor({state:'visible'});
    await review.locator('#reviewer-password').fill(process.env.W4_REVIEWER_PASSWORD);
    await review.locator('#reviewer-form button').click();
    await review.locator('#reviewer-status').waitFor({state:'visible'});
    await review.reload();await review.locator('#workspace').waitFor({state:'visible'});
    await review.locator('#approve').waitFor({state:'visible'});
    await review.waitForFunction(()=>!document.querySelector('#approve').disabled);
    await review.locator('#approve').click();
    await review.waitForFunction(()=>document.querySelector('#state').textContent==='completed');
    assert.equal(await review.locator('#count').innerText(),'1');
    const downloaded=review.waitForEvent('download');await review.locator('#download').click();
    const artifact=await downloaded;assert.match(artifact.suggestedFilename(),/^run-.*\.json$/);
    const data=JSON.parse(fs.readFileSync(await artifact.path(),'utf8'));
    assert.equal(data.task.output.payment_id,data.payment.payment_id);
    assert.equal(data.effects.balance_delta,-150000);
    assert.equal(JSON.stringify(data).includes(process.env.W4_REVIEWER_PASSWORD),false);
    await artifact.saveAs(`workshops/w4/evidence/incident-browser-${stamp}.json`);
    for(const width of [320,390,700,1024,1920]) {
      await page.setViewportSize({width,height:1000});
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Overflow at '+width);
    }
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:`workshops/w4/evidence/incident-mobile-${stamp}.png`,fullPage:true});
    assert.deepEqual(errors,[]);
    console.log('W4 browser passed: fixed attacks, isolated loss, refresh, independent approval, one bound payment, exports and responsive layouts.');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
