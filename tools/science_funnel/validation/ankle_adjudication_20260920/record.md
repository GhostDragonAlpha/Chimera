# ANKLE-ADJUDICATION RECORD — Rule 0 membrane, written BEFORE any gathering

Lane `ankadj` (branch `lane/ankle-adjudication-20260920` @ a13a4d87, the k-fill close-out,
inherited tests 13/13 green at this head). Mission: adjudicate the ankle-specific fork the
k-fill lane named when F1 fired — derived ankle plantar capability 4.398653 N.m = 0.7434x the
Oku walk demand 5.9171 N.m, while the SAME derived force set COVERs knee (8.489511 / 5.3144 =
1.5975x) and MTP (1.163086 / 0.7051 = 1.6495x). Candidates, judged one against the other,
never blended: (A) ARCHITECTURE SIDE — the Guimaraes 2026 ankle PCSAs understate; (B) DEMAND
SIDE — the Oku walk peak is context-shifted for our animal; (C) ARM SIDE — the deposit's
measured ankle moment arms misrepresent the arms the datasets assume.

This file and `receipt.json` were written BEFORE the first web gather and BEFORE the
adjudication table script ran. Every prediction below is hand-derived from banked, sha-pinned
bytes (k_fill_book.json, the pennation annotation, the ankle arms book, the Oku snapshots) —
the only new computation this lane adds is bookkeeping arithmetic on already-committed numbers
plus cited literature context.

## RULE 0

**STATEMENT.** The ankle-specific inconsistency has a decidable cause among A/B/C: the gathered
evidence (per-muscle force ratios; the cited physiological specific-tension range; Oku's
experimental context; Guimaraes' ankle-vs-knee PCSA methodology) can name the side, or it
cannot and the honest verdict is UNDECIDED with the measurement that would decide it.
Someone could disagree three ways: (a) the per-muscle shortfall may be uniform (a scale/
constant problem) rather than concentrated (specific rows); (b) the literature specific-tension
range may honestly contain the sigma that would close the gap, making sigma non-discriminating;
(c) no literature or methods evidence may reach the ankle rows at all. All three disagreements
are answered with numbers, or with the explicit word UNDECIDED.

**PREDICTION (pre-named, before any gather).** B (context-shifted demand) is the most likely
primary cause, for two reasons visible in banked bytes before this lane computed anything:
(1) knee and MTP cover on the same force set, so no global constant (sigma, units, pennation
law) can be the cause — a constant error moves all joints together; (2) the demand and the
capability belong to different animals: the Oku peaks are measurements of a 10.038 kg model
animal, the derived capability is an absolute quantity (8 kg specimen PCSAs x 0.30 MPa on the
deposit's own measured arms) carried by the game's 6.15 kg mass-set animal, and the k-lane's
D5 consumes the raw demand without mass context. The mass arithmetic, hand-derived NOW:
5.9171 N.m / 10.038 kg = 0.58947 N.m/kg; at the band midpoint 6.15 kg the linear mass-scaled
demand is 3.62522 N.m (coverage 4.398653 / 3.62522 = 1.2134x COVERED); at geometric similarity
(torque ~ M^(4/3)) it is 5.9171 x (6.15/10.038)^(4/3) = 2.9478 N.m (coverage 1.4919x COVERED).
The prediction: B, with the secondary, independently recorded finding that the shortfall is
CONCENTRATED, not uniform — specifically that the SOL row (derived 36.8507 N vs Oku peak
214.99 N = 0.1714x) is the outlier while GAS matches (MG+LG 130.7047 N vs Oku 125.8 N =
1.0390x); predicted per-muscle spread (max/min among shared muscles) >= 2x.

**FALSIFIERS (named before the run).**
- **F1 NO-DECISION** — if the gathered evidence cannot discriminate, the verdict is UNDECIDED
  plus the named measurement that would decide it (a second measured-force study, or cadaver
  PCSA by dissection). An honest undecidable is a valid result; a forced verdict is not.
- **F2 SWEEP-BAN** — any tuning of sigma, PCSA, or pennation to close the 0.7434x gap FIRES
  this lane. Constants move only with new citations, and never to fit demand. Reporting the
  mass context of a demand is comparison, not tuning; no number that any book consumes moves.
- **F3 TRACEABILITY** — every number in the verdict is sha-pinned to a committed artifact or
  cited to literature with DOI/PMCID. Zero uncited constants.
- **F4 DETERMINISM** — the adjudication-table script runs 3 times, deliverable byte-identical,
  sha256 recorded in the receipt's measured block.
- **F5 SCOPE** — no source changes outside
  `tools/science_funnel/validation/ankle_adjudication_20260920/`
  (unittest-asserted via `git status --porcelain`).

## DECISIONS (openly recorded, before gathering)

**D1 — THE DISCRIMINATING TABLE.** Per-muscle derived force (k-fill book's derived force set =
pennation annotation at sigma 0.30 MPa) vs Oku walk per-muscle peak AND mean
(`hind_torque_book_20260921/inputs/derived_numbers.snapshot.json` oku_muscle_forces_N, both the
"before" and "after" variants reported). Shared ankle classes only (SOL, GAS=MG+LG, FDL, TA,
EDL); PL/PB/FHL/EHL have no Oku counterpart and are reported as such, never interpolated.
Concentration metric: spread = max(ratio)/min(ratio) over the shared plantar classes.
Predicted >= 2x; a uniform reading (< 1.5x) would instead implicate a global constant.

**D2 — THE SIGMA QUESTION, HONESTLY.** Gather the cited literature range for mammalian skeletal
muscle specific tension; report the range with citations. Closing the ankle gap needs sigma =
(5.9171 / 4.398653) x 0.30 MPa = 0.403542 MPa. If and only if the cited range honestly contains
0.404 MPa, sigma is declared NON-DISCRIMINATING and the verdict says so. The value 0.404 MPa is
NEVER adopted anywhere; it appears only as this diagnostic.

**D3 — THE OKU CONTEXT TABLE.** Subject mass, speed, grade, duty, and the ankle peak's phase,
from the pinned `oku2021.xml` (already consumed by the deposit_mass lane) plus the banked
snapshot numbers (GRF_v peak 1.0823 xBW at 3% of cycle, duty factor 0.6832, ankle plantar peak
at 25.0% of the cycle = 36.6% of stance, Froude 0.27, timing speed ~1.01 m/s at 10.038 kg).
Compared to our 6.15 kg band midpoint (Turnquist & Kessler 1989 band 5.4-6.9 kg via the
committed k_forensics receipt). Phase evidence is SUPPORTING only.

**D4 — THE GUIMARAES METHODS QUESTION.** How PCSA was computed for ankle vs knee rows in the
same paper (pinned full text, sha a1ded31f..., per the k receipt's F3 block; its PMC open
version may be read but the pinned bytes are the citation of record). Predicted BEFORE the
gather: the method is uniform across the hind limb (the repo's closure law PCSA = musc_mass /
(1060 kg/m^3 x FL) already reproduces the SOL row exactly: 0.01254 / (1060 x 0.0953) =
1.2408e-4 m^2 vs the sheet 1.24136e-4), so NO ankle-specific methodological asymmetry exists;
any asymmetry found FIRES this prediction and supports (A).

**D5 — THE ARM DOOR CLOSES (OR NOT) ON BANKED ARITHMETIC.** The ankle arms book already banks
the decisive test: at Oku's OWN walk forces the measured deposit arms reproduce the Oku demand
(V1_S1 cap 6.247077 vs 5.9171 = 1.0558x; the no-FDL-reuse triceps-only sub-envelope 5.318868 =
0.8989x). If those banked numbers stand, (C) cannot explain a 1.345x shortfall: the arms that
carry Oku's own forces to within 5.6% of Oku's own torque are not the wrong arms. This lane
does not recompute the arms; it consumes the banked envelope.

**D6 — CONSEQUENCE, NOT EDIT.** The verdict paragraph names what the engine's force-set choice
should consume (which side of the divergence it stands on, per the k-lane's own closing line)
WITHOUT touching `gait_controller.hpp`, any `gait_*` validation, `first_skill_prestage_20260922/`,
master, or shared tooling. The engine's mass-context reading (game animal 6.15 kg vs the
demand's 10.038 kg source animal) is REPORTED; the D5 raw-demand consumption of the k-lane is
not changed by this lane.

## INTERPRETATION MATRIX (pre-registered)

- Concentrated (P1 spread >= 2) + arms reproduce demand (D5 banked) + methods uniform (D4
  predicted) + sigma range does NOT contain 0.404 (D2): verdict leans B for the magnitude with
  the architecture-side SOL-row conflict recorded as a named secondary (an A-flavor datum, not
  the primary cause).
- Uniform (< 1.5x) + sigma range contains 0.404: sigma non-discriminating; verdict leans B
  (context) but the record says the two constant candidates cannot be told apart — UNDECIDED
  between B-as-context and A-as-constant unless the context table separates them.
- No literature reaches the ankle rows and methods are unreadable: UNDECIDED + the named
  measurement (F1).
