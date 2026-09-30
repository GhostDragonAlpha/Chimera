---
name: intake-gait-lane-2026-09-17
description: INTAKE-GAIT lane shipped (4c9a9658, branch
  lane/intake-gait-20260917) — Janisch strides + Dryad gait metadata admitted,
  connectors_*.py auto-load convention born, Copernicus CRLF pin-drift repaired,
  Dryad bearer-token deferral path recorded
metadata:
  node_type: memory
  type: project
  originSessionId: sess_3be03512-a444-447d-8dcc-1a7e69958f3c
---

Lane INTAKE-GAIT (GLM 5.3, 2026-09-17, worktree E:\ChimeraWork\intake-gait-20260917, branch lane/intake-gait-20260917 off 5a180eb4, published 4c9a9658 — branch only, never master): Janisch 2024 wild primate kinematics admitted as 386 per-stride observation records (class batch.observation.janisch_stride, 14 checks; the file's one all-NA row quarantines by design — 387 fetched == 386 + 1); Dryad Granatosky z08kprrd5 + Higurashi fj6q573tc admitted as 14 deferred file-identity records (batch.deferred.dryad_file) with digests pinned from the authless API v2 version-file lists. Receipt at tools/science_funnel/validation/batch_gait_20260917/receipt.json — 4,221 verified / 0 failures / graphify HONEST 7 checks / same-command re-run adds 0 objects. Lane dossier: docs/research/20260917_gait_intake.md.

**Why:** the operator's batch-prove-library directive; the Dryad bytes cannot be script-downloaded without a free bearer token (API 401 + Anubis bot wall, first-hand bodies committed in each data dir), so the lane pins identity for a future token-enabled download instead of pretending.

**How to apply:** (1) NEW INTAKE LANES use the connectors_*.py auto-load convention (batch/connectors.py tail merges lane CONNECTORS; duplicate ids refuse) + adapters in a lane module (adapters_gait.py pattern registers into the shared ADAPTERS dict in place — shared adapters.py never edited) + reprove blob-index dirs now DERIVE from merged connectors, so new data dirs are re-provable with no reprove.py edit. (2) BYTE-STABILITY LAW for pinned data: `tools/science_funnel/data/** -text` now in .gitattributes (fresh clones must not CRLF-convert pinned bytes); the prior batch had committed the Copernicus EOXML CRLF-stripped (43,891 vs pinned 44,729 — would pin_drift any fresh clone) — repaired by re-download from the receipt-pinned S3 URL, re-proven 8 records byte-identical. ALWAYS blob-verify staged data files against receipt pins before commit. (3) New generic contract check kinds available: field_in, numeric_tree_range. (4) The dossier's "mammal_gait.txt = stream 863884" mapping was WRONG (that id is mcmc_out.txt) — file ids must come from the API version-files list, not prose. Related: [[batch-intake-lane-2026-09-17]], [[alan-operator-preferences]].
