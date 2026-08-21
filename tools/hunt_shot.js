// hunt_shot.js -- the SOURCE HUNT lane: see a candidate the way the human does.
// Mandatory Playwright: the AI never judges a source it has not SEEN, and the
// human is shown the same pixels.
//
//   node tools/hunt_shot.js page <url> <out.png> [wait_ms]
//       Screenshot any web page (a gallery render, an HF viewer, a listing).
//   node tools/hunt_shot.js splat <file_name_in__qualify> <out_dir> [r] [viewset]
//       Stage a downloaded 3DGS candidate through the REAL viewer: canonical
//       views (viewset 6 default) exactly like source_shots.js.
const path = require("path");
const { chromium } = require("playwright");

const VIEWSETS = {
  "6": [
    ["front", 0.0, 0.15], ["back", Math.PI, 0.15],
    ["left", Math.PI / 2, 0.15], ["right", -Math.PI / 2, 0.15],
    ["top", 0.0, 1.45], ["bottom", 0.0, -1.45],
  ],
  "3": [
    ["front", 0.0, 0.15], ["side", Math.PI / 2, 0.15], ["top", 0.0, 1.45],
  ],
};

(async () => {
  const mode = process.argv[2];
  const browser = await chromium.launch();
  if (mode === "page") {
    const [url, out, waitMs] = [process.argv[3], process.argv[4], process.argv[5] || "5000"];
    const page = await (await browser.newContext({ viewport: { width: 1280, height: 800 } })).newPage();
    await page.goto(url, { waitUntil: "networkidle", timeout: 60000 }).catch(() => {});
    await page.waitForTimeout(parseInt(waitMs));
    await page.screenshot({ path: out });
    console.log("page ->", out);
  } else if (mode === "splat") {
    const [splat, outDir, r, vs] = [process.argv[3], process.argv[4], process.argv[5] || "1.0", process.argv[6] || "6"];
    const page = await (await browser.newContext({ viewport: { width: 640, height: 360 } })).newPage();
    await page.addInitScript(() => {
      const css = document.createElement("style");
      css.textContent = "#loading,#hud,#error{display:none!important}";
      document.addEventListener("DOMContentLoaded", () => document.head.appendChild(css));
    });
    for (const [name, az, el] of VIEWSETS[vs]) {
      await page.goto(
        `http://localhost:8081/viewer.html?ply=_qualify/${splat}&orient=0&az=${az}&el=${el}&r=${r}`,
        { waitUntil: "networkidle" });
      await page.waitForTimeout(3000);
      await page.screenshot({ path: path.join(outDir, `${name}.png`) });
    }
    console.log(`${VIEWSETS[vs].length} views ->`, outDir);
  } else {
    console.error("usage: hunt_shot.js page|splat ..."); process.exit(1);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
