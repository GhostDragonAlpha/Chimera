const path = require('path');
const { chromium } = require(path.join('E:/PythonChimera/node_modules/playwright-core'));
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto('http://127.0.0.1:8206/?debug=1', { waitUntil: 'load' });
  await sleep(1800);
  await page.fill('#name-input', 'h7diag'); await page.click('#play-btn');
  await sleep(1200);
  try { await page.click('#intro-begin', { timeout: 2000 }); } catch (e) {}
  await sleep(600);
  await page.keyboard.press(']'); await sleep(800);   // L2
  await page.evaluate(() => { const f = document.getElementById('force'); f.value = 6000;
    f.dispatchEvent(new Event('input')); });
  let touchResp = null;
  await page.route('**/api/touch_hit', async route => {
    const resp = await route.fetch(); const b = await resp.text(); touchResp = b;
    await route.fulfill({ response: resp, body: b });
  });
  // mouse-aimed foot press (what probe_after does)
  const px = await page.evaluate(() => {
    const c = { r: 26, theta: -0.55, phi: 0.42, target: [0, 4.5, 0] };
    const vsub=(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]]; const vdot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
    const vcross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
    const vnorm=a=>{const l=Math.hypot(a[0],a[1],a[2])||1;return [a[0]/l,a[1]/l,a[2]/l];};
    const ch=Math.cos(c.phi);
    const eye=[c.target[0]+c.r*ch*Math.sin(c.theta),c.target[1]+c.r*Math.sin(c.phi),c.target[2]+c.r*ch*Math.cos(c.theta)];
    const cv=document.getElementById('gl');const b=cv.getBoundingClientRect();
    const tanF=Math.tan(45*Math.PI/360);
    const fwd=vnorm(vsub(c.target,eye)); const right=vnorm(vcross(fwd,[0,1,0])); const up=vcross(right,fwd);
    const d=vsub([0.46,0.18,0.3],eye); const a=vdot(d,fwd);
    const ndcX=(vdot(d,right)/a)/(tanF*(cv.width/cv.height)); const ndcY=(vdot(d,up)/a)/tanF;
    return {x:b.left+(ndcX+1)/2*b.width, y:b.top+(1-ndcY)/2*b.height};
  });
  console.log('aim px:', JSON.stringify(px));
  await page.mouse.move(px.x, px.y); await page.mouse.down(); await sleep(800);
  console.log('mid-press:', await page.evaluate(() => document.getElementById('judge-debug').textContent),
    '| hand:', await page.evaluate(() => document.getElementById('hand-state').textContent),
    '| touch resp:', touchResp);
  await page.mouse.up(); await sleep(4500);
  console.log('after:', await page.evaluate(() => document.getElementById('judge-debug').textContent),
    '| verdict:', await page.evaluate(() => document.getElementById('verdict').textContent));
  await page.unroute('**/api/touch_hit');
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
