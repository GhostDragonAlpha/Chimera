"""train_inbetween.py -- THE IN-BETWEEN training harness: physics AND structure across the range.

RULE 0, stated before the run, because this membrane is a theory:

    STATEMENT   the in-between must be TRAINED -- physics AND structure -- across the WHOLE joint
                angle range, not just at the validated extremes. A primitive that is physical at
                its nominal pose can still break between poses; every intermediate configuration
                must hold.

    PREDICTION  within the nominal joint envelope, every primitive behaves physically: no NaN/Inf,
                no penetration past the structural stop, energy bounded. The report LOCALIZES the
                first configuration at which physics or structure breaks.

    FALSIFIER   an in-range configuration produces a non-physical result with no recorded failure.
                (By recording every breakdown we refuse this failure mode; if a real in-range
                breakdown is found, the PREDICTION -- "every in-range config is physical" -- is
                what falls, and the report names exactly where.)

LAWS ENFORCED:
    BLACK BOX   the primitives (SWING, LAND, UPRIGHT) are called exactly as written. This harness
                never edits them; it only injects a swept joint angle into the model's keyframe
                and instruments MuJoCo's own step/forward to watch for breakdowns.
    DETERMINISM the body is loaded once per config with no random seed; MuJoCo's fixed-timestep
                integrator is deterministic, so a config that breaks will break identically again.
    HONESTY     real breakdowns are recorded at the step they occur -- never smoothed, never hidden.

METHOD. For each primitive we sweep its central leg joint (hip_flexion_r) across the model's OWN
published jnt_range. At each angle we (1) inject the angle into the keyframe the primitive reads,
(2) run the primitive as a black box while a wrapper on mujoco.mj_step / mujoco.mj_forward watches
every step for non-finite state, contact penetration past the structural stop, and unbounded
energy, (3) record the per-config verdict. The precise config that first fails is localized.

UPRIGHT is gated on availability (MEMBRANE: "add UPRIGHT when its branch lands"). It has landed, so
it is swept; if it is ever absent the harness skips it and says so rather than failing the build.

    python tools/train_inbetween.py     ->  Saved/train_inbetween/report.json
"""
from __future__ import annotations

import json
import math
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import mujoco                                                      # noqa: E402
from port_registry import MYOBODY                                   # noqa: E402

# ── monitor thresholds (declared before the run) ───────────────────────────────────────────────
PEN_THRESH = 0.05          # m of contact penetration = past the hardened geometric stop (structural break)
ENERGY_VEL_THRESH = 1.0e3  # |qvel| above this = an energy blow-up (physics break)
N_POINTS = 9               # samples across each joint's nominal range


class PhysicsBreakdown(Exception):
    """Raised the moment a step/forward produces a non-physical state. Carries the config + step."""

    def __init__(self, kind, step, value, extra=""):
        self.kind, self.step, self.value, self.extra = kind, step, value, extra
        super().__init__(f"{kind} @ step {step}: {value} {extra}")


# ── instrumentation state ──────────────────────────────────────────────────────────────────────
_MON = {"nstep": 0, "nforward": 0, "max_pen": 0.0, "max_vel": 0.0}
_ORIG_STEP = mujoco.mj_step
_ORIG_FORWARD = mujoco.mj_forward


def _check(d, label):
    if not (np.all(np.isfinite(d.qpos)) and np.all(np.isfinite(d.qvel))):
        raise PhysicsBreakdown("nan", _MON["nstep"], float("nan"),
                               f"non-finite state during {label}")
    if label == "step":
        mv = float(np.max(np.abs(d.qvel))) if d.qvel.size else 0.0
        if mv > _MON["max_vel"]:
            _MON["max_vel"] = mv
        if mv > ENERGY_VEL_THRESH:
            raise PhysicsBreakdown("energy", _MON["nstep"], mv,
                                   f"|qvel| > {ENERGY_VEL_THRESH}")
        if d.ncon > 0:
            pen = 0.0
            for c in range(d.ncon):
                dist = float(d.contact[c].dist)
                if dist < pen:
                    pen = dist
            if pen < _MON["max_pen"]:
                _MON["max_pen"] = pen
            if pen < -PEN_THRESH:
                raise PhysicsBreakdown("penetration", _MON["nstep"], pen,
                                       f"contact penetration {pen:.4f} m > {PEN_THRESH} m")


def _mon_step(m, d, *a, **k):
    _ORIG_STEP(m, d, *a, **k)
    _MON["nstep"] += 1
    _check(d, "step")


def _mon_forward(m, d, *a, **k):
    _ORIG_FORWARD(m, d, *a, **k)
    _MON["nforward"] += 1
    _check(d, "forward")        # forward only needs the finite check (settling may briefly touch)


# ── joint-angle injection (black box: we only touch the keyframe the primitive reads) ───────────
_CURRENT = {}                    # {"joint": name, "angle": rad} set per config; empty = no override


def _patched_load(xml_path, mj=None, **kw):
    if mj is None:
        import mujoco as _m
        mj = _m
    model, g = _ORIG_LOAD(xml_path, mj, **kw)
    jn = _CURRENT.get("joint")
    if jn:
        try:
            jid = mj.mj_name2id(model, mj.mjtObj.mjOBJ_JOINT, jn)
        except Exception:
            jid = -1
        if jid >= 0:
            adr = int(model.jnt_qposadr[jid])
            model.key_qpos[0, adr] = float(_CURRENT["angle"])
            model.qpos0[adr] = float(_CURRENT["angle"])
    return model, g


_ORIG_LOAD = None                # set after we import world


def _range_of(m, joint):
    jid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, joint)
    if jid >= 0 and m.jnt_limited[jid]:
        return float(m.jnt_range[jid][0]), float(m.jnt_range[jid][1])
    return -1.5, 1.5             # fallback for an un-limited joint


def _sweep_angles(rmin, rmax, off_deg):
    hi = min(rmax, rmax - math.radians(off_deg))   # keep primitive's internal start offset in range
    lo = rmin
    if hi <= lo:
        hi = rmax
    return list(np.linspace(lo, hi, N_POINTS))


def run():
    global _ORIG_LOAD
    # patch load_body BEFORE importing the primitive modules, so their `from world import
    # load_body` binds to the patched version and every primitive run can be angle-injected.
    import world                                       # noqa: E402
    _ORIG_LOAD = world.load_body
    world.load_body = _patched_load

    import action_tests                                # noqa: E402  (a_swing, a_land)
    import action_upright                              # noqa: E402  (a_upright, gated)

    # ── which primitives are available (gate on availability) ──────────────────────────────────
    prims = [
        ("swing", action_tests.a_swing, "hip_flexion_r", 12.0),
        ("land", action_tests.a_land, "hip_flexion_r", 0.0),
    ]
    if hasattr(action_upright, "a_upright"):
        prims.append(("upright", action_upright.a_upright, "hip_flexion_r", 0.0))
    upright_gated = ("upright" not in [p[0] for p in prims])

    # discover each joint's nominal range from the model itself
    mbody, g = world.load_body(MYOBODY, mujoco)    # _CURRENT empty -> no override
    sweep_info = {}
    for pname, _, joint, off in prims:
        rmin, rmax = _range_of(mbody, joint)
        sweep_info[pname] = dict(joint=joint, rmin=rmin, rmax=rmax,
                                 off_deg=off, angles=_sweep_angles(rmin, rmax, off))

    configs = []
    first_breakdown = None
    per_prim_first = {}

    for pname, pfn, joint, off in prims:
        info = sweep_info[pname]
        for ang in info["angles"]:
            _CURRENT["joint"] = joint
            _CURRENT["angle"] = float(ang)
            _MON["nstep"] = 0
            _MON["nforward"] = 0
            _MON["max_pen"] = 0.0
            _MON["max_vel"] = 0.0
            mujoco.mj_step = _mon_step
            mujoco.mj_forward = _mon_forward
            physics_ok = True
            breakdown = None
            primitive_pass = None
            got = detail = None
            try:
                r = pfn(None)
                if isinstance(r, dict):
                    primitive_pass = bool(r.get("pass_"))
                    got = r.get("got")
                    detail = r.get("detail")
                    # backstop: a NaN/Inf that slipped past the step monitor (e.g. in a static
                    # derivation) still shows up in the returned numbers.
                    txt = ""
                    try:
                        txt = json.dumps(r, default=str)
                    except Exception:
                        txt = str(r)
                    if "nan" in txt.lower() or "infinity" in txt.lower():
                        physics_ok = False
                        breakdown = dict(kind="nonfinite_result", step=-1, value="NaN/Inf in result",
                                         extra=f"{joint}={math.degrees(float(ang)):.2f} deg")
            except PhysicsBreakdown as e:
                physics_ok = False
                breakdown = dict(kind=e.kind, step=e.step, value=float(e.value)
                                if isinstance(e.value, (int, float)) else str(e.value),
                                extra=e.extra)
            except Exception as e:                # any other crash is itself a non-physical breakdown
                physics_ok = False
                breakdown = dict(kind="exception", step=_MON["nstep"], value=str(e)[:200],
                                extra=traceback.format_exc().splitlines()[-1])
            finally:
                mujoco.mj_step = _ORIG_STEP
                mujoco.mj_forward = _ORIG_FORWARD

            rec = dict(
                primitive=pname, joint=joint,
                angle_deg=round(math.degrees(float(ang)), 4),
                angle_rad=round(float(ang), 6),
                angle_fraction=round((float(ang) - info["rmin"]) / max(info["rmax"] - info["rmin"], 1e-9), 4),
                physics_ok=physics_ok,
                breakdown=breakdown,
                primitive_pass=primitive_pass,
                primitive_got=got,
                primitive_detail=(str(detail)[:2000] if detail is not None else None),
                max_penetration_m=round(_MON["max_pen"], 6),
                max_abs_qvel=round(_MON["max_vel"], 4),
            )
            configs.append(rec)

            if not physics_ok and pname not in per_prim_first:
                per_prim_first[pname] = rec
            if not physics_ok and first_breakdown is None:
                first_breakdown = rec

    # ── verdict ────────────────────────────────────────────────────────────────────────────────
    prediction_holds = all(c["physics_ok"] for c in configs)
    falsifier_fired = not prediction_holds     # a real in-range breakdown was found & recorded
    n_total = len(configs)
    n_bad = sum(1 for c in configs if not c["physics_ok"])

    if falsifier_fired:
        verdict = (f"PREDICTION FALSIFIED: {n_bad}/{n_total} in-range configs were non-physical. "
                   f"First breakdown: {first_breakdown['primitive']} {first_breakdown['joint']} "
                   f"at {first_breakdown['angle_deg']} deg ({first_breakdown['breakdown']['kind']}). "
                   f"The in-between training LOCALIZES the break; this is the honest result, not a "
                   f"smoothed pass.")
    else:
        verdict = (f"PREDICTION HOLDS: all {n_total} in-range configurations across "
                   f"{', '.join(sweep_info)} behaved physically (no NaN, no penetration past the "
                   f"stop, energy bounded). The in-between is trained.")

    report = dict(
        membrane=dict(
            name="train_inbetween",
            statement="the in-between must be TRAINED -- physics AND structure -- across the whole "
                      "joint-angle range; every intermediate configuration must hold.",
            prediction="within the nominal joint envelope, every primitive behaves physically "
                       "(no NaN/Inf, no penetration past the structural stop, energy bounded); the "
                       "report localizes the first breakdown.",
            falsifier="an in-range config produces a non-physical result with no recorded failure.",
            laws=["black-box primitives (unmodified)", "determinism (no RNG, fixed integrator)",
                  "honesty (real breakdowns recorded, not smoothed)"],
        ),
        generated=datetime.now(timezone.utc).isoformat(),
        world=dict(gravity=round(float(g), 6), body="external/myo_sim/body/myobody.xml"),
        primitives_swept=[p[0] for p in prims],
        upright_gated=upright_gated,
        sweep=dict(
            joint_per_primitive={p[0]: p[2] for p in prims},
            n_points=N_POINTS,
            internal_offset_deg={p[0]: p[3] for p in prims},
            range_source="model jnt_range (published)",
            pen_threshold_m=PEN_THRESH,
            energy_vel_threshold=ENERGY_VEL_THRESH,
        ),
        n_configs=n_total,
        n_physical=n_total - n_bad,
        n_nonphysical=n_bad,
        first_breakdown=first_breakdown,
        per_primitive_first_failure=per_prim_first or None,
        configs=configs,
        verdict=dict(prediction_holds=prediction_holds, falsifier_fired=falsifier_fired,
                     summary=verdict),
    )

    out = ROOT / "Saved" / "train_inbetween" / "report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf8")

    # stdout summary
    print("=" * 90)
    print("  THE IN-BETWEEN TRAINING HARNESS -- physics AND structure across the joint range")
    print("=" * 90)
    print(f"  primitives swept : {', '.join(report['primitives_swept'])}"
          + ("   [UPRIGHT gated in]" if not upright_gated else "   [UPRIGHT MISSING -- gated out]"))
    print(f"  configs          : {n_total}  ({n_bad} non-physical)")
    for pname in sweep_info:
        pf = per_prim_first.get(pname)
        print(f"    {pname:8} {sweep_info[pname]['joint']:14} "
              f"range [{math.degrees(sweep_info[pname]['rmin']):.1f},"
              f"{math.degrees(sweep_info[pname]['rmax']):.1f}] deg -> "
              + (f"FIRST FAIL @ {pf['angle_deg']} deg ({pf['breakdown']['kind']})"
                 if pf else "all physical"))
    print("-" * 90)
    print(f"  VERDICT: {'PREDICTION HOLDS' if prediction_holds else 'PREDICTION FALSIFIED'}")
    print(f"  {verdict}")
    print(f"  report : {out}")
    return report


if __name__ == "__main__":
    run()
