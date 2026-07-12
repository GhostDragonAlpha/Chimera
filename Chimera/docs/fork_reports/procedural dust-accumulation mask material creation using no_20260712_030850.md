# Fork report: procedural dust-accumulation mask material creation using no (20260712_030850Z)

## wild — 60.0/100 (WINNER)
- scoring: locked reference +20 (recognized against campus seeds); exact params 2 (+4/20); sources +10; principles 3 (+6/10); anchor +10; criteria 2 (+10/30); failure_sources 3 (Gate 4 met)
```json
{
 "fork": "wild",
 "feature": "procedural dust-accumulation mask material creation using no",
 "approach": "Invert the standard noise-based masking by utilizing inverted aerodynamic drag coefficients from NASA's CFD surface pressure models as a height-map source, feeding drag-derived pressure gradients directly into Unreal Engine 5.8's procedural mesh deform node to generate dust-accumulation masks via negative porosity mapping instead of standard grain-size distributions. This cross-domain technique bypasses conventional noise generators by treating fluid dynamic pressure as an inverted displacement field, forcing the material shader to interpret vacuum exposure as dust retention rather than erosion.",
 "canonical_reference": "NASA/TP-2019-220187: 'Computational Fluid Dynamics Methods for Low Earth Orbit Environment Modeling'",
 "campus_sources": [
  "UE 5.8 Material Subsystem Documentation",
  "NASA Langley Research Center CFD Surface Deposition Models",
  "Cross-domain Fluid-Solid Interaction literature"
 ],
 "parameters": {
  "inverted_drag_coefficient_multiplier": "-1.47",
  "porosity_mapping_inversion_threshold": "0.35"
 },
 "principles": [
  "Inverted Parameter Mapping",
  "Cross-Domain CFD-to-Material Transfer",
  "Negative Porosity Masking"
 ],
 "emotional_anchor": "visceral dread of decay",
 "acceptance_criteria": [
  "Dust accumulation mask must exhibit negative correlation between surface curvature and dust density in-engine",
  "Material must render dust accumulation masks using only inverted drag coefficient inputs without standard noise nodes"
 ],
 "failure_sources": [
  "Standard grain-size distribution nodes fail under inverted aerodynamic parameter sets",
  "UE 5.8 procedural mesh deform nodes reject negative porosity values without clamping",
  "NASA-reference realism standards reject non-physical dust deposition gradients"
 ]
}
```

## conservative — 56.0/100 (sacrificed)
- scoring: locked reference +20 (recognized against campus seeds); exact params 1 (+2/20); sources +10; principles 2 (+4/10); anchor +10; criteria 2 (+10/30); failure_sources 2 (Gate 4 met)
```json
{
 "fork": "conservative",
 "feature": "procedural dust-accumulation mask material creation using no",
 "approach": "The campus-canonical approach utilizes locked references from A+ school sources to establish standard proven parameters for procedural dust accumulation masks in UE 5.8 space-trader environments. This method relies on NASA-reference realism standards to ensure accurate physical simulation of particulate deposition and surface wear over time.",
 "canonical_reference": "NASA-HDBK-6003: Particulate Contamination Control for Spacecraft Systems",
 "campus_sources": [
  "UE 5.8 Material Library Documentation - Procedural Masking",
  "NASA-HDBK-6003 Particulate Contamination Control",
  "Campus A+ Source: Procedural Masking in UE Materials"
 ],
 "parameters": {
  "DustAccumulationRate": 0.75
 },
 "principles": [
  "Physical realism in particulate deposition",
  "Procedural mask generation via noise-driven accumulation"
 ],
 "emotional_anchor": "safety assurance",
 "acceptance_criteria": [
  "Dust mask opacity matches NASA-HDBK-6003 particulate deposition rates within 5% tolerance in-engine",
  "Procedural mask node chain renders at 60 FPS in UE 5.8 space-trader viewport"
 ],
 "failure_sources": [
  "Non-procedural texture baking methods for dynamic dust accumulation",
  "Standard height-based masking without noise-driven temporal accumulation"
 ]
}
```

## alternative — 0.0/100 (sacrificed)
- scoring: NO locked reference (0/20); exact params 0 (+0/20); sources 0 (0/10); principles 0 (+0/10); no anchor (0/10); criteria 0 (+0/30); failure_sources 0 (Gate 4 unmet)
```json
{
 "fork": "alternative",
 "feature": "procedural dust-accumulation mask material creation using no",
 "approach": "(generation failed: timed out)"
}
```
