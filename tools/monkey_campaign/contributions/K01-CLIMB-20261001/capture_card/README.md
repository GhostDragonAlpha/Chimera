# capture-gate-template v1

Standing capture/acceptance template for monkey-campaign cards. It wires the
VISUAL-GATE-1 object-ID / co-location gate INTO the normal card capture
pipeline: capture -> gate -> receipts is one flow, and the gate call is part
of it — a card's run_all cannot emit a pass without the gate having run.

Provenance: `capture_gate/mask_gate.py`, `view_spec.py`, `png_writer.py`,
`review_export.py`, `synthetic_renderer.py` are byte-identical copies of the
reviewed VISUAL-GATE-1 modules (sealed package
`03a95c39cd7d4e80993eeec5875ce8c5`, visual-gate lane, 7/7 planted defects,
sergeant visual PASS). `TEMPLATE_MANIFEST.json` pins every file by sha256;
a card package embeds this template verbatim and receipts cite the manifest.

## Who owns what

- CARD (each card lane) owns: its `view_spec.json` (per-object ID constants,
  palettes, frozen floors/thresholds, declared occlusions), its
  `card_prereg.json` (pins the view-spec hash BEFORE capture), its capture
  script (`render` callback producing the sidecar pair), and its case table.
- TEMPLATE owns: prereg binding, sidecar capture contract, the two-stage
  gate call, receipt chain, exception receipts, review-export hook, and the
  exit-code law. Cards import it; cards do not fork it.

## Card recipe

1. Author `view_spec.json` (schema `chimera.visualgate.view_spec.v1`): every
   object declares `mask_code` (its object-ID constant) and `beauty_palette`;
   view classes freeze per-object pixel floors, `co_location_min_ratio`,
   occluder floors, and any `expected_occluded` entries with machine
   justification (exception_class, law_ref, geometry_ref, census_required).
2. Compute the canonical prereg hash:
   `capture_gate.view_spec.spec_prereg_sha256(spec)` and pin it in
   `card_prereg.json` with `declared_before_run/declared_before_capture: true`.
   Register the prereg per campaign law BEFORE runs (a seal does not replace
   a required prereg commit).
3. Write the capture script: `render(view_class, frame_id, defect)` returns
   `(beauty, mask)` uint8 `(h, w, 3)`. The mask buffer is a SEPARATE object-ID
   channel, never composited into beauty. See `demo_card/render_card.py`.
4. Copy `demo_card/run_all.py` and replace its case table. run_all calls
   `capture_gate.pipeline.run_pipeline` per case; do not bypass it.
5. Evidence: declare `pipeline_receipt.json`, `gate_receipt.json`,
   `capture_manifest.json` (+ review files for exception frames) as runner
   keeps, and record their sha256 in the card's EVIDENCE file. Acceptance
   binds to receipts from this flow, not to isolated gate calls.

## Exit-code law (enforced by run_all)

- 0: every selected case's pipeline verdict is GREEN (after both gate
  stages; declared-occlusion exceptions count as GREEN with receipt rows).
- 1: REJECTED — the gate went RED on at least one frame. The run is failed
  evidence, not a harness error; keep the receipts.
- 2: REFUSED — prereg mismatch, invalid spec, or capture-contract violation,
  BEFORE rendering/gating. Never a pass.

## Pipeline laws baked in

- PREREG-BEFORE-CAPTURE: the spec hash pin is verified pre-render; threshold
  tampering refuses with `prereg_spec_hash_mismatch`.
- FREEZE: thresholds live only in the spec; the gate never adjusts them.
- TWO-STAGE GATE: stage-0 palette blank-check (the U07 law, retained) plus
  stage-1 mask co-location (floors, co-location, declared-code accounting,
  occlusion evidence). Stage-0 totals are smoke census and never decisive.
- CANNOT-PASS-WITHOUT-GATE: `assemble_pipeline_receipt` refuses
  (`GateNotRun`) without an actual gate receipt; run_all has no skip path.
- TAMPER-EVIDENT CHAIN: pipeline receipt pins sha256 of the on-disk
  `gate_receipt.json` and `capture_manifest.json`; `verify_pipeline_receipt`
  re-checks from disk.
- EXCEPTION RECEIPTS: declared occlusions pass only with census rows and are
  exported (deterministic crops + manifest) for an independent visual pass.

## Status (fact, 2026-10-01)

Integrated standing template delivered by VISUAL-GATE-2 (lane wk-visual-gate-int):
implemented + reviewed (VISUAL-GATE-1 pattern) + INTEGRATED here, demonstrated
end-to-end through this exact path. U07 was accepted with the palette stage-0
gate only and was NOT checked with the stronger mask co-location gate; no
retroactive re-gating of DONE cards without a Captain order. Production
enforcement begins with the next card capture from this template.
