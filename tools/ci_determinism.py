"""ci_determinism.py -- assert the physics is STABLE across runs, at two strengths.

MEMBRANE (Rule 0, stated before the build):
  STATEMENT : the engine is deterministic; the same primitive/action, asked the same
              question from the same initial condition, returns the same VERDICT every run --
              and the physics underneath the verdict is bit-identical: the same MuJoCo model,
              integrator, timestep and initial state yield the same joint angles, velocities
              and forces at every step (theDeterminism's S4 experiment, pre-registered in
              docs/THE_DETERMINISM_S4.md).
  PREDICTION: across N repeated runs, every item's verdict (pass / refused / fail) is
              identical run-to-run; and across 2 recorded runs, the per-step state digest
              stream (time, qpos, qvel, qacc, qfrc_applied, ctrl, actuator_force) is EXACTLY
              equal -- bit-identity, which implies the pre-registered 1e-15 tolerance with
              max |delta| = 0.
  FALSIFIER : any item whose verdict FLIPS between runs; or any digest mismatch between the
              two recorded runs -> the harness exits non-zero and names the first divergent
              step. (A stable FAIL or stable REFUSED is NOT a flip; pre-existing gaps are
               allowed to be stably wrong. Only non-determinism is a defect.)

Run:  python -m tools.ci_determinism [N]
  N = number of verdict repetitions (default 3). Trajectories are always compared across 2.
Prints a JSON stability report and exits 0 if everything is stable, 1 otherwise.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import tools.action_tests as at
import tools.primitive_tests as pt


def _verdict(meta):
    """Call one registered item and reduce its result to a stable label."""
    try:
        r = meta["fn"](None)
    except Exception as exc:  # noqa: BLE001 - a crash is itself a verdict to track
        return f"error:{type(exc).__name__}"
    if r.get("pass_"):
        return "pass"
    if r.get("refused"):
        return "refused"
    return "fail"


# ------------------------------------------------------------------------------------------------
# THE TRAJECTORY RECORDER (S4). Wraps mujoco.mj_step so every step the SUITE ACTUALLY RUNS leaves
# a 16-byte digest of the state the step produced. A digest stream is compared EXACTLY: equality
# is bit-identity, strictly stronger than the pre-registered 1e-15. Recording the raw arrays
# instead would cost hundreds of MB over a full suite; on a mismatch the failing item is re-run
# with raw recording to quantify max |delta| -- expensive only on failure.
# ------------------------------------------------------------------------------------------------
class StepRecorder:
    # qfrc_constraint (the contact/constraint force field), qacc_warmstart (the solver's carried
    # warm-start state) and act (the Hill actuators' internal activation) are recorded NAMED:
    # the S5 why-terminal points each discovered variable at its own measured stream.
    FIELDS = ("time", "qpos", "qvel", "qacc", "qacc_warmstart", "qfrc_applied",
              "qfrc_constraint", "ctrl", "act", "actuator_force")

    def __init__(self):
        self.digests = []
        self.stream_h = {f: hashlib.blake2b(digest_size=16) for f in self.FIELDS}
        self.raw = None          # when not None, raw arrays are kept too (failure quantification)
        self._orig = None

    def _record(self, m, d):
        import numpy as np
        h = hashlib.blake2b(digest_size=16)
        h.update(m.nq.to_bytes(4, "little"))
        h.update(m.nv.to_bytes(4, "little"))
        for f in self.FIELDS:
            arr = getattr(d, f, None)
            if arr is not None:
                # np.asarray, not memoryview: d.time is a Python SCALAR and memoryview()
                # refuses it -- a TypeError here once silently recorded an empty stream.
                b = np.asarray(arr).tobytes()
                h.update(b)
                self.stream_h[f].update(b)
        self.digests.append(h.digest())
        if self.raw is not None:
            self.raw.append(tuple(getattr(d, f).copy() for f in ("qpos", "qvel", "actuator_force")))

    def stream_digests(self) -> dict:
        return {f: self.stream_h[f].hexdigest() for f in self.FIELDS}

    def __enter__(self):
        import mujoco
        self._orig = mujoco.mj_step
        rec = self

        def wrapped(m, d, nstep=1):
            for _ in range(nstep):
                rec._orig(m, d)
                rec._record(m, d)

        mujoco.mj_step = wrapped
        return self

    def __exit__(self, *exc):
        import mujoco
        mujoco.mj_step = self._orig
        return False


def _run_suite_with_recorder(raw=False):
    """One full pass over every registered item, recording every stepped state."""
    rec = StepRecorder()
    if raw:
        rec.raw = []
    with rec:
        for registry in (at.ACTIONS, pt.PRIMITIVES):
            for meta in registry.values():
                _verdict(meta)
    return rec


def _trajectory_comparison():
    """The S4 experiment: two recorded runs must be bit-identical, step for step."""
    a = _run_suite_with_recorder()
    b = _run_suite_with_recorder()
    if not a.digests or not b.digests:
        # THE COUNT IS ASSERTED: an empty stream is a broken INSTRUMENT, never a pass --
        # the "4/4 ports validated" lesson, applied to this recorder's own first version.
        return {"bit_identical": False,
                "detail": f"INSTRUMENT FAILURE: recorder captured {len(a.digests)}/"
                          f"{len(b.digests)} steps -- an empty stream cannot verify anything"}
    if len(a.digests) != len(b.digests):
        return {"bit_identical": False,
                "detail": f"step COUNT diverged: run A {len(a.digests)} vs run B {len(b.digests)} "
                          f"-- a control-flow nondeterminism, worse than a value drift"}
    first = next((i for i, (x, y) in enumerate(zip(a.digests, b.digests)) if x != y), None)
    if first is None:
        record = {"bit_identical": True, "steps": len(a.digests),
                  "detail": f"{len(a.digests)} stepped states compared exactly; max |delta| = 0 "
                            f"(bit-identity implies the pre-registered 1e-15 tolerance)"}
        _write_s4_record(a, b)
        return record
    # quantify: re-run raw to measure the actual divergence magnitude
    ra, rb = _run_suite_with_recorder(raw=True), _run_suite_with_recorder(raw=True)
    worst = 0.0
    for sa, sb in zip(ra.raw, rb.raw):
        for xa, xb in zip(sa, sb):
            if xa.shape == xb.shape and xa.size:
                import numpy as np
                worst = max(worst, float(np.max(np.abs(xa - xb))))
    return {"bit_identical": False, "first_divergent_step": first, "max_abs_delta": worst,
            "detail": f"FALSIFIER FIRED: step {first} of {len(a.digests)} diverged; "
                      f"max |delta| over raw re-run = {worst:.3e} (tolerance 1e-15)"}


def _write_s4_record(a, b):
    """The S4 MEASUREMENT LEDGER: docs/determinism_s4_record.json. The per-stream digests are the
    published pointers for theDeterminism's S5 why-terminal -- each discovered variable (contact
    forces, warm-start state, actuator activation, FP reduction order) terminates at the stream
    that measured it. Written ONLY on bit-identity; a failed run publishes no record."""
    da, db = a.stream_digests(), b.stream_digests()
    assert da == db, "record written only when the streams themselves are bit-identical"
    run_h = hashlib.blake2b(digest_size=16)
    for dig in a.digests:
        run_h.update(dig)
    rec = {"experiment": "theDeterminism S4 -- two full-suite recorded passes, compared exactly",
           "recorded_steps": len(a.digests),
           "bit_identical": True,
           "max_abs_delta": 0.0,
           "digest_algorithm": "blake2b-16",
           "run_digest": run_h.hexdigest()}
    rec.update({f"{f}_digest": h for f, h in da.items()})
    out = Path(__file__).resolve().parent.parent / "docs" / "determinism_s4_record.json"
    out.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf8")
    return out


def _collect(kind, registry, n):
    runs = []
    for _ in range(n):
        runs.append({name: _verdict(meta) for name, meta in registry.items()})
    # transpose to per-item verdict lists
    items = {}
    for name in registry:
        items[name] = [run[name] for run in runs]
    return items


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3

    actions = _collect("action", at.ACTIONS, n)
    primitives = _collect("primitive", pt.PRIMITIVES, n)

    report = {"runs": n, "actions": {}, "primitives": {}}
    unstable = []
    for kind, items in (("actions", actions), ("primitives", primitives)):
        for name, verdicts in items.items():
            stable = len(set(verdicts)) == 1
            report[kind][name] = {"verdicts": verdicts, "stable": stable}
            if not stable:
                unstable.append(f"{kind}:{name}")

    report["stable"] = not unstable
    report["unstable_items"] = unstable

    print(json.dumps(report, indent=2))
    if unstable:
        print(f"\nNON-DETERMINISTIC: {len(unstable)} item(s) flipped verdict across runs: {unstable}")
        return 1

    # S4: the verdicts being stable is necessary but not sufficient -- the TRAJECTORIES under
    # them must be bit-identical too (docs/THE_DETERMINISM_S4.md, pre-registered).
    traj = _trajectory_comparison()
    print(f"\nTRAJECTORY (S4): {traj['detail']}")
    total = len(actions) + len(primitives)
    if not traj["bit_identical"]:
        print("NON-DETERMINISTIC: the physics trajectories diverge under identical inputs.")
        return 1
    print(f"\nDETERMINISTIC: {total} items stable across {n} runs; "
          f"{traj['steps']} stepped states bit-identical across 2 recorded runs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
