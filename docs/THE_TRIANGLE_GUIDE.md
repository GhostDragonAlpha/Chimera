# THE TRIANGLE GUIDE — how to work with triangles in this system

Written 2026-08-28 after the L6 hinge night: a torn leg was diagnosed, a knee
axis was re-derived, the skin was made to move, and the renderer was made to
stream — each step after a visible failure. This guide is for agents less
advanced than the one that did that work. Every law here names the failure
that taught it. Do not skip the failures: the law without the failure reads
like a suggestion, and it is not one.

The files named are real and current: the set builder `.tmp/tri_hinge2.py`,
the report `agent_logs/kimi/leg_fix_01.md`, the membrane
`docs/THE_ARTISTS_SOLID.md` (L6 section), the method
`docs/THE_MASTER_LIST.md` §11, the engine `ChimeraEngine/engine/`.

---

## 0 · The mental model (read until you can recite it)

- A mesh is a list of triangles. Each triangle is a **cell**. Its center is
  its Cartesian address. The **dual graph** is the adjacency: two triangles
  are neighbors iff they share an edge. Almost everything you do with a mesh
  in this system is a walk on that graph.
- **Welded twins**: two vertex *indices* can sit at the *exact same position*
  (split seams, shell attachments, birth-repair patches). The index graph does
  not connect them. The **welded graph** does. If your algorithm walks
  adjacency, decide which graph it walks — the wrong choice is the #1 bug
  source in this system.
- A deformation is an assignment: which triangles move, how, and how the
  motion dies out with distance. Every visible artifact is a wrong answer to
  one of those three questions.

## 1 · The set-building law — GEODESIC, never spatial windows

**Failure:** a "leg shell" cut by a coordinate window (a slab around the knee
axis) caught 179 triangles of thigh up to the hip. Rigidly rotating that set
swung thigh skin off the pelvis — the operator's screenshot showed a ribbon of
shredded skin where a leg should be.

**Law:** a region of the body is a **flood on the dual graph from anatomical
seeds**, never a box/cylinder/slab in space. Seeds = triangles touching the
relevant bone-rod endpoints. Assignment = weighted Dijkstra Voronoi (nearest
seed wins, ties frozen). Spatial windows fail because the pose is never
symmetric to your axes — a crouch puts an arm where your window expects a leg.

**How:** see `build_set` in `.tmp/tri_hinge2.py`. Cross-check the result
against any known-good set (ours matched the repaired reference with symmetric
difference 0). Acceptance must include: component list, nothing above the
joint's parent joint, boundary loop at the expected height.

## 2 · The weld law — scan ALL weld groups, always

**Failure:** weld group 5080 — two vertex indices at the identical rest
position at the inner knee, one side rotating, one frozen. The set builder's
weld scan only looked at *boundary edges* of the index graph; a coincident
seam has no index edge, so the scan was blind. The knee opened a 1.2 cm slit
on the first bend.

**Law:** after any set assignment, compute the split-weld-group count over
**every** weld group in the mesh: a group is split iff some member vertex
feeds moving triangles and another feeds frozen ones. Drive it to zero
(promote the frozen side's triangles, iterate to fixpoint). "The boundary
looks clean" is not a substitute — twins are invisible until they move.

## 3 · The axis law — re-measure ill-conditioned quantities stably

**Failure:** the knee axes were fit from bone directions — but at rest the
tibia and femur point the same way, so the fit was noise. The right axis spent
0.74 of its unit length pointing *sideways*: the shin swung out like a hacky
sack. It measured "correct" by its own test and looked wrong to any human.

**Law:** when a fit is ill-conditioned, find a **different measurement of the
same anatomical quantity** that is well-conditioned. For a knee: the
inter-knee line (`normalize(J_right − J_left)` from the derived joint centers)
— knees are hinges on one transverse line. Get the **sign** from anatomy, not
convention: flexion moves the foot *posterior*, and posterior is measured
(eye-socket centroid = anterior; tail = posterior). A test that passes on a
noisy measurement proves nothing; the operator's eye is the terminal.

## 4 · The skin-moving law — many triangles make the radius

**Failures, in order:** (a) rigid set + frozen skin → spike triangles at the
boundary (they stretch 28×). (b) Hiding the spikes → holes: "not watertight
anymore." (c) Absorbing the spike strip into the rigid set → the knee became a
rigid block: "messed up the look." (d) A blend whose weights couldn't cross
welded seams → "everything is disconnected." (e) A blend with a 42-hop falloff
→ the belly swung with the shin.

**Law (the operator stated it first):** *"when I bend my knee, a ball forms —
it's round — you have to use many triangles to make the radius."* Every vertex
near the joint rotates by `θ·w_i` about the measured joint center, with
`w = clip(1 − d_to_set / R, 0, 1)`: full weight inside the control set,
fading to zero over a **local** radius. R is not a knob: it is the joint's own
measured extent (ours is 0.3, the recorded ring-band slab half-width). Draw
**all** triangles. Distance-to-set is computed against set *vertices*
(cKDTree), which crosses welded seams for free — no disconnection.

## 5 · The streaming law — never idle the GPU, never steal the camera

**Failures:** rotation died while animating (twice, for two different
reasons), and motion stuttered.

**Laws:**
- The animation driver posts **vertex updates into a persistently mapped,
  host-visible vertex buffer** (`Engine::update_mesh` — memcpy only). A full
  re-upload with `vkDeviceWaitIdle` per frame blocks the render thread on the
  GPU queue; at 12 posts/s the operator's mouse starved. First post = full
  load; every later post = update (`/mesh_bin` slotmode ≥ 100).
- **Never set the camera from a driver.** `cam_radius ≤ 0` means keep the
  operator's camera. The operator orbits while it moves; that is the point.
- **Drain the whole OS message queue per frame**, not one message — one-per-
  frame starves input at any render rate below the input rate.
- Sync updates with the previous frame's **fence**, never device-idle.

## 6 · Verification — measure, then look with your own eyes

- **Classify before solving**: color the sets (rigid/ring/free/pinned) and
  render the rest pose. What the machine thinks the sets are is usually the
  bug.
- **The stretch metric**: deform, compute per-triangle edge-length ratio vs
  rest. Anything ≫1 near the joint is a spike waiting to be seen. Measure it
  before the operator sees it.
- **TORN-SHEET**: on the welded graph, the free skin's component count must
  not grow, and no weld group may split, at any sweep step.
- **Synthetic input test**: post synthetic mouse drags to the window and diff
  the pixels (`/tmp/input_test.py`). "Input feels dead" is a measurable fact.
- **The placebo trap**: a check that silently no-ops is worse than none — our
  "F1 = 0 self-intersections" was a `hasattr` guard that never measured
  anything. Run your check against a case that MUST fail, once, to prove it
  can fail.
- **Dyad discipline**: one picture per call, one report per picture. Batch
  frames and the vision model averages away exactly the minute defect you are
  hunting.
- View every render you ship a claim about. A number is not a look.

## 7 · Honest negatives — the win and the caveat ship together

Record, in the same breath as the result: what is still stubbed (the ARAP
skin), what was measured about a superseded quantity (the ROM limits were
swept about the old tilted axes — re-sweep is open), what the mesh itself
carries (1,461 pre-existing rest intersections in the recon soup), and every
retracted experiment with the reason. The next agent — maybe a less advanced
one — inherits your pathway only if the negative space is mapped.

---

## The short version

1. Regions are graph floods from anatomy, never spatial windows.
2. Weld twins split invisibly; scan them all.
3. Re-measure noisy fits against a stable proxy; sign from anatomy.
4. The fold is many triangles rotating by a local falloff — a ball, not a
   crease. Hide nothing.
5. Stream vertices through a mapped buffer; never idle the GPU; never touch
   the operator's camera.
6. Prove checks can fail; view your renders; one picture per dyad call.
7. Ship the honest negative with the win.
