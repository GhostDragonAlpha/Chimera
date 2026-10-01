# PREREG (DRAFT) — K-TIER CLIMB SENSITIVITY SCREENING

Lane: `E:/ChimeraWork/monkey-coordination/sensitivity/` (write scope). Worker: wk-sens.
Date drafted: 2026-10-01. Status: **DRAFT — not committed; not authorized to run.**
Gating: this file must be committed by the publication owner BEFORE the sweep runs;
the sweep binary refuses to execute unless the sha256 of the packaged byte-identical
copy equals the pin SHA handed back after commit (harness exit 4 otherwise).
Harness: `E:/ChimeraWork/monkey-coordination/sensitivity/harness/sensitivity_harness.py`
(mode `sweep --pin SHA`).

## 0. Identity and law

- Parent records: `climb-derivation/DERIVATION.md` (sha256
  7e21792c2d777265d02b77bf8ebc92306c7347f30778fe55e8808d9d92d4a865) and
  `climb-derivation/grasp-geometry/` (grasp_geometry.py e5614b31..., SGT review
  f09ba353...). G-tier store reports G01 e6d6c432..., G04 dfca5b55..., G06
  2e434319..., G07 34a4a095..., FRICTION_SOURCES 336118e9... (full hashes in
  `sensitivity/EVIDENCE.md` and pinned inside the harness).
- Law inherited: every sealed number is copied with its source; everything the
  sweep computes is **BAND-ARITHMETIC / DERIVED-PREDICTION screening on the
  sealed closed forms**, carries the derivation's **CONDITIONAL** label, and is
  NOT a sealed run result. No synthetic constant occupies an absent slot:
  measured mu, x_press, x_aperture, x_reach, x_com/x_inertia, pad compliance
  stay ABSENT. Screening ranges are declared envelopes, not measurements.
- Precondition (hard gate): the harness `verify` mode — the reproduction gate —
  must pass with 0 failures (exit 0) on the same interpreter (C:/Python314,
  CPython 3.14.3) before any sweep seal. A reproduction failure is a blocker,
  never approximated silently. First-gate discovery (preserved receipt, runner
  job `fae5cc1f46a14d39a37c746fb08a4042`, exit 3): two DERIVATION.md gap-1
  prose static-mu_crit quotes for band_mid/band_hi n=2 are the n=1 values
  (exact identity proven); the recorded `derivation_output.txt` and every
  G-tier sealed number reproduce exactly. The parent-prose discrepancy is
  carried as a DOCUMENTED RECORDS DISCREPANCY (owner: wk-climb-derive lane);
  it does not block the gate over recorded outputs and does not change any
  sweep model: the sweep uses the sealed closed forms, and its static verdict
  rows use the true threshold mu >= W/(n*(jn/DT)) exactly as the G01 law
  states it.

## 1. Parameter set and EXPLICIT ranges

| p | parameter | nominal (sealed/declared) | declared screening range / grid | basis and label |
|---|---|---|---|---|
| mu | static friction coefficient, volar-pad-on-bark interface | 0.6 (NAMED PLACEHOLDER, G04; FRICTION_SOURCES GAP) | 141 regular points 0.300 + 0.005*i, i=0..140 (the F-A falsifier band [0.3, 1.0]), plus 4 DERIVED anchor points {0.5470708910000001, 0.8206063365000001, 0.8399663223427114, 0.9114734545064815} -> 145 points, sorted, deduped | F-A band is the preregistered measured-mu falsifier band; anchors are the sealed critical-mu values (scene n=4 transfer, scene n=3 transfer, WRAP-2 pincer, scene n=3 static). BAND-ARITHMETIC. |
| n | support-channel count | 3 (G06 fixture pattern) | ordinal {1, 2, 3, 4, 5} | n=4 is the sealed DERIVED-PREDICTION extension; n=5 declared extrapolation; n=1 carried to show the never-closes boundary. |
| m | body mass reading | per reading: scene 10.037998 kg (certified line) and band {5.4, 6.15, 6.9} kg | 701 regular points (400+i)/100, i=0..700 (4.00..11.00 kg), plus scene anchor 10.037998 -> 702 points | The two sealed mass systems stay DISTINCT (lineage gap 9): each verdict row is evaluated at its own reading's mass; no averaging, no reconciliation. |
| jn | per-channel press (limb force ceiling proxy, x_press) | 0.3 N*s/tick (F03 S1 declared operating point; press normal jn/DT = 60.0 N) | 91 regular points (150+5i)/1000, i=0..90 (0.150..0.600 N*s/tick = 30..120 N normal) | Declared fixture input, NOT an actuator qualification; the axis screens what the corridor NEEDS (jn_crit) against the W04 cap table context (caps listed, no N*m->N derivation exists). |
| s | fingertip span / achievable aperture proxy (WRAP-2) | 0.056663099802559125 m (A09/G01 recorded span; no reconfiguration below it) | SPAN + 0.0005*i, i=0..46 (all <= 0.0796631 m), plus 0.080 -> 48 points | Upper end covers the recorded PINCH palm-opposed distances (0.0783-0.0836 m) and the full diameter 0.074; screen of x_aperture, which is ABSENT. |

Held fixed (declared, with reasons):
- mu_k = 0.4 (placeholder): the closed-form verdicts depend on mu_s only; slip
  dynamics are out of scope for this harness.
- Hand-mass block (0.049 kg anatomical hand; m_eff 0.048761970806378674 kg;
  impulse ratio ~1/205): a CONSTANT CONDITIONAL flag on every scene-line row —
  structural, not screenable by any ranged parameter here.
- Pad stiffness/compliance: **OUT OF SCOPE for this sweep.** The sealed stage
  B/C closed forms contain no compliance parameter; the only compliance-linked
  sealed numbers are the G07 hold account (creep 1.2266e-4 m/tick at the
  operating point) and AMENDMENT-2 equilibrium penetration ~9.8e-4 m. Inventing
  a compliance term would be a synthetic constant; compliance screening is
  assigned to a runtime-solver lane (C17/B07-successor debt line).
- Moment/rotation class (x_com/x_inertia; couple 0.0393-0.0435 kg*m^2/s): out
  of scope (UNDECIDABLE in records; needs the adopted-assembly inertia).

## 2. Verdicts and models (exact forms, sealed conventions)

Evaluated per grid point; margin >= 0 means the verdict HOLDS (sealed law is
"WITHIN/CLOSES iff <= threshold", so exact equality counts as holding):

- **V1 static hang** (G01 closed form, standard-g rows): margin = (jn/DT) −
  (m*9.80665)/(n*mu) N, per reading; holds iff P_req <= 60.0 N.
- **V2 transfer** (G06 closed form, record-g): margin = mu*jn −
  ((m/(n−1))*9.81*0.005) N*s, per reading; holds iff req <= mu*jn; n=1 has no
  holding channel -> never holds (−inf).
- **V3 pincer wrap** (WRAP-2, recorded-joint span): margin = s −
  0.074*cos(atan(mu)) m; holds iff the span meets the friction window.

Rows evaluated per cell: V1 and V2 for each of the 4 readings
(scene, band_lo, band_mid, band_hi) + V3 (reading-independent) = **9 rows**.
Scene-line rows carry the hand-mass CONDITIONAL flag; n=4/n=5 cells are labeled
DERIVED-PREDICTION / EXTENSION wherever they appear in any output.

## 3. Sweep design (what runs at which grid)

1. **Axis screens (ranking input).** For each parameter, its full declared grid
   with all other parameters at nominal (mu=0.6, n=3, jn=0.3, s=sealed span;
   each reading at its own sealed mass): ~1,100 cells, 9 verdict rows each.
2. **Decisive-threshold tables (exact, closed form, DERIVED).** For each
   reading: mu_min per verdict per n (n=1..5 static; n=2..5 transfer),
   m_max at nominal mu per n, jn_min at nominal mu per n, and the pincer
   span_min at mu in {0.3, 0.41, 0.6, 0.8399663223427114, 1.0}.
   These are exact critical boundaries, not grid interpolations.
3. **Corridor composition.** ascent/hold corridor existence per reading =
   whether any declared n gives a holding V2/V1 row at that mu; reported via
   the mu_min tables (this quantifies "friction is the corridor hostage" as a
   function of measured mu, including the mu=0.41 no-corridor case).

Total work is closed-form arithmetic (seconds); no physics engine, no GPU.

## 4. Output metrics

- Per axis: per-row flip count (sign changes along the ordered grid),
  integrated normalized margin swing score2 = trapz(|margin|/scale) with scales
  V1=60.0 N, V2=0.18 N*s, V3=0.074 m, and the full margin traces.
- Ranked table: score1 (total flips) desc, then score2 desc, then name asc.
- Decisive thresholds (exact criticals) and corridor mu_min per reading.
- Machine output: `outputs/sensitivity_result.json` + `outputs/ranked_table.txt`
  (both declared with --keep through the runner) + the runner receipt.

## 5. Ranking rule (preregistered before execution)

- **score1(p)** = number of verdict-row flips across p's declared grid at
  other-parameters-nominal (verdict-resolution bought by the full range).
- **score2(p)** = integrated normalized margin swing (continuous axes only; the
  ordinal n axis ranks on score1 alone).
- Rank: score1 desc, score2 desc, parameter name asc (deterministic tie-break).
- **Measurement-research assignment**: rank order maps onto the declared effort
  classes — mu -> bench F-A/F-B/F-C on a bark-covered 74 mm cylinder at 20-60 N
  (REPIN ORDER 2); jn -> isometric force/PCSA (C17) + N*m->N grasp-posture
  lever-arm derivation (needs x_reach/x_inertia); m -> lead-level mass-lineage
  decision (gap 9); s -> A09/C05 joint-limit/aperture work (x_aperture);
  n -> fixture/morphology declaration. The Captain's friction-funding decision
  reads the mu row's flips and the mu_min tables: they state exactly which
  currently-failing verdicts a measured mu above which threshold would flip.
- A parameter whose entire declared range flips nothing resolves no ambiguity
  and is reported as such (no purchase at the declared resolution).

## 6. Gates, execution, failure preservation

- Reproduction gate first (harness verify, exit 0 required) — Phase A, already
  sealed through the runner before this sweep is authorized.
- Sweep executes ONLY through `task_package.py run` with `--pin` = the committed
  prereg sha256; BUSY (exit 75) -> wait >= 10 s, retry same package; four slots;
  CPU only. Kept outputs: `outputs/sensitivity_result.json`,
  `outputs/ranked_table.txt`, runner receipt copied to `sensitivity/receipts/`.
- Failures (any exit != 0, any BUSY exhaustion, any drift/hash mismatch) are
  preserved and reported verbatim; no rerun without an amendment commit.
- Amendments require a new committed prereg revision and a new pin; no re-pin
  mid-run; no post-hoc grid or range changes.
- Every published row carries the CONDITIONAL label of section 0; no
  unconditional climb claim is made or implied by any sweep output.

## 7. Falsifier of this screening study

- If the axis screens show **no** parameter flipping any verdict row within its
  declared range, the corridor verdicts are insensitive to all declared
  parameters at the declared resolution and the ranking purchase is nil; the
  funding decision then rests on the sealed critical-mu table alone.
- If the reproduction gate fails on any sealed number, the harness (not the
  derivation) is the blocker and nothing downstream runs until it is explained
  and fixed or the discrepancy is escalated to the Lieutenant.

## 8. What this prereg does NOT claim

It does not measure mu, does not qualify x_press or any actuator, does not
resolve the hand-mass block, the mass-lineage split, aperture, reach, compliance
or rotation couple, and does not convert any CONDITIONAL closure into a
capability. It ranks where measurement buys the most verdict-resolution.
