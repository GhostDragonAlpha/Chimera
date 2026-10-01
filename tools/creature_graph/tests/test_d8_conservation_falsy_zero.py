"""DEFECT 8 -- engine_live.py:61 `abs(tick.get("conserve_pct") or 1.0) < 0.01`:
the falsy-zero bug.  EXACT conservation (conserve_pct == 0.0, the BEST physical
outcome) is replaced by the sentinel 1.0 and the check FAILS, while a tiny
non-zero residue (1e-6) passes.

EXPECTED-HONEST: the check must pass for every |conserve_pct| < 0.01 INCLUDING
exactly 0.0; absence (None) must be reported as missing data, not conflated
with zero via `or`.
OBSERVED (base a12bfbcc): conserve_pct=0.0 fails the "conservation ~0" check;
conserve_pct=1e-6 passes; every OTHER check in the same report is green, so
the sentinel alone flips a perfectly conserved world to a failed verification.
"""

import json

import harness
import engine_live


def _tick(conserve_pct):
    return {"cells": [], "n_cells": 0, "sealed": True, "seal_refusal": None,
            "conserve_pct": conserve_pct, "V_whole": 0.0, "ts_us": 1,
            "ticks": 731615}


def _conservation_check(report):
    for c in report["checks"]:
        if c["check"] == "conservation ~0":
            return c
    return None


def run():
    g = harness.min_store(objects=[])  # no verified instances: conservation is the only live check

    report_zero = engine_live.cross_check(g, _tick(0.0))
    check_zero = _conservation_check(report_zero)
    others_zero = [c for c in report_zero["checks"] if c["check"] != "conservation ~0"]
    all_others_ok = all(c["ok"] for c in others_zero)

    report_eps = engine_live.cross_check(g, _tick(1e-6))
    check_eps = _conservation_check(report_eps)

    reproduced = (
        check_zero is not None
        and check_zero["ok"] is False          # EXACT zero FAILS
        and all_others_ok                      # nothing else is wrong
        and check_eps["ok"] is True            # 1e-6 PASSES
    )
    return harness.verdict(
        defect="D8",
        title="exact conservation zero fails via `or 1.0`",
        expected_honest="|conserve_pct| < 0.01 must pass INCLUDING exactly 0.0 "
                        "(the best case); None must be reported as missing, not "
                        "swapped for a sentinel",
        observed="conserve_pct=0.0 -> check ok=False (sentinel 1.0 substituted); "
                 "conserve_pct=1e-6 -> check ok=True; all other checks green in "
                 "both reports, so the falsy-zero alone fails a perfect world",
        reproduced=reproduced,
        evidence={
            "check_exact_zero": check_zero,
            "other_checks_exact_zero_all_ok": all_others_ok,
            "check_1e-6": check_eps,
            "code": "engine_live.py:61  abs(tick.get(\"conserve_pct\") or 1.0) < 0.01",
        },
        contract_refs=["engine_live.py:59-62", "ev acceptance: |conserve_pct| < 0.01"],
    )


def test_defect_8_reproduced():
    assert run()["verdict"] == "REPRODUCED"


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))
