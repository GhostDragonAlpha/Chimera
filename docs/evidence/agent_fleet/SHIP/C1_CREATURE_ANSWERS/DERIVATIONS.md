# C1 CREATURE ANSWERS — DERIVATIONS

Every number in the reflexes, traced. Measured on scratch 8163 (CURRENT
binary, snapshot-copied cwd, headless, killed by PID after the runs) with
[measure_floors.py](measure_floors.py); raw outputs:
[floors_scratch8163.json](floors_scratch8163.json),
[walk_scales_scratch8163.json](walk_scales_scratch8163.json),
[stance_floor_scratch8163.json](stance_floor_scratch8163.json).

## 0. The body (measured)

| quantity | value | source |
|---|---|---|
| mass | 13,824.5 kg | `mass_kg_` (movement-law header; V_whole 13.8246 m³ x water) |
| sealed cells | 4 | /tick_state: feet 0.288 m³ (y −0.02..0.338), **torso 12.509 m³ (y 3.415..9.971)**, mid 0.693, lower 0.335 |
| torso skin area | 64.694 m² | divergence over the torso cell's external triangles (mesh_bin + seal-tree blobs, offline) |
| tick period | 3.34 ms (299 Hz) | ticks counter over a 3 s wall window |
| kappa | 4.6e-10 Pa⁻¹ | `kappa_` (water at 25 C, in the header) |
| skin yield | 15 MPa | `yield_pa_` (Yamada 1970, in the header) |
| gentle-hand bar | 50 kPa | `GAIT_P_RELAX_PA` (named in-file bar) |

Torso cell = **argmax v0** over `seal_cells_` (90.5% of the body; a named,
taste-free rule; re-derived at every arm, frozen at arm).

## 1. The pressure ladder (measured — the flinch threshold's ruler)

Held touches on a mid-radius torso vertex (belly hit (−0.000, 5.112, −4.288)),
per-cell sealed pressure at plateau:

| force | peak \|P\| (torso cell) | vs 100 kPa threshold |
|---|---|---|
| 500 N | 3.646 kPa | below — tolerated |
| 2 kN | 10.94 kPa | below — tolerated |
| 10 kN | 51.05 kPa | below — gentle handling tolerated |
| 20 kN | 432.2 kPa | **above — flinch** (the W2 demo press is 20 kN) |
| 50 kN | 9.086 MPa | far above — flinch hard |

Floors: rest max|P| **exactly 0** (4 s, 20 Hz); stance-idle max|P| **exactly
0** (6 s). Onset shape: the press block SETS its offsets (no ramp), so the
plateau arrives within one tick — measured: the first poll sample above 1 kPa
was already at plateau (10,938.6 Pa for the 2 kN hold).

**Threshold = 1.0e5 Pa.** Arithmetic: 2 x GAIT_P_RELAX_PA (the creature
tolerates everything the repo already calls a gentle contact); = 0.67% of
yield (150x below damage — a flinch is a warning, not an injury); sits
between the 10 kN and 20 kN ladder rungs. AWAITING ASTRA.

## 2. The walk's own pressures (measured — the suppression gate's ruler)

3-stride gait run, 30 ms polls: per-cell pmax **median 24.1 MPa, max
86.4 MPa**; per-poll |dP/dt| p50 3.5 MPa/s, p95 281 MPa/s, max 583 MPa/s;
|conserve_pct| worst 3.3e-4 (bar 0.01); teardown max|P| **exactly 0**.

Consequences, both measured-mandatory:
- **Flint/startle suppression under gait is not a policy choice**: the walk's
  floor-state pressures exceed the flinch threshold ~240x. Ungated, the
  creature flinches at its own legs.
- A level or rate detector cannot separate touch from walk — no threshold
  exists that fires on touches and not on strides. The gate IS the design.

## 3. Breathing rate (Stahl allometric law — shown arithmetic)

Law: mammalian respiratory frequency f = 53.5 · M^(−0.26) breaths/min
(Stahl 1967; the same allometric family the repo already cites for
mass-derived quantities).

```
M        = 13,824.5 kg
ln M     = 9.5345
M^-0.26  = e^(−0.26 x 9.5345) = e^(−2.4790) = 0.08388
f        = 53.5 x 0.08388 = 4.485 breaths/min
period T = 60/4.485 = 13.38 s
omega    = 2π f / 60 = 0.4697 rad/s
```

Cross-check at honest anchor points: elephants (4–6 t) breathe ~4–10/min
(the law gives 6.2/min at 4 t); large whales surface-breathe at 1–2/min.

**Game-scale factor = 1.0 — no speedup applied.** Stated, not silent: at
13.8 t the creature is elephant-plus scale; observers accept that scale
breathing slowly (whales at 1–2/min read as alive); speeding it to human
rate would read as panting — the wrong body. The perceptual risk is NOT the
rate (a 13.4 s continuous sinusoidal swell is unambiguous motion), it is the
AMPLITUDE — see below; that lever is AWAITING ASTRA.

## 4. Breathing amplitude (tidal volume → swell)

Law: tidal volume V_T = 6.2 mL/kg · M^1.01 (Stahl family).

```
V_T      = 6.2e-3 L/kg x 13,824.5^1.01 kg = 6.2e-3 x 15,157 L = 94.0 L
         = 0.0940 m^3
fraction = 0.0940 / 12.509 = 0.752% of the torso cell's rest volume
swell    = V_T / A_torso = 0.0940 / 64.694 = 1.45 mm mean (raised-cosine
           profile peak ≈ 2 x mean ≈ 2.9 mm)
```

**Why the breath is a volume-target offset, not a pressure event — shown,
not assumed.** If the kappa law saw a 0.752% torso volume swing it would
answer ΔP = ΔV/(κ·V0) = 0.0940/(4.6e-10 x 12.509) = **14.9 MPa — 99% of the
skin yield — every breath**. A Pa-scale "honest" pressure swing instead gives
ΔV = ΔP·κ·V0 = 500 Pa x 4.6e-10 x 12.509 = 2.9e-6 m³ = a 0.04 µm swell —
invisible by six orders of magnitude. In a water-stiff sealed cell the two
demands ("Pa-scale pressure swing", "visible surface swell") are
incompatible BY THE LAW. The resolution is the animal's own: the breath
lives in the COMPLIANT THORAX (ribs+diaphragm), not the water coelom. The
breath is therefore the cell's volume TARGET moving (with the surface
tracking it through the engine's pose-displacement machinery), and the
sealed-cell pressure law is structurally blind to it. The conservation
export is tiling-consistency (Σ cell vols vs whole posed volume, same
triangles) and nets the breath out exactly (pass order); window #8 MEASURES
both blindness clauses (R1 prediction) rather than assuming them.

## 5. Flinch response limb (the same-limb law, re-verified)

The V3a net-weight law, re-derived from the snapshot blobs in standalone
Python during this prereg (vertbind + mesh + seal tree): foot set = rest
verts with y ≤ feet yhi (0.338) split by x-sign; per-pin net weight =
own-side minus opposite; top-2 per side:

```
L: pins [17, 15], nets [965.1, 63.2]   -> strut 17, clear 15
R: pins [18, 16], nets [965.1, 63.2]   -> strut 18, clear 16
```

matches the engine's enable log (strutPinL/R 17/18, clearPinL/R 15/16) and
drive_resolution_prediction.json exactly. The reflex reuses the gait
machine's resolved pins when this body has them (one source of truth) and
otherwise runs this same law itself. Response = the STRUT pin (the measured
z/raising channel); raising direction = lift_sign (the +20 deg branch law's
own sign, also persistent from gait when available).

Amplitude = STANCE_THETA_MAX_DEG (5 deg, the F1 named bar): the reflex may
never demand more ankle than the balance rung's own derived authority, so a
flinch can always be recovered from. Decay: exp(−t/0.5 s), tau_relax_ (the
named tissue family), cutoff 1e-3 rad with deterministic pin zeroing.

## 6. Startle nudge (magnitude through the stance channel)

The stance probe measured |S| = 0.283 m/rad of sagittal lean per rad of
symmetric ankle pitch (V2 bar; read live as 1/stance_kp_ = 3.531 →
S = 0.2831, matching the prereg reference). The startle spends ONE rest-sink
quantum of lean (GAIT_SINK_M = 0.01 m, the body's own named vertical
scale):

```
theta = GAIT_SINK_M / S = 0.01 / 0.283 = 0.03534 rad = 2.03 deg
cap   = STANCE_THETA_MAX_DEG = 5 deg  ->  2.5 deg of headroom kept for the
        servo's own response (inside the existing caps, as required)
```

dP/dt threshold = 1.0e6 Pa/s ≈ 3.3 kPa/tick at the measured 3.34 ms tick:
above every measured floor (rest and stance-idle are EXACTLY 0 Pa/s) and
below the lightest ladder rung's onset (500 N steps 3.6 kPa in ≤1 tick
≈ 1.1 MPa/s). Post-gait quiet window 1.0 s = 2 tissue taus (the walk's
measured collapse rates reach 583 MPa/s — a cut would otherwise false-fire
the whole-body reflex at its own stumble).

## 7. What was NOT derivable (handed to Astra, explicitly)

- Whether the breath's honest 1.45 mm swell reads as alive at game camera
  (the amplitude multiple is taste).
- The behavioral threshold where "tolerated handling" becomes "flinch"
  (100 kPa interim = twice the repo's own gentle bar).
- The startle's sensitivity floor and nudge size (1 MPa/s, 2.03 deg interim,
  both anchored to named/measured scales).

The mechanism (detector → two-neuron arc → envelope → composition → gates →
nerve cut) is complete and does not change when Astra re-numbers it.
