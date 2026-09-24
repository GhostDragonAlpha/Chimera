# M03 REPORT — non-unit `scale_to_m`: mass / COM / full-inertia scaling

**Agent:** M03_scale · **Date:** 2026-09-24 · **Workspace:** worktree `E:/ChimeraWork/mvc-20260924`
(branch `material-volume-campaign-20260924`, base `3db8bc4e`) · **Mode:** validation-only, CPU-only.
**Verdict: EXPORTER VERIFIED for non-unit `scale_to_m`** — with one preregistration anchor erratum
logged (falsifier fired against the frozen document; root cause agent-side, receipts preserved).
**No tools/ or docs/ changes. No decision request required. STOP.**

---

## 1. Contract as read (what the documents and schemas say)

| Source | Contract statement |
|---|---|
| `Chimera/docs/matter/material_volume_admission.md` (line 30) | `coordinate_frame` carries a **descriptive** `coordinate_unit` and a positive finite `scale_to_m`; "**every input position is multiplied by this scale to obtain metres**"; "no reflection, frame conversion, or automatic registration". |
| Same doc (line 93) | Out of scope: "implicit unit conversion **beyond the declared positive uniform `scale_to_m`**" — `scale_to_m` is the ONLY unit conversion. |
| Same doc (line 69) | "For constant density, a uniform scale `s` changes volume and mass by `s^3` and COM-relative inertia by `s^5`." |
| `Chimera/docs/matter/material_volume_compiler.md` (lines 24-26, 90) | Compiler input is SI (`coordinate_unit: "m"`, `density_unit: "kg/m^3"`, "v1 does no implicit conversion"); under uniform scale `V -> s^3 V`, `m -> s^3 m`, `I -> s^5 I`. |
| `Chimera/docs/matter/material_volume_body_export.md` (Authored frames) | `x_domain = R_domain_from_body * x_body + origin_domain_m`; exporter writes body-frame COM as `R^T(COM_domain - origin)` and inertia as `R^T I_domain R`; mass/volume frame-invariant; COM/inertia named in the authored frame (m, kg*m^2). |
| `tools/material_volume_admission_schema.json` | `scale_to_m`: number, exclusiveMinimum 0; `coordinate_unit`: free identifier. |
| `tools/material_volume_body_export_schema.json` | body frame `coordinate_unit` const `"m"`; `origin_m`: "Authored transform x_domain = rotation * x_body + origin_m." — origin is in **metres**, not mesh units. |
| Code path (read-only) | `material_volume_admission.py::_compiler_input` (`coordinate * scale`), `material_volume_body_export.py` (scale applied to partition vertex positions ONLY; `origin_m` used as-is in `_body_mass_properties`). |

**Gap closed:** the existing check `material_volume_admission_checks.py::test_uniform_geometric_scale_changes_identity_and_obeys_mass_property_laws` scales vertex POSITIONS at fixed `scale_to_m: 1.0`; no proof exercised a non-unit `scale_to_m` **declaration** on unchanged mesh coordinates through admission + body export, and none tested the origin interaction (§2b).

## 2. Independent derivation (stated before the runs)

Assumptions: raw coordinates are mesh numbers; `scale_to_m = s` is the only unit conversion; density is
declared in SI kg/m^3 and is NOT rescaled; the authored body frame is fixed across runs.

**(a) Bulk laws.** Edges proportional to s means `V(s) = s^3 V(1)`; `m = rho*V` with rho fixed in SI means
`m(s) = s^3 m(1)`; centroid linear in coordinates means `C_domain(s) = s C_domain(1)`; inertia about COM
`I = integral rho(|r|^2 delta - r r^T) dV` with `r` proportional to s and `dV` to s^3 means **every one of
the 9 entries** scales as s^3 * s^2 = s^5, diagonals and off-diagonals alike.

**(b) The mixed question (origin interaction).** The contract converts units ONLY via raw positions x s;
`origin_m` is authored in metres directly (field name, schema description, body-frame
`coordinate_unit: "m"`). Hence `origin_m` must NOT be multiplied by s, and the exported body-frame COM
obeys the **affine law**

```
COM_body(s) = R^T (s*c1 - o) = s*COM_body(1) + (s-1)*R^T*o
```

- `o = 0` gives pure linear (`s*COM_body(1)`).
- `o != 0` means pure linearity is FALSE by design. An implementation that scaled `origin_m` by s would
  produce `s*COM_body(1)` even for `o != 0`; a body group with non-zero origin therefore
  **discriminates** the two readings. The contract's own semantics predict the AFFINE law.
- Inertia about the COM is origin-free, so exactly s^5 regardless of `o`.

**(c) Reconciliation.** First principles and the doc contract AGREE on all laws (s^3 / s^3 / s-linear
domain COM / s^5 / affine body COM). **No DECISION REQUEST is required.** Two contract observations
recorded (consistency notes, not conflicts):

1. `coordinate_unit` is descriptive of the RAW coordinates, so at non-unit `s` an honest fixture must
   not say `"m"`; this fixture declares `"mesh-unit"` at every scale. The existing check
   `test_equivalent_coordinate_units_preserve_si_identity_and_mass_properties` (declares
   `"half-metre"`, scale 0.5) confirms this reading.
2. Practical consequence for callers: re-fitting the same mesh at a different declared factor while
   keeping an authored `origin_m` moves the exported body-frame COM AFFINELY, not linearly — the
   metre-valued origin is deliberately unscaled. Consumers (contract v1 proposal) should state this.

## 3. Preregistration (frozen before execution)

- Document: `PREREG.md`, **sha256 `59adffa63f477e67bfe14ec9a685a3a925843a9a7b69867df79a0dd5af45460a`**
  (recorded in `receipts/prereg_sha256.txt`; mtime order proves freeze: PREREG.md 13:30:20 < hash
  receipt 13:31:05 < first run 13:31:48 local).
- Fixture: one two-tetrahedron coupon (cell-A unit right tet at origin, rho=12; cell-B unit right tet at
  (3,-2,1), rho=6 — same layout as the existing exporter example, so cross-checkable), byte-identical
  mesh coordinates at every scale, only `scale_to_m` varying. Body A: R=I, `origin_m=(0,0,0)`;
  body B: R = 90-degree z-rotation, `origin_m=(3,-2,1)` (non-zero origin, discriminates §2b).
- Runs: s in {1.0, 0.5, 2.0, 0.065} (0.065 = the project's real mesh factor).
- Tolerance (frozen): `|observed - expected| <= 1e-9 * |expected|` relative, all quantities.
- Falsifier (frozen): any quantity deviating beyond tolerance, or any refusal/error on schema-valid input.
- Stop rule (frozen): all scales run, every quantity verdicted, failures preserved, then STOP.
- Fixtures: `fixtures/manifest_s{1p0,0p5,2p0,0p065}.json`, `fixtures/partition_s*.json`,
  `fixtures/groups.json` — **9/9 validate against the EXISTING schemas**
  (`receipts/schema_validation.txt`, jsonschema Draft 2020-12).

## 4. Receipts (4 scales x commands / exit codes)

```
admission s1p0 exit=0     (python work/material_volume_admission.py --manifest fixtures/manifest_s1p0.json --partition fixtures/partition_s1p0.json)
export    s1p0 exit=0     (python work/material_volume_body_export.py --manifest ... --partition ... --groups fixtures/groups.json)
admission s0p5 exit=0
export    s0p5 exit=0
admission s2p0 exit=0
export    s2p0 exit=0
admission s0p065 exit=0
export    s0p065 exit=0
reader    s0p5 exit=0     (python work/material_volume_body_export_reader.py receipts/export_s0p5.json)
```

All 9 runs: admission `validation_only_admissible`, export `complete` (both bodies `exported`), all
exit 0. Module copies under `work/`; `PYTHONDONTWRITEBYTECODE=1` throughout; stdout preserved verbatim
in `receipts/`.

## 5. Results — three verdict layers, reported honestly

**Layer C — LAW / RATIO TESTS (anchor-free; the objective of this task): 39/39 PASS, worst relative
deviation 7.90e-16.** Mass, volume, geometric volume, combined mass: ratio exactly s^3. Domain COM and
zero-origin body COM: exactly s. All 9 inertia entries of both bodies and the combined tensor: exactly
s^5. Body-B COM (o != 0): affine law, max deviation 1.2e-16; the pure-linear alternative is refuted by
relative deviations of 115x (x), 173x (y), 58x (z) — **`origin_m` is provably NOT scaled by
`scale_to_m`, exactly as the metre-valued-origin contract requires.** Observed examples: body-B COM at
s=0.5 = (1.125, 1.625, -0.375) = affine prediction, vs pure-linear (0.125, 0.125, 0.125).

**Layer A — PREREG-AS-FROZEN absolute comparison: 35/42 PASS; falsifier FIRED on 7 quantities** —
`B.I[xy]`, `B.I[yx]`, `B.I[yz]`, `B.I[zy]` (relative deviation exactly 2.0 = sign flip) and
`comb.I[xx]`, `comb.I[yy]`, `comb.I[zz]` (relative ~0.48). **Root cause: two arithmetic slips in this
agent's hand-derived anchors, not in the exporter** — full demonstration, corrected values, and the
independent trace check (trace 15.675 = 1881/120) are logged in `ERRATA.md`. Receipts preserved;
`PREREG.md` itself not edited after the freeze.

**Layer B — CORRECTED ANCHORS (logged errata): 42/42 PASS, worst relative deviation 7.40e-16**
(float64 roundoff; tolerance headroom greater than 6 orders of magnitude).

### Ratio table (per quantity: observed ratio vs derived law)

| quantity | law | s=0.5 observed vs law | s=2.0 observed vs law | s=0.065 rel dev vs law | max rel dev | verdict |
|---|---|---|---|---|---|---|
| `A.I[xx]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 3.65e-16 | 3.65e-16 | PASS |
| `A.I[xy]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 5.48e-16 | 5.48e-16 | PASS |
| `A.I[xz]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 5.48e-16 | 5.48e-16 | PASS |
| `A.I[yx]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 5.48e-16 | 5.48e-16 | PASS |
| `A.I[yy]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 3.65e-16 | 3.65e-16 | PASS |
| `A.I[yz]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 5.48e-16 | 5.48e-16 | PASS |
| `A.I[zx]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 5.48e-16 | 5.48e-16 | PASS |
| `A.I[zy]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 5.48e-16 | 5.48e-16 | PASS |
| `A.I[zz]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 3.65e-16 | 3.65e-16 | PASS |
| `A.com[x]` | s | `0.5` vs 0.5 | `2` vs 2 | 0.00e+00 | 0.00e+00 | PASS |
| `A.com[y]` | s | `0.5` vs 0.5 | `2` vs 2 | 0.00e+00 | 0.00e+00 | PASS |
| `A.com[z]` | s | `0.5` vs 0.5 | `2` vs 2 | 0.00e+00 | 0.00e+00 | PASS |
| `A.mass_kg` | s^3 | `0.125` vs 0.125 | `8` vs 8 | 5.92e-16 | 5.92e-16 | PASS |
| `A.volume_m3` | s^3 | `0.125` vs 0.125 | `8` vs 8 | 7.90e-16 | 7.90e-16 | PASS |
| `B.I[xx]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 3.65e-16 | 3.65e-16 | PASS |
| `B.I[xy]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 7.30e-16 | 7.30e-16 | PASS |
| `B.I[xz]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 5.48e-16 | 5.48e-16 | PASS |
| `B.I[yx]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 7.30e-16 | 7.30e-16 | PASS |
| `B.I[yy]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 3.65e-16 | 3.65e-16 | PASS |
| `B.I[yz]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 5.48e-16 | 5.48e-16 | PASS |
| `B.I[zx]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 5.48e-16 | 5.48e-16 | PASS |
| `B.I[zy]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 5.48e-16 | 5.48e-16 | PASS |
| `B.I[zz]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 3.65e-16 | 3.65e-16 | PASS |
| `B.com[x]` | affine | `1.125` vs affine `1.125` | `-1.5` vs affine `-1.5` | 1.18e-16 | 1.18e-16 | PASS |
| `B.com[y]` | affine | `1.625` vs affine `1.625` | `-2.5` vs affine `-2.5` | 0.00e+00 | 0.00e+00 | PASS |
| `B.com[z]` | affine | `-0.375` vs affine `-0.375` | `1.5` vs affine `1.5` | 1.21e-16 | 1.21e-16 | PASS |
| `B.mass_kg` | s^3 | `0.125` vs 0.125 | `8` vs 8 | 5.92e-16 | 5.92e-16 | PASS |
| `B.volume_m3` | s^3 | `0.125` vs 0.125 | `8` vs 8 | 7.90e-16 | 7.90e-16 | PASS |
| `comb.I[xx]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 1.83e-16 | 1.83e-16 | PASS |
| `comb.I[xy]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 5.48e-16 | 5.48e-16 | PASS |
| `comb.I[xz]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 1.83e-16 | 1.83e-16 | PASS |
| `comb.I[yx]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 5.48e-16 | 5.48e-16 | PASS |
| `comb.I[yy]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 3.65e-16 | 3.65e-16 | PASS |
| `comb.I[yz]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 1.83e-16 | 1.83e-16 | PASS |
| `comb.I[zx]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 1.83e-16 | 1.83e-16 | PASS |
| `comb.I[zy]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 1.83e-16 | 1.83e-16 | PASS |
| `comb.I[zz]` | s^5 | `0.03125` vs 0.03125 | `32` vs 32 | 3.65e-16 | 3.65e-16 | PASS |
| `comb.com[x]` | s | `0.5` vs 0.5 | `2` vs 2 | 0.00e+00 | 0.00e+00 | PASS |
| `comb.com[y]` | s | `0.5` vs 0.5 | `2` vs 2 | 2.14e-16 | 2.14e-16 | PASS |
| `comb.com[z]` | s | `0.5` vs 0.5 | `2` vs 2 | 0.00e+00 | 0.00e+00 | PASS |
| `comb.mass_kg` | s^3 | `0.125` vs 0.125 | `8` vs 8 | 0.00e+00 | 0.00e+00 | PASS |
| `geo.volume_m3` | s^3 | `0.125` vs 0.125 | `8` vs 8 | 1.97e-16 | 1.97e-16 | PASS |

Worst relative deviation over all 42 quantities x 4 scales (including s=1 vs exact anchors in
`receipts/analysis.json`, corrected layer: 7.40e-16): **7.896e-16** vs frozen tolerance 1e-09.
All 42 PASS.

## 6. s = 0.065 (the project's real mesh factor) — flag

**Nothing special happened, and the prereg predicted nothing special**: the compiler's nondegeneracy
gate `|det|/max_edge^3` and the overlap contact tolerance `128*eps*max(edge)` are scale-INVARIANT
ratios; s=0.065 is an ordinary float64 magnitude; no code branch keys on scale size. All 42 quantities
pass at s=0.065 (worst 7.9e-16). Observed: body-A mass 0.00054925 kg, body-A COM
(0.01625, 0.01625, 0.01625) m, body-B COM (1.88625, 2.82125, -0.91875) m (affine, dominated by the
metre-valued origin), combined mass 0.000823875 kg. Geometry signatures correctly DIFFER across scales
(each declared SI geometry is its own identity): `0dec4196...`, `5d8f9ea6...`, `ca209d10...`, `9b1fb615...`.

## 7. Integrity

```
$ git status --porcelain -- tools Chimera/docs/matter
(empty — exit 0, no output)
```

No `__pycache__` in `tools/`; no writes outside `agents/M03_scale/` (worktree status shows only the
expected untracked `material_volume_campaign/agents/*` directories). tools/ and Chimera/docs/matter
were used read-only.

## 8. Artifacts

- `brief.md` — task brief (verbatim copy)
- `PREREG.md` — frozen preregistration (sha256 59adffa6..., unmodified after freeze)
- `ERRATA.md` — logged anchor corrections E1/E2 (campaign-law correction receipt)
- `fixtures/` — 9 schema-valid fixture documents (4 manifest/partition pairs + groups)
- `work/` — module copies + `make_fixtures.py`, `validate_fixtures.py`, `analyze.py`
- `receipts/` — `run_log.txt`, per-scale admission/export JSON + stderr, `schema_validation.txt`,
  `reader_s0p5.json`, `analysis.json` (all three verdict layers), `ratio_table.md`, `prereg_sha256.txt`

## 9. Verdict

Non-unit `scale_to_m` is **proven correct end-to-end** under the existing density/unit contract:
mass and volume scale as s^3, domain and zero-origin body-frame COM as s, non-zero-origin body-frame
COM follows the derived affine law `s*COM(1) + (s-1)*R^T*o` (origin_m in metres, unscaled), and all 9
inertia-tensor entries scale as s^5 — through the full admission + body-export path, at
s in {1.0, 0.5, 2.0, 0.065}, within 7.9e-16 relative of the independent derivation (frozen tolerance
1e-9). The one falsifier firing traces to preregistered-anchor arithmetic (logged in ERRATA.md), not
to the exporter. Stop rule satisfied: all runs executed, every quantity verdicted, failures preserved.
STOP.
