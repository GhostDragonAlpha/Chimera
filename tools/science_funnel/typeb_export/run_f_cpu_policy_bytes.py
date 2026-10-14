"""TypeB-P3: F-CPU-POLICY-BYTES driver.

Clause (a): the same manifest evaluated twice in FRESH processes must produce
byte-identical action streams on the fixed observation sequence (3 passes over the
recorded wave-38 slice = 900 ticks = 60 decisions at hold 15).

Clause (b): the manifest hash pins every component -- 14 preregistered single-field
mutations (plus a real seed+1 weight regeneration) must ALL move the canonical hash.

Fires (fails) on any byte difference or any mutation that leaves the hash unchanged.
Usage: python run_f_cpu_policy_bytes.py driver <validation_dir>
       python run_f_cpu_policy_bytes.py worker <validation_dir> <out.bin> <out.json>
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dummy_actor  # noqa: E402
import policy_manifest as pman  # noqa: E402
from infer_numpy import NumpyPolicy  # noqa: E402


def fixed_obs_sequence(slice_path: str, passes: int, max_ticks: int | None = None) -> list[dict]:
    with open(slice_path, "rb") as f:
        sl = json.loads(f.read().decode("utf-8"))
    ticks = sl["ticks"]
    n = len(ticks)
    total = n * passes
    if max_ticks is not None:
        total = min(total, max_ticks)
    return [ticks[t % n] for t in range(total)]


def replay(policy: NumpyPolicy, seq: list[dict]) -> tuple[bytes, list[list[float]]]:
    policy.reset()
    per_tick: list[float] = []
    per_decision: list[list[float]] = []
    for rec in seq:
        applied, info = policy.act(rec)
        per_tick.extend(float(v) for v in applied)
        if info["deciding"]:
            per_decision.append([float(v) for v in applied])
    return np.asarray(per_tick, dtype="<f4").tobytes(), per_decision


def worker(validation_dir: str, out_bin: str, out_json: str) -> None:
    manifest = pman.load_manifest(
        os.path.join(validation_dir, "policy_manifest.json"),
        os.path.join(validation_dir, "dummy_actor.npz"))
    ev = manifest["evaluation"]["fixed_obs_sequence"]
    seq = fixed_obs_sequence(os.path.join(validation_dir, "trace_slice_wave38.json"),
                             ev["passes"], ev["n_ticks"])
    params = dict(np.load(os.path.join(validation_dir, "dummy_actor.npz")))
    policy = NumpyPolicy(manifest, params)
    stream, per_decision = replay(policy, seq)
    with open(out_bin, "wb") as f:
        f.write(stream)
    digest = hashlib.sha256(stream).hexdigest()
    with open(out_json, "w") as f:
        json.dump({"sha256": digest, "bytes": len(stream),
                   "n_decisions": len(per_decision),
                   "decisions": per_decision}, f, indent=1)
    print("worker sha256:", digest, f"({len(stream)} bytes, {len(per_decision)} decisions)")


def mutations(manifest: dict) -> dict[str, dict]:
    """The 14 preregistered single-component mutations + the real weight rebuild."""
    muts: dict[str, dict] = {}

    def add(name, fn):
        m = copy.deepcopy(manifest)
        m.pop("manifest_hash", None)
        fn(m)
        muts[name] = m

    add("weights_sha256_field", lambda m: m["policy"].__setitem__(
        "weights_sha256", "0" * 64))
    add("arch_dims", lambda m: m["policy"]["architecture"].__setitem__(1, 127))
    add("activation", lambda m: m["policy"].__setitem__("activation", "relu"))
    add("obs_field_name", lambda m: (
        m["observation"]["order"].__setitem__(4, "gait_phase_fraction"),
        m["observation"]["per_field"].__setitem__(
            "gait_phase_fraction", m["observation"]["per_field"].pop("gait_phase_frac"))))
    add("obs_order_swap", lambda m: m["observation"]["order"].__setitem__(
        4, m["observation"]["order"][5]) or
        m["observation"]["order"].__setitem__(5, "gait_phase_frac"))
    add("normalization_entry", lambda m: m["normalization"]["std"].__setitem__(0, 1.001))
    add("action_bound", lambda m: m["action"]["bounds_hi"].__setitem__(0, 0.26))
    add("action_scale", lambda m: m["action"]["scale"].__setitem__(0, 0.125001))
    add("hold_ticks", lambda m: m["action"]["clock"].__setitem__("hold_ticks", 14))
    add("policy_hz", lambda m: m["action"]["clock"].__setitem__("policy_hz", 19))
    add("reset_phase0", lambda m: m["reset"].__setitem__("phase0", 0.05))
    add("reflex_version", lambda m: m["reflex_set"].__setitem__(
        "version", "wave38-banked-reflex/1.0.1"))
    add("physics_version", lambda m: m["physics_version"].__setitem__("version", "wave38b"))
    add("eval_seed", lambda m: m["evaluation"].__setitem__("seed", 20260922))
    return muts


def driver(validation_dir: str) -> dict:
    mpath = os.path.join(validation_dir, "policy_manifest.json")
    wpath = os.path.join(validation_dir, "dummy_actor.npz")
    manifest = pman.load_manifest(mpath, wpath)
    base_hash = manifest["manifest_hash"]

    # clause (a): two fresh processes
    outs = []
    for i in (1, 2):
        b = os.path.join(validation_dir, f"actions_run{i}.bin")
        j = os.path.join(validation_dir, f"actions_run{i}.json")
        r = subprocess.run([sys.executable, os.path.abspath(__file__), "worker",
                            validation_dir, b, j], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"worker {i} failed:\n{r.stdout}\n{r.stderr}")
        with open(b, "rb") as f:
            outs.append(f.read())
    byte_identity = outs[0] == outs[1]
    stream_sha = hashlib.sha256(outs[0]).hexdigest()

    # clause (b): every pinned component moves the hash
    results = {}
    for name, m in mutations(manifest).items():
        h = pman.manifest_hash(m)
        results[name] = {"changed": h != base_hash, "hash": h}
    # real weights regeneration (not just the field)
    p2 = dummy_actor.export_dummy_actor(seed=dummy_actor.SEED + 1)
    results["weights_regenerated_seed_plus_1"] = {
        "changed": dummy_actor.weights_sha256(p2) != manifest["policy"]["weights_sha256"]}

    all_moved = all(v["changed"] for v in results.values())
    passed = byte_identity and all_moved
    report = {
        "falsifier": "F-CPU-POLICY-BYTES",
        "fires": not passed,
        "pass": passed,
        "clause_a_byte_identity": {
            "pass": byte_identity, "sha256_run1": hashlib.sha256(outs[0]).hexdigest(),
            "sha256_run2": hashlib.sha256(outs[1]).hexdigest(),
            "bytes": len(outs[0]), "identical": byte_identity},
        "clause_b_component_pinning": {
            "pass": all_moved, "base_hash": base_hash,
            "mutations": results},
        "detail": (
            f"two fresh processes produced {'BYTE-IDENTICAL' if byte_identity else 'DIFFERING'} "
            f"action streams (sha256 {stream_sha[:16]}..., {len(outs[0])} bytes, 60 decisions); "
            f"{sum(1 for v in results.values() if v['changed'])}/{len(results)} component "
            f"mutations moved the manifest hash "
            f"({base_hash[:16]}...)"
        ),
    }
    with open(os.path.join(validation_dir, "hash_pin.json"), "w") as f:
        json.dump(report, f, indent=1)
    return report


if __name__ == "__main__":
    mode = sys.argv[1]
    vd = os.path.abspath(sys.argv[2])
    if mode == "worker":
        worker(vd, sys.argv[3], sys.argv[4])
    else:
        rep = driver(vd)
        print(json.dumps({"falsifier": rep["falsifier"], "pass": rep["pass"],
                          "fires": rep["fires"], "detail": rep["detail"]}, indent=1))
