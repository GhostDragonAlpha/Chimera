# M-S01 — Distribution provenance and dependencies audit

Item S01 (verbatim): **"Every shipped asset/model/library has a recorded source and applicable distribution terms."**
Constraint: **"Existing license receipts are inputs, not blanket clearance for future assets."**

Audited 2026-09-24 · worktree `E:/ChimeraWork/monkey-play-20260924` · branch `monkey-play-20260924` · HEAD `42f7cdc4ba421cf83ecd2fa0be69e94fb772cd37` · read-only everywhere outside this dir.

**Preregistered falsifier (from the brief, tested below):** any shipped-surface artifact with NO recorded source, or terms asserted without evidence.

---

## 1. The shipped surface (the playable build's actual consumption chain, from slice_server.py outward)

`tools/playable_slice/slice_server.py` (front door, stdlib HTTP) serves and drives:

- **Runtime code:** `slice_server.py`, `scene_boot.py`, `push_channel.py` (in-repo), plus the `/push` page `tools/thin_client_pilot/push_client.html`.
- **Page + registry:** `index.html` (self-contained — zero external/CDN refs, verified by grep), `mock_registry.json`, `boot_cache_manifest.json`.
- **CT-derived assets (the player-visible animal):** `standing_body.obj` (the tick body, imported through the engine's real `/mesh_import`), its derived boot cache `standing_body.glb` (served verbatim at `/standing_body.glb`), `ghost_standing.obj` (the declared overlay, composed from the committed CT previews via the standing pose). All three descend from MorphoSource media **000875604** (Macaca mulatta USNM 497136-3) through `meshes_preview/` → `meshes_body_20260922/body_manifest.json`.
- **The engine binary** `chimera_engine.exe` (DEFAULT_EXE `.tmp/slice_build/Release/`): launched per boot (`--no-restore --hidden`), owns gravity/contact/rendering. **Absent in this worktree** (`.tmp/` gitignored — it must be built; identity pending). Built from in-repo `ChimeraEngine/engine` C++ (CMake; Vulkan + Win32 only — the include scan found no vendored third-party code; GLB/OBJ parsing is engine-authored).
- **Python runtime** for the server: CPython 3.14.3 + numpy 2.2.6 + scipy 1.17.0 (via `scene_boot` → `standing_pose_core`), rest stdlib.
- **Campaign scene data** (this branch's integrated additions): `data/monkey_clearing/` (declaration + recipe + terrain bundle/query), `data/monkey_trunk/trunk_declaration.json`, `product/` modules (input_mapper, follow_camera, focus_policy, session_flow + tests). All campaign-authored.
- **Oku-2021-derived numbers:** the walker's segment masses/lengths are derived facts from the published paper, banked with a receipt; consumed at package time as code/data constants, not as a shipped file.
- **NOT in the chain (verified):** `myo_sim` (vendored at `E:/PythonChimera/vendor/myo_sim`, serves the grab/foot science lanes); the FreeMusco chimanoid XML (absent from this worktree entirely — 0 hits; lives only in the main repo's analysis-only forearm packet).

W7 coordination honored: `tools/material_volume*.py` and `tools/tests/` were **listed only** (landing in flight), never opened for edit; nothing outside this dir was written.

---

## 2. THE FROZEN MATRIX (row set fixed from the enumeration above, before verdicts)

Schema (preregistered in the brief): `artifact | identity (hash/revision) | source (cited) | license/terms (recorded evidence, or UNKNOWN + action)`.
Frozen rows: R1 runtime code (4 files), R2 page assets (3 files), R3 standing_body.obj, R4 standing_body.glb, R5 ghost_standing.obj, R6 CT preview meshes (25), R7 engine binary, R8 Vulkan SDK/loader, R9 MSVC/UCRT runtime, R10 CPython, R11 numpy, R12 scipy, R13 clearing data, R14 trunk data, R15 product modules, R16 Oku-2021 derived numbers, R17 myo_sim (vendor, non-shipping), R18 FreeMusco chimanoid (exclusion check).

---

## 3. THE FILLED MATRIX

| # | Artifact | Identity | Source | Terms (recorded evidence) | Row verdict |
|---|----------|----------|--------|---------------------------|-------------|
| R1 | `slice_server.py`, `scene_boot.py`, `push_channel.py`, `thin_client_pilot/push_client.html` | sha256 per file (receipts/ship_surface_hashes.txt); tracked @ HEAD 42f7cdc4 | This repo (game lineage; slice lanes mesh-parse/push-channel/thin-client-20260920 per in-file headers) | Repo terms: **AGPL-3.0** (`/LICENSE`, read: "GNU AFFERO GENERAL PUBLIC LICENSE Version 3") | CLEAR (repo's own terms; AGPL obligations ride any distribution) |
| R2 | `index.html`, `mock_registry.json`, `boot_cache_manifest.json` | sha256 (receipts/ship_surface_hashes.txt) | This repo (lane/render-truth-20260920, mesh-parse-20260920) | AGPL-3.0 (repo). `index.html` self-contained — no third-party JS | CLEAR |
| R3 | `standing_body.obj` (tick body) | sha256 `bc9033bf…111` — **matches the P02P03 report pin** (`agents/P02P03/report.md` L24) and `body_manifest.json` | MorphoSource **000875604** CT → segmented (mesh_receipt.json, 25 bones, sha-pinned) → repaired+decimated (body_manifest.json: 712,224 repaired faces, ratio r=0.7020263287954351, ≤500,000-tri cap) | **MorphoSource Standard Usage Agreement, banked PDF** `000875604_ms_usage_std_comm_no_rearc_ms_3d_yes.pdf` (sha `d68ede8f…`, read in full): title "**Commercial Use Prohibited** – Derivatives Re-archived On MorphoSource – 3D Printing Permitted"; CSV rights fields: `permits_commercial_use=CommercialUseNotPermitted`, `copyright_statement=UND (undetermined)`, `ip_holder=Smithsonian NMNH`, `required_archival_of_published_derivatives=OnMorphoSource`; clauses (a)(b) attribution+citation (USNM:MAMM:USNM 497136 + ark:/87602/m4/875604), (d) no re-deposit elsewhere w/o written permission, (e) no commercial use w/o explicit approval, (f) distributed-product derivatives re-archived on MorphoSource within 1 year | **BLOCKED FOR SHIP** — terms recorded, and they restrict; see §5 |
| R4 | `standing_body.glb` (boot cache) | sha256 `adb6aff2…ae5` == `boot_cache_manifest.json` pin; `derived_from` standing_body.obj, `byte_identical: true` | Derived from R3 (deterministic conversion, lane mesh-parse-20260920) | Same MorphoSource terms as R3 (a derivative of a derivative) | **BLOCKED FOR SHIP** (with R3) |
| R5 | `ghost_standing.obj` (declared overlay) | sha256 `d07d976c…71d` == boot_cache_manifest pin; compose_record: pose `standing_pose_20260921/pose.json`, mesh_dir `meshes_preview` | Composed from R6 (CT previews) | Same MorphoSource terms as R3 | **BLOCKED FOR SHIP** (with R3) |
| R6 | 25 CT preview meshes `meshes_preview/*.obj` (git-tracked) | pinned by `meshes/manifest.json` (source: "MorphoSource CT 000875604 (Macaca mulatta USNM 497136-3, infant, 160 µm)") | MorphoSource 000875604 (download_receipt.json: zip sha `e3faf37a…`, media manifest csv sha `ff7cdc46…`) | Same MorphoSource terms (receipts/morphosource_000875604_rights_evidence.txt) | **BLOCKED FOR SHIP** (with R3) |
| R7 | `chimera_engine.exe` | **ABSENT** — not built in this worktree (`.tmp/` gitignored, no Release dir) | In-repo source `ChimeraEngine/engine` (CMakeLists.txt: project chimera_engine; include scan: only Vulkan + Win32/WinSDK headers, no vendored third-party code) | Repo AGPL-3.0 for source; toolchain terms rows R8/R9. Identity sha256 pending the S02 build | CLEAR source; identity action at build |
| R8 | Vulkan SDK / vulkan-1 loader | SDK 1.4.328.1 installed at `C:/VulkanSDK` | `CMakeLists.txt` find_package(Vulkan); links `${VULKAN_SDK}/Lib/vulkan-1.lib` | `C:/VulkanSDK/1.4.328.1/Licenses/LICENSE.txt` (read): LunarG notice — components "MIT or Apache 2.0"; per-component disclosure lives at vulkan.lunarg.com and is **not yet banked** | UNKNOWN (component-level) — action in §5; loader DLL version to pin at package time |
| R9 | MSVC/UCRT runtime (vcruntime, ucrtbase) | MSVC 19.44 recorded (`ChimeraEngine/engine/README.md` L78) | VS 2022 Build Tools toolchain | Microsoft distributable-code terms — **not yet banked**, exact redist version unpinned | UNKNOWN — action in §5 |
| R10 | CPython 3.14.3 | `python -V` = 3.14.3 | `C:\Python314` | `C:\Python314\LICENSE.txt` exists (PSF license history; read head) | CLEAR (PSF terms ride the package) |
| R11 | numpy 2.2.6 | installed metadata | PyPI wheel | metadata License field (NumPy Developers BSD text) + classifier "License :: OSI Approved :: BSD License" | CLEAR (BSD-3; attribution ships with package) |
| R12 | scipy 1.17.0 | installed metadata | PyPI wheel | metadata License field (Enthought/SciPy BSD text) + classifier BSD | CLEAR (BSD-3; attribution ships with package) |
| R13 | clearing data (declaration/recipe/bundle/query) | file sha256s (receipts/ship_surface_hashes.txt); recipe: cosine mounds, seed 4598321 | Campaign-authored (this branch, F01/F02 integrated commits) | AGPL-3.0 (repo) | CLEAR |
| R14 | `trunk_declaration.json` | file sha256 `94ff906e…3f1` | Campaign-authored (F03; trunk height Oku-derived 1.158 m per commit b4de4de8) | AGPL-3.0 (repo) | CLEAR |
| R15 | `product/` modules (4 + tests) | tracked @ HEAD (U01/U02/U03/X02 integrated commits) | Campaign-authored | AGPL-3.0 (repo) | CLEAR |
| R16 | Oku-2021 walker numbers (10.038 kg assembly) | `derived_numbers.json` sources block; xlsx sha256 `0dd92e44…` (verified on disk, matches receipt) | Oku, Ide & Ogihara 2021, Commun Biol 4:1831, DOI 10.1038/s42003-021-01831-w, supp xlsx via EuropePMC PMC7940622 (`oku_bipedal/download_receipt.json`) | **CC BY 4.0** — recorded from the article's permissions block, banked in the receipt. Shipped form = derived facts in code/data + citation | CLEAR (facts; CC BY attribution rides docs that present the derivation) |
| R17 | myo_sim v0.1.0 (vendored, **not in shipping chain**) | `E:/PythonChimera/vendor/myo_sim`; VERSION=`0.1.0`; LICENSE sha256 `1eb85fc9…c8c6` | MyoSuite/MyoHub (README); recorded claim `research_references/human/SOURCES.md` L31 | Vendored **LICENSE file = Apache-2.0** (read); upstream WebCheck 2026-09-24 confirms MyoHub repos Apache-2.0. The brief's "typically BSD" guess: refuted by both. Path drift: SOURCES.md says `external/myo_sim`, disk truth `vendor/myo_sim` | CLEAR (Apache-2.0) — not shipped today; if vendored later, LICENSE/NOTICE ride along |
| R18 | FreeMusco chimanoid XML | 0 hits in this worktree (find); lives at `E:/PythonChimera/.tmp/chimanoid.xml` + `forearm_package/` copies | FreeMusco (arXiv:2511.14205) fictional human-based character per `bindings.json` mapping_receipt | **EXCLUSION CONFIRMED structurally**: not present in the shipped tree; analysis-only pin recorded (`forearm_package/USTR_DIAGNOSTIC_RECEIPT.md @ b04a3acd`: "Nothing here executes anything"; R1 falsifier fired there) | CONFIRMED EXCLUDED — no license acquisition needed for ship |

---

## 4. Falsifier results

- **FIRED once, with evidence banked:** `morphosource_ct/download_receipt.json` asserts `"license": "MorphoSource standard commercial use, no rearchive, 3D yes"`. The pinned agreement PDF (same directory, sha-matched to both media receipts) is titled "**Commercial Use Prohibited**", and the banked media-manifest CSV field reads `CommercialUseNotPermitted`. A receipt paraphrase asserted terms its own pinned evidence refutes — exactly the falsifier class named at freeze. The correction is a RECORDING fix (one line in that receipt), flagged in §5, not made here (read-only audit).
- **Source falsifier: did not fire** — every enumerated artifact has a recorded source (the engine binary's source provenance is in-repo; its own hash is pending the build, which is an identity action, not a source gap).
- **Blanket-clearance check (the constraint):** no row was cleared by "a receipt exists". The MorphoSource receipt existed and was still read against its own PDF/CSV — that is where the contradiction was found. The constraint is load-bearing.

## 5. Gap list — each with the smallest acquisition action

1. **MorphoSource 000875604 distribution clearance (the shipping blocker).** Smallest action: an operator/registry decision recorded as paper — either (a) explicit written approval from the Content provider (Smithsonian NMNH — Division of Mammals; depositor Isabel Mormile; NSF 2341137) for the intended distribution, or (b) a recorded non-commercial distribution decision that ships the clause (a)/(b) acknowledgment + citation block (MorphoSource; Smithsonian NMNH; USNM:MAMM:USNM 497136; media 000875604; ark:/87602/m4/875604) AND banks the clause (f) plan to archive the derivative on MorphoSource within one year of product release, or (c) replace the render body with an asset the project owns. Evidence paths: `receipts/morphosource_000875604_rights_evidence.txt`.
2. **Receipt-paraphrase correction.** Smallest action: one-line edit to `tools/science_funnel/data/morphosource_ct/download_receipt.json`'s `license` field to quote the agreement title + CSV fields (not done here — read-only audit; hand to the campaign).
3. **Vulkan component disclosure.** Smallest action: bank the vulkan.lunarg.com SDK licensing registry page (or a manifest of `C:/VulkanSDK/1.4.328.1/Licenses/`) + the exact vulkan-1.dll version the package ships.
4. **MSVC/UCRT redistributable receipt.** Smallest action: record the exact vc_redist version + Microsoft's distributable-code license URL in the S02 package manifest.
5. **Engine binary identity.** Smallest action: at the S02 build, record the exe sha256 + toolchain versions (MSVC per README 19.44; note the README's "Vulkan 1.2" vs installed SDK 1.4.328.1 drift) in the package manifest.
6. **Package attribution set (pure assembly, no third-party consent needed):** BSD-3 blocks for numpy/scipy, PSF license text for CPython, AGPL-3 license text, Apache-2.0 LICENSE only if myo_sim is ever vendored, and the Oku 2021 + Turnquist & Kessler citations in product docs.
7. **myo_sim path drift (recording fix, non-blocking):** `research_references/human/SOURCES.md` pins `external/myo_sim`; disk truth is `E:/PythonChimera/vendor/myo_sim`.

## 6. S02-readiness verdict

**NO — a package cannot legally ship today.** What blocks it is exactly one third-party consent: the player-visible animal (R3–R6, the MorphoSource 000875604 derivative chain) carries `CommercialUseNotPermitted`, copyright status UND, a no-re-deposit clause, and a one-year derivative re-archival obligation — and the in-product acknowledgment/citation block required even for non-commercial distribution does not exist yet in the slice UI/package. Everything else is recorded and clear or actionable without consent: repo code is AGPL-3 (own terms), numpy/scipy/CPython BSD/PSF, myo_sim Apache-2.0 (not shipped), chimanoid confirmed excluded, Oku numbers are cited facts (CC BY 4.0 attribution). The Vulkan and MSVC component receipts are assembly-time paperwork, not consent.

**Order of clearing:** gap 1 (the MorphoSource decision — operator paper) → gap 2 (receipt correction) → gaps 3–6 fold into the S02 package manifest build. S02 can start its packaging machinery in parallel; its distribution-terms row stays BLOCKED until gap 1 lands.

## 7. Integrity

Writes confined to `tools/monkey_campaign/agents/S01_provenance/` (`brief.md`, `report.md`, `receipts/morphosource_000875604_rights_evidence.txt`, `receipts/vendor_library_and_dependency_licenses.txt`, `receipts/ship_surface_hashes.txt`). No file outside this dir was created, modified, or deleted; `tools/material_volume*` and `tools/tests/` listed only. WebSearch used once, to verify the on-disk myo_sim LICENSE against upstream (recorded in the receipt). Sources: [github.com/MyoHub/myo_sim](https://github.com/MyoHub/myo_sim).
