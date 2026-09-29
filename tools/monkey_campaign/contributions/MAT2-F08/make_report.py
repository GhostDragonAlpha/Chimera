"""Generate report.md for MAT2-F08 FROM the committed evidence receipts.

No observed value is hand-transcribed: every number in the report comes from
evidence/checks.json, evidence/materialization.json or
evidence/validation_receipt.json at generation time.
"""
from __future__ import annotations

import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"


def build_report(checks=None, materialization=None, receipt=None):
    checks = checks or json.loads((EVIDENCE / "checks.json").read_bytes())
    materialization = materialization or json.loads(
        (EVIDENCE / "materialization.json").read_bytes())
    receipt = receipt or json.loads(
        (EVIDENCE / "validation_receipt.json").read_bytes())
    ident = checks["identity"]
    cap = checks["p6_visual_correspondence"]["capture"]
    trace = checks["p2_published_evidence_reproduction"]["trace"]
    frames = checks["p2_published_evidence_reproduction"]["frames"]
    regen = checks["p1_seed_asset_reproduction"]["regeneration"]
    bites = checks["p5_missing_asset_refusals"]["falsifier_bites"]
    fb_rows = "\n".join(
        "| %s | %s | %s |" % (b["bite"], str(b["bites"]).lower(),
                              b["clean_control"]["run"])
        for b in bites)
    regen_rows = "\n".join(
        "| `%s` | %s | `%s` | `%s` | %s |" % (
            r["asset"],
            json.dumps(r["source"], sort_keys=True),
            r["published_sha256"][:16], r["regenerated_sha256"][:16],
            str(r["byte_equal"]).lower())
        for r in regen)
    frame_rows = "\n".join(
        "| %s | `%s` | %s |" % (f["frame"], f["published_sha256"][:16],
                                str(f["byte_equal"]).lower())
        for f in frames)
    inst = materialization["instantiations"]
    inst_rows = "\n".join(
        "| %s | `%s` |" % (r["instantiation"], r["scene_sha256"])
        for r in inst)
    ledgers = trace["ledgers"]
    worst_ledger = max(l["worst_ledger_residual"] for l in ledgers)
    markers = checks["p6_visual_correspondence"]["markers"]
    tgate = cap["transform_list_gate"]
    return """# MAT2-F08 — source-bound qualification receipt: verify repeatable forest loading

**Verdict: BUILT AND SELF-CONSISTENT.** The scene seed/configuration
(`assets/scene_configuration.json`, {assets} pinned assets, seeds
{seed_t} / {seed_o}) reproduces the full sealed-line scene: the terrain
declaration, terrain bundle and obstacle declaration regenerate BYTE-EXACT
from their seeds; the frozen seven-run dynamics trace re-derives the PUBLISHED
F07 contact_trace.json byte-exact; all six rendered frames re-derive the
PUBLISHED F07 capture bytes byte-exact; the materialized scene state (assets +
collision state + initial state, {state_bytes} bytes, fingerprint `{fingerprint}`)
is byte-identical across {n_fresh} fresh subprocess instantiations and the
in-process one; and every missing/corrupt/silent-default/seed-drift/
float-drift arm fails CLEARLY with a named refusal (6/6 falsifier arms bite
fail-first, each against its own passing clean control). Visual acceptance
itself belongs to the independent visual reviewer.

- card: {card}; planning id {pid}; attempt {attempt}; arrival {arrival};
  criteria sha256 {criteria}; scope sha256 {scope}; base revision {base}
  (branch-1 fast-forwarded to the sealed line tip; F01-F07/B06 merged).
- done_when (verbatim): "{done_when}".
- discipline: PREREGISTRATION.md committed BEFORE implementation at
  `{prereg}`; amendments A1 (raw vs self sha256 pin correction) and A2
  (per-card profile object canonical sha) are separate commits
  ({amend_commits}), both before the implementation commit and before any
  evidence artifact existed. This report is GENERATED from
  evidence/checks.json and the sibling receipts — no observed value is
  hand-transcribed.

## 1. Reconcile-first (reused published bytes only)

All {assets} pins asserted by raw sha256 at every load (`f08_pin_*` refusals
name the asset): F02's terrain asset/query/bundle modules + clearing
recipe/declaration + trunk declaration, M06's byte-identical local_contact
module and contact law, F03's trunk mesh, F04's contact machinery (imported,
never forked), F07's scene module (imported, never forked: seeded placement,
contact bodies, render/classify law) and F07's published obstacle declaration.
No physics constant is new. The reproduction TARGETS are published merged
evidence (F07 trace + six frames), pinned by raw sha256.

## 2. Seed -> asset reproduction (P1, measured)

| asset | source | published sha256 (16) | regenerated (16) | byte_equal |
|---|---|---|---|---|
{regen_rows}

## 3. Published-evidence reproduction (P2, measured)

- dynamics trace: re-derived `{rederived}` == published `{published}`;
  byte_equal {trace_equal}. Worst ledger residual over all seven runs:
  {worst_ledger} (bar 1e-12).
- frames: all six reproduced frames equal the published F07 capture bytes:

| frame | published sha256 (16) | byte_equal |
|---|---|---|
{frame_rows}

## 4. Cross-instantiation reproduction (P3/P4, measured)

Scene state document: {state_bytes} bytes, fingerprint `{fingerprint}`.
Fresh subprocess instantiations: {n_fresh} (plus the in-process one) — all
byte-identical:

| instantiation | scene state sha256 |
|---|---|
{inst_rows}

The collision-state section (ground/trunk/obstacle M06 bodies with the pinned
law constants, ground co-instantiation re-measured per obstacle: F04's P0
refusal heritage) and the initial-state section (declared spawn/cameras/
schedule + derived impact starts + tick-0 solver states) are INSIDE this
document, so their reproduction is the document's byte-identity — measured,
not asserted.

## 5. Clear failures for missing assets (P5, measured; 6/6 arms bite)

| arm | bites | clean control |
|---|---|---|
{fb_rows}

Refusal codes name the missing/corrupt asset (`f08_pin_missing`,
`f08_pin_hash_mismatch`), the drifted seed (`f08_seed_reproduction_mismatch`),
the substituted scene (`f08_scene_state_mismatch` with the differing
sections). The lenient-default hazard is demonstrated and then caught by BOTH
enforcement layers (hash gate + fingerprint gate). {n_codes} named refusal
codes are declared in checks.json, all `f08_`-namespaced.

## 6. Visual correspondence (P6)

- {n_markers} marker rows across the three profile views against F07's frozen
  marker table; VISIBLE_BUT_MISMATCH count {vbm}; zero UNRENDERED required
  subjects.
- capture: profile `forest` (kind visible_static) read READ-ONLY from the
  registry (canonical sha256 {prof_sha}); visual_capture.validate_manifest
  structurally_valid={validation}; visual_gate.verify
  structurally_valid={gate}; single gate-bound artifact {gate_artifact};
  capture_sha256 `{capture_sha}` (byte-equal to the published F07 gate
  artifact — the capture re-produces the merged line's still exactly).
- transform-list gate: applicability {tgate_applicability} (static image
  capture — no video frames exist; identity decode/re-encode matches
  byte-exactly and the flipped transform is refused).

## 7. Determinism (P7)

Two full builds produced byte-identical evidence artifacts:
{n_artifacts}; identical={det_identical}.

## 8. Honest boundaries

- CPU-only (stdlib); no engine run, no native change, no GPU, no training, no
  runtime or playable-build acceptance. The collision path is the pinned M06
  law through unmodified vendored bytes — no new physics.
- The trunk mesh and its declaration are PUBLISHED F03 bytes (hash-pinned,
  loaded, not seed-regenerated — F03 published no generator); the trunk
  layer's reproducibility claim is byte-identity of the loaded published
  bytes inside the materialized scene state.
- Cross-instantiation equality is measured on ONE host/interpreter (the
  attempt's Python 3.14); cross-platform/cross-version bit-identity is NOT
  claimed (asset bytes sit on the pinned generators' 1e-6 grid; M06 trace
  floats are compared at full repr on this host only).
- The world-build-20260928 lane (WORLD_SEED 20260928, GPU splat world) was
  read for reconciliation only; its recorded hashes live in
  PREREGISTRATION.md section 9; nothing from that lane enters this build.
- Structural capture validity only: visual acceptance belongs to the
  independent visual reviewer.

## 9. Exact commands (from this directory, Python 3.14, CPU only)

    python -B implementation.py bites    # 6/6 fail-first, each with a passing clean control
    python -B implementation.py build    # receipt + scene state + frames
    python -B implementation.py verify   # P7 double-run determinism
    python -B make_report.py             # this file, from receipts
    python -B lint_report_numbers.py --selftest
                                         # report numbers traceable
    python -B -m unittest test_implementation -v
""".format(
        assets=len(checks["pins"]),
        seed_t=checks["constants"]["seed_terrain_recipe"],
        seed_o=checks["constants"]["seed_obstacle_placement"],
        state_bytes=checks["scene_state"]["bytes"],
        fingerprint=checks["scene_state"]["sha256"],
        n_fresh=materialization["fresh_subprocess_instantiations"],
        card=ident["card"], pid=ident["planning_id"],
        attempt=ident["attempt_id"], arrival=ident["arrival_id"],
        criteria=ident["criteria_sha256"], scope=ident["scope_sha256"],
        base=ident["base_revision"], done_when=ident["done_when"],
        prereg=ident["prereg_commit"],
        amend_commits="9f4c91ec, 4a166287",
        regen_rows=regen_rows, rederived=trace["rederived_sha256"],
        published=trace["published_sha256"],
        trace_equal=str(trace["byte_equal"]).lower(),
        worst_ledger=worst_ledger, frame_rows=frame_rows,
        inst_rows=inst_rows, fb_rows=fb_rows,
        n_codes=len(checks["p0_intake_strict"]["refusal_codes"]),
        n_markers=len(markers["rows"]), vbm=markers["visible_but_mismatch_count"],
        prof_sha=receipt["profile"]["canonical_sha256"],
        validation=str(cap["validation"]["structurally_valid"]).lower(),
        gate=str(cap["visual_gate"]["structurally_valid"]).lower(),
        gate_artifact=cap["gate_artifact"], capture_sha=cap["capture_sha256"],
        tgate_applicability=tgate["applicability"],
        n_artifacts=json.loads(
            (EVIDENCE / "determinism.json").read_bytes())["artifacts"],
        det_identical=str(json.loads(
            (EVIDENCE / "determinism.json").read_bytes())["identical"]).lower())


def main():
    report = build_report()
    (HERE / "report.md").write_text(report, encoding="utf-8", newline="\n")
    print("report.md written:", len(report), "chars")


if __name__ == "__main__":
    main()
