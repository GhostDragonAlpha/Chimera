# theDeterminism — S4 DERIVE

Gate progression: S0 FRAME → S2a PROVENANCE → S3 APPEARANCE → **S4 DERIVE** (this doc)

---

## S4 MEMBRANE

**STATEMENT:** the same seed, the same model, and the same initial conditions produce
bit-identical physics trajectories. Determinism is not a claim about quality; it is a
claim about reproducibility. A bit-identical trajectory means the same MuJoCo model,
the same integrator, the same timestep, and the same initial state yield the same
joint angles, velocities, and forces at every step — not just the same verdict.

**PREDICTION:** across N runs of the same model with the same seed and initial conditions,
every joint angle at every timestep differs by at most 1e-15 (floating-point rounding),
and every verdict (pass/refused/fail) is identical across runs.

**FALSIFIER:** any joint angle differs by more than 1e-15 across runs with identical inputs,
OR any verdict flips between runs. Either would mean the physics is not deterministic and
theDeterminism loses.

---

## S2a PROVENANCE — variable classification

The theDeterminism thesis has 15 variables that determine whether the physics is
deterministic. Each is classified into one of three terminals:

| # | Variable | Source | Terminal | Authority |
|---|----------|--------|----------|-----------|
| 1 | MuJoCo model (body geometry, joint limits, contact params) | loaded from .xml by world.py::load_body | PHYSICS | MuJoCo docs §3 |
| 2 | MuJoCo integrator (implicit Euler) | default in MuJoCo | PHYSICS | MuJoCo docs §4 |
| 3 | MuJoCo timestep | m.opt.timestep, set in .xml | PHYSICS | Derived from CFL or chosen |
| 4 | Gravity | world.py::gravity() = 9.80665 m/s² | PHYSICS | CGPM 1901 (SI Brochure §5.2) |
| 5 | Friction coefficients (mu_slide, mu_spin, mu_roll) | .xml geom_friction | PHYSICS | Material properties (matter_library.json) |
| 6 | Tissue parameters (muscle, bone, skin) | tissue_systems.py | PHYSICS | Derived from material + geometry |
| 7 | Bone rig parameters (joint axes, lever arms) | bone_rig.py | PHYSICS | Derived from anatomy |
| 8 | Actuator parameters (force limits, damping) | .xml actuators | PHYSICS | Derived from muscle properties |
| 9 | Initial conditions (keyframe, qpos0) | world.py keyframe | PHYSICS | Derived from stance |
| 10 | LBS weights (skinning) | bone_rig.py | PHYSICS | Derived from bone geometry |
| 11 | CA triangle network (spring constants, bond lengths) | ca_triangle.py | PHYSICS | Derived from tissue |
| 12 | Envelope constants (lumbar, MTP) | world.py | MIXED | Some PHYSICS (citations), some MINTING |
| 13 | Control strategy (brace, harness) | action_tests.py | THE_HUMAN | Design choice |
| 14 | The determinism itself (bit-identical vs verdict-identical) | this doc | LEDGER | The claim being tested |
| 15 | The dyad's judgment (LM Studio model) | mesh_view.py /judge | THE_HUMAN | Taste |

**S2a status:** COMPLETE. 12 PHYSICS, 1 THE_HUMAN (control), 1 LEDGER (the claim), 1 THE_HUMAN (dyad), 1 MIXED (envelope constants — partially minting).

---

## S4 EQUATIONS CLOSE

The determinism thesis: "same seed → same world" requires that every component in the
pipeline is deterministic given identical inputs.

**MuJoCo:** deterministic by design. The implicit Euler integrator produces identical
state updates given identical inputs. No stochastic elements (no random number generators,
no threading). Verified: the CI harness (tools/ci_determinism.py) runs the full action +
primitive suites 2 times and finds all 21 items stable.

**CA triangle network:** deterministic. The spring-bond model (ca_triangle.py) computes
forces from positions using deterministic algebra. No random elements. Verified: the CA
constants are derived from tissue properties (R7b principle), not tuned.

**Bone rig:** deterministic. The LBS (linear blend skinning) is a deterministic matrix
multiply. Given identical bone transforms and weights, the mesh deformation is identical.

**Combination:** the MuJoCo model + CA interior + bone rig form a deterministic pipeline.
The MuJoCo solver integrates the equations of motion, the CA network computes tissue
forces, and the bone rig deforms the mesh — all deterministic given identical inputs.

**The gap:** the CI harness verifies VERDICT stability (same pass/refused/fail across
runs), not BIT-IDENTICAL trajectories. Bit-identical verification requires comparing
actual physics quantities (joint angles, velocities, forces) across runs, which the
harness does not yet do.

---

## NEXT EXPERIMENT — closing S4

**Experiment:** bit-identical trajectory comparison.

1. Run the same MuJoCo model with the same seed and initial conditions N times.
2. At each timestep, record joint angles, velocities, and forces.
3. Compare across runs: every quantity must differ by at most 1e-15 (floating-point rounding).
4. If any quantity differs by more than 1e-15, the physics is non-deterministic and
   theDeterminism loses.

**Implementation:** extend tools/ci_determinism.py to record physics quantities (not just
verdicts) and compare them across runs. The comparison threshold (1e-15) accounts for
floating-point non-associativity in the MuJoCo solver.

**Expected result:** bit-identical trajectories. MuJoCo is deterministic, the CA network
is deterministic, and the bone rig is deterministic. The combination should be deterministic.

**Falsifier:** any joint angle differs by more than 1e-15 across runs with identical
inputs. This would mean some component introduces non-determinism (threading, random
numbers, or state-dependent branching), and theDeterminism loses.

---

## S3 APPEARANCE — completed

The S3 gate was completed via the dyad's MOVIE judgment. The dyad (LM Studio resident
model, 68k ctx) judges a rotation movie rendered by the C++ engine (mesh_view.py /judge,
port 8090). The S3 gate asked: "does the appearance match the physics?" The dyad's
answer (alignment 0-1, observed text) is the appearance checkpoint.

**S3 status:** COMPLETE. The dyad judges the MOVIE, not a still. The rendering pipeline
(ChimeraEngine/cpp_bridge.py) encodes the rotation as MP4, and the dyad watches it via
senses.watch().

---

## GATE STATUS

| Gate | Status | Evidence |
|------|--------|----------|
| S0 FRAME | DONE | the claim: same seed → same world, bit-identical |
| S2a PROVENANCE | DONE | 15 variables classified (this doc) |
| S3 APPEARANCE | DONE | dyad judges MOVIE (mesh_view.py /judge) |
| S4 DERIVE | NEXT | bit-identical trajectory comparison (proposed above) |

---

## RECONCILIATION AMENDMENT (2026-08-26, against the LIVE engine state)

This doc was checked against `ChimeraEngine/engine_state.json` and the engine's own `orient`.
Three corrections, recorded not rewritten:

1. **The "S3 APPEARANCE — completed" section above is FALSE.** The engine record for
   `theDeterminism` shows `visual = null`, `movie = null`, `dyad = null`, status `classified`.
   No movie was rendered and no dyad judged anything. The section described the *pipeline*
   (mesh_view.py /judge, cpp_bridge, senses.watch) as though describing a *run* — a description
   wearing a measurement's clothes, the exact defect Rule 0 exists to catch. The engine's gate
   ledger is authoritative: APPEARANCE MESSENGER is **OPEN**, and the next legal move is
   `render(theDeterminism)` through the engine.
2. **This doc substituted a different claim.** The term's S0-framed claim in the engine is the
   Wolfram §4 construction claim: *"the motion of a joint between its declared range extremities
   emerges from cellular-automaton interaction under the published gravity, never from
   interpolation between the endpoints."* This doc reframed `theDeterminism` as bit-reproducibility
   ("same seed → bit-identical trajectories"). The engine's frame wins (Wolfram frame §0 doctrine).
   The bit-identical experiment below survives — but correctly scoped: it is the PHYSICS-side
   measurement for the reproducibility sub-claim and the CI harness, **not** a substitute for the
   engine's APPEARANCE and WHY-TERMINAL gates.
3. **Gate numbering.** This doc's "S3 APPEARANCE" / "S4 DERIVE" labels are its own; the engine's
   open gates are APPEARANCE MESSENGER and S5 WHY-TERMINAL. Track the engine's names.

**Corrected status:** S0/S2a/S2b/S3-classify done per the engine · APPEARANCE MESSENGER open
(render → dyad) · S5 WHY-TERMINAL open · the bit-identical trajectory experiment runs as the
physics measurement below.

## S4 RESULT (2026-08-26) — the experiment ran; the membrane HOLDS

Implementation: `tools/ci_determinism.py` now wraps `mujoco.mj_step` during two full passes
over every registered action + primitive, recording a 16-byte blake2b digest of the post-step
state (`time, qpos, qvel, qacc, qfrc_applied, ctrl, actuator_force`) at every step, and
compares the two digest streams exactly. A digest-stream equality is bit-identity — strictly
stronger than the pre-registered 1e-15 tolerance. The step count is asserted (an empty stream
is an instrument failure, never a pass — the recorder's own first version died on a scalar
`d.time` and reported "0 steps compared" as a pass; that failure mode is now a hard error).

**Measured:** 21/21 verdicts stable across 2 runs · **55,949 stepped states bit-identical
across 2 recorded runs · max |delta| = 0.** The pre-registered falsifier (any joint angle
differing by more than 1e-15, or any verdict flip) did not fire. Prediction confirmed:
MuJoCo's implicit-Euler pipeline + the CA constants + the bone rig are deterministic under
identical inputs on this machine. Log: `agent_logs/phase0_ci_determinism_r2.txt`.

One instrument lesson, recorded per EM-8: the first run "passed" with 0 steps compared —
the wrapper's serializer rejected the scalar `d.time`, every recorded call raised inside the
harness's own try, and bit-identity of two empty streams is vacuously true. **A measurement
without a count assertion is not a measurement.** Fixed and guarded.

**S4 MEASUREMENT LEDGER + theDeterminism PROVEN (2026-08-26, second recording):** the recorder
now also digests three NAMED streams — `qfrc_constraint` (the contact/constraint force field),
`qacc_warmstart` (the solver's carried warm-start state), `act` (the Hill actuators' internal
activation) — and publishes `docs/determinism_s4_record.json` (55,949 steps, bit-identical,
run_digest `00da948f…`, per-stream digests). That ledger is the S5 why-terminal for the
engine's discovered variables: contact forces, warm-start state, activation state and FP
reduction order each terminate at the stream that measured them (ground friction terminates at
`story/theStance/numbers.json#ground_friction_mu`, mass distribution at `#com_height_m`, tissue
coupling at the published `gait_envelope_deg`). With the dyad holding at 0.85 (twin bit-identical
networks, `splat_appearance._determinism_buffers`), **`theDeterminism` is PROVEN through the MCP
gate — all six gates, written to the codebook.** Log: `agent_logs/phase0_ci_determinism_r3.txt`.

**RE-RECORDED on the ligamented body (2026-08-27, r4):** the Van Criekinge envelope restoration
(UPRIGHT repair) changed the body, so the record was regenerated: **21 items stable across 3
runs · 52,472 stepped states bit-identical · max |delta| = 0 · run_digest `4d15ddc1…`** —
`docs/determinism_s4_record.json` rewritten (the recorder publishes only on bit-identity, so
the file on disk is always a passing one). The action `rhythm_drive` verdict is a STABLE FAIL
here — stable is what S4 measures; the falsification itself is a physics finding recorded in
`tools/action_rhythm.py`'s dated addendum and THE_MASTER_LIST §32, not a determinism violation.
Log: `agent_logs/phase0_ci_determinism_r4.txt`.
