#!/usr/bin/env python3
"""WALK-PHYS-20261004 sealed battery (phase 2; prereg-pinned).

Prereg of record: PREREGISTRATION.md in this directory -- committed ALONE-FIRST
as 2b58118cae81110b8e1c69a26e83d0aadab002f4 on origin/review/WALK-PHYS-20261004
(blob sha256 b4326a0971326db3d6267c9e00a9372ce33707d084b11a897417406e319de3fe;
this file's copy must hash-verify equal BEFORE anything runs).

Order is law: pins -> build (pinned recipe) -> clean anchor arm (P1) ->
discriminator arms (P5-P9) -> determinism pass (P8) -> receipt. The physics
input is the sealed scene f6844eea... UNCHANGED on every CLEAN arm; the
control arms (mu=0, drive-cut, cap-raise, state-write probe) are the prereg's
declared deltas and are EXPECTED to lose support/motion. A falsified
prediction is a recorded result, never a runner failure; the receipt carries
verdicts. Exit 0 = battery completed + receipt written; exit 2 = refusal
(pin/build/toolchain) with the reason on stderr.

Run (inside a task_package slot):
  python -B tools/monkey_campaign/contributions/WALK-PHYS-20261004/run_battery.py --smoke
  python -B tools/monkey_campaign/contributions/WALK-PHYS-20261004/run_battery.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "inputs"
ANCHORS = INPUTS / "anchors"
VCVARS = r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"

# ---------------------------------------------------------------- pins
# Frozen input identities (phase-1 EVIDENCE + the sealed W03 anchor record).
PINS = {
    "PREREGISTRATION.md": "b4326a0971326db3d6267c9e00a9372ce33707d084b11a897417406e319de3fe",
    "inputs/scene.json": "f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342",
    "inputs/gait_unit_viswalk_dump_orig.cpp": "dea2be78762860b201a348824fd6a4a4fe9f2a1dd3f9552157187729568f1cab",
    "inputs/gait_controller.hpp": "f0ffea12795bd47f7c48f5ed9b8aa98869725467d94a1081b1d942f6fba129bd",
    "inputs/build_dump.ps1": "2e3fcf50933d177c932bacf18dbbcf12f7e79b4346fcfa9512dcddbdb0b33200",
    "inputs/anchors/dump_stdout.txt": "8c537cdb7cb8c43cf9423cb50056787bcc31ee487d70d3c2a1e73ed5d60b06cc",
    "inputs/anchors/states_run1.jsonl": "b47b709c43a021d24bfee13bb2fe4592167cf205ee0abf9971de462319389c93",
    "inputs/anchors/states_run2.jsonl": "b47b709c43a021d24bfee13bb2fe4592167cf205ee0abf9971de462319389c93",
    "inputs/anchors/dump_run_record.json": "6278f4b02089d62500b5ce48748209a476ccbdb773bc40f1a413bb9e2954bb85",
    "inputs/anchors/walk_numbers_record.json": "717a721499b5ad4b829d8e50b611b11da38621c1a3f9a80ddb833088286e0d5d",
}
# The sealed anchor numbers (dump_run_record.json / W03 REPORT):
SEALED_STDOUT_SHA = "8c537cdb7cb8c43cf9423cb50056787bcc31ee487d70d3c2a1e73ed5d60b06cc"
SEALED_STDERR_SHA = "c6f9b6c00a1d549a4bc709724d2f62f8f28b37823696de4689e1950651c37481"
SEALED_QDUMP_SHA = "b47b709c43a021d24bfee13bb2fe4592167cf205ee0abf9971de462319389c93"
SEALED_DX = 0.9131056683968011
SEALED_DY = -0.7178374101385098
SEALED_TICKS = 302
SEALED_LEDGER_J = 30.970714            # stdout-precision anchor
SEALED_BAL300_J = 30.970713623726674   # the record's raw run-1 value (tick 300)
SEALED_MU = 0.6                        # the scene's declared placeholder friction
SEALED_HIP_CAP = 11.2125               # drives[0].torque_cap_N_m (hip_flexion_left)
WALK_LO, WALK_HI = 60, 300             # the prereg's declared walk window
CUT_TICK = 150                         # P6 declared drive-cut tick
INJ_TICK = 100                         # P9 declared state-write probe tick
GE_WINDOW_J = 1e-6                     # G-E per-tick ledger window (prereg 2/P4)
P3_WINDOW = 1e-9                       # P3 attribution window (prereg 2/P3)
P5_COM_WINDOW_M = 1e-4                 # P5 COM-x frozen window
P6_MOM_WINDOW = 1e-6                   # P6 momentum window (kg*m/s)


def require(ok, code, detail=""):
    if not ok:
        print(f"REFUSAL: {code} {detail}", file=sys.stderr)
        raise SystemExit(2)


def sha_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------- pins stage
def verify_pins() -> dict:
    got = {}
    for rel, want in PINS.items():
        p = HERE / rel
        require(p.exists(), "input_pin_missing", rel)
        h = sha_file(p)
        require(h == want, "input_pin_drift", f"{rel} {h} != {want}")
        got[rel] = h
    return got


# ---------------------------------------------------------------- build stage
_BAT_N = [0]


def vc_batch(scratch: Path, lines: list, capture: bool = True):
    """Run lines inside a fresh cmd batch AFTER activating the VS toolchain.
    Quotes are native in a batch file; the activation's own output is
    suppressed per-command so the captured streams carry ONLY the payload's
    bytes (the anchor-hash law). CreateProcess PATH-search never happens:
    every executable is invoked through the batch."""
    require(Path(VCVARS).exists(), "toolchain_missing", VCVARS)
    _BAT_N[0] += 1
    bat = scratch / f"walkphys_vc_{_BAT_N[0]}.cmd"
    body = b'@echo off\r\ncall "' + VCVARS.encode("ascii") + \
        b'" x64 >nul 2>&1\r\n'
    body += b"".join(l.encode("utf-8") + b"\r\n" for l in lines)
    body += b"exit /b %ERRORLEVEL%\r\n"
    bat.write_bytes(body)
    return subprocess.run(["cmd", "/c", str(bat)], capture_output=capture)


BUILD_HEADERS = {  # the pinned include closure (revision 17ba94b9 chain)
    "inputs/gait_controller.hpp": "engine/gait_controller.hpp",
    "inputs/coupled_articulation.hpp": "engine/coupled_articulation.hpp",
    "inputs/earth_environment.hpp": "engine/earth_environment.hpp",
    "inputs/force_models.hpp": "engine/force_models.hpp",
    "inputs/json/json.hpp": "native/viewer3rd/json.hpp",
}
BUILD_HEADER_SHAS = {
    "inputs/gait_controller.hpp": "f0ffea12795bd47f7c48f5ed9b8aa98869725467d94a1081b1d942f6fba129bd",
    "inputs/coupled_articulation.hpp": "5bd73c2d43b85b229040da1ac779ef3733dc7d4dbe04cbeb1447c03767dc9fb5",
    "inputs/earth_environment.hpp": "b4747d349ce201ebadb74227b33725466d16edd860ed421ac590ad789178469a",
    "inputs/force_models.hpp": "483b97f4600ce0e4c178bc0d9420de55ae9cb853910e3c38a3e5cf9919f0630c",
    "inputs/json/json.hpp": "9bea4c8066ef4a1c206b2be5a36302f8926f7fdc6087af5d20b417d0cf103ea6",
}


def build(scratch: Path) -> dict:
    engine = scratch / "engine"
    tca = engine / "tests_coupled_arm"
    tca.mkdir(parents=True, exist_ok=True)
    for src_rel, dst_rel in BUILD_HEADERS.items():
        require(sha_file(HERE / src_rel) == BUILD_HEADER_SHAS[src_rel],
                "header_pin_drift", src_rel)
        dst = scratch / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(HERE / src_rel, dst)
    shutil.copyfile(HERE / "gait_unit_viswalk_dump_walkphys.cpp",
                    tca / "gait_unit_viswalk_dump.cpp")
    outdir = scratch / "build"
    outdir.mkdir(exist_ok=True)
    exe = outdir / "gait_unit_viswalk_dump.exe"
    cl = ("cl /nologo /std:c++17 /O2 /W4 /fp:precise /EHsc /DGAIT_EVENT_TRACE "
          '"engine\\tests_coupled_arm\\gait_unit_viswalk_dump.cpp" '
          f'/Fe:"{exe}" /Fo:"{outdir / "dump.obj"}"')
    proc = vc_batch(scratch, [f'cd /d "{scratch}"', cl])
    (outdir / "build_log.txt").write_bytes(
        (proc.stdout or b"") + (proc.stderr or b""))
    require(proc.returncode == 0 and exe.exists(), "build_failed",
            ((proc.stdout or b"") + (proc.stderr or b""))[-1500:].decode(
                "utf-8", "replace"))
    return {"exe": str(exe), "exe_sha256": sha_file(exe),
            "cl_version": next((l.strip() for l in
                                ((proc.stdout or b"") + (proc.stderr or b""))
                                .decode("utf-8", "replace").splitlines()
                                if "for x64" in l or l.strip().startswith("Version")),
                               "unparsed")}


# ---------------------------------------------------------------- run stage
def run_arm(scratch, exe, scene, out: Path, tag: str, extra_env=None,
            with_dumps=True):
    out.mkdir(parents=True, exist_ok=True)
    lines = [f'set "GAITPHYS_TELEMETRY={out / f"telemetry_{tag}.jsonl"}"']
    if with_dumps:
        lines.append(f'set "GAIT_STATE_DUMP={out / f"qdump1_{tag}.jsonl"}"')
        lines.append(f'set "GAIT_STATE_DUMP2={out / f"qdump2_{tag}.jsonl"}"')
    for k, v in (extra_env or {}).items():
        lines.append(f'set "{k}={v}"')
    lines.append(f'"{exe}" "{scene}"')
    proc = vc_batch(scratch, lines)
    (out / f"stdout_{tag}.txt").write_bytes(proc.stdout)
    (out / f"stderr_{tag}.txt").write_bytes(proc.stderr)
    summary = {}
    try:
        summary = json.loads(proc.stdout.decode("utf-8", "replace"))
    except Exception:
        pass
    rec = {"tag": tag, "exit": proc.returncode,
           "stdout_sha256": sha_bytes(proc.stdout),
           "stderr_sha256": sha_bytes(proc.stderr),
           "summary": summary}
    if with_dumps:
        q1, q2 = out / f"qdump1_{tag}.jsonl", out / f"qdump2_{tag}.jsonl"
        rec["qdump1_sha256"] = sha_file(q1) if q1.exists() else None
        rec["qdump2_sha256"] = sha_file(q2) if q2.exists() else None
    tel = out / f"telemetry_{tag}.jsonl"
    rec["telemetry_sha256"] = sha_file(tel) if tel.exists() else None
    rec["telemetry_rows"] = (sum(1 for _ in tel.open(encoding="utf-8"))
                             if tel.exists() else 0)
    return rec


def telemetry(path: Path, tag: str) -> list:
    rows = []
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("run") == tag:
                rows.append(r)
    rows.sort(key=lambda r: r["tick"])
    return rows


# ------------------------------------------------------------- P-evaluators
def eval_p1(rec, qdump1: Path):
    """P1 ANCHOR IDENTITY: recording must not perturb physics."""
    checks = {
        "stdout_sha": rec["stdout_sha256"] == SEALED_STDOUT_SHA,
        "stderr_sha": rec["stderr_sha256"] == SEALED_STDERR_SHA,
        "qdump1_sha": rec["qdump1_sha256"] == SEALED_QDUMP_SHA,
        "qdump2_sha": rec["qdump2_sha256"] == SEALED_QDUMP_SHA,
    }
    rows = [json.loads(l) for l in qdump1.open(encoding="utf-8")]
    dx = rows[-1]["q"][3] - rows[0]["q"][3]
    dy = rows[-1]["q"][4] - rows[0]["q"][4]
    checks["ticks_302"] = len(rows) == SEALED_TICKS
    checks["dx_exact"] = (dx == SEALED_DX)
    checks["dy_exact"] = (dy == SEALED_DY)
    note = next((m for m in rec["summary"].get("measured", [])
                 if m.startswith("WALK refused_tick=")), "")
    checks["refused_note"] = note == (
        f"WALK refused_tick={SEALED_TICKS} "
        f"worst_ledger_J={SEALED_LEDGER_J}")
    return {"checks": checks, "dx": dx, "dy": dy, "walk_note": note,
            "pass": all(checks.values())}


def eval_p2(rows):
    """P2 SUPPORT CENSUS: every walk-window tick carries a loaded pad."""
    viol, census = [], {p["name"]: {"touch_ticks": 0, "reaction_Ns": 0.0,
                                    "friction_Ns": 0.0}
                        for p in rows[0]["contact"]["points"]} if rows else {}
    for r in rows:
        if not (WALK_LO <= r["tick"] <= WALK_HI):
            continue
        loaded = [p for p in r["contact"]["points"]
                  if p["touching"] and p["reaction_N"] > 1e-9]
        if not loaded:
            viol.append(r["tick"])
        for p in r["contact"]["points"]:
            c = census.setdefault(p["name"], {"touch_ticks": 0,
                                              "reaction_Ns": 0.0,
                                              "friction_Ns": 0.0})
            if p["touching"]:
                c["touch_ticks"] += 1
                c["reaction_Ns"] += p["reaction_N"] / 300.0
                c["friction_Ns"] += abs(p["friction_force_N"]) / 300.0
    return {"violations": viol, "census": census,
            "pass": not viol, "window": [WALK_LO, WALK_HI]}


def eval_p3(rows, mass):
    """P3 PROPULSION ATTRIBUTION: per-tick horizontal COM momentum change vs
    the recorded contact friction impulses (the only serialized horizontal
    force channel). CORRECTED TO IMPULSE UNITS: the sealed receipt of job
    075ada58 compared a force against an impulse (unit bug, superseded);
    this form compares impulse (kg*m) against the friction-magnitude bound
    sum(|friction_force_N|)*dt. The serialized channels are direction-free
    scalars, so the rigorous closable claim is the containment
    |m*d(COMx)| <= sum(|frc|)*dt + window; the exact-equality subset and the
    instrument limitation are recorded either way."""
    viol, worst, rows_out = [], -1e30, []
    imps, bounds = [], []
    for a, b in zip(rows, rows[1:]):
        if not (WALK_LO <= a["tick"] < WALK_HI):
            continue
        dt = b["tick"] - a["tick"]
        if dt <= 0:
            continue
        dt_s = dt / 300.0
        imp = mass * (b["support"]["east"] - a["support"]["east"])
        fsum = sum(abs(p["friction_force_N"]) for p in b["contact"]["points"])
        bound = fsum * dt_s
        resid = abs(imp) - bound
        imps.append(abs(imp)); bounds.append(bound)
        rows_out.append({"tick": a["tick"], "imp": imp, "bound": bound})
        worst = max(worst, resid)
        if resid > P3_WINDOW:
            viol.append({"tick": a["tick"], "resid": resid})
    imps.sort(); bounds.sort()
    med = lambda v: v[len(v) // 2] if v else 0.0
    return {"violations": viol[:20], "violation_count": len(viol),
            "ticks_evaluated": len(imps),
            "median_imp_Ns": med(imps), "median_bound_Ns": med(bounds),
            "worst_resid_Ns": worst, "window": P3_WINDOW,
            "pass": not viol,
            "note": "impulse-units containment: |m*d(COMx)| <= "
                    "sum(|friction_force_N|)*dt + 1e-9 (direction-free "
                    "serialized scalars; see INSTRUMENT_PROVENANCE.md)"}


def eval_p4(rows):
    """P4 ENERGY LEDGER SPLIT: per-tick increments of the engine's own balance
    identity over the walk window + the tick-300 identity with the anchor."""
    bal = {r["tick"]: r["energy"]["balance_error_J"] for r in rows}
    incs = [(t, bal[t1] - bal[t]) for t, t1 in
            zip([x for x in bal if WALK_LO <= x < WALK_HI],
                [x for x in bal if WALK_LO < x <= WALK_HI])]
    worst = max((abs(d) for _, d in incs), default=0.0)
    b300 = bal.get(WALK_HI)
    anchor_close = (b300 is not None and abs(b300 - SEALED_BAL300_J) <= 1e-9)
    return {"worst_per_tick_inc_J": worst, "window_J": GE_WINDOW_J,
            "bal_at_300": b300, "bal300_vs_anchor_within_1e-9": anchor_close,
            "gate": "closed" if worst <= GE_WINDOW_J else "FIRED",
            "pass": worst <= GE_WINDOW_J and anchor_close}


def eval_p5(rows):
    """P5 ZERO-FRICTION DISCRIMINATOR: COM_x frozen with mu=0."""
    mus = {r["contact"]["friction_mu"] for r in rows}
    east = {r["tick"]: r["support"]["east"] for r in rows}
    t_lo = min(t for t in east if WALK_LO <= t <= WALK_HI)
    t_hi = max(t for t in east if WALK_LO <= t <= WALK_HI)
    d = abs(east[t_hi] - east[t_lo])
    return {"mu_values_seen": sorted(mus), "com_x_displacement_m": d,
            "window_m": P5_COM_WINDOW_M, "pass": mus == {0.0} and d <= P5_COM_WINDOW_M}


def eval_p6(rows):
    """P6 DRIVE-CUT DISCRIMINATOR: horizontal COM momentum non-increasing
    from the cut through cut+100."""
    m = rows[0]["support"]["mass_kg"]
    east = {r["tick"]: r["support"]["east"] for r in rows}
    if CUT_TICK not in east or CUT_TICK + 1 not in east:
        return {"pass": False, "measured": False,
                "note": "run refused before the cut window"}
    p0 = m * (east[CUT_TICK + 1] - east[CUT_TICK]) * 300.0
    worst = 0.0
    for t in range(CUT_TICK, min(CUT_TICK + 100, max(east))):
        if t not in east or t + 1 not in east:
            continue
        p = m * (east[t + 1] - east[t]) * 300.0
        worst = max(worst, p - p0)
    return {"max_momentum_rise_kg_m_s": worst, "window": P6_MOM_WINDOW,
            "measured": True, "pass": worst <= P6_MOM_WINDOW}


def eval_p7(rows, clean_rows):
    """P7 CAP-RAISE TAMPER: the raised cap must move torque beyond the SEALED
    cap and the audit must flag it; the clean arm must show zero flags."""
    def flags(rows_):
        out = []
        for r in rows_:
            for j in r["joints"]:
                if j["name"] == "hip_flexion_left" and \
                        abs(j["motor_torque_N_m"]) > SEALED_HIP_CAP + 1e-9:
                    out.append({"tick": r["tick"], "tau": j["motor_torque_N_m"],
                                "cap_recorded": j["torque_cap_N_m"]})
        return out
    tam = flags(rows)
    cln = flags(clean_rows)
    return {"tampered_exceeding_sealed_cap": tam[:10],
            "tampered_count": len(tam),
            "clean_count": len(cln),
            "pass": len(tam) > 0 and len(cln) == 0}


def eval_p9(tel_inj: Path, tel_clean: Path):
    """P9 STATE-WRITE PROBE: the tick-100 write must be refused or visibly
    diverge against the clean continuation; a silent vanish fails."""
    a = telemetry(tel_inj, "w1")
    b = telemetry(tel_clean, "w1")
    bb = {r["tick"]: r for r in b}
    first_div = None
    for r in a:
        o = bb.get(r["tick"])
        if o is None:
            continue
        if json.dumps(r, sort_keys=True) != json.dumps(o, sort_keys=True):
            first_div = r["tick"]
            break
    return {"first_divergence_tick": first_div, "injected_at": INJ_TICK,
            "caught": first_div is not None,
            "pass": first_div is not None}


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true",
                    help="pre-gated feasibility probe: pins + build + 1 tick")
    a = ap.parse_args()

    pins = verify_pins()
    # Keep-check law: declared outputs resolve against the job's working
    # directory (the runner's scratch root), not CHIMERA_OUTPUT_DIR
    # (job 5c6567e0 wrote to the latter and failed the keep check with the
    # science already green). cwd-relative "outputs" is the contract.
    outdir = Path.cwd() / "outputs"
    art = outdir / "artifacts"
    art.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix="walkphys_"))
    receipt = {"schema": "chimera.walkphys.battery.v1",
               "prereg_sha256": PINS["PREREGISTRATION.md"],
               "scene_sha256": PINS["inputs/scene.json"],
               "pins": pins, "smoke": a.smoke}
    try:
        receipt["build"] = build(scratch)
        exe = receipt["build"]["exe"]
        scene = INPUTS / "scene.json"

        if a.smoke:
            # Pre-gated feasibility: build + ONE FULL clean arm with the
            # instrument on (telemetry + dumps), checked against the sealed
            # anchors. (A 1-tick truncation crashes the native post-walk
            # falsifier stack - job f9582e50, 0xC0000005 - so the smoke runs
            # the real thing; ~40 s.)
            rec = run_arm(scratch, exe, scene, art, "smoke")
            require(rec["exit"] == 0, "smoke_run_failed",
                    hex(rec["exit"] & 0xFFFFFFFF))
            p1s = eval_p1(rec, art / "qdump1_smoke.jsonl")
            rows_s = telemetry(art / "telemetry_smoke.jsonl", "w1")
            receipt["smoke_arm"] = {k: v for k, v in rec.items()
                                    if k != "summary"}
            receipt["smoke_anchor_identity"] = p1s
            receipt["smoke_telemetry_rows_w1"] = len(rows_s)
            (outdir / "smoke_receipt.json").write_text(
                json.dumps(receipt, indent=1, sort_keys=True),
                encoding="utf-8")
            print("SMOKE anchor_identity:", p1s["pass"],
                  "; receipt:", outdir / "smoke_receipt.json")
            return

        # ---- clean anchor arms (P1, P2, P3, P4) + determinism pass (P8)
        c1 = run_arm(scratch, exe, scene, art, "clean1")
        require(c1["exit"] == 0, "clean_run_failed", str(c1["exit"]))
        p1 = eval_p1(c1, art / "qdump1_clean1.jsonl")
        rows1 = telemetry(art / "telemetry_clean1.jsonl", "w1")
        mass = rows1[0]["support"]["mass_kg"]
        p2 = eval_p2(rows1)
        p3 = eval_p3(rows1, mass)
        p4 = eval_p4(rows1)
        c2 = run_arm(scratch, exe, scene, art, "clean2")
        p8 = {"stdout": c1["stdout_sha256"] == c2["stdout_sha256"],
              "stderr": c1["stderr_sha256"] == c2["stderr_sha256"],
              "qdump1": c1["qdump1_sha256"] == c2["qdump1_sha256"],
              "qdump2": c1["qdump2_sha256"] == c2["qdump2_sha256"],
              "telemetry": c1["telemetry_sha256"] == c2["telemetry_sha256"]}
        p8["pass"] = all(p8.values())

        # ---- declared control arms
        # mu0 scene: the single declared delta (prereg 2/P5)
        scene_j = json.loads(scene.read_text(encoding="utf-8"))
        mu0 = json.loads(scene.read_text(encoding="utf-8"))
        mu0["gait_controller"]["recipe"]["defaults"]["contact_friction"] = 0.0
        p_mu0 = scratch / "scene_mu0.json"
        p_mu0.write_text(json.dumps(mu0, sort_keys=True), encoding="utf-8")
        cap15 = json.loads(scene.read_text(encoding="utf-8"))
        d0 = cap15["gait_controller"]["recipe"]["drives"][0]
        require(d0["coordinate"] == "hip_flexion_left", "cap_target_drift",
                d0["coordinate"])
        d0["torque_cap_N_m"] = SEALED_HIP_CAP * 1.5
        p_cap = scratch / "scene_cap15.json"
        p_cap.write_text(json.dumps(cap15, sort_keys=True), encoding="utf-8")

        r5 = run_arm(scratch, exe, p_mu0, art, "mu0")
        p5 = eval_p5(telemetry(art / "telemetry_mu0.jsonl", "w1"))
        r6 = run_arm(scratch, exe, scene, art, "cut",
                     {"GAITPHYS_POWER_CUT_TICK": CUT_TICK})
        p6 = eval_p6(telemetry(art / "telemetry_cut.jsonl", "w1"))
        r7 = run_arm(scratch, exe, p_cap, art, "cap15")
        p7 = eval_p7(telemetry(art / "telemetry_cap15.jsonl", "w1"), rows1)
        r9 = run_arm(scratch, exe, scene, art, "inject",
                     {"GAITPHYS_INJECT_TICK": INJ_TICK})
        p9 = eval_p9(art / "telemetry_inject.jsonl",
                     art / "telemetry_clean1.jsonl")

        def armrec(r):
            return {k: v for k, v in r.items() if k != "summary"}
        preds = {"P1_anchor_identity": p1, "P2_support_census": p2,
                 "P3_propulsion_attribution": p3, "P4_energy_ledger": p4,
                 "P5_zero_friction": p5, "P6_drive_cut": p6,
                 "P7_cap_tamper": p7, "P8_determinism": p8,
                 "P9_state_write_probe": p9}
        gates = {
            "G_PROPULSION": p3["pass"],
            "G_COMMAND_ROLE": p9["pass"],
            "G_ENERGY": p4["pass"],
            "G_DETERMINISM": p8["pass"],
            "G_BACKSTOP": p1["pass"] and p7["pass"],
        }
        core_green = (p1["pass"] and p2["pass"] and p3["pass"]
                      and p5["pass"] and p6["pass"] and p7["pass"]
                      and p8["pass"] and p9["pass"])
        if core_green and gates["G_ENERGY"]:
            verdict = "SUPPORTED"
        elif core_green:
            verdict = "MIXED_AS_MEASURED"  # the pre-accepted ledger negative
        else:
            verdict = "FALSIFIED_OR_PARTIAL"
        receipt.update({
            "arms": {"clean1": armrec(c1), "clean2": armrec(c2),
                     "mu0": armrec(r5), "cut": armrec(r6),
                     "cap15": armrec(r7), "inject": armrec(r9)},
            "declared_control_deltas": {
                "mu0": {"field": "gait_controller.recipe.defaults."
                                 "contact_friction", "value": 0.0,
                        "scene_sha256": sha_file(p_mu0)},
                "cap15": {"field": "gait_controller.recipe.drives[0]."
                                   "torque_cap_N_m",
                          "value": SEALED_HIP_CAP * 1.5,
                          "scene_sha256": sha_file(p_cap)},
                "cut": {"env": "GAITPHYS_POWER_CUT_TICK", "tick": CUT_TICK},
                "inject": {"env": "GAITPHYS_INJECT_TICK", "tick": INJ_TICK,
                           "write": "speeds()[3] += 0.05"}},
            "predictions": preds,
            "gates": gates,
            "verdict": verdict,
        })
        (outdir / "walkphys_receipt.json").write_text(
            json.dumps(receipt, indent=1, sort_keys=True), encoding="utf-8")
        print("BATTERY COMPLETE verdict:", verdict,
              "receipt:", outdir / "walkphys_receipt.json")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    main()
