# Gatekeeper's drill — autopsy of a real failure (fable-5)

**The corpse:** failed build mutation_130c51530c92 @ 2026-07-12T01:04 — the
DustAccumulationMaterial failure family (the build-trend's most common recent
error signature, twice over).

**The gate that guards it:** gate_build_succeeded — UBT must return 0; the
pipeline halts with exit code 1 and the grade auto-drops to F on violation. It
did its job: the failure was recorded, not silently continued past (no fallback
ladders).

**The H-rule that names the disease:** H-1 — a C2039 missing-member error in
ProceduralGenerated/ means TEMPLATE DRIFT: the constructor's member-initializer
list referenced AccumulationRate / DecayRate / NormalThreshold / NoiseFrequency
that the header never declared. The cure matched the rule: declare the members
with the same change that exercises them (landed as commit 50548ad, verified by
the 01:23 passing build). For generator-owned files the fix must go in the
generator template; DustAccumulationMaterial is loop-built manual, so the
hand-fix was legal under the Contract.
