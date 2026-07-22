"""Orbitable 3D dev viewer (the development surface, done in real 3D this time).

The wind demo's HTML backend drew a flat side elevation — legible, but still 2D.
This one is a genuine perspective 3D view you can ORBIT (drag) around, with a
DEPTH dial that runs the flat 2D picture through the construction algorithm
(Construction/lift.py) and fills in the third dimension in front of you:

    depth = 0   ->   the flat 2D picture (a card; edge-on it nearly vanishes)
    depth = 1   ->   the full 3D volume (branches fanned around the trunk)

The JS lift() below MIRRORS Construction/lift.py — same golden-angle rule, so
this viewer and the ParticleEngine renderer construct the same geometry.
"""
from __future__ import annotations
import json


def _round(o, nd=2):
    if isinstance(o, float):
        return round(o, nd)
    if isinstance(o, list):
        return [_round(x, nd) for x in o]
    if isinstance(o, dict):
        return {k: _round(v, nd) for k, v in o.items()}
    return o


def payload(flat_trees, width=680, height=560):
    """flat_trees: list of (flat_dict, origin_tuple).  The FLAT 2D pictures — the
    viewer lifts them to 3D itself, so the depth dial is live."""
    return {
        "trees": [{"origin": _round(list(o)), "flat": _round(fl)} for fl, o in flat_trees],
        "view": {"w": width, "h": height},
    }


def build_fragment(pl: dict) -> str:
    return _FRAGMENT.replace("/*__PAYLOAD__*/", json.dumps(pl))


def write_page(path: str, pl: dict) -> str:
    frag = build_fragment(pl)
    page = ("<!doctype html><html><head><meta charset='utf-8'>"
            "<title>Construction — 2D picture lifted to 3D</title></head>"
            "<body style='margin:0;background:#0d1117'>" + frag + "</body></html>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    return path


_FRAGMENT = r"""
<style>
  .vwrap{font-family:system-ui,sans-serif;color:#c9d1d9;max-width:720px;margin:0 auto;padding:8px}
  .vwrap canvas{width:100%;height:auto;border-radius:10px;display:block;background:#0e1526;cursor:grab;touch-action:none}
  .vwrap canvas:active{cursor:grabbing}
  .vbar{display:flex;align-items:center;gap:12px;margin-top:12px}
  .vbar input{flex:1;accent-color:#5aa9e6}
  .vbar .lbl{font-weight:600;font-size:13px;letter-spacing:.06em}
  .vread{margin-top:8px;font:12px/1.5 ui-monospace,monospace;color:#8b949e;white-space:pre-wrap}
  .vtitle{font-size:13px;color:#8b949e;margin:2px 0 10px}
</style>
<div class="vwrap">
  <div class="vtitle">Drag to orbit. The DEPTH dial runs the flat 2D picture through the construction algorithm — the third dimension is filled in, not recovered.</div>
  <canvas id="v3d"></canvas>
  <div class="vbar">
    <span class="lbl">FLAT&nbsp;2D</span>
    <input id="depth" type="range" min="0" max="1" step="0.001" value="0">
    <span class="lbl">3D&nbsp;VOLUME</span>
  </div>
  <div class="vread" id="vread"></div>
</div>
<script>
(function(){
  const PL = /*__PAYLOAD__*/;
  const W = PL.view.w, H = PL.view.h;
  const cvs = document.getElementById('v3d'); cvs.width = W; cvs.height = H;
  const ctx = cvs.getContext('2d');
  const depth = document.getElementById('depth');
  const vread = document.getElementById('vread');

  const GOLDEN = Math.PI*(3-Math.sqrt(5));
  // ── lift() mirror of Construction/lift.py ─────────────────────────────────
  function lift(f, amount, start, pazi){
    const azi = pazi + f.azi, phi = azi*amount;
    const hx = f.dir2[0], dz = f.dir2[2];
    let d = [hx*Math.cos(phi), hx*Math.sin(phi), dz];
    const m = Math.hypot(d[0],d[1],d[2])||1e-9; d = [d[0]/m,d[1]/m,d[2]/m];
    const s = start || f.start2.slice();
    const L = f.len, e = [s[0]+d[0]*L, s[1]+d[1]*L, s[2]+d[2]*L];
    return {start:s, end:e, radius:f.radius, depth:f.depth, is_leaf:f.is_leaf, phase:f.azi,
            children:f.children.map(c=>lift(c, amount, e, azi))};
  }
  // ── tiny vec + orbit camera (z-up world) ──────────────────────────────────
  const sub=(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]], dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
  const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
  const norm=v=>{const m=Math.hypot(v[0],v[1],v[2])||1e-9; return [v[0]/m,v[1]/m,v[2]/m];};
  const TARGET=[0,0,30], R=560; let yaw=-Math.PI/2, pitch=0.16, spin=true;
  function project(p, C, B, focal){
    const rel=sub(p,C), zc=dot(rel,B.f); if (zc<=1) return null;
    return [W/2 + focal*dot(rel,B.r)/zc, H/2 - focal*dot(rel,B.u)/zc, zc];
  }
  function prng(seed){ let a=(seed*104729)>>>0; return ()=>{a+=0x6D2B79F5;let t=a;
    t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return((t^t>>>14)>>>0)/4294967296;};}

  function draw(){
    const amount=parseFloat(depth.value);
    // sky
    const g=ctx.createLinearGradient(0,0,0,H);
    g.addColorStop(0,'#132038'); g.addColorStop(1,'#25405f');
    ctx.fillStyle=g; ctx.fillRect(0,0,W,H);

    const C=[TARGET[0]+R*Math.cos(pitch)*Math.cos(yaw), TARGET[1]+R*Math.cos(pitch)*Math.sin(yaw), TARGET[2]+R*Math.sin(pitch)];
    const f=norm(sub(TARGET,C)), r=norm(cross(f,[0,0,1])), u=cross(r,f), B={f,r,u};
    const focal=0.95*Math.min(W,H);

    const prims=[]; let ymax=0;
    for(const tr of PL.trees){
      const o=tr.origin, lifted=lift(tr.flat, amount, null, 0);
      (function walk(n){
        ymax=Math.max(ymax, Math.abs(n.end[1]));
        const a=project([n.start[0]+o[0],n.start[1]+o[1],n.start[2]+o[2]],C,B,focal);
        const b=project([n.end[0]+o[0],n.end[1]+o[1],n.end[2]+o[2]],C,B,focal);
        if(a&&b){ const sh=90+n.depth*11;
          prims.push({k:'l', a,b, d:(a[2]+b[2])/2, w:n.radius, col:`rgb(${sh+24},${sh-2},${(sh*0.6)|0})`}); }
        if(n.is_leaf){
          const rnd=prng((n.phase*1000)|0);
          for(let i=0;i<14;i++){
            const off=[(rnd()-0.5)*34,(rnd()-0.5)*34,(rnd()-0.5)*28];
            const p=project([n.end[0]+o[0]+off[0],n.end[1]+o[1]+off[1],n.end[2]+o[2]+off[2]],C,B,focal);
            if(p){ const gg=120+(rnd()*90|0);
              prims.push({k:'p', p, d:p[2], s:2.4+rnd()*3, col:`rgb(${40+(rnd()*30|0)},${gg},${50+(rnd()*25|0)})`}); }
          }
        }
        for(const c of n.children) walk(c);
      })(lifted);
    }
    prims.sort((x,y)=>y.d-x.d);   // painter's: far first
    for(const p of prims){
      if(p.k==='l'){ ctx.strokeStyle=p.col; ctx.lineCap='round';
        ctx.lineWidth=Math.max(1, p.w*focal/p.d*0.9);
        ctx.beginPath(); ctx.moveTo(p.a[0],p.a[1]); ctx.lineTo(p.b[0],p.b[1]); ctx.stroke();
      } else { ctx.globalAlpha=0.72; ctx.fillStyle=p.col;
        ctx.beginPath(); ctx.arc(p.p[0],p.p[1], Math.max(1.2, p.s*focal/p.d), 0, 6.28); ctx.fill();
        ctx.globalAlpha=1;
      }
    }
    vread.textContent = `depth = ${amount.toFixed(3)}   ->   construction fills Y up to ${ymax.toFixed(0)} units   ·   drag to orbit (yaw ${(yaw*57.3).toFixed(0)}°)`;
  }

  // orbit interaction
  let drag=false, px=0, py=0;
  cvs.addEventListener('pointerdown', e=>{drag=true; spin=false; px=e.clientX; py=e.clientY; cvs.setPointerCapture(e.pointerId);});
  cvs.addEventListener('pointermove', e=>{ if(!drag) return;
    yaw += (e.clientX-px)*0.01; pitch = Math.max(-0.2, Math.min(1.2, pitch + (e.clientY-py)*0.006));
    px=e.clientX; py=e.clientY; });
  cvs.addEventListener('pointerup', ()=>{drag=false;});
  depth.addEventListener('input', ()=>{});

  function loop(){ if(spin) yaw += 0.004; draw(); requestAnimationFrame(loop); }
  requestAnimationFrame(loop);
})();
</script>
"""
