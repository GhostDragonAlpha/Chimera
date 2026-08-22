// tools/laneE_render_grid.js — render a 24-view grid of a splat through the HTTP viewer.
// Usage: node tools/laneE_render_grid.js <splat-name> <out-dir> [radius]
// Requires the viewer server on :8081 and Playwright Chromium.
const { chromium } = require("playwright");
const path = require("path");
const fs = require("fs");

const AZS = 8;
const ELS = [-0.6, 0.15, 0.9];
const WIDTH = 1280;
const HEIGHT = 720;

function makeViews() {
  const views = [];
  for (let e = 0; e < ELS.length; e++) {
    for (let a = 0; a < AZS; a++) {
      const az = (2 * Math.PI * a) / AZS;
      views.push({ idx: views.length, az, el: ELS[e] });
    }
  }
  return views;
}

(async () => {
  const [splat, outDir, radiusArg] = process.argv.slice(2);
  if (!splat || !outDir) {
    console.error("usage: node tools/laneE_render_grid.js <splat> <out-dir> [radius]");
    process.exit(1);
  }
  const r = radiusArg || "1.825";
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: WIDTH, height: HEIGHT } });
  const views = makeViews();
  const meta = [];
  for (const v of views) {
    const url = `http://localhost:8081/viewer.html?ply=${splat}&orient=0&az=${v.az}&el=${v.el}&r=${r}`;
    await page.goto(url, { waitUntil: "networkidle" });
    await page.waitForTimeout(5000);
    const name = `view_${String(v.idx).padStart(3, "0")}_az${v.az.toFixed(4)}_el${v.el.toFixed(4)}.png`;
    const out = path.join(outDir, name);
    await page.screenshot({ path: out });
    meta.push({ idx: v.idx, az: v.az, el: v.el, r: parseFloat(r), file: name });
    console.log(`${name}`);
  }
  fs.writeFileSync(path.join(outDir, "laneE_views.json"), JSON.stringify(meta, null, 2));
  await browser.close();
  console.log(`wrote ${views.length} views to ${outDir}`);
})();
