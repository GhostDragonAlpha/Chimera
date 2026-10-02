"""Standing capture-gate template for campaign cards (capture-gate-template v1).

Future cards IMPORT this package into their capture scripts and call
``pipeline.run_pipeline`` from run_all; the object-ID/co-location gate is part
of the normal pipeline (prereg -> capture -> GATE -> receipts -> review
export), not an optional add-on:

- prereg.py: card prereg binding; the view-spec hash is pinned BEFORE capture
  and any mismatch refuses the run pre-render;
- sidecar.py: sidecar mask-buffer capture; per-object ID constants come from
  the card's view-spec; channel isolation is audited at capture time;
- palette_stage.py: stage-0 blank-frame detector + totals smoke census (the
  U07 palette-gate law, kept at its proven strength);
- mask_gate.py / view_spec.py / png_writer.py / review_export.py /
  synthetic_renderer.py: the reviewed VISUAL-GATE-1 modules, copied
  byte-identical from sealed package
  03a95c39cd7d4e80993eeec5875ce8c5 (visual-gate lane);
- pipeline.py: the mandatory two-stage gate call, chained canonical
  receipts, exception receipt rows, review-export hook and exit-code law.

Scope note: this template is a standing pattern for card-owned capture
scripts. It does not qualify any live capture, does not retroactively re-gate
cards accepted before it existed (U07 keeps its palette-gate record), and
touches no engine/renderer file in the source checkout.
"""
