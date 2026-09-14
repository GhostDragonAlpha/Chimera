/* CHIMERA — tools/game_shell/sound.js
 *
 * All sound for the game page, synthesized at runtime with WebAudio:
 * oscillators, noise buffers, envelopes. NO audio files, NO network,
 * NO external assets — this one file is the entire sound department.
 *
 * Integration:
 *   <script src="sound.js"></script>
 *   PLAY button click : ChimeraSound.init(); ChimeraSound.ambient(true);
 *   touch begins      : ChimeraSound.press(forceN [, region]);  (re-call while held: the tone follows force AND region, live)
 *   touch released    : ChimeraSound.pressEnd();
 *   cell first crosses its wake bar : ChimeraSound.wakeWhoosh();   (pass 2 — a ~300 ms noise swell)
 *   release-phase heal completes    : ChimeraSound.healShimmer();  (pass 2 — a very quiet high shimmer)
 *   cell wakes        : ChimeraSound.cellWake();
 *   lesson passed     : ChimeraSound.passed();
 *   progress saved    : ChimeraSound.saved();
 *
 * The region hint (pass 2): the creature has 4 sealed cells, each with its
 * own voice. Accepts a region NAME ('foot' | 'body' | 'thigh' | 'shin' —
 * plurals and 'torso' alias; default 'body'), a CELL INDEX (0 feet, 1 torso,
 * 2 thighs, 3 shins — lessons.json's cell map), or a WORLD POINT [x,y,z]
 * (its Y is matched against the live per-cell ylo/yhi bands from /api/state).
 * Omitted while a press is held = keep the held press's region.
 *
 * If WebAudio is unavailable, every call feature-detects and no-ops silently.
 *
 * ---------------------------------------------------------------------------
 * PASS-2 WIRING — exact index.html call sites (the html lane owns that file;
 * this block is the contract; line numbers refer to index.html 2026-09-13):
 *
 *   1. SPACE press — key handler, inside the postJSON(API.touchHit).then,
 *      where the existing press call sits (~line 1268). Add the region hint;
 *      the page already holds the world target:
 *          ChimeraSound.press(Number(forceEl.value), touchTarget);
 *
 *   2. Gamepad A press — pollGamepad, the existing press call (~line 1302):
 *          ChimeraSound.press(f, touchTarget);
 *
 *   3. Canvas touch — tryTouch, inside `if (res && res.ok)` (~line 1389).
 *      This path is currently SILENT; give it the same voice, using the
 *      engine's own resolved hit from the /tick_touch response:
 *          ChimeraSound.press(Number(forceEl.value), res.hit);
 *
 *   4. Force-follow mid-hold — the #force 'input' listener (~line 1452).
 *      The gamepad path already re-calls press on force change; the
 *      keyboard/slider path does not, so '-'/'=' and slider drags during a
 *      SPACE hold never retarget the tone. Add:
 *          if (holding && window.ChimeraSound) ChimeraSound.press(Number(forceEl.value));
 *      press() retargets the held voice live (80 ms glide), never stacks.
 *
 *   5. wakeWhoosh — judgeState. Fire ONCE per false-to-true crossing of a
 *      cell's wake bar: memo per (cell, threshold) across polls (a plain
 *      object on curState(), e.g. st.wokeMemo) and call when `woke()`
 *      (~line 1141) flips a memo from false to true:
 *          ChimeraSound.wakeWhoosh();
 *      The existing ChimeraSound.cellWake() keeps its goal-met role — the
 *      whoosh marks the CROSSING, the chime marks the LATCH.
 *
 *   6. healShimmer — judgeState, the release-phase heal branch
 *      (`st.phase === 'release'` && calm, ~line 1160), just before
 *      ChimeraSound.passed():
 *          ChimeraSound.healShimmer();
 * --------------------------------------------------------------------------- 
 */
(function () {
"use strict";

// -- shared state -----------------------------------------------------------
var ctx = null;        // the AudioContext — created by init() inside the user gesture
var master = null;     // master gain (0.5 ceiling) feeding a subtle compressor
var whiteBuf = null;   // shared white-noise buffer (press "skin tension")
var brownBuf = null;   // shared brown-noise buffer (ambient "air")
var ambV = { built: false, fade: null, sources: [], killTimer: null };
var pressV = null;     // live press voice, or null when the player is not pressing

var FORCE_MIN = 500;   // the slider's floor, in newtons
var FORCE_MAX = 50000; // the slider's ceiling, in newtons
var AMB_LEVEL = 0.25;  // ambient fade target — a very quiet, -24 dB feel
var AMB_IN_S = 3;      // ambient fade-in seconds
var AMB_OUT_S = 2;     // ambient fade-out seconds (per spec)

function ready() { return !!(ctx && master && ctx.state !== "closed"); }
function now() { return ctx.currentTime; }

// buildMaster: master gain (0.5 max) into a gentle DynamicsCompressor, then out.
function buildMaster() {
  master = ctx.createGain();
  master.gain.value = 0.5;
  var comp = ctx.createDynamicsCompressor();
  comp.threshold.value = -18;
  comp.knee.value = 24;
  comp.ratio.value = 3;
  comp.attack.value = 0.01;
  comp.release.value = 0.25;
  master.connect(comp);
  comp.connect(ctx.destination);
}

// makeNoise: fill a 2 s mono buffer — brown (integrated, drift-corrected) or white.
function makeNoise(brown) {
  var len = Math.floor(ctx.sampleRate * 2);
  var buf = ctx.createBuffer(1, len, ctx.sampleRate);
  var d = buf.getChannelData(0);
  var last = 0;
  for (var i = 0; i < len; i++) {
    var w = Math.random() * 2 - 1;
    if (brown) { last = (last + 0.02 * w) / 1.02; d[i] = last * 3.5; }
    else { d[i] = w; }
  }
  return buf;
}

// tone: one enveloped oscillator partial — attack, exponential decay, self-stopping.
function tone(type, freq, at, peak, attack, decay) {
  var o = ctx.createOscillator();
  o.type = type;
  o.frequency.value = freq;
  var g = ctx.createGain();
  g.gain.setValueAtTime(0.0001, at);
  g.gain.linearRampToValueAtTime(peak, at + attack);
  g.gain.exponentialRampToValueAtTime(0.0001, at + attack + decay);
  o.connect(g);
  g.connect(master);
  o.start(at);
  o.stop(at + attack + decay + 0.05);
  return o;
}

// forceCurve: map 500..50000 N to 0..1 with a square-root curve so most of the slider stays subtle.
function forceCurve(force_n) {
  var f = Number(force_n);
  if (!isFinite(f)) f = FORCE_MIN;
  var t = (f - FORCE_MIN) / (FORCE_MAX - FORCE_MIN);
  t = Math.max(0, Math.min(1, t));
  return Math.sqrt(t);
}

// -- region map (pass 2) ----------------------------------------------------
// Each sealed cell is its own instrument: the press band lives inside the
// region's band, sweeping lo->hi as force grows (foot: dull thud, thigh:
// rounder, shin: brighter, body: full low). s0/s1 are the low sine hum's
// endpoints for the region; q0/q1 the bandpass Q (foot is tighter = thuddier).

var REGIONS = {
  foot:  { name: "foot",  lo:  80, hi: 150, q0: 1.2, q1: 2.2, s0: 42, s1:  58 },
  body:  { name: "body",  lo:  60, hi: 200, q0: 0.8, q1: 1.6, s0: 52, s1:  98 },
  thigh: { name: "thigh", lo: 200, hi: 400, q0: 0.7, q1: 1.4, s0: 48, s1:  72 },
  shin:  { name: "shin",  lo: 500, hi: 900, q0: 0.7, q1: 1.4, s0: 60, s1: 105 }
};
var CELL_REGION   = ["foot", "body", "thigh", "shin"];   // lessons.json cell map: 0 feet, 1 torso, 2 thighs, 3 shins
var FALLBACK_BANDS = [[-0.020, 0.338], [3.415, 9.9712], [1.903, 3.415], [0.338, 1.903]]; // by CELL index; measured 2026-09-13
var cellBands = null;      // live [[ylo,yhi] x4] from /api/state, once a fetch lands
var bandsAt = 0;           // when the last bands fetch was attempted (10 s throttle)

// fetchBands: pull the live per-cell ylo/yhi bands so a world point can be
// named. Fire-and-forget, relative URL (same server serves the page), stale
// bands keep sounding while a refresh is in flight.
function fetchBands() {
  if (!window.fetch) return;
  var t = Date.now();
  if (bandsAt && t - bandsAt < 10000) return;
  bandsAt = t;
  window.fetch("/api/state").then(function (r) { return r.json(); }).then(function (s) {
    var cells = (s && s.cells) || [];
    if (cells.length >= 2) {
      cellBands = cells.map(function (c) { return [Number(c.ylo) || 0, Number(c.yhi) || 0]; });
    }
  }).catch(function () { /* keep fallback bands */ });
}

// regionFromY: which cell owns this height? Exact band hit wins; otherwise the
// nearest band midpoint (so a point a hair off the surface still names a part).
function regionFromY(y) {
  var bands = cellBands || FALLBACK_BANDS;
  var best = 0, bestD = Infinity;
  for (var i = 0; i < bands.length && i < CELL_REGION.length; i++) {
    if (y >= bands[i][0] && y <= bands[i][1]) { fetchBands(); return CELL_REGION[i]; }
    var d = Math.abs(y - (bands[i][0] + bands[i][1]) / 2);
    if (d < bestD) { bestD = d; best = i; }
  }
  fetchBands();
  return CELL_REGION[best];
}

// resolveRegion: normalize any region hint (name / cell index / world point /
// absent) into a REGIONS entry. Absent keeps the current one (default body).
function resolveRegion(region, cur) {
  if (region === undefined || region === null) return cur || REGIONS.body;
  var k = null;
  if (typeof region === "string") {
    k = region.toLowerCase();
    if (k === "torso") k = "body";
    if (k === "feet") k = "foot";
    if (k === "thighs") k = "thigh";
    if (k === "shins") k = "shin";
    if (!REGIONS[k]) k = null;
  } else if (typeof region === "number" && isFinite(region)) {
    k = CELL_REGION[region] || null;                 // 0..3; anything else falls back
  } else if (region && typeof region.length === "number" && region.length >= 1) {
    var y = Number(region[1]);
    if (isFinite(y)) k = regionFromY(y);
  }
  return (k && REGIONS[k]) || cur || REGIONS.body;
}

// -- ambient voice ----------------------------------------------------------

// buildAmb: the evolving bed — 3 detuned low oscillators breathed by two slow LFOs, plus faint low-passed brown noise for air.
function buildAmb() {
  var fade = ctx.createGain();
  fade.gain.value = 0;
  fade.connect(master);
  var mix = ctx.createGain();
  mix.gain.value = 0.6;
  mix.connect(fade);
  [{ type: "sine", freq: 55.00, det: +4, gain: 0.30 },
   { type: "sine", freq: 82.41, det: -5, gain: 0.22 },
   { type: "triangle", freq: 110.0, det: +7, gain: 0.10 }].forEach(function (s) {
    var o = ctx.createOscillator();
    o.type = s.type;
    o.frequency.value = s.freq;
    o.detune.value = s.det;
    var g = ctx.createGain();
    g.gain.value = s.gain;
    o.connect(g);
    g.connect(mix);
    o.start();
    ambV.sources.push(o);
  });
  [[0.05, 0.25], [0.13, 0.12]].forEach(function (l) {   // slow swells on the mix gain
    var lfo = ctx.createOscillator();
    lfo.frequency.value = l[0];
    var lg = ctx.createGain();
    lg.gain.value = l[1];
    lfo.connect(lg);
    lg.connect(mix.gain);
    lfo.start();
    ambV.sources.push(lfo);
  });
  var air = ctx.createBufferSource();
  air.buffer = brownBuf;
  air.loop = true;
  var lp = ctx.createBiquadFilter();
  lp.type = "lowpass";
  lp.frequency.value = 320;
  var ag = ctx.createGain();
  ag.gain.value = 0.06;
  air.connect(lp);
  lp.connect(ag);
  ag.connect(fade);
  air.start();
  ambV.sources.push(air);
  ambV.fade = fade;
  ambV.built = true;
}

// fadeAmb: ramp the ambient bus to a level over the given seconds, from wherever it is now.
function fadeAmb(level, seconds) {
  var g = ambV.fade.gain;
  var t = now();
  g.cancelScheduledValues(t);
  g.setValueAtTime(g.value, t);
  g.linearRampToValueAtTime(level, t + seconds);
}

// killAmb: stop and tear down the ambient voice (scheduled after the fade-out lands).
function killAmb() {
  if (!ambV.built) return;
  ambV.sources.forEach(function (s) { try { s.stop(); } catch (e) {} });
  if (ambV.fade) { try { ambV.fade.disconnect(); } catch (e) {} }
  ambV.sources = [];
  ambV.fade = null;
  ambV.built = false;
}

// -- public API -------------------------------------------------------------

// init: create/resume the AudioContext — call once from the PLAY button's click (a user gesture); safe to call again.
function init() {
  if (ctx) {
    if (ctx.state === "suspended") ctx.resume().catch(function () {});
    return;
  }
  var AC = window.AudioContext || window.webkitAudioContext;
  if (!AC) return;                                   // no WebAudio: every call below stays a silent no-op
  try { ctx = new AC(); } catch (e) { ctx = null; return; }
  buildMaster();
  whiteBuf = makeNoise(false);
  brownBuf = makeNoise(true);
  if (ctx.state === "suspended") ctx.resume().catch(function () {});
}

// ambient: soft evolving bed of detuned low oscillators + faint filtered brown noise; on=false fades it out over 2 s.
function ambient(on) {
  if (!ready()) return;
  if (on) {
    if (ambV.killTimer) { clearTimeout(ambV.killTimer); ambV.killTimer = null; }
    if (!ambV.built) buildAmb();
    fadeAmb(AMB_LEVEL, AMB_IN_S);
  } else {
    if (!ambV.built) return;
    fadeAmb(0, AMB_OUT_S);
    if (!ambV.killTimer) ambV.killTimer = setTimeout(killAmb, AMB_OUT_S * 1000 + 300);
  }
}

// press: begin (or re-target, idempotently) the sustained skin-tension tone — band-passed noise + a low sine whose brightness and volume follow the force in newtons, subtle to firm, never harsh.
// Region hint (pass 2): press(force_n, region) where region is 'foot'|'body'|'thigh'|'shin' (or a cell index 0..3, or a world point [x,y,z]) —
// no hint = 'body' (backward compatible); omitted on a mid-hold re-call = keep the held press's region. Force AND region retarget live (80 ms glide).
function press(force_n, region) {
  if (!ready()) return;
  var c = forceCurve(force_n);
  var r = resolveRegion(region, pressV ? pressV.region : REGIONS.body);
  var p = {
    bandHz: r.lo + (r.hi - r.lo) * c,   // the region's band, sweeping lo->hi as force grows
    bandQ:  r.q0 + (r.q1 - r.q0) * c,
    noiseG: 0.015 + 0.075 * c,
    sineHz: r.s0 + (r.s1 - r.s0) * c,   // the body hum rises slightly under load
    sineG:  0.04 + 0.10 * c,
    busG:   0.5 + 0.5 * c
  };
  if (pressV) {                 // already held: just follow the new force/region, never stack voices
    var t2 = now(), k = 0.08;
    pressV.band.frequency.setTargetAtTime(p.bandHz, t2, k);
    pressV.band.Q.setTargetAtTime(p.bandQ, t2, k);
    pressV.ng.gain.setTargetAtTime(p.noiseG, t2, k);
    pressV.osc.frequency.setTargetAtTime(p.sineHz, t2, k);
    pressV.og.gain.setTargetAtTime(p.sineG, t2, k);
    pressV.bus.gain.setTargetAtTime(p.busG, t2, k);
    pressV.region = r;
    return;
  }
  var bus = ctx.createGain();
  bus.gain.value = 0;
  var ns = ctx.createBufferSource();
  ns.buffer = whiteBuf;
  ns.loop = true;
  var band = ctx.createBiquadFilter();
  band.type = "bandpass";
  band.frequency.value = p.bandHz;
  band.Q.value = p.bandQ;
  var ng = ctx.createGain();
  ng.gain.value = p.noiseG;
  ns.connect(band);
  band.connect(ng);
  ng.connect(bus);
  var osc = ctx.createOscillator();
  osc.type = "sine";
  osc.frequency.value = p.sineHz;
  var og = ctx.createGain();
  og.gain.value = p.sineG;
  osc.connect(og);
  og.connect(bus);
  bus.connect(master);
  ns.start();
  osc.start();
  var t = now();
  bus.gain.setValueAtTime(0, t);
  bus.gain.linearRampToValueAtTime(p.busG, t + 0.12);   // swell in, no click
  pressV = { bus: bus, ns: ns, band: band, ng: ng, osc: osc, og: og, region: r };
}

// pressEnd: release the skin-tension tone with a short (~150 ms) natural decay.
function pressEnd() {
  if (!pressV) return;
  var v = pressV;
  pressV = null;
  var t = now();
  v.bus.gain.cancelScheduledValues(t);
  v.bus.gain.setValueAtTime(v.bus.gain.value, t);
  v.bus.gain.setTargetAtTime(0, t, 0.05);               // 3τ ≈ 150 ms release
  try { v.ns.stop(t + 0.3); } catch (e) {}
  try { v.osc.stop(t + 0.3); } catch (e) {}
  setTimeout(function () { try { v.bus.disconnect(); } catch (e) {} }, 400);
}

// wakeWhoosh (pass 2): a ~300 ms filtered-noise swell — one cell just crossed its wake bar.
// A rising bandpass over white noise (no pitch, no chime) so a crossing reads as "something
// woke THERE" and several near-simultaneous crossings stack without phase-locking.
function wakeWhoosh() {
  if (!ready()) return;
  var t = now() + 0.01;
  var ns = ctx.createBufferSource();
  ns.buffer = whiteBuf;
  ns.loop = true;
  var band = ctx.createBiquadFilter();
  band.type = "bandpass";
  band.Q.value = 0.9;
  var v = 0.8 + Math.random() * 0.4;                     // per-call variance: swells never phase-lock
  band.frequency.setValueAtTime(350 * v, t);
  band.frequency.exponentialRampToValueAtTime(900 * v, t + 0.30);   // the rise is the whoosh
  var g = ctx.createGain();
  g.gain.setValueAtTime(0.0001, t);
  g.gain.linearRampToValueAtTime(0.11, t + 0.13);        // swell up, no click
  g.gain.exponentialRampToValueAtTime(0.0001, t + 0.30); // gone by ~300 ms
  ns.connect(band);
  band.connect(g);
  g.connect(master);
  ns.start(t);
  ns.stop(t + 0.35);
  setTimeout(function () { try { g.disconnect(); } catch (e) {} }, 500);
}

// healShimmer (pass 2): a very quiet high shimmer (C7/E7/G7 pairs, 2093-3136 Hz, ±3.5 cents
// so each pair beats slowly) with a 600 ms fade — the release-phase heal just completed and
// every cell is calm. Deliberately quieter than everything else: a reward, not an event.
function healShimmer() {
  if (!ready()) return;
  var t = now() + 0.02;
  [[2093.00, 0.030], [2637.02, 0.024], [3135.96, 0.016]].forEach(function (s, i) {
    var at = t + i * 0.07;                               // a gentle cascade, not a chord stab
    var up = Math.pow(2, 3.5 / 1200), dn = 1 / up;       // ±3.5 cents — the shimmer's slow beat
    tone("sine", s[0] * up, at, s[1] * 0.5, 0.08, 0.60); // soft rise, 600 ms fade
    tone("sine", s[0] * dn, at, s[1] * 0.5, 0.08, 0.60);
  });
}

// cellWake: one-shot warm chime — two sines a fifth apart (F4/C5), ~0.4 s, gentle attack.
function cellWake() {
  if (!ready()) return;
  var t = now() + 0.01;
  tone("sine", 349.23, t, 0.16, 0.05, 0.30);
  tone("sine", 523.25, t + 0.02, 0.12, 0.06, 0.30);
}

// passed: small resolved motif — three marimba-like notes (G4 C5 E5, sine body + triangle touch + fast decay) across ~0.9 s.
function passed() {
  if (!ready()) return;
  var t = now() + 0.02;
  [392.00, 523.25, 659.26].forEach(function (f, i) {
    var at = t + i * 0.28;
    tone("sine", f, at, 0.20, 0.008, 0.38);             // the marimba body
    tone("triangle", f * 2, at, 0.045, 0.008, 0.25);    // a touch of triangle
    tone("sine", f * 4, at, 0.03, 0.004, 0.10);         // the strike partial
  });
}

// saved: a single soft confirmation blip.
function saved() {
  if (!ready()) return;
  var t = now() + 0.01;
  tone("sine", 587.33, t, 0.14, 0.012, 0.16);           // D5, quick and gentle
  tone("sine", 1174.66, t, 0.03, 0.008, 0.07);          // faint overtone for definition
}

window.ChimeraSound = {
  init: init,
  ambient: ambient,
  press: press,
  pressEnd: pressEnd,
  wakeWhoosh: wakeWhoosh,
  healShimmer: healShimmer,
  cellWake: cellWake,
  passed: passed,
  saved: saved
};

})();
