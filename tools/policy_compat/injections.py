"""The injection suite: every preregistered incompatibility is injected FOR
REAL and must be CAUGHT; the falsifier verdicts are recorded per injection.

  I1 (F1): perturb ONE periodic state hash inside the issued certificate's
      evidence chain (AND recompute cert_hash -- the sophisticated-attacker
      form) -> the chain verification must invalidate -> deploy BLOCK.
  I2 (F1): swap ONE normalization constant in a COPIED manifest -> the
      canonical manifest hash moves (the P3 clause-b property) -> compat_key
      mismatch -> deploy BLOCK; AND the corpus actions move (second detection).
  I3 (F2): drop the RNG stream from a restart snapshot -> structural refusal
      naming the missing inventory item, AND the forced resume moves the
      continuation bytes. (The drop-warm case is proven in CHECK 1 itself.)
  I4 (F3): alter ONE action-mapping entry in a COPIED manifest -> the frozen
      corpus action bytes differ in the same runtime -> DETECTED byte-wise,
      plus the structural hash movement.

No false positives (P4/FP): three clean_pipeline runs on the unmodified
artifacts must produce BYTE-IDENTICAL canonical bundles.
"""
from __future__ import annotations

import copy
import json
import os

import numpy as np

from .certificate import canonical_json, cert_hash, check_deploy, sha256_hex, \
    validate_certificate
from .runner import (P3_DIR, PolicyCompatError, build_corpus, check1, clean_pipeline,
                     load_bundle)


def _write(path: str, obj) -> bytes:
    b = canonical_json(obj) if isinstance(obj, dict) else obj
    with open(path, "wb") as f:
        f.write(b)
    return b


def _corpus_actions_for(manifest: dict, bundle: dict, passes: int = 3,
                        n_ticks: int = 900) -> tuple[str, int]:
    """Corpus actions under an arbitrary (possibly tampered) manifest, same
    frozen recipe, same runtime."""
    with open(os.path.join(P3_DIR, "trace_slice_wave38.json"), "rb") as f:
        ticks = json.loads(f.read().decode("utf-8"))["ticks"]
    n = len(ticks)
    seq = [ticks[t % n] for t in range(min(n * passes, n_ticks))]
    policy = bundle["NumpyPolicy"](manifest, bundle["params"])
    policy.reset()
    per_tick: list[float] = []
    for rec in seq:
        applied, _ = policy.act(rec)
        per_tick.extend(float(v) for v in applied)
    stream = np.asarray(per_tick, dtype="<f4").tobytes()
    return sha256_hex(stream), len(stream)


def run_injections(work_dir: str, cert: dict, deploy_request: dict, clean_corpus_sha: str,
                   snapshot_path: str, reference_full_bin: str,
                   seed: int, horizon: int, checkpoint_tick: int) -> dict:
    """cert: the clean issued certificate; deploy_request: its matching 5-tuple;
    clean_corpus_sha: the pinned corpus bytes; snapshot_path/reference_full_bin:
    CHECK 1's checkpoint + uninterrupted artifacts. Every verdict must be
    CAUGHT; a single MISSED is a fired falsifier."""
    os.makedirs(work_dir, exist_ok=True)
    bundle = load_bundle()
    results: dict[str, dict] = {}

    # ---------------------------------------------------------- I1 (F1)
    tampered = copy.deepcopy(cert)
    victim = tampered["replay_evidence"]["events"][5]
    victim["state_sha256"] = ("deadbeef" + victim["state_sha256"][8:])[:64]
    tampered["cert_hash"] = cert_hash(tampered)   # attacker fixes the outer hash
    violations = validate_certificate(tampered)
    deploy = check_deploy(deploy_request, tampered)
    caught = (deploy["decision"] == "BLOCK"
              and any("chain mismatch" in v or "INVALIDATED" in v for v in violations))
    results["I1_perturbed_state_hash"] = {
        "falsifier": "F1_silent_promotion", "verdict": "CAUGHT" if caught else "MISSED",
        "validator_violations": violations,
        "deploy_decision": deploy["decision"],
        "detail": ("perturbed the tick-5 periodic state hash AND recomputed "
                   f"cert_hash (the sophisticated-attacker form): the hash-chain "
                   f"recomputation invalidated the evidence -> {deploy['decision']}")}

    # ---------------------------------------------------------- I2 (F1)
    with open(os.path.join(P3_DIR, "policy_manifest.json"), "rb") as f:
        raw = json.loads(f.read().decode("utf-8"))
    tampered_manifest = copy.deepcopy(raw)
    tampered_manifest["normalization"]["std"][0] = \
        tampered_manifest["normalization"]["std"][0] * 1.001
    errs = bundle["pman"].validate_manifest(tampered_manifest)  # structurally valid
    tampered_hash = bundle["pman"].manifest_hash(tampered_manifest)
    clean_hash = cert["relation"]["policy_bundle"]["manifest_hash"]
    req2 = copy.deepcopy(deploy_request)
    req2["policy_bundle"] = dict(deploy_request["policy_bundle"])
    req2["policy_bundle"]["manifest_hash"] = tampered_hash
    deploy2 = check_deploy(req2, cert)
    acts_sha, _ = _corpus_actions_for(tampered_manifest, bundle)
    corpus_moved = acts_sha != _clean_corpus_sha()
    caught2 = (deploy2["decision"] == "BLOCK"
               and tampered_hash != clean_hash and corpus_moved
               and not errs)
    results["I2_swapped_normalization_constant"] = {
        "falsifier": "F1_silent_promotion", "verdict": "CAUGHT" if caught2 else "MISSED",
        "structural_manifest_hash_moved": tampered_hash != clean_hash,
        "tampered_manifest_hash": tampered_hash,
        "tampered_manifest_structurally_valid": not errs,
        "deploy_decision": deploy2["decision"],
        "corpus_actions_sha256_under_tampered_manifest": acts_sha,
        "corpus_actions_moved": corpus_moved,
        "detail": ("normalization.std[0] x1.001 in a COPIED manifest: the "
                   "canonical manifest hash moved (compat_key mismatch -> "
                   f"{deploy2['decision']}) AND the corpus action bytes moved "
                   "(second detection)")}

    # ---------------------------------------------------------- I3 (F2)
    with open(snapshot_path, "r", encoding="utf-8") as f:
        snap = json.load(f)
    broken = copy.deepcopy(snap)
    broken["scene"].pop("rng_stream")
    from .scene_cpu import SnapshotError, build_n, make_scene  # noqa: PLC0415
    _, p = build_n()
    scene = make_scene("cpu-walk-scene-build-N", p, seed)
    refusal = None
    try:
        scene.restore_snapshot(broken)
    except SnapshotError as exc:
        refusal = str(exc)
    pf = os.path.join(work_dir, "i3_resume_forced")
    rf = _worker("resume-forced", [snapshot_path, pf, str(seed), str(horizon),
                                   str(checkpoint_tick), "rng"])
    contf = open(pf + ".bin", "rb").read()
    with open(reference_full_bin, "rb") as f:
        full = f.read()
    tail = full[checkpoint_tick * 32:]
    full_doc = json.load(open(os.path.splitext(reference_full_bin)[0] + ".json",
                              encoding="utf-8"))
    fj = json.load(open(pf + ".json", encoding="utf-8"))
    n_full_events = len(full_doc["events"])
    state_moved = (fj["events"] != full_doc["events"][n_full_events - len(fj["events"]):]
                   or fj["final_state_sha256"] != full_doc["final_state_sha256"])
    moved = state_moved or contf != tail
    caught3 = refusal is not None and moved and rf.returncode == 0
    results["I3_dropped_rng_from_restart_snapshot"] = {
        "falsifier": "F2_resume_drift", "verdict": "CAUGHT" if caught3 else "MISSED",
        "structural_refusal": refusal,
        "state_hashes_moved": state_moved,
        "action_bytes_moved": contf != tail,
        "forced_resume_differs": moved,
        "forced_missing_reported": fj["forced_missing"],
        "detail": ("dropped rng_stream from the checkpoint-317 snapshot: the "
                   "loader REFUSED naming the missing inventory item, and the "
                   "FORCED resume moved the continuation TRAJECTORY (the "
                   "tick-wise state hashes diverge from the first tick -- the "
                   "micro-terrain draws are trajectory-visible by declaration; "
                   "the v1 observation masks pad channels so the action bytes "
                   "may stay identical, which is exactly why the gate's "
                   "evidence currency is the state hash, not only the actions)")}

    # ---------------------------------------------------------- I4 (F3)
    tampered_action = copy.deepcopy(raw)
    tampered_action["action"]["scale"][2] = \
        tampered_action["action"]["scale"][2] + 0.000001
    errs4 = bundle["pman"].validate_manifest(tampered_action)
    hash4 = bundle["pman"].manifest_hash(tampered_action)
    acts4_sha, _ = _corpus_actions_for(tampered_action, bundle)
    moved4 = acts4_sha != clean_corpus_sha
    caught4 = moved4 and hash4 != clean_hash and not errs4
    results["I4_altered_action_mapping_entry"] = {
        "falsifier": "F3_legacy_action_drift", "verdict": "CAUGHT" if caught4 else "MISSED",
        "structural_manifest_hash_moved": hash4 != clean_hash,
        "tampered_manifest_hash": hash4,
        "corpus_actions_sha256_under_tampered_mapping": acts4_sha,
        "corpus_actions_moved": moved4,
        "detail": ("action.scale[2] 0.4 -> 0.400001 on the FROZEN observation/"
                   "command corpus in the SAME runtime: the recomputed corpus "
                   "action bytes differ from the pinned bytes (byte-wise "
                   "detection) AND the manifest hash moved")}

    all_caught = all(r["verdict"] == "CAUGHT" for r in results.values())
    report = {
        "suite": "upgrade_gate_20260920/injections_v1",
        "all_caught": all_caught,
        "falsifier_summary": {
            "F1_silent_promotion": "CAUGHT" if
                results["I1_perturbed_state_hash"]["verdict"] == "CAUGHT"
                and results["I2_swapped_normalization_constant"]["verdict"] == "CAUGHT"
                else "FIRED",
            "F2_resume_drift": "CAUGHT" if
                results["I3_dropped_rng_from_restart_snapshot"]["verdict"] == "CAUGHT"
                else "FIRED",
            "F3_legacy_action_drift": "CAUGHT" if
                results["I4_altered_action_mapping_entry"]["verdict"] == "CAUGHT"
                else "FIRED",
        },
        "injections": results,
    }
    _write(os.path.join(work_dir, "injections_report.json"), report)
    return report


def _worker(mode: str, args: list[str]):
    import subprocess, sys
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return subprocess.run([sys.executable, "-B", "-m", "tools.policy_compat", mode, *args],
                          cwd=repo, capture_output=True, text=True)


_CLEAN_CORPUS: str | None = None


def _clean_corpus_sha() -> str:
    global _CLEAN_CORPUS
    if _CLEAN_CORPUS is None:
        bundle = load_bundle()
        _CLEAN_CORPUS = build_corpus(bundle)["actions_sha256"]
    return _CLEAN_CORPUS


def run_clean_triple(out_dir: str, seed: int, horizon: int, checkpoint_tick: int) -> dict:
    """P4/FP: three clean full-pipeline runs -> byte-identical bundles."""
    bundles = []
    for i in (1, 2, 3):
        b = clean_pipeline(f"clean_{i}", out_dir, seed, horizon, checkpoint_tick)
        blobs = canonical_json(b)
        bundles.append(blobs)
    identical = bundles[0] == bundles[1] == bundles[2]
    report = {
        "suite": "upgrade_gate_20260920/clean_triple_v1",
        "pass": identical,
        "bundle_sha256": [sha256_hex(b) for b in bundles],
        "detail": ("three clean full-gate runs (corpus -> runs -> checks 1-3 -> "
                   "issue -> deploy checks) produced "
                   f"{'BYTE-IDENTICAL' if identical else 'DIFFERING'} canonical "
                   "bundles -- no false positives on the unmodified artifacts"),
    }
    with open(os.path.join(out_dir, "clean_triple_report.json"), "w",
              encoding="utf-8", newline="\n") as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write("\n")
    return report
