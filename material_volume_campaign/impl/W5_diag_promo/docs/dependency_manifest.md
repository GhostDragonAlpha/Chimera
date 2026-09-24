# Dependency manifest — `material_volume_diagnostic` promotion copy (W5)

Machine-readable twin: `../receipts/dependency_oids.json` (generated from
`git ls-tree` at the pin; every OID verified with `git cat-file -e`).

**Pinned revision: `feb01661bedb81063d88937d4c284ee9b4fa3ebd`**
(branch `material-volume-campaign-20260924`, 2026-09-24).
At freeze: `git cat-file -e feb01661…` OK; `git diff feb01661 -- tools/` EMPTY,
so the working-tree bytes below ARE the pinned blobs.

Identity convention (MV-B4-1; see `material_volume_diagnostic.md` §Identity
layers): the **portable claim** is `blob OID at pinned rev` + SHA-256 over
LF-canonical bytes; the `working_tree_sha256` recorded below is the **raw disk
equality** claim for the CRLF-materialized checkout — a DISTINCT, weaker claim.

## Direct dependencies (imported by the CLI itself)

| path (from repo root) | role | what the CLI consumes | blob OID @ pin |
|---|---|---|---|
| `tools/material_volume_body_export_reader.py` | DIRECT — the located dependency | `summarize_export_report` (ALL validation, statuses, per-body summaries, readiness), `canonical_json` (machine output) | `1ee791e0580ca0e30bf0b73321cfd981cd79b486` |
| `tools/material_volume_body_export.py` | DIRECT + transitive | `read_json_file` (all file parsing; strict: duplicate keys / nonstandard constants rejected), `ExportInputError`, `EXPORT_SCHEMA` (tests) | `f6fd2af161705371cb9a59df941460ca2b8e2b84` |

## Transitive dependencies (module-load imports of the above)

| path | imported by | blob OID @ pin |
|---|---|---|
| `tools/material_volume_admission.py` | `material_volume_body_export` | `41615ec7d3f1488007fcd30e3d887702c6b51290` |
| `tools/material_volume.py` | `material_volume_admission` | `3d46b030e75d6200a1764aadf72d81be9942bcdc` |

Import graph, verified by grep at freeze (`^import material_volume`):
`reader -> body_export -> admission -> material_volume`; nothing else local.
The CLI locates exactly ONE directory (`--tools-dir` / env `M09_TOOLS_DIR` /
nearest-ancestor `tools/`) and imports both direct modules from it — so all
four local modules must coexist in that one directory.

## External dependencies

| name | version at freeze | role |
|---|---|---|
| CPython | 3.14.3 | runtime |
| numpy | 2.2.6 | transitive (imported by all four local modules) |

## Test fixtures (consumed by the suite, not by the tool)

| path | role | blob OID @ pin |
|---|---|---|
| `tools/material_volume_body_export_example_report.json` | T1/T7 happy-path input, read as-is | `2091bee63193f029b4adf7a9e4bc88a2ce1f277b` |
| `tools/material_volume_body_export_manifest_example.json` | fixture-generator input (in-memory mutations) | `c6acf49f221ec87a8b5d055ed30316fdc2e630c1` |
| `tools/material_volume_body_export_partition_example.json` | fixture-generator input | `3b6e4f5265b486fb4f4d357e9e7dc905d9959c5b` |
| `tools/material_volume_body_export_groups_example.json` | fixture-generator input | `cb8514ee1c9816c03f5d10b6fd325bf986762eb0` |

All other fixtures are GENUINE exporter outputs generated in memory at test
time and written only under the suite's own `work/` dir.

## The W3 situation and the re-pin rule

W3's M13 reader repair was IN FLIGHT (uncommitted ` M
tools/material_volume_body_export_reader.py` at HEAD `df5ac8c6`) when W5 was
dispatched; the brief ordered W5 to pin by role + blob OID at a recorded
revision, note the re-pin, and not block on W3. Measured timeline: W3 landed
(`af735b7f` — "reader M13 repair (14/14 crash shapes -> named located refusals;
valid output + existing refusals byte-identical; no blanket catch;
failing-first trail preserved)") BEFORE this pin was taken, so **the pinned
reader blob `1ee791e0…` already contains W3's repair**, and the 17/17 suite
results at both locations (original + home) were measured against it.

**RE-PIN RULE (binding at integration):** if HEAD has moved after
`feb01661…`, the publisher re-runs `git ls-tree <landed-rev> -- tools/`,
updates this manifest + `receipts/dependency_oids.json`, and re-runs the home
suite (acceptance: 17/17 + battery 0 mismatches) before publishing. The home
copy's own bytes do NOT change — only the manifest's OIDs can.

## Source blobs (what the promotion copy is made of)

| artifact | blob OID @ pin |
|---|---|
| `material_volume_campaign/agents/M09_diagnostic/material_volume_diagnostic.py` (source; home copy = this + comment header only) | `f9763b4318e6954b9141b8bc954c10a856c39cf2` |
| `material_volume_campaign/agents/M09_diagnostic/tests/test_material_volume_diagnostic.py` (home copy verbatim) | `c9ba51a63e0fa5714771c884066e48168568b44b` |
| `material_volume_campaign/agents/M09_diagnostic/run_suite.py` (home copy = this + 2 path-constant adaptations) | `848b4ee1cac98f8e08ba653803cc8356755610e9` |
