# VANHOOF LAW 20260920 — lane record (the law re-registration the VTRANS stop named)

Lane: `lane/vanhoof-law-20260920` @ base `f59bd873` (the transcription lane's tip,
"VTRANS lane close: F1 STOP FLOOR FIRED, zero admission"). Agent: `Agent: vlaw`.
RULE 0 prereg: `receipt.json` in this directory, written BEFORE any constant
derivation and BEFORE any law pass re-run.

## The theory (Rule 0, stated before the build)

**STATEMENT** — the source's own arithmetic constant is derivable (stated in the
paper, or measured from the source's own arithmetic by the landed estimator), and
the pcsa_closure law re-registered at that ONE constant (tolerance 0.02, floors
0.80/0.90, law form — all inherited, unchanged) passes >= 90% of the 218 checkable
rows.

**PREDICTION** — the paper states (or cites its density source for) rho ~=
1.10-1.112 g/cm3 (the standard primate muscle density of that literature); pass
rate at the registered constant lands 90-98%; the failing minority concentrates in
source-structured rows (merged muscles, marker-heavy rows), not uniformly.

**FALSIFIERS** — F1 LAW-STILL-FAILS (< 0.90 at the derived constant => STOP,
report residual structure as a source data-quality finding); F2 FIT-TO-PASS (any
constant chosen after seeing a pass rate at it, or any tolerance/floor change =>
fired; the evidence order — stated-cited first, measured-declared second — is
pre-committed); F3 NO-RETRANSCRIBE (any value differing from the landed 654
TENTATIVE cells => fired; value pin sha256 efbd3aefc6711e66b6461ea5b9af6abb646a99ed5aedd0b6d30945d9ca21f4b7
pinned in the prereg); F4 DETERMINISM (every lane script 3-run byte-identical);
F5 SCOPE (lane dir only; shared tooling, graph store, S1, gait_*, master: read-only
or untouched).

## Why this lane exists

The transcription lane (`vanhoof_transcription_20260920`) landed a perfect
double-entry transcription of the S2 macaque table — 654/654 exact agreement — and
then honored its own stop floor: at the funnel's inherited rho = 1060 kg/m3 the
pcsa_closure law passed only 19/218 checkable rows (8.72% << 90%), while the
measured IMPLIED density of the table itself is median 1.1004 g/cm3 (IQR
1.095-1.115). The source's own arithmetic differs from the funnel's constant. The
stop receipt named this successor scope: re-register the law at the source's
arithmetic, values ready, no re-reading. This lane executes exactly that, with the
constant derived by evidence (stated-cited preferred, measured-declared fallback)
and registered BEFORE the re-run — the registration, not the run, is the theory
under test.

## Discipline carried

- The ONE constant is re-derived; everything else (tolerance, floors, law form,
  deviation-class bands 0.02/0.10) is inherited or pre-named in the prereg.
- Successor option (b) from the stop receipt — tolerance sized from the measured
  residual distribution — is DECLINED: that is fit-to-pass by construction (Rule 1).
- The 654 TENTATIVE values are pins: consumed byte-exactly, never re-read from the
  TIFFs, never edited; a law-exposed suspect is named, never silently changed.
- admit_vanhoof.py (the prestage's 7-field machinery) is NOT modified and NOT
  forced onto the measured 3-field manifest — the intake's F-MANIFEST named branch;
  the manifest is registered honestly as a 3-field source.
- Marker refusals (absent / absent cf. / crossrefs) and merged-covered positions
  stay the source's named truth; no repair, no imputation anywhere.

## Ledger (appended as measured)

- prereg written + committed BEFORE any derivation (commit 038aebd8).
- constant derivation, route (a) STATED-CITED SUCCEEDED — the paper states its
  constant, explicitly, in Methods 2.3: "For both gibbons and macaques, the average
  muscle density is 0.0011 g/mm3 (SD <0.0001 g/mm3), which is almost equal to the
  density defined for human muscles (0.00106 g/mm3) (Ward and Lieber, 2005). ...
  Therefore, the density value of 0.0011 g/mm3 is used in the calculation of the
  PCSA for all muscles in this study." (PCSAmass / (FL x density), Eq. 1; density
  measured per Eq. 2, extrinsic muscles; pennation omitted by the authors' stated
  omission, cos 0-30 deg = 1-0.87; multi-belly PCSA = sum of bellies.) Registered
  constant: **rho = 1.1 g/cm3 = 1100 kg/m3** (0.0011 g/mm3 as printed). The
  funnel's inherited 1060 kg/m3 is the paper's CITED HUMAN constant (Ward & Lieber
  2005) — the funnel had registered the citation, not the paper's own used value.
  Cross-check: the landed measured implied median 1.1004 g/cm3 (IQR 1.095-1.115)
  sits at the stated 1.1 (0.04% off) — measurement corroborates the statement.
  Evidence in `constants.json` (two independent full-text reads; citation
  verified against the intake's sha-pinned front-matter XML; that XML is
  front-matter only and cannot carry the Methods statement). P-CONST measured
  true at the boundary of its predicted band (1.10 in 1.10-1.112). No pass rate
  was seen at this constant before registration (F2 order held).
- law re-run at the registered constant (`laws_registered.py` -> laws_registered.json,
  sha256 9d9a40cee863217286f60f2f49374651881fb8fedd9feb9d24b636ea816cf414, 3-run
  byte-identical): **F1 LAW-STILL-FAILS — FIRED**. Pass rate 146/218 = 66.97% << 90%
  floor (P-RATE's predicted 90-98% is MEASURED FALSE; reported, not tuned).
  What the constant DID fix: dev p50 0.88% (was 3.77% at the inherited 1060 — the
  median row now closes at the paper's stated arithmetic), p25 0.19%; 202/218 (92.7%)
  land within the 10% descriptive band. The residual structure is sharp and
  interpretable: **67 of 72 failing rows have mass < 2 g** — the small intrinsic hand
  muscles (APB, ODM, ADM, Anc, C5, LUMB, OPP, FPB, FDM...), exactly the muscles the
  paper itself says it could NOT volume-measure by submersion ("we calculated the
  muscle density only for the extrinsic muscles") — their printed 1-decimal mass
  register (±0.05 g on 0.1-2.0 g) cannot carry 2%-closure arithmetic. Only 5 large-mass
  rows fail (B 11.7 g, Bb 34.1 g, DET 8.6 g, ECU 4.6 g, CB 1.5 g — 4 of them Mm2
  upper-arm/shoulder rows, implied rho 0.87-1.07). Per-specimen: Mm2 16/35 and Mm7
  14/27 pass (the worst), Mm3/Mm4 27/34, 27/33 (the best). 15 rows pass at the
  inherited 1060 but not at 1.1 — implied rho 1.045-1.077, i.e. the funnel's constant
  was fitting the rounding tail of small muscles, not the source's arithmetic. Deviation
  classes (descriptive, prereg-declared): law_pass 146, moderate_register_unrounded 56,
  large_per_row_structure 16; named suspects (large band) listed individually with
  values + implied rho in laws_registered.json — the F3 pin holds, nothing changed.
- gate semantics note (transparency): the first draft of laws_registered.py (written
  pre-run) echoed the VTRANS lane's consequence string ("zero admission") in its
  gate field; the committed PREREG is the binding instrument and its
  admission_tiers_original dispose cells unconditionally (law-PASS rows ADMITTED,
  FAIL rows REFUSED row_closure_violation), while F1's pre-registered consequence is
  STOP-TUNING + report-structure. The gate string was corrected to prereg semantics
  AFTER the run; the change touches a report string only — no constant, floor,
  tolerance, tier, or verdict changed (measured numbers identical pre/post edit:
  146/218 = 0.6697).
- funnel admission (`admit_law.py` -> admission.json + records_vanhoof_s2.json,
  commit bae5ef0a, 3-run byte-identical): the prereg's admission_tiers_original
  executed — **438 cells ADMITTED** (the 146 law-PASS row-triples) as
  batch.property.measurement v1 drafts with full provenance (tiff sha + panel +
  both-pass crop shas + both-pass printed values + legibility + row_closure_law
  verdict); **336 cells refused, named**: 216 row_closure_violation (168
  moderate_register_unrounded / 48 large_per_row_structure), 105 source-marker
  cells (45 marker_absent, 42 marker_absent_cfr, 6 marker_crossref_APB,
  12 marker_crossref_FDP), 15 merged-covered. Count identity closes:
  **774 = 438 + 336, zero silent drops**. admit_vanhoof.admit not modified, not
  forced (7-field require vs the measured 3-field manifest — the intake's
  F-MANIFEST named branch); the manifest registered honestly (3-field source)
  in admission.json. Graph apply / controller admission NOT run from this lane
  (shared state; the funnel's proposal-not-claim mode is the honest ceiling);
  training_gate named not-applicable (it gates trainer targets, not batches).
- cross-specimen summary (`cross_specimen.py` -> cross_specimen_summary.json +
  .csv, 3-run byte-identical): 35 source muscle keys x 3 fields x {n, mean, min,
  max} across Mm1-Mm7, all 654 TENTATIVE cells summarized (admitted and refused
  alike — the extraction the forearm/hand books consume), law verdicts riding
  along as conditions. Highlights: FDP n=7 mass 30.43 g (16.3-42.9) FL 44.23 mm
  (38.1-54.2); FDS n=7 mass 11.13 g (6.8-14.0) FL 33.46 mm (25.5-48.3); Bb n=4
  (upper-arm group only in panel 1) mass 40.85 g (34.1-45.8) FL 85.4 mm
  (67.5-118.3); APB n=7 mass 0.87 g (0.4-1.4); conn. FDS-FDP n=3.
- lane tests: `test_lane.py` 9/9 OK (pins, constant consistency, law agreement,
  count identity, no-guess, provenance completeness, replay digest, mutation
  probe, summary closure).
- falsifier verdicts (receipt_final.json): **F1 FIRED** (66.97% << 90% — the
  headline statement is measured false, reported); F2/F3/F5 HELD; F4 GREEN;
  P-CONST true at band edge, P-RATE measured false, P-RESIDUAL true (structured,
  not uniform). Successor scope named: a print-register error model derived from
  the paper's own declared precision (analytic propagation — a new instrument,
  preregistered, never a widened tolerance), or consumption of the 438
  law-verified cells with their law-verdict conditions as-is. The constant may
  never again be chosen against a pass rate.

