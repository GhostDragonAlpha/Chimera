# ANKLE-ADJUDICATION VERDICT (measured block — appended after the gathers; the prereg above/`record.md` is unedited)

Lane `ankadj` @ lane/ankle-adjudication-20260920, prereg commit 19030212.
Deliverable: `adjudication_table.json` sha256 b501216ebd5f7ccd9a35c18fcc0934afd9b388681de1730dc9f800b20e19d053
(3 independent derivations byte-identical; `test_ankle_adjudication.py` 12/12 green).

## THE VERDICT: **B — DEMAND SIDE**, with two named qualifications

The ankle-specific inconsistency (plantar 4.398653 / 5.9171 = 0.7434x while knee 1.5975x and
MTP 1.6495x cover on the SAME derived set) is caused by the DEMAND side: what the k-fill lane
consumes as "the Oku walk demand" is not a measured steady-walk value of an animal like ours —
it is the **transient peak of a forward-dynamic simulation of a 10.038 kg modeled macaque**,
consumed raw (k-fill D5) against a capability that rides the game's 6.15 kg animal.

### The discriminating numbers

**Per-muscle table (derived force vs Oku walk forces; primary ratio = vs Oku "before" peak):**

| muscle | derived N (sigma 0.30 MPa x PCSA x cos(pennation)) | Oku before peak/mean N | ratio vs peak | ratio vs mean | reading |
|---|---|---|---|---|---|
| SOL | 36.8507 | 214.99 / 93.05 | **0.1714** | 0.3960 | THE OUTLIER (5.83x conflict) |
| GAS (MG+LG) | 130.7047 | 125.8 / 59.7 | **1.0390** | 2.1894 | MATCH — architecture covers GAS |
| FDL whole (as consumed) | 138.0639 | 204.57 / 86.21 | 0.6749 | 1.6015 | deferred whole, uncorrected by declaration |
| FDL whole (law-corrected, cos 21.4) | 128.5452 | 204.57 / 86.21 | 0.6284 | 1.4911 | the law-consistent value of the same row |
| TA | 21.5860 | 63.87 / 19.66 | 0.3380 | 1.0980 | second outlier (dorsal side) |
| EDL whole (as consumed) | 11.49 | 24.2 / 3.31 | 0.4748 | 3.4713 | deferred whole, uncorrected by declaration |
| PL / PB / FHL / EHL | 146.5842 / 57.1647 / 29.9961 / 24.1186 | — (no Oku counterpart) | — | — | Oku's 2D model has no such muscles |

Concentration metric (pre-registered, threshold 2x): plantar spread max/min = **6.06x** — the
shortfall is **CONCENTRATED, not uniform** (SOL row 0.1714x while GAS row 1.0390x; class-matched
triceps force ratio 0.4917). P1 HELD. A uniform shortfall would have indicted the global
constants; a concentrated one cannot, and knee/MTP cover confirms no global constant is wrong.

**Sigma is NON-DISCRIMINATING (declared per the pre-registered D2 rule).** Closing the ankle
plantar gap needs sigma = 0.30 x 1.345207 = **0.403562 MPa = 40.36 N/cm2** — a diagnostic, never
adopted. The cited literature range honestly contains it: Persad, Wang, Pino, Binder-Markey,
Kaufman & Lieber (2024), "Specific tension of human muscle in vivo: a systematic review", J Appl
Physiol 137(4):945-962, DOI 10.1152/japplphysiol.00296.2024, PMCID PMC11486478 — traditional
accepted mammalian value 22.5 N/cm2; reported human in vivo span **1.8-72.7 N/cm2** (30 studies,
96 values); recommended weighted median 26.8 N/cm2 (IQR 20-43). 40.36 sits inside the span and
the IQR, above the traditional and recommended points. So sigma alone cannot tell A from B — the
pre-registered D2 rule fires, and the verdict says so. No constant moved.

**The Oku context (D3, from the pinned oku2021.xml + banked snapshot).** Oku, Ide & Ogihara
(2021), "Forward dynamic simulation of Japanese macaque bipedal locomotion demonstrates better
energetic economy in a virtualised plantigrade posture", Communications Biology 4:1831,
DOI 10.1038/s42003-021-01831-w, PMCID PMC7940622: a **2D nine-link neuromusculoskeletal model
simulation**, not an animal measurement. The model animal is 10.038 kg (HAT 8.184 + 2 x 0.927);
the walk is level, moderate (Froude 0.27; GRF_v peak 1.0823 xBW at 3% of cycle; duty 0.6832;
speed 1.01 m/s simulated); the ankle plantar peak 5.9171 N.m lands at **25.0% of the cycle =
36.6% of stance**; muscle forces are validated against EMG activation PATTERNS of five hindlimb
muscles — not against measured tendon forces. Consequences for the pre-named flavors of B:
speed/grade flavor **DEAD** (level, moderate walk); subjects/mass flavor **HELD** (10.038 kg
modeled animal vs our 6.15 kg animal — mass ratio 1.632); peak-flavor **HELD** (simulation
transient peak, not a measured steady value). Mass context alone flips the coverage:
scaled to the game animal's own mass the demand is 3.625241 N.m (linear) → **1.2133x COVERED**,
or 3.079022 N.m (geometric, torque ~ M^(4/3)) → **1.4286x COVERED**, with knee (3.07x) and MTP
(3.17x) also covered — the ankle-specificity dissolves with the context. (Reported comparison
only; the k-fill D5 raw-demand consumption is not changed by this lane.)

**The arm door closes (C EXCLUDED, on banked arithmetic, prereg D5).** At Oku's OWN walk forces,
the measured deposit arms reproduce Oku's own ankle peak: V1_S1 cap 6.247077 N.m = 1.0558x the
demand; the no-FDL-reuse triceps-only sub-envelope 5.318868 N.m = 0.8989x. The arms that carry
Oku's forces to within 5.6% of Oku's own torque cannot be the cause of a 1.345x shortfall.

**The Guimaraes methods door (D4 prediction HELD).** The pinned full text
(PMC13425262_fulltext.xml, sha a1ded31fa6d615b4b1dabc91bec824c2b05b90ad37fbbcf709480027b3eb9d40)
uses ONE uniform protocol for every hind limb muscle — fresh-frozen dissection, single observer,
caliper FL (+/-0.01 mm, ~10 sites averaged), protractor pennation, and one PCSA equation
(PCSA = cos(theta) x belly_mass / (1060 kg/m3 x FL), Mendez & Keys 1960 via Zajac 1989). **No
ankle-vs-knee methodological asymmetry exists**; hypothesis (A) as "method asymmetry" is
refuted. Two side observations, recorded for honesty: the published sheet PCSA column is
pennation-uncorrected against the paper's own equation (already handled uniformly by the
pennation-correction lane, decisive bucket 17-0), and the PB/PL rows carry no measured pennation
(factor 1.0), so those two derived forces are slightly OVERstated — the ankle shortfall is
slightly WORSE than 0.7434x under the exact law, not better.

**The A-flavor secondary (named, not decided).** The conflict CONCENTRATES at the SOL row:
Oku's simulation requires a SOL capability 5.83x the measured Guimaraes SOL (PCSA 124.136 mm2,
single M. mulatta specimen, id 127, 8.0 kg adult male, KU Leuven), while the GAS row matches
(1.0390x). This is a real dataset conflict between a measured dissection and a simulation's
force requirement — which side yields cannot be decided from these two datasets alone; it is
recorded as the named measurement for the next lane (below).

## PREREG OUTCOMES (F5 ledger)

- **P1 concentration (>= 2x spread): HELD** — measured 6.06x.
- **P-prediction B primary: HELD** (with the two flavors above).
- **D4 methods-uniform prediction: HELD** (no asymmetry found).
- **D2 rule: EXECUTED as pre-registered** — containment found, sigma declared NON-DISCRIMINATING.
- **FIRED and recorded (never absorbed): a preregistration hand-arithmetic slip** — prereg D2
  wrote the gap-closing diagnostic as 0.403542 MPa; the exact value is 0.30 x 1.345207 =
  **0.403562 MPa** (the prereg's hand division was off by 2e-5 MPa; the law itself is exact).
  The prereg text is unedited; this record is the correction. Same class of slip as the k-lane's
  P7 record.
- **F1 (NO-DECISION): NOT fired** — the evidence reached a verdict.
- **F2 (SWEEP-BAN): HELD** — sigma stays 0.30 MPa (cited); no PCSA, pennation, mass, or arm
  moved; the diagnostic sigma and the mass-scaled demands appear as REPORTED context only.
- **F3 (TRACEABILITY): HELD** — every number traces to a sha-pinned artifact (5 pins, load
  refuses on drift) or to the cited Persad 2024 / Oku 2021 / Guimaraes 2026 literature.
- **F4 (DETERMINISM): HELD** — 3 independent derivations byte-identical
  (sha256 b501216ebd5f7ccd9a35c18fcc0934afd9b388681de1730dc9f800b20e19d053), unittest-asserted.
- **F5 (SCOPE): HELD** — git status names nothing outside
  `tools/science_funnel/validation/ankle_adjudication_20260920/` (unittest-asserted).

## CONSEQUENCE FOR THE ENGINE'S FORCE-SET CHOICE (D6 — names the choice, edits nothing)

The derived force set itself is NOT invalidated and nothing in it moves: knee 1.60x and MTP
1.65x cover, and the ankle's 0.7434x is now EXPLAINED, not tuned. What the engine wave must
name, per the k-lane's own closing line:

1. **Under the k-fill D5 consumption (raw simulated 10.038 kg-animal peaks as demands, the
   conservative reading):** the ankle plantar class is under-covered 0.7434x and the 7/7
   stance-hold plantar nodes stay over-cap. The honest reading of that number is now on record:
   the derived set cannot lift the measured-class walk of a 1.63x-heavier simulated animal —
   it is not a defect of the architecture, the sigma, the pennation law, or the arms.
2. **Under a demand-mass-context reading (the game animal's own 6.15 kg):** the same walk
   scales to 3.625 N.m (linear) or 3.079 N.m (geometric) and the derived set covers at
   1.21x-1.43x, with margin thinner than knee/MTP. Choosing this reading is an operator
   decision about what the game's demand envelope IS; this lane tuned nothing to make it look
   attractive.
3. **The named measurement that would settle the SOL row** (the A-flavor secondary): a second
   macaque (or cadaver) muscle-architecture study of triceps surae — SOL PCSA by dissection,
   n>1 — against Guimaraes' 124.136 mm2 single-specimen row. If a second study corroborates
   ~124 mm2, the Oku simulation's SOL force-sharing is model-side and the secondary closes in
   favor of the architecture; if it corroborates Oku's implied ~700+ mm2, hypothesis (A)
   upgrades to the primary.

Tests: `python -B -m unittest tools.science_funnel.validation.ankle_adjudication_20260920.test_ankle_adjudication`
— 12/12 green (pins, determinism x3, scope, sigma non-adoption, concentration, arm door,
verdict inputs, mass arithmetic, Oku context identity, inherited quarantine integrity).
