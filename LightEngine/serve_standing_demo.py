"""theStandingHuman DEMO v1+v2 -- the LIVE feed, now with the push verb.

RULE 0 -- STATEMENT (v2, the push): a derived push is a perturbation the
muscle servo measurably RESISTS, and the command channel delivers it
faithfully: a shove whose impulse is the derived STEP THRESHOLD (omega0 *
margin * m at the sternum, over one pendulum timescale) produces the
derived COM velocity change when nothing fights it, and a visibly smaller
excursion when the muscles are on.

PREDICTION (named before the run):
  (a) IMPULSE FIDELITY: muscles cut, then pushed: the COM gains
      |dv| = J/m = 0.5 * omega0 * margin to within 25% (gravity and the
      mid-buckle leak are the only thieves);
  (b) SERVO RESISTANCE: the same push with muscles on vs muscles cut:
      the 500-tick COM-x excursion is SMALLER with muscles on -- any
      positive margin; "indistinguishable" falsifies the servo;
  (c) the flags channel shows [PUSHING] for exactly the derived window.

FALSIFIERS: the push moves nothing (command decoration); muscles-on and
muscles-off excursions are indistinguishable (servo decoration).  Either
fires -> record, don't patch.

v1 membrane (the feed itself) and its verdict: docs/THE_CATEGORIES.md,
STANDING DEMO v1 VERDICT 2026-08-08.

Usage:
    PYTHONPATH=E:/PythonChimera python LightEngine/serve_standing_demo.py
    # then open http://127.0.0.1:8765/   (loopback only, per bind-guard)
"""

from __future__ import annotations

import asyncio
import json
import os
import queue
import struct
import sys
import threading
import time

import numpy as np

from LightEngine.kinematic import build_spec, transforms
from LightEngine.kinematic.dynamics import (
    GRAVITY_MPS2, center_of_mass, init_state, step,
)
from LightEngine.kinematic.muscle_controller import MuscleController
from LightEngine.build_standing_demo import (
    DEMO_SAMPLE_EVERY, _region, load_three_bridged,
)
from LightEngine.demo_kinematic import DT

HOST = "127.0.0.1"   # loopback only -- bind-guard law
PORT = 8765

CMDQ: queue.Queue[str] = queue.Queue()
# A live feed carries the NEWEST state, never a backlog: maxsize=1 and the
# producer evicts the stale frame.  Measured 2026-08-08: a 256-deep queue
# let a faster (muscles-cut) run put the viewer ~800 ticks behind the sim,
# so a "push at tick 96" landed at tick 895 -- into the collapsed frame.
FRAMEQ: queue.Queue[bytes] = queue.Queue(maxsize=1)
CLIENTS: set = set()


# ---------------------------------------------------------------------------
# Sim thread: the battery's physics, stepped forever, framed at 8-tick cadence
# ---------------------------------------------------------------------------

def _endpoints(spec, state):
    names = list(state["link_names"])
    d = np.zeros((len(names), 6), dtype=np.float64)
    for i, name in enumerate(names):
        link = spec["links"][name]
        com_off = np.asarray(link["com_offset_m"], dtype=np.float64)
        d_tip = link["R_world_to_local"] @ (
            np.asarray(link["dist_m"]) - np.asarray(link["prox_m"]))
        R = transforms.to_matrix(state["quat"][i])
        d[i, :3] = state["pos"][i] + R @ (-com_off)
        d[i, 3:] = state["pos"][i] + R @ (d_tip - com_off)
    return d


def _push_force(spec, state, factor: float):
    """The derived push (Lane D6 / DEMO v2): (force vector, ticks) or None.

    The STEP THRESHOLD of balance biomechanics, derived from the live support
    geometry at push time -- no number is chosen:
      omega0 = sqrt(g / h_com)     inverted-pendulum eigenfrequency
      margin = max(polygon x) - com_x   forward margin to the toe edge
      v*     = omega0 * margin     COM velocity that carries the pendulum
                                   to the polygon edge (the step threshold)
      J      = factor * m * v*     0.5 = sub-threshold, 2.0 = super-threshold
      dt_push = 1 / omega0         the push acts over ONE natural timescale
                                   of the body
      F      = J / dt_push, +x on the STERNUM

    DOMAIN: the pendulum model exists only for the STANDING frame.  Outside
    it (COM at/below the support plane, or COM past the toe edge) the
    derivation has no meaning -- measured 2026-08-08: a push issued into the
    collapsed frame read h = clamp(1e-6) -> omega0 = 3 130 rad/s -> a
    17.7 MN lie.  The membrane REFUSES; a refused push is honest data.
    """
    m = float(np.sum(state["mass"]))
    com = center_of_mass(spec, state)
    h = float(com[2])
    poly_x = []
    for rec in state["contact_records"]:
        # G0: world-floor endpoints (side "W") are not the support margin.
        if rec.get("side") == "W":
            continue
        li = rec["link_idx"]
        R = transforms.to_matrix(state["quat"][li])
        p = state["pos"][li] + R @ rec["offset_local"]
        poly_x.append(float(p[0]))
    margin = max(poly_x) - float(com[0])
    if h <= 0.0 or margin <= 0.0:
        return None
    omega0 = (GRAVITY_MPS2 / h) ** 0.5
    v_star = omega0 * margin
    dt_push = 1.0 / omega0
    ticks = max(1, round(dt_push / DT))
    F = factor * m * v_star / (ticks * DT)
    return np.array([F, 0.0, 0.0], dtype=np.float64), ticks


def sim_loop():
    # G0 WORLD-FLOOR build (2026-08-08): anatomic de Leva masses + a
    # contact endpoint on every link, so cut-muscles crumples ONTO a
    # floor instead of sinking through the world (floorless: head_z
    # -50.8 m @8000, VERDICT 2).  The full ghost-free config comes with
    # it -- that is the config the floor probe measured green under.
    spec = build_spec(1.80, 80.0, mass_model="deleva", floor_links=True)

    def fresh():
        state = init_state(spec)
        state["rotation_locks"] = 2
        state["pos_pass_mode"] = 1
        # v3e battery verdict: the hybrid ground loop (normals in-solve,
        # friction swept) is battery-equivalent-or-better vs the sweep on
        # all six meters -- it is the demo default.  CONTACTS_IN_SOLVE=0
        # opts back out to the pre-v3a sweep path.
        if os.environ.get("CONTACTS_IN_SOLVE", "1") == "1":
            state["contacts_in_solve"] = True
            state["contact_friction"] = 2
        # Spring-paced contact recovery: a sunk point is lifted at one
        # depth per contact-spring period (T = 0.162 s, derived from
        # k_contact), so the pile settles instead of ratcheting into the
        # slab (one-way gate forensic, JOINT_ATLAS.md VERDICT 4).
        state["contact_recovery"] = 3
        # Servo domain refusal: when the COM leaves the foot polygon the
        # standing program terminates (a fallen body is not stand-served
        # -- run-4 diag: the live servo shoved endpoints to -0.359 m).
        state["servo_domain_refusal"] = True
        # MEASURED BILINEAR FLOOR (2026-08-08, runs 17-21 proven): each
        # world-floor endpoint rides a zoned implicit spring-damper row
        # -- pad zone: bias k*d/(dt*k+c) + gamma 1/(dt*(dt*k+c)) on the
        # K diagonal, c = 2*sqrt(m_load*k) with m_load from the previous
        # tick's solved impulse; below the pad: the spring-paced lift.
        # Drop arm green at REST 0.020 J (JOINT_ATLAS run 19).
        state["contact_penalty"] = 2
        state["contact_priority"] = 0  # run 21: gated per-tick below --
        # retention exists to resist MOTOR crush; no live servo, no
        # crush source (always-on reproduced the run-6 tunnel disease).
        state["ext_force"] = np.zeros((len(state["link_names"]), 3),
                                      dtype=np.float64)
        state["ext_torque"] = np.zeros((len(state["link_names"]), 3),
                                       dtype=np.float64)
        return state, MuscleController(spec, state)

    state, ctrl = fresh()
    skull = state["name_to_idx"]["skull"]
    sternum = state["name_to_idx"]["sternum"]
    tick = 0
    n_links = len(state["link_names"])
    push_remaining = 0
    t0 = time.time()
    while True:
        # commands from the page
        try:
            while True:
                cmd = CMDQ.get_nowait()
                if cmd == "cut":
                    ctrl.enabled = False
                    print(f"[sim] muscles CUT at tick {tick}", flush=True)
                elif cmd == "reset":
                    state, ctrl = fresh()
                    skull = state["name_to_idx"]["skull"]
                    sternum = state["name_to_idx"]["sternum"]
                    tick = 0
                    push_remaining = 0
                    t0 = time.time()
                    print("[sim] reset", flush=True)
                elif cmd in ("push", "shove"):
                    factor = 0.5 if cmd == "push" else 2.0
                    derived = _push_force(spec, state, factor)
                    if derived is None:
                        com_now = center_of_mass(spec, state)
                        print(f"[sim] {cmd.upper()} REFUSED at tick {tick}: "
                              f"frame not standing (com_z={com_now[2]:.3f} m)",
                              flush=True)
                    else:
                        F, ticks = derived
                        state["ext_force"][:] = 0.0
                        state["ext_force"][sternum] = F
                        push_remaining = ticks
                        print(f"[sim] {cmd.upper()} at tick {tick}: "
                              f"|F|={F[0]:.1f} N for {ticks} ticks "
                              f"(J={F[0]*ticks*DT:.1f} N s)", flush=True)
        except queue.Empty:
            pass

        ctrl.apply(state)
        state["contact_priority"] = 1 if ctrl.enabled else 0  # run 21 gate
        step(spec, state, DT, n_proj_iters=20)
        # The push window counts DOWN AFTER the step that used the force --
        # measured 2026-08-08: decrementing before the step zeroed a 1-tick
        # push before the solver ever saw it (the whole push was a no-op).
        if push_remaining > 0:
            push_remaining -= 1
            if push_remaining == 0:
                state["ext_force"][:] = 0.0
        if tick % DEMO_SAMPLE_EVERY == 0:
            seg = _endpoints(spec, state)
            com = center_of_mass(spec, state)
            head_z = float(state["pos"][skull][2])
            flags = (1 if ctrl.enabled else 0) | (2 if push_remaining else 0)
            payload = struct.pack("<IIf", tick, flags, head_z) \
                + seg.astype("<f4").tobytes() \
                + np.asarray(com, dtype="<f4").tobytes()
            try:
                FRAMEQ.put_nowait(payload)
            except queue.Full:
                try:
                    FRAMEQ.get_nowait()   # evict the stale frame
                except queue.Empty:
                    pass
                try:
                    FRAMEQ.put_nowait(payload)
                except queue.Full:
                    pass
        tick += 1
        if tick % 2000 == 0:
            rate = tick / (time.time() - t0)
            print(f"[sim] tick {tick}  ({rate:.0f} ticks/s)", flush=True)


# ---------------------------------------------------------------------------
# The live page (v0 player rendering, live feed instead of baked frames)
# ---------------------------------------------------------------------------

_LIVE_JS = r"""
const ws = new WebSocket(`ws://${location.host}`);
ws.binaryType = 'arraybuffer';
let META = null, N_LINKS = 0;
let prevF = null, curF = null, curAt = 0, prevAt = 0;  // frame + arrival ms
let tpsEMA = 0, lastTick = 0, lastTickAt = 0;

// ---- scene (identical idiom to the v0 player) ------------------------------
const renderer = new WebGLRenderer({ antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(window.innerWidth, window.innerHeight);
document.getElementById('view').appendChild(renderer.domElement);
const scene = new Scene();
scene.background = new Color(0x101418);
const camera = new PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.01, 200);
camera.up.set(0, 0, 1);
scene.add(new HemisphereLight(0xbfd4ff, 0x30281e, 1.1));
const sun = new DirectionalLight(0xffffff, 1.4);
sun.position.set(3, -4, 6);
scene.add(sun);
const ground = new Mesh(
  new PlaneGeometry(60, 60),
  new MeshBasicMaterial({ color: 0x2a2f36, transparent: true, opacity: 0.22, depthWrite: false })
);
scene.add(ground);
const grid = new GridHelper(60, 60, 0x445060, 0x2f3842);
grid.rotation.x = Math.PI / 2;
scene.add(grid);

const REGION_COLORS = {
  head:  [1.00, 0.95, 0.85], torso: [0.75, 0.75, 0.80],
  spine: [0.45, 0.85, 0.45], arm:   [0.95, 0.65, 0.25],
  leg:   [0.30, 0.55, 0.95],
};
let bones = null, boneGeo = null, bonePos = null;
let joints = null, jointGeo = null, jointPos = null;
const comMarker = new Mesh(new SphereGeometry(0.035, 16, 12),
  new MeshBasicMaterial({ color: 0xff3355 }));
scene.add(comMarker);

function buildBones() {
  N_LINKS = META.link_names.length;
  if (bones) { scene.remove(bones); scene.remove(joints); }
  boneGeo = new BufferGeometry();
  bonePos = new Float32Array(N_LINKS * 2 * 3);
  boneGeo.setAttribute('position', new BufferAttribute(bonePos, 3));
  const boneCol = new Float32Array(N_LINKS * 2 * 3);
  for (let i = 0; i < N_LINKS; i++) {
    const c = REGION_COLORS[META.link_regions[i]] || [0.7, 0.7, 0.7];
    for (let v = 0; v < 2; v++) {
      boneCol[(i * 2 + v) * 3] = c[0];
      boneCol[(i * 2 + v) * 3 + 1] = c[1];
      boneCol[(i * 2 + v) * 3 + 2] = c[2];
    }
  }
  boneGeo.setAttribute('color', new BufferAttribute(boneCol, 3));
  bones = new LineSegments(boneGeo, new LineBasicMaterial({ vertexColors: true }));
  // The geometry starts all-zero and its bounding sphere freezes at radius 0
  // on the first render; the follow-COM camera then culls every bone
  // (measured 2026-08-08: renderer.info bs=0, 0 bone lines drawn).
  bones.frustumCulled = false;
  scene.add(bones);
  jointGeo = new BufferGeometry();
  jointPos = new Float32Array(N_LINKS * 3);
  jointGeo.setAttribute('position', new BufferAttribute(jointPos, 3));
  joints = new Points(jointGeo, new PointsMaterial({ color: 0xffe9b0, size: 0.03 }));
  joints.frustumCulled = false;
  scene.add(joints);
}

// ---- camera orbit ----------------------------------------------------------
let orbit = { theta: -1.4, phi: 1.15, dist: 4.5, cx: 0, cy: 0, cz: 0.9 };
function applyCamera() {
  const sp = Math.sin(orbit.phi), cp = Math.cos(orbit.phi);
  camera.position.set(
    orbit.cx + orbit.dist * sp * Math.cos(orbit.theta),
    orbit.cy + orbit.dist * sp * Math.sin(orbit.theta),
    orbit.cz + orbit.dist * cp);
  camera.lookAt(orbit.cx, orbit.cy, orbit.cz);
}
let drag = null;
renderer.domElement.addEventListener('mousedown', e => { drag = { x: e.clientX, y: e.clientY }; });
window.addEventListener('mouseup', () => { drag = null; });
window.addEventListener('mousemove', e => {
  if (!drag) return;
  orbit.theta -= (e.clientX - drag.x) * 0.005;
  orbit.phi = Math.min(3.0, Math.max(0.15, orbit.phi - (e.clientY - drag.y) * 0.005));
  drag = { x: e.clientX, y: e.clientY };
  applyCamera();
});
renderer.domElement.addEventListener('wheel', e => {
  orbit.dist = Math.min(40, Math.max(0.8, orbit.dist * (1 + e.deltaY * 0.001)));
  applyCamera();
});

// ---- feed --------------------------------------------------------------------
ws.onmessage = ev => {
  if (typeof ev.data === 'string') {
    META = JSON.parse(ev.data);
    buildBones();
    return;
  }
  const dv = new DataView(ev.data);
  const tick = dv.getUint32(0, true);
  const flags = dv.getUint32(4, true);
  const headz = dv.getFloat32(8, true);
  const segs = new Float32Array(ev.data, 12, N_LINKS * 6);
  const com = new Float32Array(ev.data, 12 + N_LINKS * 24, 3);
  if (tick < lastTick) { prevF = null; curF = null; }  // server reset
  const now = performance.now();
  if (lastTickAt > 0) {
    const dtSim = tick - lastTick, dtWall = (now - lastTickAt) / 1000;
    if (dtWall > 0 && dtSim > 0) tpsEMA = 0.9 * tpsEMA + 0.1 * (dtSim / dtWall);
  }
  lastTick = tick; lastTickAt = now;
  prevF = curF ? { segs: curF.segs.slice(), com: curF.com.slice() } : null;
  prevAt = curAt;
  curF = { tick, flags, headz, segs: new Float32Array(segs), com: new Float32Array(com) };
  curAt = now;
  // probe/telemetry hook lives in the message handler, NOT the RAF loop:
  // headless Chromium may throttle RAF, the feed itself is the truth.
  window.__live = { tick, headz, tps: tpsEMA, cut: (flags & 1) === 0 };
};

ws.onopen = () => { el('status').textContent = 'connected'; };
ws.onclose = () => { el('status').textContent = 'DISCONNECTED -- is the server running?'; };

const el = id => document.getElementById(id);
el('btnCut').onclick = () => ws.send('cut');
el('btnReset').onclick = () => ws.send('reset');
el('btnPush').onclick = () => ws.send('push');
el('btnShove').onclick = () => ws.send('shove');

function loop() {
  requestAnimationFrame(loop);
  if (curF && bonePos) {
    let a = 0.0;
    if (prevF && curAt > prevAt) {
      a = Math.min(1.0, (performance.now() - curAt) / (curAt - prevAt));
    }
    for (let k = 0; k < N_LINKS * 6; k++) {
      bonePos[k] = prevF ? prevF.segs[k] * (1 - a) + curF.segs[k] * a : curF.segs[k];
    }
    for (let i = 0; i < N_LINKS; i++) {
      jointPos[i * 3] = bonePos[i * 6];
      jointPos[i * 3 + 1] = bonePos[i * 6 + 1];
      jointPos[i * 3 + 2] = bonePos[i * 6 + 2];
    }
    boneGeo.attributes.position.needsUpdate = true;
    jointGeo.attributes.position.needsUpdate = true;
    comMarker.position.set(curF.com[0], curF.com[1], curF.com[2]);
    if (el('follow').checked) {
      orbit.cx = curF.com[0]; orbit.cy = curF.com[1]; orbit.cz = curF.com[2];
      applyCamera();
    }
    const cut = (curF.flags & 1) === 0 ? '  [MUSCLES CUT]' : '';
    const pushing = (curF.flags & 2) ? '  [PUSHING]' : '';
    el('hud').textContent =
      `LIVE  tick ${curF.tick}   ${tpsEMA.toFixed(0)} ticks/s` +
      `  (${(tpsEMA / 1000).toFixed(2)}x realtime, honest slow motion)` +
      `   head z ${curF.headz.toFixed(2)} m${cut}${pushing}`;
    window.__live = { tick: curF.tick, headz: curF.headz, tps: tpsEMA,
                      cut: (curF.flags & 1) === 0 };
    // render-side telemetry for the probe (module scope is unreachable)
    let mn = Infinity, mx = -Infinity, nan = 0;
    for (let k = 0; k < N_LINKS * 6; k++) {
      const v = bonePos[k];
      if (Number.isNaN(v)) nan++;
      else { if (v < mn) mn = v; if (v > mx) mx = v; }
    }
    window.__dbg = { boneMin: mn, boneMax: mx, nan, nlinks: N_LINKS,
                     hasPrev: !!prevF, a,
                     camC: [orbit.cx, orbit.cy, orbit.cz],
                     draws: renderer.info.render.calls,
                     lines: renderer.info.render.lines,
                     tris: renderer.info.render.triangles,
                     bonesInScene: !!(bones && bones.parent),
                     bs: (boneGeo.boundingSphere ? boneGeo.boundingSphere.radius : null) };
  }
  renderer.render(scene, camera);
}
loop();
"""

_LIVE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Chimera -- theStandingHuman LIVE demo</title>
<style>
  body { margin: 0; background: #101418; color: #cfd8e3;
         font: 13px/1.4 monospace; overflow: hidden; }
  #view { position: fixed; inset: 0; }
  #ui { position: fixed; left: 10px; top: 10px; background: rgba(10,14,18,.8);
        padding: 10px 12px; border: 1px solid #2f3842; border-radius: 6px; }
  button { background: #1c232c; color: #cfd8e3; border: 1px solid #3a4654;
           border-radius: 4px; padding: 3px 10px; margin-right: 6px;
           font: inherit; cursor: pointer; }
  #btnCut { background: #5d2f2f; border-color: #c05a5a; }
  #hud { margin-top: 6px; color: #9fb2c8; }
  #status { color: #5a8c5a; }
</style>
</head>
<body>
<div id="view"></div>
<div id="ui">
  <button id="btnCut">CUT MUSCLES</button>
  <button id="btnPush">PUSH</button>
  <button id="btnShove">SHOVE</button>
  <button id="btnReset">reset</button>
  <div id="hud">connecting...</div>
  <div id="status">connecting...</div>
  <div style="margin-top:4px"><label><input id="follow" type="checkbox" checked> follow COM</label></div>
  <div style="margin-top:4px;color:#5a6a7c">drag=orbit wheel=zoom</div>
  <div style="margin-top:6px;color:#7c8ea3;max-width:340px">the battery's physics,
    computed as you watch (~0.12x realtime -- measured, not tuned).  Muscles
    hold ~0.3 s, legs buckle (STAND falsified, ground reaction one phase
    late).  CUT MUSCLES drops the frame harder -- your action, live.</div>
</div>
<script type="module">
__THREE_CORE__
</script>
<script type="module">
__THREE_MODULE__
{
__LIVE_JS__
}
</script>
</body>
</html>
"""


def build_live_html() -> bytes:
    core, module = load_three_bridged()
    html = (_LIVE_HTML
            .replace("__THREE_CORE__", core)
            .replace("__THREE_MODULE__", module)
            .replace("__LIVE_JS__", _LIVE_JS))
    return html.encode("utf-8")


# ---------------------------------------------------------------------------
# Server: one port, HTTP for the page, websocket for the feed (loopback only)
# ---------------------------------------------------------------------------

async def _async_main():
    from websockets.asyncio.server import serve
    from websockets.datastructures import Headers
    from websockets.http11 import Response

    spec = build_spec(1.80, 80.0)
    init_msg = json.dumps({
        "link_names": list(spec["links"].keys()),
        "link_regions": [_region(n) for n in spec["links"].keys()],
        "sample_every": DEMO_SAMPLE_EVERY,
        "dt": DT,
    })
    page = build_live_html()

    def process_request(connection, request):
        # Websocket handshakes must pass through; only plain HTTP GETs get
        # the page (measured bug 2026-08-08: answering the handshake with
        # the HTML page -> client sees 'Unexpected response code: 200').
        if request.headers.get("Upgrade", "").lower() == "websocket":
            return None
        if request.path in ("/", "/index.html"):
            return Response(200, "OK", Headers(
                [("Content-Type", "text/html; charset=utf-8")]), page)
        return Response(404, "Not Found", Headers(
            [("Content-Type", "text/plain")]), b"not found")

    async def handler(ws):
        CLIENTS.add(ws)
        try:
            await ws.send(init_msg)
            async for msg in ws:
                cmd = str(msg).strip().lower()
                if cmd in ("cut", "reset", "push", "shove"):
                    CMDQ.put(cmd)
        finally:
            CLIENTS.discard(ws)

    async def broadcaster():
        loop = asyncio.get_running_loop()
        while True:
            frame = await loop.run_in_executor(None, FRAMEQ.get)
            if CLIENTS:
                dead = []
                for c in list(CLIENTS):
                    try:
                        await c.send(frame)
                    except Exception:
                        dead.append(c)
                for c in dead:
                    CLIENTS.discard(c)

    threading.Thread(target=sim_loop, daemon=True).start()
    async with serve(handler, HOST, PORT, process_request=process_request):
        print(f"[live] serving http://{HOST}:{PORT}/  (loopback only)", flush=True)
        await broadcaster()


def main():
    if "--selftest" in sys.argv:
        # Probe hook: build the page and print its size (no server).
        print(f"live page: {len(build_live_html())/1e6:.1f} MB")
        return
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
