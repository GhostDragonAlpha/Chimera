"""Noun + Verb viewer: a constructed 3D noun, given a verb, composed.

The golden noun (Construction/lift, the rule that won on the evidence) is fixed in
3D; the WIND verb (Construction/tree.pose, mirrored in JS below) bends it every
frame.  Drag to orbit (see it is genuinely 3D); the dial drives the verb
(CALM<->GALE).  This is blow(construct(picture)) — noun and verb put together like
normal programming.
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


def payload(nouns, calm, gale, max_depth, width=680, height=560):
    """nouns: list of (noun_skeleton_3d, origin).  The noun is already constructed
    (golden lift); the viewer only applies the verb."""
    return {
        "nouns": [{"origin": _round(list(o)), "noun": _round(nd)} for nd, o in nouns],
        "anchors": {"lo": calm, "hi": gale},
        "max_depth": max_depth,
        "view": {"w": width, "h": height},
    }


def build_fragment(pl: dict) -> str:
    return _FRAGMENT.replace("/*__PAYLOAD__*/", json.dumps(pl))


def write_page(path: str, pl: dict) -> str:
    frag = build_fragment(pl)
    page = ("<!doctype html><html><head><meta charset='utf-8'>"
            "<title>Construction — noun + verb</title></head>"
            "<body style='margin:0;background:#0d1117'>" + frag + "</body></html>")
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    return path


_FRAGMENT = r"""
<style>
  .nvwrap{font-family:system-ui,sans-serif;color:#c9d1d9;max-width:720px;margin:0 auto;padding:8px}
  .nvwrap canvas{width:100%;height:auto;border-radius:10px;display:block;background:#0e1526;cursor:grab;touch-action:none}
  .nvwrap canvas:active{cursor:grabbing}
  .nvbar{display:flex;align-items:center;gap:12px;margin-top:12px}
  .nvbar input{flex:1;accent-color:#5aa9e6}
  .nvbar .lbl{font-weight:600;font-size:13px;letter-spacing:.06em}
  .nvread{margin-top:8px;font:12px/1.5 ui-monospace,monospace;color:#8b949e;white-space:pre-wrap}
  .nvtitle{font-size:13px;color:#8b949e;margin:2px 0 10px}
</style>
<div class="nvwrap">
  <div class="nvtitle">The golden NOUN, given the wind VERB. Drag to orbit (it is 3D); the dial drives the verb.</div>
  <canvas id="nv"></canvas>
  <div class="nvbar">
    <span class="lbl">CALM</span>
    <input id="wind" type="range" min="0" max="1" step="0.001" value="0">
    <span class="lbl">GALE</span>
  </div>
  <div class="nvread" id="nvread"></div>
</div>
<script>
(function(){
  const PL = /*__PAYLOAD__*/;
  const W = PL.view.w, H = PL.view.h, MAXD = PL.max_depth;
  const cvs = document.getElementById('nv'); cvs.width = W; cvs.height = H;
  const ctx = cvs.getContext('2d');
  const wind = document.getElementById('wind');
  const nvread = document.getElementById('nvread');

  // ── scene.Axis.fill mirror (the verb's dial) ──────────────────────────────
  function fill(t){ const lo=PL.anchors.lo, hi=PL.anchors.hi, o={};
    for(const k in lo) o[k]=lo[k]*(1-t)+(k in hi?hi[k]:0)*t; return o; }
  // ── tree.pose mirror (the WIND verb) ──────────────────────────────────────
  function rotY(v,a){ const c=Math.cos(a),s=Math.sin(a);
    return [c*v[0]+s*v[2], v[1], -s*v[0]+c*v[2]]; }
  function pose(n, w, time, pbend, pend){
    const df=n.depth/Math.max(1,MAXD);
    const gust=0.5+0.5*Math.sin(2*Math.PI*(w.gust_hz||0.6)*time + n.phase);
    const local=(w.lean||0)*0.16*(0.4+df)+(w.sway||0)*gust*0.20*(0.3+df);
    const total=pbend+local;
    const start=pend||n.start.slice();
    const d=rotY(n.dir,total), L=n.length;
    const end=[start[0]+d[0]*L, start[1]+d[1]*L, start[2]+d[2]*L];
    return {start,end,radius:n.radius,depth:n.depth,is_leaf:n.is_leaf,phase:n.phase,
            children:n.children.map(c=>pose(c,w,time,total,end))};
  }
  // ── orbit camera (z-up) ───────────────────────────────────────────────────
  const sub=(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]], dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
  const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
  const norm=v=>{const m=Math.hypot(v[0],v[1],v[2])||1e-9; return [v[0]/m,v[1]/m,v[2]/m];};
  const TARGET=[0,0,30], R=560; let yaw=-Math.PI/2, pitch=0.16, spin=true;
  function project(p,C,B,focal){ const rel=sub(p,C), zc=dot(rel,B.f); if(zc<=1) return null;
    return [W/2+focal*dot(rel,B.r)/zc, H/2-focal*dot(rel,B.u)/zc, zc]; }
  function prng(seed){ let a=(seed*104729)>>>0; return ()=>{a+=0x6D2B79F5;let t=a;
    t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return((t^t>>>14)>>>0)/4294967296;};}

  function draw(time){
    const t=parseFloat(wind.value), w=fill(t), sky=w.sky||0, flut=w.flutter||0;
    const g=ctx.createLinearGradient(0,0,0,H);
    g.addColorStop(0,`rgb(${(19+22*sky)|0},${(32+16*sky)|0},${(56-6*sky)|0})`);
    g.addColorStop(1,`rgb(${(37+10*sky)|0},${(64-4*sky)|0},${(95-24*sky)|0})`);
    ctx.fillStyle=g; ctx.fillRect(0,0,W,H);

    const C=[TARGET[0]+R*Math.cos(pitch)*Math.cos(yaw), TARGET[1]+R*Math.cos(pitch)*Math.sin(yaw), TARGET[2]+R*Math.sin(pitch)];
    const f=norm(sub(TARGET,C)), r=norm(cross(f,[0,0,1])), u=cross(r,f), B={f,r,u};
    const focal=0.95*Math.min(W,H);

    const prims=[];
    for(const it of PL.nouns){
      const o=it.origin, blown=pose(it.noun, w, time, 0, null);
      (function walk(n){
        const a=project([n.start[0]+o[0],n.start[1]+o[1],n.start[2]+o[2]],C,B,focal);
        const b=project([n.end[0]+o[0],n.end[1]+o[1],n.end[2]+o[2]],C,B,focal);
        if(a&&b){ const sh=90+n.depth*11;
          prims.push({k:'l',a,b,d:(a[2]+b[2])/2,w:n.radius,col:`rgb(${sh+24},${sh-2},${(sh*0.6)|0})`}); }
        if(n.is_leaf){ const rnd=prng((n.phase*1000)|0);
          for(let i=0;i<14;i++){
            const fj=flut*10*Math.sin(time*6+i+n.phase);
            const off=[(rnd()-0.5)*34+fj,(rnd()-0.5)*34,(rnd()-0.5)*28];
            const p=project([n.end[0]+o[0]+off[0],n.end[1]+o[1]+off[1],n.end[2]+o[2]+off[2]],C,B,focal);
            if(p){ const gg=120+(rnd()*90|0);
              prims.push({k:'p',p,d:p[2],s:2.4+rnd()*3,col:`rgb(${40+(rnd()*30|0)},${gg},${50+(rnd()*25|0)})`}); }
          }
        }
        for(const c of n.children) walk(c);
      })(blown);
    }
    prims.sort((x,y)=>y.d-x.d);
    for(const p of prims){
      if(p.k==='l'){ ctx.strokeStyle=p.col; ctx.lineCap='round';
        ctx.lineWidth=Math.max(1,p.w*focal/p.d*0.9);
        ctx.beginPath(); ctx.moveTo(p.a[0],p.a[1]); ctx.lineTo(p.b[0],p.b[1]); ctx.stroke();
      } else { ctx.globalAlpha=0.72; ctx.fillStyle=p.col;
        ctx.beginPath(); ctx.arc(p.p[0],p.p[1],Math.max(1.2,p.s*focal/p.d),0,6.28); ctx.fill(); ctx.globalAlpha=1; }
    }
    nvread.textContent = `noun = golden construction   ·   verb = wind ${t.toFixed(2)} (lean ${(w.lean||0).toFixed(2)} sway ${(w.sway||0).toFixed(2)})   ·   drag to orbit (yaw ${(yaw*57.3).toFixed(0)}°)`;
  }

  let drag=false, px=0, py=0;
  cvs.addEventListener('pointerdown', e=>{drag=true; spin=false; px=e.clientX; py=e.clientY; cvs.setPointerCapture(e.pointerId);});
  cvs.addEventListener('pointermove', e=>{ if(!drag) return;
    yaw += (e.clientX-px)*0.01; pitch=Math.max(-0.2,Math.min(1.2,pitch+(e.clientY-py)*0.006));
    px=e.clientX; py=e.clientY; });
  cvs.addEventListener('pointerup', ()=>{drag=false;});

  let t0=null;
  function loop(ts){ if(t0===null)t0=ts; if(spin) yaw+=0.004; draw((ts-t0)/1000); requestAnimationFrame(loop); }
  requestAnimationFrame(loop);
})();
</script>
"""
