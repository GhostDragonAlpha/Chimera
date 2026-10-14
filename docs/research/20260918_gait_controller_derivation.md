# MACAQUE GAIT CONTROLLER — DERIVATION FROM ADMITTED MOVEMENT DATA

Lane: `lane/gait-controller-20260918` (agent: GLM 5.3). Authored 2026-09-18 against
origin/master. **AUTHOR-ONLY**: this document derives the gait controller contract and
banks it; it implements no engine code. The walking macaque is produced when the
free-root packet (`docs/packets/free_root_balance_v1.md`) and the native joint ladder
(`docs/packets/seven_coordinate_lift_v1.md`) are implemented and a hindlimb lift packet
(owed, Section 7 stage D) executes the tables in Section 2 of this document.

Rule-0 admission record: `work.creature.gait_controller`, admitted by
`tools/creature_graph/validation/admit_gait_controller_20260918.py` (idempotent,
revision-aware) into `tools/creature_graph/data/authored/project_program.json`, rebuilt
into the store by `tools/creature_graph/build_graph.py`.

Every number below is computed from the pinned data artifacts by the committed script
`tools/science_funnel/validation/gait_controller_20260918/derive_gait_numbers.py`, whose
full machine-readable output is `tools/science_funnel/validation/gait_controller_20260918/derived_numbers.json`.
Re-running the script reproduces the JSON byte-for-byte (deterministic: no clock, no
randomness).

---

## RULE 0 — ADMISSION

**STATEMENT (someone could disagree with this):** The measured bipedal gait of the
Japanese macaque — one duty factor, four joint-angle waveforms, one ground-reaction
force pair, four joint-moment waveforms over one 0.71 s cycle (Oku 2021, admitted
bytes), with the quadrupedal cercopithecoid stride statistics (Janisch 2024, admitted
bytes) as the forelimb/substrate analog — fully determines a phase-driven walking
controller: a gait-phase lookup of joint targets, the qualified mass-normalized PD
servo, torque caps and per-drive stores derived from the measured moments and positive
work, and support-polygon stability from the free-root packet. Nothing needs to be
learned, swept, or tasted; every constant below is either measured, quoted, or derived
from a stated equation with one declared assumption.

**PREDICTION (not yet measured):** A free-root macaque assembly carrying the Section 2
target tables through the Section 5 control law walks: duty factor 0.68 (envelope
0.63–0.73), peak vertical GRF 1.08 BW (envelope 0.97–1.19 BW), toe-off at 68% cycle
(envelope 63–73%), per-drive positive work per stride at or below the Section 4 store
table with zero store-depletion events over 10 consecutive cycles, and the CoM
projection inside the support hull at every loaded tick. None of this is measured yet;
the falsifiers in Section 6 name the refusals.

**FALSIFIER (named before the run):** If the controller is removed and the body does
not fall, if the realized angles, GRF profile, or duty factor leave the stated
envelopes, if a drive depletes its store mid-walk, if the CoM projection leaves the
support hull without a tip, or if the ledger identities (`|balance_error_J| < 1e-5`,
`|store_balance_error_J| < 1e-5`) break on any status query — this derivation is FALSE
and the controller is refused. A creature that cannot FALL cannot walk: a controller
that "walks" a body the simulator refuses to drop has falsified itself.

---

## 0. SOURCES AND THEIR EXACT STANDING

| Source | Admission | What it contributes here | Standing |
| --- | --- | --- | --- |
| Oku, Ide & Ogihara 2021, Commun Biol 4:1831 (PMC7940622), Supplementary Data 1 xlsx | `oku_bipedal` connector, member sha256 pinned in `tools/science_funnel/data/oku_bipedal/download_receipt.json` | THE bipedal cycle: 101 samples x = 0..100% cycle, two column blocks (FIRST = before foot-morphology alteration = the digitigrade macaque, SECOND = after, per the pinned Fig. 4 caption line order): GRF h/v (N), hip/knee/ankle/MP angles (rad) and torques (N·m); sheet Fig3D: 10 muscle forces (N) | Bytes in-tree, read by the committed script; simulation output of a planar nine-link model (recorded on every admitted record), anchored to measured macaque gait in the paper text |
| Janisch et al. 2024 wild-primate kinematics, figshare 10.6084/m9.figshare.23231366 | `janisch_wildprimate_kin` connector, sha256 pinned; 386 stride records admitted (1 all-NA row quarantined by design) | Quadrupedal comparison: TD/MID/LO angles, excursions, yields, body mass for the four cercopithecoid species (145 strides) — the macaque-analog forelimb/substrate reference (no macaque species is in the Janisch sample; flagged on every record) | Bytes in-tree (`wildprimate_kin.csv`) |
| Oku fulltext XML (`PMC7940622_fulltext.xml`, in-tree attachment) | attachment of `oku_bipedal` | Table 1 segment masses/lengths/COM/MOI; the temporal anchors (cycle 0.71 s, stride 0.72 m, speed 1.01 m/s, duty 0.67 simulated; 0.75 s / 0.79 m / duty 0.65 measured); the sign conventions; viscous coefficients | Quoted verbatim; quoted sentences are identified as quotes |
| Granatosky (Wimberly/Slater/Granatosky 2021) tetrapod gait database, Dryad 10.5061/dryad.z08kprrd5 | `granatosky_gait` connector — 12 file-identity records | NOTHING numeric. The 11 analytic tables (duty factors, stance/swing ratios, limb phase) are DEFERRED: Dryad download returned 401/Anubis; only digest-pinned identities are admitted | Bytes ABSENT — every dependency on these tables is labelled UNMEASURED and carries its own falsifier |
| Higurashi & Kumakura 2021, Dryad 10.5061/dryad.fj6q573tc | `higurashi_gait` connector — 2 file-identity records, DEFERRED | NOTHING numeric. Abstract-level facts only: on a pole, macaques lower the hip, keep hand/foot clearance small (stability strategies against FALLING) | Bytes ABSENT — same honesty |

The digitigrade FIRST block is the contract morphology (the macaque is digitigrade;
the altered-foot block is reported where it sharpens a falsifier envelope, not as the
target).

---

## 1. THE GAIT CYCLE

### 1.1 Body model (all scaling anchors on it)

From the pinned Oku Table 1 (nine segments, 2D): HAT 8.184 kg / 0.482 m, thigh
0.557 / 0.163, shank 0.269 / 0.182, foot 0.080 / 0.074, phalanges 0.021 / 0.045
(COM at 52/41/40/62/50%, MOI about segment COM 2.07e-2 / 1.61e-3 / 7.01e-4 /
5.49e-5 / 6.26e-6 kg·m²). Total:

```
m = 8.184 + 2·(0.557 + 0.269 + 0.080 + 0.021) = 10.038 kg
BW = m·g = 98.44 N          (g = 9.80665)
l_leg (hip→MP) = 0.163 + 0.182 + 0.074 = 0.419 m
```

### 1.2 Timing (measured and quoted)

| Quantity | Simulated intact (the data below) | Measured macaque (paper text) | After foot alteration |
| --- | --- | --- | --- |
| Cycle duration T | 0.71 s | 0.75 s | 0.72 s |
| Stride length | 0.72 m | 0.79 m | 0.70 m |
| Speed | 1.01 m/s | 1.05 m/s (0.79/0.75) | 0.97 m/s |
| Duty factor | 0.67 (paper) / 0.683 (sampled, Sec 1.3) | 0.65 | 0.683 (sampled) |

### 1.3 Stance/swing timing extracted from the GRF

Contact = samples with GRFv > 0. The digitigrade block holds: stance x = 0..68%,
swing 68..100% — **toe-off at 68% of the cycle, duty factor 0.683 sampled (paper
states 0.67)**, stance 0.483 s, swing 0.227 s. Duty > 0.5 means 18% of the cycle is
double support: there is ALWAYS a support polygon with ≥ 2 feet while any foot is
loaded. The 0.67-vs-0.683 delta is the sample grid (101 bins, boundary row counted);
the falsifier envelope (0.63–0.73) covers both readings.

### 1.4 Phase relationships

- **Bipedal (this contract's stage F):** left/right legs offset exactly 0.5 cycle
  (symmetric alternation, forced by the single measured cycle being representative of
  both legs). Double support exists for (2·duty − 1) = 0.37 of each leg's stance
  overlap — the stability margin Section 5.5 uses.
- **Quadrupedal (stage G):** the Janisch bytes carry angles at three events per
  stride, NOT timing; the Granatosky limb-phase tables are DEFERRED bytes. The
  primate footfall order (diagonal-sequence, diagonal-couplet walk) is a METADATA
  claim from the admitted Granatosky abstract. Any limb-phase NUMBER for the
  quadrupedal stage is UNMEASURED until those bytes land — labelled so in stage G,
  and falsified by the deferred-data landing test there.

### 1.5 Stride length vs. speed (honest: one anchor + one law)

Two points exist (simulated and measured, Section 1.2). The relation is NOT fitted
from a sweep (there is no speed series in the admitted bytes). Instead the anchor is
placed on the dynamic-similarity law:

```
Froude  Fr = v² / (g·l_leg):
  simulated  Fr = 1.01² / (9.80665·0.419) = 0.248
  measured   Fr = 1.053² / (9.80665·0.419) = 0.270
```

A comfortable walk sits at Fr ≈ 0.25 (walk–run transition near Fr = 0.5); duty factor
0.65–0.68 at Fr ≈ 0.25 is the anchor this controller uses. Speed changes are
AUTHORED (a scale on cycle frequency), never swept: the falsifiable form is
`T_cycle(Fr) = sqrt(l_leg·Fr_ratio)`-type scaling validated per stage G, not assumed
here.

### 1.6 The natural pendulum check (why the oscillator is driven, not passive)

Swing leg as a compound pendulum about the hip (Table 1 numbers):

```
I_hip = Σ [I_i + m_i·d_i²] = 0.0361 kg·m²,  m_leg = 0.927 kg,  d_com = 0.1523 m
T_nat = 2π·sqrt(I / (m·g·d)) = 1.015 s    (half-period 0.507 s)
```

The measured swing lasts 0.227 s = 0.45 of the half-period: **the swing leg moves
2.2× faster than its natural pendulum** — the gait rides ABOVE the body's natural
frequency (f_gait = 1/0.71 = 1.41 Hz vs f_nat = 0.985 Hz). Consequences: (i) a
passive/van-der-Pol oscillator alone cannot produce this gait (the existing
`tools/gait_controller.py` pendulum law predicts 0.5·T_nat pacing — falsified by this
data unless driven); (ii) the phase generator must be an explicit clock with contact
reset (Section 5.1), not a relaxation oscillator.

### 1.7 Quadrupedal vs. bipedal (Janisch bytes)

Janisch parses to 387 rows = 386 real strides + the 1 pre-existing all-NA quarantine;
14 species. The cercopithecoid analog subset (145 strides):
Lophocebus_albigena 58, Chlorocebus_aethiops 43, Papio_anubis 29,
Cercopithecus_lhoesti 15; body mass 8.44 ± 5.52 kg (range 4.24–19.20).

| Quantity (cercopithecoid quadrupedal) | mean ± sd | n |
| --- | --- | --- |
| Shoulder excursion (deg) | 58.95 ± 18.87 | 133 |
| Hip excursion (deg) | 43.00 ± 20.80 | 131 |
| Knee yield at TD (deg) | 15.40 ± 18.70 | 133 |
| Elbow yield at TD (deg) | 13.99 ± 20.51 | 135 |

The compliant-forelimb signature: the forelimb travels MORE than the hindlimb
(59.0° vs 43.0° excursions) and both give (yield) ~14–15° at touchdown — the
quadrupedal macaque analog is a compliant-limbed walker. Against the bipedal data:
hip excursion GROWS from 43.0° (quadrupedal) to 60.0° (bipedal Oku) — standing up
liberates the hip; the bipedal knee excursion 42.5° matches the quadrupedal range.
These are the envelopes stage G must reproduce.

---

## 2. JOINT TRAJECTORIES (the target tables)

### 2.1 Conventions (quoted from the pinned fulltext, then pinned here)

"Joint angles and moments were positive for hip flexion, knee extension, and ankle and
metatarsophalangeal dorsiflexion." (PMC7940622, Fig. 4 caption.) This contract adopts
exactly that convention for its four hindlimb coordinates; the implementing hindlimb
packet MUST declare the ±1 mapping from these signed tables to its coordinate stems
in writing (the engine's anatomy stems are flexion-named).

### 2.2 Key events over one cycle (digitigrade block)

| Event | x (% cycle) | Evidence |
| --- | --- | --- |
| Touch-down (TD) | 0 | GRFv = 0 at x=0, 93.6 N at x=1 |
| GRFv peak (early-stance single hump) | 3% (21 ms) | 106.5 N = 1.082 BW |
| GRFv falls through BW | 10% | 98.4 N at x=10 |
| Braking → propulsion crossover (GRFh sign) | 19.5% | −23.9 N early, +17.2 N late |
| Ankle plantarflexor moment peak | 25% | −5.92 N·m |
| Hip moment reversal (extensor → flexor) | 44% | +5.53 N·m max |
| MP dorsiflexion peak | 58% | +1.346 rad |
| Hip max extension | 63% | −0.156 rad |
| Toe-off | 68% | GRFv = 0 from x=68 on |
| Knee deepest flexion | 78% | −1.213 rad |
| Hip max flexion (swing) | 92% | +0.891 rad |

Mid-stance in this gait is NOT a quiet plateau: the vertical GRF decays from 1.08 BW
at 3% to 0.70 BW at 50% — a single-hump, early-peaked profile (the human-like
double-hump appears only in the altered-foot block: GRFv 119.6 N = 1.215 BW at 1%,
second hump 86.3 N at 40%).

### 2.3 Excursions (digitigrade block, rad and deg)

| Joint | TD (rad) | min (rad @ %) | max (rad @ %) | excursion |
| --- | --- | --- | --- | --- |
| hip | +0.809 | −0.156 @ 63 | +0.891 @ 92 | 60.0° |
| knee | −0.472 | −1.213 @ 78 | −0.470 @ 100 | 42.5° |
| ankle | +0.928 | +0.846 @ 65 | +1.506 @ 38 | 37.8° |
| MP | +0.558 | −0.147 @ 79 | +1.346 @ 58 | 85.5° |

(Altered-foot deltas, for the falsifier envelopes: knee more extended in stance, ankle
less plantarflexed, MP less dorsiflexed — excursions 39.7° / 33.2° / 73.4°.)

### 2.4 THE TARGET TABLES (the contract's controller content)

Piecewise-linear phase tables at 5% resolution (21 nodes, φ = 0, 0.05, ..., 1.00 of
the cycle; linear interpolation between nodes; node k applies at φ = k/20). Maximum
reconstruction error against the 101 measured samples: hip 1.76°, knee 2.02°,
ankle 2.70°, MP 4.07°.

```
phi       0      .05   .10   .15   .20   .25   .30   .35   .40   .45   .50
hip  rad  0.809 0.835 0.825 0.751 0.651 0.525 0.412 0.297 0.128 0.043 -0.027
knee rad -0.472 -0.670 -0.852 -0.948 -0.973 -0.959 -0.946 -0.890 -0.826 -0.849 -0.860
ankl rad  0.928 1.232 1.383 1.440 1.447 1.465 1.460 1.487 1.499 1.433 1.354
MP   rad  0.558 0.338 0.368 0.497 0.651 0.741 0.827 0.856 0.914 1.046 1.140

phi       .55   .60   .65   .70   .75   .80   .85   .90   .95   1.00
hip  rad -0.065 -0.139 -0.146 -0.042 0.167 0.442 0.767 0.887 0.885 0.807
knee rad -0.872 -0.847 -0.922 -1.045 -1.174 -1.201 -1.084 -0.865 -0.633 -0.470
ankl rad  1.153 0.910 0.846 0.852 0.969 1.253 1.303 1.225 1.071 0.927
MP   rad  1.319 1.295 0.865 -0.025 -0.114 -0.142 -0.092 -0.035 0.134 0.559
```

In degrees: hip [46.4, 47.8, 47.3, 43.0, 37.3, 30.1, 23.6, 17.0, 7.3, 2.5, −1.5, −3.7,
−8.0, −8.4, −2.4, 9.6, 25.3, 43.9, 50.8, 50.7, 46.2]; knee [−27.0, −38.4, −48.8,
−54.3, −55.7, −54.9, −54.2, −51.0, −47.3, −48.6, −49.3, −50.0, −48.5, −52.8, −59.9,
−67.3, −68.8, −62.1, −49.6, −36.3, −26.9]; ankle [53.2, 70.6, 79.2, 82.5, 82.9, 83.9,
83.7, 85.2, 85.9, 82.1, 77.6, 66.1, 52.1, 48.5, 48.8, 55.5, 71.8, 74.7, 70.2, 61.4,
53.1]; MP [32.0, 19.4, 21.1, 28.5, 37.3, 42.5, 47.4, 49.0, 52.4, 59.9, 65.3, 75.6,
74.2, 49.6, −1.4, −6.5, −8.1, −5.3, −2.0, 7.7, 32.0].

Left leg = same table at (φ + 0.5) mod 1. The quadrupedal forelimb tables are
THREE-KEYPOINT (the Janisch bytes carry TD/MID/LO only): stage G interpolates
TD→MID→LO→TD and labels the waveform as 3-keypoint until a continuous forelimb
waveform source is admitted; cercopithecoid means (degrees, Janisch conventions, NOT
the Oku convention): shoulder TD 91.02 ± 18.67, elbow TD 127.38 ± 19.78, wrist TD
153.33 ± 14.69; hindlimb TD: hip 33.26 ± 11.02, knee 120.36 ± 19.32, ankle 98.22 ± 17.15.

---

## 3. THE FORCE PROFILE

### 3.1 Vertical GRF (digitigrade block), 10%-grid samples (N)

```
x%    0     10    20    30    40    50    60    70   ...  100
GRFv  0.0   98.4  82.4  81.5  75.5  68.5  31.7  0.0        0.0
```

| Quantity | Value | Body-weight units |
| --- | --- | --- |
| Peak | 106.5 N at 3% (21 ms) | **1.082 BW** |
| Impulse over stance | 34.48 N·s (0.483 s) | mean 71.4 N = 0.73 BW |
| Max loading rate | 13.2 kN/s | 134 BW/s |
| Toe-off | 68% | — |

**Weight-support closure (internal identity of the data reading):** over one full
cycle both legs must together deliver BW·T of vertical impulse:

```
2 · I_stance = 2 · 34.48 = 68.96 N·s
BW · T       = 98.44 · 0.71 = 69.89 N·s        ratio 0.987  (−1.3%)
```

The −1.3% gap is the sample-grid quadrature error; the falsifier envelope allows ±3%.
The horizontal net impulse closes the same way: +0.072 N·s over the cycle = 0.1% of
the vertical impulse — a periodic gait, neither accelerating nor braking.

### 3.2 Horizontal GRF

Braking peak −23.9 N (0.24 BW) early, propulsion peak +17.2 N, crossover at 19.5%;
braking impulse −1.79 N·s (short pulse), propulsion +1.86 N·s (long tail). Sign
convention per the pinned caption: "Horizontal GRFs were negative for breaking and
positive for propelling components."

### 3.3 Muscle-force envelope (Fig3D, digitigrade block, peaks in N)

IL 668.5, GMED 330.2, VAS 276.7, SOL 215.0, FDL 204.6, BIFl 142.2, GAS 125.8,
RF 106.0, TA 63.9, EDL 24.2. The iliopsoas (IL) peak at 6.8 BW is the passive
element restricting hip extension — the paper's own reading, visible in the bytes;
it is why the hip torque cap (Section 4) is the largest.

---

## 4. TORQUE REQUIREMENTS AND THE ACTUATOR BUDGET

### 4.1 Measured joint moments (digitigrade block, N·m)

| Joint | TD | min (@ %) | max (@ %) | |peak| stance | RMS stance |
| --- | --- | --- | --- | --- | --- |
| hip | −4.16 | −8.97 @ 4 | +5.53 @ 44 | 8.97 | 5.37 |
| knee | −1.66 | −5.31 @ 2 | +5.30 @ 45 | 5.31 | 3.18 |
| ankle | −0.70 | −5.92 @ 25 | +1.12 @ 78 | 5.92 | 4.65 |
| MP | +0.33 | −0.71 @ 54 | +0.33 @ 99 | 0.71 | 0.39 |

(Altered block: hip |peak| 11.23 — the digitigrade foot SAVES hip torque; one more
reason it is the contract morphology.)

### 4.2 Per-joint mechanical work over one cycle

`W = ∫ τ dθ` over the measured waveforms (positive work = actuator source; negative
work = absorbed):

| Joint | W+ (J) | W− (J) | net (J) | peak positive power (W) |
| --- | --- | --- | --- | --- |
| hip | 5.249 | −2.321 | +2.928 | 24.1 |
| knee | 2.557 | −0.473 | +2.083 | 35.1 |
| ankle | 3.266 | −2.233 | +1.033 | 32.3 |
| MP | 0.501 | −0.422 | +0.079 | 6.5 |
| **total** | **11.573** | **−5.449** | **+6.123** | — |

The net +6.12 J/stride is NOT free energy: the Oku model dissipates it in its joint
viscous dampers (hip 0.109, knee 0.317, ankle 0.0943, MP 0.01 N·m·s/rad — quoted);
in the engine's ledger the same role is played by the authored damping and impact
terms, and the ledger closure identity (F-G8) is what verifies the balance.

### 4.3 Torque caps (derived, not tasted)

Cap law: `cap_d = 1.25 × |τ_peak,d|` (the 25% headroom is the same factor the servo
saturation analysis in Section 5.2 needs; it is ONE number with ONE reason, not a
sweep). At the Oku scale, and scaled to the coupled-arm assembly mass by
`cap ∝ m·g·l ∝ m` (geometric similarity):

| Drive | |τ_peak| (N·m) | cap @ 10.04 kg (N·m) | cap @ 7.006 kg arm (N·m) |
| --- | --- | --- | --- |
| hip | 8.97 | 11.2 | 7.8 |
| knee | 5.31 | 6.6 | 4.6 |
| ankle | 5.92 | 7.4 | 5.2 |
| MP | 0.71 | 0.9 | 0.6 |

The qualified arm scene's authored caps (shoulder 0.6, elbow 0.3 N·m; code-range
require ≤ 1.0 / ≤ 0.6) are TWO ORDER magnitudes below what any leg drive needs even
at arm scale — the hindlimb packet must supersede the cap range per this table or the
walk is torque-starved by construction.

### 4.4 Energy per stride vs. the actuator store — THE budget verdict

Scaling law (one declared assumption: dynamic + geometric similarity between the
10.038 kg Oku model and a target assembly of mass m): torque ∝ m·g·l, angles are
dimensionless, so per-stride work scales `E ∝ m·g·l ∝ m^(4/3)`; the proportionality
is pinned at the Oku reference (no fit). Arm assembly 7.006 kg → factor
(7.006/10.038)^(4/3) = 0.619.

| Drive | W+ @ 10.04 kg (J/stride) | W+ @ arm scale (J/stride) | required store = 1.5×W+ @ arm scale (J) |
| --- | --- | --- | --- |
| hip | 5.25 | 3.25 | **4.9** |
| knee | 2.56 | 1.58 | **2.4** |
| ankle | 3.27 | 2.02 | **3.0** |
| MP | 0.50 | 0.31 | **0.5** |
| all drives | 11.57 | 7.17 | — |

**The qualified 2.0 J per-drive battery does NOT power one stride of the hip or ankle
drive even at arm scale** (needs 3.25 / 2.02 J) and is short by 3–4× at macaque
scale. Three honest consequences:

1. The 1.5× multiplier is the derived store floor (25% tracking headroom on top of
   the cap headroom) — the hindlimb packet must admit per-drive stores of at least
   the table's last column at its stage's mass scale.
2. The qualified store semantics are DEPLETIVE: braking (W− = −5.45 J/stride at Oku
   scale) accumulates `brake_` heat and does NOT recharge `battery_`. A regenerative
   variant (brake_d → battery_d) would roughly halve the required stores
   (|net| ≈ 6.1 J vs W+ 11.6 J) but is a NEW contract with its own falsifier — listed
   as a non-claim here, never smuggled in.
3. The per-tick cap (40-step bisection against the store, `coupled_dynamics.hpp`) is
   NOT binding for gait: peak positive power 35 W = 0.117 J per 300 Hz tick, two
   orders below any plausible store. The binding constraint is TOTAL energy per
   stride; the falsifier F-G4 measures exactly that.

Energy per unit mass per distance (for cross-checks): W+ 11.57 J per 0.72 m stride
per 10.04 kg = 1.60 J/(kg·m) mechanical — against the paper's estimated GROSS
METABOLIC cost of transport 14.5 J/(kg·m) ("whereas that estimated based on measured
CO2 production rates was ~15"): the mechanical share is ~11% of metabolic, the rest
is muscle inefficiency the engine does not model (honest scope, Section 8).

---

## 5. THE CONTROLLER ARCHITECTURE

NOT a learned policy — nothing is trained. Four derived pieces: a phase clock, the
target tables, the qualified capped servo, and the support-polygon reflex.

### 5.1 The phase clock (hybrid oscillator)

```
phi_leg(t) = (t / T_cycle + off_leg) mod 1,   T_cycle = 0.71 s,  off = {0, 0.5}
RESET: at own foot contact (gap_k <= kTouch = 1e-5 m), phi_leg <- 0
```

The reset is the hybrid event that makes the clock robust: slip or drag changes the
actual stance duration and the clock re-anchors at every touchdown instead of
drifting (the open-loop clock is the falsified alternative — F-G2's left/right
offset check catches it). The contact event needs NO new machinery: the touching
band and its gate exist in the qualified contact code (`kTouch`, `kSlip`).

### 5.2 The servo (the qualified law, bandwidth derived)

```
tau_d = clamp( kp_d·(q*_d(phi) - q_d) - kd_d·v_d, ±cap_d )
kp_d = M[d][d]·(2·pi·f_s)²,   kd_d = 2·zeta·M[d][d]·(2·pi·f_s)
```

with `M[d][d]` the drive's diagonal mass at the model defaults (the qualified
mass-normalized PD), zeta = 0.8 (qualified), and f_s DERIVED for gait tracking:
the gait fundamental is f_g = 1/0.71 = 1.408 Hz; demanding amplitude ratio ≥ 0.95
on a damped-2nd-order tracking loop, `1/sqrt((1-r²)² + (2·zeta·r)²) ≥ 0.95` with
`r = f_g/f_s`, gives r ≤ 0.35, i.e. **f_s ≥ 4.0 Hz**. The qualified arm's 2.0 Hz
(r = 0.70, amplitude ratio 0.80) is falsified for direct gait tracking — the
hindlimb packet pins f_s = 4.0 Hz with this derivation. The torque cap does the
rest: the tables were generated BY torques of the Section 4.1 size, so saturation
at 1.25×|τ_peak| cannot be the thing that breaks tracking (F-G1 measures the
result, not the hope).

### 5.3 The contact schedule (duty gating)

Foot k is a legal support point only while its gap is in the touching band; the
tables already encode swing (targets lift the MP to −0.142 rad at φ = 0.80). The
contact state the controller ACTS on is the simulator's own touching flag — never a
clock guess (a controller that "supports" through a foot the simulator says is
airborne is exactly the faked-balance failure the free-root packet refuses).

### 5.4 Stability: the support-polygon argument (from the free-root packet, D7)

Static and quasi-static balance through unilateral contact is possible IFF the CoM
horizontal projection lies in the convex hull of the touching points (the
barycentric normal distribution cancels weight AND weight moment with zero
friction; outside the hull NO nonnegative distribution does, and the base tips).
This gait's numbers make the polygon non-degenerate:

- single support (50% of the cycle): the hull is the loaded foot's contact points —
  digitigrade TD lands MP-first with the MP angle RISING (0.558 → 1.346 rad by 58%),
  i.e. the toe strip rolls onto the ground and the hull is the metatarsal-to-toe
  segment, ~0.12 m long, under a CoM that passes over it between 30–50% cycle;
- double support (duty 0.68 → 37% overlap): the hull spans rear-toe to front-toe,
  ~half a stride = 0.36 m.

The Oku waveforms WERE generated by a dynamically balanced simulation, so tracking
them keeps the CoM inside the hull by construction — the controller adds ONE derived
reflex for the unmodeled cases: if the CoM projection exits the hull while its
velocity points outward (a tip in progress), the swing leg's phase JUMPS to φ = 0.95
(early TD — a capture step). The reflex is a discrete law with its own falsifier
(F-G6): without it, a push must tip; with it, the capture step must land.

### 5.5 The energy budget (the verdict of Section 4.4)

Per drive: `battery_d >= 1.5 × W+_d` at the stage's mass scale (table in 4.4),
braking recharges nothing (qualified semantics), `empty_events_d` must stay 0. At
the CURRENT qualified 2.0 J the walk is REFUSED by construction (hip needs 3.25 J
per stride at arm scale) — this is the derivation's headline: **the free root makes
falling possible; the store table makes walking possible; both must land together.**

---

## 6. THE FALSIFIERS (each a measured refusal)

- **F-G1 — trajectory envelope.** After 3 gait cycles from a standing start, the
  realized angle of every drive stays within the Section 2.4 node table ±0.087 rad
  (5°) for ≥ 95% of each cycle, and each drive's measured excursion is within ±10%
  of Section 2.3 (hip 60.0° ± 6, knee 42.5° ± 4.3, ankle 37.8° ± 3.8, MP 85.5° ± 8.6).
  A wider excursion REFUTES the servo/cap derivation.
- **F-G2 — duty and phase.** Measured duty per leg 0.68 within [0.63, 0.73]
  (covers the sampled 0.683, the paper's 0.67, the measured-animal 0.65); left/right
  phase offset 0.50 ± 0.02 over 10 cycles. An open-loop drift beyond 0.02 REFUTES
  the contact-reset claim.
- **F-G3 — GRF envelope.** Peak vertical GRF = 1.08 BW within ±10%; toe-off at
  68% ± 5% cycle; loading rate 13.2 kN/s ± 30%; braking then propulsion in the
  measured order with the crossover at 19.5% ± 5%; net horizontal impulse ≤ 5% of
  the vertical impulse; the closure identity `2·I_stance = BW·T_cycle` within ±3%.
  A single-hump profile growing a human-like second hump REFUTES the foot-morphology
  fidelity (that is the altered block's signature, 1.215 BW at 1%).
- **F-G4 — energy within budget.** Per drive, measured positive work per stride
  ≤ 2× the Section 4.2 table value AND ≤ its store; `empty_events_d = 0` over a
  10-stride run. A depletion mid-walk REFUTES the store table or the tracking
  (whichever the ledger names).
- **F-G5 — the free-root falsifier.** With the controller powered off (`power=false`),
  the free body FALLS: base height decreases, no pose holds, joints fold onto their
  stops. Any hover, any phantom stance REFUTES the simulator, not the controller.
- **F-G6 — stability and the capture reflex.** 10 consecutive cycles: the CoM
  projection stays inside the support hull at every tick with a touching, loaded
  foot; no tip occurs WITHOUT the reflex; with the reflex armed, a scripted
  CoM-shifting push produces an early touchdown (capture step) and the walk
  continues. A fall without push REFUTES the tables; a fall under push with the
  reflex disarmed REFUTES nothing (expected); a tip while the CoM is reported
  INSIDE the hull REFUTES the support machinery itself.
- **F-G7 — determinism.** Two identical runs produce bit-identical status streams
  (the repo's determinism law; the phase reset makes the hybrid system's event
  order part of the claim).
- **F-G8 — ledger closure (inherited).** `|balance_error_J| < 1e-5` and
  `|store_balance_error_J| < 1e-5` on every status query of every run above. One
  violation REFUTES everything else measured on top of the ledger.

---

## 7. THE STAGED IMPLEMENTATION LADDER (mounted arm → walking macaque)

- **Stage A — the frozen mounted arm (EXISTS).** The qualified 2-coordinate scene
  stays byte-untouched; every later stage re-proves it (the packets' F1/F8 pattern).
- **Stage B — the seven-coordinate lift (packet banked).**
  `docs/packets/seven_coordinate_lift_v1.md`, ladder 2 → 3 → 5 → 7 with the
  `Assembly` oracle at 1e-12; per-drive stores land here (S2).
- **Stage C — the free root (packet banked).** `docs/packets/free_root_balance_v1.md`,
  falsifiers F1–F9: the body falls at g, zero-torque standing collapses, the
  support-polygon condition tips. After C the creature CAN fall.
- **Stage D — the hindlimb lift (packet OWED; this document is its contract).**
  New coordinates in the pin order `hip_flexion, knee_extension, ankle_dorsiflexion,
  MP_dorsiflexion` (Oku sign convention, ±1 stem mapping declared in the packet),
  staged 1 → 4 coordinates with the B-stage oracle pattern; per-drive caps and
  stores from Section 4.3/4.4; `f_s = 4.0 Hz` from 5.2. Gate: oracle ≤ 1e-12, stops
  at 1e-9, ledger < 1e-5, and the B/C stage falsifiers re-proven.
- **Stage E — bipedal stand.** Free root + four leg drives, targets frozen at the
  φ = 0 column of the tables; measured: CoM in hull, servos hold with per-minute
  work ≤ 60×W+_hip (budget recorded, not asserted), zero-torque collapse still
  demonstrable (C's F2 re-run with legs). Gate: a 60 s stand without a store
  depletion and without a tip.
- **Stage F — bipedal walk.** The Section 5 controller; falsifiers F-G1..G8 in
  order; the run is not a pass until the GRF closure identity (F-G3) and the energy
  budget (F-G4) hold on the SAME run.
- **Stage G — quadrupedal and substrates (after the deferred bytes, or flagged
  UNMEASURED).** Forelimb drives with the Janisch 3-keypoint tables (Section 2.4);
  footfall order authored as diagonal-sequence per the Granatosky abstract METADATA
  — limb-phase NUMBERS stay out of any falsifier until the Dryad bytes land and the
  admitted tables confirm or replace them; pole substrate per Higurashi's abstract
  facts (lower hip, small clearance — the falling-risk strategy). The Dryad landing
  test: the pinned sha256s must match, the tables must reproduce the published duty
  factor 0.65 measured anchor within their own envelopes, and any disagreement
  supersedes THIS record first.

---

## 8. HONEST SCOPE / NON-CLAIMS

- Nothing here is measured on the engine: every falsifier is UNTESTED. The admission
  record says `status: specified`, falsifier `untested`.
- The Oku data are simulation outputs of a planar nine-link model anchored to
  measured macaque gait (recorded on every admitted record); this derivation
  inherits that standing — it is a controller contract derived from a validated
  simulation, not from a living animal.
- No muscles: the ten muscle-force waveforms (Section 3.3) bound what the torque
  sources must deliver but the engine's ideal capped drives remain ideal; isometric
  cost and metabolic stores stay out (the 14.5 J/(kg·m) figure is quoted as the
  metabolic envelope, not modeled).
- No frontal-plane control: the Oku model is 2D sagittal; hip abduction (the real
  macaque's lateral stability) is unnamed in the tables and enters only as stage
  D's optional fifth coordinate with its own packet. The support-polygon reflex
  (5.4) is the derived substitute until then.
- Single speed: the tables are one Froude point (0.25); speed scaling is authored
  per stage G, never swept into this contract.
- The Granatosky and Higurashi bytes are ABSENT; every number from them is a
  metadata-level claim, labelled, and falsifiable on landing.
- No engine file changes: this lane adds this document, the derivation script +
  JSON, and the admission record — nothing in `ChimeraEngine/`.

---

## PROVENANCE

- Derivation script: `tools/science_funnel/validation/gait_controller_20260918/derive_gait_numbers.py`
- Machine output: `tools/science_funnel/validation/gait_controller_20260918/derived_numbers.json`
- Data pins: `tools/science_funnel/data/oku_bipedal/download_receipt.json`,
  `tools/science_funnel/data/janisch_kinematics/download_receipt.json`
- Reproduce: `python -B tools/science_funnel/validation/gait_controller_20260918/derive_gait_numbers.py`
  (pinned interpreter; deterministic; rewrites the JSON identically)
- Admission: `tools/creature_graph/validation/admit_gait_controller_20260918.py`
  then `python -B tools/creature_graph/build_graph.py` (evidence count must remain 11)
