# SHIPPED-SURFACE PROVENANCE REGISTRY — S01 / card ONT-S01 (attempt a3ed434776cf4eff8b09170cdf990f3a)

Status: **RECORDED — closed-world provenance registry, every row evidence-backed,
machine-enforced.** Machine-readable authority: `provenance_registry.json` (this
directory); verifier `verify_provenance.py` (12 git pins, 3 deep re-hashes, 5 on-disk
evidence checks, bidirectional surface coverage); falsifier suite
`test_verify_provenance.py` (31 tests). Human report: `../../../../../report.md`
(attempt workspace root).

Reconcile-first: this registry MECHANIZES the already-verified M-S01 provenance audit
(`762eb589`, 18-row matrix + receipts), reuses the qualified ONT-P02 lineage map
(`8c7ed8c2`) and the ship-asset decision request (`066485ae`), and re-hashes the
load-bearing evidence itself (agreement PDF, rights CSV, render body) from the git
object store. It derives no new claims and invents no terms.

## The frozen done_when, mechanized

"Every shipped asset/model/library has a recorded source and applicable distribution
terms" holds exactly when, on the enumerated shipped surface (20 explicit paths from
the pinned hash receipt + declared extras, plus the pinned 25-preview set):

- every path is covered by exactly one registry row, and every covered path is on the
  surface (closed world, both directions);
- every row records a source and terms backed by registered evidence (pin, deep
  re-hash, on-disk hash, or banked dated snapshot); CLEAR without evidence is a
  refusal;
- the observation is enforced as code: **existing license receipts are inputs, not
  blanket clearance for future assets** — an unregistered shipped artifact is a
  named refusal, and the closure rule's future-asset duty is load-bearing.

## THE MATRIX (verdicts; full identities in provenance_registry.json)

| # | Artifact | Source | Terms (recorded evidence) | Verdict |
|---|----------|--------|---------------------------|---------|
| R1 | Runtime code (slice_server, scene_boot, push_channel, push_client.html) | This repo | AGPL-3.0 (LICENSE pin @ base) | CLEAR |
| R2 | Page + registry assets (index.html self-contained, mock_registry, boot_cache_manifest) | This repo | AGPL-3.0 | CLEAR |
| R3 | standing_body.obj (18,469,042 bytes; re-hashed from object store) | MorphoSource 000875604 CT -> segmented -> repaired+decimated | Commercial Use **Prohibited**; copyright UND (Smithsonian NMNH); 1-year derivative re-archival duty (agreement PDF + rights CSV re-hashed) | **RESTRICTED_RECORDED** — operator gate (options A/B/C) |
| R4 | standing_body.glb (byte-identical boot cache of R3) | Derived from R3 | Same MorphoSource terms | **RESTRICTED_RECORDED** |
| R5 | ghost_standing.obj (composed from CT previews) | Composed from R6 | Same MorphoSource terms | **RESTRICTED_RECORDED** |
| R6 | 25 CT preview meshes (set-pinned via manifest; count machine-checked) | MorphoSource 000875604 | Same MorphoSource terms | **RESTRICTED_RECORDED** |
| R7 | chimera_engine.exe | In-repo source (no vendored third-party code per include scan) | AGPL-3.0 source; runtime rows R8/R9 | PENDING_BUILD_IDENTITY (absent at audit; sha256 action at S02 build — recorded, not a gap) |
| R8 | Vulkan SDK / vulkan-1 loader (SDK 1.4.328.1) | LunarG | SDK disclosure file (hashed): 100% open-source components, majority MIT / Apache 2.0; component registry not statically retrievable 2026-09-26 — banked honest snapshot; residual package-time action recorded | RECORDED (was M-S01 UNKNOWN) |
| R9 | MSVC/UCRT runtime (vcruntime140, ucrtbase, ...) | VS 2022 Build Tools (MSVC 19.44) | Microsoft Distributable Code: VS2022 REDIST list — unmodified distribution with your program, subject to MSLT; licensed-VS-users limit; banked snapshot with pinned doc commits; vc_redist version pin at package time | RECORDED (was M-S01 UNKNOWN) |
| R10 | CPython 3.14.3 | C:/Python314 | PSF License (LICENSE.txt hashed + marker) | CLEAR |
| R11 | numpy 2.2.6 | PyPI wheel | BSD-3 (classifier machine-checked live) | CLEAR |
| R12 | scipy 1.17.0 | PyPI wheel | BSD-3 (classifier machine-checked live) | CLEAR |
| R13 | Clearing data (declaration, bundle + recipe/bundle/query builders) | Campaign-authored (F01/F02) | AGPL-3.0 | CLEAR |
| R14 | trunk_declaration.json (Oku-derived 1.158 m cited inside) | Campaign-authored (F03) | AGPL-3.0 | CLEAR |
| R15 | product/ modules (input_mapper, follow_camera, focus_policy, session_flow) | Campaign-authored (U01-U03/X02) | AGPL-3.0 | CLEAR |
| R16 | Oku-2021 walker numbers (10.038 kg) — derived facts in code/data, no file shipped | Oku, Ide & Ogihara 2021, Commun Biol 4:1831 | CC BY 4.0 attribution recorded; facts + citation | CLEAR |
| R17 | myo_sim v0.1.0 (vendored) — NOT in the shipping chain | MyoSuite/MyoHub | Apache-2.0 (LICENSE re-hashed 2026-09-26, equals the 2026-09-24 receipt sha) | CLEAR_NOT_SHIPPED (structural exclusion recorded) |
| R18 | FreeMusco chimanoid XML (fictional human-based MSK) | FreeMusco (arXiv:2511.14205) | No acquisition needed: 0 hits in the shipped tree (pinned receipt marker); "Nothing here executes anything" (USTR receipt pin) | CONFIRMED_EXCLUDED |

## Falsifier results (preregistered set)

- F1 dead pin: **did not fire** (12/12 pins resolve; one transcription error — a
  "boot_cache_manifest.json" marker that the receipt words as "boot_cache_manifest
  pin" — was caught by the verifier's own marker check and corrected in the registry
  before any pass was claimed).
- F2 identity mismatch: **did not fire** (agreement PDF `d68ede8f…`, rights CSV
  `ff7cdc46…`, render body `bc9033bf…9111` / 18,469,042 bytes re-hashed from the
  object store; myo_sim LICENSE re-hash equals the 2026-09-24 receipt).
- F3 coverage hole: **did not fire** (20 explicit paths covered exactly, both
  directions; the closed-world rule converts any future unregistered asset into a
  refusal).
- F4 unsupported terms: **did not fire** (every non-exclusion row cites registered
  evidence; CLEAR-without-evidence is refused).
- F5 blanket clearance: **did not fire** (the observation sentence is bound verbatim;
  removing the future-asset duty or a restricted row's operator gate is refused).
- F6 verifier blind spot: **did not fire** (31 mutation controls + live idempotence
  all behave as registered).

## What this card does NOT claim

- No clearance of the CT chain: R3-R6 are recorded-as-RESTRICTED; the operator
  decision (SHIP_ASSET_DECISION_REQUEST @ 066485ae: provider approval /
  non-commercial compliance / asset replacement) remains the S02 distribution gate.
- No package manifest: R7-R9 identity actions (exe sha256, vulkan-1.dll version,
  vc_redist version) are recorded package-time actions, not performed here.
- No claim that the M-S01 falsifier-fired receipt paraphrase is fixed: the one-line
  correction to `download_receipt.json` lives on a lane outside this card's sparse
  path and is routed as a named remaining gate.
