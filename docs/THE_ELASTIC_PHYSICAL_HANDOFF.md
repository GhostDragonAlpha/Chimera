# Elastic physical fixture handoff

Status: CPU prerequisite packet v2 complete; GPU admission remains open.

The rejected first candidate and its raw outputs are preserved under
`docs/evidence/elastic_physical_fixtures/superseded-rejected-v1-20260910_*`. Its output
must not be used as physical evidence: legacy v1 `E_f64`, `h_f64`, and expected arrays carry
the historical implicit-unit semantics and are never relabelled as Pa inputs here.

`tools/elastic_foundation/physical_fixtures.py` generates and verifies a new
`elastic-physical-fixture/v2` packet from explicit synthetic recipes. The packet stores
original binary64 geometry/material inputs and a distinct round-to-binary32 upload stream,
including rounded positions, E3d, h, E2, nu, B, reference area, and CSR arrays. Evaluation
consumes the stored upload fields rather than rebuilding or silently substituting them.
Structured source/provenance and schema hashes are bound into the packet; verification also
requires the caller-supplied trusted SHA-256 of the packet manifest.

The independent rational triangle and canonical patch references contain complete F, energy,
Wbar, w_vol, corner-force, and gathered vertex-force arrays. Tests mutate actual B/area/CSR,
material thickness, provenance, output fields, references, source hashes, and trust anchors;
malformed/nonfinite values and extra schema fields refuse by name. Generation and verification
refuse existing outputs and return nonzero on failures. Legacy fixture files remain byte-for-byte
unchanged and are used only for hash-anchored geometry compatibility.

Applied sample command:

```powershell
$env:CHIMERA_FIXTURE_REPO='E:\ChimeraWork\slot-03'
python tools/elastic_foundation/physical_fixtures.py generate --output docs/evidence/elastic_physical_fixtures/packet_v2_20260910T223000Z --legacy-run docs/evidence/elastic_foundation/fixtures/v1/run_20260908T231140Z --legacy-manifest-sha256 6ce4116b8bab3b6b2e6820e66dfe457e307a4f2266e2f2497f75d9c0359537bc
python tools/elastic_foundation/physical_fixtures.py verify --manifest docs/evidence/elastic_physical_fixtures/packet_v2_20260910T223000Z/manifest.json --manifest-sha256 8bbe19872e82287eeeb053d8c3f1e51e8c2e5c9a83dd02d230e4eb8929a1cc8c --output docs/evidence/elastic_physical_fixtures/verify_v2_20260910T223000Z.json
```

Both commands returned zero; the verification report records both fixtures `ok: true` and
`gpu_acceptance: OPEN`. No f32 GPU tolerance, ABI, performance, or real-material claim is made.
Future GPU admission must run the separate GPU_HANDOFF Stage C checks.
