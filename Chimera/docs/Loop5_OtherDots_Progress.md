> **DEPRECATED** — This document describes the old approach.
> Read `AGENT_ONBOARDING.md`, `DECISION_METHOD.md`, and `EMERGENT_WORKFLOW.md` instead.
> The thought chain is at `docs/THOUGHT_CHAIN.md`.

# Loop 5 — Other Dots: Progress Report

**Emotional Anchor:** Society — Connection ("Safe" emotion: 3200K, soft shadows, fabric/wood, contained space)

**Current Status:** Phase 2 — Apply & Verify

---

## Feature Status

| # | Feature | Type | Status | Details |
|---|---------|------|--------|---------|
| 1 | NPC_Basic_Model | geometry | ✓ Implemented | EVA suit astronaut assembled from 6 static meshes |
| 2 | NPC_Basic_Material | material | ✓ Implemented | MAT_EVASuit_Refined6, PBR fabric, Professor grade: A (4.0) |
| 3 | NPC_Basic_Animation | animation | ⬜ Not started | — |
| 4 | NPC_Basic_AI | behavior | ⬜ Not started | — |
| 5 | Social_Trade | interaction | ⬜ Not started | — |
| 6 | Social_Conflict | interaction | ⬜ Not started | — |

---

### NPC_Basic_Model ✓

**Description:** Astronaut EVA suit character model assembled from 6 primitive static meshes in T-pose. Based on NASA EMU (Extravehicular Mobility Unit) specifications.

**Parameters Extracted:**
- Humanoid proportions: ~170-180cm height, 2:1 torso-to-leg ratio
- Torso: Cylinder r=25cm, h=60cm (EMU Hard Upper Torso)
- PLSS Backpack: Box 30×20×60cm (Life Support System)
- Helmet: Sphere r=15cm
- Upper arms: Cylinder r=8cm, h=30cm (each)
- Lower arms: Cylinder r=7cm, h=25cm (each)
- Thighs: Cylinder r=12cm, h=40cm (each)
- Silhouette: Bulky, rectangular with rounded edges — no sharp corners

**Meshes Created (6):**
- `/Game/Characters/NPCs/SM_NPC_Torso_SM_NPC_Torso`
- `/Game/Characters/NPCs/SM_NPC_PLSS_SM_NPC_PLSS`
- `/Game/Characters/NPCs/SM_NPC_Helmet_SM_NPC_Helmet`
- `/Game/Characters/NPCs/SM_NPC_UpperArm_SM_NPC_UpperArm`
- `/Game/Characters/NPCs/SM_NPC_LowerArm_SM_NPC_LowerArm`
- `/Game/Characters/NPCs/SM_NPC_Thigh_SM_NPC_Thigh`

**Materials Applied:**
- Torso/PLSS/Limbs: MAT_EVASuit_Refined5 (padded fabric)
- Helmet: MAT_GoldVisor (gold-coated polycarbonate)

**Existing NPC Framework (pre-existing):**
- `/Game/Characters/NPCs/BP_NPC_Basic` — Blueprint
- `/Game/Characters/NPCs/AIC_NPC_Basic` — AI Controller
- `/Game/Characters/NPCs/BT_NPC_Basic` — Behavior Tree
- `/Game/Characters/NPCs/BB_NPC_Basic` — Blackboard
- Source: NPCTradeComponent (trade interaction logic)

---

### NPC_Basic_Material ✓

**Description:** Refined PBR materials for the EVA suit NPC, created based on NASA EMU (Extravehicular Mobility Unit) specifications with proper fabric, wear, and hardware parameters.

**Professor Grade:** A (4.0) — LM Studio confirmed specific parameters ✓, locked reference ✓, solid principles ✓

**Research Sources:**
- Art School (Campus 2): PBR material layering, color theory for fabric
- Engineering School (Campus 5): NASA EMU specifications, ISS reference photos
- UE Craft School (Campus 6): MCP material creation pathways
- **Campus +1 Discovery:** NASA EMU Suit Reference Photos from ISS (spaceflight.nasa.gov gallery)

**Extracted Parameters (NASA EMU Reference):**

| Component | PBR Parameter | Value | Rationale |
|-----------|--------------|-------|-----------|
| Suit Fabric (Orthofabric) | BaseColor | (0.83, 0.81, 0.78) | White fabric — NASA's actual white orthofabric color |
| Suit Fabric | Roughness | 0.85 | Fabric weave texture, not smooth |
| Suit Fabric | Metallic | 0.0 | Non-metallic fabric |
| Dirt/Wear Layer | BaseColor | (0.55, 0.45, 0.30) | Rust/tan deposits at joints |
| Dirt/Wear Layer | Roughness | 0.9 | Rougher than clean fabric |
| Dirt/Wear Layer | Metallic | 0.0 | Dirt is non-metallic |
| Gold Visor | BaseColor | (0.6, 0.45, 0.1) | Thin-film gold reflection |
| Gold Visor | Metallic | 0.1 | Slightly metallic (thin film) |
| Gold Visor | Emissive | 0.05 | Subtle glow from coating |
| Connectors (anodized Al) | Roughness | 0.3 | Polished aluminum |
| Connectors | Metallic | 0.9 | Highly metallic |
| Connectors | BaseColor | (0.3, 0.3, 0.32) | Dark anodized aluminum |
| PLSS thermal blanket | BaseColor | (0.15, 0.15, 0.18) | Dark thermal layer |
| PLSS thermal blanket | Roughness | 0.6 | Semi-rough blanket fabric |

**Material Assets:**
- `/Game/Chimera/Materials/MAT_EVASuit_Refined6.MAT_EVASuit_Refined6` — New PBR fabric material for EVA suit
- `/Game/Chimera/Materials/MAT_EVASuit_Refined5` — Existing fabric material (reused)
- `/Game/Chimera/Materials/MAT_GoldVisor` — Existing gold visor material

**Education Principles Applied:**
1. Art School: PBR material layering for fabric (roughness maps fabric texture)
2. Engineering School: Wear/dirt patterns mapped to joint articulation points (knees, elbows)
3. Film School: High-key fill lighting on white suits to show surface detail
4. Emotion-to-Parameter: "Safe" anchor (3200K, soft shadows) — the suit is a shelter in void

**Known Limitation:**
- MAT_EVASuit_Refined6 created as base Material. PBR parameters (Roughness, Metallic, BaseColor) require conversion to MaterialInstance or manual tuning in UE5 editor for runtime control via `set_scalar_parameter_value` pathway.

---

## Next Steps

1. ✅ ~~NPC_Basic_Material (refined EVA suit materials with dirt/wear)~~
2. Proceed to NPC_Basic_Animation (Loop 5, Feature 3)
3. Integrate meshes into BP_NPC_Basic blueprint hierarchy
4. Continue spiral — next feature: NPC_Basic_Animation

---

### Campus Discoveries (Loop 5)

| Source | Type | Quality | Feature |
|--------|------|---------|---------|
| NASA EMU Suit Specs (Wikimedia Commons) | Reference photos | A+ | NPC_Basic_Model |
| NASA EMU ISS gallery (spaceflight.nasa.gov) | High-res wear patterns | A+ | NPC_Basic_Material |