"""theStandingHuman DEMO v1 -- the LIVE feed (Lane D5).

RULE 0 -- STATEMENT: the same physics the battery ran can be watched AS IT
IS COMPUTED, and the viewer's action changes it live: a local feed (sim in
a thread, websocket broadcast) drives the v0 player at the measured solve
rate, and a "cut muscles" button press visibly deepens the fall -- the
first interactive membrane.

PREDICTION (named before the run):
  (a) the stream sustains >= 100 sim-ticks/s over the probe window
      (measured 116 ticks/s solo, 2026-08-08);
  (b) with no commands, the live head_z at tick T matches the baked MAIN
      export at the same tick to 1e-9 (same deterministic trajectory,
      verified bitwise in the controller lane);
  (c) a cut at tick ~250 leaves head_z at tick 850 at least 0.1 m BELOW
      the baked MAIN at tick 850 -- the viewer's action has real effect.

FALSIFIERS: (a) fails -> the live membrane cannot sustain the rate;
(b) fails -> the live loop is not the battery's physics; (c) fails ->
the button is decoration.  Any firing -> record, don't patch.

Usage:
    PYTHONPATH=E:/PythonChimera python LightEngine/serve_standing_demo.py
    # then open http://127.0.0.1:8765/   (loopback only, per bind-guard)
"""

from __future__ import annotations

import asyncio
import json
import queue
import struct
import sys
import threading
import time

import numpy as np

from LightEngine.kinematic import build_spec, transforms
from LightEngine.kinematic.dynamics import center_of_mass, init_state, step
from LightEngine.kinematic.muscle_controller import MuscleController
from LightEngine.build_standing_demo import (
    DEMO_SAMPLE_EVERY, _region, load_three_bridged,
)
from LightEngine.demo_kinematic import DT

HOST = "127.0.0.1"   # loopback only -- bind-guard law
PORT = 8765

CMDQ: queue.Queue[str] = queue.Queue()
FRAMEQ: queue.Queue[bytes] = queue.Queue(maxsize=256)
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


def sim_loop():
    spec = build_spec(1.80, 80.0)

    def fresh():
        state = init_state(spec)
        state["rotation_locks"] = False
        return state, MuscleController(spec, state)

    state, ctrl = fresh()
    skull = state["name_to_idx"]["skull"]
    tick = 0
    n_links = len(state["link_names"])
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
                    tick = 0
                    t0 = time.time()
                    print("[sim] reset", flush=True)
        except queue.Empty:
            pass

        ctrl.apply(state)
        step(spec, state, DT, n_proj_iters=20)
        if tick % DEMO_SAMPLE_EVERY == 0:
            seg = _endpoints(spec, state)
            com = center_of_mass(spec, state)
            head_z = float(state["pos"][skull][2])
            flags = 1 if ctrl.enabled else 0
            payload = struct.pack("<IIf", tick, flags, head_z) \
                + seg.astype("<f4").tobytes() \
                + np.asarray(com, dtype="<f4").tobytes()
            try:
                FRAMEQ.put_nowait(payload)
            except queue.Full:
                pass  # slow client: drop, never block the physics
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
    el('hud').textContent =
      `LIVE  tick ${curF.tick}   ${tpsEMA.toFixed(0)} ticks/s` +
      `  (${(tpsEMA / 1000).toFixed(2)}x realtime, honest slow motion)` +
      `   head z ${curF.headz.toFixed(2)} m${cut}`;
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
                if cmd in ("cut", "reset"):
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
