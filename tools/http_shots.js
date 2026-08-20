// http_shots.js — screenshot a splat in the HTTP viewer at controlled angles.
// The viewer (viewer.html?ply=X&orient=0&az=<rad>&el=<rad>&r=<dist>) is the
// culling-free eye for the whole pipeline. This captures 4 azimuth views plus
// a top view (el +0.9) and a bottom view (el -0.9) — the full coverage check.
//
// Usage:  node tools/http_shots.js <splat-name-in-viewer-dir> <out-dir> [radius] [orient]
// Needs:  the viewer server running (python -m http.server 8081 in
//         models/triposplat/static/viewer), playwright chromium.
const { chromium } = require("playwright");
const path = require("path");
const fs = require("fs");

const VIEWS = [
  ["front", 0, 0.15],
  ["right", Math.PI / 2, 0.15],
  ["back", Math.PI, 0.15],
  ["left", (3 * Math.PI) / 2, 0.15],
  ["top", 0, 0.95],
  ["bottom", 0, -0.95],
];

(async () => {
  const [splat, outDir, radiusArg, orientArg] = process.argv.slice(2);
  if (!splat || !outDir) {
    console.error("usage: node tools/http_shots.js <splat> <out-dir> [radius] [orient]");
    process.exit(1);
  }
  const r = radiusArg || "1.9";
  // orient: "0" = raw space (DiffSplat/direct PLY conversions); "1" = viewer applies
  // SPLAT_ORIENT -- REQUIRED for splats written by cb.save_splat (mesh_to_splat lane),
  // which pre-applies the inverse so the default-oriented viewer shows them upright.
  const orient = orientArg || "0";
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  for (const [name, az, el] of VIEWS) {
    const url = `http://localhost:8081/viewer.html?ply=${splat}&orient=${orient}&az=${az}&el=${el}&r=${r}`;
    await page.goto(url, { waitUntil: "networkidle" });
    // Judging hygiene (2026-08-20): the eye was burning "not a photograph" verdicts on the
    // HUD text itself ("UI overlay = 3D viewport"). The HUD is instrument chrome, not the
    // asset -- hide it before the shot so the gate measures the bear, not the viewer.
    await page.evaluate(() => {
      const hud = document.getElementById("hud");
      if (hud) hud.style.display = "none";
    });
    await page.waitForTimeout(5000); // splat parse + a few frames
    const out = path.join(outDir, `${name}.png`);
    await page.screenshot({ path: out });
    console.log(`${name}: ${out}`);
  }
  await browser.close();
})();
