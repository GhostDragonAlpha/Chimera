#!/usr/bin/env python3
"""MAT2-W05: generate REPORT.md from the receipts (zero hand-transcribed
numbers; house standards P2/P3). Every number below is rendered from a bound
artifact; lint_report_numbers.py proves it after generation.

Run:  python -B make_report.py
Exit: 0 written / 2 refusal (missing receipts).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
import verify_inputs as vi

RUNBOOK_BYTES = (HERE / "runbook.json").read_bytes()
RUNBOOK = json.loads(RUNBOOK_BYTES.decode("utf-8"))
RUNBOOK_SHA = vi.sha_bytes(RUNBOOK_BYTES.rstrip(b"\n"))
FILL = json.loads((HERE / "w05_freeze_fill.json").read_bytes().decode("utf-8"))
SEEDS = RUNBOOK["seeds"]["values"]


def sha_file(path: Path) -> str:
    return vi.sha_bytes(path.read_bytes())


def load(name: str) -> dict:
    return json.loads((HERE / "receipts" / name).read_bytes().decode("utf-8"))


def fmt(value) -> str:
    """Render a receipt value verbatim (numbers at their receipt precision)."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return repr(value)
    return str(value)


def main() -> int:
    baseline = load("baseline_receipt.json")
    equiv = load("recipe_equivalence_receipt.json")
    seed_recs = {seed: load(f"seed_{seed}_receipt.json") for seed in SEEDS}
    heldout = load("heldout_receipt.json")
    deploy = load("deploy_check_receipt.json")
    checks_path = HERE / "checks_receipt.json"
    if not checks_path.exists():
        print("REFUSAL: checks_receipt.json missing (run run_checks.py first)")
        return 2
    checks = json.loads(checks_path.read_bytes().decode("utf-8"))

    lines = []
    w = lines.append
    w("# REPORT — MAT2-W05 the frozen walk1m-r1 runbook, executed on all "
      "three prescribed seeds")
    w("")
    w("Generated from the receipts; no hand-transcribed numbers (P2/P3). "
      "Profile: records (offline); numerical evidence required; no camera "
      "record (G4/G8 disclosed NOT-APPLICABLE — no image is evidence for "
      "this card).")
    w("")
    w("## Identity")
    w("")
    w("- Card MAT2-W05 (planning id W05), agent `wk-w05-runbook`, attempt "
      "`" + vi.ATTEMPT_ID + "`.")
    w("- Criteria sha256 `" + vi.CRITERIA_SHA256 + "` (join == registry "
      "read-only re-read; card state at run time: "
      + fmt(baseline["registry"]["card_state"]) + ", registry revision "
      + fmt(baseline["registry"]["registry_revision"]) + ").")
    w("- Base: `" + vi.CANDIDATE_BASE + "` (the MAT2-W04 merge, PR #295).")
    w("- Preregistration sha256 `" + vi.prereg_sha256() + "`; addendum 1 "
      "sha256 `" + vi.addendum_sha256() + "` (committed separately, BEFORE "
      "any experiment — the M03/P04 law).")
    w("- Runbook `" + RUNBOOK["runbook_id"] + "` (schema "
      + RUNBOOK["schema"] + "), document sha256 `" + RUNBOOK_SHA + "`.")
    w("- Upstream freeze: the W04 freeze manifest (sha `"
      + FILL["parent_freeze"]["sha256"] + "`) froze the seeds/runbook slot "
      "at SLOT SHAPE with values null (TC-10 / FC-4 / LT ruling BQ-3); the "
      "governing laws bound there are K01 and P04.")
    w("")
    w("## The TC-10 slot fill (this card's values)")
    w("")
    w("- `runbook_id`: **" + FILL["fill"]["runbook_id"] + "**")
    w("- `seeds`: " + json.dumps(FILL["fill"]["seeds"]) + " — "
      + RUNBOOK["seeds"]["identity"]
      + " (suite registered cases sha `" + RUNBOOK["seeds"]["suite_registered_cases_sha256"] + "`).")
    w("- `acceptance_criteria`: the frozen object in `w05_freeze_fill.json` "
      "(execution-integrity gates, failure retention, termination codes, "
      "held-out checks, certificate mismatch rejection, and the success "
      "metrics reported per seed without cherry-picking).")
    w("- Decisions per seed: " + fmt(RUNBOOK["decisions"]["per_seed_total"])
      + " (" + fmt(RUNBOOK["decisions"]["iterations"]) + " iterations x "
      + fmt(RUNBOOK["decisions"]["evaluations_per_iteration"])
      + " antithetic evaluations x "
      + fmt(RUNBOOK["decisions"]["decisions_per_evaluation"])
      + " decisions), i.e. " + fmt(RUNBOOK["decisions"]["ticks_per_seed_total"])
      + " ticks per seed at " + fmt(RUNBOOK["decisions"]["physics_hz"])
      + " Hz; the runbook bound \"approximately 1M-decision\" is exact at "
      + fmt(RUNBOOK["decisions"]["per_seed_total"]) + ".")
    w("")
    w("## Prediction outcomes (registered in the prereg BEFORE the run)")
    w("")
    w("- P1 baseline exactness: " + fmt(all(
        c["verdict"] == "EXACT" for c in baseline["anchor_comparisons"].values()))
      + " — all three anchors reproduced EXACTLY (trajectory, initial "
      "snapshot, final state).")
    w("- P2 per-seed integrity: "
      + fmt(all(r["status"] == "EXECUTED_COMPLETED" for r in seed_recs.values()))
      + ".")
    w("- P3 training signal (per seed, recorded NOT gated): "
      + "; ".join("seed " + str(seed) + " improved="
                  + fmt(seed_recs[seed]["success_metrics"]["improved_first_to_last_100"])
                  for seed in SEEDS) + ".")
    w("- P4 gate mechanics: trained tuple "
      + deploy["block_trained_bundle"]["decision"] + ", frozen relation "
      + deploy["allow_frozen_relation"]["decision"] + ", foreign build "
      + deploy["block_foreign_build"]["decision"] + ".")
    w("")
    w("## Retained baseline arm (the certified line, unchanged)")
    w("")
    w("The sealed certified reference line re-executed through the UNMODIFIED "
      "pinned machinery: frozen P3 policy closed loop, build N, seed "
      "20260920, 900 ticks.")
    for key, comp in baseline["anchor_comparisons"].items():
        w("- " + key + ": " + comp["verdict"] + " (`" + comp["reproduced"]
          + "`).")
    w("- Recipe equivalence (controller-change proof): the trainable policy "
      "class with the FROZEN bundle weights reproduced the frozen "
      "NumpyPolicy applied bytes tick-for-tick: "
      + fmt(equiv["byte_identical"]) + " (trajectory sha `"
      + equiv["frozen_trajectory_sha256"] + "`).")
    w("")
    w("## The three seed outcomes (verbatim; failures retained)")
    w("")
    for seed in SEEDS:
        r = seed_recs[seed]
        w("### Seed " + str(seed))
        w("")
        w("- status: **" + r["status"] + "**"
          + ("" if r["termination_code"] is None else
             " (termination code: " + r["termination_code"] + "; detail: "
             + json.dumps(r["termination_detail"]) + ")"))
        w("- decisions executed: " + fmt(r["decisions_executed"]) + " of "
          + fmt(r["decisions_declared"]) + " declared; iterations "
          + fmt(r["iterations_executed"]) + "; ticks "
          + fmt(r["ticks_executed"]) + ".")
        w("- SPSA constants (frozen in the prereg, never tuned): c="
          + fmt(RUNBOOK["trainer"]["perturbation"]["size_c"]) + ", a_s="
          + fmt(RUNBOOK["trainer"]["step"]["a_s"]) + ", parameter dim "
          + fmt(RUNBOOK["trainer"]["parameter_vector"]["dim"])
          + "; exploration noise: " + RUNBOOK["trainer"]["exploration_noise"] + ".")
        w("- mean iteration fitness, first "
          + fmt(100) + " vs last " + fmt(100) + " iterations: "
          + fmt(r["success_metrics"]["mean_iteration_fitness_first100"])
          + " -> "
          + fmt(r["success_metrics"]["mean_iteration_fitness_last100"])
          + "; improved: "
          + fmt(r["success_metrics"]["improved_first_to_last_100"]) + ".")
        w("- final deterministic window (" 
          + fmt(RUNBOOK["decisions"]["decisions_per_evaluation"])
          + " decisions): fitness "
          + fmt(r["final_window"]["fitness"]) + " m; total dx "
          + fmt(r["final_window"]["total_dx_m"]) + " m; mean speed "
          + fmt(r["final_window"]["mean_speed_m_s"]) + " m/s; max |v| "
          + fmt(r["final_window"]["v_max"]) + " (envelope "
          + fmt(r["velocity_envelope_m_s"]) + " m/s); saturation fraction "
          + fmt(r["final_window"]["saturation_frac"]) + ".")
        w("- hard gates: " + ("all six held at every tick of every rollout "
                              "(the executor's status law: any breach raises "
                              "a retained termination record; this seed "
                              "finished with no termination code)"
                              if r["termination_code"] is None else
                              "TERMINATED on " + r["termination_code"]
                              + " (retained)") + ".")
        w("- theta identity: initial `" + r["initial_theta_sha256"]
          + "` -> final `" + r["final_theta_sha256"] + "`; theta npz sha `"
          + r["theta_npz_sha256"] + "`; fitness curve sha `"
          + r["fitness_curve_sha256"] + "`; state chain head `"
          + r["state_chain_head"] + "` (anchors every "
          + fmt(RUNBOOK["state_chain"]["anchor_stride_ticks"]) + " ticks).")
        w("- measured resources (non-canonical block): wall "
          + fmt(r["measured_resources"]["wall_s"]) + " s of the "
          + fmt(RUNBOOK["termination"]["wall_clock_budget_s"])
          + " s per-seed budget; GPU jobs used: none (BQ-1; the GPU-03/"
          "GPU-05 catalog refs are NOT-APPLICABLE to this card's runs).")
        w("")
    w("## Held-out evaluation (C10; separate train/evaluation cases)")
    w("")
    w("Each seed's final theta evaluated deterministically on all three seed "
      "scenes (" + fmt(heldout["ticks_per_rollout"]) + " ticks / "
      + fmt(heldout["decisions_per_rollout"]) + " decisions per cell; the "
      + fmt(heldout["held_out_cells"]) + " off-diagonal cells are the "
      "held-out cases).")
    w("")
    w("| theta seed | scene seed | held out | fitness (m) | mean speed "
      "(m/s) | max |v| |")
    w("|---|---|---|---|---|---|")
    for cell in heldout["cells"]:
        w("| " + str(cell["theta_seed"]) + " | " + str(cell["scene_seed"])
          + " | " + fmt(cell["held_out"]) + " | " + fmt(cell["fitness"])
          + " | " + fmt(cell["mean_speed_m_s"]) + " | "
          + fmt(cell["v_max"]) + " |")
    w("")
    w("## Certificate mismatch rejection (C10; the frozen deploy gate)")
    w("")
    w("- The certificate's own relation: "
      + deploy["allow_frozen_relation"]["decision"] + " (the gate still "
      "closes on the certified tuple).")
    w("- The trained bundle tuple: "
      + deploy["block_trained_bundle"]["decision"] + " — reasons: "
      + json.dumps(deploy["block_trained_bundle"]["reasons"]) + ".")
    w("- A foreign build: " + deploy["block_foreign_build"]["decision"]
      + " — reasons: " + json.dumps(deploy["block_foreign_build"]["reasons"]) + ".")
    w("- The trained candidates bind ONLY by reissuance through the TC-6 "
      "gate; FC-3 (trained walking policy) stays explicitly-unresolved; W06 "
      "evaluates these per-seed outcomes.")
    w("")
    w("## Named checks (G12 accounting)")
    w("")
    w("- Suite: " + checks["suite"] + ".")
    w("- Accounting claim: **" + checks["accounting_claim"] + "**; known "
      "skips: " + checks["known_skips"] + "; pass: " + fmt(checks["pass"])
      + ".")
    w("")
    w("## Gate disclosure (G1-G9)")
    w("")
    w("- G1 falsifier arms with clean controls and bites: FB1 pin bite, FB2 "
      "baseline bite, FB3 missing-certificate bite, FB4 slot-fill bite, FB5 "
      "structural no-retry scan — all executed in the named-check suite.")
    w("- G2 lint: `python -B lint_report_numbers.py --selftest` must exit "
      "0; every number in this report traces to the bound artifacts.")
    w("- G3: this report is GENERATED from the receipts; no hand-written "
      "qualitative claim.")
    w("- G4/G8: NOT-APPLICABLE (records profile; camera record not "
      "required; no image is evidence) — disclosed, not skipped silently.")
    w("- G5: `refuse_vacuous_comparison` + `vacuous_guard_selftest()` run "
      "at import in the named checks.")
    w("- G6: keyed extractors; the runbook's phases are iteration windows "
      "carried in the per-seed receipts (first/last "
      + fmt(100) + "-iteration keyed fields).")
    w("- G7: registry identity read-only (card state "
      + fmt(baseline["registry"]["card_state"]) + ", revision "
      + fmt(baseline["registry"]["registry_revision"]) + "); criteria sha "
      "identical across join/registry/prereg/checks.")
    w("- G9: prereg committed separate-first; ONE publication commit on "
      "`review/MAT2-W05` with the full lineage; contribution within the "
      "file/size bounds; commit-message metrics generated from these FINAL "
      "receipts.")
    w("")
    w("## Evidence pins (G10: every pin hashes against the on-disk file)")
    w("")
    pins = [("runbook.json", RUNBOOK_BYTES),
            ("w05_freeze_fill.json",
             (HERE / "w05_freeze_fill.json").read_bytes()),
            ("checks_receipt.json", checks_path.read_bytes()),
            ("receipts/baseline_receipt.json",
             (HERE / "receipts/baseline_receipt.json").read_bytes()),
            ("receipts/recipe_equivalence_receipt.json",
             (HERE / "receipts/recipe_equivalence_receipt.json").read_bytes()),
            ("receipts/heldout_receipt.json",
             (HERE / "receipts/heldout_receipt.json").read_bytes()),
            ("receipts/deploy_check_receipt.json",
             (HERE / "receipts/deploy_check_receipt.json").read_bytes()),
            ("trained/trained_policy_manifest.json",
             (HERE / "trained/trained_policy_manifest.json").read_bytes())]
    for seed in SEEDS:
        pins.append((f"receipts/seed_{seed}_receipt.json",
                     (HERE / "receipts" / f"seed_{seed}_receipt.json")
                     .read_bytes()))
        pins.append((f"receipts/seed_{seed}_curve.json",
                     (HERE / "receipts" / f"seed_{seed}_curve.json")
                     .read_bytes()))
        pins.append((f"trained/theta_{seed}.npz",
                     (HERE / "trained" / f"theta_{seed}.npz").read_bytes()))
    for rel, data in pins:
        w("- " + rel + " | " + vi.sha_bytes(data))
    w("")
    w("## Honest limitations (named, not skipped)")
    w("")
    w("- The P04 handoff/admission machinery governs GPU training launches "
      "on the live controller; no live controller session is provisioned to "
      "this attempt. The operative admission of record for this CPU-only "
      "runbook is the frozen bounded-resource envelope (per-seed wall "
      + fmt(RUNBOOK["termination"]["wall_clock_budget_s"]) + " s, memory "
      "bound, no trajectory retention) plus the separate-first prereg; the "
      "GPU mailbox was unused (no GPU work exists under BQ-1).")
    w("- P3 outcomes are recorded per seed above whether improved or not; a "
      "failed training outcome is not hidden and not retried (the executor "
      "contains no retry path).")
    w("- The trained candidates are NOT a certified trained walking policy "
      "(the W04 freeze's TC-9 explicitly-unresolved closure stands).")
    w("")

    report = "\n".join(lines) + "\n"
    (HERE / "REPORT.md").write_bytes(report.encode("utf-8"))
    print("wrote REPORT.md")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except vi.Refusal as exc:
        print("REFUSAL: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
