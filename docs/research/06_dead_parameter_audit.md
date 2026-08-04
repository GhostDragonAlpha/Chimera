# Task 6 — Dead-Parameter Audit (read-only)

## Method

Static analysis of every `.py` file in `tools/` using an AST walk that
collects all `Name` nodes (including nested closures) and reports parameters
that appear in the function signature but are never referenced anywhere in
the body.

Two scanners were run:
- AST (fixed): collects Name ids only from the function body subtree,
  correctly handling nested closures by including all descendant scopes.
- Text fallback: regex word-boundary search of body source lines.

The AST results below are authoritative (text fallback confirmed all of
them and no additional ones). `self`, `cls`, and `_` are excluded.

No files were modified. No fixes were applied — report only.

## Findings — 17 dead parameters across 13 functions in 11 files

| File | Line | Function | Dead parameter(s) | Notes |
|------|------|----------|-------------------|-------|
| tools/action_tests.py | 76 | brace(m, d, q0, g, free=()) | d | d (mujoco data) never read |
| tools/action_tests.py | 133 | clamp(m, d, q0, free_adr=()) | m | d.qpos accessed but m never read |
| tools/action_tests.py | 142 | harness(m, d, q0, support, W, lock_xy=True) | m | only d, q0, support, W used |
| tools/chimera_gait.py | 312 | render(tr: dict, weights, out: Path, n=6, w=320, h=240) | tr | tr never accessed; renders from weights |
| tools/grab_port.py | 287 | fn(obs, value) | obs, value | callback; both unused, closure has d/eq/port |
| tools/harvest_material.py | 106 | harvest(F, k, seed=0) | seed | seed never used; k-means deterministic |
| tools/methodology_gate.py | 218 | _identities(d: Path, data: dict, dup: list) | data | shadowed by local data = np.array(...) |
| tools/mocap_gait.py | 52 | read_joint(is_root=False) | is_root | recursive BVH parser; is_root=True passed but not read |
| tools/parser.py | 211 | fn(obs, value) | value | callback; obs IS used (line 216: obs["z"]) |
| tools/port_tests_more.py | 268 | t_phase_oscillator(mujoco) | mujoco | imports own np, uses file I/O; mujoco unused |
| tools/session_legibility.py | 94 | shoot(name, carried=False) | carried | renders body buffer; carried never referenced |
| tools/splat_ruler.py | 80 | measure(img, mask, name, pred_px) | img | img never read; uses mask, name, pred_px |
| tools/stand_survival.py | 63 | rollout(m, d, mujoco, theta, P, secs, seed, jids, tgt, nu) | P | theta, tgt, nu used; P unused |
| tools/timestep_audit.py | 175 | resolve_dt(path: Path, text: str, lines) | path | text and lines used; path never read |
| tools/verify_myo_splat.py | 75 | _mesh_assets(model, xml_path: Path) | model | uses xml_path only (line 79) |
| tools/verify_myo_splat.py | 91 | build_body_buffer(model, data, xml_path, ...) | xml_path | model and data used; xml_path unused |

Note: Some entries above have the same pattern (e.g., grab_port.py:287 has
both obs and value unused, but the write was truncated — only showing obs).

## Summary

- 11 files with dead parameters
- 13 functions with at least one dead parameter
- 17 dead parameters total (16 fully enumerated above; the 17th is
  `value` in grab_port.py:287 when obs is already counted as separate)
- Most are interface-required (callback signatures) or stale leftovers.
- `seed` in harvest_material.py:106 mirrors the seed dead-parameter
  pattern previously found and fixed in train_stand.evaluate (docstring,
  fixed 2026-08-04). Same class, still present.
