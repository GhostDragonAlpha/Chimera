# rope_network_design.md — Lane R standing skeleton tension network

*2026-08-07. Body-plan frame only; no bone scaling. Integration with
LightEngine/skeleton_scaling.py (Lane S) is out of scope for this file.*

---

## 0. BODY-PLAN FRAME (independent of Lane S)

All coordinates are in a normalized standing frame:

- origin: midpoint between the ankle joint centers on the ground (`z = 0`).
- `+x`: anterior (forward).
- `+y`: left lateral.
- `+z`: superior.
- total standing height `H = 1.0`.
- whole-body COM: `(+0.020 H, 0, +0.550 H)` — slightly anterior to the ankle
  and roughly level with the sacral promontory / lower lumbar spine.

Joint-center estimates used for the COM-line argument:

| joint group | center (x, y, z) in H |
|---|---|
| ankle (talocrural) | `(0.000, +/-0.060, 0.040)` |
| knee | `(0.030, +/-0.070, 0.260)` |
| hip | `(0.040, +/-0.090, 0.530)` |
| L5-S1 ... L1-L2 | x from `+0.015` to `+0.020`, z from `0.600` to `0.740` |
| T12-L1 ... T1-T2 | x from `+0.010` to `-0.020`, z from `0.770` to `0.880` |
| C7-T1 ... C1-C2 | x from `-0.020` to `-0.020`, z from `0.895` to `0.940` |
| occipito-atlantal | `(-0.025, 0, 0.955)` |
| shoulder (glenohumeral) | `(0.020, +/-0.160, 0.820)` |
| foot arch keystone | `(0.020, +/-0.040, 0.025)` |
| pelvis arch keystone (sacral promontory) | `(-0.020, 0, 0.580)` |

The COM projection at `x = +0.020 H` is the single reference line used in
every antagonist argument below.

---

## 1. THE ROPE LAWS CITED BY EVERY ENTRY

Every rope in this network cites three settled laws:

1. **unique-stability** — theLeg v3 full-arc gate: a rope makes one pose the
   unique stable equilibrium only if it is taut on the loaded side of the
   reachable arc and can crumple on the unloaded side. The gate's refusal
   proved muscle-alone cannot hold; geometry + rope must do the work.
2. **no-prop** — theTendon v4 / theLeg v3: a rope is tension-only; when slack
   it folds/crumples and never routes compression. Each record names the
   slack direction that guarantees this.
3. **anchor-on-bone-end** — socket v1 law: joints capture by wrapping the
   bone's END. Therefore every rope anchors on the END region of its bone
   (epiphysis / metaphysis / process), never on a mid-shaft cylinder, so the
   bone end is already inside the cup before the rope loads.

---

## 2. PER-JOINT DESIGN

### 2.1 ANKLE PAIR (talocrural, left + right)

**Cup-capture rotation axes.** The talus is a rounded bone end wrapped by the
distal tibia + fibula malleoli. After the socket wraps the talus, the only
free motion is rotation about a medial-lateral axis (plantarflexion /
dorsiflexion). Inversion/eversion and translation are captured by the
malleolar cup.

**Standing compression load path.** Ground reaction → calcaneus + metatarsal
heads → talus → tibia → knee. The tibia presses DOWN on the talus; the talus
presses UP on the tibia. The ankle carries compression along its long axis.

**Minimal rope set.** Because the COM line (`x = +0.020`) is ANTERIOR to the
ankle center (`x = 0.000`), the tibia/whole body tends to rotate forward into
dorsiflexion. A posterior rope is required.

- `ankle_posterior_L`, `ankle_posterior_R` (Achilles / triceps surae analog):
  - anchor_a: posterior distal femur / posterior proximal tibia region.
  - anchor_b: posterior calcaneus.
  - line of pull: posterior-inferior from leg to heel.
  - kills_mode: forward-tip / dorsiflexion collapse of the ankle.
  - slack_direction: ankle plantarflexion (calcaneus moves anterior, distance
    between anchors shortens, rope folds into the popliteal/ posterior ankle
    space).
  - antagonist_of: `ankle_anterior_*`.

Because standing COM is only slightly anterior and real bipedal sway moves
the projection across the ankle axis, an anterior rope is also required for
unique stability of the standing equilibrium:

- `ankle_anterior_L`, `ankle_anterior_R` (tibialis anterior analog):
  - anchor_a: anterior distal tibia.
  - anchor_b: anterior tarsal / metatarsal base.
  - line of pull: anterior-inferior from shin to dorsal foot.
  - kills_mode: backward-tip / plantarflexion collapse.
  - slack_direction: ankle dorsiflexion (tibia moves anterior over talus,
    distance shortens, rope folds on the anterior ankle).
  - antagonist_of: `ankle_posterior_*`.

**Antagonist question.** YES — the ankle pair needs an anterior/posterior
antagonist pair. The COM line is only `0.020 H` anterior of the ankle axis;
standing sway moves the projection back and forth across the axis, so either
rope can be the loaded one. Neither may prop in the unloaded direction.

---

### 2.2 KNEE PAIR (tibiofemoral, left + right)

**Cup-capture rotation axes.** The femoral condyles are rounded bone ends
wrapped by the tibial plateau + meniscal/capsular cup. Free motion is flexion /
extension about a medial-lateral axis. The socket v1 wrap on the femoral
condyle ends locks anterior/posterior and medial/lateral translation.

**Standing compression load path.** Femur → tibial plateau → tibia. The femur
presses DOWN on the tibia; the tibia presses UP.

**Minimal rope set.** The COM line (`x = +0.020`) is POSTERIOR to the knee
center (`x = +0.030`). The femur therefore tends to roll backward into
hyperextension. A posterior rope is required.

- `knee_posterior_L`, `knee_posterior_R` (PCL + posterior capsule / hamstring
  analog):
  - anchor_a: posterior distal femur.
  - anchor_b: posterior proximal tibia.
  - line of pull: posterior, slightly inferior.
  - kills_mode: knee hyperextension / backward-collapse.
  - slack_direction: knee flexion (femoral condyles roll forward, posterior
    anchor distance shortens, rope folds into the popliteal fossa).
  - antagonist_of: `knee_anterior_*`.

To make the knee pose unique across the full reachable arc, an anterior rope
is included as the antagonist:

- `knee_anterior_L`, `knee_anterior_R` (quadriceps / patellar tendon analog):
  - anchor_a: anterior distal femur.
  - anchor_b: anterior proximal tibia / tibial tuberosity.
  - line of pull: anterior-inferior.
  - kills_mode: knee flexion / forward-collapse (sitting down).
  - slack_direction: knee extension (patellar tendon shortens, rope folds on
    the anterior knee).
  - antagonist_of: `knee_posterior_*`.

**Antagonist question.** NO for static standing; the COM line is clearly
posterior to the knee axis (`0.010 H` posterior), so the posterior rope is
loaded and the anterior rope slacks. The anterior rope is present only to
bound the opposite side of the arc, not because gravity tips the knee both
ways in the standing pose.

---

### 2.3 HIP PAIR (femoroacetabular, left + right)

**Cup-capture rotation axes.** The femoral head is a spherical bone end
wrapped by the acetabular cup. Free motion is tri-axial rotation, but for the
standing skeleton the relevant one is flexion / extension about a medial-
lateral axis. The acetabular rim wraps the head end, locking translation.

**Standing compression load path.** Pelvis (ilium) → acetabulum → femoral
head → femur. The pelvis presses DOWN through the acetabulum onto the femoral
head.

**Minimal rope set.** The COM line (`x = +0.020`) is POSTERIOR to the hip
center (`x = +0.040`). The trunk tends to fall backward, extending the hip.
An anterior rope is required.

- `hip_anterior_L`, `hip_anterior_R` (iliofemoral ligament / anterior capsule
  analog):
  - anchor_a: anterior inferior pelvis (iliopectineal / AIIS region).
  - anchor_b: anterior proximal femur (intertrochanteric line).
  - line of pull: anterior-inferior from pelvis to femur.
  - kills_mode: hip hyperextension / backward-collapse of the trunk.
  - slack_direction: hip flexion (femur swings forward, anterior anchor
    distance shortens, rope folds in the anterior hip).
  - antagonist_of: `hip_posterior_*`.

The posterior antagonist bounds the flexion side of the arc:

- `hip_posterior_L`, `hip_posterior_R` (ischiofemoral ligament / hamstring
  analog):
  - anchor_a: posterior ischium / ischial tuberosity.
  - anchor_b: posterior proximal femur.
  - line of pull: posterior-inferior.
  - kills_mode: hip flexion / forward-collapse.
  - slack_direction: hip extension.
  - antagonist_of: `hip_anterior_*`.

**Antagonist question.** NO for static standing; the COM line is posterior to
the hip axis, so the anterior rope is loaded and the posterior rope slacks.
The posterior rope is present only as an arc-boundary member.

---

### 2.4 LUMBAR INTERVERTEBRAL GROUP (L5-S1, L4-L5, L3-L4, L2-L3, L1-L2)

**Cup-capture rotation axes.** Each vertebral body end is wrapped by the cup
formed by the adjacent vertebral body + facet capsule. Free motion is
rotation about a medial-lateral axis (flexion / extension) plus small lateral
and rotational components guided by the facet joints. The cup wrap on the
vertebral end-plate locks translation.

**Standing compression load path.** Superior vertebra → inferior vertebra
through the vertebral bodies and discs. Each lumbar vertebra presses DOWN on
the one below it; the sacrum presses DOWN on the pelvis.

**Minimal rope set.** The COM line (`x = +0.020`) is ANTERIOR to the lumbar
vertebral-body centers (x from `+0.015` to `+0.020`, but the vertebral body
center is posterior to the spinous-process rope line and the overall trunk
mass is anterior). Each lumbar segment therefore tends to flex forward. One
posterior rope per level is required.

- `lumbar_posterior_1` ... `lumbar_posterior_5` (supraspinous / interspinous
  ligament analog, one per interspace):
  - anchor_a: spinous process of the inferior vertebra.
  - anchor_b: spinous process of the superior vertebra.
  - line of pull: posterior-superior along the spinous-process line.
  - kills_mode: lumbar flexion / forward-bending collapse of that segment.
  - slack_direction: lumbar extension (spinous processes separate, distance
    shortens, rope folds in the posterior gutter).
  - antagonist_of: None for static standing.

**Antagonist question.** NO for static standing; extension is bounded by
facet-joint compression (bone-on-bone stop) and by the natural lumbar
lordosis, not by an anterior rope. The COM line stays anterior to the lumbar
axis.

---

### 2.5 THORACIC INTERVERTEBRAL GROUP (T12-L1 through T1-T2)

**Cup-capture rotation axes.** Same as lumbar: vertebral end wrapped by the
cup of the adjacent vertebra + rib/ facet complex. Rotation about a medial-
lateral axis is the primary standing degree of freedom.

**Standing compression load path.** Each thoracic vertebra presses DOWN on
the one below; T1 presses DOWN on T2, etc. Ribs and sternum form a composite
compression cage around the heart/lungs but do not carry tension in the
standing load path.

**Minimal rope set.** The COM line (`x = +0.020`) is ANTERIOR to the thoracic
vertebral centers (x from `+0.010` down to `-0.020` at T1). The thoracic
kyphosis makes the spinous processes point posteriorly, so the COM is well
anterior of the functional axis. One posterior rope per thoracic interspace
is required.

- `thoracic_posterior_1` ... `thoracic_posterior_12`:
  - anchor_a: spinous process of the inferior vertebra.
  - anchor_b: spinous process of the superior vertebra.
  - line of pull: posterior-superior.
  - kills_mode: thoracic flexion / forward-bending collapse.
  - slack_direction: thoracic extension.
  - antagonist_of: None.

**Antagonist question.** NO for static standing; extension is bounded by
facet and rib-cage compression. The COM line remains anterior.

---

### 2.6 CERVICAL INTERVERTEBRAL GROUP + OCCIPITO-ATLANTAL (C7-T1, C6-C7,
C5-C6, C4-C5, C3-C4, C2-C3, C1-C2, C0-C1)

**Cup-capture rotation axes.** Vertebral end wrapped by adjacent cup; the
atlas wraps the occipital condyles (socket v1). Free motion is primarily
flexion / extension about a medial-lateral axis. C1-C2 has a unique rotation
component, but for the standing skeleton the sagittal degree of freedom is
the one that carries stability.

**Standing compression load path.** Skull → C1 → C2 → ... → C7 → T1. Each
vertebra presses DOWN on the one below.

**Minimal rope set.** The COM line (`x = +0.020`) is ANTERIOR to the cervical
and occipital centers (x around `-0.020`). The head and upper cervical column
tend to nod forward. One posterior rope per cervical interspace plus one
posterior rope from occiput to C1/C2 is required.

- `cervical_posterior_1` ... `cervical_posterior_7` for C7-T1 up to C1-C2:
  - anchor_a: spinous process of the inferior vertebra.
  - anchor_b: spinous process of the superior vertebra.
  - line of pull: posterior-superior.
  - kills_mode: cervical flexion / forward nod at that segment.
  - slack_direction: cervical extension.
  - antagonist_of: None.

- `skull_posterior` (ligamentum nuchae / posterior occipital membrane
  analog):
  - anchor_a: posterior spinous region of C2 / posterior atlas.
  - anchor_b: posterior occiput.
  - line of pull: posterior-superior.
  - kills_mode: skull forward nod / atlanto-occipital flexion collapse.
  - slack_direction: skull extension.
  - antagonist_of: None.

**Antagonist question.** NO for static standing; extension is bounded by the
anterior longitudinal ligament/capsule and by facet compression. The COM
line is anterior to the cervical column.

---

### 2.7 SHOULDER PAIR (glenohumeral, left + right)

**Cup-capture rotation axes.** The humeral head is a spherical bone end
wrapped by the glenoid cup. Free motion is tri-axial rotation; for standing
with arms at the side, the relevant motion is inferior translation /
adduction of the humerus.

**Standing compression load path.** Humeral head → inferior glenoid →
scapula → clavicle → sternum / ribs → spine. The hanging arm's weight is
carried in compression through the inferior glenoid, not by a rope.

**Minimal rope set.** Because the humeral-head COM is INFERIOR to the glenoid
center, the primary static instability is inferior dislocation (the head
slipping out the bottom of the cup). A superior rope is required to center
the head in the socket.

- `shoulder_superior_L`, `shoulder_superior_R` (supraspinatus / superior
  capsule analog):
  - anchor_a: superior scapula (supraspinous fossa / acromial region).
  - anchor_b: superior humeral head (greater tubercle).
  - line of pull: superior-medial from humerus to scapula.
  - kills_mode: inferior subluxation of the humeral head.
  - slack_direction: humeral abduction / elevation (distance shortens, rope
    folds in the subacromial space).
  - antagonist_of: None for static standing.

**Antagonist question.** NO for arms hanging at the side; gravity pulls the
humerus inferiorly, so only the superior rope is loaded. Dynamic abduction
would load an inferior axillary pouch rope, but that is outside the standing
pose.

**Honesty note.** The shoulder is listed in section 5 as a joint where a
rope-only solution is insufficient: the inferior glenoid rim must provide a
bone-on-bone compression stop to carry the arm's weight in the standing pose.
The superior rope only centers the head and prevents dislocation; it does not
carry the entire load.

---

### 2.8 FOOT ARCH PAIR (longitudinal arch, left + right)

**Compression geometry.** The foot arch is not a joint with free rotation;
it is a compression arch. The calcaneus and metatarsal heads are the two
abutments; the talus / navicular / cuneiforms form the keystone. Ground
reaction presses UP on calcaneus and metatarsals; the keystone presses DOWN.

**Standing compression load path.** Tibia → talus → navicular → cuneiforms →
metatarsals → ground. The arch carries compression along the bony arch.

**Minimal rope set.** The arch tends to FLATTEN under body weight (keystone
depresses, abutments spread). A plantar tension member is required.

- `foot_arch_plantar_L`, `foot_arch_plantar_R` (plantar fascia analog):
  - anchor_a: plantar-posterior calcaneus.
  - anchor_b: plantar heads of the metatarsals.
  - line of pull: anterior-inferior from heel to ball of foot.
  - kills_mode: arch flattening / talar depression.
  - slack_direction: arch rising / supination (calcaneus and metatarsals move
    closer, distance shortens, rope folds on the plantar surface).
  - antagonist_of: None.

**Antagonist question.** NO for standing; gravity only flattens the arch.

---

### 2.9 PELVIS ARCH

**Compression geometry.** The pelvis is a bony arch: the two ilia are the
springers, the femoral heads are the abutments, and the sacrum is the
keystone. There is no free rotation; the sacrum is wedged between the ilia.

**Standing compression load path.** Spine → sacrum → ilium → acetabulum →
femoral head → femur. The sacrum presses DOWN and OUT into the ilia; the ilia
press INWARD on the sacrum and DOWN into the femurs.

**Minimal rope set.** The sacrum tends to NUTATE under spinal load
(promontory moves anterior/inferior, coccyx moves posterior). Posterior
sacroiliac ligaments resist this.

- `pelvis_arch_posterior_L`, `pelvis_arch_posterior_R` (posterior
  sacroiliac ligament analog):
  - anchor_a: posterior ilium.
  - anchor_b: posterior sacrum (lateral sacral crest).
  - line of pull: posterior-medial from ilium to sacrum.
  - kills_mode: sacral nutation / pelvic arch opening anteriorly.
  - slack_direction: sacral counternutation (posterior sacrum moves away from
    ilium, distance shortens, rope folds in the posterior pelvis).
  - antagonist_of: None.

**Antagonist question.** NO for standing; spinal load consistently drives
sacral nutation. Anterior shear is resisted by the interlocking sacroiliac
joint surfaces (compression geometry), not by an anterior rope.

---

### 2.10 SKULL SUTURE CASE

**Compression geometry.** Adult cranial sutures are interlocking compression
joints between flat skull bones. They are not motion joints and they carry no
appreciable tension in standing.

**Standing compression load path.** The skull is a dome; its own weight is
small compared to the rest of the body and is carried in compression through
the cranial base to the occipital condyles → atlas → axis.

**Minimal rope set.** NONE across the sutures. The skull suture case does not
need a rope. The head-on-neck stability is handled by the cervical posterior
ropes (section 2.6).

**Antagonist question.** Not applicable.

---

## 3. SUMMARY TABLE

| joint group | loaded rope side in standing | antagonist pair? | rope count |
|---|---|---|---|
| ankle pair | posterior | YES | 4 |
| knee pair | posterior | NO | 4 |
| hip pair | anterior | NO | 4 |
| lumbar group | posterior | NO | 5 |
| thoracic group | posterior | NO | 12 |
| cervical + occipital group | posterior | NO | 8 |
| shoulder pair | superior | NO | 2 |
| foot arch pair | plantar | NO | 2 |
| pelvis arch | posterior | NO | 2 |
| skull suture | — | NO | 0 |
| **TOTAL** | | | **43** |

---

## 4. JOINTS WHERE ROPE-ONLY FAILED AND COMPRESSION GEOMETRY WAS REQUIRED

Honest list:

1. **Knee pair.** A posterior rope prevents hyperextension, but the real
   stable end-stop is the posterior femoral condyle contacting the posterior
   tibial plateau / meniscus. Without that bone-on-bone stop, the rope would
   be the only limit and would have to carry the full body-weight moment in
   the terminal degrees of extension. The rope is therefore supplemented by a
   derived extension stop (socket v1 wrap plus posterior condyle contact).

2. **Hip pair.** An anterior rope prevents hip hyperextension, but the final
   end-stop is the anterior rim of the acetabulum contacting the femoral
   neck. The iliofemoral ligament rope is the primary check; the acetabular
   rim is the compression backup.

3. **Ankle pair.** A posterior rope prevents dorsiflexion collapse, but the
   talar dome geometry and the anterior tibial plafond provide the terminal
   dorsiflexion stop. The anterior rope prevents plantarflexion collapse, and
   the calcaneus contacting the posterior tibia / posterior malleoli provides
   the plantarflexion stop.

4. **Every intervertebral joint (lumbar/thoracic/cervical).** A posterior
   rope prevents forward flexion, but extension and axial rotation are
   bounded by facet-joint compression. The facet joints are the compression
   geometry that closes the arc; the posterior ligament rope is the tension
   member that prevents flexion.

5. **Shoulder pair.** A superior rope prevents inferior dislocation, but the
   arm's weight in standing is carried primarily by the humeral head resting
   on the inferior glenoid — a bone-on-bone compression stop. The rope is a
   centering member, not the primary load path.

6. **Pelvis arch.** Posterior sacroiliac ropes resist nutation, but the final
   shear stop is the interlocking sacroiliac joint surface (compression
   geometry).

7. **Foot arch.** Plantar fascia ropes resist flattening, but the bony
   keystone (talus/navicular/cuneiform) contacting the calcaneus and
   metatarsals provides the compression path; the rope carries the tensile
   component of the arch thrust.

---

## 5. UNIQUE-STABILITY ARGUMENT, ONE LINE PER JOINT

- **ankle:** COM anterior to talocrural axis → posterior calf rope taut,
  anterior shin rope slack; sway crosses the axis, so both are present.
- **knee:** COM posterior to tibiofemoral axis → posterior rope taut,
  anterior rope slack.
- **hip:** COM posterior to femoroacetabular axis → anterior iliofemoral rope
  taut, posterior rope slack.
- **lumbar:** COM anterior to each vertebral axis → posterior supraspinous
  rope taut at every level.
- **thoracic:** COM anterior to the kyphotic column → posterior supraspinous
  rope taut at every level.
- **cervical + occipital:** COM anterior to the cervical column and skull →
  posterior ligamentum-nuchae / spinous ropes taut.
- **shoulder:** humeral-head COM inferior to glenoid → superior rope taut to
  center the head in the cup.
- **foot arch:** body weight flattens the longitudinal arch → plantar fascia
  taut.
- **pelvis arch:** spinal load nutates the sacrum → posterior sacroiliac
  ropes taut.
- **skull suture:** cranial dome is self-stable in compression; no rope is
  loaded in standing.
