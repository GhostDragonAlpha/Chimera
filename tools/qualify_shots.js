// qualify_shots.js -- render every queued patch through the REAL splat viewer.
// The numpy mini-rasterizer is approximate; the eye must judge what the viewer
// actually draws. One browser session, one top-down screenshot per patch.
//
//   node tools/qualify_shots.js <shot_dir> <r>
// shot_dir/manifest.json = ["p00000", ...]; splats live in
// models/triposplat/static/viewer/_qualify/<name>.splat; pngs land in shot_dir.
const path = require("path");
const fs = require("fs");
const { chromium } = require("playwright");

(async () => {
  const shotDir = process.argv[2];
  const r = process.argv[3] || "0.2";
  const names = JSON.parse(fs.readFileSync(path.join(shotDir, "manifest.json")));
  const browser = await chromium.launch();
  const page = await (await browser.newContext({ viewport: { width: 640, height: 360 } })).newPage();
  await page.addInitScript(() => {
    const css = document.createElement("style");
    css.textContent = "#loading,#hud,#error{display:none!important}";
    document.addEventListener("DOMContentLoaded", () => document.head.appendChild(css));
  });
  for (const name of names) {
    await page.goto(
      `http://localhost:8081/viewer.html?ply=_qualify/${name}.splat&orient=0&el=1.51&r=${r}`,
      { waitUntil: "networkidle" });
    await page.waitForTimeout(2500);
    await page.screenshot({ path: path.join(shotDir, `${name}.png`) });
  }
  await browser.close();
  console.log(`shots: ${names.length} -> ${shotDir}`);
})().catch(e => { console.error(e); process.exit(1); });
