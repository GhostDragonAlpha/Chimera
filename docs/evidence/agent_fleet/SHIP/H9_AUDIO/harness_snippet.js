  window.__SNDLOG = [];
  window.__SNDSTATE = { pressVActive: false, region: null };
  function __safe(v) {
    if (v === undefined) return 'undefined';
    if (v === null) return null;
    if (typeof v === 'number') return Math.round(v * 1000) / 1000;
    if (typeof v === 'string') return v;
    if (v && typeof v.length === 'number')
      return Array.prototype.slice.call(v, 0, 3)
        .map(function (x) { return Math.round(Number(x) * 1000) / 1000; });
    return String(v);
  }
  function __wrap(name, fn) {
    return function () {
      var args = Array.prototype.slice.call(arguments), out;
      try { out = fn.apply(null, args); }
      finally {
        var rec = { m: name, t: Date.now(),
                    ctx: ctx ? ctx.state : 'no-ctx',
                    args: args.map(__safe) };
        if (name === 'press') {
          rec.voiceActiveAfter = !!pressV;
          rec.heldRegion = pressV && pressV.region ? pressV.region.name : null;
          window.__SNDSTATE.pressVActive = !!pressV;
          window.__SNDSTATE.region = rec.heldRegion;
        }
        if (name === 'pressEnd') {
          rec.voiceActiveAfter = !!pressV;
          window.__SNDSTATE.pressVActive = !!pressV;
        }
        window.__SNDLOG.push(rec);
      }
      return out;
    };
  }
  window.ChimeraSound = {
    init: __wrap('init', init),
    ambient: __wrap('ambient', ambient),
    press: __wrap('press', press),
    pressEnd: __wrap('pressEnd', pressEnd),
    wakeWhoosh: __wrap('wakeWhoosh', wakeWhoosh),
    healShimmer: __wrap('healShimmer', healShimmer),
    cellWake: __wrap('cellWake', cellWake),
    passed: __wrap('passed', passed),
    saved: __wrap('saved', saved)
  };
