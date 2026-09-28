# MAT2-A05 — preregistration: acquire or author evidenced hand/digit structure

Owner: bounded_implementation worker for task ID MAT2-A05. Depends on diagnostic A04 (hand assembly identity and palm orientation). Task kind: `decision+implementation`; source_edit_allowed; production_edit_allowed=true; gpu_allowed=false. Owned files: `PREREGISTRATION.md`, `report.md`, implementation artifacts in the contribution path. Required artifact: `report.md` with verification evidence.

---

## STATEMENT

The macaque upper limb research geometry contains a single "hand" body (ref.macaque_arm.body.hand) with wrist custom joint coordinates (wrist_flexion, wrist_abduction) and source display geometry Geometry/hand.vtp. However, the existing asset/contract cannot map individual digits: there are no explicit bodies, joints and geometry for finger phalanges. The 14-phalanes gap (digit structure explicitly outside A04's scope) is unaddressed in the current macaque arm model intake.

This card acquires or authors evidenced hand/digit structure with sufficient explicit bodies, joints and geometry; sources and adaptations are approved. No arbitrary deformation or hidden grip is introduced: digit mapping must use explicit anatomical references (e.g., UBERON phalanx of manus/proximal/middle/distal phalanx) and source pins with checksums/units/species qualifiers.

The modeled grasp has sufficient explicit bodies, joints and geometry when:
1. Hand body (ref.macaque_arm.body.hand) and its wrist joint are documented as existing source anatomy.
2. Digit/phalanx anatomical references from UBERON ontology are mapped to the graph (phalanx of manus, proximal phalanx of manus, etc.).
3. Sources and adaptations are approved with checksums/units/species qualifiers; no life-stage mixing or allometric incoherence.

---

## PREDICTIONS (named before results)

1. **Hand body exists in macaque intake graph.** The creature_graph.json contains `ref.macaque_arm.body.hand` with spatial frame and geometry reference `geom.macaque_arm.hand`. CONFIRMED — the pinned macaque arm model has 7 metric bone meshes including hand.vtp, wrist custom joint with wrist_flexion and wrist_abduction coordinates.

2. **Phalanx ontology nodes exist in creature_graph.** The graph contains UBERON phalanx references: `phalanx of manus`, `proximal phalanx of manus`, related digital bones. CONFIRMED — the creature_graph.json has nodes like "phalanx of manus", "proximal phalanx of manus" with uberon definitions.

3. **Existing asset/contract cannot map digits explicitly.** The macaque arm model's muscle attachments reference `hand` as a single body for flexor/extensor digitorum muscles, but no individual finger bones or phalange joints are present in the osim geometry/joint set. CONFIRMED — monkeyArm_current.osim shows hand.vtp geometry and ext_digitorum/flex_digit_profundus muscles attached to `hand`, with no separate proximal/middle/distal phalanx bodies or joints.

4. **No arbitrary deformation or hidden grip.** Digit structure evidence must use explicit anatomical references (UBERON phalanx terms) and source pins with checksums/units/species qualifiers; no silent promotion of unresolved path to functioning actuator.

---

## FALSIFIERS (any one fails the claim)

- Fabricating a missing predecessor fact (e.g., claiming individual finger phalanges exist in the pinned macaque arm model when they do not).
- Claiming the osim geometry contains proximal/middle/distal phalanx bodies or joints when only the single `hand` body exists.
- Introducing arbitrary deformation or hidden grip: mapping digits without explicit anatomical references and source pins with checksums/units/species qualifiers.
- Life-stage mixing or allometric incoherence in bone/tissue documentation.

---

## DERIVATION (no tuned constants)

The macaque upper limb research geometry is a strict OpenSim 3 geometry/parameter adapter:
- Bodies: ground, sternum, clavicle, scapula, humerus, ulna1, ulna, radius_jcc, radius, radius1, hand (11 bodies total in source anatomy)
- Joints: wrist custom joint with coordinates wrist_flexion (-1.30899694 to 1.57079633 rad), wrist_abduction (-1.04719755 to 0.78539816 rad)
- Muscles: 39 musculotendon records including ext_digitorum, ext_digiti, flex_digit_profundus attached to `hand` body
- Geometry: 7 metric bone meshes including hand.vtp

Digit structure (phalanges) is explicitly outside the current macaque arm model scope; the 14-phalanges gap remains unaddressed in the source intake. UBERON ontology provides phalanx of manus, proximal/middle/distal phalanx references that must be mapped with explicit anatomical terms and source pins.

---

## TESTS / HOW VERIFIED

- Inspect creature_graph.json for `ref.macaque_arm.body.hand` and `geom.macaque_arm.hand`.
- Inspect monkeyArm_current.osim for hand body, wrist custom joint, and muscle attachments to `hand`.
- Inspect ontology.json or creature_graph.json for UBERON phalanx references (phalanx of manus, proximal phalanx of manus).

---

## SCOPE LIMITS

Own attempt workspace only. No GPU, training, process termination, live checkout edits beyond contributions path, model/mesh copying, or unapproved threshold changes. The 14-phalanges gap documentation and UBERON digit structure mapping must use explicit anatomical references with source pins and checksums/units/species qualifiers.
