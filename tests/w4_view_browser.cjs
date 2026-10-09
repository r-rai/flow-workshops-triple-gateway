// Read-only view navigation regression; no scenarios or payments are executed.
// Run with Puppeteer available through NODE_PATH; W4_TEST_SOURCE=1 serves checkout assets.
const {launch}=require('puppeteer');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const base=process.env.W4_URL || 'http://127.0.0.1:9080';

(async()=>{
  const browser=await launch({headless:true,args:['--no-sandbox']});
  try {
    const page=await browser.newPage();
    const errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    if(process.env.W4_TEST_SOURCE==='1') {
      await page.setRequestInterception(true);
      page.on('request',request=>{
        const pathname=new URL(request.url()).pathname;
        const file=pathname==='/workshop-4'?'incident.html':pathname==='/demo-assets/incident.js'?'incident.js':null;
        if(file) request.respond({status:200,contentType:file.endsWith('.js')?'application/javascript':'text/html',body:fs.readFileSync(path.join(__dirname,'../src/demo/static',file))});
        else request.continue();
      });
    }
    await page.goto(base+'/workshop-4?view=participant');
    await page.click('#signin-form button');
    await page.waitForSelector('#workspace',{visible:true});
    for(const view of ['presenter','reviewer','participant']) {
      await page.select('#view',view);
      assert.equal(await page.$eval('#presenter',el=>!el.hidden),view==='presenter');
      assert.equal(await page.$eval('#reviewer-form',el=>!el.hidden),view==='reviewer');
      assert.equal(new URL(page.url()).searchParams.get('view'),view,'URL must follow the dropdown selection');
      assert.equal(await page.$eval('#approve',el=>el.disabled),true,'View selection must not grant reviewer authority');
      await page.reload();
      await page.waitForSelector('#workspace',{visible:true});
      assert.equal(await page.$eval('#view',el=>el.value),view,'Reload must preserve the selected view');
      assert.equal(await page.$eval('#presenter',el=>!el.hidden),view==='presenter');
      assert.equal(await page.$eval('#reviewer-form',el=>!el.hidden),view==='reviewer');
    }
    await page.select('#view','presenter');
    await page.click('#chapters button:nth-child(2)');
    assert.equal(await page.$eval('#ticket-panel',el=>el.hidden),false);
    await page.goto(base+'/workshop-4?view=invalid');
    await page.waitForSelector('#workspace',{visible:true});
    assert.equal(await page.$eval('#view',el=>el.value),'participant');
    assert.equal(new URL(page.url()).searchParams.get('view'),'participant');
    assert.deepEqual(errors,[]);
    console.log('W4 views passed: dropdown, panels, URL, reload, chapter reveal and reviewer separation.');
  } finally {
    await browser.close();
  }
})().catch(error=>{console.error(error);process.exitCode=1;});
