# W6 dependency pinning manifest — promoted validator

Tool: `rigid_body_mass_consumption_validator.py` (W6 promotion candidate,
`impl/W6_validator/`). Identity claims below follow the contract §6 identity
table: **Git blob identity** pins a revision and is portable across checkouts;
raw-file SHA-256 is checkout-materialization dependent (finding M-1) and is
recorded only as a secondary observation.

## Pinned revision

- Worktree `E:/ChimeraWork/mvc-20260924`, branch `material-volume-campaign-20260924`.
- Initial pin: campaign tip **`d1c99335`** (16:0x). During this session the
  sibling lanes W3 (reader M13 repair) and W1 (source-bound regeneration
  verifier) were integrated, moving the tip to **`feb01661`** (16:51). Only ONE
  pinned dependency changed: `tools/material_volume_body_export_reader.py`
  (W3's M13 repair: 14/14 crash shapes → named located refusals; valid outputs
  byte-identical — its summary layout is unchanged, so the R0 cross-check and
  the MV-B3-1 summary detection are unaffected; the full W6 suite re-ran green
  against the repaired reader at 16:59, `receipts/test_run_full.txt`).
- **Authoritative pin: `feb01661`** (current tip). d1c99335 OIDs retained below
  for provenance.

## Import closure (exact, verified by sandboxed import test)

The validator imports, via `sys.path` insertion of `tools/` with
`sys.dont_write_bytecode = True` set before any import:

| # | module | imported by | Git blob OID @ feb01661 (authoritative) | @ d1c99335 (initial) | role |
|---|---|---|---|---|---|
| 1 | `tools/material_volume_body_export_reader.py` | the validator (R0 cross-check; `summarize_export_report`, `canonical_json`) | `bd7e08d98399ad75fc2534b12632e0524bde1e01` | `8a30267f557512f6faf705e470f593313643dea5` | read-only reader (W3/M13-repaired) |
| 2 | `tools/material_volume_body_export.py` | reader (line 23, `import material_volume_body_export as exporter`); validator uses `read_json_file`, `ExportInputError` | `f6fd2af161705371cb9a59df941460ca2b8e2b84` | same | exporter (strict loader, `_canonical_hash`) |
| 3 | `tools/material_volume_admission.py` | exporter (line 27, `import material_volume_admission as admission`) | `41615ec7d3f1488007fcd30e3d887702c6b51290` | same | admission model |
| 4 | `tools/material_volume.py` | admission (line 25, `import material_volume as mv`) | `3d46b030e75d6200a1764aadf72d81be9942bcdc` | same | tetrahedral compiler module |

Empirical closure proof (this session, sandboxed copy of exactly these four
modules): importing the reader without `material_volume.py` fails with
`ModuleNotFoundError: No module named 'material_volume'` (M07 harness-incident
precedent); with all four, the reader parses and summarizes the shipped example
report. The repaired reader's import block is unchanged (stdlib + numpy +
`material_volume_body_export`), so the four-module closure still holds.
**The minimal dependency set is exactly these four files plus the Python
standard library and numpy.**

Also pinned (read-only references, not imported by the tool):

| artifact | identity |
|---|---|
| **DECIDED v1.0 contract** — `Chimera/docs/matter/rigid_body_mass_export_consumption_contract_v1_proposal.md` in the MAIN checkout `E:/PythonChimera` (reconciler of record; worktree copy is the older v0.9) | Git blob `ee254224d6bc0cdabd08e6597aa218887b4447f0` @ main-checkout HEAD `b04a3acd`; raw-file SHA-256 `c69778683f6f8bea6c40c7374f90bf2c004b75b594780f2c989100f4901ca13d`; canonical-content SHA-256 `fa845491194f0fba3693f73a5f8793cc876ac3dd5c77c615bc1c513a133a28c6` |
| Worktree's v0.9 contract copy (NOT the reconciled text; recorded only to prevent accidental reconciliation against it) | Git blob `376adfa5f46e8d5f6befc37de5e14d4757993c41` @ feb01661 |

## Non-repo runtime dependencies

| dependency | version at pinning | notes |
|---|---|---|
| Python | 3.14.3 | standard library only beyond numpy |
| numpy | 2.2.6 | linear algebra for CON-10 frame checks and CON-16 aggregation; CPU-only |

## Promotion-time re-verification steps

1. `git ls-tree <rev> -- tools/material_volume_body_export_reader.py tools/material_volume_body_export.py tools/material_volume_admission.py tools/material_volume.py` — the four authoritative OIDs above must match (or a superseding revision must be re-adjudicated and this manifest appended, never edited).
2. Re-verify the DECIDED v1.0 contract blob in the main checkout (`ee254224…` or a superseding decided revision).
3. `python rigid_body_mass_consumption_validator.py --version` — identity line must name W6-promotion 1.0.0 and the M06-H04 exit classes.
4. Run the frozen suite: `PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/ -q` — expected green count recorded in `receipts/test_run_full.txt` (101).


> RE-PIN (publisher, 2026-09-24): the reader dependency advanced to the W3b revision (mv commit 28e8233f; blob bd7e08d98399ad75fc2534b12632e0524bde1e01) per the RE-PIN RULE after W7 caught the concurrent move. Suites re-run green post-sync.
