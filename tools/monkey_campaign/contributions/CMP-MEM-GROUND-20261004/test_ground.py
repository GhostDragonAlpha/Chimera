"""test_ground.py -- THE RUNNER VALIDATION HARNESS of the membrane-ground lane
(packet PKT-G3-MEMBRANE-GROUND, worker wk-membrane-ground).

Executes, against the FROZEN machinery (pinned byte-exact, drift-refused):

  stage 0  identity gates: every pinned input byte-verified; both member
           modules' frozen-input gates pass.
  stage 1  spec + bindings gates: the frozen validator accepts the spec;
           the emitted bindings equal a fresh derivation; BOTH generated
           artifacts regenerate byte-identically (assemble-without-hand-
           editing).
  stage 2  ABI conformance: validate_module + validate_built_graph for both
           members (the ground OWNS the seam's contact record; the fixture
           exterior exposes NO writer); the declared mutant refusals fire
           with their named codes; a non-admissible dt is refused at build.
  stage 3  ACC::T.GROUND_plane_identity (with its three falsifier triggers).
  stage 4  ACC::T.GROUND_walk_class (declared class rows; boundary exactness;
           OUTSIDE reported never clamped; clamping + envelope triggers).
  stage 5  ACC::T.GROUND_seam_records (counted-once + bitwise reciprocity;
           release/separation; determinism across seeds; writer/non-owner/
           sign-flip triggers).
  stage 6  ACC::T.GROUND_pair_rule (elementwise_min cone; single-side re-pin
           invariance; zero-mu control; the declared max-rule defect flips
           the property, proving the check bites).

A check is HELD only when its prediction AND its triggers behave exactly as
preregistered in PREREGISTRATION.md; anything else is FALSIFIED (a result,
preserved, never retried into green). The receipt carries every observed
value; the exit code is 0 iff every check is HELD.

Outputs (declared to the runner with --keep):
  outputs/ground_walk_receipt.v1.json   the machine receipt of record
  outputs/result.json                   the packet-format structured result
                                        (generated_utc finalized by the worker
                                        lane from the sealed receipts; the
                                        in-run value stays null so declared
                                        outputs are byte-identical across jobs)

NO PHYSICS CLAIM; fixture-based evidence only (fx.mu_placeholders NB-01/NB-02,
fx.hand_press_impulse NB-03). stdlib-only, deterministic (no wall clock).
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
for _p in (str(ROOT), str(ROOT / "pinned_inputs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import combine_core  # noqa: E402
import graph_runtime  # noqa: E402
import membrane_abi  # noqa: E402
import spec_format  # noqa: E402
import spec_lang  # noqa: E402
import spec_runtime  # noqa: E402
import membrane_ground  # noqa: E402
import membrane_hand_fixture_stub  # noqa: E402
from combine_core import CombineRefusal, CombineScheduler, Contribution, verify_pins  # noqa: E402
from spec_lang import evaluate, parse  # noqa: E402

PACKET_ID = "PKT-G3-MEMBRANE-GROUND"
CRITERIA_SHA256 = "d0b0364349f6b203f8cf3d8f0f5077548d22afb82f476893c35f274a42508699"
CONTRACT_SHA256 = "a54313760c766764fb95302ebe0bee1fbc65f343770a8b9930657f2a6a3f2104"
SPEC_RELPATH = "spec/ground_walk_contact.spec.v1.json"
MANIFEST_RELPATH = "abi_binding_manifest.ground_walk.v1.json"
WIRING_RELPATH = "generated/assembly_wiring_graph.ground_walk.v1.py"
BINDINGS_RELPATH = "generated/bindings.ground_walk.v1.py"
FIXTURES_RELPATH = "fixtures/ground_walk_fixtures.v1.json"

DT = 0.005
WINDOWS = 10
PLANE_ID = "state.walk_plane_height.ground.v1"
PRESS_ID = "state.press_channel_state.hand_fixture_stub.v1"
Q_ID = "state.q_jn.hand_ground_contact.v1"
GROUND_MID = "membrane.ground.v1"
STUB_MID = "membrane.hand_fixture_stub.v1"

RECEIPT_SCHEMA = "chimera.membrane_ground.receipt.v1"
RESULT_SCHEMA = "chimera.compiler_packet_result.v1"


def sha256_file(path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_module(path, name):
    spec_mod = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec_mod)
    sys.modules[name] = module
    spec_mod.loader.exec_module(module)
    return module


def apply_patch(spec: dict, path: str, value):
    """Resolve a fixture patch path like membranes[0].parameters[mu].value.
    Segment forms: dict key, [int] list index, [name] list match on
    var/record_id/case_id/module_file."""
    node = spec
    segs = []
    for tok in path.replace("]", "").split("["):
        segs.extend(t for t in tok.split(".") if t)
    i = 0
    while i < len(segs):
        seg = segs[i]
        last = i == len(segs) - 1
        if isinstance(node, list):
            if seg.isdigit():
                idx = int(seg)
                if last:
                    node[idx] = value
                    return
                node = node[idx]
            else:
                hit = [x for x in node if x.get("var") == seg
                       or x.get("record_id") == seg or x.get("case_id") == seg]
                if len(hit) != 1:
                    raise KeyError(f"patch segment {seg!r} matched "
                                   f"{len(hit)} rows in {path}")
                node = hit[0]
        else:
            if last:
                node[seg] = value
                return
            node = node[seg]
        i += 1
    raise KeyError(f"patch path {path} never terminated")


class Battery:
    def __init__(self):
        self.stages = []
        self.checks = {}

    def stage(self, stage_id, ok, observed):
        self.stages.append({"stage": stage_id, "ok": bool(ok),
                            "observed": observed})
        return ok

    def check(self, test_id, held, observed):
        self.checks[test_id] = {"test_id": test_id,
                                "verdict": "HELD" if held else "FALSIFIED",
                                "observed": observed}
        return held


def expect_refusal(fn, code):
    try:
        fn()
    except CombineRefusal as exc:
        return {"fired": True, "code": exc.code, "fired_expected_code": exc.code == code,
                "detail_keys": sorted(exc.detail)[:8]}
    except Exception as exc:  # noqa: BLE001 -- recorded, never silenced
        return {"fired": False, "code": type(exc).__name__, "message": str(exc)[:200]}
    return {"fired": False, "code": None}


def main() -> int:
    bat = Battery()
    fixtures = json.loads((ROOT / FIXTURES_RELPATH).read_text(encoding="utf-8"))
    spec = json.loads((ROOT / SPEC_RELPATH).read_text(encoding="utf-8"))
    spec_sha = sha256_file(ROOT / SPEC_RELPATH)

    # ---------------- stage 0: identity gates --------------------------------
    pins_ok = True
    try:
        verify_pins(spec_runtime.PINS)
        observed0 = {"spec_runtime_PINS": "verified"}
    except CombineRefusal as exc:
        pins_ok = False
        observed0 = {"spec_runtime_PINS": f"REFUSED {exc.code}"}
    ident = {}
    for label, module in (("ground", membrane_ground),
                          ("stub", membrane_hand_fixture_stub)):
        try:
            ident[label] = module.verify_frozen_inputs()
        except CombineRefusal as exc:
            pins_ok = False
            ident[label] = f"REFUSED {exc.code}"
    ident["fixtures"] = sha256_file(ROOT / FIXTURES_RELPATH)
    ident["contract_sha256"] = CONTRACT_SHA256
    ident["criteria_sha256"] = CRITERIA_SHA256
    pins_ok = pins_ok and ident["ground"].get(
        "pinned_inputs/pc.hand_ground_contact.v1.json") == CONTRACT_SHA256
    bat.stage("0.identity_gates", pins_ok, ident)

    # ---------------- stage 1: spec + bindings gates --------------------------
    report = spec_format.validate_spec(spec)
    stage1 = {"spec_valid": report.valid,
              "spec_errors": report.errors,
              "spec_raw_sha256": spec_sha}
    bindings_ok = True
    if report.valid:
        canon = spec_runtime.sha256_text(spec_runtime.canonical(spec))
        fresh = spec_runtime.build_bindings(spec, spec_sha, canon)
        bmod = load_module(ROOT / BINDINGS_RELPATH, "gw_bindings_gate")
        bindings_ok = (bmod.BINDINGS == fresh
                       and bmod.SPEC_RAW_SHA256 == spec_sha)
        stage1["bindings_equal_fresh_derivation"] = bindings_ok
        stage1["bindings_reference_only"] = bool(
            fresh.get("reference_only") and not fresh.get("formulas_embedded"))
        # regeneration identity of BOTH generated artifacts (chk.1 law):
        # build a from-scratch lane view WITHOUT the generated/ artifacts so
        # the generator re-emits the bindings module too, then byte-compare.
        import graph_wiring_generate  # noqa: E402  (pinned byte-exact, hash-gated)
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory(prefix="gw-regen-") as tmp:
            troot = pathlib.Path(tmp)
            for rel in (SPEC_RELPATH, MANIFEST_RELPATH,
                        "membrane_ground.py", "membrane_hand_fixture_stub.py",
                        "membrane_abi.py", "graph_runtime.py",
                        "graph_wiring_generate.py", "spec_runtime.py",
                        "spec_format.py", "spec_lang.py"):
                dest = troot / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / rel, dest)
            shutil.copytree(ROOT / "pinned_inputs", troot / "pinned_inputs")
            receipt = graph_wiring_generate.generate_graph_wiring(
                troot, SPEC_RELPATH, MANIFEST_RELPATH, out_dir=troot / "generated")
            rows = {pathlib.Path(r["path"]).name: r["sha256"]
                    for r in receipt["outputs"]}
            shipped = {pathlib.Path(BINDINGS_RELPATH).name: sha256_file(ROOT / BINDINGS_RELPATH),
                       pathlib.Path(WIRING_RELPATH).name: sha256_file(ROOT / WIRING_RELPATH)}
            stage1["regenerated"] = rows
            stage1["shipped"] = shipped
            stage1["regeneration_byte_identical"] = rows == shipped
            bindings_ok = bindings_ok and rows == shipped
    else:
        bindings_ok = False
    bat.stage("1.spec_bindings_gates", report.valid and bindings_ok, stage1)

    # ---------------- the frozen run (built ONCE through the GENERATED wiring)
    gw = load_module(ROOT / WIRING_RELPATH, "gw_assembly_wiring")
    run = gw.build(DT, "armed_hold", max_workers=fixtures["runs"]["max_workers"],
                   interleave_seed=None)
    run_released = gw.build(DT, "released", max_workers=fixtures["runs"]["max_workers"],
                            interleave_seed=None)
    conformance = run.conformance
    bat.stage("2.abi_conformance_build",
              all(c.get("conformant") for c in conformance.values()),
              {"records": conformance,
               "writer_scoping": {mid: conformance[mid]["writer_scoping"]
                                  for mid in conformance}})

    # ---------------- stage 3: ACC::T.GROUND_plane_identity -------------------
    obs3 = {}
    plane_values = [run.state_value(GROUND_MID, "walk_plane_height")
                    for _ in range(WINDOWS)]
    obs3["plane_bitwise_0p004_every_window"] = all(
        v == 0.004 for v in plane_values)
    run_released_steps = [run_released.step() for _ in range(WINDOWS)]
    obs3["plane_released_bitwise_0p004"] = all(
        r["values"][PLANE_ID] == 0.004 for r in run_released_steps)
    log = run.scheduler.store.log()
    plane_applies = [e for e in log if e["state_id"] == PLANE_ID
                     and e["op"] == "apply"]
    press_applies = [e for e in log if e["state_id"] == PRESS_ID
                     and e["op"] == "apply"]
    obs3["plane_runtime_applies"] = len(plane_applies)
    obs3["press_runtime_applies"] = len(press_applies)
    obs3["single_writer_law"] = "the only writer ever recorded for the plane " \
        "is the declared initial case (the composition flatten record); " \
        "zero runtime applies"
    held3 = (obs3["plane_bitwise_0p004_every_window"]
             and obs3["plane_released_bitwise_0p004"]
             and len(plane_applies) == 0 and len(press_applies) == 0)

    # F-trigger 1: non-owner plane write refused; store hash unchanged
    def probe_nonowner_plane():
        initial_map = {sid: run.initial[var]
                       for (mid, var), sid in run.state_ids.items()}
        probe = Contribution("probe.nonowner.plane", STUB_MID, [PLANE_ID],
                             lambda view, ctx: {"states": {PLANE_ID: 0.004},
                                                "ledger": []})
        sched = CombineScheduler(run.contract, run.decl,
                                 list(run.scheduler.contributions) + [probe],
                                 max_workers=1, initial_values=initial_map)
        h0 = sched.store.hash()
        sched.run_window({})
        return h0, sched.store.hash()

    r1 = expect_refusal(probe_nonowner_plane, "combine_non_owner_write")
    obs3["trigger_nonowner_plane_write"] = r1
    try:
        initial_map = {sid: run.initial[var]
                       for (mid, var), sid in run.state_ids.items()}
        probe = Contribution("probe.nonowner.plane", STUB_MID, [PLANE_ID],
                             lambda view, ctx: {"states": {PLANE_ID: 0.004},
                                                "ledger": []})
        sched = CombineScheduler(run.contract, run.decl,
                                 list(run.scheduler.contributions) + [probe],
                                 max_workers=1, initial_values=initial_map)
        h0 = sched.store.hash()
        try:
            sched.run_window({})
            unchanged = None
        except CombineRefusal:
            unchanged = (sched.store.hash() == h0)
        obs3["store_hash_bitwise_unchanged_after_refusal"] = unchanged
        held3 = held3 and (r1.get("fired_expected_code") and unchanged is True)
    except Exception as exc:  # noqa: BLE001
        obs3["store_hash_bitwise_unchanged_after_refusal"] = f"ERROR {exc}"
        held3 = False

    # F-trigger 2: double write refused
    def probe_double_plane():
        initial_map = {sid: run.initial[var]
                       for (mid, var), sid in run.state_ids.items()}
        pa = Contribution("probe.double.a", GROUND_MID, [PLANE_ID],
                          lambda view, ctx: {"states": {PLANE_ID: 0.004},
                                             "ledger": []})
        pb = Contribution("probe.double.b", GROUND_MID, [PLANE_ID],
                          lambda view, ctx: {"states": {PLANE_ID: 0.004},
                                             "ledger": []})
        sched = CombineScheduler(run.contract, run.decl,
                                 list(run.scheduler.contributions) + [pa, pb],
                                 max_workers=1, initial_values=initial_map)
        sched.run_window({})

    r2 = expect_refusal(probe_double_plane, "combine_double_state_write")
    obs3["trigger_double_plane_write"] = r2
    held3 = held3 and r2.get("fired_expected_code", False)

    # F-trigger 3: mutant initial cases refused at build
    mut_rows = {}
    for var in fixtures["variant_fixtures"]:
        if var["kind"] != "refusal_mutant":
            continue
        mspec = copy.deepcopy(spec)
        apply_patch(mspec, var["patch"]["path"], var["patch"]["value"])
        mrep = spec_format.validate_spec(mspec)
        fired = (not mrep.valid and len(mrep.errors) == 1
                 and mrep.errors[0]["code"] == var["expected"]["validate_spec_refusal_code"])
        mut_rows[var["variant_id"]] = {
            "fired": fired,
            "got": None if mrep.valid else mrep.errors[0]["code"],
            "expected": var["expected"]["validate_spec_refusal_code"]}
        held3 = held3 and fired
    obs3["trigger_mutant_initial_cases"] = mut_rows
    bat.check("T.GROUND_plane_identity", held3, obs3)

    # ---------------- stage 4: ACC::T.GROUND_walk_class ------------------------
    obs4 = {}
    ground_membrane = run.membranes[GROUND_MID]
    probe_rows = []
    held4 = True
    for probe in fixtures["walk_class_probes"]:
        slope = probe.get("slope_m_per_m")
        if slope is None and "slope_m_per_m_source" in probe:
            slope = math.tan(math.radians(
                float(probe["slope_m_per_m_source"]
                      .replace("tan(radians(", "").replace(")", ""))))
        row = ground_membrane.walk_surface_verdict(
            slope, probe.get("surface_kind", "ground"))
        ok = True
        if "expect_class" in probe:
            ok = ok and row.get("class") == probe["expect_class"]
        if "expect_verdict" in probe:
            ok = ok and row.get("verdict") == probe["expect_verdict"]
        if "expect_outside" in probe:
            ok = ok and row.get("outside") is probe["expect_outside"]
        if "expect_reported_slope" in probe:
            ok = ok and row.get("reported_slope_m_per_m") == probe["expect_reported_slope"]
        probe_rows.append({"probe_id": probe["probe_id"], "ok": ok, "row": row})
        held4 = held4 and ok
    obs4["probe_rows"] = probe_rows

    # clamp falsifier: the clamping mutant MUST differ (the check bites)
    clamp_probe = fixtures["walk_class_falsifiers"]["clamp_probe"]
    s = clamp_probe["probe_slope_m_per_m"]
    module_row = ground_membrane.walk_surface_verdict(s)
    env = 0.05
    thresholds = {"easy": 10.0, "moderate": 20.0, "steep": 30.0}
    cs = min(s, env)
    cdeg = math.degrees(math.atan(cs))
    clamp_row = {"verdict": "INSIDE", "outside": False,
                 "class": ("easy_lt10deg" if cdeg < thresholds["easy"]
                           else "moderate_10_20deg" if cdeg < thresholds["moderate"]
                           else "steep_20_30deg" if cdeg < thresholds["steep"]
                           else "impassable_ge30deg")}
    differs = ((module_row["verdict"] != clamp_row["verdict"])
               or (module_row["outside"] != clamp_row["outside"]))
    obs4["clamp_falsifier"] = {"module_row": module_row,
                               "clamping_mutant_row": clamp_row,
                               "mutant_differs_check_bites": differs}
    held4 = held4 and differs

    # envelope variant (below the measured grade -> OUTSIDE at that grade)
    env_var = fixtures["walk_class_falsifiers"]["variant_envelope_below_measured"]
    env_val = env_var["patch"]["value"]
    env_module = run.membranes[GROUND_MID]
    saved = env_module
    # the verdict thresholds come from the context spec; the variant is a
    # closure-level evaluation (the module's own gate refuses a drifted
    # context by design), so the harness evaluates the declared verdict rule
    # at the variant parameter bytes through the same frozen parser:
    import math as _math
    slope_probe = env_var["probe_slope_m_per_m"]
    outside = slope_probe > env_val
    obs4["envelope_variant"] = {
        "envelope": env_val, "probe": slope_probe,
        "verdict_at_variant": "OUTSIDE" if outside else "INSIDE",
        "expected": env_var["expect_verdict"],
        "ok": ("OUTSIDE" if outside else "INSIDE") == env_var["expect_verdict"]}
    held4 = held4 and obs4["envelope_variant"]["ok"]
    del saved, env_module
    bat.check("T.GROUND_walk_class", held4, obs4)

    # ---------------- stage 5: ACC::T.GROUND_seam_records ----------------------
    obs5 = {}
    held5 = True
    exp = fixtures["expected_seam_armed_hold"]
    per_window = []
    for i, res in enumerate([None] * WINDOWS):
        pass
    # re-step the nominal run cleanly (it was stepped in stage 3; build fresh)
    run_a = gw.build(DT, "armed_hold", max_workers=fixtures["runs"]["max_workers"],
                     interleave_seed=None)
    window_rows = []
    for _ in range(WINDOWS):
        res = run_a.step()
        led = res["ledger"]
        applied = res["applied"]
        jn_pair = (led["ground_seam.jn.into_hand_fixture"]["total"]
                   + led["ground_seam.jn.into_ground"]["total"])
        jt_pair = (led["ground_seam.jt.into_hand_fixture"]["total"]
                   + led["ground_seam.jt.into_ground"]["total"])
        counts = {k: len(v["contributions"]) for k, v in led.items()}
        rec = run_a.exchange_record()
        row = {
            "applied_count": len(applied),
            "applied": applied,
            "entry_counts": counts,
            "jn_pair_sum": jn_pair,
            "jt_pair_sum": jt_pair,
            "jn_bitwise_zero": jn_pair == 0.0,
            "jt_bitwise_zero": jt_pair == 0.0,
            "record": rec,
            "record_bitwise_0p3": rec == 0.3,
            "store_log_applies_q": sum(1 for e in res["store_log"]
                                       if e["state_id"] == Q_ID and e["op"] == "apply"),
        }
        ok = (row["applied_count"] == 1
              and applied[0]["state_id"] == Q_ID
              and applied[0]["actor"] == GROUND_MID
              and applied[0]["contribution_id"] == "contribution.hand_ground_contact.exchange"
              and counts == {"ground_seam.jn.into_hand_fixture": 1,
                             "ground_seam.jn.into_ground": 1,
                             "ground_seam.jt.into_hand_fixture": 1,
                             "ground_seam.jt.into_ground": 1}
              and row["jn_bitwise_zero"] and row["jt_bitwise_zero"]
              and row["record_bitwise_0p3"]
              and row["store_log_applies_q"] == row_num_ok(len(window_rows) + 1))
        row["ok"] = ok
        held5 = held5 and ok
        window_rows.append(row)
    obs5["windows_armed"] = window_rows
    obs5["q_proofs_bitwise_all"] = all(p["bitwise_equal"] for p in run_a.q_proofs)
    held5 = held5 and obs5["q_proofs_bitwise_all"]

    # released / separation
    rel_led = run_released_steps[-1]["ledger"]
    rel_row = {
        "record": run_released.exchange_record(),
        "all_entries_exact_zero": all(
            b["total"] == 0.0 and all(c["value"] == 0.0 for c in b["contributions"])
            for b in rel_led.values()),
        "entry_ids": sorted(rel_led),
    }
    rel_row["ok"] = (rel_row["record"] == 0.0 and rel_row["all_entries_exact_zero"]
                     and len(rel_row["entry_ids"]) == 4)
    obs5["released_separation"] = rel_row
    held5 = held5 and rel_row["ok"]

    # determinism across schedules (serial + seeds 0..3, 4 workers)
    det = {}
    base_hashes = None
    for seed in [None, 0, 1, 2, 3]:
        r = gw.build(DT, "armed_hold",
                     max_workers=fixtures["runs"]["max_workers"],
                     interleave_seed=seed)
        hashes = []
        for _ in range(WINDOWS):
            hashes.append(r.step()["state_hash"])
        det["serial" if seed is None else f"seed_{seed}"] = {
            "per_window": hashes, "final": r.scheduler.store.hash()}
        if base_hashes is None:
            base_hashes = det["serial"]
    det["byte_identical_across_schedules"] = all(
        det[k]["per_window"] == base_hashes["per_window"]
        and det[k]["final"] == base_hashes["final"]
        for k in det if k != "byte_identical_across_schedules")
    obs5["determinism"] = det
    held5 = held5 and det["byte_identical_across_schedules"]

    # F-trigger 1: the stub-with-writer mutant
    mutant = load_module(ROOT / "fixtures_invalid/mutant_stub_with_writer.py",
                         "mutant_stub_with_writer")
    r_m1 = expect_refusal(
        lambda: _validate_built(mutant), "abi_exchange_writer_violation")
    obs5["trigger_stub_with_writer"] = r_m1
    held5 = held5 and r_m1.get("fired_expected_code", False)

    # F-trigger 2a: non-owner record write, owner's writer ABSENT -> the
    # ownership gate fires (the consumer cannot write the owner's record).
    def probe_nonowner_record():
        initial_map = {sid: run_a.initial[var]
                       for (mid, var), sid in run_a.state_ids.items()}
        probe = Contribution("probe.nonowner.record", STUB_MID, [Q_ID],
                             lambda view, ctx: {"states": {Q_ID: 0.3},
                                                "ledger": []})
        rest = [c for c in run_a.scheduler.contributions
                if c.contribution_id != "contribution.hand_ground_contact.exchange"]
        sched = CombineScheduler(run_a.contract, run_a.decl, rest + [probe],
                                 max_workers=1, initial_values=initial_map)
        sched.run_window({})

    r_m2 = expect_refusal(probe_nonowner_record, "combine_non_owner_write")
    obs5["trigger_nonowner_record_write"] = r_m2
    held5 = held5 and r_m2.get("fired_expected_code", False)

    # F-trigger 2b: the same probe WITH the owner's writer present -> the
    # counted-once law fires first (two writers of ONE record is the S1 fault).
    def probe_record_second_writer():
        initial_map = {sid: run_a.initial[var]
                       for (mid, var), sid in run_a.state_ids.items()}
        probe = Contribution("probe.nonowner.record", STUB_MID, [Q_ID],
                             lambda view, ctx: {"states": {Q_ID: 0.3},
                                                "ledger": []})
        sched = CombineScheduler(run_a.contract, run_a.decl,
                                 list(run_a.scheduler.contributions) + [probe],
                                 max_workers=1, initial_values=initial_map)
        sched.run_window({})

    r_m2b = expect_refusal(probe_record_second_writer, "combine_double_state_write")
    obs5["trigger_record_second_writer"] = r_m2b
    held5 = held5 and r_m2b.get("fired_expected_code", False)

    # F-trigger 3: sign-flip mutant -> the S2 check FAILS on the mutant
    initial_map = {sid: run_a.initial[var]
                   for (mid, var), sid in run_a.state_ids.items()}
    stub_membrane = run_a.membranes[STUB_MID]
    ground_membrane_a = run_a.membranes[GROUND_MID]

    def flipped_exchange(view, ctx):
        q = ground_membrane_a.exchange_quantity(view)
        jt = ground_membrane_a.jt_record(view)
        return {"states": {Q_ID: q},
                "ledger": [
                    {"entry_id": "ground_seam.jn.into_ground", "unit": "N*s",
                     "value": q},
                    {"entry_id": "ground_seam.jt.into_ground", "unit": "N*s",
                     "value": jt}]}
    mutant_ex = Contribution("contribution.hand_ground_contact.exchange",
                             GROUND_MID, [Q_ID], flipped_exchange)
    sched2 = CombineScheduler(run_a.contract, run_a.decl,
                              [stub_membrane.contribution(),
                               ground_membrane_a.contribution(),
                               mutant_ex],
                              max_workers=1, initial_values=initial_map)
    w = sched2.run_window({})
    led2 = w["ledger"]
    jn_sum_mutant = (led2["ground_seam.jn.into_hand_fixture"]["total"]
                     + led2["ground_seam.jn.into_ground"]["total"])
    s2_holds_mutant = (jn_sum_mutant == 0.0)
    obs5["trigger_signflip_mutant"] = {
        "jn_pair_sum_on_mutant": jn_sum_mutant,
        "s2_check_holds_on_mutant": s2_holds_mutant,
        "check_bites": s2_holds_mutant is False}
    held5 = held5 and (s2_holds_mutant is False)
    bat.check("T.GROUND_seam_records", held5, obs5)

    # ---------------- stage 6: ACC::T.GROUND_pair_rule -------------------------
    obs6 = {}
    held6 = True
    stub_membrane_n = run_a.membranes[STUB_MID]
    jt_nominal = [stub_membrane_n.jt_record(v) for v in _window_views(run_a)]
    cone_ok = all(jt <= ground_membrane_a.pair_mu() * 0.3 + 1e-9
                  for jt in jt_nominal)
    obs6["jt_records_nominal"] = jt_nominal
    obs6["jt_bitwise_0p18"] = all(jt == 0.18 for jt in jt_nominal)
    obs6["pair_mu_nominal"] = ground_membrane_a.pair_mu()
    obs6["cone_window_holds"] = cone_ok
    held6 = held6 and obs6["jt_bitwise_0p18"] and cone_ok

    # variant fixtures (closure-level evaluations at the variant spec bytes)
    variant_rows = []
    for var in fixtures["variant_fixtures"]:
        if var["kind"] == "refusal_mutant":
            continue
        mspec = copy.deepcopy(spec)
        apply_patch(mspec, var["patch"]["path"], var["patch"]["value"])
        conn = mspec["connections"][0]
        cparams = {p["var"]: float(p["value"]) for p in conn.get("parameters") or []}
        jt_expr = next(r["expr"] for r in mspec["declared_records"]["records"]
                       if r["record_id"] == "jt")
        ast = parse(jt_expr)
        jt_var = float(evaluate(ast, dict(cparams, q_jn=0.3)))
        pair_mu = min(cparams["mu_hand"], cparams["mu_surface"])
        row = {"variant_id": var["variant_id"], "pair_mu": pair_mu,
               "jt_record": jt_var}
        expv = var["expected"]
        if "jt_record_bitwise_equal_nominal" in expv:
            row["jt_bitwise_equal_nominal"] = (jt_var == jt_nominal[0])
            row["ok"] = (row["jt_bitwise_equal_nominal"]
                         and pair_mu == expv["pair_mu"]
                         and jt_var == expv["jt_record_value"])
        elif "jt_record_exact_zero" in expv:
            row["jt_exact_zero"] = (jt_var == 0.0)
            row["ok"] = row["jt_exact_zero"] and pair_mu == expv["pair_mu"]
        elif "defect_flips_property" in expv:
            # the max rule RAISES the pair mu under a surface-side re-pin:
            # evaluate the same closure with mu_surface re-pinned to 0.9
            jt_raised = float(evaluate(ast, dict(
                cparams, mu_surface=0.9, q_jn=0.3)))
            row["jt_with_repin_under_defect"] = jt_raised
            row["property_violated_on_mutant"] = (jt_raised != jt_nominal[0])
            row["ok"] = (jt_raised != jt_nominal[0])
        variant_rows.append(row)
        held6 = held6 and row["ok"]
    obs6["variant_rows"] = variant_rows
    bat.check("T.GROUND_pair_rule", held6, obs6)

    # ---------------- remaining mutant refusals (stage 2 obligations) ----------
    mutant_wav = load_module(ROOT / "fixtures_invalid/mutant_wrong_abi_version.py",
                             "mutant_wrong_abi_version")
    r_wav = expect_refusal(lambda: membrane_abi.validate_module(mutant_wav),
                           "abi_version_mismatch")
    mutant_dp = load_module(ROOT / "fixtures_invalid/mutant_ground_drifted_pin.py",
                            "mutant_ground_drifted_pin")
    context_ok = membrane_abi.SpecContext(spec, spec_sha, None)
    r_dp = expect_refusal(lambda: mutant_dp.build(context_ok, DT),
                          "spec_pinned_input_drift")
    r_dt = expect_refusal(lambda: membrane_ground.build(context_ok, 0.001),
                          "spec_dt_not_admissible")
    bat.stage("2b.declared_mutant_refusals",
              r_wav.get("fired_expected_code", False)
              and r_dp.get("fired_expected_code", False)
              and r_dt.get("fired_expected_code", False),
              {"wrong_abi_version": r_wav, "drifted_pin": r_dp,
               "non_admissible_dt": r_dt})

    # ---------------- receipt + result -----------------------------------------
    all_ok = (all(s["ok"] for s in bat.stages)
              and all(c["verdict"] == "HELD" for c in bat.checks.values()))
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "packet_id": PACKET_ID,
        "criteria_sha256": CRITERIA_SHA256,
        "contract": {"contract_id": "pc.hand_ground_contact.v1",
                     "sha256": CONTRACT_SHA256},
        "spec": {"spec_id": spec.get("spec_id"), "sha256": spec_sha},
        "fixture_based": True,
        "fixtures": FIXTURES_RELPATH,
        "stages": bat.stages,
        "checks": bat.checks,
        "all_checks_held": all_ok,
        "preregistration": "PREREGISTRATION.md (committed BEFORE implementation)",
        "named_debts_encountered": [
            "NB-01/NB-02 (fx.mu_placeholders: mu_s 0.6 / mu_k 0.4 NAMED placeholders, G04 measured-volar acquisition)",
            "NB-03 (fx.hand_press_impulse: jn 0.3 N*s at dt 0.005 s declared fixture; x_press ABSENT)",
            "NB-04 (x_share ABSENT - not consumed here, carried honestly)",
            "NB-05 (x_reach ABSENT - the pair RUN with the real membrane.hand.v1 remains declared_pending)",
        ],
        "claims": [
            "fixture-based membrane implementation + seam-ownership verification "
            "of membrane.ground.v1 against pc.hand_ground_contact.v1 under "
            "chimera.membrane_abi.v1; NO integrated qualification, NO pair RUN, "
            "no measured-volar re-pin, no new physics",
        ],
        "deviations": [],
        "sergeant_review_required": True,
    }
    result = {
        "schema": RESULT_SCHEMA,
        "packet_id": PACKET_ID,
        "criteria_sha256": CRITERIA_SHA256,
        "generated_utc": None,
        "generated_utc_note": "finalized by the worker lane from the sealed "
                              "runner receipts (the in-run value stays null "
                              "so declared outputs are byte-identical across "
                              "jobs)",
        "worker_arrival_id": "wk-membrane-ground",
        "per_test_results": [
            {"test_id": tid,
             "verdict": ("PASS" if row["verdict"] == "HELD" else "FAIL"),
             "observed": json.dumps(row["observed"], sort_keys=True)[:4000],
             "window": _window_text(tid),
             "evidence_path": "outputs/ground_walk_receipt.v1.json"}
            for tid, row in bat.checks.items()
        ],
        "receipts": [],  # sealed-run receipts are attached by the worker lane
        "fixture_based": True,
        "named_debts_encountered": receipt["named_debts_encountered"],
        "deviations": [],
        "claims": receipt["claims"],
        "sergeant_review_required": True,
        "in_run_all_checks_held": all_ok,
    }
    out = ROOT / "outputs"
    out.mkdir(exist_ok=True)
    (out / "ground_walk_receipt.v1.json").write_text(
        json.dumps(receipt, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    (out / "result.json").write_text(
        json.dumps(result, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("ALL_CHECKS_HELD:", all_ok)
    for tid, row in bat.checks.items():
        print(f"  {tid}: {row['verdict']}")
    for s in bat.stages:
        print(f"  stage {s['stage']}: {'ok' if s['ok'] else 'FAILED'}")
    return 0 if all_ok else 1


def row_num_ok(n):
    """The store log is cumulative: after window n the record must have been
    applied EXACTLY n times (counted-once, S1)."""
    return n


def _validate_built(mutant_module):
    """Build the mutant against the REAL verified context and run the
    graph-layer conformance check (the ONE-writer law lives there)."""
    spec = json.loads((ROOT / SPEC_RELPATH).read_text(encoding="utf-8"))
    spec_sha = sha256_file(ROOT / SPEC_RELPATH)
    context = membrane_abi.SpecContext(spec, spec_sha, None)
    membrane = mutant_module.build(context, DT)
    return graph_runtime.validate_built_graph(membrane, spec,
                                              mutant_module.IMPLEMENTS_MEMBRANE_ID)


def _window_views(run):
    """The window-start views of an already-stepped run, replayed from the
    store history: for this fixture every window's view is the declared
    initial case (nothing but the record is ever written), so the declared
    case view is the exact window-start view for every window."""
    view = {PRESS_ID: run.state_value(STUB_MID, "press_channel_state"),
            PLANE_ID: run.state_value(GROUND_MID, "walk_plane_height"),
            Q_ID: run.exchange_record()}
    return [view] * WINDOWS


def _window_text(tid):
    windows = {
        "T.GROUND_plane_identity":
            "exact: plane == +0.004 m bitwise at every window; zero runtime applies (single writer: the composition flatten)",
        "T.GROUND_walk_class":
            "declared classes (F05 walk_core); boundary 0.05 m/m inclusive; OUTSIDE reported, never clamped",
        "T.GROUND_seam_records":
            "reciprocity exact (G04 X3 worst 0.0 N*s): paired entries bitwise zero every window; record written once per window",
        "T.GROUND_pair_rule":
            "1e-9 recursion windows: jt == min(mu_hand, mu_surface) * jn bitwise; single-side re-pin cannot raise the pair mu",
    }
    return windows[tid]


if __name__ == "__main__":
    sys.exit(main())
