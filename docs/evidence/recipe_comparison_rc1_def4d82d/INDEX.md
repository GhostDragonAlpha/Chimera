# Recipe-comparison evidence index — candidate `def4d82d`

Date: 2026-10-12. This directory is the **current** recipe-comparison receipt
for the construction release candidate; it supersedes
`docs/evidence/recipe_comparison_20261013/receipt.json`, which is **stale
relative to this candidate** — both formally (different native binary) and
physically (the measured equilibrium numbers moved; see table). The
predecessor's original bytes are preserved untouched at its path.

## Why the predecessor is stale

Commit `def4d82d` ("B8: acceptance gallery closes swept contact…") changed the
native contact solver: half-space containment for pair contact, the
`B2_FACE_TOL` coplanar noise floor, the one-way velocity-gated impact
backstop, and friction impulse caps. The cradle block rests on its ground
support with ground and connector **sharing** the 0.4 N lift, so contact-model
changes can and did move the equilibrium split. Reproduction of the old
numbers was treated as a hypothesis to test, not assumed.

**Outcome: the hypothesis failed — the old qualification does not carry
forward.** The baseline state hash itself changed (`c2336e9a…` → `805af3e4…`):
the block's resting contact state differs under the new law. Equilibrium
forces shifted ≈ −0.9 % (table below). The comparison *contract* still holds:
direction check, ~18.5× extension ratio, exact repeat reproducibility, and
every trial within the declared 0.02 N analytical-reference tolerance.

## Measurements — predecessor vs candidate

| Variant | Predecessor force (N) | Candidate force (N) | Δ | Predecessor ext (µm) | Candidate ext (µm) |
|---|---|---|---|---|---|
| soft (1 000 N/m) | 0.368730 | 0.365492 | −0.003238 (−0.88 %) | 368.730 | 365.492 |
| stiff (20 000 N/m) | 0.398294 | 0.394519 | −0.003775 (−0.95 %) | 19.915 | 19.726 |

Candidate receipt checks: `passed=true`; 4 reversed-order trials;
repeat-relative difference 2.7e-09 (soft) / 0 (stiff); force-vs-reference
error ≤ 0.0038 N (tolerance 0.02 N); `direction_check=true`;
`log_verified=true`; viewer A/B selection verified. Offline suites re-run
against the same chain: 6 comparison-contract tests + 23 compiler tests,
29 passed.

## Provenance

- **Native binary (the variable):** built from a clean detached worktree at
  the pinned commit `def4d82ddf67f8116e947ae5c5f5e662988f391f`
  (`cmake -S ChimeraEngine/engine -B .tmp/body-engine` +
  `cmake --build .tmp/body-engine --config Release`), SHA-256
  `b2fd55366f5309740f2d57fa052e3da020d04c13c7b0a026443572c7c68c5e22`.
  Shader hashes are recorded in `receipt.json` (`shader_sha256`).
- **Python chain (held constant):** `runner.py`, `cradle_recipe.py`,
  `b2_scene_gen.py`, `packet.py`, `material_volume.py`, `client.py` are
  **untracked working code** (authored outside this branch's commits); each
  was verified byte-identical to the predecessor run before launching
  (all six `source_sha256` entries match the predecessor receipt). The
  experiment spec `cradle.json` is unchanged (`c74ac41e…`).
- **Predecessor:** `docs/evidence/recipe_comparison_20261013/receipt.json`,
  `native_sha256 c8a36cc2b5bf5892…`, `passed=true`, produced pre-B8. Also
  untracked at authoring time; preserved as found.

## Capture retention

Per `docs/evidence/CAPTURE_RETENTION.md`, the five 7.4 MB captures and the
3.3 MB `native/` payload were **deleted after extraction**:
`CAPTURE_DIGEST.json` records each deleted image's SHA-256, dimensions,
content check, and the physics it demonstrated (per-trial settled COM,
weld force, equivalent extension, final state hash). The receipt's
`artifacts_sha256` independently hashed those same bytes before deletion,
so the audit chain survives the pixels.

## Freshness check for later readers

```
python -B -m tools.recipe_experiments.runner --check-result docs/evidence/recipe_comparison_rc1_def4d82d/receipt.json
```

Any change to the native binary, the Python chain, or `cradle.json` marks
this receipt stale by the §11.13.1 rule; re-run against the new candidate and
add a row here rather than editing either receipt.
