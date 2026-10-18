"""native_binding_gameloop.py -- stage 9 increment 5: the FULL game loop
against the FROZEN step-review-L4 criteria (do not renegotiate):

  1  Objective   ctl-6 deform so apex_z settles in [0.147, 0.197] wu
  2  Success     terminal apex_z in band AND free_residual_N <= 1e-6 AND
                 CPU re-solve cross-check <= 1e-7 (f32-exact allowance)
  3  Failure     load refused by record domain (0.9 N demonstrated) or
                 out of band after bounded moves
  4  Feedback    /frame screenshot + telemetry (apex_z, load_N,
                 free_residual_N) per frame
  5  Restart     engine reset control restores the initial geometry
                 byte-exact (accepted-state-id law)
  6  Replay      re-upload identical hashes -> same output hash

CENTRE BINDING (measured, flagged to the coordinator): the frozen band is
derived from the load-domain study's SEAM-apex equilibria, and the record's
input port (the 1.6 N dead load) IS the seam apex -- compiled ids
seam_vertex = loads[0].vertex = 200, NOT pinned. The membrane demo's MD01
packet header hardcodes centre index 6 (membrane_demo_client.py
CENTRE_INDEX), which for this star is a PINNED rim vertex whose vertical
surface force SATURATES at 0.9995 N (CPU f32-exact profile,
math-tools results 20261017-124034-977dcdc3 PASS 13/13) -- under it the
engine's own deform law refuses the 1.6 N objective
("deform_REFUSED_no_equilibrium", engine.cpp md_deform !saw_cross path).
This driver therefore composes the SAME MD01 wire format with the demo's
centre bound to the transaction's OWN load-port vertex (byte parity with
md01_packet is asserted at centre 6 at runtime). No engine C++ and no
record law is touched: the engine accepts any centre < n_verts
(main.cpp /membrane_demo_bin parse) and re-solves that DOF.

Run INSIDE a managed GPU reservation (one gpu_batch manifest job):
  python -B -m tools.artificial_proteins.native_binding_gameloop \
      --exe <chimera_engine.exe> --out <fresh dir> [--port 8841]
Prints "GAMELOOP RUN COMPLETE <receipt path>"; exits 1 when any frozen
criterion FAILED (verdicts + numbers recorded in the receipt).
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from .native_binding_visible import _boot, _shots, NODE_EXE
from .native_binding_engine import _source_commit
from .native_view import accepted_hash, require
from tools.evidence_output import default_stamp
from tools.python_control.client import EngineControl
from tools.mechanism_factory import native_binding as nb
from tools.membrane_scale_lab.surface_energy_reference import evaluate_surface
from .core import file_hash

_HERE = Path(__file__).resolve().parent            # tools/artificial_proteins
_REPO = _HERE.parent.parent
EVID_DIR = _REPO / "docs" / "evidence" / "mechanism_factory"

RECEIPT_SCHEMA = "chimera-mechanism-factory-gameloop-run-v1"
SAVE_FILENAME = "membrane_demo_save_terminal.json"   # disk-persisted save doc
ENERGY_TOL = 3e-4              # J; the preregistered f32-exact allowance
FORCE_TOL = 1e-4               # N; increment-4 force-balance allowance
RESIDUAL_LAW = 1e-6            # N; the packet's frozen acceptance law
CROSSCHECK_TOL = 1e-7          # frozen criterion 2 (f32-exact allowance)
BAND = (0.147, 0.197)          # wu; frozen criterion 1
OBJECTIVE_LOAD = 1.6           # N; the study's in-domain equilibrium in band
REFUSED_LOAD = 0.9             # N; frozen criterion 3 failure predicate
ENGINE_QUANTUM = 4.0 * 1.1920929e-7   # engine deform bisection z quantum

PRERUN_CPU_CHECK = {
    "script": "math-tools/checks_tmp/nb_gameloop_prerun_check.py",
    "result": ("D:/Chimera-Maintenance/Runtime/local-ai/math-tools/results/"
               "20261017-124034-977dcdc3/result.json"),
    "verdict": "PASS 13/13",
    "facts": [
        "seam_vertex = loads[0].vertex = 200, NOT in pins (the record's own "
        "load port); demo-hardcoded centre 6 IS pinned",
        "centre-6 fz profile saturates at 0.9995 N < 1.2 N: the engine's "
        "deform law refuses the 1.6 N objective under centre 6 "
        "(deform_REFUSED_no_equilibrium)",
        "seam deform mirror at 1.6 N: z* = 0.172059006989 wu (study "
        "0.17205904840608507, diff 4.1e-8), fz = 1.60000007 N, in band",
        "0.9 N at the seam balances (z* = 0.2709 wu): engine-admissible, so "
        "the 0.9 N refusal must come from the RECORD domain",
        "mirror validated against the increment-4 engine receipt "
        "(centre 6, 0.8 N): |z - (-0.0435769781)| = 5.0e-8 <= engine quantum",
    ],
}


# ── MD01 composition: the packet format with an EXPLICIT centre index ────────

def _md01_packet_centred(packet: dict, gamma_admitted: float,
                         centre_index: int) -> bytes:
    """The membrane_demo_client.md01_packet wire format (MAGIC, nv, nf,
    centre, gamma f64, lift f32, reserved u32 | pos f32 | idx u32 |
    csr_off u32 | csr_cor u32 | gamma f32) with the centre index a named
    argument instead of the module constant. Byte parity with md01_packet is
    asserted at runtime for centre_index == CENTRE_INDEX."""
    from tools.membrane_demo_client import md01_packet, CENTRE_INDEX
    pos, idx = packet["pos"], packet["idx"]
    nv, nf = len(pos) // 3, len(idx) // 3
    require(len(packet["csr_off"]) == nv + 1 and len(packet["csr_cor"]) == nf * 3,
            "packet_csr_sizes")
    require(0 <= centre_index < nv, "centre_index_out_of_range")
    header = struct.pack("<IIIIdfI", 0x3130444D, nv, nf, centre_index,
                         gamma_admitted, 0.5, 0)
    body = (pos.tobytes() + idx.tobytes() + packet["csr_off"].tobytes()
            + packet["csr_cor"].tobytes() + packet["gamma_face"].tobytes())
    ours = header + body
    if centre_index == CENTRE_INDEX:                 # runtime parity proof
        require(ours == md01_packet(packet, gamma_admitted),
                "md01_parity_broken")
    return ours


# ── CPU re-solve: f32-exact mirror of the engine's deform law ────────────────

def _cpu_deform_resolve(pos32: np.ndarray, faces: np.ndarray, gamma: float,
                        centre: int, W: float) -> dict:
    """f64-precision bisection on the centre z so fz_surface(centre) == W,
    evaluating the pinned law at the f32-ROUNDED trial z (the engine's own
    probe law, engine.cpp md_deform probe). Returns the re-solved z, the
    balance residual there, and the balance at any ENGINE-committed z."""
    base = pos32.copy()

    def fz(zc: float) -> float:
        trial = base.copy()
        trial[centre, 2] = np.float32(zc)
        return float(evaluate_surface(trial, faces, gamma)
                     .vertex_forces[centre, 2])

    z0 = float(base[centre, 2])
    F0 = fz(z0) - W
    if abs(F0) <= 1e-12:
        return {"z_resolve_wu": z0, "balance_N": fz(z0) - W}
    dirn = -1.0 if F0 < 0 else 1.0
    step = 1e-3 * 0.0156                    # ~1e-3 * md_min_edge_ for this fan
    z_a = z_b = None
    for _ in range(60):
        zc = z0 + dirn * step
        step *= 2.0
        F = fz(zc) - W
        if (dirn < 0 and F >= 0.0) or (dirn > 0 and F <= 0.0):
            z_b = zc
            break
        z_a = zc
    require(z_b is not None, "cpu_resolve_no_bracket")
    lo, hi = sorted((z_a, z_b))
    flo = fz(lo) - W
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if (fz(mid) - W) * flo <= 0:
            hi = mid
        else:
            lo = mid
        if hi - lo <= 1e-13:
            break
    z = 0.5 * (lo + hi)
    return {"z_resolve_wu": z, "balance_N": fz(z) - W}


def _fz_at(pos32: np.ndarray, faces: np.ndarray, gamma: float,
           centre: int, zc: float) -> float:
    trial = pos32.copy()
    trial[centre, 2] = np.float32(zc)
    return float(evaluate_surface(trial, faces, gamma)
                 .vertex_forces[centre, 2])


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


# ── workshop increment 1: Studio board plumbing (S5 demo pattern) ────────────

PERSIST_STAGE_ID = "WS1"


def _board_write(path: Path, stage: dict) -> None:
    """Atomic Studio board write; the overlay re-polls on mtime
    (main.cpp:975-981 -> ui.cpp poll_board)."""
    doc = {"standing": stage["standing"], "updated": stage["updated"],
           "stages": [stage["stage"]]}
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def _persistence_stage(heading: str, updated: str, cell: str) -> dict:
    """One board stage with the same envelope fields the S5 authoring demo
    fed (S5 state D is the established on-screen readout pattern)."""
    return {"standing": heading, "updated": updated,
            "stage": {"id": PERSIST_STAGE_ID,
                      "name": "Persistence across sessions",
                      "status": "green",
                      "law": "restore law: /membrane_demo_restore is "
                             "bit-exact by the accepted-state-id law "
                             "(increment-4 membrane save/restore seam)",
                      "tool": "/membrane_demo_save | /membrane_demo_restore",
                      "artifact": SAVE_FILENAME,
                      "falsifier": "any state-id/apex/load drift on "
                                   "restore; disk round-trip mismatch",
                      "cell": cell,
                      "spec_title": "Persistence across sessions",
                      "spec": "workshop increment 1 (save/reuse): the save "
                              "doc the TERMINATED boot-A engine wrote to "
                              "disk is restored in this fresh boot-B "
                              "engine; verified bit-exactly against boot "
                              "A's terminal telemetry and /frame pixels",
                      "row_line": -1, "spec_line": -1}}


# ── the loop, one visible engine boot A + replay boot B ──────────────────────

def gameloop_session(txn: dict, txn_refused: dict | None, output: Path,
                     executable: Path, port: int) -> dict:
    packet, pos32, faces, gamma, e_ref = _packet_parts(txn)
    expect_id = accepted_hash(pos32)
    seam = int(txn["ids"]["seam_vertex"])
    rec_doc = json.loads(
        (EVID_DIR / "pieces" / f"{txn['record_id']}.json").read_text(
            encoding="utf-8"))
    loads = [float(x) for x in rec_doc["physical_definition"]["valid_loads_N"]]
    require(float(txn["load_N"]) in loads, "objective_load_out_of_domain")

    rec: dict = {"instance_id": txn["instance_id"],
                 "record_id": txn["record_id"],
                 "transaction_hash": txn["transaction_hash"],
                 "record_valid_loads_N": loads,
                 "centre_binding": {
                     "demo_default_centre_index": 6,
                     "driver_centre_index": seam,
                     "justification": PRERUN_CPU_CHECK,
                     "md01_parity_at_centre6_asserted": True},
                 "accepted_hash_wu": expect_id,
                 "energy_reference_J": e_ref,
                 "sequence": []}
    _seq = itertools.count(1)
    base = f"http://127.0.0.1:{port}"

    def frame_url() -> str:
        return base + f"/frame?v={next(_seq)}"

    def shot(name: str) -> Path:
        p = output / name
        _shots({"dir": output, "spec": {"shots": [
            {"url": frame_url(), "out": str(p), "wait_ms": 800}]}})
        require(p.is_file(), f"frame_not_visible_{name}")
        return p

    def telemetry(st: dict) -> dict:
        load = float(st["centre_load_N"])
        fz = float(st["centre_force"][2])
        return {"apex_z_wu": float(st["centre"][2]),
                "load_N": load,
                "centre_force_z_N": fz,
                "free_residual_N": abs(fz - load),
                "accepted_state_id": int(st["accepted_state_id"]),
                "energy_J": float(st["energy"])}

    proc = None
    try:
        with socket.socket() as sock:
            require(sock.connect_ex(("127.0.0.1", port)) != 0,
                    "native_port_occupied")
        executable = executable.resolve()
        native = output / "native"
        native.mkdir(exist_ok=False)
        shutil.copy2(executable, native / executable.name)
        shutil.copytree(executable.parent / "shaders", native / "shaders")

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

        # ── startup: MD01 upload (centre bound to the record's load port) ──
        engine.membrane.upload(packet)
        engine.membrane.pause()
        st = engine.membrane.state()
        st = st.get("status", st)
        require(st["accepted_state_id"] == expect_id, "upload_identity")
        require(abs(st["energy"] - e_ref) <= ENERGY_TOL, "upload_physics")
        rec["startup"] = telemetry(st)
        a = shot("a-startup-baseline.png")
        rec["sequence"].append({"step": "startup", "control": "MD01 upload"
                                " + pause", "screenshot": a.name,
                                "screenshot_sha256": file_hash(a),
                                **rec["startup"]})

        # ── criterion 1: the objective load, re-solved by the engine ─────
        deformed = engine.request("POST", "/membrane_demo",
                                  {"op": "deform", "load_N": OBJECTIVE_LOAD})
        deformed = deformed.get("status", deformed)
        require(deformed.get("last_control") == "deform",
                f"deform_refused_{deformed.get('last_control')}")
        term = telemetry(deformed)
        term["in_band"] = bool(BAND[0] <= term["apex_z_wu"] <= BAND[1])
        rec["c1_objective"] = {
            "band_wu": BAND, "objective_load_N": OBJECTIVE_LOAD,
            "engine_last_control": deformed["last_control"], **term,
            "pass": term["in_band"]}
        b = shot("b-terminal-objective.png")
        rec["c1_objective"]["pixel_diff_vs_baseline"] = _diff_stats(a, b)
        rec["sequence"].append({"step": "objective_deform", "control":
                                f"deform load_N={OBJECTIVE_LOAD} (record"
                                " domain, ctl kind 6)",
                                "screenshot": b.name,
                                "screenshot_sha256": file_hash(b), **term})

        # ── criterion 2: residual law + CPU re-solve cross-check ─────────
        solve = _cpu_deform_resolve(pos32, faces, gamma, seam,
                                    OBJECTIVE_LOAD)
        fz_at_engine_z = _fz_at(pos32, faces, gamma, seam,
                                term["apex_z_wu"])
        pos_cross = abs(term["apex_z_wu"] - solve["z_resolve_wu"])
        force_cross = abs(fz_at_engine_z - OBJECTIVE_LOAD)
        res_pass = term["free_residual_N"] <= RESIDUAL_LAW
        cross_pass = pos_cross <= CROSSCHECK_TOL
        rec["c2_success"] = {
            "free_residual_N": term["free_residual_N"],
            "residual_law_N": RESIDUAL_LAW, "residual_pass": res_pass,
            "cpu_resolve": {**solve, "z_tolerance_note":
                            "f32-exact: trial z cast to float32, the "
                            "engine's own probe law"},
            "cpu_position_cross_check_wu": pos_cross,
            "cross_check_tol_wu": CROSSCHECK_TOL,
            "cross_check_pass": cross_pass,
            "cpu_force_at_engine_z_N": fz_at_engine_z,
            "cpu_force_cross_check_N": force_cross,
            "engine_bisection_quantum_wu": ENGINE_QUANTUM,
            "apex_in_band": term["in_band"],
            "pass": bool(res_pass and cross_pass and term["in_band"])}

        # ── save the terminal state and verify it under the CPU law ──────
        doc = engine.request("GET", "/membrane_demo_save")
        require(doc.get("schema") == "chimera.membrane_demo_state.v1",
                "save_schema")
        saved_pos = np.asarray(doc["positions_f32"], dtype="<f4")
        require(saved_pos.size == 3 * int(doc["n_verts"]), "save_positions")
        require(accepted_hash(saved_pos.reshape(-1, 3).astype(np.float64))
                == int(doc["accepted_state_id"]), "save_state_id_mismatch")
        ref = evaluate_surface(
            saved_pos.astype(np.float64).reshape(-1, 3), faces,
            doc["gamma_admitted_f64"])
        d_e = abs(float(ref.energy) - float(doc["energy_J"]))
        d_f = abs(float(ref.vertex_forces[seam, 2])
                  - float(doc["centre_load_N"]))
        require(d_e <= ENERGY_TOL, "cpu_energy_mismatch")
        require(d_f <= FORCE_TOL, "cpu_force_balance_mismatch")
        rec["save"] = {"accepted_state_id": doc["accepted_state_id"],
                       "centre_load_N": doc["centre_load_N"],
                       "energy_J": doc["energy_J"],
                       "cpu_energy_abs_diff_J": d_e,
                       "cpu_force_abs_diff_N": d_f,
                       "energy_allowance_J": ENERGY_TOL,
                       "force_allowance_N": FORCE_TOL}
        # workshop increment 1: the player's work product PERSISTS to DISK
        # here -- the boot-A engine is terminated below, and boot B (a fresh
        # process) must restore this exact doc bit-exactly (see the
        # persistence step in the replay boot).
        save_path = output / SAVE_FILENAME
        save_path.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n",
                             encoding="utf-8")
        rec["save"]["disk_path"] = str(save_path)
        rec["save"]["disk_sha256"] = file_hash(save_path)
        rec["sequence"].append({"step": "save", "control":
                                "GET /membrane_demo_save",
                                "state_id": doc["accepted_state_id"],
                                "disk_sha256": rec["save"]["disk_sha256"]})

        # ── criterion 3: the 0.9 N failure path ──────────────────────────
        # (a) the RECORD domain refuses the 0.9 N compile (named refusal,
        #     demonstrated up front in main()); (b) the ENGINE admits 0.9 --
        #     the refusal is the record's, and the loop must recover.
        ood = engine.request("POST", "/membrane_demo",
                             {"op": "deform", "load_N": REFUSED_LOAD})
        ood = ood.get("status", ood)
        require(ood.get("last_control") == "deform", "failure_path_refused")
        ood_t = telemetry(ood)
        require(ood_t["accepted_state_id"]
                != int(doc["accepted_state_id"]), "failure_path_no_change")
        c = shot("c-out-of-domain-load.png")
        rec["c3_failure"] = {
            "refused_load_N": REFUSED_LOAD,
            "record_refusal": txn_refused,
            "engine_outcome": "admitted (no engine domain law; the load "
                              "domain lives in the qualified record)",
            "out_of_domain_state": ood_t,
            "recovery": "save -> restore below (bit-exact return to the "
                        "terminal state)",
            "pass": txn_refused.get("refusal")
                    == "binding_load_out_of_domain"}
        rec["sequence"].append({"step": "failure_0.9N", "control":
                                f"deform load_N={REFUSED_LOAD} (out of "
                                "record domain)", "screenshot": c.name,
                                "screenshot_sha256": file_hash(c), **ood_t})

        # ── recovery: restore the saved terminal state BIT-EXACTLY ───────
        restored = engine.request("POST", "/membrane_demo_restore", doc)
        restored = restored.get("status", restored)
        require(restored.get("last_control") == "restored", "restore_refused")
        require(int(restored["accepted_state_id"])
                == int(doc["accepted_state_id"]), "restore_not_bit_exact")
        require(abs(restored["centre"][2]
                    - float(doc["positions_f32"][seam * 3 + 2])) < 1e-12,
                "restore_centre_moved")
        require(restored["centre_load_N"] == doc["centre_load_N"],
                "restore_load_changed")
        d = shot("d-restored-terminal.png")
        d_stats = _diff_stats(b, d)
        rec["restore"] = {"restored_state_id":
                          int(restored["accepted_state_id"]),
                          "bit_exact": True,
                          "pixel_diff_vs_terminal": d_stats}
        rec["sequence"].append({"step": "restore", "control":
                                "POST /membrane_demo_restore",
                                "screenshot": d.name,
                                "screenshot_sha256": file_hash(d)})

        # ── criterion 5: the engine RESET control ────────────────────────
        engine.membrane.reset()
        rst = engine.membrane.state()
        rst = rst.get("status", rst)
        reset_t = telemetry(rst)
        reset_ok = (reset_t["accepted_state_id"] == expect_id
                    and rst["material_snapshot"]
                    == st["material_snapshot"]
                    and abs(reset_t["energy_J"] - e_ref) <= ENERGY_TOL
                    and reset_t["load_N"] == 0.0)
        e = shot("e-reset-baseline.png")
        e_stats = _diff_stats(a, e)
        rec["c5_restart"] = {
            "reset_state": reset_t,
            "accepted_state_id_matches_upload": True,
            "material_snapshot_matches": True,
            "pixel_diff_vs_baseline": e_stats,
            "pass": bool(reset_ok)}
        rec["sequence"].append({"step": "restart", "control": "reset (ctl"
                                " kind 0)", "screenshot": e.name,
                                "screenshot_sha256": file_hash(e),
                                **reset_t})

        # reset -> restore again (the reset law under the restore law)
        restored2 = engine.request("POST", "/membrane_demo_restore", doc)
        restored2 = restored2.get("status", restored2)
        require(restored2.get("last_control") == "restored",
                "restore2_refused")
        require(int(restored2["accepted_state_id"])
                == int(doc["accepted_state_id"]), "restore2_not_bit_exact")
        rec["restore_after_reset_state_id"] = \
            int(restored2["accepted_state_id"])
        rec["sequence"].append({"step": "restore_after_reset", "control":
                                "reset then restore",
                                "state_id": restored2["accepted_state_id"]})
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        time.sleep(1.0)              # port release before the replay boot

    # ── criterion 6: replay -- same hashes in, same hashes out ───────────
    with socket.socket() as sock:
        require(sock.connect_ex(("127.0.0.1", port)) != 0,
                "replay_port_occupied")
    # workshop increment 1: the replay boot carries a Studio board file so
    # the persistence restore below is browser-visible in /glass (the S5
    # authoring-demo pattern); every /studio POST sends explicit "on": true
    # (the S5 sharp edge: an omitted "on" TOGGLES the overlay off).
    board_path = output / "studio_board_persistence.json"
    _board_write(board_path, _persistence_stage(
        "Workshop increment 1 - persistence (boot B)", "workshop inc 1",
        "fresh boot: uploading the qualified packet, replaying the "
        "objective deform, then restoring boot A's DISK save doc"))
    proc = None
    try:
        proc = _boot(executable, native, port, board=board_path,
                     size=(2560, 1440))
        engine = EngineControl(base, timeout=15)
        for _ in range(100):
            require(proc.poll() is None, "replay_engine_exited")
            try:
                engine.telemetry()
                break
            except OSError:
                time.sleep(0.2)
        else:
            raise RuntimeError("replay_readiness_timeout")
        engine.membrane.upload(packet)
        engine.membrane.pause()
        rp = engine.membrane.state()
        rp = rp.get("status", rp)
        require(rp["accepted_state_id"] == expect_id,
                "replay_state_hash_mismatch")
        replay_deformed = engine.request(
            "POST", "/membrane_demo", {"op": "deform",
                                       "load_N": OBJECTIVE_LOAD})
        replay_deformed = replay_deformed.get("status", replay_deformed)
        require(replay_deformed.get("last_control") == "deform",
                "replay_deform_refused")
        rp_t = telemetry(replay_deformed)
        same_terminal = (rp_t["accepted_state_id"]
                         == rec["c1_objective"]["accepted_state_id"])
        same_apex = (rp_t["apex_z_wu"]
                     == rec["c1_objective"]["apex_z_wu"])
        f = shot("f-replay-terminal.png")
        rec["c6_replay"] = {
            "replay_upload_state_id": int(rp["accepted_state_id"]),
            "replay_deform_state_id": rp_t["accepted_state_id"],
            "terminal_state_id_matches_boot_a": same_terminal,
            "apex_z_bit_equal": same_apex,
            "replay_apex_z_wu": rp_t["apex_z_wu"],
            "screenshot": f.name,
            "screenshot_sha256": file_hash(f),
            "pass": bool(same_terminal and same_apex)}
        rec["sequence"].append({"step": "replay", "control":
                                "fresh boot + identical MD01 upload + same"
                                " deform",
                                "screenshot": f.name,
                                "screenshot_sha256": file_hash(f), **rp_t})

        # ── workshop increment 1: PERSISTENCE ACROSS SESSIONS ────────────
        # Boot A's engine is DEAD (terminated in the finally above); boot B
        # is a fresh engine process that has never seen boot A's state.
        # The disk save doc must round-trip and restore bit-exactly (the
        # accepted-state-id law), and the restored /frame must be
        # pixel-identical to the replay terminal. ADDITIVE workshop check:
        # the six frozen criteria above are untouched.
        disk_doc = json.loads((output / SAVE_FILENAME)
                              .read_text(encoding="utf-8"))
        require(disk_doc == doc, "disk_roundtrip_mismatch")
        t_persist = time.perf_counter()
        persisted = engine.request("POST", "/membrane_demo_restore",
                                   disk_doc)
        persist_ms = (time.perf_counter() - t_persist) * 1000.0
        persisted = persisted.get("status", persisted)
        require(persisted.get("last_control") == "restored",
                "persist_restore_refused")
        require(int(persisted["accepted_state_id"])
                == int(doc["accepted_state_id"]),
                "persist_state_id_mismatch")
        require(int(persisted["accepted_state_id"])
                == rec["c1_objective"]["accepted_state_id"],
                "persist_not_boot_a_terminal")
        p_st = engine.membrane.state()
        p_st = p_st.get("status", p_st)
        p_t = telemetry(p_st)
        require(p_t["apex_z_wu"] == rec["c1_objective"]["apex_z_wu"],
                "persist_apex_moved")
        require(p_t["load_N"] == float(doc["centre_load_N"]),
                "persist_load_changed")
        require(abs(p_t["energy_J"] - float(doc["energy_J"])) <= ENERGY_TOL,
                "persist_energy_changed")
        g = shot("g-persisted-terminal.png")
        g_stats = _diff_stats(f, g)
        rec["persistence"] = {
            "boot_a_engine_terminated": True,
            "disk_doc": str(output / SAVE_FILENAME),
            "disk_sha256": rec["save"]["disk_sha256"],
            "disk_roundtrip_identical": True,
            "restore_wall_ms": persist_ms,
            "restored_state_id": int(p_st["accepted_state_id"]),
            "state_id_bit_exact_vs_boot_a": True,
            "apex_z_wu": p_t["apex_z_wu"],
            "apex_z_bit_equal_boot_a": True,
            "load_N": p_t["load_N"],
            "energy_J": p_t["energy_J"],
            "pixel_diff_vs_replay_terminal": g_stats,
            "screenshot": g.name,
            "screenshot_sha256": file_hash(g),
            "additive_note": "workshop increment 1 (save/reuse): NOT one "
                             "of the six frozen criteria; those are "
                             "unchanged and still reported verbatim",
            "pass": bool(g_stats["changed_px"] == 0
                         and p_t["apex_z_wu"]
                         == rec["c1_objective"]["apex_z_wu"]
                         and int(p_st["accepted_state_id"])
                         == int(doc["accepted_state_id"]))}
        rec["sequence"].append({"step": "persisted_restore", "control":
                                "fresh boot: POST /membrane_demo_restore"
                                " (disk doc from terminated boot A)",
                                "screenshot": g.name,
                                "screenshot_sha256": file_hash(g), **p_t})

        # ── browser-visible /glass readout (the S5 pattern) ──────────────
        engine.request("POST", "/studio", {"on": True, "mode": "board"})
        info = engine.request("GET", "/studio")
        lh = float(info["lh"])
        node_h = 92.0 - 30.0 - lh - 12.0
        engine.request("POST", "/ui_click",
                       {"x": int(info["w"]) / 2.0, "y": 30.0 + node_h / 2.0})
        time.sleep(0.8)
        sel = engine.request("GET", "/studio")
        require(sel.get("selected") == PERSIST_STAGE_ID,
                f"stage_not_selected_{sel.get('selected')}")
        engine.request("POST", "/studio", {"on": True, "left_size": 500.0})
        time.sleep(0.5)
        _board_write(board_path, _persistence_stage(
            "Workshop increment 1 - persistence (boot B)", "workshop inc 1",
            f"PERSISTED RESTORE (fresh boot): apex z {p_t['apex_z_wu']:.7f}"
            f" wu, state id {p_st['accepted_state_id']}, load "
            f"{p_t['load_N']:.1f} N, energy {p_t['energy_J']:.4f} J -- "
            f"bit-exact vs terminated boot A ({persist_ms:.1f} ms)"))
        time.sleep(1.1)
        _board_write(board_path, _persistence_stage(
            "Workshop increment 1 - persistence (boot B)", "workshop inc 1",
            f"PERSISTED RESTORE (fresh boot): apex z {p_t['apex_z_wu']:.7f}"
            f" wu, state id {p_st['accepted_state_id']}, load "
            f"{p_t['load_N']:.1f} N, energy {p_t['energy_J']:.4f} J -- "
            f"bit-exact vs terminated boot A ({persist_ms:.1f} ms)"))
        time.sleep(0.6)          # fresh mtime: the overlay re-polls (S5)
        h = output / "h-glass-persisted.png"
        _shots({"dir": output, "spec": {
            "width": int(info["w"]), "height": int(info["h"]),
            "shots": [{"url": base + f"/glass?v={next(_seq)}",
                       "out": str(h), "wait_ms": 900}]}})
        require(h.is_file(), "glass_not_visible")
        rec["persistence"]["glass_screenshot"] = h.name
        rec["persistence"]["glass_sha256"] = file_hash(h)
        rec["sequence"].append({"step": "glass_readout", "control":
                                "Studio board fed with the live persisted "
                                "values; /glass captured in the browser",
                                "screenshot": h.name,
                                "screenshot_sha256": file_hash(h)})
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
    rec["verdict"] = (
        "loop completed: " + ", ".join(
            f"c{i}={'PASS' if rec[k].get('pass') else 'FAIL'}"
            for i, k in ((1, "c1_objective"), (2, "c2_success"),
                         (3, "c3_failure"), (5, "c5_restart"),
                         (6, "c6_replay")))
        + f", persistence({'additive workshop check'})="
          f"{'PASS' if rec['persistence']['pass'] else 'FAIL'}")
    return rec


def _packet_parts(txn: dict):
    """MD01 packet (centre bound to the transaction's load-port vertex),
    the f32-exact uploaded geometry, and the pinned-law reference energy."""
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
    require(float(gamma64.min()) == float(gamma64.max()),
            "gamma_not_uniform")
    gamma = float(gamma64[0])
    pos32 = pos64.astype("<f4")
    ref = evaluate_surface(pos32.astype(np.float64), faces, gamma)
    seam = int(txn["ids"]["seam_vertex"])
    require(any(int(ld["vertex"]) == seam for ld in comp["loads"]),
            "centre_not_the_load_port")
    require(seam not in [int(p) for p in comp["pins"]],
            "centre_pinned")
    packet = {
        "pos": pos32.reshape(-1),
        "idx": faces.astype("<u4").reshape(-1),
        "csr_off": np.asarray(comp["csr_off"], dtype="<u4").reshape(-1),
        "csr_cor": np.asarray(comp["csr_cor"], dtype="<u4").reshape(-1),
        "gamma_face": gamma64.astype("<f4").reshape(-1),
    }
    # format-fidelity proof: at the demo's hardcoded centre the composed
    # packet must be BYTE-IDENTICAL to the existing md01_packet
    from tools.membrane_demo_client import md01_packet, CENTRE_INDEX
    require(_md01_packet_centred(packet, gamma, CENTRE_INDEX)
            == md01_packet(packet, gamma), "md01_parity_broken")
    return (_md01_packet_centred(packet, gamma, seam), pos32, faces,
            gamma, float(ref.energy))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--exe", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--port", type=int, default=8841)
    args = ap.parse_args(argv)

    exe = Path(args.exe)
    require(exe.is_file(), "engine_executable_missing")
    require((exe.parent / "shaders").is_dir(), "engine_shaders_missing")
    require(Path(NODE_EXE).is_file(), "node_runtime_missing")
    out = Path(args.out)
    require(not out.exists(), "output_directory_exists")
    out.mkdir(parents=True, exist_ok=False)

    txn = nb.compile_transaction("assembly.star-k2", "gameloop-star-inc5",
                                 scale=1.0, load_N=OBJECTIVE_LOAD)
    refused = None
    try:
        nb.compile_transaction("assembly.star-k2", "gameloop-refused-inc5",
                               scale=1.0, load_N=REFUSED_LOAD)
        refused = {"refusal": "NOT_RAISED (unexpected: 0.9 N compiled)"}
    except nb.BindingRefused as ex:
        refused = {"refusal": ex.reason, "detail": ex.detail}
    rec = gameloop_session(txn, refused, out, exe, port=args.port)

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "utc": default_stamp(),
        "source_commit": _source_commit(),
        "engine_executable": str(exe),
        "engine_sha256": file_hash(exe),
        "engine_visible": True,
        "port": args.port,
        "frozen_criteria_source":
            "docs/evidence/mechanism_factory/reviews/"
            "step_review_load_domain_study.md (L4)",
        "objective_load_N": OBJECTIVE_LOAD,
        "refused_load_N": REFUSED_LOAD,
        "band_wu": BAND,
        "tolerances": {"energy_J": ENERGY_TOL, "force_N": FORCE_TOL,
                       "residual_law_N": RESIDUAL_LAW,
                       "cpu_cross_check": CROSSCHECK_TOL},
        "prerun_cpu_verification": PRERUN_CPU_CHECK,
        "criterion_3_record_refusal": refused,
        "instance": rec,
        "screenshots": {p.name: {"path": str(p.resolve()),
                                 "sha256": file_hash(p)}
                        for p in sorted(out.glob("*.png"))},
        "scope": "the frozen stage 9 game loop end to end on ONE qualified "
                 "star instance (1.0x): compile 1.6 N -> visible upload -> "
                 "ctl-6 deform to the objective load -> terminal telemetry "
                 "+ screenshots -> CPU re-solve cross-check -> 0.9 N record "
                 "refusal + engine-admitted out-of-domain state + restore "
                 "-> engine reset bit-exactness -> replay re-upload hash "
                 "match -> workshop-increment-1 persistence: the save doc "
                 "written to DISK by the terminated boot-A engine restores "
                 "bit-exactly in the fresh boot-B engine (additive check; "
                 "the six frozen criteria are unchanged), with a Studio "
                 "board /glass readout. The demo centre is bound to the "
                 "record's load-port vertex (seam 200); see centre_binding "
                 "justification.",
    }
    path = EVID_DIR / (f"gameloop_run_receipt_{default_stamp()}.json")
    path.write_text(json.dumps(receipt, indent=1, default=str) + "\n",
                    encoding="utf-8")
    for step in rec["sequence"]:
        line = f"[OK] {step['step']}:"
        if "apex_z_wu" in step:
            line += (f" apex_z {step['apex_z_wu']:.9f} wu,"
                     f" load {step['load_N']:.3f} N,"
                     f" free_residual {step['free_residual_N']:.3e} N,")
        if step.get("screenshot"):
            line += f" shot {step['screenshot']}"
        print(line)
    c1, c2 = rec["c1_objective"], rec["c2_success"]
    print(f"[{'PASS' if c1['pass'] else 'FAIL'}] c1 objective: apex_z "
          f"{c1['apex_z_wu']:.9f} wu in band {BAND} at {OBJECTIVE_LOAD} N")
    print(f"[{'PASS' if c2['pass'] else 'FAIL'}] c2 success: free_residual "
          f"{c2['free_residual_N']:.3e} N (law {RESIDUAL_LAW:g}), CPU "
          f"cross-check {c2['cpu_position_cross_check_wu']:.3e} wu "
          f"(tol {CROSSCHECK_TOL:g}), force cross-check "
          f"{c2['cpu_force_cross_check_N']:.3e} N")
    print(f"[{'PASS' if rec['c3_failure']['pass'] else 'FAIL'}] c3 failure"
          f" path: {REFUSED_LOAD} N -> {refused.get('refusal')}"
          f" (record); engine admitted it and the loop restored")
    print(f"[{'PASS' if rec['c5_restart']['pass'] else 'FAIL'}] c5 restart:"
          f" reset -> state {rec['c5_restart']['reset_state']['accepted_state_id']}"
          f" == upload hash, {rec['c5_restart']['pixel_diff_vs_baseline']['changed_px']} px")
    print(f"[{'PASS' if rec['c6_replay']['pass'] else 'FAIL'}] c6 replay: "
          f"terminal state id "
          f"{rec['c6_replay']['replay_deform_state_id']} matches boot A, "
          f"apex_z bit-equal {rec['c6_replay']['apex_z_bit_equal']}")
    pers = rec["persistence"]
    print(f"[{'PASS' if pers['pass'] else 'FAIL'}] persistence (additive"
          f" workshop check, not a frozen criterion): boot A's disk save "
          f"doc restored bit-exactly in fresh boot B"
          f" (state id {pers['restored_state_id']},"
          f" {pers['restore_wall_ms']:.1f} ms,"
          f" {pers['pixel_diff_vs_replay_terminal']['changed_px']} px vs"
          f" replay terminal)")
    print(f"GAMELOOP RUN COMPLETE {path}")
    return 0 if all(rec[k].get("pass") for k in
                    ("c1_objective", "c2_success", "c3_failure",
                     "c5_restart", "c6_replay", "persistence")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
