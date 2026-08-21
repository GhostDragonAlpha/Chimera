// source_shots.js -- 6 canonical views of a source splat through the real viewer.
//   node tools/source_shots.js <splat_name_in__qualify> <out_dir> [r]
const path = require("path");
const { chromium } = require("playwright");

(async () => {
  const splat = process.argv[2];
  const outDir = process.argv[3];
  const r = process.argv[4] || "1.0";
  const views = [
    ["front", 0.0, 0.15], ["back", Math.PI, 0.15],
    ["left", Math.PI / 2, 0.15], ["right", -Math.PI / 2, 0.15],
    ["top", 0.0, 1.45], ["bottom", 0.0, -1.45],
  ];
  const browser = await chromium.launch();
  const page = await (await browser.newContext({ viewport: { width: 640, height: 360 } })).newPage();
  await page.addInitScript(() => {
    const css = document.createElement("style");
    css.textContent = "#loading,#hud,#error{display:none!important}";
    document.addEventListener("DOMContentLoaded", () => document.head.appendChild(css));
  });
  for (const [name, az, el] of views) {
    await page.goto(
      `http://localhost:8081/viewer.html?ply=_qualify/${splat}&orient=0&az=${az}&el=${el}&r=${r}`,
      { waitUntil: "networkidle" });
    await page.waitForTimeout(3000);
    await page.screenshot({ path: path.join(outDir, `${name}.png`) });
  }
  await browser.close();
  console.log("6 views ->", outDir);
})().catch(e => { console.error(e); process.exit(1); });
