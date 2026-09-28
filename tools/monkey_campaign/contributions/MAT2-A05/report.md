# MAT2-A05 Blocker Report: No Evidenced Digit Structure in Pinned Sources

## Summary
Path B chosen: Honest blocker + decision request documenting exhaustive source search with evidence showing no evidenced digit data is available in pinned sources.

## Source Search Evidence

### 1. monkeyArm_current.osim (limblab/monkeyArmModel v4fb7dddeec06a0df9525c18f37234a824cb1b5b1)
- File: `/e/PythonChimera/tools/science_funnel/data/macaque_arm/monkeyArm_current.osim`
- SHA256: 4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895
- Bodies defined: ground, sternum, clavicle, scapula, humerus, ulna1, ulna, radius_jcc, radius, radius1, hand (single body)
- Geometry files: clavicle.vtp, scapula.vtp, sternum.vtp, humerus.vtp, radius.vtp, ulna.vtp, hand.vtp
- Result: No individual finger bones, phalanges, or metacarpals defined as separate bodies.

### 2. Chimera/data/ Directory
- Contents: specification files only (appearance_spec.json, control_spec.json, gait_spec.json, etc.)
- Result: No anatomy or digit/phalange data present.

### 3. .s04_reference/ and .s04_authors/ Directories
- Contents: tool documentation and player diagnostics
- Result: No hand/digit anatomy data or macaque phalange structure present.

### 4. tools/science_funnel Staged Sources (macaque_arm)
- Same as monkeyArm_current.osim above, confirmed no phalange or digit structure data.

### 5. Creature Graph / Reference Store
- Paths: `/e/PythonChimera/tools/reference_data/data/reference_store.json`, `/e/PythonChimera/tools/creature_graph/data/creature_graph.json`
- Contents Found: UBERON ontology nodes for phalanges (phalanx of manus, proximal phalanx of manus, metacarpal bone, etc.)
- Result: UBERON nodes exist in the graph, but no actual digit structure (14 phalanges as explicit bodies + joints + geometry) is provided.

### 6. Human OpenSim Reference Models
- Paths: `/e/PythonChimera/research_references/human/opensim/Rajagopal2016.osim`, `FullBodyModel_Hamner2010_v2_0.osim`
- Bodies: pelvis, femur_r/l, tibia_r/l, patella_r/l, talus_r/l, calcn_r/l, toes_r/l, torso, humerus_r/l, ulna_r/l, radius_r/l, hand_r/l
- Result: Even human OpenSim models use a single `hand_r`/`hand_l` body without individual phalange bodies.

## Conclusion
The exhaustive search of pinned sources yields no evidenced digit data that provides the 14 phalanges as explicit bodies with joints and geometry. Authoring digit structure without evidence would violate the no-invented-anatomy law (REALITY category laws: real macaque anatomy required, species-true, stage-true).

## Decision Request (Captain-Level Data Question)
External source acquisition is a Captain-level data question. The 14-phalanges gap for the modeled grasp requires sourced digit structure (explicit bodies + joints + geometry with source pins) or an explicit deferral to acquire such external anatomy data from a macaque hand/digit reference model or scan that provides phalange-level anatomical detail.
