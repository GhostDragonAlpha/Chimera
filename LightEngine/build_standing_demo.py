"""theStandingHuman v2-rigid -- GAME DEMO v0 (Lane D).

RULE 0 -- STATEMENT: a blind viewer of the exported frames (a self-contained
HTML player) can tell MAIN (muscles on, frame stands) from CONTROL (muscles
cut at tick 1200, frame collapses) WITHOUT reading any log -- i.e. the
exported trajectory is a faithful, legible replay of the muscle battery.

PREDICTION (named before the run):
  (a) frames export at 8-tick cadence for both runs; head z at frame 0 matches
      the battery's deterministic head_z0 to 1e-9 (same trajectory, re-run);
  (b) the rendered HTML at tick 0 shows a standing figure (head z ~1.75 m in
      the HUD) and CONTROL at tick >= 1800 shows head z < 0.5 m -- verified by
      playwright screenshots, not by prose.

FALSIFIERS: if the exported head-z trace disagrees with the live battery
metrics at matching ticks, the export is unfaithful; if the screenshots do
not visibly show stand-vs-collapse, the demo is illegible.  Either fires ->
record, don't patch.

Pipeline:
    python LightEngine/build_standing_demo.py              # sim + HTML
    python LightEngine/build_standing_demo.py --html-only  # reuse cached frames

Outputs:
    LightEngine/output/standing_demo_frames.json  (cached frame data)
    LightEngine/output/standing_demo.html         (self-contained player)
"""

from __future__ import annotations

import base64
import json
import sys
import time
from pathlib import Path

import numpy as np

from LightEngine.kinematic import build_spec, transforms
from LightEngine.kinematic.dynamics import center_of_mass, init_state, step
from LightEngine.kinematic.muscle_controller import MuscleController
from LightEngine.demo_kinematic import CONTROL_CUT_TICK, DT, N_TICKS

DEMO_SAMPLE_EVERY = 8        # ticks between recorded frames
OUT_DIR = Path(__file__).resolve().parent / "output"
FRAMES_JSON = OUT_DIR / "standing_demo_frames.json"
HTML_OUT = OUT_DIR / "standing_demo.html"
THREE_DIR = Path(__file__).resolve().parent.parent / "node_modules" / "three" / "build"


def _region(link_name: str) -> str:
    """Color bucket for the player.  Substring rules over the 77 link names."""
    n = link_name.lower()
    if "skull" in n or "head" in n or "mandible" in n or "hyoid" in n:
        return "head"
    if any(k in n for k in ("femur", "tibia", "fibula", "patella",
                            "tarsal", "metatars", "toe", "calcane", "foot")):
        return "leg"
    if any(k in n for k in ("humerus", "radius", "ulna", "carp",
                            "metacarp", "phal", "hand", "finger")):
        return "arm"
    if any(k in n for k in ("vertebra", "sacrum", "coccyx", "spine")):
        return "spine"
    return "torso"


def _b64_f32(arr: np.ndarray) -> str:
    return base64.b64encode(
        np.ascontiguousarray(arr, dtype="<f4").tobytes()).decode("ascii")


def _export_run(spec, label: str, relax_muscles_at: int | None) -> dict:
    """Re-run the battery trajectory, recording bone endpoints per frame.

    The battery (demo_kinematic_v2) is deterministic; this records the SAME
    trajectory the meters judged.  The dynamics state is meter-based (pos is
    each link's COM in meters); segments are prox-origin -> distal-tip.
    """
    state = init_state(spec)
    state["rotation_locks"] = False
    ctrl = MuscleController(spec, state)

    names = list(state["link_names"])
    n_links = len(names)
    # Bone endpoints in each link's LOCAL frame, relative to the COM-origin
    # state (dynamics.py: pos is the link COM in meters; quat maps local->world).
    # a = proximal joint origin, b = distal tip, both relative to COM, meters.
    a_local = np.zeros((n_links, 3), dtype=np.float64)
    b_local = np.zeros((n_links, 3), dtype=np.float64)
    for i, name in enumerate(names):
        link = spec["links"][name]
        com_off = np.asarray(link["com_offset_m"], dtype=np.float64)
        d_tip = link["R_world_to_local"] @ (
            np.asarray(link["dist_m"]) - np.asarray(link["prox_m"]))
        a_local[i] = -com_off
        b_local[i] = d_tip - com_off

    skull = state["name_to_idx"]["skull"]
    head_z0 = float(state["pos"][skull][2])
    # Prediction (a): same trajectory as the battery -> head_z0 sits inside the
    # STAND band region [1.746, 1.875].  A miss here means the export units or
    # the state convention drifted from the battery -- stop, don't export.
    if not (1.70 < head_z0 < 1.92):
        raise RuntimeError(
            f"export/battery mismatch: head_z0={head_z0:.4f} m, "
            f"expected inside ~[1.70, 1.92] (battery band [1.746, 1.875])")

    frames = []
    coms = []
    head_z = []
    relaxed = False
    for tick in range(N_TICKS + 1):
        if relax_muscles_at is not None and tick == relax_muscles_at and not relaxed:
            ctrl.enabled = False
            relaxed = True
        ctrl.apply(state)
        step(spec, state, DT, n_proj_iters=20)
        if tick % DEMO_SAMPLE_EVERY != 0:
            continue
        seg = np.zeros((n_links, 6), dtype=np.float64)
        for i in range(n_links):
            R = transforms.to_matrix(state["quat"][i])
            pc = state["pos"][i]
            seg[i, :3] = pc + R @ a_local[i]
            seg[i, 3:] = pc + R @ b_local[i]
        frames.append(seg)
        coms.append(center_of_mass(spec, state))
        head_z.append(float(state["pos"][skull][2]))

    frames_arr = np.stack(frames)            # (n_frames, n_links, 6)
    return {
        "label": label,
        "head_z0": head_z0,
        "frames_b64": _b64_f32(frames_arr),
        "com_b64": _b64_f32(np.stack(coms)),
        "head_z": [round(z, 4) for z in head_z],
    }


def export_frames() -> dict:
    spec = build_spec(1.80, 80.0)
    names = list(spec["links"].keys())
    t0 = time.time()
    main = _export_run(spec, "MAIN", None)
    print(f"[export] MAIN   {len(main['head_z'])} frames "
          f"({time.time() - t0:.1f}s)  head_z0={main['head_z0']:.4f} m")
    t1 = time.time()
    control = _export_run(spec, "CONTROL", CONTROL_CUT_TICK)
    print(f"[export] CONTROL {len(control['head_z'])} frames "
          f"({time.time() - t1:.1f}s)  head_z0={control['head_z0']:.4f} m")

    data = {
        "dt": DT,
        "sample_every": DEMO_SAMPLE_EVERY,
        "n_ticks": N_TICKS,
        "cut_tick": CONTROL_CUT_TICK,
        "link_names": names,
        "link_regions": [_region(n) for n in names],
        "main": main,
        "control": control,
    }
    FRAMES_JSON.write_text(json.dumps(data))
    print(f"[export] wrote {FRAMES_JSON} "
          f"({FRAMES_JSON.stat().st_size / 1e6:.1f} MB)")
    return data


# ---------------------------------------------------------------------------
# HTML player (self-contained: three.js core+module inlined, import stripped)
# ---------------------------------------------------------------------------

_PLAYER_JS = r"""
// ---- data ----------------------------------------------------------------
const DATA = __DATA_JSON__;

function decodeF32(b64) {
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new Float32Array(bytes.buffer);
}

const N_LINKS = DATA.link_names.length;
const RUNS = { MAIN: DATA.main, CONTROL: DATA.control };
for (const k in RUNS) {
  RUNS[k].frames = decodeF32(RUNS[k].frames_b64);   // nF * nLinks * 6
  RUNS[k].com = decodeF32(RUNS[k].com_b64);         // nF * 3
  RUNS[k].nFrames = RUNS[k].head_z.length;
}

const REGION_COLORS = {
  head:  [1.00, 0.95, 0.85],
  torso: [0.75, 0.75, 0.80],
  spine: [0.45, 0.85, 0.45],
  arm:   [0.95, 0.65, 0.25],
  leg:   [0.30, 0.55, 0.95],
};

// ---- scene ---------------------------------------------------------------
const renderer = new WebGLRenderer({ antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(window.innerWidth, window.innerHeight);
document.getElementById('view').appendChild(renderer.domElement);

const scene = new Scene();
scene.background = new Color(0x101418);
const camera = new PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.01, 200);
camera.up.set(0, 0, 1);   // sim is z-up

scene.add(new HemisphereLight(0xbfd4ff, 0x30281e, 1.1));
const sun = new DirectionalLight(0xffffff, 1.4);
sun.position.set(3, -4, 6);
scene.add(sun);

// ground: the floor holds ONLY 10 foot contact points in the sim, so an
// opaque plane would hide the honest below-grid crumple.  Faint glass.
const ground = new Mesh(
  new PlaneGeometry(60, 60),
  new MeshBasicMaterial({ color: 0x2a2f36, transparent: true, opacity: 0.22, depthWrite: false })
);
scene.add(ground);  // z=0 plane
const grid = new GridHelper(60, 60, 0x445060, 0x2f3842);
grid.rotation.x = Math.PI / 2;  // GridHelper is xz by default -> xy
scene.add(grid);

// bones: one LineSegments, 2 vertices per link
const boneGeo = new BufferGeometry();
const bonePos = new Float32Array(N_LINKS * 2 * 3);
boneGeo.setAttribute('position', new BufferAttribute(bonePos, 3));
const boneCol = new Float32Array(N_LINKS * 2 * 3);
for (let i = 0; i < N_LINKS; i++) {
  const c = REGION_COLORS[DATA.link_regions[i]] || [0.7, 0.7, 0.7];
  for (let v = 0; v < 2; v++) {
    boneCol[(i * 2 + v) * 3]     = c[0];
    boneCol[(i * 2 + v) * 3 + 1] = c[1];
    boneCol[(i * 2 + v) * 3 + 2] = c[2];
  }
}
boneGeo.setAttribute('color', new BufferAttribute(boneCol, 3));
const bones = new LineSegments(boneGeo, new LineBasicMaterial({ vertexColors: true }));
// The follow-COM camera can leave the stale first-frame bounding sphere
// behind; never cull the skeleton (measured trap in the live lane).
bones.frustumCulled = false;
scene.add(bones);

// joints: small points at prox endpoints
const jointGeo = new BufferGeometry();
const jointPos = new Float32Array(N_LINKS * 3);
jointGeo.setAttribute('position', new BufferAttribute(jointPos, 3));
const joints = new Points(jointGeo, new PointsMaterial({ color: 0xffe9b0, size: 0.03 }));
joints.frustumCulled = false;
scene.add(joints);

// COM marker
const comMarker = new Mesh(
  new SphereGeometry(0.035, 16, 12),
  new MeshBasicMaterial({ color: 0xff3355 })
);
scene.add(comMarker);

// ---- camera orbit (drag = orbit, wheel = zoom) -----------------------------
let orbit = { theta: -1.4, phi: 1.15, dist: 4.5, cx: 0, cy: 0, cz: 0.9 };
function applyCamera() {
  const sp = Math.sin(orbit.phi), cp = Math.cos(orbit.phi);
  camera.position.set(
    orbit.cx + orbit.dist * sp * Math.cos(orbit.theta),
    orbit.cy + orbit.dist * sp * Math.sin(orbit.theta),
    orbit.cz + orbit.dist * cp
  );
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

// ---- playback --------------------------------------------------------------
let runName = 'MAIN';
let frameF = 0;           // fractional frame index
let playing = true;
let speed = 1.0;
const FPS_ASSUMED = 60;

const el = id => document.getElementById(id);
const slider = el('scrub');
const hud = el('hud');

function currentRun() { return RUNS[runName]; }

function showFrame(fFrac) {
  const run = currentRun();
  const f0 = Math.min(run.nFrames - 1, Math.floor(fFrac));
  const f1 = Math.min(run.nFrames - 1, f0 + 1);
  const a = fFrac - f0;
  const base0 = f0 * N_LINKS * 6, base1 = f1 * N_LINKS * 6;
  for (let i = 0; i < N_LINKS; i++) {
    for (let k = 0; k < 6; k++) {
      const v = run.frames[base0 + i * 6 + k] * (1 - a) + run.frames[base1 + i * 6 + k] * a;
      bonePos[i * 6 + k] = v;
    }
    jointPos[i * 3]     = bonePos[i * 6];
    jointPos[i * 3 + 1] = bonePos[i * 6 + 1];
    jointPos[i * 3 + 2] = bonePos[i * 6 + 2];
  }
  boneGeo.attributes.position.needsUpdate = true;
  jointGeo.attributes.position.needsUpdate = true;
  comMarker.position.set(
    run.com[f0 * 3] * (1 - a) + run.com[f1 * 3] * a,
    run.com[f0 * 3 + 1] * (1 - a) + run.com[f1 * 3 + 1] * a,
    run.com[f0 * 3 + 2] * (1 - a) + run.com[f1 * 3 + 2] * a
  );
  if (el('follow').checked) {
    orbit.cx = comMarker.position.x;
    orbit.cy = comMarker.position.y;
    orbit.cz = comMarker.position.z;
    applyCamera();
  }
  const tick = Math.round(fFrac * DATA.sample_every);
  const hz = run.head_z[f0] * (1 - a) + run.head_z[Math.min(run.nFrames - 1, f0 + 1)] * a;
  const cut = (runName === 'CONTROL' && tick >= DATA.cut_tick) ? '  [MUSCLES CUT]' : '';
  hud.textContent = `${runName}  tick ${tick} / ${DATA.n_ticks}` +
    `   head z ${hz.toFixed(2)} m${cut}`;
  slider.value = String(fFrac);
}

function setRun(name) {
  runName = name;
  el('btnMain').classList.toggle('on', name === 'MAIN');
  el('btnControl').classList.toggle('on', name === 'CONTROL');
  el('cutmark').style.display = name === 'CONTROL' ? 'block' : 'none';
  showFrame(frameF);
}

el('btnMain').onclick = () => setRun('MAIN');
el('btnControl').onclick = () => setRun('CONTROL');
el('btnPlay').onclick = () => { playing = !playing; el('btnPlay').textContent = playing ? 'pause' : 'play'; };
el('speed').onchange = e => { speed = parseFloat(e.target.value); };
slider.oninput = e => { frameF = parseFloat(e.target.value); playing = false; el('btnPlay').textContent = 'play'; showFrame(frameF); };

// slider max + cut marker position
slider.max = String(RUNS.MAIN.nFrames - 1);
el('cutmark').style.left = (DATA.cut_tick / DATA.sample_every / (RUNS.MAIN.nFrames - 1) * 100) + '%';

// URL params for deterministic screenshots: ?run=CONTROL&frame=250&theta=..&phi=..&dist=..
const q = new URLSearchParams(location.search);
if (q.get('run')) setRun(q.get('run').toUpperCase());
if (q.get('frame')) { frameF = parseFloat(q.get('frame')); playing = false; }
if (q.get('theta')) orbit.theta = parseFloat(q.get('theta'));
if (q.get('phi')) orbit.phi = parseFloat(q.get('phi'));
if (q.get('dist')) orbit.dist = parseFloat(q.get('dist'));
applyCamera();
showFrame(frameF);

function loop() {
  requestAnimationFrame(loop);
  const run = currentRun();
  if (playing) {
    // realtime: sim runs at 1/dt ticks/s; sampled every sample_every ticks,
    // so realtime playback = (1/dt)/sample_every sampled frames per second,
    // divided by rendered fps => frames per rendered frame.
    frameF += (1 / DATA.dt / DATA.sample_every / FPS_ASSUMED) * speed;
    if (frameF > run.nFrames - 1) frameF = run.nFrames - 1;
    showFrame(frameF);
  }
  renderer.render(scene, camera);
}
loop();
"""

_PLAYER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Chimera -- theStandingHuman v2-rigid demo</title>
<style>
  body { margin: 0; background: #101418; color: #cfd8e3;
         font: 13px/1.4 monospace; overflow: hidden; }
  #view { position: fixed; inset: 0; }
  #ui { position: fixed; left: 10px; top: 10px; background: rgba(10,14,18,.8);
        padding: 10px 12px; border: 1px solid #2f3842; border-radius: 6px; }
  button { background: #1c232c; color: #cfd8e3; border: 1px solid #3a4654;
           border-radius: 4px; padding: 3px 10px; margin-right: 6px;
           font: inherit; cursor: pointer; }
  button.on { background: #2f5d8a; border-color: #5a8cc0; }
  #scrubwrap { position: fixed; left: 10px; right: 10px; bottom: 12px; }
  #scrub { width: 100%; }
  #cutmark { position: absolute; top: -4px; width: 2px; height: 22px;
             background: #ff3355; display: none; pointer-events: none; }
  #hud { margin-top: 6px; color: #9fb2c8; }
  select { background: #1c232c; color: #cfd8e3; border: 1px solid #3a4654;
           font: inherit; }
</style>
</head>
<body>
<div id="view"></div>
<div id="ui">
  <button id="btnMain" class="on">MAIN (muscles on)</button>
  <button id="btnControl">CONTROL (cut @1200)</button>
  <button id="btnPlay">pause</button>
  <select id="speed">
    <option value="0.25">0.25x</option>
    <option value="0.5">0.5x</option>
    <option value="1" selected>1x</option>
    <option value="2">2x</option>
    <option value="4">4x</option>
  </select>
  <div id="hud">loading...</div>
  <div style="margin-top:4px"><label><input id="follow" type="checkbox" checked> follow COM</label></div>
  <div style="margin-top:4px;color:#5a6a7c">drag=orbit wheel=zoom</div>
  <div style="margin-top:6px;color:#7c8ea3;max-width:340px">muscles hold the frame
    ~0.3 s, then the legs buckle (battery: STAND falsified -- ground reaction
    arrives one phase late).  CONTROL cuts the muscles at tick 1200: the frame
    sinks ~2x deeper (battery: CONTROL passed).  Floor holds only the feet;
    below-grid sinking is a known model limit, shown honestly.</div>
</div>
<div id="scrubwrap">
  <div id="cutmark"></div>
  <input id="scrub" type="range" min="0" max="100" value="0" step="0.1">
</div>
<script type="module">
__THREE_CORE__
</script>
<script type="module">
__THREE_MODULE__
__PLAYER_JS__
</script>
</body>
</html>
"""


def load_three_bridged() -> tuple[str, str]:
    """Inline-ready three.js r185 sources: (core_js, module_js).

    The two builds cannot share one inline module scope (duplicate mangled
    identifiers), so the core is transformed to publish its exports on
    window.__THREE_CORE__ and the module to destructure them back.  The
    module's own import covers only 197 of the 444 core exports (Scene,
    WebGLRenderer arrive via the re-export), so the FULL core export list is
    destructured.  No 'as' aliases exist in any statement (verified r185).
    """
    import re
    core = (THREE_DIR / "three.core.js").read_text(encoding="utf-8")
    module = (THREE_DIR / "three.module.js").read_text(encoding="utf-8")
    m_core_exp = re.search(r"export\s*\{([^}]*)\}\s*;", core, flags=re.DOTALL)
    if m_core_exp is None:
        raise RuntimeError("three bridge failed (core export not found)")
    core_names = m_core_exp.group(1)
    core = core[:m_core_exp.start()] + \
        "window.__THREE_CORE__ = {" + core_names + "};" + \
        core[m_core_exp.end():]
    module, n1 = re.subn(
        r"import\s*\{[^}]*\}\s*from\s*'\./three\.core\.js';",
        "const {" + core_names + "} = window.__THREE_CORE__;",
        module, count=1, flags=re.DOTALL)
    module, n2 = re.subn(
        r"export\s*\{[^}]*\}\s*from\s*'\./three\.core\.js';",
        "", module, count=1, flags=re.DOTALL)
    if n1 != 1 or n2 != 1:
        raise RuntimeError(
            f"three bridge failed (import={n1}, reexport={n2})")
    return core, module


def build_html(data: dict) -> None:
    core, module = load_three_bridged()

    # Slim payload for the page: drop the raw python-side duplicates.
    page_data = {
        "dt": data["dt"],
        "sample_every": data["sample_every"],
        "n_ticks": data["n_ticks"],
        "cut_tick": data["cut_tick"],
        "link_names": data["link_names"],
        "link_regions": data["link_regions"],
        "main": data["main"],
        "control": data["control"],
    }
    player_js = _PLAYER_JS.replace(
        "__DATA_JSON__", json.dumps(page_data, separators=(",", ":")))
    # three.module.js has its own top-level `const DATA` (a lookup table);
    # the player shares its module scope, so fence the player in a block.
    player_js = "{\n" + player_js + "\n}"

    html = (_PLAYER_HTML
            .replace("__THREE_CORE__", core)
            .replace("__THREE_MODULE__", module)
            .replace("__PLAYER_JS__", player_js))
    HTML_OUT.write_text(html, encoding="utf-8")
    print(f"[html] wrote {HTML_OUT} ({HTML_OUT.stat().st_size / 1e6:.1f} MB)")


def main() -> None:
    html_only = "--html-only" in sys.argv
    data = None
    if html_only:
        data = json.loads(FRAMES_JSON.read_text())
        print(f"[html] reusing cached {FRAMES_JSON}")
    else:
        data = export_frames()
    build_html(data)


if __name__ == "__main__":
    main()
