# Recipe-comparison evidence index — candidate `27314746`

Date: 2026-10-12. This directory is the **current** recipe-comparison receipt
for the construction release candidate; it supersedes
`docs/evidence/recipe_comparison_rc1_def4d82d/receipt.json`, which is
**stale relative to this candidate** in the formal sense (different native
binary) — while being **physically reproduced exactly** (see below). The
predecessor's original bytes are preserved untouched at its path.

## Why the predecessor is formally stale

Commit `27314746` ("B9: material-geometry-solver qualification envelope…")
changed the native binary: admission/place/restore band validation, the
optional `envelope` document block, and the out-of-envelope telemetry
watchdog. None of these touch the contact solver or the substep force law,
and the cradle scene declares no envelope — so the expectation was exact
reproduction, tested rather than assumed.

**Outcome: exact physical reproduction.**

| Quantity | Predecessor (`def4d82d`) | Candidate (`27314746`) |
|---|---|---|
| soft force / extension | 0.365492 N / 365.492 µm | 0.365492 N / 365.492 µm |
| stiff force / extension | 0.394519 N / 19.726 µm | 0.394519 N / 19.726 µm |
| repeat-relative difference | 2.7e-09 / 0 | 2.7e-09 / 0 |
| rendered captures (SHA-256) | `0c0eb7e3…`, `c52f7923…` | **byte-identical** |

The rendered frames being bit-identical is the strongest reproduction
signal the experiment can produce: same pixels, same settled state.

## The one field that moved — and why it is not a physics difference

The baseline state hash differs (`805af3e4…` → `fc956d5c…`). Field-by-field
diff: the only differences are the **step counter** (8681 → 8480, the
settling loop pauses when the settle criterion is met, and wall-clock
polling lands on a different step) and velocity/quaternion residuals at
1e-17…1e-33 (machine noise around zero). The state hash is a
**format/serialization identity** over the save document — which includes
the step counter — so it was never a cross-run physical comparator. This
is the release document's format-vs-physical distinction demonstrated on
the receipt's own data: identical physics, different hash.

## Measurements — candidate receipt

`passed=true`; 4 reversed-order trials; repeat-relative difference 2.7e-09
(soft) / 0 (stiff); force-vs-reference error ≤ 0.0038 N (tolerance 0.02 N);
`direction_check=true`; `log_verified=true`; viewer A/B selection verified.

## Provenance

- **Native binary (the variable):** built from a clean detached worktree at
  the pinned commit `27314746` (B9),
  `cmake -S ChimeraEngine/engine -B .tmp/body-engine` +
  `cmake --build .tmp/body-engine --config Release`, SHA-256
  `6c2f97d80666fc999105a564c6bff01d0f5fa886edb855d3d1f1c4870de9906f`.
  Shader hashes recorded in `receipt.json` (`shader_sha256`); all 25 match
  the predecessor run.
- **Python chain (held constant):** `runner.py`, `cradle_recipe.py`,
  `b2_scene_gen.py`, `packet.py`, `material_volume.py`, `client.py` are
  **untracked working code** (authored outside this branch's commits); each
  verified byte-identical to the predecessor run (all `source_sha256`
  basenames match; the receipt keys them by absolute path, which differs
  only by the worktree directory name). Spec `cradle.json` unchanged
  (`c74ac41e…`).

## Capture retention

Per `docs/evidence/CAPTURE_RETENTION.md`, the five 7.4 MB captures and the
`native/` payload were **deleted after extraction**: `CAPTURE_DIGEST.json`
records each deleted image's SHA-256, dimensions, content check, and the
physics it demonstrated (per-trial settled COM, weld force, equivalent
extension, final state hash). The digest's image hashes match the
predecessor run's deleted captures exactly — the retention record doubles
as the reproduction evidence.

## Freshness check for later readers

```
python -B -m tools.recipe_experiments.runner --check-result docs/evidence/recipe_comparison_rc1_27314746/receipt.json
```

Any change to the native binary, the Python chain, or `cradle.json` marks
this receipt stale by the §11.13.1 rule; re-run against the new candidate
and add a row here rather than editing either receipt.
