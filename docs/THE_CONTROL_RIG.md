# THE CONTROL RIG — two triangle populations; every triangle has a bone

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY MEMBRANE IS A THEORY. STATE IT BEFORE YOU BUILD IT.** Three parts, all three
> required: a **STATEMENT** someone could disagree with · a **PREDICTION** you have not measured
> yet · a **FALSIFIER** named *before* the run. **A description survives any result; a theory can
> lose.** No falsifier, no build.
>
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
<!-- CHIMERA-LAW -->

*2026-08-25. Captured from the operator before any build. Provenance: operator words this session,
recorded where quoted; synthesis from repo machinery is flagged. This is the law the rigging lane
is judged against. It POINTS at existing machinery — it does not duplicate it.*

---

## THE OPERATOR'S THEORY, in his words

*"The movement input and control system is just a series of triangles which drive the outer shell
of the item, which is another set of triangles. The control triangles run the visual triangles.*
*The visual triangles, each one will have its own rules based on what it needs to do. So everything,
even static objects, will have control rigs. These control and give rules to the triangles they are
assigned to — essentially, which bones they're assigned to.*
*Every triangle has a bone, and that bone determines how that triangle operates. (I do believe
there are several bones in the human knee, as a metaphor.)*"

And on the ideal: *"You could create a perfect representation of the human skeleton and provide
muscles and everything; that would be the ultimate ideal. But we have a teddy-bear in-between
version, where all the muscles and fibers are just triangles working together, providing force
within a volume of space that the triangle is representing, broken down by membranes."*

And on sampling: *"You just have to have the mesh be the way you want it to be in every position —
or at least pick a certain number of positions that covers the entire visual range (relative to
pixel size). Everything's basically a morphable lattice, like a crane that moves. Think about the
surface area of skin relative to points on the skin: when you bend your knee, the skin on the front
kind of stretches. All of that can be learned through shape analysis."*

---

## THE TWO POPULATIONS (STATEMENT)

One lattice, two roles. Both are triangles; both obey the same one-algorithm physics
(`docs/THE_LIGHT_SEED.md` — DRAW + RESISTANCE). The distinction is *what reads them*:

| population | what it is | physics it runs | maps to |
|---|---|---|---|
| **CONTROL triangles** | the rig inside the volume: **bones** (rigid assemblies) + **muscles/fibers** (force-providing springs spanning bones) | bond law between control elements; bones are locked-packet rigid frames per `THE_TRANSLATION.md` law 4 ("truly rigid parts may lock their packets to one frame") — a material property, never a mode | the "muscles and fibers … providing force within a volume" |
| **VISUAL triangles** | the outer shell — the existing triangle carrier (`docs/THE_TRIANGLE_CARRIER.md`: area + bending + curvature springs) | surface CA + **the rule of its bone** | the skin, fur, the thing light reads |

**EVERY TRIANGLE HAS A BONE.** The assignment table (visual triangle → bone) is the lattice's
skinning: each visual triangle's rule comes from the control assembly it is assigned to. Boundary
triangles assigned across bones are why knee skin CREASES instead of tearing — the surface CA
absorbs the bones' relative motion.

**Even static objects have control rigs.** A rock's crystal lattice IS its control rig
(`docs/THE_COMPILER.md` passive-tissue table). Static = the degenerate one-bone case: same code
path, no special cases.

**The ROM lives in the control layer.** Joint limits are control-triangle springs between bones
(the ligaments): rest length = the ROM slider, stiffness = the stop's resistance, slack through the
motion the body performs (`tools/world.py::derive_ligaments` precedent). The visual shell never
sees the joint directly — it follows its bone assignments and lets its own surface CA handle the
look. Control does joints and forces; visual does surface and look.

## THE KNEE (the worked example)

Several bones cooperate at one joint — femur, tibia, patella — exactly as the operator's metaphor
states. The mechanisms, all readers of the one field (no new force system):

1. **Ligaments** = control-layer springs across the joint. Rest length defines the ROM boundary
   (the operator's two states: fully bent / max hyperextension); stiffness defines the stop.
   Slack in between. THE ROM SLIDERS ARE THESE REST LENGTHS, literally.
2. **Bones** = stiff inclusions (high K_BOND regions). Compression crosses the joint bone-to-bone;
   rotation within ROM is nearly free. The biphasic knee: stiff in compression, free in flexion.
3. **Contact** = saturated-density contact (`docs/THE_TWO_FORCES.md` Stage 8 v2 — proven, seam
   1.2 nm, not yet wired into this loop). At max flexion the calf meets the thigh; tissue
   compresses by the contact law. No authored stop, no clip-through.
4. **The look** = the visual shell draping over the structure. A stiff patella-like inclusion
   makes the soft shell crease WHERE ANATOMY PUTS IT. Uniform stiffness bends a smooth noodle
   (wrong); bone + patella + soft flesh distribution creases correctly (right).

## THE POSE-MORPH SYSTEM (the second system that applies)

The CA is the consistency engine; a second system applies it. **Runtime does not integrate
dynamics for the look — it samples.**

- **The parameter:** one scalar per joint — foot position relative to butt. "One triangle
  represents the entire actuation": one handle drives the lattice.
- **The keypose set:** N poses covering the visual range, N set by PIXEL SIZE — adjacent poses
  differ by less than a pixel, so interpolation between them is visually exact. (~100–150 poses
  for a knee sweeping ~200 px through ~145°.)
- **Pose generation (offline, no frame budget):** impose the bone rotation for angle θᵢ; let the
  CA surface springs relax the visual shell around it; settle; save mesh + per-triangle strain
  field.
- **Runtime:** lattice morph between adjacent keyposes (the crane that moves). The CA runs as a
  READER only — one cheap pass evaluating the blended shape's strain field, driving skin-stress
  appearance and fur behavior.
- **The training data:** the per-pose strain field IS the shape analysis — front stretches (+),
  back folds (−), magnitude per angle. Reference imagery can correct poses later; the CA's own
  strain measurements are the first dataset.

### The CA functions and their jobs at the joint

| CA function (built in `tools/ca_triangle.py`) | measures/enforces | job at the knee |
|---|---|---|
| Area mode (`A/A₀` per triangle) | skin stretch per patch | front +, back −; the strain field is the skin behavior |
| Bending mode (dihedral springs) | where folding concentrates | puts the crease at the knee line |
| Volume mode (`V/V₀`) | limb keeps its bulk | bent leg doesn't deflate |
| Curvature mode (rest mean curvature) | smooth drape | surface wraps the joint cleanly |
| DRAW walk (gravity) | tissue sag | each pose settles under its weight — OFFLINE only |
| Contact (Stage 8 v2) | hard stop | calf-thigh at max flexion |

## THE BEAR REBUILD (text-to-3D pipeline)

The bear will be redone per-part with rigging from the start: **thigh and shin as separate
watertight shells that meet at a proper knee** (`cad_sample.load_glb_triangles` requires
watertight per-part shells for the volume/inside tests). Local text-to-3D gives part-level
control. Control rigs are lattice-native — generated inside the volume, never seen, only felt.
The first bear will probably have to be TRAINED (the operator's words).

Repo inventory (2026-08-25): a full TRELLIS C++ tree exists (`.tmp/trellis-cpp-src` — app,
models, src, thirdparty), and prior generation attempts: `models/genbear`, `genbear2`,
`genbear3`, `littlebear`, `teddyloop`, `trellis`. "Maybe we already have something" — being
verified. 2D-to-3D was tried and "kind of sucked" (operator); text-to-3D preferred for part
control.

---

## MEMBRANES (Rule 0) — named before build

### MEMBRANE R1 — the keypose library + strain signature

- **STATEMENT:** Imposing a bone rotation θ on the bear's leg and relaxing the visual shell with
  the CA surface springs (area + bend + curvature, k derived from K_BOND) produces a settled pose
  whose per-triangle strain field shows the knee signature: front-of-knee triangles +strain
  (stretch), back-of-knee triangles −strain (fold), magnitude growing with θ.
- **PREDICTION:** Over ~24 sampled angles spanning the ROM, the mean signed strain of front
  region vs back region has opposite signs at every θ, and |mean strain| grows monotonically with
  θ. The relaxation settles (finite, energy-bounded) for every θ in the range.
- **FALSIFIER:** front and back strain same sign at any θ; non-monotonic growth with no physical
  explanation; any non-finite settle. One firing ends this construction; successor = explicit
  skin-attachment constraints (surface pinned to bone at named anchor triangles).

### MEMBRANE R2 — the bend, rendered and judged

- **STATEMENT:** The keypose sequence, uploaded per-frame to the C++ triangle pipeline
  (`/mesh_bin`, already verified at 0.8 for the static bear), renders as a knee-bend movie that a
  blind dyad recognizes as "a knee bending" with the stretch on the correct side.
- **PREDICTION:** dyad alignment ≥ 0.7 on "does this look like a knee bending" over the sampled
  sequence; the morph between adjacent keyposes is visually continuous (no pops) because poses
  are sampled below pixel resolution.
- **FALSIFIER:** alignment < 0.5; visible popping between adjacent poses (sampling too coarse —
  refine N, do not tune the render); render fails to reflect pose changes.

### MEMBRANE R3 — text-to-3D per-part bear

- **STATEMENT:** A locally-run text-to-3D model generates teddy-bear parts (thigh, shin, foot) as
  separate watertight shells that assemble into a bear whose knee works: two shells meeting at a
  joint with room for a control rig between them.
- **PREDICTION:** generated parts pass the existing import chain (`load_glb_triangles`:
  watertight, per-part, clean topology for shared-edge adjacency) and assemble at the knee with
  matched interface geometry within a named tolerance.
- **FALSIFIER:** non-watertight output; topology unusable by the lattice (unbounded vertex
  duplication); interface mismatch beyond tolerance. Successor named in advance: retopology pass
  (mesh → clean lattice) before import, as its own membrane.

## BUILD ORDER

1. **R1** keypose library + strain signature (uses existing CA functions unmodified — wrapper only)
2. **R2** bend movie through the C++ engine + dyad
3. Text-to-3D inventory → research → pick model → **R3** per-part bear
4. Control-rig layer: bone assignment table + ligament springs in the CA tick (new plumbing, no
   new physics) — membrane to be written before that build
5. Contact wiring (Stage 8 v2 into the tick loop) — membrane to be written before that build
6. Training: dyad alignment → parameter search over K_BOND distribution + ligament rest lengths
