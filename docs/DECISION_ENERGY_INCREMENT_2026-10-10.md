# Decision Record — Energy-Based Actuation Increment (2026-10-10)

Author: Qwen (decisions) / Tiel (record, implementation). Status: accepted.

## User vision

Advanced RPG in the Citizen-Sleeping-like class: a more real world, advanced
graphics and physics, persistent world knowledge, all built on the
energy-based ontology of docs/THE_MEMBRANE_INVENTORY.md ("stored energy →
force" as the only causal primitive for movement).

## Decisions (2026-10-10)

1. First increment = one muscle→tendon pair driving one joint, implemented as
   a dynamic mode. Three gated steps: (a) standalone module
   (ChimeraEngine/engine/tendon_drive.hpp, this record); (b) engine
   integration, default-OFF; (c) scratch-engine falsifiers plus the 11-lesson
   regression. No step proceeds while the previous one is unproven.
2. All actuator parameters are declared-synthetic with units and provenance
   notes, following the finite_area_attachment coupon precedent. They are
   plausible in kind, not sourced from measurement.
3. Falsifier runs execute on the scratch engine only, never the shared live
   world.
4. Pose-lesson re-judging is deferred until the dynamic mode is proven; the
   existing kinematic pose lessons keep their current judging.
5. Acceptance --refresh is deferred to the end of step (c).

## Roadmap after this increment

force-driven limb → contact/slash physics with lasting damage →
persistence/sensing (world knowledge) → RPG goals and consequences.

## Citations

- docs/THE_MEMBRANE_INVENTORY.md, build order #2: one force path across a
  joint; falsifier: "a tendon that can be severed without changing the
  commanded movement is not carrying that movement".
- docs/architecture/CREATURE_ARCHITECTURE_REBASE_2026-09-15.md:36, :215, :262
  (energy-first actuation, synthetic-parameter discipline, scratch falsifier
  boundary).
