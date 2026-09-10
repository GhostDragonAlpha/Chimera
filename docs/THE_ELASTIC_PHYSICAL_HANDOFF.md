# Elastic physical fixture handoff

Status: corrected CPU reference candidate has passing observed tests; its fixed-recipe numerical envelope remains subject to independent review. GPU ABI, ordering, and binary32 acceptance budgets remain OPEN.

The v2 packet uses explicit synthetic E3d [Pa], h [m], E2 [N/m], and nu recipes. It stores and consumes separate original binary64 and round-to-binary32 upload streams, including upload positions, material scalars, rest B, area, and CSR arrays. Source/provenance/schema hashes and a caller-supplied trusted manifest SHA bind the packet. Complete F, energy, Wbar, w_vol, corner-force, and gathered vertex-force references are checked componentwise.

The corrected implementation withdraws the earlier unsupported gamma-only claim and propagates representation and operation error through the fixed scalar expression graph. Tests include actual evaluator mutations, malformed/nonfinite fields, changed references, altered B/area/CSR, trust-anchor replacement, and output overwrite refusal. Results are CPU observations for fixed recipes; they do not certify a GPU or real material.

Historical rejected and gen2 candidates remain preserved under scoped superseded directories. Legacy v1 NPZ bytes and implicit-unit semantics are unchanged and are used only for trusted geometry compatibility and immutable hash checks.

Fresh corrected packet: `packet_v2_corrected_20260910T230000Z/manifest.json`
Trusted manifest SHA-256: `7ef80dcbc16fb80055b341ace4a5cf39ee2ecea6c25472142bae2dcc102d58df`
Verification report: `verify_v2_corrected_20260910T230000Z.json`
Raw command/result record: `correction-20260910T230000Z.txt`

Fresh generate and verify commands returned zero; both fixtures pass with GPU acceptance OPEN. No GPU ABI, GPU tolerance, performance, or real-material claim is made.
