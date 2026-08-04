# THE FOOT & HIP TISSUE — the off-sagittal ligament ports

> DRAFT membrane, stated 2026-08-04. Opened by the port contract's own work list
> (`tools/f3_stand.py`, measured after the trunk membrane): seven joints over their
> stops in standing, and the harness names why each is not held — `subtalar_angle_r/l`
> (worst, 1.16×), `mtp_angle_l/r`, `hip_rotation_l/r`, `hip_adduction_l/r` all
> "never reached the derivation: theHuman's gait_envelope_deg publishes no curve
> for this joint". TheHuman publishes three sagittal curves (hip, knee, ankle);
> these four joint groups are off-sagittal, and the trunk membrane already showed
> the move: when the ledger has no envelope, take the edge from the LITERATURE.
> (The knees' one-sided ligaments are a separate, named matter — `gap 1.84° ≤
> envelope grain 4.16°`, an instrumentation question, not a missing citation.)

---

## RULE 0 — THE THEORY

**STATEMENT.** Every over-stop joint left on the port contract's list is a joint
whose *performed* envelope is a few degrees and whose *declared* stop is far past
it — the same shape the lumbar had. The trunk construction transfers unchanged:
`gap = |model_limit − literature_edge|` where the edge is the published in-vivo
performed envelope, `tau_max` from the model's own actuators driving into the
stop, `k = tau_max / gap`. No number chosen; a joint whose literature edge falls
inside the model's declared range with no gap is REFUSED and named, never fitted.

**PREDICTION.** With the ligaments derived and the stand re-judged (no retrain —
ligaments are passive; the policy is untouched), `tools/f3_stand.py`'s port
contract report shows every covered joint's sustained over-stop fraction gone
(transient-only at worst), and the port contract's open-debt count drops from 7
to the knees alone.

**FALSIFIERS.** Named before the build:
1. Any covered joint still SUSTAINED over its stop (≥ 50% of phase 1, the trunk
   membrane's own operationalization) — the derived structure is insufficient.
2. The stand regresses (pelvis MIN < the 102.3% it measures now) — the new
   tissue is a wall, not a ligament.
3. Any derived stiffness lands outside one order of magnitude of a published
   passive stiffness for that joint — the derivation answers a different
   question than the anatomy.

---

## THE RESEARCH — the performed envelopes (2026-08-04)

### Subtalar (inversion/eversion)

- **Gait, in vivo: ~6–8° total excursion** in the normal foot
  ([Mann 1988, via Glasgow thesis](https://theses.gla.ac.uk/78186/1/11007578.pdf));
  rearfoot eversion peak **8.7° at 27.8% of stance**, 95% CI 1.9–15.5
  ([Campbell et al., biplane fluoroscopy](https://sportsfootankle.com/wp-content/uploads/2015/09/normative-rearfoot-motion-during-barefoot-shod-walking-using-biplane-fluoroscopy.pdf)).
- **Passive/clinical ROM** (the stops' sanity band): inversion 20–36°, eversion
  5–19° ([Boone & Azen; Dul & Johnson; Brukner & Khan, via Massey thesis](https://mro.massey.ac.nz/server/api/core/bitstreams/5d06e66f-34a7-48d3-83d3-5a04ca541253/content)).
- **Envelope edge for the derivation: ±9°** (Mann's 8° + the fluoroscopy CI's
  upper reach, rounded UP to the conservative side).

### First MTP (dorsiflexion at push-off)

- **Gait, in vivo: ~60° dorsiflexion** barefoot, 45–50° shod
  ([Acta Orthopaedica, toes in walking](https://actaorthop.org/actao/article/download/29015/33895/82474));
  walking measurements span 50–90° across methods
  ([Nawoczenski et al. 1999, JBJS](https://www.umass.edu/locomotion/pdfs/jbjs-1999.pdf)).
- **Passive/clinical ROM**: dorsiflexion 65–110°, plantarflexion 23–45° (same JBJS review).
- **Envelope edge: 65°** (the gait distribution's high end; the passive range
  sits comfortably past it — the ligament's gap is real).

### Hip rotation (internal/external, transverse plane)

- **Passive/clinical ROM**: internal 30–40°, external 45–60°
  ([Padua thesis, goniometry](https://thesis.unipd.it/retrieve/babc7132-f21b-48e5-97fd-e2b918ff540a/Raunich_Francesca.pdf);
  [STA hip review: IR 35°, ER 45°](http://www.stacommunications.com/journals/diagnosis/2001/04_April/bhandia.pdf)).
- **Gait, in vivo**: pelvic transverse rotation mean total excursion **4.3°,
  SD 1.1, range 2.6–7.3°** at preferred speed ([Lewis et al. 2017 citing Kadaba
  et al. 1990](https://anatomypubs.onlinelibrary.wiley.com/doi/pdf/10.1002/ar.23552));
  the hip JOINT's own rotation adds the femur's relative swing, putting the total
  in the ~10–15° band — with the honest caveat, from Winter's own text, that
  off-sagittal gait kinematics are "less well documented; accepted average values
  have yet to be established" ([Winter 1991, via ESEM primer](https://ndl.ethernet.edu.et/bitstream/123456789/36216/1/8.pdf)).
- **Envelope edge: ±8°** — the 15° total band's outer half, on the same logic the
  trunk used (the edge where the performed envelope ends and real tissue begins
  to engage), with Winter's caveat making the edge soft, not the construction.

### Hip adduction/abduction (frontal plane)

- **Passive/clinical ROM**: abduction 45–50°, adduction 20–30°
  ([Family Practice Notebook](https://fpnotebook.com/Ortho/Exam/HpRngOfMtn.htm);
  [Charles University goniometry](https://dspace.cuni.cz/bitstream/20.500.11956/180701/130355404.pdf)).
- **Gait, in vivo**: adducts at first double support, abducts at second
  ([Sutherland et al. 1994, via UGA thesis](https://openscholar.uga.edu/record/12044/files/chamnongkich_samatchai_200405_phd.pdf));
  peak hip adduction **8.8°** in healthy gait
  ([Goetschius et al., Frontiers 2025](https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2025.1546297/full));
  toe-in/toe-out perturbations move it only ±1–2.3°
  ([ApplSci 2019](https://mdpi-res.com/d_attachment/applsci/applsci-09-05245/article_deploy/applsci-09-05245.pdf?version=1575289520)).
- **Envelope edge: +9° adduction / −5° abduction** — the measured peak plus its
  perturbation band on the adduction side; the published abduction reach in gait
  is smaller, and the edge says so.

## NEXT

1. ~~Close the two open citations~~ DONE 2026-08-04 (Kadaba via Lewis for
   rotation, Goetschius for adduction; Winter's off-sagittal caveat carried).
2. Derive in `tools/world.py` — same `_derive_side` path the trunk used, each
   joint group's gap from the model's declared ranges; refusals named.
   (Build note: the hip-rotation edge is soft per Winter — if its derived k
   lands outside falsifier 3's band, the edge, not the band, is what moves,
   and the doc records which.)
3. Re-judge with `tools/f3_stand.py` (no retrain); record the verdict here.

---

## THE MODEL'S DECLARED RANGES — read 2026-08-04, before the build

From `external/myo_sim/leg/assets/myolegs_chain.xml` (r/l symmetric):

| joint | declared range | literature edge | gap |
|---|---|---|---|
| `subtalar_angle` | ±20.0° | ±9° | **11.0° each end** |
| `hip_rotation` | ±40.0° | ±8° | **32.0° each end** (wide — falsifier 3 watches this one) |
| `hip_adduction` | +30.0° / −50.0° | +9° / −5° | **21.0° / 45.0°** (which end is adduction is an axis-convention question — the build confirms it against `_derive_side`, not this table) |
| `mtp_angle` | ±30.0° | 65° dorsiflexion | **NONE — REFUSED, and the refusal is a finding** |

**The MTP refusal, stated plainly.** The published gait envelope needs ~60–65°
of MTP dorsiflexion at push-off; the model's declared stop is ±30°. The
literature edge falls OUTSIDE the model's declared range — the exact mirror of
the refusal the membrane named ("edge inside the range, no gap"). The
construction cannot run: a ligament derived as `gap = |limit − edge|` would
engage PAST the stop the physics already enforces. What the port contract
measured (`mtp_angle_l 1.10×` over stop) is therefore not missing tissue — it
is THE MODEL'S STOP CONTRADICTING PUBLISHED GAIT. The fix is a model-range
amendment (widen the MTP range toward the measured 65–110° passive band,
THEN derive the ligament across the new gap), which is a different membrane
touching the model itself, and is queued as such. Rule 20: not patched here.

---

## THE BUILD AND WHAT IT TAUGHT (2026-08-04)

**The sign table corrected by measurement.** Before deriving, the actuator
moments were read (`d.actuator_moment`, never assumed): hip_adduction's
POSITIVE side is loaded by glmed/glmin/tfl — the model's + end is ABduction,
inverting the table above's first-principles guess (the table flagged itself;
the measurement wins). Edges as built: lo = adduction −9°, hi = abduction
+5°. Subtalar + is eversion (peroneals), hip_rotation + is external
(piri/glmax) — symmetric edges, so the sign only matters for the record.

**The derivation** (`tools/world.py` OFFSAG block, trunk construction
unchanged): twelve ligaments, L/R symmetric to the tenth —

| joint | side | k (N·m/rad) | k (N·m/deg) |
|---|---|---|---|
| subtalar | eversion+ / inversion− | 333 / 243 | 5.8 / 4.2 |
| hip_rotation | external+ / internal− | 59 / 239 | 1.0 / 4.2 |
| hip_adduction | abduction+ / adduction− | 694 / 444 | 12.1 / 7.7 |

**Falsifier 3 does not fire:** every derived stiffness sits in the published
passive-stiffness band for its joint (1–12 N·m/deg, the same band as the
lumbar's measured 6–11).

**Falsifier 2 FIRED, and it taught an instrument defect first.** The
no-retrain re-judge FELL at t = 1.76 s. Diagnosis, measured not argued: the
keyframe carries `hip_rotation_r` at **−35.18°** — 27° past the −8° edge, a
gait frame's transverse rotation frozen into a stand — which is ~113 N·m of
taut spring at t = 0, the 689 N·m trap one level subtler (inside range, so
the range-clamp never saw it). Fix: off-sagittal keyframe joints are seated
to their published edges in `world.py`. The re-judge STILL fell (t = 2.10 s)
with the seating verified clean (−8.00° exactly). The regression is real:
the policy trained with those DOF free cannot stand against the new springs.
That is the trunk's own history repeating — FE ligament in, old policy,
19.3% — and its cure is the same: **retrain the stand with the tissue in**
(running as this is written). Two outcomes, both verdicts: the retrained
body stands → the ligaments are ligaments and the membrane's no-retrain
prediction was the error; it falls → the tissue is a wall and falsifier 2
stands as fired.
