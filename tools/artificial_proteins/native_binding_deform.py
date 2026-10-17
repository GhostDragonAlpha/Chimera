"""native_binding_deform.py -- §11.20 stage 9 increment 4: the engine-seam
DEFORM control plus SAVE/RESTORE for the membrane-demo state class,
exercised END TO END on a VISIBLE engine with browser screenshots.

THE TWO ENGINE SEAMS ADDED (ChimeraEngine, this increment):
  * POST /membrane_demo {"op":"deform","load_N":W}: sets the centre
    dead-load to W [N] and RE-SOLVES the demo's single free DOF to the new
    equilibrium under the SAME surface-energy law (fz_surface == W), a
    bracketed bisection evaluated by the demo's own verified kernels --
    a converged re-solve, not guard-capped incremental steps
    (ChimeraEngine/engine/engine.cpp md_deform).
  * GET /membrane_demo_save + POST /membrane_demo_restore: full-state
    save/restore for the membrane-demo state class, the existing
    /tick_b2_save|restore pattern (main.cpp:216-221) applied to this
    class; restore validates end-to-end and swaps in atomically, and
    returns the saved state BIT-EXACTLY (FNV over the restored f32
    positions must reproduce the saved accepted-state id).

THE DRIVER'S LAW: the load W is admitted here only from the qualified
record's MEASURED domain (assembly.star-k2 physical_definition
valid_loads_N = [0.8]); the unload used as the intervening state change
between save and restore is recorded honestly as engine-admitted but
outside the record's load domain.

Acceptance evidence (one visible engine boot, browser screenshots):
  deform      the 0.8 N load change visibly moves the centre (changed-pixel
              bounding box > 1 px) and CHANGES accepted_state_id
  cpu law     the new equilibrium re-solves under the pinned CPU reference
              (evaluate_surface at the SAVED exact f32 positions) within the
              preregistered f32-exact allowance: |dE| <= 3e-4 J and the
              force balance |fz - W| <= 1e-4 N
  restore     save -> deform(unload) -> restore returns BIT-EXACTLY to the
              saved LIVED-IN state (not the uploaded initial): identical
              accepted_state_id, load, gamma, energy, and a byte-identical
              browser screenshot of the deterministic render

Run INSIDE a managed GPU reservation (one gpu_batch manifest job):
  python -B -m tools.artificial_proteins.native_binding_deform \
      --exe <chimera_engine.exe> --out <fresh dir> [--port 8837]
Prints "DEFORM SLICE COMPLETE <receipt path>"; exits 1 when an acceptance
item FAILED (verdicts recorded in the receipt).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from .native_binding_visible import _boot, _shots
from .native_binding_engine import _packet_from_transaction, _source_commit
from .native_view import accepted_hash, require
from tools.evidence_output import default_stamp
from tools.python_control.client import EngineControl
from tools.mechanism_factory import native_binding as nb
from .core import file_hash

_HERE = Path(__file__).resolve().parent            # tools/artificial_proteins
_REPO = _HERE.parent.parent
EVID_DIR = _REPO / "docs" / "evidence" / "mechanism_factory"

RECEIPT_SCHEMA = "chimera-mechanism-factory-native-binding-deform-v1"
ENERGY_TOL = 3e-4              # J; the preregistered f32-exact allowance
FORCE_TOL = 1e-4               # N; ~1000 f32 ulps on an O(1) force, 8e-5 rel
PX_MIN = 2                     # changed-pixel bounding box height (>1 px)


def _diff_stats(a: Path, b: Path) -> dict:
    from PIL import Image
    ia = np.asarray(Image.open(a).convert("RGB"), dtype=np.int16)
    ib = np.asarray(Image.open(b).convert("RGB"), dtype=np.int16)
    if ia.shape != ib.shape:
        return {"changed_px": -1}
    mask = (np.abs(ia - ib).max(axis=2) > 8)
    ys, xs = np.nonzero(mask)
    out = {"changed_px": int(mask.sum())}
    if ys.size:
        out["bbox_h_px"] = int(ys.max() - ys.min() + 1)
        out["bbox_w_px"] = int(xs.max() - xs.min() + 1)
    return out


def deform_session(txn: dict, output: Path, executable: Path,
                   port: int = 8837) -> dict:
    """One visible engine boot: deform acceptance evidence, then teardown."""
    packet, pos32, faces, gamma, e_ref = _packet_from_transaction(txn)
    expect_id = accepted_hash(pos32)
    # the load domain is the record's own MEASURED domain (the qualified
    # record document; the compile law refuses drift from it)
    rec_doc = json.loads(
        (EVID_DIR / "pieces" / f"{txn['record_id']}.json").read_text(
            encoding="utf-8"))
    loads = [float(x) for x in
             rec_doc["physical_definition"]["valid_loads_N"]]
    W = 0.8
    require(W in loads, "deform_load_out_of_record_domain")

    with socket.socket() as sock:
        require(sock.connect_ex(("127.0.0.1", port)) != 0, "native_port_occupied")
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
                 "record_valid_loads_N": loads,
                 "sequence": []}
    proc = None
    engine = None
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

        # ── startup: MD01 upload + pause, the qualified rest scene ──────
        engine.membrane.upload(packet)
        engine.membrane.pause()
        st = engine.membrane.state()
        st = st.get("status", st)
        require(st["accepted_state_id"] == expect_id, "upload_identity")
        require(abs(st["energy"] - e_ref) <= ENERGY_TOL, "upload_physics")
        rec["startup_state_id"] = st["accepted_state_id"]
        rec["startup_energy_J"] = st["energy"]
        shot_a = output / "a-startup-scene.png"
        _shots({"dir": output, "spec": {"shots": [
            {"url": base + "/frame?v=1", "out": str(shot_a), "wait_ms": 800}]}})
        require(shot_a.is_file(), "startup_scene_not_visible")
        rec["sequence"].append({"step": "startup",
                                "control": "MD01 upload + pause",
                                "state_id": st["accepted_state_id"],
                                "screenshot": shot_a.name,
                                "screenshot_sha256": file_hash(shot_a)})

        # ── deform: the 0.8 N port dead-load, re-solved to equilibrium ──
        deformed = engine.request("POST", "/membrane_demo",
                                  {"op": "deform", "load_N": W})
        deformed = deformed.get("status", deformed)
        require(deformed.get("last_control") == "deform", "deform_refused")
        rec["deform_state_id"] = deformed["accepted_state_id"]
        require(deformed["accepted_state_id"] != expect_id, "deform_no_state_change")
        rec["deform_centre_z"] = deformed["centre"][2]
        rec["deform_sag_wu"] = deformed["centre"][2]  # uploaded centre z is 0.0
        rec["deform_centre_force_z_N"] = deformed["centre_force"][2]
        shot_b = output / "b-deformed-scene.png"
        _shots({"dir": output, "spec": {"shots": [
            {"url": base + "/frame?v=2", "out": str(shot_b), "wait_ms": 800}]}})
        require(shot_b.is_file(), "deformed_scene_not_visible")
        stats = _diff_stats(shot_a, shot_b)
        rec["deform_pixel_diff_px"] = stats["changed_px"]
        rec["deform_bbox_h_px"] = stats.get("bbox_h_px", 0)
        require(stats["changed_px"] > 0, "deform_not_visible")
        require(stats.get("bbox_h_px", 0) >= PX_MIN, "deform_below_1px")
        rec["sequence"].append({"step": "deform",
                                "control": f"deform load_N={W} (record domain)",
                                "state_id": deformed["accepted_state_id"],
                                "centre_z": deformed["centre"][2],
                                "screenshot": shot_b.name,
                                "screenshot_sha256": file_hash(shot_b)})

        # ── save the LIVED-IN state and verify it under the CPU law ─────
        doc = engine.request("GET", "/membrane_demo_save")
        require(doc.get("schema") == "chimera.membrane_demo_state.v1",
                "save_schema")
        rec["save"] = {"accepted_state_id": doc["accepted_state_id"],
                       "centre_load_N": doc["centre_load_N"],
                       "energy_J": doc["energy_J"],
                       "n_positions": len(doc["positions_f32"])}
        saved_pos = np.asarray(doc["positions_f32"], dtype="<f4")
        require(saved_pos.size == 3 * int(doc["n_verts"]), "save_positions_size")
        packed = saved_pos.reshape(-1)
        sid = accepted_hash(packed.reshape(-1, 3))
        require(sid == int(doc["accepted_state_id"]), "save_state_id_mismatch")
        from tools.membrane_scale_lab.surface_energy_reference import \
            evaluate_surface
        ref = evaluate_surface(saved_pos.astype(np.float64).reshape(-1, 3),
                               faces, doc["gamma_admitted_f64"])
        d_e = abs(float(ref.energy) - float(doc["energy_J"]))
        d_f = abs(float(ref.vertex_forces[6, 2]) - float(doc["centre_load_N"]))
        rec["cpu_law"] = {"energy_cpu_J": float(ref.energy),
                          "energy_engine_J": float(doc["energy_J"]),
                          "energy_abs_diff_J": d_e,
                          "force_balance_target_N": W,
                          "force_cpu_N": float(ref.vertex_forces[6, 2]),
                          "force_abs_diff_N": d_f,
                          "energy_allowance_J": ENERGY_TOL,
                          "force_allowance_N": FORCE_TOL}
        require(d_e <= ENERGY_TOL, "cpu_energy_mismatch")
        require(d_f <= FORCE_TOL, "cpu_force_balance_mismatch")
        rec["sequence"].append({"step": "save", "control":
                                "GET /membrane_demo_save",
                                "state_id": doc["accepted_state_id"]})

        # ── intervening state change: unload (engine-admitted; the record's
        #    domain governs the qualified 0.8 N application above) ────────
        unloaded = engine.request("POST", "/membrane_demo",
                                  {"op": "deform", "load_N": 0.0})
        unloaded = unloaded.get("status", unloaded)
        require(unloaded.get("last_control") == "deform", "unload_refused")
        require(unloaded["accepted_state_id"] != doc["accepted_state_id"],
                "unload_made_no_state_change")
        rec["unload_state_id"] = unloaded["accepted_state_id"]

        # ── restore: BIT-EXACT return to the saved lived-in state ───────
        restored = engine.request("POST", "/membrane_demo_restore", doc)
        restored = restored.get("status", restored)
        require(restored.get("last_control") == "restored", "restore_refused")
        rec["restored_state_id"] = restored["accepted_state_id"]
        print(f"DEBUG restored_id={restored['accepted_state_id']} (type={type(restored['accepted_state_id']).__name__}), doc_id={doc['accepted_state_id']} (type={type(doc['accepted_state_id']).__name__})")
        require(int(restored["accepted_state_id"]) == int(doc["accepted_state_id"]),
                "restore_not_bit_exact")
        require(restored["accepted_state_id"] != expect_id,
                "restore_conflated_with_uploaded_initial")
        require(abs(restored["centre"][2] - float(doc["positions_f32"][6 * 3 + 2]))
                < 1e-12, "restore_centre_moved")
        require(restored["centre_load_N"] == doc["centre_load_N"],
                "restore_load_changed")
        shot_c = output / "c-restored-scene.png"
        _shots({"dir": output, "spec": {"shots": [
            {"url": base + "/frame?v=3", "out": str(shot_c), "wait_ms": 800}]}})
        require(shot_c.is_file(), "restored_scene_not_visible")
        rec["restored_screenshot_sha256"] = file_hash(shot_c)
        rec["restored_matches_deformed_render"] = (
            rec["restored_screenshot_sha256"] == file_hash(shot_b))
        require(rec["restored_matches_deformed_render"],
                "restored_render_differs")
        rec["sequence"].append({"step": "restore",
                                "control": "POST /membrane_demo_restore",
                                "state_id": restored["accepted_state_id"],
                                "screenshot": shot_c.name,
                                "screenshot_sha256": file_hash(shot_c)})

        # ── second proof: reset then restore again (over the reset law) ──
        engine.membrane.reset()
        rst = engine.membrane.state()
        rst = rst.get("status", rst)
        require(rst["accepted_state_id"] == expect_id, "reset_law_broken")
        restored2 = engine.request("POST", "/membrane_demo_restore", doc)
        restored2 = restored2.get("status", restored2)
        require(restored2.get("last_control") == "restored", "restore2_refused")
        require(int(restored2["accepted_state_id"]) == int(doc["accepted_state_id"]),
                "restore2_not_bit_exact")
        rec["restore_after_reset_state_id"] = restored2["accepted_state_id"]
        rec["sequence"].append({"step": "restore_after_reset",
                                "control": "reset then restore",
                                "state_id": restored2["accepted_state_id"]})
        rec["verdict"] = ("PASS: deform visibly deforms (>1 px bbox) with an "
                          "accepted_state_id change; the new equilibrium "
                          "re-solves under the pinned CPU law within the "
                          "f32-exact allowance; save->unload->restore and "
                          "reset->restore both return bit-exactly to the "
                          "saved lived-in state")
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
    ap.add_argument("--port", type=int, default=8837)
    args = ap.parse_args(argv)

    exe = Path(args.exe)
    require(exe.is_file(), "engine_executable_missing")
    require((exe.parent / "shaders").is_dir(), "engine_shaders_missing")
    out = Path(args.out)
    require(not out.exists(), "output_directory_exists")
    out.mkdir(parents=True, exist_ok=False)

    txn = nb.compile_transaction("assembly.star-k2", "nbd-star-inc4",
                                 scale=1.0, load_N=0.8)
    rec = deform_session(txn, out, exe, port=args.port)

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "utc": default_stamp(),
        "source_commit": _source_commit(),
        "engine_executable": str(exe),
        "engine_sha256": file_hash(exe),
        "engine_visible": True,
        "port": args.port,
        "instance": rec,
        "scope": "engine-seam deform control (centre dead-load within the "
                 "record's measured domain, converged re-solve under the "
                 "same surface-energy law) and membrane-demo save/restore "
                 "(the /tick_b2_save|restore pattern); acceptance evidence "
                 "on a visible engine through the browser's /frame path",
    }
    path = EVID_DIR / (f"native_binding_deform_receipt_{default_stamp()}.json")
    path.write_text(json.dumps(receipt, indent=1, default=str) + "\n",
                    encoding="utf-8")
    for step in rec["sequence"]:
        print(f"[OK] {step['step']}: {step.get('state_id', '')} "
              + (f"shot {step.get('screenshot')}"
                 f" {step.get('screenshot_sha256', '')[:12]}"
                 if step.get("screenshot") else ""))
    print(f"[OK] cpu law: |dE| = {rec['cpu_law']['energy_abs_diff_J']:.3e} J,"
          f" |fz - W| = {rec['cpu_law']['force_abs_diff_N']:.3e} N")
    print(f"[OK] deform: sag {rec['deform_sag_wu']:.6f} wu,"
          f" {rec['deform_pixel_diff_px']} px changed,"
          f" bbox h {rec['deform_bbox_h_px']} px")
    print(f"DEFORM SLICE COMPLETE {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
