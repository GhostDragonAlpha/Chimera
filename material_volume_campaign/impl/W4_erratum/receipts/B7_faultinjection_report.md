# B7 — Fault-Injection Detection Coverage Report

Agent: B7_faultinjection · 2026-09-24 · worktree `E:/ChimeraWork/mvc-20260924`
branch `material-volume-campaign-20260924` · CPU-only · all writes confined to
`material_volume_campaign/agents/B7_faultinjection/` · `tools/` + `docs/` untouched
(module copies in `work/`, `PYTHONDONTWRITEBYTECODE=1` on every invocation).

## 1. What was under test (read before anything ran)

| Module | What it claims to catch |
|---|---|
| `tools/material_volume_body_export.py` (the exporter, generation side) | bad schema/identifiers, non-orthonormal or reflected authored frames, duplicate cell/body ownership, unknown group cells, mixed/unsupported mass authority; **recomputes admission from the actual manifest+partition every call** (no caller flag can bypass); blocks on `missing_density`; refuses non-finite/non-positive mass inputs |
| `tools/material_volume_body_export_reader.py` (the reader, consumption side) | docstring: "validates the output version and each exported mass tensor" — concretely: schema_version, `export_status` enum, group-status/mass_properties consistency, tensor shape (3,3), finiteness, mass>0, symmetry (atol 1e-12), the three tensor contract flags; rejects NaN literals and duplicate JSON keys at load |
| `tools/material_volume_checks.py` (17 tests) | generation-side compiler falsifiers (mass/COM/inertia oracles, topology refusals) — not parameterizable by an arbitrary report file |
| `tools/material_volume_admission_checks.py` (21 tests) | generation-side admission falsifiers (scale_mismatch, missing_density, duplicate_mass_owner_id, ownership collisions) — same, input-side only |
| `tools/material_volume_export_proof_verify.py` (7 tests) | reproduces the three suites (17+21+8), CLI determinism, saved-example bytes, coupon oracle-independence audits — fixed file set, not report-parameterizable |

**Structural fact the matrix is built on:** for a *report artifact* the reader is the
ONLY consumption-time validator that exists. The three suites and the proof verifier
guard generation, not artifacts.

## 2. Baseline (green, before any mutation)

- `exporter.build_export_report` on the tools example inputs (copies in
  `fixtures/inputs/`): `export_status=complete`, `admission_status=validation_only_admissible`,
  `dynamics_readiness_claimed=False`, deterministic across two builds; written to
  `fixtures/valid_report.json` (5472 bytes canonical). coupon-body-A mass 2.0 kg,
  coupon-body-B mass 1.0 kg.
- Clean battery, run read-only in place (`receipts/baseline_battery.txt`):
  body_export_checks **8 tests OK**, material_volume_checks **17 tests OK**,
  admission_checks **21 tests OK**, export_proof_verify **7 tests OK**.
- Environment note: `core.autocrlf=true`, so the saved example report carries a
  trailing CRLF that the CLI stdout also produces on Windows; the proof verifier's
  byte-equality test passes on this checkout. Raw canonical bytes differ from the
  saved file only by that CRLF — checkout artifact, not a defect.

## 3. Frozen matrix (preregistered before execution)

`work/mutation_matrix_frozen.json` — 17 rows (12 canonical mutations, 5 extra
variants/controls), each with target, predicted detector, predicted message,
predicted verdict, written BEFORE any check ran against any corrupted copy. The
runner (`run_mutations.py`) refuses to run without it and judges every observation
against it. **Falsifier (frozen): any predicted-DETECTED row that passes silently
is the headline finding.**

## 4. Detection verdict table (17 mutations)

| ID | Mutation | Predicted | Observed | Verdict |
|---|---|---|---|---|
| M01 | inertia off-diagonal sign flip (body-B [0][1] 0.0125→−0.0125) | DETECTED by reader `nonsymmetric_inertia` | reader exit 2: `nonsymmetric_inertia: body_groups[1] inertia is not symmetric` | **DETECTED-BY** reader (MATCH) |
| M02 | inertia diagonal flip (body-B [0][0] →0.076, symmetric) | MISSED | reader exit 0; wrong tensor reaches consumers | **MISSED — finding F1** |
| M03 | broken tensor symmetry (body-A [0][1]=0.0251 vs [1][0]=0.025) | DETECTED by reader | exit 2: `nonsymmetric_inertia: body_groups[0] inertia is not symmetric` | **DETECTED-BY** reader (MATCH) |
| M04 | mass 2.0→2.5 (body-A) | MISSED | reader exit 0; summary carries `mass_kg=2.5` (`receipts/missed_case_evidence.txt`) | **MISSED — finding F1** |
| M05 | mass 2.0→−2.0 (body-A) | DETECTED by reader | exit 2: `bad_export_report: body_groups[0] has invalid numeric properties` | **DETECTED-BY** reader (MATCH) |
| M06 | COM shift (body-A x 0.25→0.75) | MISSED | reader exit 0 | **MISSED — finding F1** |
| M07 | density 12.0→13.0 inside report provenance (mass left inconsistent) | MISSED | reader exit 0 | **MISSED — finding F1** |
| M07b | CONTROL: density nulled in partition INPUT, report regenerated | DETECTED by exporter/admission revalidation | `export_status=blocked`, `admission=not_admitted`, reason `missing_density`, group mass_properties None (`receipts/M07b_regenerated_report.json`) | **DETECTED-BY** exporter revalidation (MATCH) |
| M08 | delete `material_mass_source_provenance` from exported group | MISSED | reader exit 0 | **MISSED — finding F2** |
| M09 | `mass_owner_id` → `owner-IMPOSTOR` in report provenance | MISSED | reader exit 0 | **MISSED — finding F1** |
| M09b | CONTROL: duplicate mass_owner_id in INPUTS, report regenerated | DETECTED by admission | `export_status=blocked`, `admission=refused`, `compiler_refusal:duplicate_mass_owner_id` (`receipts/M09b_regenerated_report.json`) | **DETECTED-BY** exporter revalidation (MATCH) |
| M10 | top-level `export_status` complete→partial | MISSED | reader exit 0 (enum-accepted; no cross-check vs `unassigned_cell_ids`) | **MISSED — finding F3** |
| M10b | group `export_status` exported→not_exported, mass_properties kept | DETECTED by reader | exit 2: `blocked_group_has_mass: body_groups[0] is not exported but includes properties` | **DETECTED-BY** reader (MATCH) |
| M11 | `dynamics_readiness_claimed` false→true | MISSED (silently dropped) | reader exit 0; file says `true`, reader summary hardcodes `False` — tamper invisible, no warning | **MISSED — finding F4** |
| M12 | `admission_report_sha256` → 64 zeros | MISSED | reader exit 0; digest copied verbatim into summary | **MISSED — finding F5** |
| M13 | truncate tensor row (body-B row 0 → 2 elements) | DETECTED (shape check) | **detected, path differs**: numpy raises uncaught `ValueError` (inhomogeneous shape) at reader line 52; CLI exit 1 with raw traceback, not a named refusal (exit 2) | **DETECTED-BY** reader, PATH-DIFFERS — finding F6 |
| M14 | NaN in tensor (body-A [2][2]) | DETECTED (two paths) | in-process: `bad_export_report: body_groups[0] has invalid numeric properties` (isfinite); file path: strict loader rejects NaN literal (`input_read_error`, exit 2); third layer: `canonical_json(allow_nan=False)` refuses to serialize | **DETECTED-BY** reader + loader + serializer (MATCH) |

**Tally: 8 detected / 9 missed / 0 surprises / 0 falsified.** Full per-row evidence in
`work/results.json`; fixture diffs in `receipts/diffs/M*.diff`; corrupted fixtures
`fixtures/corrupt_M*.json`; mutated input copies `fixtures/inputs_mutated_M{07b,09b}/`.

## 5. Falsifier verdict

**HELD.** No predicted-detectable mutation passed silently. One detection path
differed from its prediction (M13: loud failure via uncaught `ValueError`, exit 1,
instead of the predicted named `ExportInputError`, exit 2) — recorded verbatim in
`receipts/missed_case_evidence.txt`, preserved as finding F6, not tuned away.

## 6. Missed-mutation findings (itemized)

- **F1 — No consumption-time value oracle (M02, M04, M06, M07, M09).** Any
  symmetry-preserving, finite, positive wrong number — a wrong inertia diagonal, a
  scaled mass, a shifted COM, a density inconsistent with the reported mass, an
  impostor `mass_owner_id` — passes the reader at exit 0 and flows to consumers
  unchanged. The reader does exactly what its docstring scopes (version + tensor
  structure), but the campaign should decide: F1 is acceptable ONLY if reports are
  never trusted after generation and are always regenerated alongside revalidation.
  A regeneration-diff would have flagged 15/15 report-level mutations (column
  `regeneration_diff_would_flag` in `work/results.json`) — no such check exists.
- **F2 — Report artifact has no schema gate (M08).** The exporter validates INPUTS
  strictly (`_strict_object`: missing/unknown fields refused); the reader validates
  OUTPUTS loosely: dropping a whole provenance object is invisible. Decision request.
- **F3 — Status enum accepted without consistency check (M10).** `complete→partial`
  passes although `unassigned_cell_ids` is empty; the reader never cross-checks
  status against body_groups/unassigned rows.
- **F4 — Readiness tampering is neutralized silently (M11).** The reader hardcodes
  `dynamics_readiness_claimed: False` in its summary, so a tampered `true` can
  never be promoted — safe by construction — but the corruption is invisible (exit 0,
  no warning code). Decision request: accept silent neutralization, or refuse a
  `true` claim as `bad_export_report`?
- **F5 — Integrity digests are inert at consumption (M12).** `admission_report_sha256`
  and `input_hashes` are computed honestly at generation and copied through
  unverified at consumption; no consumer can recompute them without the original
  inputs. A tampered digest is undetectable by the check layer.
- **F6 — Ragged tensor violates the named-refusal contract (M13).** A truncated
  tensor row is still caught (exit 1), but as an uncaught numpy `ValueError`
  traceback instead of the reader's named `ExportInputError` discipline — the shape
  guard at line 55 is unreachable for non-rectangular input because line 52's
  `np.asarray` raises first.

## 7. Integrity

```
$ git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- tools Chimera/docs/matter
(empty; exit 0)
```

Full-worktree porcelain shows only untracked sibling agent dirs under
`material_volume_campaign/agents/` (B5, B6, B7, B9, M01, M04, M06, M08) — no
modification to any tracked file.

## 8. Artifacts

- `brief.md` — task brief, verbatim
- `work/mutation_matrix_frozen.json` — preregistered matrix + falsifier
- `run_mutations.py` — preregistration-gated runner
- `work/results.json` — per-row observed evidence and judgements
- `fixtures/valid_report.json`, `fixtures/corrupt_M*.json`, `fixtures/inputs/`,
  `fixtures/inputs_mutated_M{07b,09b}/`
- `receipts/baseline_battery.txt`, `receipts/diffs/M*.diff`,
  `receipts/missed_case_evidence.txt`, `receipts/M{07b,09b}_regenerated_report.json`
