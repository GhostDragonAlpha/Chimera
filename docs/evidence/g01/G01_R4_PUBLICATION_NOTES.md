# G01-R4 publication notes (publisher: Big Pickle)

Published 2026-09-07 from the G01 worker's isolated checkout
`E:\Chimera_G01` into this repository. This note records the
source-to-destination mapping, the verification performed from the
published layout, and any publication-time changes. It is appended by the
publisher only; the G01 worker made no commits, branches, or pushes.

Source of truth for content and layout intent:
`agent_logs/glm_foundation_g01/PUBLISHER_MANIFEST_R4.md` (included below)
and the R3-era snapshot `docs/evidence/g01/r3_snapshot/`.

## Source-to-destination mapping (explicit)

| Source (E:\Chimera_G01) | Destination (this repo) | Preserved bytes |
|---|---|---|
| `tools/evidence_output.py` | `tools/evidence_output.py` | yes (SHA-256 bit-identical to source) |
| `tools/material_contract.py` | `tools/material_contract.py` | yes |
| `tools/material_contract_checks.py` | `tools/material_contract_checks.py` | yes |
| `tools/overdamped_descent.py` | `tools/overdamped_descent.py` | yes |
| `tools/overdamped_descent_checks.py` | `tools/overdamped_descent_checks.py` | yes |
| `tools/surface_energy_checks.py` | `tools/surface_energy_checks.py` | yes |
| `tools/surface_energy_reference.py` | `tools/surface_energy_reference.py` | yes |
| `docs/FOUNDATION_G01_REPORT.md` | `docs/FOUNDATION_G01_REPORT.md` | yes |
| `docs/FOUNDATION_G01_GPU_HANDOFF.md` | `docs/FOUNDATION_G01_GPU_HANDOFF.md` | yes |
| `agent_logs/glm_foundation_g01/PUBLISHER_MANIFEST_R4.md` | `docs/evidence/g01/PUBLISHER_MANIFEST_R4.md` | yes |
| `agent_logs/glm_foundation_g01/PUBLISHER_MANIFEST_R3.md` | `docs/evidence/g01/PUBLISHER_MANIFEST_R3.md` | yes |
| `agent_logs/glm_foundation_g01/RUN_HISTORY_R4.md` | `docs/evidence/g01/RUN_HISTORY_R4.md` | yes |
| `agent_logs/glm_foundation_g01/RUN_HISTORY_R3.md` | `docs/evidence/g01/RUN_HISTORY_R3.md` | yes |
| `agent_logs/glm_foundation_g01/RUN_HISTORY_R2.md` | `docs/evidence/g01/RUN_HISTORY_R2.md` | yes |
| `agent_logs/glm_foundation_g01/RUN_HISTORY.md` | `docs/evidence/g01/RUN_HISTORY.md` | yes |
| `agent_logs/glm_foundation_g01/*_results_*.json` (all R4-era stamped runs; see manifest) | `docs/evidence/g01/` (same names) | yes |
| `agent_logs/glm_foundation_g01/surface_energy_checks_results.json` | `docs/evidence/g01/surface_energy_checks_results.json` | yes (historical file; byte-identical after all R4 runs) |
| `agent_logs/glm_foundation_g01/surface_energy_checks_R2_run.txt` | `docs/evidence/g01/surface_energy_checks_R2_run.txt` | yes |
| `agent_logs/glm_foundation_g01/material_contract_checks_R2_run.txt` | `docs/evidence/g01/material_contract_checks_R2_run.txt` | yes |
| `docs/evidence/g01/MANIFEST.md` | `docs/evidence/g01/MANIFEST.md` | yes (original G01 packet manifest) |
| `docs/evidence/g01/MANIFEST_R2.md` | `docs/evidence/g01/MANIFEST_R2.md` | yes (G01-R2 the correction-pass manifest) |
| `docs/evidence/g01/r3_snapshot/**` (11 files + SHA256SUMS.txt; all referenced blobs included, not only the hash list) | `docs/evidence/g01/r3_snapshot/` | yes (every file verified against the snapshot's own SHA256SUMS.txt: 11/11 match) |

Every destination was hash-verified against its source after copying
(SHA-256 exact, 0 mismatches). No bytes were transformed, recompressed, or
line-end-filtered anywhere in this publication.

## Publication-time changes (none to content; layout only)

- The G01 worker's R4 manifest said "copy each file to the SAME
  repo-relative path under `docs/evidence/g01/`". The publisher does NOT
  do that with the operational files: to preserve the functional
  repository layout (the R4 assignment's layout goal), the seven Python
  source/check files live at `tools/`, the two foundation docs at
  `docs/`, and only run histories, raw results, and publisher manifests
  live under `docs/evidence/g01/`. This is a layout-only adjustment;
  every blob is byte-identical to source.
- The R3 snapshot is placed at `docs/evidence/g01/r3_snapshot/` with the
  ACTUAL files its SHA256SUMS.txt references (all 11 present and
  hash-verified) — not a pointer to E:\Chimera_G01.
- This notes file is the publisher's own addition.

## Verification from the published layout (dependencies at target commit)

Run from `tools/` in this repo (published layout), Python 3.14.3, numpy
2.2.6 (matches the R4 records; float64 eps 2.220446049250313e-16):

| Command | Result (re-run) | R4-recorded result |
|---|---|---|
| `python overdamped_descent_checks.py` | 13/13 PASS, exit 0 | 13/13 PASS |
| `python surface_energy_checks.py` | 8/8 PASS, exit 0 | 8/8 PASS |
| `python material_contract_checks.py` | 16/16 PASS, exit 0 | 16/16 PASS |

The re-run transcripts were written by the tools themselves as stamped
JSON into `agent_logs/glm_foundation_g01/` (gitignored at source; matching
the tools' own evidence-law behavior). No unpublished file from
`E:\Chimera_G01` is required to run these checks from the published
layout.

## Evidence preservation claims — supported

- "11 files + SHA256SUMS.txt at r3_snapshot" — supported: the directory
  contains the actual files; internal hashes verified 11/11.
- "Historical surface_energy_checks_results.json unchanged after all R4
  runs" — supported: the published blob equals the ORIGINAL G01 manifest's
  hash `cfe48cb1...`.
- R2 manifests remain alongside R4 (MANIFEST_R2.md, PUBLISHER_MANIFEST_R3 /
  RUN_HISTORY_R3), so the R3 latency correction history is preserved, not
  erased by the R4 supercedure.

No engine integration, no live testing, no protected-directory writes were
performed during this publication.