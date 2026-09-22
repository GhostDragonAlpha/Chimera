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
