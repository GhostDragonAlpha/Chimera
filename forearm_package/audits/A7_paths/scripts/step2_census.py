"""A7 step 2 - comparability census (the 42/120 claim).

Comparability rule, read from baseline_snapshot/code/experiment_transverse_fit.py
lines 382-408 (tendon_deltas loop): a tendon is `comparable` (ok_chain == True)
iff EVERY site of its ordered path has a finite fitted global position in the
fitted packet. Unresolved (NaN -> null) sites are skipped and the summed length
bridges across the last resolved point, but ok_chain is False, so the recorded
path_length_delta_m is null for such tendons.

This script re-implements that rule from the packet alone, verifies the 42 count,
cross-checks every flag against runs/experiment_transverse_candidate.json, and
enumerates all non-comparable tendons with the unresolved bodies each touches.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

BASE = Path(r"E:\PythonChimera\forearm_package\baseline_snapshot")
OUT = Path(r"E:\PythonChimera\forearm_package\audits\A7_paths\receipts")

FIT = json.loads((BASE / "runs" / "actual_monkey_fit.json").read_text(encoding="utf-8"))
EXP = json.loads((BASE / "runs" / "experiment_transverse_candidate.json").read_text(encoding="utf-8"))


def main() -> None:
    sites_by_name = {s["name"]: s for s in FIT["sites"]}
    unresolved_bodies = set(FIT["admission"]["bodies"]["unresolved"])
    # independence check: the packet's own per-site `unresolved` flag must agree
    # with the admission ledger's unresolved-body list, for every path site
    flag_disagreements = []
    for s in FIT["sites"]:
        should = s["segment"] in unresolved_bodies
        if bool(s.get("unresolved", False)) != should:
            flag_disagreements.append(s["name"])

    comparable, non_comparable = [], []
    reasons: dict[str, list[str]] = {}
    for t in FIT["tendons"]:
        bad_bodies = []
        for sn in t["sites"]:
            s = sites_by_name[sn]
            if s["fitted_pos_global"] is None or s["segment"] in unresolved_bodies:
                if s["segment"] not in bad_bodies:
                    bad_bodies.append(s["segment"])
        if bad_bodies:
            non_comparable.append(t["name"])
            reasons[t["name"]] = sorted(bad_bodies)
        else:
            comparable.append(t["name"])

    # cross-check against the experiment record, flag by flag
    td = EXP["tendon_deltas"]
    flag_mismatch = []
    delta_null_mismatch = []
    for name, rec in td.items():
        mine = name in set(comparable)
        if bool(rec["comparable"]) != mine:
            flag_mismatch.append(name)
        if rec["comparable"] and rec["path_length_delta_m"] is None:
            delta_null_mismatch.append(name)
        if (not rec["comparable"]) and rec["path_length_delta_m"] is not None:
            delta_null_mismatch.append(name)

    # categories: by the exact set of unresolved bodies in the chain
    by_set = Counter(tuple(reasons[n]) for n in non_comparable)
    by_body = Counter()
    for n in non_comparable:
        for b in reasons[n]:
            by_body[b] += 1
    # the 78 must not overlap the 42
    overlap = sorted(set(comparable) & set(non_comparable))

    receipt = {
        "rule_source": "experiment_transverse_fit.py lines 382-408: ok_chain iff every path site finite",
        "n_comparable_recomputed": len(comparable),
        "n_non_comparable_recomputed": len(non_comparable),
        "claim_in_record": "42/120",
        "count_verified": len(comparable) == 42 and len(non_comparable) == 78,
        "flag_mismatch_vs_experiment_record": flag_mismatch,
        "delta_null_mismatch_vs_experiment_record": delta_null_mismatch,
        "admission_unresolved_bodies": sorted(unresolved_bodies),
        "per_site_unresolved_flag_vs_admission_disagreements": flag_disagreements,
        "overlap_42_78": overlap,
        "category_counts_by_unresolved_body_set": {" + ".join(k): v for k, v in sorted(by_set.items())},
        "per_unresolved_body_tendon_counts": dict(sorted(by_body.items())),
        "comparable_42": sorted(comparable),
        "non_comparable_78": [
            {"tendon": n, "unresolved_bodies_in_chain": reasons[n]} for n in sorted(non_comparable)
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "step2_census_receipt.json").write_text(json.dumps(receipt, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in receipt.items() if k != "non_comparable_78" and k != "comparable_42"}, indent=1))
    print("-- non-comparable enumeration (tendon: unresolved bodies) --")
    for n in sorted(non_comparable):
        print(f"{n}: {', '.join(reasons[n])}")


if __name__ == "__main__":
    main()
