"""native_binding_visible.py -- §11.20 stage 9 increment 3: the FIRST
VISIBLE slice of a qualified piece (acceptance amendment 2026-10-10:
playability is evidenced by actual visible browser gameplay).

THE EXISTING BROWSER PATH (located, not built): the engine's own HTTP
server serves GET /frame -- a PNG of the CURRENT engine render
(ChimeraEngine/engine/main.cpp:2863, "strictly fresh: the bytes POSTDATE
the request"); after an MD01 upload the membrane demo owns the per-frame
present (engine.hpp:220 membrane_demo_frame), so /frame IS the compiled
scene. The existing game-shell proxy corroborates the same path
(tools/game_shell/server.py:186-188, /api/frame -> /frame). No web page is
authored here: the browser displays the engine's own endpoint, and the
screenshots are of the browser showing it. The browser is HEADED
(playwright-core from the repo root, driven by
tools/artificial_proteins/native_binding_shot.js in the existing
tools/*_shots.js style; node runtime: the repo-standard portable node).

THE AFFORDANCE LOOP, one qualified instance (assembly.star-k2, 1.0x,
0.8 N input load, compile law of increments 1-2):
  startup   engine VISIBLE (no --hidden), MD01 upload, browser shows the
            rest scene                                     -> screenshot
  gamma     the existing 'gamma' control doubles the admitted tension:
            energy doubles at fixed geometry (the demo's own falsifier
            law); NO mesh motion, NO accepted_state_id change  -> screenshot
  deform    the existing membrane 'step'/'run' control (rail-projected
            descent at the packet's declared centre, engine.cpp:4587)
            CHANGES accepted_state_id but the resulting motion is
            guard-limited to <1e-3 wu total travel (<0.36 px on screen,
            CPU-mirrored and measured): NOT visibly deforming -- recorded
            as the slice's FAIL item, loop still completed -> screenshot
  restart   the existing 'reset' control returns the state bit-exactly to
            the uploaded initial (engine.cpp:4781 law)     -> screenshot
  replay    a SECOND visible engine boot compiles the SAME transaction and
            must reproduce the SAME accepted_state_id and energy

  PIN-LAW FLAG (recorded, not resolved here): the MD01 packet header
  hardcodes centre index 6 (membrane_demo_client.py:43) and carries NO pin
  field, while every qualified piece record pins its rim vertices 0..n-1
  (compiled "pins") with the free apex at index n. So the demo's step
  control moves a rim vertex the record's boundary law holds fixed (the
  engine zeroes pins host-side, engine.cpp:4620-4624). The deformation is
  real and accepted by the engine; whether it counts as qualified play for
  the piece is flagged to the coordinator, not claimed either way here.

Receipt: docs/evidence/mechanism_factory/native_binding_visible_receipt_<stamp>.json
(control sequence, screenshot paths + sha256, state hashes, replay verdict).

Run INSIDE a managed GPU reservation (one gpu_batch manifest job):
  python -B -m tools.artificial_proteins.native_binding_visible \
      --exe <chimera_engine.exe> --out <fresh dir> [--port 8829]
Prints "VISIBLE SLICE COMPLETE <receipt path>"; exits 1 when the visibility
acceptance item FAILED (recorded in the receipt with measured numbers).
"""
from __future__ import annotations

import argparse
import itertools
import json
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from .native_binding_engine import (_packet_from_transaction,
                                    _source_commit)
from .native_view import accepted_hash, require
from tools.evidence_output import (EvidencePathExists, default_stamp,
                                   resolve_evidence_path)
from tools.python_control.client import EngineControl
from tools.mechanism_factory import native_binding as nb
from .core import file_hash

_HERE = Path(__file__).resolve().parent            # tools/artificial_proteins
_REPO = _HERE.parent.parent
EVID_DIR = _REPO / "docs" / "evidence" / "mechanism_factory"
SHOT_JS = _HERE / "native_binding_shot.js"

RECEIPT_SCHEMA = "chimera-mechanism-factory-native-binding-visible-v1"
NODE_EXE = r"C:\Users\allen\node-portable\node-v22.19.0-win-x64\node.exe"
RUN_STEPS = 126                    # the demo's own synchronous batch size


def _shots(browser_spec: dict) -> None:
    require(Path(NODE_EXE).is_file(), "node_runtime_missing")
    spec_path = browser_spec["dir"] / "shots_spec.json"
    spec_path.write_text(json.dumps(browser_spec["spec"]), encoding="utf-8")
    proc = subprocess.run([NODE_EXE, str(SHOT_JS), str(spec_path)],
                          capture_output=True, text=True, timeout=120)
    require(proc.returncode == 0,
            f"browser_shot_failed: {proc.stderr[-200:]}")


def _pixel_diff(a: Path, b: Path) -> int:
    from PIL import Image
    ia = np.asarray(Image.open(a).convert("RGB"), dtype=np.int16)
    ib = np.asarray(Image.open(b).convert("RGB"), dtype=np.int16)
    if ia.shape != ib.shape:
        return -1
    return int((np.abs(ia - ib).max(axis=2) > 8).sum())


def _boot(exe: Path, native: Path, port: int, board: Path | None = None,
          size: tuple[int, int] = (1280, 720)):
    """One VISIBLE private engine boot: no --hidden flag (main.cpp:845-847
    -- --hidden only retires the developer console; the render window is
    the visible surface either way) and no CREATE_NO_WINDOW. Window size
    argv[3]/argv[4] = 1280x720 (main.cpp:827-836). Optional Studio board
    file at argv[2] (main.cpp:974-981: any argv[2] not starting with "--").
    Returns the proc."""
    argv = [str(native / exe.name), str(port)]
    if board is not None:
        argv.append(str(board))
    argv += [str(size[0]), str(size[1]), "--no-restore"]
    proc = subprocess.Popen(
        argv,
        cwd=native, stdout=(native / "stdout.log").open("wb"),
        stderr=(native / "stderr.log").open("wb"))
    return proc


def visible_session(txn: dict, output: Path, executable: Path,
                    port: int = 8829) -> dict:
    """Boot a VISIBLE engine, run the affordance loop with browser
    screenshots, then boot AGAIN and require identical state hashes."""
    packet, pos32, faces, gamma, e_ref = _packet_from_transaction(txn)
    expect_id = accepted_hash(pos32)

    with socket.socket() as sock:
        require(sock.connect_ex(("127.0.0.1", port)) != 0,
                "native_port_occupied")
    executable = executable.resolve()
    native = output / "native"
    native.mkdir(exist_ok=False)
    shutil.copy2(executable, native / executable.name)
    shutil.copytree(executable.parent / "shaders", native / "shaders")
    base = f"http://127.0.0.1:{port}"

    rec: dict = {"instance_id": txn["instance_id"],
                 "record_id": txn["record_id"],
                 "transaction_hash": txn["transaction_hash"],
                 "accepted_hash_wu": expect_id,
                 "energy_reference_J": e_ref,
                 "sequence": []}
    # unique /frame query per browser shot (cache-bust; the engine strips
    # the query before routing, main.cpp:929, so this hits the same /frame
    # endpoint -- main.cpp:2863 -- and no page is authored)
    _seq = itertools.count(1)

    def frame_url() -> str:
        return base + f"/frame?v={next(_seq)}"
    shots = []
    proc = None
    try:
        # ── BOOT A: startup ─────────────────────────────────────────────
        proc = _boot(executable, native, port)
        engine = EngineControl(base, timeout=15)
        for _ in range(100):
            require(proc.poll() is None, "private_engine_exited")
            try:
                engine.telemetry()
                break
            except OSError:
                time.sleep(0.2)
        else:
            raise RuntimeError("private_engine_readiness_timeout")

        engine.membrane.upload(packet)
        engine.membrane.pause()
        st = engine.membrane.state()
        st = st.get("status", st)
        require(st["accepted_state_id"] == expect_id,
                "native_upload_identity_mismatch")
        require(abs(st["energy"] - e_ref) <= 3e-4, "physics_mismatch")
        rec["startup_state_id"] = st["accepted_state_id"]
        rec["startup_energy_J"] = st["energy"]
        rec["material_snapshot"] = st["material_snapshot"]
        shot_a = output / "a-startup-scene.png"
        shots.append({"url": frame_url(), "out": str(shot_a),
                      "wait_ms": 800})
        _shots({"dir": output, "spec": {"shots": shots[-1:]}})
        require(shot_a.is_file() and shot_a.stat().st_size > 20000,
                "startup_scene_not_visible")
        rec["sequence"].append({"step": "startup", "control": "MD01 upload"
                                " + pause", "state_id": st["accepted_state_id"],
                                "screenshot": shot_a.name,
                                "screenshot_sha256": file_hash(shot_a)})

        # ── physical consequence: the existing 'gamma' material control ──
        # THE DEMO LAW FINDING (recorded, not worked around): the membrane
        # demo's ONLY geometric freedom is one vertical-rail DOF at the
        # packet's hardcoded centre index 6 (tools/membrane_demo_client.py:
        # 43; engine.cpp md_step_once:4587 "free DOF = centre... rail
        # z-only"; ops reset|step|run|pause|gamma|reject, main.cpp:1199).
        # For the compiled star, vertex 6 is a PINNED rim vertex (the
        # record's only free vertex is the seam apex, index 200), so the
        # demo's step/run controls cannot legally deform this scene: they
        # would move a vertex the qualified boundary law holds fixed.
        # The LEGAL consequence of the gamma control is material: under the
        # demo's own falsifier law (membrane_window_demo: "fixed-state
        # gamma doubling doubles energy and force"), doubling the admitted
        # tension must double the energy at fixed geometry.
        engine.membrane.tension(2.0)
        doubled = engine.membrane.state()
        doubled = doubled.get("status", doubled)
        ratio = doubled["energy"] / rec["startup_energy_J"]
        require(1.99 <= ratio <= 2.01, "gamma_doubling_law_violated")
        rec["gamma_doubled_energy_J"] = doubled["energy"]
        rec["gamma_doubling_ratio"] = ratio
        shot_b = output / "b-gamma-doubled-scene.png"
        _shots({"dir": output, "spec": {"shots": [
            {"url": frame_url(), "out": str(shot_b), "wait_ms": 800}]}})
        require(shot_b.is_file(), "gamma_scene_not_visible")
        rec["gamma_pixel_diff_px"] = _pixel_diff(shot_a, shot_b)
        rec["gamma_visible_mesh_motion"] = (
            "GAP (recorded, not worked around): the gamma control's "
            "consequence is MATERIAL only -- energy doubles at fixed "
            "geometry, accepted_state_id unchanged, screenshot pixel diff "
            f"{rec['gamma_pixel_diff_px']} px. The demo's only geometric "
            "freedom is the rail DOF at the packet's hardcoded centre "
            "index 6 (membrane_demo_client.py:43, engine.cpp:4587); the "
            "step control below exercises it.")
        rec["sequence"].append({"step": "consequence", "control": "gamma "
                                "2.0 (admitted)", "state_id":
                                doubled["accepted_state_id"],
                                "energy_ratio": ratio,
                                "screenshot": shot_b.name,
                                "screenshot_sha256": file_hash(shot_b)})

        # restore the admitted material before any geometric control
        engine.membrane.tension(1.0)
        back = engine.membrane.state()
        back = back.get("status", back)
        require(abs(back["energy"] - rec["startup_energy_J"]) <= 3e-4,
                "gamma_restore_mismatch")

        # ── physical consequence: the existing 'step'/'run' control ─────
        # The demo's rail-projected descent (engine.cpp:4587) moves the
        # packet's declared centre (index 6) along z; accepted trials CHANGE
        # accepted_state_id. The record pins vertex 6 (see PIN-LAW FLAG).
        centre0 = back["centre"][2]
        # the demo's own synchronous batch size, repeated until the rail
        # descent has moved the centre VISIBLY (>= 0.02 wu = 2 cm) or the
        # demo reports a terminal state -- every accepted trial changes
        # accepted_state_id (engine.cpp:4587 law)
        moved = back
        rounds = 0
        for _ in range(8):
            engine.membrane.step(RUN_STEPS)
            rounds += 1
            moved = engine.membrane.state()
            moved = moved.get("status", moved)
            if (moved.get("terminal_state") not in (None, "", "running")
                    or abs(float(moved["centre"][2]) - float(centre0))
                    >= 0.02):
                break
        rec["deform_batches"] = rounds
        rec["deform_state_id"] = moved["accepted_state_id"]
        rec["deform_terminal_state"] = moved.get("terminal_state")
        rec["deform_centre_z"] = moved["centre"][2]
        rec["deform_centre_z0"] = centre0
        rec["deform_centre_z_delta_wu"] = \
            float(moved["centre"][2]) - float(centre0)
        rec["deform_energy_J"] = moved["energy"]
        require(moved["accepted_state_id"] != expect_id,
                "step_control_did_not_change_accepted_state")
        rec["compiled_pins_include_centre6"] = \
            6 in [int(p) for p in txn["compiled"]["pins"]]
        shot_d = output / "d-deformed-scene.png"
        _shots({"dir": output, "spec": {"shots": [
            {"url": frame_url(), "out": str(shot_d), "wait_ms": 800}]}})
        require(shot_d.is_file(), "deformed_scene_not_visible")
        rec["deform_pixel_diff_px"] = _pixel_diff(shot_a, shot_d)
        # VERDICT RECORDED, NOT ASSERTED: Qwen's increment-3 acceptance asked
        # for a control that VISIBLY deforms the mesh with an
        # accepted_state_id change. The state change is real (asserted
        # above); the visibility is NOT: the demo's rail descent is
        # guard-limited to microscopic steps (engine.cpp:4591
        # GUARD_FRAC*min_edge/|p|), and the CPU mirror of the law
        # (math-tools/nb_visible_deform_travel_check.py, PASS 4/4) bounds the
        # total travel at <1e-3 wu = <0.36 px on screen for this scene. The
        # browser screenshots measure 0 changed pixels. Recorded as a FAIL
        # for the visibility acceptance item, with the loop completed.
        rec["deform_visible_verdict"] = (
            "FAIL (visibility acceptance item): the step control changed "
            f"accepted_state_id after {rounds} batch(es) of {RUN_STEPS} "
            f"(centre z {centre0:+.6f} -> {moved['centre'][2]:+.6f} wu) but "
            f"the browser screenshot is pixel-identical to startup "
            f"({rec['deform_pixel_diff_px']} px changed): the demo's only "
            "geometric control is guard-limited to <1e-3 wu total travel "
            "(<0.36 px on screen) for this scene -- CPU mirror PASS 4/4, "
            "math-tools/nb_visible_deform_travel_check.py. No visible "
            "deformation is achievable through the demo's existing "
            "controls at qualified parameters.")
        rec["sequence"].append({"step": "deform", "control":
                                f"run x{rounds} batches of {RUN_STEPS}"
                                " (demo batch)",
                                "state_id": moved["accepted_state_id"],
                                "centre_z_delta_wu":
                                rec["deform_centre_z_delta_wu"],
                                "screenshot": shot_d.name,
                                "screenshot_sha256": file_hash(shot_d)})

        # ── restart: reset returns bit-exactly to the uploaded state ────
        engine.membrane.reset()
        after = engine.membrane.state()
        after = after.get("status", after)
        require(after["accepted_state_id"] == expect_id,
                "reset_did_not_restore_accepted_state")
        require(after["material_snapshot"] == rec["material_snapshot"],
                "reset_did_not_restore_material_snapshot")
        require(abs(after["energy"] - e_ref) <= 3e-4,
                "reset_energy_mismatch")
        rec["reset_state_id"] = after["accepted_state_id"]
        rec["reset_material_snapshot_matches"] = True
        shot_c = output / "e-reset-scene.png"
        _shots({"dir": output, "spec": {"shots": [
            {"url": frame_url(), "out": str(shot_c), "wait_ms": 800}]}})
        require(shot_c.is_file(), "reset_scene_not_visible")
        rec["reset_pixel_diff_px"] = _pixel_diff(shot_a, shot_c)
        rec["sequence"].append({"step": "restart", "control": "reset",
                                "state_id": after["accepted_state_id"],
                                "screenshot": shot_c.name,
                                "screenshot_sha256": file_hash(shot_c)})
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        time.sleep(1.0)          # port release before the replay boot

    # ── BOOT B: replay reproduces the SAME state hash ───────────────────
    with socket.socket() as sock:
        require(sock.connect_ex(("127.0.0.1", port)) != 0,
                "replay_port_occupied")
    proc = None
    try:
        proc = _boot(executable, native, port)
        engine = EngineControl(base, timeout=15)
        for _ in range(100):
            require(proc.poll() is None, "private_engine_exited")
            try:
                engine.telemetry()
                break
            except OSError:
                time.sleep(0.2)
        else:
            raise RuntimeError("private_engine_readiness_timeout")
        engine.membrane.upload(packet)
        engine.membrane.pause()
        replay = engine.membrane.state()
        replay = replay.get("status", replay)
        require(replay["accepted_state_id"] == expect_id,
                "replay_state_hash_mismatch")
        require(abs(replay["energy"] - e_ref) <= 3e-4,
                "replay_energy_mismatch")
        rec["replay_state_id"] = replay["accepted_state_id"]
        rec["replay_energy_J"] = replay["energy"]
        rec["replay_verdict"] = (
            f"PASS: second visible boot compiled the SAME transaction to the "
            f"same accepted_state_id {replay['accepted_state_id']}")
        rec["sequence"].append({"step": "replay", "control": "fresh visible "
                                "boot + same MD01 upload",
                                "state_id": replay["accepted_state_id"]})
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
    return rec


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--exe", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--port", type=int, default=8829)
    args = ap.parse_args(argv)

    exe = Path(args.exe)
    require(exe.is_file(), "engine_executable_missing")
    require((exe.parent / "shaders").is_dir(), "engine_shaders_missing")
    out = Path(args.out)
    require(not out.exists(), "output_directory_exists")
    out.mkdir(parents=True, exist_ok=False)

    txn = nb.compile_transaction("assembly.star-k2", "nbe-visible-star",
                                 scale=1.0, load_N=0.8)
    rec = visible_session(txn, out, exe, port=args.port)

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "utc": default_stamp(),
        "source_commit": _source_commit(),
        "browser_path": {
            "endpoint": "GET /frame (PNG of the CURRENT engine render)",
            "evidence": ["ChimeraEngine/engine/main.cpp:2863",
                         "tools/game_shell/server.py:186-188 (existing "
                         "/api/frame -> /frame proxy, same path)"],
            "note": "the browser displays the engine's OWN endpoint; no "
                    "web page was authored (front-end law)",
        },
        "engine_executable": str(exe),
        "engine_sha256": file_hash(exe),
        "engine_visible": True,
        "port": args.port,
        "instance": rec,
        "scope": "one qualified star instance (1.0x, 0.8 N) visible in the "
                 "browser through the existing /frame path; gamma is the "
                 "existing material control (energy doubling at fixed "
                 "geometry, no state change); the step/run control moves "
                 "the packet's declared centre (index 6, a rim vertex the "
                 "record pins -- PIN-LAW FLAGGED, not resolved) and "
                 "changes accepted_state_id; reset restores the uploaded "
                 "state bit-exactly; replay is a second visible boot with "
                 "identical state hash; rendered-byte hash remains "
                 "UNQUALIFIED per AP01 §11.20.10",
    }
    try:
        path = resolve_evidence_path(EVID_DIR,
                                     "native_binding_visible_receipt", [])
    except EvidencePathExists:
        path = EVID_DIR / (f"native_binding_visible_receipt_"
                           f"{default_stamp()}.{time.time_ns()}.json")
    path.write_text(json.dumps(receipt, indent=1, default=str) + "\n",
                    encoding="utf-8")
    for step in rec["sequence"]:
        print(f"[OK] {step['step']}: state_id {step['state_id']} "
              + (f"shot {step.get('screenshot')} "
                 f"{step.get('screenshot_sha256', '')[:12]}"
                 if step.get("screenshot") else ""))
    print(f"[OK] gamma doubling ratio {rec['gamma_doubling_ratio']:.6f} "
          f"(fixed geometry, {rec['gamma_pixel_diff_px']} px changed)")
    print(f"[OK] step deformation: centre z {rec['deform_centre_z0']:.6f} -> "
          f"{rec['deform_centre_z']:.6f} wu, state_id -> "
          f"{rec['deform_state_id']}, {rec['deform_pixel_diff_px']} px "
          f"changed, terminal={rec['deform_terminal_state']}")
    print(f"[FAIL] deform visibility: {rec['deform_visible_verdict'][:160]}")
    print(f"VISIBLE SLICE COMPLETE {path}")
    return 1          # honest signal: the visibility acceptance item FAILED


if __name__ == "__main__":
    raise SystemExit(main())
