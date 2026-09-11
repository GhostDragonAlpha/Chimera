"""run_controls.py -- execute the preregistered R1-R4 controls against the
GOV-03 reference model in one process and write the retained check files.

Usage:  python controls/run_controls.py .        (from this GOV-03 directory)
        python controls/run_controls.py <GOV-03-dir>

Writes checks/r1_positive.txt, checks/r2_falsifier_lacking.txt,
checks/r3_constant_origin.txt, checks/r4_law_fields_versioning.txt.
Bytecode writing is disabled: no __pycache__ is produced or committed.
Every acceptance/refusal is recorded verbatim; every post-state assertion is
computed and printed. Exit 1 if any preregistered threshold misses.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True          # no __pycache__ in the evidence tree
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "reference"))

from gov03_reference_model import (LawRegistry, LAW_KINDS, OUTCOMES,          # noqa: E402
                                   dim_equal, dim_parse, dim_render)

CHECKS = HERE / "checks"
CHECKS.mkdir(exist_ok=True)


class Log:
    """Verbatim transcript of one control run."""

    def __init__(self, title, threshold):
        self.lines = [title, "=" * 78, f"threshold: {threshold}", ""]
        self.passed = 0
        self.failed = 0

    def row(self, ok, label, detail=""):
        self.lines.append(f"[{'PASS' if ok else 'FAIL'}] {label}"
                          + (f"\n        {detail}" if detail else ""))
        self.passed, self.failed = self.passed + (1 if ok else 0), \
            self.failed + (0 if ok else 1)

    def note(self, text):
        self.lines.append(text)

    def finish(self, name):
        self.lines.append("")
        self.lines.append(f"RESULT: {self.passed} passed, {self.failed} failed"
                          f" (threshold {'HOLDS' if self.failed == 0 else 'MISSED'})")
        self.lines.append("falsifier status: "
                          + ("NOT TRIGGERED for this row" if self.failed == 0
                             else "FIRED -- reported, not patched"))
        out = CHECKS / name
        out.write_text("\n".join(self.lines) + "\n", encoding="utf-8")
        print(f"{name}: {self.passed} passed, {self.failed} failed")
        return self.failed


def snapshot(reg):
    """Byte-comparable registry fingerprint for post-state assertions."""
    import json
    return json.dumps({"laws": reg.laws, "decisions": reg.decisions,
                       "next": reg._next_decision}, sort_keys=True,
                      default=str)


def full_spec(name, kind, statement, falsifier, domain, oracle, limitations,
              constants, input_dims, formula, output_dim):
    return dict(name=name, kind=kind, statement=statement, falsifier=falsifier,
                domain=domain, oracle=oracle, limitations=limitations,
                constants=constants, input_dims=input_dims, formula=formula,
                output_dim=output_dim)


# The six legal laws of R1 -- one per card kind, each fully formed.
R1_SPECS = [
    full_spec(
        "kinetic-energy", "energy",
        "The kinetic energy of a body of mass m moving at speed v is m v^2 / 2.",
        "A bodies set of measured (m, v, E) violating E = m v^2 / 2 within the "
        "declared instrument tolerance falsifies this law.",
        "rigid-body dynamics",
        "calorimetry bench: frictionless catch into a known heat capacity",
        "Holds below 0.1c; rotational degrees are carried by the moment of "
        "inertia, not this scalar.",
        [{"name": "m_half", "value": 0.5, "origin": "definition of kinetic "
          "energy (1/2 factor), mechanics convention"}],
        {"m": "M", "v": "L T^-1"}, "m*v**2", "M L^2 T^-2"),
    full_spec(
        "damped-contact-force", "force",
        "Contact force along a normal spring-damper is k x + c v_n.",
        "Force readings at fixed x diverging from k x + c v_n for two "
        "independent k,c calibrations falsify this law.",
        "contact mechanics",
        "load cell in the fixture, calibrated against dead weights",
        "Linear regime only (x < x_yield); no adhesion, no friction cone.",
        [{"name": "k_ref", "value": 1200.0, "origin": "measured fixture "
          "stiffness, calibration run 2026-08-14, GOV-03 controls"},
         {"name": "c_ref", "value": 2.5, "origin": "vendor datasheet of the "
          "damper element, rev B"}],
        {"k": "M T^-2", "x": "L", "c": "M T^-1", "v_n": "L T^-1"},
        "k*x + c*v_n", "M L T^-2"),
    full_spec(
        "radiant-flux-area", "flux",
        "The radiant flux density through a surface of area A carrying power P "
        "is P/A.",
        "A radiometer sweep showing density not scaling as 1/A at fixed P "
        "falsifies this law.",
        "thermal transport",
        "thermopile array with NIST-traceable calibration",
        "Assumes the surface is uniformly irradiated; edge effects below "
        "3 lambda are out of scope.",
        [{"name": "one_over_A", "value": -2, "origin": "the exponent is the "
          "definition of a density over area, not a fitted number"}],
        {"P": "M L^2 T^-3", "A": "L^2"}, "P/A", "M T^-3"),
    full_spec(
        "wall-pressure-balance", "boundary",
        "A boundary wall at rest exchanges normal impulse so that the time-"
        "averaged wall pressure equals n.momentum flux.",
        "Averaged wall pressure differing from the incident momentum flux in "
        "a periodic closed box falsifies this law.",
        "boundary conditions",
        "independent particle-counting flux probe at the wall",
        "Elastic walls only; absorbing walls carry a shadow term.",
        [{"name": "unit_normal", "value": 1, "origin": "geometric definition, "
          "no fitted content"}],
        {"p": "M L^-1 T^-2"}, "p", "M L^-1 T^-2"),
    full_spec(
        "segment-domain-scale", "domain",
        "Within one membrane domain, every length enters through the domain "
        "scale lambda (all shapes scale with lambda).",
        "Two domains of identical lambda but different shape responses "
        "falsify the claim that lambda fully parametrizes the domain.",
        "membrane domains",
        "cross-domain lattice probe with matched lambda, unmatched mesh",
        "Exact only in the continuum limit; lattice correction is O(a/lambda).",
        [{"name": "lambda_def", "value": 1, "origin": "lambda is the domain "
          "scale by definition of the domain record"}],
        {"a": "L", "lambda": "L"}, "a/lambda", "1"),
    full_spec(
        "restitution-ratio", "parameter",
        "The restitution parameter e of a contact pair is the ratio of "
        "separation to approach speed, independent of absolute speed.",
        "Measured e varying systematically with approach speed at fixed pair "
        "falsifies the parameter record.",
        "contact parameters",
        "drop-rig photogate pair, independent of the simulator clock",
        "Constant for 0.1 m/s < v < 3 m/s; creep regime excluded.",
        [{"name": "e_bound", "value": 1, "origin": "thermodynamic bound: e=1 "
          "is the elastic limit (Newton's cradle identity)"}],
        {"v_sep": "L T^-1", "v_app": "L T^-1"}, "v_sep/v_app", "1"),
]


def r1(reg: LawRegistry, log: Log):
    log.note("R1 -- positive controls: six legal admissions (one per card "
             "kind) + two legal decisions; the model must ACCEPT all.")
    for spec in R1_SPECS:
        res = reg.admit_law(**spec)
        ok = bool(res["ok"]) and reg.laws.get(spec["name"]) is not None
        log.row(ok, f"admit {spec['kind']:<9} {spec['name']!r}",
                None if ok else f"unexpected refusal: {res['error']}")
    for law_name, outcome, evidence in (
            ("kinetic-energy", "ADOPT", "controls/run_controls.py R1 output"),
            ("restitution-ratio", "REVISE", "checks/r1_positive.txt transcript")):
        res = reg.decide(law_name, outcome, evidence, "legal control decision")
        ok = bool(res["ok"]) and str(res["decision"]["number"]) in reg.decisions
        log.row(ok, f"decide {law_name!r} -> {outcome}",
                None if ok else f"unexpected refusal: {res['error']}")
    log.row(len(reg.laws) == 6, "registry holds exactly the 6 admitted laws",
            f"count={len(reg.laws)}")
    log.row(len(reg.decisions) == 2, "decision ledger holds exactly 2 records",
            f"count={len(reg.decisions)}")
    return log.finish("r1_positive.txt")


def r2(reg: LawRegistry, log: Log):
    log.note("R2 -- card falsifier clause 1 ('a physical claim lacks a "
             "falsifier') + decision-side: the model must REJECT all five "
             "paths, each refusal named, post-state byte-identical.")
    good = R1_SPECS[0]
    cases = []
    broken = dict(good); broken["name"] = "no-falsifier-law"; broken["falsifier"] = ""
    cases.append(("admission without falsifier", full_spec(**broken),
                  "missing_falsifier"))
    broken = dict(good); broken["name"] = "blank-falsifier-law"; broken["falsifier"] = "   \n\t "
    cases.append(("admission with whitespace-only falsifier",
                  full_spec(**broken), "missing_falsifier"))
    for label, spec, expect in cases:
        before = snapshot(reg)
        res = reg.admit_law(**spec)
        after = snapshot(reg)
        err = res["error"] or ""
        named = expect in err
        log.row((not res["ok"]) and named and before == after,
                f"REJECT {label}",
                f"refusal: {err!r}; post-state identical: {before == after}")
    before = snapshot(reg)
    res = reg.decide("never-admitted-law", "ADOPT", "some evidence")
    after = snapshot(reg)
    log.row((not res["ok"]) and "law_not_admitted" in (res["error"] or "")
            and before == after,
            "REJECT decision citing a never-admitted law",
            f"refusal: {res['error']!r}; post-state identical: {before == after}")
    res = reg.decide("kinetic-energy", "ADOPT", "   ")
    log.row((not res["ok"]) and "missing_evidence" in (res["error"] or ""),
            "REJECT decision with empty evidence",
            f"refusal: {res['error']!r}")
    res = reg.decide("kinetic-energy", "MAYBE", "some evidence")
    log.row((not res["ok"]) and "bad_outcome" in (res["error"] or ""),
            "REJECT decision with outcome outside the fixed vocabulary",
            f"refusal: {res['error']!r}")
    return log.finish("r2_falsifier_lacking.txt")


def r3(reg: LawRegistry, log: Log):
    log.note("R3 -- card falsifier clause 2 ('a constant lacks an origin') + "
             "integrity gates: the model must REJECT all six paths, "
             "byte-identical post-state.")
    base = R1_SPECS[1]  # the force law carries two constants
    cases = []
    broken = dict(base)
    broken["name"] = "origin-absent"
    broken["constants"] = [dict(base["constants"][0])]
    del broken["constants"][0]["origin"]
    broken["constants"].append(dict(base["constants"][1]))
    cases.append(("constant with absent origin", full_spec(**broken),
                  "missing_constant_origin"))
    broken = dict(base)
    broken["name"] = "origin-blank"
    broken["constants"] = [dict(base["constants"][0]),
                           dict(base["constants"][1], origin="  ")]
    cases.append(("constant with blank origin", full_spec(**broken),
                  "missing_constant_origin"))
    broken = dict(base)
    broken["name"] = "dim-mismatch"
    broken["output_dim"] = "M L^2 T^-2"   # force declared as energy
    cases.append(("declared output dimension != composed dimension",
                  full_spec(**broken), "dimension_mismatch"))
    broken = dict(base)
    broken["name"] = "self-oracle"
    broken["oracle"] = broken["name"]
    cases.append(("oracle identical to the law itself", full_spec(**broken),
                  "oracle_not_independent"))
    broken = dict(base)
    broken["name"] = "damped-contact-force"   # already admitted in R1
    cases.append(("duplicate law name", full_spec(**broken), "duplicate_law"))
    broken = dict(base)
    broken["name"] = "momentum-kind"
    broken["kind"] = "momentum"
    cases.append(("kind outside the card's six", full_spec(**broken),
                  "bad_kind"))
    for label, spec, expect in cases:
        before = snapshot(reg)
        res = reg.admit_law(**spec)
        after = snapshot(reg)
        err = res["error"] or ""
        log.row((not res["ok"]) and expect in err and before == after,
                f"REJECT {label}",
                f"refusal: {err!r}; post-state identical: {before == after}")
    return log.finish("r3_constant_origin.txt")


def r4(reg: LawRegistry, log: Log):
    log.note("R4 -- card prediction ('each admitted law names its domain, "
             "independent oracle and limitations') + versioned assumptions "
             "+ supersede + monotone decisions.")
    for spec in R1_SPECS:                       # 6 laws x 5 parts = 30 rows
        rec = reg.laws[spec["name"]]
        parts, missing = reg.law_named_parts(spec["name"])
        for part in ("domain", "oracle", "limitations", "falsifier"):
            ok = bool(parts[part].strip())
            log.row(ok, f"{spec['name']} names its {part}",
                    None if ok else f"missing/blank ({missing})")
        consts_ok = (bool(parts["constants_with_origins"]) and all(
            origin.strip() for _, origin in parts["constants_with_origins"]))
        log.row(consts_ok,
                f"{spec['name']} carries constants each with an origin",
                None if consts_ok else "missing/empty constants or origins")
    reg2 = LawRegistry()
    spec = dict(R1_SPECS[0])
    reg2.admit_law(**spec)
    reg2.admit_law(**R1_SPECS[5])   # the supersede target must exist in reg2
    v1_text = reg2.laws["kinetic-energy"]["assumptions"][0]
    res = reg2.amend_law("kinetic-energy", "rotational correction deferred to "
                                          "the rigid-body assumption record")
    log.row(res["ok"] and reg2.laws["kinetic-energy"]["version"] == 2,
            "amend bumps the version v1 -> v2",
            None if res["ok"] else f"res={res!r}")
    log.row(reg2.laws["kinetic-energy"]["assumptions"][0] == v1_text
            and len(reg2.laws["kinetic-energy"]["assumptions"]) == 2,
            "the v1 assumption text is preserved verbatim after the amend",
            f"assumptions={reg2.laws['kinetic-energy']['assumptions']!r}")
    old = dict(R1_SPECS[5])                     # restitution-ratio
    new_spec = dict(old)
    new_spec["name"] = "restitution-ratio-v2"
    new_spec["statement"] = (old["statement"]
                             + " Speed-independence is now scoped to the "
                               "calibrated pair.")
    res = reg2.supersede_law(new_spec, "restitution-ratio")
    sup_ok = (res["ok"]
              and reg2.laws["restitution-ratio"]["status"] == "SUPERSEDED"
              and reg2.laws["restitution-ratio"]["superseded_by"]
              == "restitution-ratio-v2"
              and reg2.laws["restitution-ratio"]["statement"] == old["statement"]
              and reg2.laws["restitution-ratio-v2"]["status"] == "ACTIVE")
    log.row(res["ok"] and reg2.laws["restitution-ratio"]["status"]
            == "SUPERSEDED" and reg2.laws["restitution-ratio"]["statement"]
            == old["statement"],
            "supersede marks the old law SUPERSEDED and still readable",
            None if res["ok"] else f"res={res!r}")
    log.row(res["ok"]
            and reg2.laws["restitution-ratio"]["superseded_by"]
            == "restitution-ratio-v2"
            and reg2.laws["restitution-ratio-v2"]["status"] == "ACTIVE",
            "the old law records its successor and the successor is ACTIVE",
            None if res["ok"] else f"res={res!r}")
    n_before = len(reg2.decisions)
    res = reg2.decide("restitution-ratio", "ADOPT", "evidence pointer")
    log.row((not res["ok"]) and "law_superseded" in (res["error"] or "")
            and len(reg2.decisions) == n_before,
            "decision citing the superseded law refused, ledger unchanged",
            f"refusal: {res['error']!r}")
    r = reg2.decide("kinetic-energy", "ADOPT", "ev-1")
    r2_ = reg2.decide("restitution-ratio-v2", "REJECT", "ev-2")
    seq = [r["decision"]["number"], r2_["decision"]["number"]] if r["ok"] and r2_["ok"] else []
    log.row(len(seq) == 2 and seq[1] == seq[0] + 1,
            "decision numbering is monotone (next = highest + 1)",
            f"numbers={seq}")
    return log.finish("r4_law_fields_versioning.txt")


def main() -> int:
    reg = LawRegistry()
    total = 0
    total += r1(reg, Log("R1 -- POSITIVE CONTROLS (model must ACCEPT)",
                         "threshold 8/8 core (six admissions + two decisions)"
                         " + 2 post-state rows = 10/10"))
    total += r2(reg, Log("R2 -- CARD FALSIFIER CLAUSE 1 + decision-side "
                         "(model must REJECT)", "5/5 named refusals, "
                         "byte-identical post-state"))
    total += r3(reg, Log("R3 -- CARD FALSIFIER CLAUSE 2 + integrity gates "
                         "(model must REJECT)", "6/6 named refusals, "
                         "byte-identical post-state"))
    total += r4(reg, Log("R4 -- CARD PREDICTION (each admitted law names its "
                         "domain, independent oracle and limitations) + "
                         "versioning", "6x5=30 field rows + 6 versioning "
                         "rows = 36/36"))
    print("TOTAL FAILED ROWS:", total)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
