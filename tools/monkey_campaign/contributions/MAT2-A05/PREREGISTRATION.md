# PREREGISTRATION — MAT2-A05 Correction Round (Path B: Honest Blocker + Decision Request)

## Task Identity
- Card: MAT2-A05
- Criteria SHA256: 34411771f7bd5dea2ec2cc4775d44b33df422e5454d283eae40676d1e3346544
- done_when: "The modeled grasp has sufficient explicit bodies, joints and geometry; sources and adaptations approved"

## Path Chosen: PATH B — Honest Blocker + Decision Request

### Rationale for Path B Choice
The prior candidate (attempt a71100257a8f4fb4a6f77858b1c70fd8, head 2b670819) documented pre-existing state only: the single `hand` body exists, `Geometry/hand.vtp` is referenced, the wrist joint exists, UBERON phalanx ontology nodes are present in the graph. Its own prediction confirmed NO individual finger bones or phalange joints exist — that is the 14-phalanges gap THIS card owns. The preregistration's own Prediction states: "no individual finger bones or phalange joints are present in the osim geometry/joint set. CONFIRMED."

This is the gap itself, restated — not its closure. Authoring digit structure without evidence would violate the no-invented-anatomy law (REALITY category laws: real macaque anatomy required, species-true, stage-true). Therefore, Path B is chosen: document the exhaustive source search with evidence (paths checked, hashes, what each contains), state that no evidenced digit data is available in the pinned sources, and record the decision request: external source acquisition is a Captain-level data question.

## Exhaustive Source Search Evidence

### 1. Pinned Vendor Package Behind monkeyArm_current.osim
**Source**: `limblab/monkeyArmModel` (revision `4fb7dddeec06a0df9525c18f37234a824cb1b5b1`)

**Files Checked**:
- `/e/PythonChimera/tools/science_funnel/data/macaque_arm/monkeyArm_current.osim`
  - SHA256: `4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895`
  - Size: 215094 bytes

**Bodies Defined in monkeyArm_current.osim**:
- ground, sternum, clavicle, scapula, humerus, ulna1, ulna, radius_jcc, radius, radius1, hand (single body)

**Geometry Files in `monkeyArm_current.osim/Geometry/`**:
- clavicle.vtp (SHA256: 84caf2d4724aef05b7f8e904474deda7342db1b6c0329cfa5b399802bfebc905)
- scapula.vtp (SHA256: e9ffe8ef9ad2dc577fb8c50afd87f694d0ddb6e243d230ba91e2aa7137480fe7)
- sternum.vtp (SHA256: fc688ea2643c356f28a6eb3c825e056941d307d407414f77f0c5d655c91a227d)
- humerus.vtp (SHA256: 87f6034aa082c49b6448259ae7ec4452c6b0d3314442d5be3e8e1a5e4ec8118b)
- radius.vtp (SHA256: 8a2d3f2fe5f8b27014c0f024994ff76659bac73a52844494926dd29b9f3bb10e)
- ulna.vtp (SHA256: 8f80ac47453fa175118fa385a5fbcb9cf770a21cf10c1757dccc5df2cceb1409)
- hand.vtp (SHA256: a06ea7e079c849df07d6eec001e9bcc2ea193ecd3914011c78a993a5faa94fc6)

**Result**: No individual finger bones, phalanges, or metacarpals defined as separate bodies. The `hand` is a single body without individual digit structure.

### 2. Chimera/data/ Directory
**Path**: `/e/PythonChimera/Chimera/data/`

**Contents**: appearance_spec.json, choose_spec.json, control_spec.json, gait_spec.json, lattice_spec.json, meaning_spec.json, rig_spec.json, scan_spec.json, stand_spec.json, voxel_types.json, walk_spec.json, world_spec.json.

**Result**: No anatomy or digit/phalange data present. These are specification files for appearance, control, gait, rig, etc.

### 3. .s04_reference/ and .s04_authors/ Directories
**Paths**: `/e/PythonChimera/.s04_reference/`, `/e/PythonChimera/.s04_authors/`

**Contents**: tool documentation (tools_monkey_campaign_product_input_settings.py, tools_monkey_campaign_product_session_flow.py, tools_monkey_campaign_product_state_feedback.py), PREREGISTRATION.md, player_diagnostics.py, etc.

**Result**: No hand/digit anatomy data or macaque phalange structure present.

### 4. tools/science_funnel Staged Sources
**Path**: `/e/PythonChimera/tools/science_funnel/data/macaque_arm/`

**Contents**: monkeyArm_current.osim, scaleSettings.xml, LICENSE, download_receipt.json, Geometry/ directory with 7 .vtp files (clavicle, hand, humerus, radius, scapula, sternum, ulna).

**Result**: Confirmed above in Section 1. No phalange or digit structure data.

### 5. Creature Graph's Macaque Arm Intake / Reference Store
**Paths Checked**:
- `/e/PythonChimera/tools/reference_data/data/reference_store.json`
- `/e/PythonChimera/tools/creature_graph/data/creature_graph.json`

**Contents Found**: UBERON ontology nodes for phalanges (phalanx of manus, proximal phalanx of manus, metacarpal bone, etc.) and mappings like `map.uberon-phalanx__osim-toes_r`. These are ontology references, NOT explicit bodies with joints and geometry.

**Result**: UBERON nodes exist in the graph, but no actual digit structure (14 phalanges as explicit bodies + joints + geometry) is provided.

### 6. Human OpenSim Reference Models
**Paths Checked**:
- `/e/PythonChimera/research_references/human/opensim/Rajagopal2016.osim`
- `/e/PythonChimera/research_references/human/opensim/FullBodyModel_Hamner2010_v2_0.osim`

**Bodies in Human Models**: pelvis, femur_r/l, tibia_r/l, patella_r/l, talus_r/l, calcn_r/l, toes_r/l, torso, humerus_r/l, ulna_r/l, radius_r/l, hand_r/l.

**Result**: Even the human OpenSim reference models use a single `hand_r`/`hand_l` body without individual phalange bodies defined as separate bones with joints and geometry. The 14-phalanges structure (proximal, middle, distal for fingers 2-5; proximal, distal for thumb) is not modeled as explicit bodies in these OSIM files.

## Conclusion: No Evidenced Digit Data Available

The exhaustive search of pinned sources yields no evidenced digit data that provides the 14 phalanges (or source-true count for this specimen) as explicit bodies with joints and geometry, bound to source pins (checksums, units, mm->m qualifiers, species/specimen labels).

Authoring digit structure without evidence would violate the no-invented-anatomy law. REALITY category laws require: real macaque anatomy required, species-true, stage-true.

## Decision Request (Captain-Level Data Question)

External source acquisition is a Captain-level data question. The 14-phalanges gap for the modeled grasp requires sourced digit structure (explicit bodies + joints + geometry with source pins) or an explicit deferral to acquire such external anatomy data from a macaque hand/digit reference model or scan that provides phalange-level anatomical detail.

This blocker record is honest; a PASS-shaped candidate documenting the gap as if it were closure would not be acceptable per the lead's finding.
