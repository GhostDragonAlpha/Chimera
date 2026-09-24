# M10 REPORT — static consumption validator for the v1 mass-export contract

Agent: M10_validator · 2026-09-24 · worktree `E:/ChimeraWork/mvc-20260924`
(branch `material-volume-campaign-20260924`, base `3db8bc4e`)

## ACCEPTANCE VERDICT: MET

All six acceptance criteria of the brief are satisfied, with measured numbers below.
**71/71 tests pass** (pytest, Python 3.14.3). Integrity check empty. No commit made
(none requested); all files live in the worktree under
`material_volume_campaign/agents/M10_validator/`.

## 1. Numbered rule set (frozen BEFORE implementation)

`PREREGISTRATION.md` holds the Rule-0 membrane, rules **R1–R16** plus reader
cross-check **R0**, each quoting the contract line it enforces, and the frozen test
plan. Freeze hashes (append-only amendment A1 recorded a scoping fix found by
inspecting real exporter output — exported bodies carry no per-body readiness flag,
so requiring one would have false-rejected clean reports):

- pre-amendment: `01c3d12b5c1a618c818908058e901b718ec1b3d25dc532bef5ca60911a9cd83f`
- frozen-as-implemented: `a5eb73e9ad18bb9832ee0ea978788d597ed7afcc28f064c515bfc2d973204025`

Rule set in one line each (full contract quotes in PREREGISTRATION.md):
R1 report identity/strict parse · R2 root `export_status` gate (only `complete`
consumable; `partial`/`blocked`/`unsupported`/`refused`/unknown REJECT) · R3
`admission_status == "validation_only_admissible"` exact · R4 hash binding
(presence, 64-lowercase-hex, root↔body consistency on `complete`, optional
recomputation against a supplied admission document) · R5 only `exported` bodies
with non-null properties (no placeholders) · R6 mass (kg, frame-invariant, > 0) ·
R7 volume form (m^3, frame-invariant) · R8 COM (3 finite values, m, in `frame_id`)
· R9 full-tensor integrity (9 entries, exact symmetry, all three flags exact,
kg\*m^2, authored body frame/basis) · R10 body frame (right-handed, meters,
proper-orthonormal rotation refused-never-repaired, tol 1e-12) · R11 ownership
verbatim + provenance travels (CON-8/12) · R12 readiness prohibition with recursive
nested-key scan (CON-14) · R13 fixed v1 safety flags · R14 unassigned cells
surfaced and consistent · R15 no recombination fields · R16 no lineage fields /
v1-only schema.

## 2. Implementation receipts

`receipts/implementation_receipt.txt`: `rigid_body_mass_consumption_validator.py`
sha256 `94c2ee772c4a15db0966fcf963ed13fe2fcb9987f45c5897f8072a62f636f5dd`, CLI
`--help` captured. Static-only by construction: no assembly, no physics-engine
import, no mutation, no promotion/recombination API; verdict JSON carries
`static_only: true, runtime_wiring: false`. Reuses the read-only reader
(`tools/material_volume_body_export_reader.py`) via `sys.path` with
`sys.dont_write_bytecode = True` set before import and `PYTHONDONTWRITEBYTECODE=1`
in every run — reader cross-check R0 runs on the raw report, while all flag checks
read the RAW document (the reader's summary hard-codes readiness `False`; test
`test_validator_reads_raw_report_not_reader_summary` pins this). Hash recomputation
mirrors the exporter's `_canonical_hash` (no trailing newline). No writes outside
`agents/M10_validator/`; `tools/` untouched (`tools/__pycache__` does not exist).

## 3. Accept + reject test table (every rule exercised)

Suite: `tests/test_validator.py` — **71 tests, 71 passed, 0 failed, 0.8s**
(`receipts/test_run.txt`). Fixtures: 53 frozen JSON files in `fixtures/`
(generated deterministically by `fixtures/make_fixtures.py`; the accept fixture is
a verbatim copy of `tools/material_volume_body_export_example_report.json`,
sha256 `d71f7621...` — tools originals never mutated).

| rule | accept evidence | reject fixtures (all REJECT, rule named) |
|---|---|---|
| R0 reader cross-check | accept fixture: reader pass | blocked-with-mass, truncated tensor, case-variant status (reader refusal preserved) |
| R1 identity/parse | accept: schema v1, 2 bodies | (covered by reader strict-parse; unknown version via R16 class) |
| R2 root status | accept: `complete` | partial, blocked, unsupported, refused, unknown `assembled`, case-variant `Complete` |
| R3 admission | accept: exact value root+bodies | `Validation_Only_Admissible`, `admissible` |
| R4 hash binding | accept: consistent 64-hex | missing, 63-char, body≠root, uppercase; recompute match ACCEPTs, mismatch/supplied-wrong-doc tamper-REJECT |
| R5 body status | accept: 2 `exported` bodies | `not_exported` (null props), placeholder-mass `not_exported` |
| R6 mass | accept: 2.0 kg / 1.0 kg | unit `g`, negative, `frame_invariant:false` |
| R7 volume | accept: m^3 | unit `cm^3` |
| R8 COM | accept: in frame_id | frame mismatch, 2-element vector |
| R9 tensor | accept: 9 entries, symmetric, flags exact | truncated (2×3), asymmetric pair, PA=true, off-diag flag false, full flag false, unit `kg m^2`, frame mismatch |
| R10 frame | accept: proper orthonormal, right, m | det=−1, scaled non-orthonormal, `left`, `cm` |
| R11 ownership/provenance | accept: bijective provenance | provenance stripped, owned cell w/o row, conflicting duplicate owner, `mass_owner_ids` mismatch, wrong `mass_source_kind`, source `mass_authority` |
| R12 readiness | accept: flag false, scan clean | root true, body-level true, nested `admission.dynamics_ready:true` |
| R13 safety flags | accept: all exact | `production_wired`, `physical_state_mutated`, `source_effective_segment_payloads_consumed`, `validation_only:false` |
| R14 unassigned cells | accept: none | unassigned id inside `complete`, `all_supplied_cells_assigned:false` |
| R15 recombination | accept: absent | `composite_of` present |
| R16 lineage | accept: absent | `frame_lineage` present |

Preservation duty verified: blocked reports echo `blocking_cell_ids` /
`blocking_assignment_statuses` / `reason_codes`; refused reports echo
`reason_codes` + `detail` into the verdict. CLI exit codes: ACCEPT→0, REJECT→1,
unreadable→2.

## 4. The five DECISION REQUESTS (strictest reading implemented, logged for Astra)

Each is listed in every verdict under `decision_requests` with `exercised` set when
a report's shape engages it; tests pin the exercised flags (11 cases).

- **D1 readiness promotion** — strictest: any true readiness claim anywhere =
  REJECT; no promotion path exists in the validator. Enforced by R12. Await Astra.
- **D2 `partial` policy** — strictest: `partial` and any unassigned cell = REJECT
  always; no explicit-subset-consumption path. Enforced by R2/R14. Await Astra.
- **D3 composite recombination** — strictest: any recombination field = REJECT; the
  validator computes no composite/parallel-axis math. Enforced by R15. Await Astra.
- **D4 parent-frame lineage schema** — strictest: any lineage field or non-v1
  schema = REJECT; v1 flat frames only. Enforced by R16. Await Astra.
- **D5 source-effective mass transport** — strictest: `unsupported` status,
  non-`reconstructed_tissue_mass` authority, or any consumed source-payload flag =
  REJECT. Enforced by R2/R11/R13. Await Astra.

## 5. Adversarial self-probe results (`receipts/adversarial_probe.txt`)

| probe | vector | result |
|---|---|---|
| A1 | truncated tensor (2×3) with `full_symmetric_tensor:true` | REJECT — R0, R9 (exit 1) |
| A2 | transposed/mismatched off-diagonal pair (0.025 vs 0.0125) | REJECT — R0, R9 exact-symmetry (exit 1) |
| A3 | case-variant statuses `Complete`/`Exported` | REJECT — R0, R2, R5 exact matching (exit 1) |
| A4 | readiness claim nested at `body_groups[0].admission.dynamics_ready` | REJECT — R12 recursive scan; the reader alone misses it (exit 1) |
| A5 | silently diagonalized tensor, symmetry + flags kept | **ACCEPT — as PREDICTED in the frozen preregistration.** This is the pre-declared static LIMIT L2, not an unplanned bypass: a wrong-but-symmetric, correctly-flagged tensor is indistinguishable from a genuinely diagonal authored body without the reference documents. Mitigation implemented: `--admission-report` recomputation path (tamper-refuses on any supplied document that does not hash to the binding; test `test_recompute_path_rejects_wrong_document_for_original_report`). |

Falsifier verdict: no unplanned-bypass fixture exists in the probe set; the one
ACCEPT under adversarial pressure is the pre-named limit class, measured and
mitigated. The frozen membrane's prediction held on all points.

## 6. Integrity

```
$ git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- tools Chimera/docs/matter
(paste of receipts/integrity_git_status.txt — 0 bytes: EMPTY)
```

## Limits & interpretations (honest record)

1. Hash **recomputation** requires the supplied documents; without them only
   presence/well-formedness/root↔body consistency are checkable (CON-13 limit).
2. Static validation cannot see the A5 class (see §5).
3. Root↔body hash equality enforced only on `complete` reports: the exporter's
   `_blocked_group` legitimately binds a different document subset per body.
4. Interpretations recorded: `volume` presence required (§1 authority table lists
   it; the exporter always emits it); statuses/units/hashes case-sensitive exact;
   tensor symmetry exact (stricter than the reader's 1e-12 — authored doubles
   round-trip exactly); `integration_model`/`material_records` checked for
   presence/form, not pinned to literal values the contract does not fix.

## Files

- `E:/ChimeraWork/mvc-20260924/material_volume_campaign/agents/M10_validator/rigid_body_mass_consumption_validator.py`
- `.../M10_validator/tests/test_validator.py`
- `.../M10_validator/fixtures/` (53 frozen JSON + `make_fixtures.py`)
- `.../M10_validator/receipts/` (test_run, adversarial_probe, implementation,
  integrity, freeze hashes)
- `.../M10_validator/PREREGISTRATION.md`, `brief.md`, `report.md`
