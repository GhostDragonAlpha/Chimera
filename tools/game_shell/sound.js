/* CHIMERA — tools/game_shell/sound.js
 *
 * All sound for the game page, synthesized at runtime with WebAudio:
 * oscillators, noise buffers, envelopes. NO audio files, NO network,
 * NO external assets — this one file is the entire sound department.
 *
 * Integration:
 *   <script src="sound.js"></script>
 *   PLAY button click : ChimeraSound.init(); ChimeraSound.ambient(true);
 *   touch begins      : ChimeraSound.press(forceN);      (re-call while held to follow the slider)
 *   touch released    : ChimeraSound.pressEnd();
 *   cell wakes        : ChimeraSound.cellWake();
 *   lesson passed     : ChimeraSound.passed();
 *   progress saved    : ChimeraSound.saved();
 *
 * If WebAudio is unavailable, every call feature-detects and no-ops silently.
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
function press(force_n) {
  if (!ready()) return;
  var c = forceCurve(force_n);
  var p = {
    bandHz: 120 + 680 * c,      // brighter skin as force grows, capped low enough to stay soft
    bandQ:  0.8 + 0.8 * c,
    noiseG: 0.015 + 0.075 * c,
    sineHz: 52 + 46 * c,        // the body hum rises slightly under load
    sineG:  0.04 + 0.10 * c,
    busG:   0.5 + 0.5 * c
  };
  if (pressV) {                 // already held: just follow the new force, never stack voices
    var t2 = now(), k = 0.08;
    pressV.band.frequency.setTargetAtTime(p.bandHz, t2, k);
    pressV.band.Q.setTargetAtTime(p.bandQ, t2, k);
    pressV.ng.gain.setTargetAtTime(p.noiseG, t2, k);
    pressV.osc.frequency.setTargetAtTime(p.sineHz, t2, k);
    pressV.og.gain.setTargetAtTime(p.sineG, t2, k);
    pressV.bus.gain.setTargetAtTime(p.busG, t2, k);
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
  pressV = { bus: bus, ns: ns, band: band, ng: ng, osc: osc, og: og };
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
  cellWake: cellWake,
  passed: passed,
  saved: saved
};

})();
