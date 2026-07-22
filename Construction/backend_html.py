"""HTML backend (the development surface).

Emits a self-contained HTML canvas that renders the SAME scene model as the 3D
backend, with a live CALM<->GALE dial.  This is the AI-legible surface: fast to
emit, render, read back, and adjust (DESIGN §6).

The JS pose()/fill() below MIRROR Construction/tree.py and Construction/scene.py.
They are duplicated across the language boundary (Python vs JS) — the one place
the two backends can silently drift.  Guarded at the anchors: at t=0 and t=1 the
fill reduces to the exported anchor params verbatim, which both sides share
(DESIGN §6, §10).
"""
from __future__ import annotations
import json


def _bounds(trees):
    """World x/z extent of the rest skeletons across all placed trees, padded to
    leave room for the downwind lean (+X) and canopy sway (+Z)."""
    xs, zs = [], []

    def walk(n, ox, oz):
        s, d, L = n["start"], n["dir"], n["length"]
        e = (s[0] + d[0] * L, s[1] + d[1] * L, s[2] + d[2] * L)
        xs.append(s[0] + ox); xs.append(e[0] + ox)
        zs.append(s[2] + oz); zs.append(e[2] + oz)
        for c in n["children"]:
            walk(c, ox, oz)

    for sk, origin in trees:
        walk(sk, origin[0], origin[2])
    xmin, xmax = min(xs), max(xs)
    zmin, zmax = min(zs), max(zs)
    pad_x = (xmax - xmin) * 0.35 + 80
    pad_z = (zmax - zmin) * 0.25 + 80
    return xmin - pad_x, xmax + pad_x, zmin - 40, zmax + pad_z


def _round(o, nd=2):
    """Trim float precision so the exported HTML stays small (2dp is well under
    a pixel at these scales)."""
    if isinstance(o, float):
        return round(o, nd)
    if isinstance(o, list):
        return [_round(x, nd) for x in o]
    if isinstance(o, dict):
        return {k: _round(v, nd) for k, v in o.items()}
    return o


def payload(scene_trees, anchors_lo, anchors_hi, max_depth, width=680, height=560):
    """Build the JSON-serializable payload the HTML consumes.

    scene_trees: list of (skeleton_dict, origin_tuple)."""
    xmin, xmax, zmin, zmax = _bounds(scene_trees)
    return {
        "anchors": {"lo": anchors_lo, "hi": anchors_hi},
        "max_depth": max_depth,
        "trees": [{"origin": _round(list(o)), "skeleton": _round(sk)} for sk, o in scene_trees],
        "view": {"xmin": round(xmin, 1), "xmax": round(xmax, 1),
                 "zmin": round(zmin, 1), "zmax": round(zmax, 1),
                 "w": width, "h": height},
    }


def build_fragment(pl: dict) -> str:
    """Return the HTML body (canvas + dial + script) for show_widget or a page."""
    data = json.dumps(pl)
    return _FRAGMENT.replace("/*__PAYLOAD__*/", data)


def write_page(path: str, pl: dict) -> str:
    """Write a standalone .html file (the DOM run-mode artifact)."""
    frag = build_fragment(pl)
    page = ("<!doctype html><html><head><meta charset='utf-8'>"
            "<title>Construction — tree in the wind</title></head>"
            "<body style='margin:0;background:#0d1117'>" + frag + "</body></html>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    return path


# The fragment.  /*__PAYLOAD__*/ is replaced with the scene JSON.
_FRAGMENT = r"""
<style>
  .cwrap{font-family:system-ui,sans-serif;color:#c9d1d9;max-width:720px;margin:0 auto;padding:8px}
  .cwrap canvas{width:100%;height:auto;border-radius:10px;display:block;background:#87b8e0}
  .cbar{display:flex;align-items:center;gap:12px;margin-top:12px}
  .cbar input{flex:1;accent-color:#5aa9e6}
  .cbar .lbl{font-weight:600;font-size:13px;letter-spacing:.08em}
  .cread{margin-top:8px;font:12px/1.5 ui-monospace,monospace;color:#8b949e;white-space:pre}
  .ctitle{font-size:13px;color:#8b949e;margin:2px 0 10px}
</style>
<div class="cwrap">
  <div class="ctitle">One scene model · one dial · the difference between CALM and GALE <b>is</b> the axis.</div>
  <canvas id="cvs"></canvas>
  <div class="cbar">
    <span class="lbl">CALM</span>
    <input id="dial" type="range" min="0" max="1" step="0.001" value="0">
    <span class="lbl">GALE</span>
  </div>
  <div class="cread" id="read"></div>
</div>
<script>
(function(){
  const PL = /*__PAYLOAD__*/;
  const V = PL.view, MAXD = PL.max_depth;
  const cvs = document.getElementById('cvs');
  cvs.width = V.w; cvs.height = V.h;
  const ctx = cvs.getContext('2d');
  const dial = document.getElementById('dial');
  const read = document.getElementById('read');

  // ── scene.Axis.fill mirror ────────────────────────────────────────────────
  function fill(t){
    const lo = PL.anchors.lo, hi = PL.anchors.hi, o = {};
    for (const k in lo) o[k] = lo[k]*(1-t) + (k in hi ? hi[k] : 0)*t;
    for (const k in hi) if (!(k in o)) o[k] = (k in lo ? lo[k] : 0)*(1-t) + hi[k]*t;
    return o;
  }
  // ── tree.pose mirror ──────────────────────────────────────────────────────
  function rotY(v, a){ const c=Math.cos(a), s=Math.sin(a);
    return [c*v[0]+s*v[2], v[1], -s*v[0]+c*v[2]]; }
  function pose(n, w, time, pbend, pend){
    const df = n.depth/Math.max(1,MAXD);
    const gust = 0.5 + 0.5*Math.sin(2*Math.PI*(w.gust_hz||0.6)*time + n.phase);
    const local = (w.lean||0)*0.16*(0.4+df) + (w.sway||0)*gust*0.20*(0.3+df);
    const total = pbend + local;
    const start = pend || n.start.slice();
    const d = rotY(n.dir, total);
    const L = n.length;
    const end = [start[0]+d[0]*L, start[1]+d[1]*L, start[2]+d[2]*L];
    return {start:start, end:end, radius:n.radius, depth:n.depth,
            is_leaf:n.is_leaf, phase:n.phase,
            children:n.children.map(c=>pose(c, w, time, total, end))};
  }
  // deterministic per-leaf offsets (seeded from phase) so leaves don't reshuffle
  function prng(seed){ let a = (seed*104729)>>>0; return function(){
    a += 0x6D2B79F5; let t = a; t = Math.imul(t ^ t>>>15, t|1);
    t ^= t + Math.imul(t ^ t>>>7, t|61); return ((t ^ t>>>14)>>>0)/4294967296; }; }

  const sx = () => Math.min((V.w)/(V.xmax-V.xmin), (V.h)/(V.zmax-V.zmin));
  function proj(x, z){ const s = sx();
    return [ (x - V.xmin)*s, V.h - (z - V.zmin)*s ]; }

  function lerp(a,b,t){ return a+(b-a)*t; }
  function draw(time){
    const t = parseFloat(dial.value), w = fill(t);
    // sky greys with wind (same knob as the 3D backend)
    const sky = w.sky||0;
    const g = ctx.createLinearGradient(0,0,0,V.h);
    g.addColorStop(0, `rgb(${lerp(135,150,sky)|0},${lerp(184,150,sky)|0},${lerp(224,158,sky)|0})`);
    g.addColorStop(1, `rgb(${lerp(198,170,sky)|0},${lerp(224,175,sky)|0},${lerp(235,180,sky)|0})`);
    ctx.fillStyle = g; ctx.fillRect(0,0,V.w,V.h);
    // ground
    const gy = proj(0, V.zmin+40)[1];
    ctx.fillStyle = `rgb(${lerp(90,74,sky)|0},${lerp(110,88,sky)|0},${lerp(70,60,sky)|0})`;
    ctx.fillRect(0, gy, V.w, V.h-gy);

    const s = sx();
    for (const tr of PL.trees){
      const ox = tr.origin[0], oz = tr.origin[2];
      const posed = pose(tr.skeleton, w, time, 0, null);
      // branches
      (function branch(n){
        const [x0,y0] = proj(n.start[0]+ox, n.start[2]+oz);
        const [x1,y1] = proj(n.end[0]+ox,   n.end[2]+oz);
        ctx.lineWidth = Math.max(1, n.radius*s*0.9);
        ctx.lineCap = 'round';
        const sh = 60 + n.depth*8;
        ctx.strokeStyle = `rgb(${sh+18},${sh-6},${(sh*0.5)|0})`;
        ctx.beginPath(); ctx.moveTo(x0,y0); ctx.lineTo(x1,y1); ctx.stroke();
        if (n.is_leaf){
          const r = prng((n.phase*1000)|0);
          ctx.globalAlpha = 0.55;
          for (let i=0;i<16;i++){
            const dx = (r()-0.5)*36, dz = (r()-0.5)*30;
            const fj = (w.flutter||0)*8*Math.sin(time*6 + i + n.phase);
            const [lx,ly] = proj(n.end[0]+ox+dx+fj, n.end[2]+oz+dz);
            const gg = 90 + (r()*90|0);
            ctx.fillStyle = `rgb(${30+(r()*30|0)},${gg},${40+(r()*25|0)})`;
            ctx.beginPath(); ctx.arc(lx, ly, 3+r()*4, 0, 6.28); ctx.fill();
          }
          ctx.globalAlpha = 1;
        }
        for (const c of n.children) branch(c);
      })(posed);
    }
    read.textContent =
      `dial t = ${t.toFixed(3)}   ->   ` +
      `lean ${(w.lean||0).toFixed(2)}  sway ${(w.sway||0).toFixed(2)}  ` +
      `flutter ${(w.flutter||0).toFixed(2)}  gust ${(w.gust_hz||0).toFixed(2)}Hz  sky ${(w.sky||0).toFixed(2)}`;
  }

  let t0 = null;
  function loop(ts){
    if (t0===null) t0 = ts;
    draw((ts - t0)/1000);
    requestAnimationFrame(loop);
  }
  dial.addEventListener('input', ()=>{});   // draw() reads dial each frame
  requestAnimationFrame(loop);
})();
</script>
"""
