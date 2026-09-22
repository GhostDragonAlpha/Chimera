# K-FILL RECORD — Rule 0 membrane, written BEFORE any number of this lane

Lane `agent/k-fill-20260920` (branch `lane/k-fill-20260920` @ bd4bf630), the K-FILL mission:
promote the hind torque book's PROVISIONAL "PCSA x sigma" variants (5.46x/5.22x the doc caps)
to a DERIVED force set — every per-muscle PCSA cited, pennation-corrected per the
pennation_correction lane's math, ONE specific tension constant cited (never swept), segment
masses rescaled to the adult female band — and re-run the hind book at deposit scale. The
operator directive is settled: NO author email; the game derives its own numbers; the SI-scale
branch of every book is dead.

This file was written before this lane computed its first number. Everything below the
"DECISIONS" heading is a determination on already-committed artifacts; every prediction band in
`receipt.json` was derived by hand from those banked numbers, not from a run.

## RULE 0

**STATEMENT.** The published macaque muscle-architecture data already admitted by the funnel
(the Guimaraes sheet PCSAs, pennation-corrected per sigma-law/pennation-correction) suffice to
replace the deposit's placeholder 1 N muscle forces with a fully derived capability set: for
each hind class, cap = max over the MEASURED deposit-arm scan of sum F_m |r_m(q)| with F_m =
0.30 MPa x PCSA_m x cos(pennation_m), and the deposit's template junk masses can be rescaled to
the anatomical adult-female expectation by one derived factor. Someone could disagree three
ways: (a) the physiological-sigma set may not cover the measured walk (the provisional set's
walk consistency came from fitting sigma = 1.28091414 Pa to Oku's Fmax — a demand-side fit;
at the cited physiological sigma the same architecture may under-cover); (b) the rescaled mass
set may not land inside the anatomical expectation envelope; (c) the rear-up class the
operator authored may or may not be covered. All three disagreements are answered with
numbers, before the run, in `receipt.json`.

**PREDICTION.** The pre-registered prediction bands P1-P7 in `receipt.json` — derived by hand
from banked artifacts (the pennation-corrected forces are known bytes; the measured arm curves
are known bytes; the only new arithmetic is the envelope sums and the mass rescale). Headline
predictions: the derived ankle plantar capability lands BELOW the operator's F1 band
[5.0, 7.5] N.m (~4.4 N.m predicted) — F1 FIRES and the divergence is REPORTED, never tuned;
the derived knee capability ~8.5 N.m covers the measured walk knee peak 5.3144 N.m; the
rear-up class C* is NOT covered (max capability < 33.6 N.m on either definition).

**FALSIFIERS.** The operator's four, verbatim, plus lane bands:
- **F1** — derived ankle capability outside [5.0, 7.5] N.m -> the force set is wrong: REPORT
  the divergence with its numbers and its named cause; never tune inside the band.
- **F2** — determinism: 3 independent full derivations byte-identical; sha256 recorded in the
  receipt.
- **F3** — traceability: every number in the deliverable is sha-pinned to a committed artifact
  or cited to pinned literature; zero uncited constants.
- **F4** — no source changes outside `tools/science_funnel/validation/k_fill_20260920/`
  (unittest-asserted via `git status --porcelain`).
- **F5** — any prediction band above measured outside, or any band moved after the first run,
  is recorded as FIRED with its number; never absorbed, never re-written.

Any hit is measured and recorded. Nothing is tuned.

## DECISIONS (openly recorded, one number one reason, nothing swept)

**D1 — THE ONE SPECIFIC TENSION CONSTANT: sigma = 0.30 MPa = 30.0 N/cm^2.**
Cited to `LightEngine/kinematic/muscles.py:79` (ANATOMY-DATUM, sha-pinned by the pennation
lane's receipt), to the sigma-law lane's verdict ("RETAINED AS ASSUMED, NOT RETIRED BY
MEASUREMENT", the assumed point in the 23-32 N/cm^2 band), and to the pennation-correction
lane's law (`F_corrected_N = sigma * PCSA_m2 * 1e4 * cos(radians(pennation_deg))`). NOT swept.
The deposit record's 1.28091414 Pa is REJECTED as the capability sigma with a stated reason:
it is a least-squares fit of mass-adjusted Oku Fmax onto matched Guimaraes PCSA sums
(8 groups; muscle_path_geometry.snapshot hindlimb.specific_tension.method) — i.e. a
DEMAND-SIDE fit, circular for a capability set, and 4.27x above the physiological band.

**D2 — THE FORCE SET = the pennation-correction lane's admitted annotation.**
The 23 paired muscles' corrected forces, plus the declared carried terms (EDL whole 11.49 N,
FDL whole 138.0639 N, both UNCORRECTED-by-declaration; the 5 absent-admitted muscles
150.5691 N sum), consumed byte-exact from
`pennation_correction_20260921/macaque_assembly_force_annotated_pennation_corrected.json`
(sha-pinned). Every PCSA is therefore PUBLISHED MACAQUE (Macaca mulatta sheet of the
Guimaraes batch, xlsx sha 08ead4a9... pinned inside the annotation) and every pennation is the
sheet's measured value with factor 1.0 on the four declared absences (AM, GRA, PB, PL).
**Substitution policy, recorded in advance:** substitutions are lawful only for ABSENT rows;
QUARANTINED rows (R_RF, R_SAR, R_AB, R_BFS, R_TP carry
`exact_name_row_quarantined_at_admission`) stay NAMED GAPS — overriding the funnel's own
admission verdict with a homolog number would be a silent fill of a knowingly-conflicted
number. Consequence: the knee book stays vasti-only (RF gap, as the hind book's V2), the
plantar book carries no TP (as the ankle lane's V2). No needed class has an ABSENT row.

**D3 — THE MASS SET = the deposit's scale-free fractions rescaled to the cited anatomical
expectation.** Target sum = Oku 2021 Table 1 hindlimb-chain fraction (2 x 0.927 / 10.038,
byte-pinned `deposit_mass_20260921/literature/oku2021.xml`) x the adult-female band midpoint
6.15 kg (Turnquist & Kessler 1989 band 5.4-6.9 kg via the committed k-lane receipt; the
band-midpoint is the deposit_mass lane's own banked convention, not a new choice). Rescale:
every deposit segment mass x (target sum / 0.7717839 measured deposit sum). WHY the deposit's
fractions rather than a per-segment literature table: the model's dynamics need the deposit's
own mass DISTRIBUTION preserved (Oku's table has no pelvis counterpart, so per-segment
substitution would force an invented pelvis split); the literature enters where it is
strongest — the expected SUM. Declared honestly: the literature anchors exclude the pelvis
segment, so a pelvis-carrying set rescaled to a pelvis-exclusive anchor is the deposit-mass
lane's pre-registered conservative bound, inherited and named.

**D4 — THE REAR-UP CLASS IS OPERATOR-AUTHORED.** C* in (22.4, 33.6] N.m appears nowhere in
the repo (grepped); it is the mission's own demand class, numerically (2x, 3x] the live hip
cap 11.2125 (22.425 = 2 x 11.2125; 33.6 = 3 x 11.2125). It is consumed as GIVEN, not
re-derived. Max capability is pre-registered under two definitions: PRIMARY = max over the
derived books including the hip-extension context book (record straight-line arms — the
declared 25%-unknown arm class, named on the record); CONSERVATIVE = max over the three
measured-arm books only (knee, ankle, MTP). COVERED iff max capability > 33.6 N.m; the
conservative definition bounds the primary from below, so a NOT-COVERED under the primary is
robust.

**D5 — DEMANDS ARE NEVER RESCALED.** The Oku measured walk peaks and the wave-4 stance-hold
demands are measurements on real animals; the mass set changes what the game's animal WEIGHS,
not what the measured walk demanded. The stance-hold node table is re-priced by cap
denominators only (the measured_caps_statics lane's ratio law).

## CONSEQUENCE MAP (what this lane feeds)

The derived set is the game's own-number source: per-muscle cited forces, measured deposit
arms, derived masses — a complete adult-female physical model at deposit scale. The SI-scale
branch stays dead (the k-gate closure, banked separately in this directory). If F1 fires, the
report names the mutual inconsistency: the Oku walk's muscle forces are not reproducible from
published macaque architecture at physiological specific tension — both are published
measurements; the divergence is theirs, ours is only to refuse to paper over it.
