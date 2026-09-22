# VANHOOF TRANSCRIPTION 20260920 — lane record (the scan-class vision day)

Lane: `lane/vanhoof-transcription-20260920` @ base `d374ab04` (the intake lane's tip,
"byte-stability verified"). Agent: `Agent: vtrans` — the vision-transcription lane.
RULE 0 prereg: `receipt.json` in this directory, written BEFORE any S2 pixel value
was read by any pass.

## The theory (Rule 0, stated before the build)

**STATEMENT** — the S2 macaque table (7 adult *M. mulatta*, Mm1-Mm7, two panels; mass g /
FL mm / PCSA mm2 per specimen) is transcribable by double-entry vision — two independent
full passes over overlapping named panel crops, different traversal order and different
read strategy, no cross-consultation — with law-verified admission at or above the
pre-registered stop floors (agreement >= 80% on legible cells, closure-law pass >= 90% on
checkable rows).

**PREDICTION** — exact-agreement 85-95% on CLEAR cells; the pcsa_closure law catches most
DISPUTED cells (one misread digit breaks closure by >= ~10% against a 2% inherited
tolerance); 10-20% of the table is genuinely unreadable at this paper-scan quality and
stays refused.

**FALSIFIER** — F1 stop-floor (either floor missed => STOP, report rates);
F2 no-guess (admitted cell without both-pass agreement + law verdict = fired);
F3 provenance (crop sha + panel + row/col identity + both pass values on every admitted
value); F4 determinism (reconcile + laws + crop pinning 3-run byte-identical — the
transcription is two human-class reads, the LAWS are the determinism);
F5 lane scope (lane dir + out-of-repo staging only; no image bytes in git).

## Why this lane exists

The intake lane (`vanhoof_intake_20260920`) measured the wall: the frozen born-digital
OCR route reaches 4.8% CONFIDENT on the CMYK paper scans (F-CAL STOP GATE FIRED), and
named its successor scope in `receipt.json -> real_run.successor_scope_named`:
scan-class route, 3-field manifest, S2-only, pcsa_closure (rho=1060) as the only runnable
row law, paper markers as named refusal classes. This lane executes the operator's-door
alternative that receipt names: the agent's own vision reads the table, honestly, twice,
and the laws — not the reader's confidence — decide admission.

## Discipline carried

- Both transcription passes written COMPLETELY to disk before any reconciliation;
  pass B produced without consulting pass A (pass A's file is sha-pinned first).
- MARKED-ABSENT source markers ("absent (cf. EDST)", "damaged", "not measured") are
  transcribed as named refusals, never numbers.
- No guessed cell anywhere. A cell that cannot be checked by law is refused, named.
- Count identity closes over the full 1512-cell grid: admitted + refused(weighted) = 1512.
- Constants inherited, not tuned: rho=1060 (adapters_muscle.MUSCLE_DENSITY_KG_M3),
  tolerance=0.02 (LAW_TOLERANCE), floors 0.80/0.90 (pre-registered in the prereg).
- Derived PNG tiles live OUTSIDE git at E:/ChimeraWork/vanhoof2-staging/ (re-derivable
  from the committed, sha-pinned TIFF + the committed prep script + declared constants);
  the lane dir holds scripts, crop pins (sha + geometry), transcriptions, receipts.

## Ledger (appended as measured)

- prereg written + committed BEFORE any transcription (this commit).
- prep: `prep_s2_panels.py` — panel bounds MEASURED CONSTANTS asserted against detected
  ruling lines; 12 overlapping tiles (2x LANCZOS) pinned in `crops_manifest.json`
  (sha256 + geometry), 3-run byte-identical. Tiles live out-of-git in
  `E:/ChimeraWork/vanhoof2-staging/s2_tiles/`.
- geometry corrected BEFORE keying values from affected bands: rows start at y=114 (P1)
  and y=1734 (P2), not at the first full-width lines below the headers. Established by
  three independent mechanical checks: muscle-column text-blob scan (labels vs bands),
  group-column fill boundary (white→gray at FDS), and 3x band crops. P1: header 14-114,
  39 rows APB..B (Mm1-Mm4). P2: header 1651-1734, 34 rows APB..APL, NO upper-arm group
  (Mm5-Mm7). True table = 774 value positions; the intake's 1512 was its coarse 54x28
  page-grid model — both counts reported, nothing forced.
- pass A (row-wise muscle-major, forward): 12/12 tiles, committed before pass B began.
- pass B (column-wise animal-major, REVERSE): 12/12 tiles, produced without consulting
  pass A. Independent correction found by pass B: Mm7's APB+FPB merged cell (1.0|10.4)
  — pass A had initially keyed 0.7|13.9 as FPB; corrected in pass A's file with note.
- reconcile: 774 cells classified: 654 TENTATIVE (numeric, both passes exact) +
  105 MARKER_AGREED (source's own text markers) + 15 BLANK_AGREED (merged-cell covered
  positions). Exact-agreement rate on legible numeric cells = 1.0 (floor 0.80 MET).
  Zero silent drops. Declared normalization rules (marker refusal classes; role ignored
  for valueless block-spanning marker cells) documented in the receipt.
- laws (`laws.py`, constants INHERITED not tuned — rho=1060, tol=0.02):
  **F1 STOP FLOOR FIRED**. pcsa_closure passes only 19/218 checkable rows (8.72% << 90%).
  Deviation percentiles p5/p50/p95 = 1.2%/3.8%/13.5% — the prereg's P-CLOSURE prediction
  (rounding-driven, median <1%) is MEASURED FALSE. Implied density median 1.1004 g/cm3
  (IQR 1.095-1.115): the authors computed PCSA with ~1.10 g/cm3 (and possibly per-row
  effects), not the funnel's 1060 kg/m3. Zero admission. Constants not moved.
- refusal taxonomy: marker_absent_cfr 42, marker_absent 45, marker_crossref_APB 6,
  marker_crossref_FDP 12, merged-covered 15; 654 numeric cells unadmitted under the F1
  stop (not refused as reads — refused as un-admittable under the preregistered law).
  Note: P2's conn row has a BLANK muscle-label cell in the source (blob-verified); its
  values are transcribed and identified by position.
- determinism: prep manifest, reconcile.py, laws.py, build_receipt.py each 3-run
  byte-identical (cmp-verified). Tests beyond determinism: not applicable — the two
  transcription passes are human-class reads; the scripts are pure functions of frozen
  inputs and their 3-run identity is the verification.
- falsifier verdicts in `receipt_final.json`: F1 FIRED (honored: STOP, zero admission),
  F2/F3/F5 HELD, F4 GREEN. Successor scope named: re-register the law at the source's
  own arithmetic (implied rho 1.1004 g/cm3 median + tolerance from the measured
  residual distribution, or per-row pennation) — the 654 TENTATIVE values from this
  lane are the ready input; no re-reading required.

