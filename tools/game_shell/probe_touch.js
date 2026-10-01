/* probe_touch.js -- map each lesson touch target to the cell it ACTUALLY dents.
   Speaks the page's own protocol: POST /api/touch_hit {hit, force_n},
   read GET /api/state, then POST /api/touch_clear and wait for calm.
   Answers with numbers: target -> per-cell peak Pa.
   Run: node tools/game_shell/probe_touch.js */
const sleep = ms => new Promise(r => setTimeout(r, ms));
const BASE = process.argv[2] || 'http://127.0.0.1:8206';

const state = async () => (await fetch(BASE + '/api/state')).json();
const hit = async (hitPt, forceN) => {
  const r = await fetch(BASE + '/api/touch_hit', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hit: hitPt, force_n: forceN })
  });
  return r.json();
};
const clear = async () => {
  const r = await fetch(BASE + '/api/touch_clear', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})
  });
  return r.json();
};
const waitCalm = async (capMs) => {
  const t0 = Date.now();
  while (Date.now() - t0 < capMs) {
    const s = await state();
    const ps = (s.cells || []).map(c => Math.abs(Number(c.P) || 0));
    if (ps.length && ps.every(p => p < 1000)) return true;
    await sleep(250);
  }
  return false;
};

(async () => {
  // optional: probe one explicit point: node probe_touch.js [url] x y z force
  const manual = process.argv.slice(3).map(Number);
  if (manual.length === 4) {
    const [x, y, z, f] = manual;
    const peak = [];
    const res = await hit([x, y, z], f);
    const t0 = Date.now();
    while (Date.now() - t0 < 2500) {
      const s = await state();
      (s.cells || []).forEach((c, i) => {
        peak[i] = Math.max(peak[i] || -1e9, Number(c.P) || 0);
      });
      await sleep(200);
    }
    console.log('manual hit=' + JSON.stringify([x, y, z]), 'force=' + f,
      '->', JSON.stringify(res),
      'peak Pa per cell:', peak.map((p, i) => 'c' + i + '=' + Math.round(p)).join(' '));
    await clear();
    console.log('calm after clear:', await waitCalm(12000));
    return;
  }

  console.log('baseline calm:', await waitCalm(8000));

  // THE FIRST-PRESS QUESTION: a single fresh press on the belly target,
  // exactly what L1 does as the very first touch of a session.
  const targets = [
    ['L1/L3/L5 belly', [0.0, 4.5, 0.35], 50000],
    ['L2 foot       ', [0.46, 0.18, 0.3], 500],
    ['L5 shin       ', [0.48, 1.2, -0.15], 50000]
  ];
  for (const [name, pt, f] of targets) {
    const peak = [];
    const res = await hit(pt, f);
    console.log(name, 'POST /tick_touch ->', JSON.stringify(res));
    const t0 = Date.now();
    while (Date.now() - t0 < 2500) {
      const s = await state();
      (s.cells || []).forEach((c, i) => {
        peak[i] = Math.max(peak[i] || -1e9, Number(c.P) || 0);
      });
      await sleep(200);
    }
    console.log(name, 'hit=' + JSON.stringify(pt), 'force=' + f,
      '-> peak Pa per cell:', peak.map((p, i) => 'c' + i + '=' + Math.round(p)).join(' '));
    await clear();
    console.log(name, 'calm after clear:', await waitCalm(12000));
  }
})().catch(e => { console.error('PROBE FAILED:', e.message); process.exit(1); });
