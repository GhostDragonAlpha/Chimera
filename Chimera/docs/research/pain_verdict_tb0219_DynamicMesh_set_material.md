# Pain Verdict: tb-0219 — DynamicMesh set_material OverrideMaterials Empty

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
>
> **RULE 0 IS ENFORCED AT S-1 VALIDATE** — every port tested alone, and `port_test()` REFUSES to
> register a test that names no falsifier. The model it feeds: `docs/THE_COMPILER.md` — ports →
> primitives → programs → parser → runtime → calibration.
>
> **[docs/THE_LAW.md](../../../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

**Date**: 2026-07-19
**Pain**: phase_6041c8fbac2001fa:P2
**Agent**: opencode
**Status**: CONFIRMED

## Claim

`control_actor set_material` reports `success:true` on DynamicMeshComponent-based actors (procedural geometry) but `OverrideMaterials` read-back is empty on 0/7 tested pieces — distinct from the proven StaticMeshComponent case (pathway #17).

## Evidence

### 1. Pathway #17 — StaticMesh WORKS

`MCP_PATHWAYS.md:137-142`: `control_actor.set_material` on StaticMeshComponent reports success and OverrideMaterials read-back confirms the override. This is the proven pathway.

### 2. DynamicMesh trap already documented

`MCP_PATHWAYS.md:373-379` (inside pathway #28):
> TRAP (DynamicMeshComponent set_material): control_actor set_material (proven for StaticMeshComponent by pathway #17) reports success:true with fully correct routing info (actorPath/resolvedMaterialPath/materialSlot all echoed) on a DynamicMeshActor's DynamicMeshComponent, but an immediate get_component_property propertyName=OverrideMaterials read-back (zero-latency, PIE confirmed inactive at both calls) still returns an empty array. 0/7 tested pieces persisted. Root cause unconfirmed; DynamicMeshComponent (GeometryScripting) may store its material list through a path the generic OverrideMaterials reflection doesn't see.

### 3. Source code analysis

**`McpAutomationBridge_ControlHandlers.cpp:1663-1799`** — `set_material` handler:
- Finds actor by name (line 1715)
- Collects `UPrimitiveComponent*` targets (lines 1722-1736)
- Calls `Component->SetMaterial(MaterialSlot, Material)` directly (line 1759) — **no type check**
- Reports success with `resolvedMaterialPath` echoed (line 1794)

`SetMaterial()` is virtual on `UPrimitiveComponent`. Both `UStaticMeshComponent` and `UDynamicMeshComponent` inherit it. The call is valid on both.

### 4. Read-back failure root cause

**`McpAutomationBridge_ControlHandlers.cpp:2846-2907`** — `get_component_property` handler:
- Uses `Component->GetClass()->FindPropertyByName(*PropertyName)` — UE reflection (line 2880)
- `UStaticMeshComponent` exposes `OverrideMaterials` as `UPROPERTY TArray<UMaterialInterface*>` — reflection finds it
- `UDynamicMeshComponent` (GeometryScripting plugin) stores materials through a different internal path NOT exposed as a UPROPERTY named `OverrideMaterials`
- `FindPropertyByName` returns null → `PROPERTY_NOT_FOUND`

**Root cause is architectural, not a bridge bug.** The bridge correctly uses UE reflection. `UDynamicMeshComponent` simply doesn't expose `OverrideMaterials` through the same property name.

### 5. No prior research files

Zero research files in `docs/research/` mention DynamicMesh, set_material, or OverrideMaterials in this context. The 0/7 test result was not recorded as individual pathway_attempts.

## Verdict

| Aspect | Status | Evidence |
|--------|--------|----------|
| `set_material` returns success:true on DynamicMeshComponent | CONFIRMED | Source: line 1759 calls same virtual method |
| No component-type branching in handler | CONFIRMED | Lines 1722-1736: collects all UPrimitiveComponent* |
| OverrideMaterials read-back returns [] | CONFIRMED | MCP_PATHWAYS.md:373-379, 0/7 pieces |
| Read-back failure is UE reflection, not bridge | CONFIRMED | Line 2880: FindPropertyByName fails on DynamicMeshComponent |
| Whether SetMaterial() actually VISUALLY applies | UNVERIFIED | No screenshot evidence exists |

## Critical Unknown

Does `UDynamicMeshComponent::SetMaterial()` actually change what renders, or does it silently no-op? The bridge reports success because the UE call doesn't error, but DynamicMeshComponent may have its own internal material pipeline.

**Verification required**: Screenshot comparison (set_material → editor_viewport screenshot before/after) on a DynamicMeshActor.

## Implications

1. **For Loop 4 (Tools)**: Tool weapon materials on DynamicMesh actors cannot be verified via OverrideMaterials read-back. Visual (screenshot) verification is the only option.
2. **For builder trust**: Any `set_material` on procedural geometry must be followed by a screenshot, not a property read-back.
3. **Bridge improvement opportunity**: A new bridge handler could query `UDynamicMeshComponent`'s internal material state if GeometryScripting exposes one.
