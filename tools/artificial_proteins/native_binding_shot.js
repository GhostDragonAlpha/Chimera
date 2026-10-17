// native_binding_shot.js -- browser screenshot driver for the §11.20 stage 9
// visible-play evidence, in the existing tools/*_shots.js style (one browser
// session, one screenshot per entry; playwright-core from the repo root).
//
//   node native_binding_shot.js <spec.json>
// spec.json = {"shots":[{"url":..., "out":..., "wait_ms":...}, ...]}
// Each URL is fetched and DISPLAYED BY THE BROWSER (no page is authored --
// the engine's own /frame PNG endpoint is the existing browser path,
// ChimeraEngine/engine/main.cpp:2863).
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright-core");

(async () => {
  const spec = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
  const browser = await chromium.launch({ headless: false });  // VISIBLE browser
  const page = await (await browser.newContext({
    viewport: { width: spec.width || 1280, height: spec.height || 720 },
  })).newPage();
  for (const shot of spec.shots) {
    await page.goto(shot.url, { waitUntil: "networkidle", timeout: 20000 });
    await page.waitForTimeout(shot.wait_ms || 500);
    await page.screenshot({ path: shot.out });
    console.log("SHOT " + shot.out);
  }
  await browser.close();
})().catch((e) => { console.error("SHOT FAIL " + String(e).slice(0, 300)); process.exit(1); });
