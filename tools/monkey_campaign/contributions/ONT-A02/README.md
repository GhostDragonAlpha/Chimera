# ONT-A02 — radioulnar definition, independent evidence, B4 result, before/after radius mapping

Task: `ONT-A02`; attempt: `b4a2b12b8c854e55bc400c64a502c85c`; criteria SHA-256:
`ab47206c8bd41e3f9769f8f96489545c3335cf2183a76f88f6c010e3b3789cb1`.

This contribution presents all four `done_when` items with an independent,
pin-bound re-derivation (own code over byte-exact extracted inputs), the
required anatomy-profile visual capture, and a hash-bound qualification
receipt. It changes no production file, executes no supersession, and claims no
anatomical support for the re-anchor (R1's refutation is retained).

## Contents

- `PREREGISTRATION.md` — frozen statement, predictions/tolerances, falsifiers,
  probes and views (frozen before any new probe ran; sequence disclosed).
- `REPORT.md` — findings, the honest fired-prediction record, exact commands,
  counts and identities, bounds, submission state.
- `ota02_radioulnar.py` — task-owned numerical verifier (P1-P7): XML rest-pose
  walk, radioulnar identity + owner discrimination, closed-form before/after
  similarity maps (both sides), closure mechanism, C01 landmark/round-trip
  oracles, C16 coverage topology, R1 drift law + retained refutation.
- `ota02_render_views.py` — deterministic CPU z-buffer capture of the three
  declared views (diagnostic+clean pairs), bounds-guarded framing, state-hash
  preservation across view toggles, canonical validator at write time.
- `test_ota02_radioulnar.py` — 26 CPU tests incl. failing-first falsifier
  demos (clipped-subject guard, tampered hash/scale detection, wrong owners).
- `make_qualification_receipt.py` — builds the hash-bound qualification +
  independent-review receipts and enforces `visual_gate.verify` before writing.
- `reference/` — read-only extractions from git pins (`EXTRACTION.json` binds
  every file's bytes + sha256 to its pin); kept read-only after extraction.
- `evidence/` — `state_snapshot.json`, `numerical_receipt.json`,
  `capture_sheet.png`, `capture_manifest.json`, `capture_context.json`,
  `visual_provenance.json`, `qualification_receipt.json`,
  `independent_review_receipt.json`.

Run with `python -B` (CPU-only, deterministic, no network/GPU): the module, the
renderer, then the receipt builder; `python -B -m unittest
test_ota02_radioulnar` re-verifies everything (26 tests).
