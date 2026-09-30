---
name: creature-graph-and-membrane-roadmap
description: The operator-approved creature-graph architecture + Astra's 42-item
  membrane inventory (the roadmap of record) + the one-honest-limb build —
  shipped substrate, build order, and the central falsifier
metadata:
  node_type: memory
  type: project
  originSessionId: sess_141e362c-a25b-452d-bd03-88fb5f876ce6
---

The 2026-09-15 anatomy pivot's architecture (operator-approved via pasted
briefs "Prompt for GLM 5.3: Chimera spatial graph, reference data, and one
honest limb" — the LATER paste is the updated version of record; Alan relays
these composed briefs through the [[astra-consultation-channel]]).

**THE DESIGN — one graph, three coordinated views** (spatial: the body in
engine coordinates with TRANSPARENT PLACEHOLDERS for unbuilt structures;
physical: compartments/membranes/attachments/laws; roadmap: what exists, what's
missing, what blocks it, which experiments prove completion). Selecting an
object in any view selects the same object in all three. An unfinished membrane
has identity, place, intended connections, and acceptance tests BEFORE it is
built. CENTRAL FALSIFIER: "if the graph says a structure exists and works, we
must be able to select it, inspect its physical connections, intervene on it,
and observe the predicted change."

**SHIPPED — G2 creature-graph substrate (a3d63215, tools/creature_graph/ +
tools/reference_data/ + docs/THE_MEMBRANE_INVENTORY.md in slot-01)**: schema
v2.0.0, 1,482 objects / 130 relations; the six distinctions ENFORCED (type vs
instance; intended vs observed; physical connection vs implementation
prerequisite; reference assertion vs selected parameter; known/provisional/
unknown geometry; reference pose vs live state vs layout position — schema
REJECTS layout keys in spatial); readiness computed ONLY on the
requires_implementation DAG (physical rels may cycle); validation lifecycle
independent (untested/passing/failing/stale, conservative invalidation,
EXTRACTED never verifies). Pinned deterministic imports (no LLM rows):
Uberon appendicular-minimal v2026-06-23 (CC BY 3.0), RO v2026-09-04 (CC0),
QUDT units (license UNKNOWN — recorded), OpenSim leg6dof9musc (XML parsed,
NEVER executed; 63 property assertions), BodyParts3D deferred. 30 name-
similarity mappings are CANDIDATES, never equivalences. Idempotent re-import
(sha256-identical store). Six gap queries working (Q6: next = partition_leg_l).
NOTE: the brief's cited Graphify paths (E:\PythonChimera\Docs\...) do NOT
exist; the real pieces are E:\PythonChimera\Chimera\core\graphify_interface.py
+ graphify_record.py.

**THE ROADMAP — Astra's 42-item membrane inventory** (docs/
THE_MEMBRANE_INVENTORY.md): 12 anatomy (per-bone compartments P0, load-bearing
skin P0, septa/fascia P0, joint capsules P0, contractile tissue P0-for-muscle,
tendons/ligaments P0, bone walls P1, cartilage P1, vessels P1, respiratory P0-
correction, gut P1, filtration P2), 10 materials/lifecycle (material surfaces
P0, adhesives P0, tensile web P0, yield/scratch P0, cracks/rupture P0, pores/
leakage P0, patches/repair P0, thermal P0-ledger, growth/fission P1, molecular
P2), 6 world (ground P0, water P1, soil P1, atmosphere P1, containers P1,
cosmic P2), 7 senses (tactile receptor patches P0, proprioception P0, axonal
delayed propagation P0, synapses/reflex integration P0, eyes P0, ears P1,
chemical/thermal P2), 6 product interfaces (player mechanical P0, sim↔browser
truth P0, measurement/explanation P0, import/sealing P0, persistence P0,
lesson-counterfactual P0, care loop P0). **Top-five build order**: (1) per-bone
compartments + shared septa + inspection, ONE limb first; (2) one force path
across a joint (contractile→tendon→bone→capsule, sliding skin); (3) local
touch + delayed reflexes + honest gaze; (4) rupture→leak→patch→reload; (5)
HUD-independent press-answer-investigate-repair.

**IN FLIGHT — AN2 one-honest-limb (56762faf)**: leg segments from skeleton
CONNECTIVITY (hip 13→knee 15→ankle 17 → thigh_L/shin_L/foot_L; engine
re-derives and refuses by name if connectivity disagrees); seal refactor
(seal_cut_core_ — ONE winding law for horizontal AND oblique walls); sensor
patches (finite receptor regions, τ=10 ms filter, finite delay distance/70
m/s, per-path disconnectable); causal demo measured on the current binary
(path cut → flinch env exactly 0 while passive press response identical;
isolation conserve −0.000117%). Window #10: the partition's own gate fired
honestly (thigh_L v0=NaN in the oblique volume integral — AN2 round 2 pending);
the lead fixed AN2's missing-JSON-key bug that poisoned /tick_state. NAMED
GAPS: open-wound fluid transfer NOT implemented (puncture = next task; never
call two auto-sealed daughters leakage); the servo "force-limited" claim is
STALE (kinematic pose writes, NO force state — the XPBD appliance brings real
constraint forces). Breathing must be relabeled/reimplemented per the inventory
(actuated volume-preserving shape motion or a real gas compartment; the water-
volume oscillator is not respiration).

Next five graph-backed tasks (G2 HANDOFF.md, now evidence-gated):
partition_leg_l DONE (live, window #12) → **septa_leg_l (puncture isolation)
NEXT, gated on Codex's D3/D4 capture-integrity repairs** → causal_demo_leg_l
(traces keyed to stable IDs, flipping ev.reflex_controls_fail honestly) →
reference_adaptation_osim (human confirm/reject of the 30 candidate mappings)
→ inspect_consistent_ids.
Related: [[fleet-state-2026-09-15]], [[astra-consultation-channel]],
[[membrane-game-product-vision]], [[matter-kernel-spec-and-build]].
