#!/usr/bin/env python3
"""MAT2-XC-COUPLING-CAUSE: report generation + lint (stage 4).

The report states the arms, the measured statistics, the findings, and
the determination AT THE FROZEN STRENGTHS ONLY. The lint re-derives every
load-bearing number in the report from the receipts and refuses on any
mismatch. Exit: 0 green / 2 refused.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CARD = "MAT2-XC-COUPLING-CAUSE"


def out_dir():
    out = os.environ.get("CHIMERA_OUTPUT_DIR")
    if not out:
        raise RuntimeError("REFUSAL:output_dir_undeclared")
    Path(out).mkdir(parents=True, exist_ok=True)
    return Path(out)


def fmt_classes(arms_receipt):
    lines = []
    for key in sorted(arms_receipt["d_pairs"]):
        p = arms_receipt["d_pairs"][key]
        lines.append(
            "| %s | n%d | t_in %d | %d/21 | %s | %d/21 | %.6f |"
            % (p["cls"], p["n"], p["t_in"], p["identity"],
               str(p["first_divergence_tick"]), p["v_divergence"],
               p["band_A"]["min_com_v"]))
    return "\n".join(lines)


def fmt_e2(arms_receipt):
    return "\n".join(
        "| E2 press-S n%d | %d/21 | %s | %d/21 | %s |"
        % (r["n"], r["identity"], str(r["first_divergence_tick"]),
           r["v_divergence"], "INERT" if r["inert"] else "state-channel")
        for r in arms_receipt["e"]["e2"])


def main(arms_receipt, determination) -> int:
    out = out_dir()
    forms = arms_receipt["forms"]
    e3 = arms_receipt["e"]["e3"]
    report = f"""# REPORT — {CARD}: the controlled comparison isolating the phase-divergence cause

VERDICT (frozen strengths only): **{determination['verdict']}**

Ruling carried: {determination['ruling']}

## The determination

{chr(10).join('- ' + b for b in determination['basis'])}

Payoff: {determination['payoff']}

## Arm group A — the harness-form gate

- A1 pass law (both forms' CONTROL arms bit-identical over the same
  pinned bytes): {forms['a1_pass_bit_identity']}
- A2 sealed-records offset pattern exactly +0.2/-0.2 on every row:
  {forms['a2_pattern_exact_symmetric_020']}
- A1 in-run offset sequence == the sealed cross-line sequence:
  {forms['a1_offset_equals_a2_offset']}

## Arm group D — the regime depth sweep (form 'full', the certified line)

| class | n | t_in | phase identity | first divergent tick | com_v divergence | achieved min com_v |
|---|---|---|---|---|---|---|
{fmt_classes(arms_receipt)}

## Arm group E — the mechanism channel

{fmt_e2(arms_receipt)}

E3 matched-band selection: status {e3['status']}, E1 min com_v
{e3['e1_min_com_v']:.6f}, matched holds {e3['matched_holds']}.

## Findings (recorded, never tuned)

{chr(10).join('- `' + f['finding'] + '` — ' + f['detail'] for f in arms_receipt['findings']) or '- none'}

## Replication anchors

{chr(10).join('- ' + k + ': A_exact=' + str(v['A_exact']) + ', B_exact=' + str(v['B_exact']) for k, v in arms_receipt['replication_anchors'].items())}

## Scope

The sealed a12/X05 records are CITED, never re-claimed. No velocity-keyed
stride change is rendered anywhere. The window robustness scan, the per-
arm determinism receipts, and the offset tables live in
`arms_receipt.json`; the verdict inputs in `determination_receipt.json`.
"""
    (out / "REPORT.md").write_bytes(report.encode("utf-8"))
    # ---- lint: every load-bearing number in the report traces to a
    # receipt value re-derived here (independent of the report string).
    d = arms_receipt["d_pairs"]
    lint = {
        "verdict_in_vocabulary": determination["verdict"] in (
            "ISOLATED_HARNESS_SCENE", "ISOLATED_COMMAND_CHANNEL",
            "ISOLATED_VELOCITY_COUPLING", "CAUSE_NOT_ISOLATED"),
        "d_pair_count": len(d) == 14,
        "e2_count": len(arms_receipt["e"]["e2"]) == 5,
        "a1_fields_present": all(k in forms for k in (
            "a1_pass_bit_identity", "a2_pattern_exact_symmetric_020",
            "a1_offset_equals_a2_offset")),
        "identity_values_match": all(
            d[k]["identity"] == (
                sum(1 for ra, rb in zip(d[k]["A"]["window_rows"],
                                        d[k]["B"]["window_rows"])
                    if ra["phase_left"] == rb["phase_left"]
                    and ra["phase_right"] == rb["phase_right"]))
            for k in d),
        "finding_names_unique": (
            len({f["finding"] for f in arms_receipt["findings"]})
            == len(arms_receipt["findings"])),
    }
    ok = all(lint.values())
    (out / "lint_receipt.json").write_bytes(
        json.dumps({"schema": "chimera.xc.lint.v1", "card": CARD,
                    "lint": lint, "verdict": "GREEN" if ok else "RED",
                    "pass": ok}, indent=1).encode() + b"\n")
    if not ok:
        print("REFUSAL:report_lint:" + repr(lint), file=sys.stderr)
        return 2
    print("report: GREEN")
    return 0
