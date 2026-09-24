# USAGE — `rigid_body_mass_consumption_validator.py` (W6 promotion candidate)

Static consumption validator for `chimera.rigid_body_mass_export.v1` export
reports, reconciled to the contract **v1.0 with D1–D5 decided (2026-09-24)**
(main checkout: `Chimera/docs/matter/rigid_body_mass_export_consumption_contract_v1_proposal.md`).
Lineage: the M10 campaign validator (`agents/M10_validator/`, 71-test frozen
suite), preserved untouched as the campaign artifact; this promoted copy carries
the decided readings.

## CLI

```
python rigid_body_mass_consumption_validator.py REPORT.json \
    [--admission-report ADMISSION.json] [--verify-aggregate] [--indent N]
python rigid_body_mass_consumption_validator.py --version
```

- `REPORT.json` — the FULL raw export report (contract §1 document). A reader
  summary (`summarize_export_report` output) is a display projection and is
  refused by name: `summary_projection_is_not_a_consumption_document` (MV-B3-1,
  decided).
- `--admission-report` — optional admission document; enables the CON-13
  recomputation path (any supplied document that does not hash to the recorded
  binding is a tamper refusal).
- `--verify-aggregate` — after an ACCEPT verdict, additionally emit the
  CON-16 read-only verification aggregate (below).

## Exit classes (M06-H04, decided)

| exit | meaning |
|---|---|
| **0** | accepted static validation (verdict `ACCEPT`; assembly-eligible under the contract) |
| **2** | named input/status refusal — a `REJECT` verdict (every rule failure enumerated and named), an unreadable/invalid input document (`could_not_evaluate: …` on stderr), or a CLI usage error |
| **1** | unexpected internal failure only (`unexpected_internal_failure: …` on stderr) |

Compatibility note: the original M10 tool keeps `0/1/2 = accept/reject/
could-not-evaluate`. Only this promoted tool carries the decided mapping.
`--version` states the tool identity: name, `W6-promotion 1.0.0`, contract v1.0
(D1–D5 decided 2026-09-24), and the exit-class contract.

## What ACCEPT means (and never means)

ACCEPT asserts static assembly-eligibility only: root `complete`, every body
`exported` with authoritative mass properties (R1–R16), hashes well-formed and
consistent (CON-13), no readiness claim anywhere (CON-14/D1), no recombination
or lineage fields (CON-15, D3/D4), no source-effective consumption (CON-5/D5).
ACCEPT never implies dynamics readiness (D1: runtime binding requires the
separate Astra-approved qualification gate), anatomical correctness, or
mechanical qualification.

## What gets REJECTED (the decided readings)

- `partial` root status or any unassigned cell — partial-assembly rejection,
  including any subset binding (D2 decided; no subset-binding exception). The
  verdict's `preserved_diagnostics` explicitly displays the omitted bodies and
  the unassigned cells (CON-3), plus blocking diagnostics for `blocked`/`refused`
  (CON-4/CON-6).
- `blocked` / `unsupported` / `refused` / unknown statuses; `not_exported`
  bodies (diagnostics, never inputs); placeholder masses; malformed authority
  fields; non-proper-orthonormal frames (refused, never repaired); stripped
  provenance; inferred ownership; readiness claims at any depth; fixed-v1
  safety-flag deviations.

## Hash scopes and full-report identity (MV-O1, decided)

Every verdict carries `admission_hash_scopes`:

- **`admission_report_document`** — the root binding and the binding of every
  `exported`/`unsupported` body: canonical-JSON SHA-256 of the full admission
  report document.
- **`reduced_block_record`** — a `not_exported` (blocked) body's binding:
  canonical-JSON SHA-256 of the REDUCED two-field object
  `{"decision": <body admission_status>, "reason_codes": <body admission_reason_codes>}`
  (exporter `tools/material_volume_body_export.py::_blocked_group`). It is NOT
  the admission report document and **never a full-report hash**.
- **`full_report_identity`** — identity of the delivered report document itself,
  verified separately at the handoff: `raw_file_sha256` (exact bytes) and
  `canonical_content_sha256` (CRLF/CR → LF, §6 declared-text rule). Distinct §6
  claim kinds, never conflated with any `admission_report_sha256`.

## CON-16 verification aggregation (D3 decided) — `--verify-aggregate`

Permitted read-only verification math, as a SEPARATE entry point; the validation
verdict itself never contains aggregate values. Allowed exactly as CON-16
states: composite mass, COM, and full inertia across `exported` bodies of an
ACCEPT-verdicted report, computed in the report's domain frame with (a) frames
stated explicitly (target frame kind, convention, per-body frame_id/rotation/
origin verbatim), (b) disjoint cell ownership taken verbatim from
`cell_provenance` (overlap refusals name the cell and both owners), (c) the
result returned as a `con16_verification_aggregate` artifact with its own error
accounting (orthonormality residuals, parallel-axis displacement norms), and
(d) no body record collapsed, rewritten, or merged — the input is never
mutated. It does NOT authorize collapsed export bodies, inferred joints, or
runtime regrouping (R15 unchanged; refused reports yield
`con16_aggregate_refusal`).

## Static-only / no-runtime claim

This tool performs static JSON validation and read-only arithmetic only: no
runtime wiring, no assembly, no physics import, no dynamics, no state mutation,
no readiness promotion, no network, CPU-only. It imports only the four pinned
`tools/` modules (see `DEPENDENCY_MANIFEST.md`) plus numpy and the standard
library, with bytecode writing disabled. It never writes files.

## Tests

`PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/ -q` — 101 tests (the adapted
M10 frozen suite + the reconciliation deltas), all green at freeze time
(`../receipts/test_run_full.txt`). Fixtures include genuine exporter outputs
(`tests/fixtures/genuine_blocked_report.json`,
`tests/fixtures/genuine_partial_report.json`) whose producer hashes match the
M07 ownership receipt exactly.
