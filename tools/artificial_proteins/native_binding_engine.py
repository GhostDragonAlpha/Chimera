"""native_binding_engine.py -- §11.20 stage 9 increment 2: compile a
QUALIFIED piece-record transaction (tools/mechanism_factory/native_binding.py)
into the EXISTING private native engine through the EXISTING capture law
(tools/artificial_proteins/native_view.py: private-port probe, executable +
shader copy into a private output dir, EngineControl readiness poll, MD01
packet upload, pause, physics/identity verification, frame capture).

REUSE, NOT FORK: native_view.py is imported and left byte-identical (its
hashes are pinned by completed AP01 evidence); this sibling re-plays the
same capture law parameterized by a compile transaction instead of an AP01
recipe. No new engine endpoint is called and none is invented.

SAVE/RESTORE SCOPE (reported honestly, not worked around): the membrane-demo
state class has NO save/restore control. Its only POST ops are
reset|step|run|pause|gamma|reject (ChimeraEngine/engine/main.cpp:1199-1213);
the engine's only save/restore endpoints, /tick_b2_save and
/tick_b2_restore (main.cpp:216-221), own the B2 assembly scene class, a
different state class; the session snapshot list k_snapshot_endpoints
(main.cpp:292-302) carries no membrane_demo blob. The ONLY existing restore
for this state class is ctl kind 0 "reset" -- bit-exact restoration of the
UPLOADED INITIAL state (engine.cpp:4781-4798). This module exercises that
existing control end to end (material change -> reset -> accepted_state_id,
material snapshot and energy return bit-exactly) and RECORDS the missing
save/restore as a gap instead of building a parallel path.

Physics allowance (preregistered): |E_engine - E_ref| <= 3e-4 J, where
E_ref is the pinned law evaluated on the EXACT f32-rounded uploaded
positions promoted to f64 (the engine's own arithmetic is f32). The AP01
native check used 3e-5 J on fans with E ~ O(1) (relative ~3e-5); the star
and patch rest energies are ~6.3 J, so the same relative strictness gives
~3e-4 J -- about 200x the AP01-measured f32-vs-f64 normalized worst
mismatch (2.5e-7). Identity law: the engine's accepted_state_id must equal
the documented accepted-hash of the uploaded f32 positions (native_view's
accepted_hash, the engine's documented FNV seed).

Run (inside a managed GPU reservation -- one gpu_batch manifest job):
  python -B -m tools.artificial_proteins.native_binding_engine \
      --exe <chimera_engine.exe> --out <fresh dir> [--port 8829]
Prints "ALL GREEN <receipt path>" and exits 0 on success.
"""
from __future__ import annotations

import argparse
import json
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from .native_view import accepted_hash, require
from tools.evidence_output import (EvidencePathExists, default_stamp,
                                   resolve_evidence_path)
from tools.membrane_demo_client import md01_packet
from tools.python_control.client import EngineControl
from tools.mechanism_factory import native_binding as nb
from .core import file_hash
from tools.membrane_scale_lab.surface_energy_reference import evaluate_surface

_HERE = Path(__file__).resolve().parent            # tools/artificial_proteins
_REPO = _HERE.parent.parent
EVID_DIR = _REPO / "docs" / "evidence" / "mechanism_factory"

RECEIPT_SCHEMA = "chimera-mechanism-factory-native-binding-engine-v1"
ENERGY_TOL = 3e-4          # J; preregistered above (AP01-relative law)
GAMMA_PROBE = 1.5          # existing 'gamma' control: a state change to undo

SAVE_RESTORE_GAP = {
    "verdict": "GAP: no save/restore control exists for the membrane-demo "
               "state class; none built (increment law)",
    "evidence": [
        "ChimeraEngine/engine/main.cpp:1199-1213: POST /membrane_demo ops "
        "are reset|step|run|pause|gamma|reject only -- no save and no "
        "restore-of-a-saved-state op",
        "ChimeraEngine/engine/main.cpp:216-221: /tick_b2_save and "
        "/tick_b2_restore exist ONLY for the B2 assembly scene class "
        "(g_tick), not for the uploaded membrane demo state (g_md_*)",
        "ChimeraEngine/engine/main.cpp:292-302: the session snapshot list "
        "k_snapshot_endpoints carries no membrane_demo blob, so the boot "
        "restore (R-restore-doctor) cannot restore this state class",
        "ChimeraEngine/engine/engine.cpp:4781-4798: the only existing "
        "restore for this class is ctl kind 0 'reset' -- bit-exact "
        "restoration of the UPLOADED INITIAL state; exercised below",
    ],
}


def _source_commit() -> str:
    import subprocess
    try:
        out = subprocess.run(["git", "-C", str(_REPO), "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=30,
                             check=True)
        return out.stdout.strip() or "UNTRACKED"
    except Exception:                                  # pragma: no cover
        return "UNTRACKED"


def _packet_from_transaction(txn: dict) -> tuple:
    """MD01 packet + f32-exact CPU reference for one compile transaction."""
    require(txn.get("schema") == nb.BINDING_SCHEMA, "transaction_schema")
    require(txn["transaction_hash"] == nb.transaction_hash(txn),
            "transaction_hash_mismatch")
    comp = txn["compiled"]
    pos64 = np.frombuffer(bytes.fromhex(comp["positions_f64"]),
                          dtype="<f8").reshape(-1, 3)
    faces = np.asarray(comp["faces"], dtype=np.int64)
    gamma64 = np.asarray(comp["gamma"], dtype=np.float64)
    require(int(pos64.shape[0]) == comp["n_vertices"], "vertex_count")
    require(len(comp["csr_off"]) == pos64.shape[0] + 1, "csr_offsets")
    require(len(comp["csr_cor"]) == faces.shape[0] * 3, "csr_corners")
    # the demo admits ONE uniform gamma (its material snapshot is scalar)
    require(float(gamma64.min()) == float(gamma64.max()), "gamma_not_uniform")
    gamma = float(gamma64[0])
    # the engine receives f32; the CPU reference evaluates the EXACT f32-
    # rounded geometry promoted to f64 (the AP01 comparison law)
    pos32 = pos64.astype("<f4")
    ref = evaluate_surface(pos32.astype(np.float64), faces, gamma)
    packet = {
        "pos": pos32.reshape(-1),
        "idx": faces.astype("<u4").reshape(-1),
        "csr_off": np.asarray(comp["csr_off"], dtype="<u4").reshape(-1),
        "csr_cor": np.asarray(comp["csr_cor"], dtype="<u4").reshape(-1),
        "gamma_face": gamma64.astype("<f4").reshape(-1),
    }
    return md01_packet(packet, gamma), pos32, faces, gamma, float(ref.energy)


def capture_transactions(txns: list, output: Path, executable: Path,
                         port: int = 8829) -> list:
    """Compile a list of transactions into ONE private-engine session
    (the native_view.capture law: one private engine, all instances
    through it), and return per-instance evidence records."""
    with socket.socket() as sock:
        require(sock.connect_ex(("127.0.0.1", port)) != 0,
                "native_port_occupied")
    executable = executable.resolve()
    native = output / "native"
    native.mkdir(exist_ok=False)
    shutil.copy2(executable, native / executable.name)
    shutil.copytree(executable.parent / "shaders", native / "shaders")

    records = []
    proc = None
    try:
        with (native / "stdout.log").open("wb") as out, \
                (native / "stderr.log").open("wb") as err:
            proc = subprocess.Popen(
                [str(native / executable.name), str(port), "--hidden",
                 "1280", "720", "--no-restore"], cwd=native, stdout=out,
                stderr=err,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            engine = EngineControl(f"http://127.0.0.1:{port}", timeout=15)
            for _ in range(100):
                require(proc.poll() is None, "private_engine_exited")
                try:
                    engine.telemetry()
                    break
                except OSError:
                    time.sleep(0.2)
            else:
                raise RuntimeError("private_engine_readiness_timeout")
            tele = engine.telemetry()
            chrome = (sorted(tele.keys()) if isinstance(tele, dict)
                      else {"raw": str(tele)[:400]})

            for txn in txns:
                packet, pos32, faces, gamma, e_ref = \
                    _packet_from_transaction(txn)
                expect_id = accepted_hash(pos32)
                rec = {"instance_id": txn["instance_id"],
                       "record_id": txn["record_id"],
                       "transaction_hash": txn["transaction_hash"],
                       "n_vertices": int(pos32.shape[0]),
                       "n_faces": int(faces.shape[0]),
                       "gamma_admitted": gamma,
                       "accepted_hash_wu": expect_id}

                # ── compile the transaction into the engine (MD01 upload) ──
                engine.membrane.upload(packet)
                engine.membrane.pause()
                status = engine.membrane.state()
                status = status.get("status", status)
                require(status["accepted_state_id"] == expect_id,
                        "native_upload_identity_mismatch")
                diff = abs(status["energy"] - e_ref)
                require(diff <= ENERGY_TOL, "native_binding_physics_mismatch")
                rec["engine_accepted_state_id"] = status["accepted_state_id"]
                rec["energy_engine_J"] = status["energy"]
                rec["energy_reference_J"] = e_ref
                rec["energy_abs_diff_J"] = diff
                rec["energy_initial_J"] = status["energy_initial"]
                rec["material_snapshot_uploaded"] = status["material_snapshot"]

                # ── rendered-byte capture (hashes recorded, NOT claimed
                #    equal: this native build leaves the rendered-byte hash
                #    unqualified per AP01 §11.20.10) ─────────────────────
                engine.request("POST", "/camera",
                               {"cam_radius": 4.0, "cam_theta": 0.4,
                                "cam_phi": 0.6})
                frame = engine.frame()
                rendered = engine.membrane.state()
                rendered = rendered.get("status", rendered)
                require(rendered["accepted_state_id"] == expect_id,
                        "native_state_changed_during_capture")
                rec["render_state_id"] = rendered["render_state_id"]
                name = f"{txn['instance_id']}-native.png"
                (output / name).write_bytes(frame)
                rec["capture"] = name
                rec["capture_sha256"] = file_hash(output / name)

                # ── the ONLY existing restore control for this class ──
                # (a) a real state change: admitted gamma moved off upload
                engine.membrane.tension(GAMMA_PROBE)
                moved = engine.membrane.state()
                moved = moved.get("status", moved)
                rec["gamma_probe_material_snapshot"] = \
                    moved["material_snapshot"]
                require(moved["material_snapshot"]
                        != rec["material_snapshot_uploaded"],
                        "gamma_probe_made_no_state_change")
                # (b) an attempted relaxation step (evidence, not asserted
                #     to move: the fan rest geometry may be stationary)
                engine.membrane.step(1)
                stepped = engine.membrane.state()
                stepped = stepped.get("status", stepped)
                rec["stepped_accepted_state_id"] = \
                    stepped["accepted_state_id"]
                rec["stepped_moved"] = (stepped["accepted_state_id"]
                                        != expect_id)
                # (c) reset: bit-exact return to the UPLOADED initial state
                engine.membrane.reset()
                after = engine.membrane.state()
                after = after.get("status", after)
                require(after["accepted_state_id"] == expect_id,
                        "reset_did_not_restore_accepted_state")
                require(after["material_snapshot"]
                        == rec["material_snapshot_uploaded"],
                        "reset_did_not_restore_material_snapshot")
                require(abs(after["energy"] - e_ref) <= ENERGY_TOL,
                        "reset_energy_mismatch")
                rec["reset_verdict"] = \
                    "PASS: bit-exact restore of the uploaded initial " \
                    "state (engine.cpp:4781 law)"
                rec["telemetry_keys"] = chrome
                records.append(rec)
        return records
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--exe", required=True, help="existing private engine exe")
    ap.add_argument("--out", required=True, help="FRESH output directory")
    ap.add_argument("--port", type=int, default=8829)
    args = ap.parse_args(argv)

    exe = Path(args.exe)
    require(exe.is_file(), "engine_executable_missing")
    require((exe.parent / "shaders").is_dir(), "engine_shaders_missing")
    out = Path(args.out)
    require(not out.exists(), "output_directory_exists")
    out.mkdir(parents=True, exist_ok=False)

    instances = [
        nb.compile_transaction("assembly.star-k2", "nbe-star-inc2",
                               scale=1.0, load_N=0.8),
        nb.compile_transaction("piece.patch-equilibrium", "nbe-piece-inc2",
                               scale=1.0, load_N=0.8),
    ]
    records = capture_transactions(instances, out, exe, port=args.port)

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "utc": default_stamp(),
        "source_commit": _source_commit(),
        "engine_executable": str(exe),
        "engine_sha256": file_hash(exe),
        "shader_hashes": {str(p.relative_to(out / "native")): file_hash(p)
                          for p in (out / "native" / "shaders").rglob("*.spv")},
        "port": args.port,
        "energy_allowance_J": ENERGY_TOL,
        "instances": records,
        "save_restore": SAVE_RESTORE_GAP,
        "scope": "compiled transaction accepted by the private engine with "
                 "identity + energy verified at the uploaded f32 geometry; "
                 "reset (the only existing restore control) round-trips "
                 "bit-exactly; rendered-byte hash remains UNQUALIFIED (AP01 "
                 "§11.20.10); no save/restore control exists for this state "
                 "class and none was built",
    }
    try:
        path = resolve_evidence_path(EVID_DIR,
                                     "native_binding_engine_receipt", [])
    except EvidencePathExists:
        # same-second stamp collision: take a NEW name, never overwrite
        path = EVID_DIR / (f"native_binding_engine_receipt_"
                           f"{default_stamp()}.{time.time_ns()}.json")
    path.write_text(json.dumps(receipt, indent=1, default=str) + "\n",
                    encoding="utf-8")
    for r in records:
        print(f"[OK] {r['instance_id']}: accepted_state_id "
              f"{r['engine_accepted_state_id']} == accepted_hash, "
              f"|dE| = {r['energy_abs_diff_J']:.3e} J, "
              f"reset {r['reset_verdict']}")
    print(f"ALL GREEN {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
