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

