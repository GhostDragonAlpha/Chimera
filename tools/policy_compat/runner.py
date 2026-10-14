"""The upgrade-gate runner: corpus, checks 1-3, certificate issuance, pipeline.

CHECK 1 -- same-build replay + checkpoint-resume equivalence (the frozen-ref
pattern: raw-byte files written by FRESH subprocess workers, byte-compared by
the driver; no shell redirection anywhere). The checkpoint-resume continuation
must be BIT-IDENTICAL to the uninterrupted run.

CHECK 2 -- cross-build equivalence on the REGISTERED open-loop cases (identical
pinned command streams into builds N and N+1; max|dv| <= the pre-derived
margin) plus the closed-loop envelope gate. Agreement on registered cases is
EVIDENCE, never universal proof (the prereg says so verbatim).

CHECK 3 -- closed-loop requalification of the frozen policy against the NEW
physics: observations and actions recomputed from the NEW trajectory every
tick, hard gates + non-regression margins. The runner REFUSES action-replay
input by construction: there is no input channel that accepts a pre-recorded
action stream, and any attempt raises PolicyCompatError("ACTION_REPLAY_REFUSED").
Why: replaying build-N actions into build N+1 tests the OLD trajectory, not the
coupled system -- the entire failure mode the gate exists to catch is what the
new physics' RESPONSES do to the loop; an action-replay would certify noise and
miss exactly the divergence it must detect (the feedback loop is the thing
under test).

The policy bundle enters ONLY through the FROZEN P3 loader
(typeb_export.policy_manifest.load_manifest) -- never re-implemented here.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys

import numpy as np

from . import SCHEMA_VERSION
from .certificate import (canonical_json, cert_hash, check_deploy, compat_key,
                          issue_certificate, sha256_hex, validate_certificate)
from .scene_cpu import (AVAILABLE_GROUPS, BUILD_N1_DELTA_NOTE, SCENE_VERSION,
                        canonical_snapshot_bytes, build_n, build_n1,
                        derived_envelope, make_scene, params_sha)

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXPORT_DIR = os.path.join(REPO, "tools", "science_funnel", "typeb_export")
P3_DIR = os.path.join(REPO, "tools", "science_funnel", "validation", "typeb_p3_20260921")
LANE_DIR = os.path.join(REPO, "tools", "science_funnel", "validation", "upgrade_gate_20260920")
RECEIPT = os.path.join(LANE_DIR, "receipt.json")

BYTES_PER_TICK = 32          # 8 applied commands, float32 LE
EVENT_STRIDE = 15            # one evidence event per decision
SUITE_ID = "upgrade_gate_20260920/registered_cases_v1"
ISSUED_BY = "upgrade-gate-20260920 lane agent (Agent: upgate)"


class PolicyCompatError(Exception):
    pass


# ------------------------------------------------------------------ bundle

def load_bundle(p3_dir: str = P3_DIR):
    """The FROZEN P3 loader is the only entry for the policy bundle."""
    if EXPORT_DIR not in sys.path:
        sys.path.insert(0, EXPORT_DIR)
    import policy_manifest as pman          # noqa: PLC0415 (the frozen loader)
    from infer_numpy import NumpyPolicy     # noqa: PLC0415
    mpath = os.path.join(p3_dir, "policy_manifest.json")
    wpath = os.path.join(p3_dir, "dummy_actor.npz")
    manifest = pman.load_manifest(mpath, wpath)
    with open(mpath, "rb") as f:
        manifest_file_sha = hashlib.sha256(f.read()).hexdigest()
    with open(wpath, "rb") as f:
        weights_file_sha = hashlib.sha256(f.read()).hexdigest()
    params = dict(np.load(wpath))
    return {"manifest": manifest, "params": params, "NumpyPolicy": NumpyPolicy,
            "pman": pman, "manifest_file_sha256": manifest_file_sha,
            "weights_file_sha256": weights_file_sha, "p3_dir": p3_dir}


# ------------------------------------------------- policy state (inventory)

def policy_snapshot(policy) -> dict:
    """decision_phase + controller_history: the policy-side restart state."""
    return {
        "decision_phase": {"tick": policy.clock.tick,
                           "decisions": policy.clock.decisions,
                           "policy_hz": policy.clock.policy_hz,
                           "physics_hz": policy.clock.physics_hz,
                           "hold_ticks": policy.clock.hold_ticks},
        "controller_history": {
            "prev_applied": [repr(float(v)) for v in policy.prev_applied],
            "prev_limiter_sat": [repr(float(v)) for v in policy.prev_limiter_sat],
            "ticks_since_intervention": policy.ticks_since_intervention,
            "ticks_since_reset": policy.ticks_since_reset,
            "prev_yaw_rate": repr(policy._prev_yaw_rate),
        },
    }


_POLICY_INVENTORY_KEYS = ("decision_phase", "controller_history")


def policy_restore(policy, snap: dict) -> None:
    missing = [k for k in _POLICY_INVENTORY_KEYS if k not in snap]
    if missing:
        raise PolicyCompatError(
            f"REFUSED: policy restart snapshot INCOMPLETE -- missing: {missing}")
    dp, ch = snap["decision_phase"], snap["controller_history"]
    if (dp["policy_hz"], dp["physics_hz"], dp["hold_ticks"]) != \
            (policy.clock.policy_hz, policy.clock.physics_hz, policy.clock.hold_ticks):
        raise PolicyCompatError("REFUSED: snapshot policy clock differs from this runtime")
    policy.clock.tick = int(dp["tick"])
    policy.clock.decisions = int(dp["decisions"])
    policy.prev_applied = np.asarray([float(v) for v in ch["prev_applied"]], dtype=np.float32)
    policy.prev_limiter_sat = np.asarray([float(v) for v in ch["prev_limiter_sat"]],
                                         dtype=np.float32)
    policy.ticks_since_intervention = int(ch["ticks_since_intervention"])
    policy.ticks_since_reset = int(ch["ticks_since_reset"])
    policy._prev_yaw_rate = float(ch["prev_yaw_rate"])


def full_snapshot(scene, policy, chain_sha: str) -> dict:
    return {"scene": scene.snapshot(), "policy": policy_snapshot(policy),
            "chain_sha_so_far": chain_sha, "traj_ticks_so_far": scene.tick}


def full_snapshot_sha(snap: dict) -> str:
    return sha256_hex(canonical_snapshot_bytes(snap))


# ------------------------------------------------------------- closed loop

def run_closed_loop(bundle: dict, build_id: str, p: dict, seed: int,
                    horizon: int, checkpoint_ticks: tuple[int, ...] = (),
                    collect_records: bool = False):
    """Frozen policy vs one physics build, closed loop. Returns the raw
    trajectory bytes, per-decision applied commands, evidence events with the
    running hash chain, snapshots at the requested ticks, and the v-series."""
    manifest, NumpyPolicy = bundle["manifest"], bundle["NumpyPolicy"]
    policy = NumpyPolicy(manifest, bundle["params"])
    policy.reset()
    scene = make_scene(build_id, p, seed)
    scene.begin([float(c) for c in manifest["action"]["center"]])
    initial_snap = full_snapshot(scene, policy, chain := sha256_hex(b"initial"))
    initial_sha = full_snapshot_sha(initial_snap)
    chain = sha256_hex(f"chain0:{initial_sha}".encode("utf-8"))

    traj = bytearray()
    applied_per_tick: list[list[float]] = []
    v_series: list[float] = []
    events = []
    snapshots: dict[int, dict] = {}
    records = [] if collect_records else None

    for t in range(horizon):
        if t in checkpoint_ticks:
            snapshots[t] = full_snapshot(scene, policy, chain)
        rec = scene.observation_record()
        if collect_records:
            records.append(json.loads(json.dumps(rec)))
        applied, info = policy.act(rec)
        scene.step(applied, info["limiter_saturation"])
        traj += np.asarray(applied, dtype="<f4").tobytes()
        applied_per_tick.append([float(v) for v in applied])
        v_series.append(scene.v)
        if (t + 1) % EVENT_STRIDE == 0 or t == horizon - 1:
            ssha = scene.state_sha256()
            chain = sha256_hex(f"{chain}:{t}:state:{ssha}".encode("utf-8"))
            events.append({"tick": t, "kind": "state", "state_sha256": ssha,
                           "chain_sha256": chain})
    final_snap = full_snapshot(scene, policy, chain)
    return {
        "traj_bytes": bytes(traj), "applied_per_tick": applied_per_tick,
        "v_series": v_series, "events": events,
        "initial_snapshot": initial_snap, "initial_snapshot_sha256": initial_sha,
        "snapshots": snapshots, "final_snapshot": final_snap,
        "final_state_sha256": scene.state_sha256(),
        "records": records,
    }


def run_open_loop(build_id: str, p: dict, seed: int,
                  commands: list[list[float]]) -> dict:
    """The registered open-loop case: a pinned command stream into ONE build."""
    scene = make_scene(build_id, p, seed)
    scene.begin(commands[0])
    v_series, states = [], []
    for cmd in commands:
        scene.step(np.asarray(cmd, dtype=np.float32), [0.0] * 8)
        v_series.append(scene.v)
        states.append(scene.state_sha256())
    return {"v_series": v_series, "final_state_sha256": scene.state_sha256(),
            "traj_sha256": sha256_hex(np.asarray(commands, dtype="<f4").tobytes())}


# ------------------------------------------------------------------ corpus

def build_corpus(bundle: dict, passes: int = 3, n_ticks: int = 900) -> dict:
    """The frozen observation/command corpus (F3): the P3 fixed 900-tick
    sequence through the frozen loader + the frozen inference recipe."""
    manifest = bundle["manifest"]
    ev = manifest["evaluation"]["fixed_obs_sequence"]
    with open(os.path.join(bundle["p3_dir"], "trace_slice_wave38.json"), "rb") as f:
        slice_sha = sha256_hex(f.read())
    ticks = json.loads(open(os.path.join(bundle["p3_dir"], "trace_slice_wave38.json"),
                            "rb").read().decode("utf-8"))["ticks"]
    n = len(ticks)
    seq = [ticks[t % n] for t in range(min(n * passes, n_ticks))]

    policy = bundle["NumpyPolicy"](manifest, bundle["params"])
    policy.reset()
    per_tick: list[float] = []
    n_decisions = 0
    for rec in seq:
        applied, info = policy.act(rec)
        per_tick.extend(float(v) for v in applied)
        if info["deciding"]:
            n_decisions += 1
    stream = np.asarray(per_tick, dtype="<f4").tobytes()
    return {
        "sequence_source": "trace_slice_wave38.json",
        "sequence_source_sha256": slice_sha,
        "passes": passes, "n_ticks": len(seq), "n_decisions": n_decisions,
        "actions_sha256": sha256_hex(stream), "actions_bytes": len(stream),
        "runtime": bundle["pman"].build_env(),
        "loader": "typeb_export.policy_manifest.load_manifest (frozen) + "
                  "infer_numpy.NumpyPolicy (the frozen recipe)",
    }


# -------------------------------------------------------- worker functions
# (run in FRESH subprocesses via python -m tools.policy_compat <mode>;
#  raw-byte files, never shell redirection -- the frozen-ref pattern)

def worker_run(out_prefix: str, seed: int, build: str, horizon: int) -> None:
    build_id, p = build_n() if build == "N" else build_n1()
    bundle = load_bundle()
    res = run_closed_loop(bundle, build_id, p, seed, horizon)
    with open(out_prefix + ".bin", "wb") as f:
        f.write(res["traj_bytes"])
    doc = {"traj_sha256": sha256_hex(res["traj_bytes"]),
           "initial_snapshot_sha256": res["initial_snapshot_sha256"],
           "final_state_sha256": res["final_state_sha256"],
           "events": res["events"],
           "v_series_sha256": sha256_hex(np.asarray(res["v_series"], "<f8").tobytes()),
           "applied": res["applied_per_tick"],
           "build_id": build_id, "seed": seed, "horizon": horizon}
    with open(out_prefix + ".json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, sort_keys=True, separators=(",", ":"))


def worker_checkpoint(out: str, seed: int, tick: int, horizon: int) -> None:
    build_id, p = build_n()
    bundle = load_bundle()
    res = run_closed_loop(bundle, build_id, p, seed, horizon,
                          checkpoint_ticks=(tick,))
    snap = res["snapshots"][tick]
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(snap, f, sort_keys=True, separators=(",", ":"))
    print(snap["chain_sha_so_far"])


def worker_resume(snapshot_path: str, out_prefix: str, seed: int,
                  horizon: int, start_tick: int, forced_drop: str | None = None) -> None:
    with open(snapshot_path, "r", encoding="utf-8") as f:
        snap = json.load(f)
    build_id, p = build_n()
    bundle = load_bundle()
    manifest, NumpyPolicy = bundle["manifest"], bundle["NumpyPolicy"]
    policy = NumpyPolicy(manifest, bundle["params"])
    scene = make_scene(build_id, p, seed)
    missing: list[str] = []
    if forced_drop is None:
        scene.restore_snapshot(snap["scene"])       # named refusal on any gap
        policy_restore(policy, snap["policy"])
        chain = snap["chain_sha_so_far"]
    else:
        sc = dict(snap["scene"])
        sc.pop("rng_stream" if forced_drop == "rng" else "contact_warm_start_cache")
        missing = scene.forced_restore_snapshot(sc)  # the probe path
        pol = dict(snap["policy"])
        policy_restore(policy, pol)
        chain = snap["chain_sha_so_far"]
    traj = bytearray()
    events = []
    for t in range(start_tick, horizon):
        rec = scene.observation_record()
        applied, info = policy.act(rec)
        scene.step(applied, info["limiter_saturation"])
        traj += np.asarray(applied, dtype="<f4").tobytes()
        if (t + 1) % EVENT_STRIDE == 0 or t == horizon - 1:
            ssha = scene.state_sha256()
            chain = sha256_hex(f"{chain}:{t}:state:{ssha}".encode("utf-8"))
            events.append({"tick": t, "kind": "state", "state_sha256": ssha,
                           "chain_sha256": chain})
    with open(out_prefix + ".bin", "wb") as f:
        f.write(bytes(traj))
    doc = {"traj_sha256": sha256_hex(bytes(traj)),
           "final_state_sha256": scene.state_sha256(),
           "events": events, "forced_missing": missing,
           "forced_drop": forced_drop, "start_tick": start_tick}
    with open(out_prefix + ".json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, sort_keys=True, separators=(",", ":"))


def _run_worker(mode: str, args: list[str]) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-B", "-m", "tools.policy_compat", mode, *args]
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)


# ------------------------------------------------------------------ CHECK 1

def check1(out_dir: str, seed: int, horizon: int, checkpoint_tick: int) -> dict:
    """Same-build replay + checkpoint-resume equivalence, fresh-process."""
    os.makedirs(out_dir, exist_ok=True)
    p1 = os.path.join(out_dir, f"c1_full_run1_s{seed}")
    r1 = _run_worker("run-full", [p1, str(seed), "N", str(horizon)])
    if r1.returncode != 0:
        raise PolicyCompatError(f"worker run-full failed: {r1.stderr}")
    p2 = os.path.join(out_dir, f"c1_full_run2_s{seed}")
    r2 = _run_worker("run-full", [p2, str(seed), "N", str(horizon)])
    if r2.returncode != 0:
        raise PolicyCompatError(f"worker run-full (replay) failed: {r2.stderr}")
    snap_path = os.path.join(out_dir, f"c1_snapshot_t{checkpoint_tick}_s{seed}.json")
    rc = _run_worker("checkpoint", [snap_path, str(seed), str(checkpoint_tick), str(horizon)])
    if rc.returncode != 0:
        raise PolicyCompatError(f"worker checkpoint failed: {rc.stderr}")
    pr = os.path.join(out_dir, f"c1_resume_s{seed}")
    rr = _run_worker("resume", [snap_path, pr, str(seed), str(horizon), str(checkpoint_tick)])
    if rr.returncode != 0:
        raise PolicyCompatError(f"worker resume failed: {rr.stderr}")

    full1 = open(p1 + ".bin", "rb").read()
    full2 = open(p2 + ".bin", "rb").read()
    cont = open(pr + ".bin", "rb").read()
    head = full1[: checkpoint_tick * BYTES_PER_TICK]
    tail = full1[checkpoint_tick * BYTES_PER_TICK:]
    replay_identical = full1 == full2
    resume_identical = tail == cont

    # F2 structural layer: an incomplete snapshot must be REFUSED by name
    snap = json.load(open(snap_path, "r", encoding="utf-8"))
    refusals = {}
    for drop in ("rng_stream", "contact_warm_start_cache"):
        broken = json.loads(json.dumps(snap))
        broken["scene"].pop(drop)
        _, p = build_n()
        scene = make_scene("cpu-walk-scene-build-N", p, seed)
        try:
            scene.restore_snapshot(broken["scene"])
            refusals[drop] = None  # NOT refused: the structural layer MISSED
        except Exception as exc:   # SnapshotError -- the named refusal
            refusals[drop] = str(exc)

    # F2 dynamic layer: the FORCED resume must move the continuation TRAJECTORY.
    # Detection instrument (declared pre-data in the receipt amendment): the
    # tick-wise STATE hashes (the certificate's own evidence currency -- the
    # trajectory of record) PLUS the action byte stream. The dropped-RNG case
    # moves the state hashes from the first tick (the micro-terrain draws
    # change) even where the v1 observation masks pad channels so the action
    # bytes can stay identical; the dropped-cache case moves both.
    full_events = json.load(open(p1 + ".json", "r", encoding="utf-8"))["events"]
    forced = {}
    for drop, key in (("rng", "rng_stream"), ("warm", "contact_warm_start_cache")):
        pf = os.path.join(out_dir, f"c1_resume_forced_{drop}_s{seed}")
        rf = _run_worker("resume-forced", [snap_path, pf, str(seed), str(horizon),
                                           str(checkpoint_tick), drop])
        if rf.returncode != 0:
            raise PolicyCompatError(f"worker resume-forced({drop}) failed: {rf.stderr}")
        contf = open(pf + ".bin", "rb").read()
        fj = json.load(open(pf + ".json", "r", encoding="utf-8"))
        state_moved = (fj["events"] != full_events[len(full_events) - len(fj["events"]):]
                       or fj["final_state_sha256"] !=
                       json.load(open(p1 + ".json", encoding="utf-8"))["final_state_sha256"])
        bytes_moved = contf != tail
        forced[drop] = {"missing_reported": fj["forced_missing"],
                        "state_hashes_moved": state_moved,
                        "action_bytes_moved": bytes_moved,
                        "n_diff_bytes": sum(a != b for a, b in zip(contf, tail))
                                        if len(contf) == len(tail) else -1,
                        "differs_from_reference": state_moved or bytes_moved}

    passed = (replay_identical and resume_identical
              and all(v is not None for v in refusals.values())
              and all(f["differs_from_reference"] for f in forced.values()))
    report = {
        "check": "CHECK_1_same_build_replay_and_checkpoint_resume",
        "pass": passed,
        "replay_byte_identical": replay_identical,
        "replay_sha256": [sha256_hex(full1), sha256_hex(full2)],
        "resume_byte_identical": resume_identical,
        "resume_head_sha256": sha256_hex(head),
        "uninterrupted_tail_sha256": sha256_hex(tail),
        "resume_tail_sha256": sha256_hex(cont),
        "checkpoint_tick": checkpoint_tick, "seed": seed, "horizon": horizon,
        "f2_structural_refusals": refusals,
        "f2_forced_resumes": forced,
        "detail": (f"fresh-process replay {'IDENTICAL' if replay_identical else 'DIFFERS'}; "
                   f"checkpoint({checkpoint_tick}) resume "
                   f"{'BIT-IDENTICAL' if resume_identical else 'DIFFERS'} to the "
                   f"uninterrupted tail; structural refusals named: "
                   f"{sorted(k for k, v in refusals.items() if v is not None)}; "
                   f"forced resumes detected: "
                   f"{sorted(k for k, v in forced.items() if v['differs_from_reference'])}"),
    }
    with open(os.path.join(out_dir, "check1_report.json"), "w", encoding="utf-8",
              newline="\n") as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write("\n")
    return report


# ------------------------------------------------------------------ CHECK 2

def check2(out_dir: str, streams: dict[int, list[list[float]]],
           cases: list[dict]) -> dict:
    """Registered open-loop cross-build cases + the closed-loop envelope."""
    env = derived_envelope()
    margin, v_env = env["openloop_crossbuild_margin_m_s"], env["velocity_envelope_m_s"]
    _, pn = build_n()
    _, pn1 = build_n1()
    os.makedirs(out_dir, exist_ok=True)
    case_results = []
    for case in cases:
        seed = case["seed"]
        cmds = streams[seed]
        a = run_open_loop("cpu-walk-scene-build-N", pn, seed, cmds)
        b = run_open_loop("cpu-walk-scene-build-N+1", pn1, seed, cmds)
        dv = [abs(x - y) for x, y in zip(b["v_series"], a["v_series"])]
        case_results.append({
            "case": case["case"], "seed": seed, "horizon_ticks": case["horizon_ticks"],
            "command_stream_sha256": a["traj_sha256"],
            "build_N_final_state": a["final_state_sha256"],
            "build_N1_final_state": b["final_state_sha256"],
            "max_abs_dv_m_s": max(dv), "mean_abs_dv_m_s": sum(dv) / len(dv),
            "within_derived_margin": max(dv) <= margin,
        })
    passed = all(c["within_derived_margin"] for c in case_results)
    report = {
        "check": "CHECK_2_cross_build_equivalence_registered_cases",
        "pass": passed,
        "derived_margin_m_s": margin,
        "velocity_envelope_m_s": v_env,
        "derivation": env["derivation"],
        "cases": case_results,
        "honesty_note": "AGREEMENT ON REGISTERED CASES IS EVIDENCE, NOT UNIVERSAL "
                        "PROOF: finitely many pinned command streams cannot prove "
                        "cross-build agreement everywhere; the certificate's "
                        "qualification scope (part d) bounds what this evidence "
                        "covers, and every future build re-runs these cases.",
        "detail": (f"{sum(1 for c in case_results if c['within_derived_margin'])}/"
                   f"{len(case_results)} registered open-loop cases within the "
                   f"pre-derived margin {margin!r} m/s (max measured "
                   f"{max(c['max_abs_dv_m_s'] for c in case_results)!r} m/s)"),
    }
    with open(os.path.join(out_dir, "check2_report.json"), "w", encoding="utf-8",
              newline="\n") as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write("\n")
    return report


# ------------------------------------------------------------------ CHECK 3

def check3(out_dir: str, seed: int, horizon: int) -> tuple[dict, dict]:
    """Closed-loop requalification on build N+1 + the action-replay refusal.

    Returns (report, run) -- the run carries the evidence for the certificate.
    """
    env = derived_envelope()
    v_env = env["velocity_envelope_m_s"]
    build_id, p = build_n1()
    bundle = load_bundle()
    manifest = bundle["manifest"]
    lo = np.asarray(manifest["action"]["bounds_lo"], dtype=np.float32)
    hi = np.asarray(manifest["action"]["bounds_hi"], dtype=np.float32)

    res = run_closed_loop(bundle, build_id, p, seed, horizon, collect_records=True)

    gates = {}
    nan_free = True
    for v in res["v_series"] + [0.0]:
        if not np.isfinite(v):
            nan_free = False
            break
    bounds_ok = all(all(l - 1e-6 <= c <= h + 1e-6 for c, l, h in zip(applied, lo, hi))
                    for applied in res["applied_per_tick"])
    intv_ok = all(r["intervention_reason"] == "none" for r in res["records"])
    contact_ok = all(r["contact_count"] >= 2 for r in res["records"])
    avail_ok = all(set(r["available_groups"]) == set(AVAILABLE_GROUPS)
                   for r in res["records"])
    envelope_ok = all(abs(v) <= v_env for v in res["v_series"])
    gates = {"bounds_honored": bounds_ok, "no_nan_inf": nan_free,
             "no_intervention": intv_ok, "contact_floor": contact_ok,
             "availability_exact": avail_ok, "velocity_envelope": envelope_ok}

    # the refusal is exercised for real: no input channel accepts actions
    refusals = []
    try:
        requalify(bundle, build_id, p, seed, horizon,
                  precomputed_actions=res["applied_per_tick"])
        refusals.append(None)  # ACCEPTED: the refusal FAILED
    except PolicyCompatError as exc:
        refusals.append(str(exc) if "ACTION_REPLAY_REFUSED" in str(exc) else None)
    try:
        requalify(bundle, build_id, p, seed, horizon, mode="action_replay")
        refusals.append(None)
    except PolicyCompatError as exc:
        refusals.append(str(exc) if "ACTION_REPLAY_REFUSED" in str(exc) else None)

    passed = all(gates.values()) and all(r is not None for r in refusals)
    report = {
        "check": "CHECK_3_closed_loop_requalification",
        "pass": passed,
        "build_id": build_id,
        "build_delta": BUILD_N1_DELTA_NOTE,
        "seed": seed, "horizon_ticks": horizon,
        "gates": gates,
        "max_abs_v_m_s": max(abs(v) for v in res["v_series"]),
        "velocity_envelope_m_s": v_env,
        "action_replay_refusals": refusals,
        "refusal_rationale": (
            "The harness REFUSES action-replay input by construction (no input "
            "channel accepts a pre-recorded action stream; attempts raise "
            "ACTION_REPLAY_REFUSED). WHY: replaying build-N actions into build "
            "N+1 tests the OLD trajectory, not the coupled system -- the "
            "failure mode the gate exists to catch is what the new physics' "
            "RESPONSES do to the loop; an action-replay would certify noise "
            "and structurally cannot see the feedback divergence it must "
            "detect. Observations and actions are therefore recomputed from "
            "the NEW trajectory at every tick."),
        "non_regression_margins": [{"name": "crossbuild_openloop_max_dv",
                                    "quantity": "max|v_N1 - v_N| over the "
                                                "registered open-loop cases",
                                    "bound": env["openloop_crossbuild_margin_m_s"],
                                    "derivation": env["derivation"]}],
        "detail": (f"closed-loop requal on {build_id}: gates "
                   f"{'ALL GREEN' if all(gates.values()) else sorted(k for k, v in gates.items() if not v)}; "
                   f"action-replay refused {sum(1 for r in refusals if r is not None)}/2 probes"),
    }
    with open(os.path.join(out_dir, "check3_report.json"), "w", encoding="utf-8",
              newline="\n") as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write("\n")
    return report, res


def requalify(bundle: dict, build_id: str, p: dict, seed: int, horizon: int,
              mode: str = "closed_loop", precomputed_actions=None) -> dict:
    """The requalification entry point. There is deliberately NO parameter that
    accepts a pre-recorded action stream: observations and actions are
    recomputed from the NEW trajectory every tick. Any attempt to pass actions
    (or the action_replay mode) raises ACTION_REPLAY_REFUSED."""
    if precomputed_actions is not None or mode != "closed_loop":
        raise PolicyCompatError(
            "ACTION_REPLAY_REFUSED: the requalification harness does not accept "
            "pre-recorded actions or an action_replay mode -- replaying build-N "
            "actions into the new build tests the old trajectory and misses the "
            "feedback-loop divergence the gate exists to detect; observations "
            "and actions are recomputed from the NEW trajectory every tick "
            "(prereg receipt.json, P7)")
    report, _ = check3(LANE_DIR, seed, horizon)
    return report


# --------------------------------------------------------------- issuance

def scene_module_sha() -> str:
    with open(os.path.join(REPO, "tools", "policy_compat", "scene_cpu.py"), "rb") as f:
        return sha256_hex(f.read())


def build_relation(bundle: dict, build_id: str, p: dict) -> dict:
    manifest = bundle["manifest"]
    with open(RECEIPT, "rb") as f:
        receipt_bytes = f.read()
    receipt = json.loads(receipt_bytes.decode("utf-8"))
    cases = receipt["pre_registration"]["registered_cases"]
    env = bundle["pman"].build_env()
    return {
        "policy_bundle": {
            "manifest_hash": manifest["manifest_hash"],
            "weights_sha256": manifest["policy"]["weights_sha256"],
            "manifest_file_sha256": bundle["manifest_file_sha256"],
            "weights_file_sha256": bundle["weights_file_sha256"],
            "architecture": manifest["policy"]["architecture"],
            "activation": manifest["policy"]["activation"],
            "normalization_clip": manifest["normalization"].get("clip", 8.0),
            "loader": "typeb_export.policy_manifest.load_manifest (frozen)",
        },
        "physics_build": {
            "build_id": build_id,
            "scene_version": SCENE_VERSION,
            "scene_module": "tools/policy_compat/scene_cpu.py",
            "scene_module_sha256": scene_module_sha(),
            "params_sha256": params_sha(p),
            "timestep_s": p["dt"],
        },
        "runtime_profile": {
            **env,
            "policy_hz": manifest["action"]["clock"]["policy_hz"],
            "physics_hz": manifest["action"]["clock"]["physics_hz"],
            "hold_ticks": manifest["action"]["clock"]["hold_ticks"],
            "inference_recipe": manifest["inference"].get("recipe",
                                                          "pinned-by-manifest-hash"),
        },
        "body_domain": {
            "body_digest": "UNBOUND_dummy (P3 manifest body: status UNBOUND -- "
                           "binds automatically when the real actor exists)",
            "domain_tag": "cpu-walk-scene/hind-pad-surrogate",
        },
        "test_suite": {
            "id": SUITE_ID,
            "prereg_registered_cases_sha256": sha256_hex(canonical_json(cases)),
            "event_stride": EVENT_STRIDE,
            "corpus": "frozen P3 900-tick/60-decision sequence",
        },
    }


def inventory_block() -> dict:
    return {
        "deployment_class": "surrogate",
        "items": [
            {"name": "body_state", "snapshotable": True,
             "snapshot_key": "scene.body_state", "contents": "com speed v, com position x, per-leg phases"},
            {"name": "contact_warm_start_cache", "snapshotable": True,
             "snapshot_key": "scene.contact_warm_start_cache",
             "contents": "per-hind-leg warm anchors + contact flags (trajectory-visible coupling)"},
            {"name": "reflex_state", "snapshotable": True,
             "snapshot_key": "scene.reflex_state", "contents": "per-leg trip tick counters"},
            {"name": "held_command", "snapshotable": True,
             "snapshot_key": "scene.held_command",
             "contents": "held 8-vector + saturation + phase offsets + lift amps"},
            {"name": "decision_phase", "snapshotable": True,
             "snapshot_key": "policy.decision_phase",
             "contents": "policy clock tick + decision count (hold phase exact)"},
            {"name": "controller_history", "snapshotable": True,
             "snapshot_key": "policy.controller_history",
             "contents": "prev applied/saturation, ticks-since-intervention/reset, prev yaw rate"},
            {"name": "rng_stream", "snapshotable": True,
             "snapshot_key": "scene.rng_stream",
             "contents": "PCG64 bit-generator state (position matters; one draw/tick)"},
            {"name": "world_state", "snapshotable": True,
             "snapshot_key": "scene.world_state",
             "contents": "terrain draws consumed + last micro height + build/params identity"},
        ],
        "registered_gaps": [
            {"name": "gap_engine_contact_warm_start", "item": "contact_warm_start_cache",
             "status": "REGISTERED GAP (pending engine binding)",
             "cause": "the C++ solver's contact/warm-start caches are not yet exposed by a snapshot API",
             "clears_when": "the engine exposes solver cache serialize/restore and CHECK 1 passes bit-identical through it"},
            {"name": "gap_engine_reflex_state", "item": "reflex_state",
             "status": "REGISTERED GAP (pending engine binding)",
             "cause": "the banked reflex set's internal state is not yet snapshotable in the engine controller",
             "clears_when": "reflex serialize/restore exists and resumes bit-identically"},
            {"name": "gap_engine_controller_history", "item": "controller_history",
             "status": "REGISTERED GAP (pending engine binding)",
             "cause": "the gait controller's internal calendars/history are not yet snapshotable",
             "clears_when": "controller state serialize/restore exists and resumes bit-identically"},
            {"name": "gap_engine_world_state", "item": "world_state",
             "status": "REGISTERED GAP (pending engine binding)",
             "cause": "full engine world state beyond the entry pose is not yet serializable",
             "clears_when": "world serialize/restore exists and resumes bit-identically"},
        ],
        "gap_rule": "PRODUCTION certificates REQUIRE zero unresolved gaps "
                    "(validator-enforced BLOCK); surrogate/evaluation classes "
                    "carry their gaps declared. This lane CANNOT measure the "
                    "engine's snapshot coverage (no engine binary touched); the "
                    "gaps are registered at the schema level against the "
                    "production path.",
    }


def scope_block() -> dict:
    env = derived_envelope()
    return {
        "bodies": ["UNBOUND_dummy (the P3 dummy actor; the certificate binds the "
                   "bundle hashes, so the real actor binds by reissuance with "
                   "identical machinery)"],
        "skills": ["level-ground forward walk surrogate (the declared CPU walk scene)"],
        "transitions": ["entry from rest at the manifest center commands"],
        "ranges": {"phase": "[0,1) per leg", "pad_gap_m": "[0, clearance + lift_amp_hi*1 + micro_terrain_amp]",
                   "com_speed_m_s": f"[0, {env['velocity_envelope_m_s']!r}] (the derived envelope V)"},
        "horizons": {"ticks": 900, "decisions": 60, "hold_ticks": 15},
        "bars": {
            "bounds_honored": "every applied command within the manifest limiter bounds",
            "no_nan_inf": "no NaN/Inf in any recorded state quantity",
            "no_intervention": "intervention_reason == none at every tick",
            "contact_floor": "contact_count >= 2 at every tick",
            "availability_exact": "available_groups exactly the declared set",
            "velocity_envelope": f"|v_t| <= V = {env['velocity_envelope_m_s']!r} m/s at every tick",
        },
        "non_regression_margins": [
            {"name": "crossbuild_openloop_max_dv",
             "quantity": "max|v_N1 - v_N| over the registered open-loop cases",
             "bound": env["openloop_crossbuild_margin_m_s"],
             "derivation": env["derivation"]},
        ],
        "universal_proof_disclaimer": "agreement on registered cases is evidence, "
                                      "never universal proof",
    }


def issue_from_run(out_dir: str, build_id: str, p: dict, run: dict,
                   monitors: list[dict]) -> dict:
    bundle = load_bundle()
    relation = build_relation(bundle, build_id, p)
    with open(os.path.join(LANE_DIR, "receipt.json"), "rb") as f:
        receipt = json.loads(f.read().decode("utf-8"))
    evidence = {
        "initial_snapshot_sha256": run["initial_snapshot_sha256"],
        "events": run["events"],
        "periodic_stride": EVENT_STRIDE,
        "final_state_sha256": run["final_state_sha256"],
        "monitors": monitors,
        "trajectory_sha256": sha256_hex(run["traj_bytes"]),
    }
    cert = issue_certificate(relation, inventory_block(), evidence, scope_block(),
                             {"issued_by": ISSUED_BY, "lane": "upgrade-gate-20260920",
                              "base_commit": "bd4bf630",
                              "prereg_receipt": "tools/science_funnel/validation/"
                                                "upgrade_gate_20260920/receipt.json",
                              "prereg_rule0_sha": receipt["pre_registration"]["frozen_rule_0_sha"]})
    errs = validate_certificate(cert)
    if errs:
        raise PolicyCompatError("issued certificate failed its own validator: " + "; ".join(errs))
    return cert


# --------------------------------------------------------- clean pipeline

def clean_pipeline(run_id: str, out_dir: str, seed: int = 20260920,
                   horizon: int = 900, checkpoint_tick: int = 317) -> dict:
    """One full gate pass: corpus -> runs -> checks 1-3 -> issue -> deploy checks.
    Wall-clock is never written to canonical payloads. Returns the canonical
    result bundle (3 runs of this must be byte-identical -- P4)."""
    bundle = load_bundle()
    os.makedirs(out_dir, exist_ok=True)

    corpus = build_corpus(bundle)
    # the frozen-ref cross-check: the corpus must equal the P3 lane's own
    # recorded fresh-process action bytes (same manifest, same sequence, same
    # recipe, same runtime) -- recorded, and asserted.
    p3_actions = os.path.join(P3_DIR, "actions_run1.bin")
    with open(p3_actions, "rb") as f:
        p3_sha = sha256_hex(f.read())
    corpus_matches_p3 = corpus["actions_sha256"] == p3_sha
    if not corpus_matches_p3:
        raise PolicyCompatError(
            "CORPUS DRIFT: the corpus actions do not reproduce the P3 lane's "
            f"recorded bytes ({corpus['actions_sha256'][:16]}... vs {p3_sha[:16]}...)")

    # CHECK 1 (fresh-process workers, raw bytes)
    c1 = check1(out_dir, seed, horizon, checkpoint_tick)

    # closed-loop build N runs for the three registered seeds (stream sources)
    _, pn = build_n()
    streams: dict[int, list[list[float]]] = {}
    cl_n_runs: dict[int, dict] = {}
    for s in (20260919, 20260920, 20260921):
        res = run_closed_loop(bundle, "cpu-walk-scene-build-N", pn, s, horizon)
        streams[s] = res["applied_per_tick"]
        cl_n_runs[s] = res

    with open(os.path.join(LANE_DIR, "receipt.json"), "rb") as f:
        receipt = json.loads(f.read().decode("utf-8"))
    cases = receipt["pre_registration"]["registered_cases"]["openloop_crossbuild"]
    c2 = check2(out_dir, streams, cases)

    c3, run_n1 = check3(out_dir, seed, horizon)

    envelope_n = all(abs(v) <= derived_envelope()["velocity_envelope_m_s"]
                     for v in cl_n_runs[seed]["v_series"])

    monitors = [
        {"name": "corpus_reproduces_p3_bytes", "pass": corpus_matches_p3,
         "detail_sha256": sha256_hex(canonical_json(corpus))},
        {"name": "CHECK_1_replay_resume_bit_identical", "pass": c1["pass"],
         "detail_sha256": sha256_hex(canonical_json(c1))},
        {"name": "CHECK_2_registered_openloop_within_derived_margin", "pass": c2["pass"],
         "detail_sha256": sha256_hex(canonical_json(c2))},
        {"name": "CHECK_3_closed_loop_requal_gates_and_refusal", "pass": c3["pass"],
         "detail_sha256": sha256_hex(canonical_json(c3))},
        {"name": "build_N_closed_loop_envelope", "pass": envelope_n,
         "detail_sha256": sha256_hex(np.asarray(cl_n_runs[seed]["v_series"], "<f8").tobytes())},
    ]

    cert = issue_from_run(out_dir, "cpu-walk-scene-build-N", pn,
                          cl_n_runs[seed], monitors)

    # deploy checks: the matching tuple ALLOWs; a foreign build BLOCKs
    req = {k: cert["relation"][k] for k in
           ("policy_bundle", "physics_build", "runtime_profile", "body_domain", "test_suite")}
    allow = check_deploy(req, cert)
    foreign = dict(req)
    foreign["physics_build"] = dict(req["physics_build"])
    foreign["physics_build"]["build_id"] = "cpu-walk-scene-build-N+1"
    block_foreign = check_deploy(foreign, cert)
    block_missing = check_deploy(req, None)

    if not (allow["decision"] == "ALLOW" and block_foreign["decision"] == "BLOCK"
            and block_missing["decision"] == "BLOCK"):
        raise PolicyCompatError("deploy gate sanity failed: "
                                f"{allow['decision']}/{block_foreign['decision']}/"
                                f"{block_missing['decision']}")

    return {
        "suite": SUITE_ID,
        "schema_version": SCHEMA_VERSION,
        "corpus": corpus,
        "p3_recorded_actions_sha256": p3_sha,
        "check1": c1,
        "check2": c2,
        "check3": c3,
        "build_N_envelope_ok": envelope_n,
        "certificate": cert,
        "deploy_allow": allow,
        "deploy_block_foreign_build": block_foreign,
        "deploy_block_missing_certificate": block_missing,
    }
