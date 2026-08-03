# THE TRUNK TISSUE — the lumbar ligament port

> Membrane stated 2026-08-04, before the build. Opened by F3's judged debt
> (`docs/THE_SLICE.md`, rung 3): the stand policy holds the pelvis at 93% of target
> through the parser, but arches the lumbar **1.14–1.34× (peak 1.56×) past L4_L5_FE's
> declared stop**, because `tools/world.py`'s passive-tissue derivation covers hip, knee
> and ankle and *refuses* the trunk — "left alone 13 (out of range, no ligament)" — for
> want of a published envelope. This document is the research that refusal demanded,
> the membrane built over it, and the derivation.

---

## THE AMENDMENT THE LEAK WROTE (2026-08-04, before the v3 run)

The membrane promised FE only. The first retrained policy answered: the arch dropped
from 1.56x to 1.12x of range -- and the body started LEANING instead, `lat_bending`
-28.2 deg against a -25 stop, L1_L2_LB 1.13x. The unsupported direction became the new
cheapest posture, which is the membrane's own logic read back to it: a ligament covers
exactly the direction it covers, and no other.

The same citation covers lateral bending. Miller 1986: "in extension AND LATERAL
BENDING the maximum intervertebral tilt in the lumbar spine has been reported to
rarely exceed 5 deg in vivo (Bakke 1931; Pearcy and Tibrewal 1984)". So the LB path is
this membrane extended, not a new theory: both directions, edge +-5 deg, per-level gap
from the model's declared ranges. Derived: `lat_bending` +-20 deg gap (463/489 N.m/rad),
L2_L3 and L3_L4 LB ~+-4 deg gaps (1760-1960 N.m/rad). Refused, named: L1_L2_LB (its own
+-4.7 deg stop sits INSIDE the performed envelope -- no gap exists to derive across)
and L4_L5_LB (gap 0.1-0.14 deg, below the 1 deg radiography grain). The falsifiers
below now judge the combined FE+LB structure; the prediction's "worst joint" was always
written over every joint, and the leak proved that was the right bar.

---

## RULE 0 — THE THEORY

**STATEMENT.** The lumbar motion segment is a passive structure with a measured
moment-angle curve: compliant through the motion the body actually performs, stiff at
the end of it. A ligament derived the same way the leg ligaments were —
`k = tau_max / gap`, where `tau_max` is the model's OWN maximal muscle torque driving
into the stop and `gap` is the slack between the published in-vivo extension envelope
edge and the model's declared limit — is enough passive structure that the stand
policy no longer drives the lumbar through its stop. No number in it is chosen.

**PREDICTION.** With the ligament in and the stand policy re-trained (same CEM, same
derived reward, warm-started), `tools/f3_stand.py` reports the port contract PASS:
worst joint < 1.00× range for the full 5 s, **and** pelvis MIN >= 90% of the 0.9201 m
target — the ligament neither lets the joint through the stop nor makes standing
impossible.

**FALSIFIER.** Named before the run, three independent triggers:
1. After retraining, L4_L5_FE still exceeds its declared stop sustained (jf >= 1.0) —
   the derived structure is insufficient, the theory loses.
2. Standing becomes unreachable (pelvis MIN < 90%) — the derived structure is a wall,
   not a ligament, the theory loses.
3. The implied end-range stiffness lands outside one order of magnitude of the measured
   6–11 Nm/deg band (Miller 1986, below) — the derivation is answering a different
   question than the anatomy, the theory loses.

A description survives any result; this one can lose three ways.

---

## THE RESEARCH — every number with its source

### 1. The measured passive moment-angle curve (the validation band)

**Miller, Schultz, Warwick & Spencer 1986**, *Mechanical properties of lumbar spine
motion segments under large loads*, J. Biomech. 19:79–84
([full text, CDC stacks](https://stacks.cdc.gov/view/cdc/224275/cdc_224275_DS1.pdf)).
Fourteen fresh human lumbar motion segments, male, mean age 29, loaded to 95 Nm in
flexion, extension, lateral bending and torsion:

- **Moment stiffness 6–11 Nm/deg** (343–630 Nm/rad) across the moment modes at large
  loads. This is the END-RANGE stiffness — the number the ligament must reproduce.
- Large-load moment stiffness is **1.5–6× the small-load values** (Schultz et al. 1979,
  same apparatus, at 4.7 Nm with 400 N compression) — the curve is nonlinear, stiffer
  at the ends. A ligament slack in the band and taut at the stop is exactly this shape.
- At rotations of ~10 deg or more, the segments passively resist **30–70% of maximal
  voluntary trunk muscle moments** (against McNeill et al. 1980). The leg derivation's
  principle — size the ligament to hold what the muscles crossing the joint can
  produce — is anatomically confirmed for the trunk: at end range the passive
  structures and the muscles are the SAME order of load.
- No specimen failed below 59 Nm in bending. Failure is not the regime here.

### 2. The neutral zone (the compliant band)

**Heuer et al. 2007** (initial stiffness values as compiled in
[Frontiers Bioeng. Biotechnol. 2024, lumped-parameter IVJ model](https://www.frontiersin.org/journals/bioengineering-and-biotechnology/articles/10.3389/fbioe.2024.1304334/full)):
**37 Nm/rad** (~0.65 Nm/deg) flexion-extension initial stiffness — the small-displacement,
near-neutral resistance. Ratio to Miller's end-range band: ~9–17×, consistent with
Miller's own "1.5–6×" at moderate rotation growing toward the stop.

**Gardner-Morse & Stokes 2004**, *Structural behavior of human lumbar spinal motion
segments*, J. Biomech. 37:205–212 ([full text, UVM](https://www.uvm.edu/~istokes/pdfs/motseg.pdf)).
Six-DOF stiffness matrices, L2-3 and L4-5, ±1 deg displacements, 0/250/500 N preload:

- Stiffness rises **×1.71 / ×2.11** with 250/500 N axial preload — compression
  stiffens the segment. The standing body carries ~500 N at the lumbar, so the
  measured curve UNDERSTATES nothing: the in-vivo structure is stiffer than the
  no-preload bench numbers.
- The load-displacement relation is **bilinear**: mean ratio of larger to smaller
  stiffness for **extension:flexion = 3.11** — extension is ~3× stiffer than flexion.
  The arch F3 caught is into EXTENSION, the direction anatomy resists hardest. The
  deficit in the model is therefore worst exactly where the tissue is strongest.

### 3. The envelope (the motion the body actually performs)

Per-segment, in vivo, cited within Miller 1986:

- **Extension: intervertebral tilt rarely exceeds 5 deg** (Bakke 1931; Pearcy &
  Tibrewal 1984, three-dimensional radiography). This is the extension envelope edge:
  the ligament engages from 5 deg of extension to the model's declared stop.
- **Flexion: average maximum ~15 deg per segment in vivo** (Adams & Hutton 1982;
  Pearcy et al. 1984). The model's declared flexion limit (+4.8 deg at L4_L5_FE) is
  INSIDE the performed envelope — there is no gap, so there is no flexion ligament to
  derive. Named and refused, the same move `world.py` makes when the gap is below the
  envelope's grain.
- Bible et al. 2010 (*Normal functional ROM of the lumbar spine during 15 ADLs*,
  J. Spinal Disord. Tech. 23:106–112): whole-lumbar functional sagittal motion 3–49 deg
  across ADLs (squat 42 deg, bend 48 deg) — corroborates that per-segment functional
  motion is a few degrees, and that the arch the policy found (-14.6 deg at one joint)
  is outside anything a body does.

### 4. What the model declares (the other half of the gap)

From `myobody.xml`, read not assumed: `L4_L5_FE` range **[-10.7, +4.8] deg** (negative
= extension; the measured violation sat at -14.6 deg). The four lumbar FE hinges
(L1_L2 … L4_L5) get the extension ligament; the slack band is
`[-10.7, -5.0] deg → gap = 5.7 deg`, identical construction at every level unless the
model's declared ranges differ, in which case each level gets its own arithmetic.

---

## THE DERIVATION (implemented in `tools/world.py`, 2026-08-04)

```
gap      = |model_limit - 5.0 deg|          (published in-vivo envelope edge; FE: extension
                                             side only. LB: BOTH sides, per the amendment)
tau_max  = max over the band of signed muscle torque INTO the stop,
           from the model's own actuator_moment at full drive, from qpos0
           (the existing derive_ligaments code path, unchanged)
k        = tau_max / gap                     (nothing selected; rule 1)
```

Emitted as the same `<fixed>` tendon form the leg ligaments use, one-directional,
engaging at the envelope edge. L == R symmetry does not apply (FE/LB joints are midline);
the check instead is that the levels derive comparable stiffness, and any level
whose muscles produce no torque into a stop is REFUSED and named, not fitted.

Measured at emission: FE extension 832 / 866 / 1013 / 1826 N.m/rad (L1_L2 -> L4_L5,
gaps 12.9 -> 5.7 deg); LB 463 / 489 (lat_bending) and 1760-1961 N.m/rad (L2_L3, L3_L4).
All inside one order of magnitude of Miller's 343-630 N.m/rad end-range band -- the
upper-bound side, as named below.

**HONEST BOUND, carried from the leg derivation:** sizing to maximal voluntary
contraction is an UPPER bound on the ligament; Miller's 30–70%-of-MVC at end range
says real tissue sits below it. Falsifier 3's order-of-magnitude band absorbs exactly
this, and the difference is published, not reconciled (Rule 17).

---

## THE LARGER THING THIS IS THE TEMPLATE FOR

This is the first NON-LEG tissue membrane, and it is the pattern the operator's
universal passive-tissue frame predicts: every structured thing in the world —
grass, tree, rock, building — gets `tau = k x + c v` with k derived from what acts
on it and the gap from what it actually does. The lumbar is the proof the pattern
travels: a joint with no gait envelope, no ledger entry, and no ligament in the model
still closes from published measurement alone.

## NEXT

1. ~~Extend `derive_ligaments` in `tools/world.py` with the lumbar FE path~~ DONE
   2026-08-04, plus the LB path the leak demanded (amendment above).
2. ~~Re-train the stand port (warm start, `--init`), then run `python tools/f3_stand.py`.~~
   DONE 2026-08-04 (v4, 16x48 CEM, warm-started, in the verified 20-ligament world
   `_tissue_662f4d48.xml`; the trainer now saves the SESSION's best theta).
3. ~~Judge against the three falsifiers above~~ DONE 2026-08-04. Verdict below.

---

## THE VERDICT (2026-08-04, v4 theta, measured by `tools/f3_stand.py`)

**The theory survives. It is not falsified on any of its three named triggers —
and its prediction over-promised by one transient.**

| Falsifier | Trigger named before the run | Measured | Verdict |
|---|---|---|---|
| 1. lumbar still through its stop SUSTAINED | jf >= 1.0 sustained | L4_L5_FE peak 1.12, over its stop **6.0%** of phase 1 | does NOT fire — transient, not sustained |
| 2. standing unreachable | pelvis MIN < 90% | pelvis MIN **92.1%** of 0.9201 m, held 5.00 s | does NOT fire |
| 3. stiffness outside the 6–11 Nm/deg band | order-of-magnitude miss | 463–1961 N.m/rad vs 343–630 — inside one order, upper side | does NOT fire |

What the ligaments changed, measured: the lumbar went from **sustained 1.14–1.34x
(peak 1.56x)** past L4_L5_FE's stop, and then (FE-only world) to a lean of
-28.2 deg against a -25 stop, to a **6% transient graze at 1.12x** — and the graze
lands inside t = 4.68–4.98 s, the same window where the CoM excursion peaks (2.56x
of the BoS box). The lumbar overshoot is now the signature of a balance wobble,
not a posture.

What the prediction got wrong, said plainly: "worst joint < 1.00x range for the
full 5 s" is NOT met (peak 1.12). The theory's claim — that derived passive
structure makes the sustained violation unnecessary — is borne out; the claim
that it makes every transient impossible was too strong, and the run said so.
That is the theory working: it was specific enough to be half-wrong in a way
that can be measured, and the half that was wrong is named.

**The residual F3 debt is re-allocated by this measurement, not erased:** the
sustained over-stop joints are no longer lumbar — `mtp_angle_l` 1.11x over 97.6%
of phase 1, `knee_angle_r` 1.05x over 95.2%, `hip_rotation_l` 1.03x over 84.4%,
`subtalar_angle_r` 1.10x over 28.0% — leg joints with pre-existing ligaments,
outside this membrane's scope, plus the CoM excursion (the policy's balance, not
the tissue's stiffness). The trunk membrane's own ledger entry closes here; what
F3 still owes is written down in `docs/THE_SLICE.md` rung 3.
