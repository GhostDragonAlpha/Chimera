# M03 PREREGISTRATION — non-unit `scale_to_m` scaling proof

**Agent:** M03_scale · **Campaign:** material-volume 24h (worktree `E:/ChimeraWork/mvc-20260924`, base `3db8bc4e`)
**Status:** FROZEN BEFORE EXECUTION. Any change after the freeze hash below invalidates this prereg.
**Freeze:** this file is hashed to `receipts/prereg_sha256.txt` before the first exporter/admission run.

---

## 1. Contract as read (citations)

- `Chimera/docs/matter/material_volume_admission.md` §Manifest contract, row `coordinate_frame`:
  "`frame_id`, right-handedness (`right` only), **descriptive `coordinate_unit`**, and positive finite
  `scale_to_m`. **Every input position is multiplied by this scale to obtain metres.** No reflection,
  frame conversion, or automatic registration is attempted." (line 30)
  §Unsupported: "no implicit unit conversion **beyond the declared positive uniform `scale_to_m`**" (line 93).
  §Canonical identity: "For constant density, a uniform scale `s` changes volume and mass by `s^3` and
  COM-relative inertia by `s^5`" (line 69).
- `Chimera/docs/matter/material_volume_compiler.md` §Derivation: "Under a uniform coordinate scale `s`,
  `V -> s^3 V`, `m -> s^3 m`, and `I -> s^5 I`." (line 90). Input contract `chimera.material_volume.v1`:
  `coordinate_unit` exact `m`, `density_unit` exact `kg/m^3`, "v1 does no implicit conversion" — this
  applies to the compiler's already-scaled SI input, not to the raw manifest/partition coordinates.
- `Chimera/docs/matter/material_volume_body_export.md` §Authored frames and tensor contract:
  `x_domain = R_domain_from_body * x_body + origin_domain_m`; "The exporter computes the volume
  properties in domain coordinates, then writes the COM as `R^T (COM_domain - origin)` and the full COM
  inertia as `R^T I_domain R`." Mass/volume frame-invariant; COM/inertia in the authored body frame (m, kg·m²).
- Code path (read, not modified): `tools/material_volume_admission.py` `_frame` (scale positive finite),
  `_compiler_input` (`vertices_m = coordinate * scale`), `_geometry_signature` (scale applied before hashing);
  `tools/material_volume_body_export.py` (scale applied to partition vertex positions only, then
  `_integrate_cells`, then `_body_mass_properties` uses `origin_m` as-is).
- Schemas: `material_volume_admission_schema.json` `coordinateFrame.scale_to_m` = positive number;
  `coordinate_unit` = free identifier (descriptive). `material_volume_body_export_schema.json`
  `bodyFrame.coordinate_unit` = const `m`; `origin_m` = vector3, described in metres.

**Gap being closed:** the existing check `material_volume_admission_checks.py::test_uniform_geometric_scale_changes_identity_and_obeys_mass_property_laws` scales vertex POSITIONS at fixed `scale_to_m: 1.0`. No proof exercises a non-unit `scale_to_m` DECLARATION on unchanged mesh coordinates through admission + body export, and none touches the origin interaction below.

## 2. Independent derivation (first principles, before reading any expected numbers from code)

Assumptions: density is declared in SI (`kg/m^3`) and is constant under re-declaration of the mesh→metre
factor; raw vertex coordinates are mesh numbers; `scale_to_m = s` is the only unit conversion; the
exported density values are never multiplied by `s`.

Let mesh coordinates be `x = s·u` where `u` is the raw mesh position. For any tetrahedral complex,

- Volume: `V = (1/6)|det(x1-x0, x2-x0, x3-x0)|` — each edge ∝ s ⇒ **`V(s) = s³·V(1)`**.
- Mass: `m = ρ·V` with ρ fixed in SI ⇒ **`m(s) = s³·m(1)`**.
- COM: `C = Σ m_t c_t / M`, each cell centroid ∝ s ⇒ **`C_domain(s) = s·C_domain(1)`** (domain frame, origin at mesh origin).
- Inertia about COM: `I = ∫ρ(|r|²δ − r r^T)dV`, `r` measured from COM; `r ∝ s`, `dV ∝ s³` ⇒ every entry
  (diagonal AND off-diagonal, all 9) ∝ s³·s² = **`s⁵`**: `I(s) = s⁵·I(1)`.

### The mixed question: does `scale_to_m` interact with `origin_m`?

The contract says the ONLY unit conversion is raw positions × `scale_to_m`; `origin_m` is authored
directly in metres (its name, its schema description `x_domain = R·x_body + origin_m`, and body-frame
`coordinate_unit: "m"`). Therefore `origin_m` is NOT multiplied by `s`. The exported body-frame COM is

```
COM_body(s) = R^T (COM_domain(s) − o) = R^T (s·c₁ − o)
            = s·COM_body(1) + (s−1)·R^T·o          [derived law: AFFINE in s]
```

where `c₁` is the s=1 domain COM. Corollaries:
- For `o = 0`: `COM_body(s) = s·COM_body(1)` exactly (pure linear).
- For `o ≠ 0`: pure linearity is FALSE, by design. A hypothetical implementation that scaled `origin_m`
  by `s` (treating the origin as mesh units) would produce `s·COM_body(1)` even when `o ≠ 0`. A body
  group with `o ≠ 0` therefore DISCRIMINATES the two interpretations; the contract's own semantics
  predict the AFFINE law. Inertia about the COM is origin-free ⇒ exactly `s⁵` regardless of `o`.

**Reconciliation verdict:** first principles and the doc contract AGREE (s³ / s³ / s-linear-in-domain /
s⁵ / affine-in-s body COM). No DECISION REQUEST is required on the scaling laws themselves. One
labelling note is recorded (not a conflict): `coordinate_unit` is descriptive of the RAW coordinates, so
at non-unit `s` an honest fixture must not declare `"m"`; the existing check
`test_equivalent_coordinate_units_preserve_si_identity_and_mass_properties` (declares `"half-metre"`,
scale 0.5) confirms this reading. This fixture declares `"mesh-unit"` at every scale.

## 3. Fixture (hand-derivable; exactly one fixture, four runs)

Geometry = the existing two-body coupon layout (mesh numbers IDENTICAL at every scale; only
`coordinate_frame.scale_to_m` varies):

- cell-A: vertices `a0..a3 = (0,0,0), (1,0,0), (0,1,0), (0,0,1)`, region-A → tissue-A, ρ_A = 12 kg/m³.
- cell-B: vertices `b0..b3 = (3,−2,1), (3,−1,1), (2,−2,1), (3,−2,2)`, region-B → tissue-B, ρ_B = 6 kg/m³.
  (edges from b0: (0,1,0),(−1,0,0),(0,0,1); det = +1 ⇒ positive orientation, V = 1/6.)
- `coordinate_frame`: `frame_id: "m03-mesh-frame"`, right, `coordinate_unit: "mesh-unit"`, `scale_to_m: s`.
- Groups (`chimera.rigid_body_cell_groups.v1`, scale-independent, ONE file):
  - body `m03-body-A` ← cell-A; R = I, `origin_m = (0,0,0)`.
  - body `m03-body-B` ← cell-B; R = `[[0,−1,0],[1,0,0],[0,0,1]]` (proper, det +1), `origin_m = (3,−2,1)`.

Scales under test (frozen): **s ∈ {1.0, 0.5, 2.0, 0.065}** (0.065 = the project's real mesh factor).

### Hand-derived anchors at s = 1 (exact fractions; derived by hand from the coordinates above)

Body A (identity frame, o = 0): m = 2 kg; V = 1/6 m³; COM_body = (1/4, 1/4, 1/4);
`I_A(1) = [[3/20, 1/40, 1/40], [1/40, 3/20, 1/40], [1/40, 1/40, 3/20]]`
(second moment S: diag 3/4, off −1/4; Q = (m/20)S; I = tr(Q)E − Q, m = 2).

Body B (in its authored body frame the tet is (0,0,0),(1,0,0),(0,−1,0),(0,0,1), centroid (1/4,−1/4,1/4), m = 1):
COM_body = R^T((11/4,−7/4,5/4) − (3,−2,1)) = R^T(−1/4,1/4,1/4) = **(1/4, 1/4, 1/4)**;
`I_B(1) = [[3/40, −1/80, 1/80], [−1/80, 3/40, −1/80], [1/80, −1/80, 3/40]]`.

Combined (admission report, domain frame): m = 3 kg; V = 1/3 m³; C = (13/12, −5/12, 7/12);
`I_comb(1)`: xx 347/144, yy 491/144, zz 683/144, xy 803/240, xz −397/240, yz 329/240
(parallel-axis by hand: d_A = (−5/6, 2/3, −1/3), d_B = (5/3, −4/3, 2/3), d_A² = 5/4, d_B² = 5).

### Frozen laws applied to anchors

- `mass(s) = s³·mass(1)`; `volume(s) = s³·volume(1)`
- `COM_A(s) = s·(1/4, 1/4, 1/4)` (o = 0, pure linear)
- `COM_B(s) = s·(1/4,1/4,1/4) + (s−1)·(−2,−3,1) = (2 − 7s/4, 3 − 11s/4, 5s/4 − 1)` (AFFINE law;
  R^T·o = (−2,−3,1))
- `I(s) = s⁵·I(1)` — all 9 entries, both bodies, plus the combined domain tensor
- `geometric_volume_m3(s) = s³/3`; combined `mass_kg(s) = 3s³`; combined `center_of_mass_m(s) = s·(13/12, −5/12, 7/12)`

### Per-run expectations (exact values; fractions evaluated in float64 at compare time)

s = 1.0: anchors above.
s = 0.5 (s³ = 1/8, s⁵ = 1/32):
- A: m 1/4; V 1/48; COM (1/8, 1/8, 1/8); I diag 3/640, off 1/1280.
- B: m 1/8; V 1/48; COM (9/8, 13/8, −3/8); I diag 3/1280; off xy −1/2560, xz +1/2560, yz −1/2560.
- Combined: V 1/24; m 3/8; COM (13/24, −5/48, 7/48); I = anchors/32.

s = 2.0 (s³ = 8, s⁵ = 32):
- A: m 16; V 4/3; COM (1/2, 1/2, 1/2); I diag 24/5, off 4/5.
- B: m 8; V 4/3; COM (−3/2, −5/2, 3/2); I diag 12/5; off xy −2/5, xz +2/5, yz −2/5.
- Combined: V 8/3; m 24; COM (13/6, −5/6, 7/6); I = 32·anchors.

s = 0.065 (s³ = 0.000274625, s⁵ = 0.000001160290625):
- A: m 0.00054925; V 0.000274625/6; COM (0.01625, 0.01625, 0.01625); I diag 1.7404359375e−7, off 2.9007265625e−8.
- B: m 0.000274625; V 0.000274625/6; COM (1.88625, 2.82125, −0.91875); I diag 8.7021796875e−8;
  off xy −1.45036328125e−8, xz +1.45036328125e−8, yz −1.45036328125e−8.
- Combined: V 0.000274625/3; m 0.000823875; COM 0.065·(13/12, −5/12, 7/12); I = 1.160290625e−6·anchors.

Prediction for s = 0.065 specifically: NOTHING special. The nondegeneracy gate `|det|/max_edge³` and the
overlap contact tolerance `128·eps·max(cell edge)` are scale-INVARIANT ratios; s = 0.065 is an ordinary
float64 magnitude; no code branch keys on scale size. Flag if anything else surfaces.

## 4. Frozen acceptance criteria

- **Tolerance:** every preregistered quantity satisfies `|observed − expected| ≤ 1e−9 · |expected|`
  (pure relative; every expected value is nonzero). RATIO check: for each quantity,
  `observed(s)/observed(1)` must equal the law ratio (s³ / s / affine / s⁵) within the same tolerance
  (for COM_B the "law ratio" is the affine law itself, tested by absolute value; body A's COM ratio
  must equal s exactly).
- **FALSIFIER:** ANY preregistered quantity at ANY scale deviating beyond the frozen tolerance, OR any
  run refusing/erroring on a schema-valid fixture, fires the falsifier ⇒ defect finding recorded and
  preserved (NO tools/ fixes from this agent).
- **Secondary falsifier (discrimination):** if body-B COM matched the pure-linear law `s·(1/4,1/4,1/4)`
  instead of the affine law, that would mean `origin_m` is being scaled by `scale_to_m` — a contract
  violation and falsifier firing.
- **Stop rule:** all four scales executed and every preregistered quantity carries a pass/fail verdict
  (failures preserved as receipts), then the report is written and work STOPS. No re-runs with adjusted
  tolerances; no fixture or expectation edits after the freeze.
- **Environment:** CPU-only; module copies under `work/`; `PYTHONDONTWRITEBYTECODE=1`; writes confined to
  `agents/M03_scale/`; `tools/` + `Chimera/docs/matter` untouched (integrity paste required in report).

## 5. Run matrix (receipts per scale)

Per scale: (a) schema-validate fixtures against the EXISTING schema files; (b)
`python material_volume_admission.py --manifest ... --partition ...` (exit 0 expected);
(c) `python material_volume_body_export.py --manifest ... --partition ... --groups ...` (exit 0 expected);
stdout saved verbatim to `receipts/`. Analysis reads receipts only.
