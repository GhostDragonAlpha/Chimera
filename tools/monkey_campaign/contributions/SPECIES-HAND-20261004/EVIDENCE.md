# EVIDENCE — species-hand lane (wk-species-hand), PHASE 1: acquisition + screening records

Task: the Captain's both-in-parallel ruling on the open species-geometry
referral (LIEUTENANT_RESUME_v2.json line 144/147). Mission: screen whether a
SPECIES-TRUE macaque hand geometry can do what the proven verdict says the
hybrid cannot (PR #344 merged at astra `28a110f2eb3ec6495318bb70738d4408859e4ac3`;
354/354 GENUINE at the bone level; 0/197,280 tested placements at the hybrid).
Phase 1 = acquisition + screening records, NO physics runs. Acceptance =
sealed receipts, never prose. NO_WORKTREES honored: no worktree, no clone;
the lane's one CPU execution ran through
`python -B E:/PythonChimera/tools/monkey_campaign/task_package.py seal|run`
on slot 2. Write scope: this NEW lane dir + this card's own task-package
contribution dir + the data store below. No other lane's bytes touched.
Checkout: `E:/PythonChimera`, branch `WK-ENGINE-PATHS-20260929-PR`, HEAD
`7222729eca6e9f97f25061c8b1dc3d229bb703d8` (read-only for this lane; dirty
work preserved). Phase 1 performed 2026-10-04 UTC.

## 1. Source (a) — Pisa rhesus skeleton STL: RESOLVED + LICENSED (CC BY-SA 4.0), NOT per-bone segmented

- Download 2026-10-04 from
  `https://upload.wikimedia.org/wikipedia/commons/8/8b/Macaca_mulatta_3d_scan_Natural_History_Museum_University_of_Pisa_C_1549.stl`
  (URL taken from the Commons API imageinfo, HTTP 200).
- License verified AT RETRIEVAL, twice: (i) Commons API extmetadata —
  UsageTerms "Creative Commons Attribution-Share Alike 4.0", LicenseUrl
  `https://creativecommons.org/licenses/by-sa/4.0`, AttributionRequired
  true, License "cc-by-sa-4.0"; (ii) the archived file description page
  (revision 1146578100, category CC-BY-SA-4.0, Wikidata P275=Q18199165).
  Artist Patrizia17 (own work), DateTimeOriginal 30 July 2024.
- Integrity: 124,518,634 bytes; source-declared SHA1
  `67e0dcbffb7f64195da29d4507bfd7f0bc9a8ff4` reproduced EXACTLY.

## 2. Sealed runner job (the segmentation screening)

- Job `cb5d4a640caf4020ab6874d4361e7570`, slot 2, state PASSED, exit 0,
  cleanup_verified TRUE, base `28a110f2eb3ec6495318bb70738d4408859e4ac3`
  (== the astra tip, PR #344 merge), sealed manifest
  `ccce193f0fea329cfdd63339b31f17c3c213aee3800dbc8983a9d58c015c4155`.
  Result dir `E:/ChimeraWork/task-runner/results/cb5d4a640caf4020ab6874d4361e7570/`.
- Command: `C:/Python314/python.exe -B
  tools/monkey_campaign/contributions/SPECIES-HAND-20261004/stl_inspect.py
  E:/ChimeraWork/research-data/20261004-species-hand/Macaca_mulatta_3d_scan_..._C_1549.stl`.
  Declared keeps: the three outputs below. Structural inspection only
  (numpy/scipy weld + connected components; deterministic; no physics).
- MEASURED VERDICT: binary STL, 2,490,371 triangles; AABB extents
  (270.199, 493.65, 369.055) units; TWO connected components under both
  exact and quantized welds — the skeleton as ONE merged surface
  (2,490,359 tris) + one stray 12-triangle chip. **THE HAND BONES ARE NOT
  PER-BONE SEGMENTED IN THE SOURCE.** In-job re-hash of the inspected file
  reproduces the download sha256 exactly (TOCTOU guard green).

## 3. Load-bearing artifacts (sha256)

Data store `E:/ChimeraWork/research-data/20261004-species-hand/`:

| artifact | sha256 |
|---|---|
| Macaca_mulatta_3d_scan_Natural_History_Museum_University_of_Pisa_C_1549.stl (124,518,634 bytes) | `3f1536a9ab5c60479364535238d1531bd0b05862bd692edcf53047af51e526fe` |
| receipt_pisa_stl.json (acquisition receipt) | `ef342aab119646cc858b28b0d3940b5a80cc943e9e90d53251be55401dfc9601` |
| commons_api_imageinfo.json (lane copy; license evidence i) | `f2c67ba2cb29be51898294bd74ecc7b6b80033e9cb0cbf5d9b0a8754f76459e1` |
| commons_file_page.html (archived description page rev 1146578100; license evidence ii) | `999de0c6dce39e642d7da1b120b8104ab4847cf3681b7980ed1b4c45af74779c` |
| morphosource_m84422_license_check_receipt.json (source (b) determination) | `2543a08f51a5b787287850052ae0210a9f4630ed1ee338375199b47282532f5a` |
| morphosource_m84422_page.html (the Anubis bot-wall HTML, 7,435 bytes — direct-fetch evidence) | `f429b70e8858bbbb6ae0fe6953bfa728ec46567c2e5f8512e2eb28d3b4a362ca` |
| almecija2024_scidata.html (Primate Phenotypes paper archive) | `417f851b9d28069fcfc75307f5c7a29028b7b22b32f15bdfd6efddf703117351` |
| visible_monkey_jkms2020.html (source (c) lead archive) | `88e1b6457e8b90794935c0cac35bd0856c84a1cecd26f85af5c638f090916a95` |

Lane `E:/ChimeraWork/monkey-coordination/species-hand/`:

| artifact | sha256 |
|---|---|
| SOURCE_VERDICTS.md (the phase-1 record; DRAFT-status lane record) | `e1bd481cb2c7c71f330bd2eae7db22e26cf069d2efc7b0b46398d29460c3236b` |
| PREREGISTRATION_SPECIES_SCREEN.md (THE PREREG DRAFT; DRAFT until the Lieutenant commits it ALONE FIRST — the committed bytes are the freeze) | `77513d085ee11bca283dfde5a1363e0b13dbfe3e4500276a27baca452a26eb18` |
| EVIDENCE.md (this file; re-hashed at every append) | self-referential |
| commons_pisa_category.json (source (c) Commons category listing, 100 members) | `3b768fb2ac05a1e32b6f4bf5072237a0a8580384e8aa15dde940dcddcab9edf0` |
| package/files/.../stl_inspect.py (the only new logic file) | `2fc87dee3447ef6578b0a21754301b1ce4043eef4d9ab796f557b084f534a95a` |
| package/sealed/94dce8304b0b483cab2d232442ab82c8/manifest.json (THE SEAL USED BY THE RUN) | `ccce193f0fea329cfdd63339b31f17c3c213aee3800dbc8983a9d58c015c4155` |
| package/sealed/94dce8304b0b483cab2d232442ab82c8/change.patch | `f9eafb973a7ab468c0c1a12de37070ecc8b1963081597f09447e52985bb139d5` |
| package/sealed/6a2751d5aad74a61b6677a4abad450bb/manifest.json (ACCIDENTAL DUPLICATE SEAL — created by an inadvertent re-run of the seal command at record time; identical substance: same changed file, same file hash, same patch sha256 `f9eafb97...`; different manifest uuid/timestamp. PRESERVED and labeled SUPERSEDED — the run receipt binds to the ORIGINAL seal's manifest `ccce193f...`) | `52a95222241c1b4a1fb5591c8c9a8c16d4b99ff3125b554447a8cac917b40b40` |
| package/sealed/6a2751d5aad74a61b6677a4abad450bb/change.patch (identical bytes to the original patch) | `f9eafb973a7ab468c0c1a12de37070ecc8b1963081597f09447e52985bb139d5` |

Runner-verified artifacts (twinned byte-identical at
`species-hand/final_inspect/`; twins re-hashed at twin time, values match
the runner receipt's artifact map):

| artifact | sha256 |
|---|---|
| outputs/stl_inspect_receipt.json | `7401fca56f667274602c7c12a8b8c7befb0190dc362c8b1d115295a6e7f7aaae` |
| outputs/stl_inspect_report.txt | `8caa4c97fd1a1410ef10ee4ab719751a83436c1fb78513bb44f15ba718bde7cc` |
| outputs/stl_components_quantized.csv | `51e9e8a7930d6189d824b00583e1bca75b09926f0ddb343cab92146f263a5e52` |
| runner.log | `8cb12f24570839d6c53ada9f7b555be933dae43827e61ec1998b184480998228` |
| receipt.json (runner receipt; artifact map above; cleanup_verified true) | `6eef341541ef61cf3af782b0578ce64d45ead237de8bd086a9e5387255679421` |

Pins cited by the prereg and independently RE-VERIFIED by this lane
(byte-exact, 2026-10-04):

| pin | declared | observed |
|---|---|---|
| instrument_v2.py (frozen instrument; lane copy `grasp-candidates/package-v22/files/tools/monkey_campaign/contributions/GRASP-CANDIDATES-20261002/instrument_v2.py`) | `9514c5b15a27948c65563070f16dffee4a5a28347c281a5d7e255fe93e516ddd` | MATCH |
| A05 mutation structure JSON (`evidence-store/MAT2-A05/workspace_evidence/48b037593f63_mutation_structure.json`) | `48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d54f45649` | MATCH |
| A05 XML (`.../9c91124600ab_macaque_hand_mutation.xml`) | `9c91124600abc67a4a33d78ce79ab1a0604a48b5a9a2e6377d15de05717e5adf` | MATCH |
| anchor surface `E:/PythonChimera/tools/science_funnel/data/macaque_arm/Geometry/hand.vtp` | `a06ea7e079c849df07d6eec001e9bcc2ea193ecd3914011c78a993a5faa94fc6` | MATCH |
| Limblab `monkeyArm_current.osim` | `4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895` | MATCH |

## 4. Source (b) — MorphoSource M84422: CHECK ONLY; NO DOWNLOAD (determination)

- The record (fields retrieved 2026-10-04 via a reader-service fetch; direct
  fetches hit the Anubis bot wall — archived) states: "Creative Commons
  license: --", "Copyright statement: Copyright Undetermined", "Morphosource
  use agreement type: Standard", "Permits commercial use: Commercial Use Not
  Permitted", "Permits 3D use: 3D Printing Permitted", "Required archival of
  published derivatives: On MorphoSource". Download requires login +
  click-through acceptance + a 50-char intent statement.
- CORRECTION to the earlier chain-wide shorthand: M84422 is NOT "CC BY-NC" —
  it carries NO formal CC license and an undetermined copyright; the
  operative terms are the MorphoSource Standard agreement with commercial
  use not permitted. Permitted (for an authorized human acceptor):
  non-commercial research use, 3D printing, citation of Almecija et al.
  2024 SciData + NSF attribution + derivative re-archival on MorphoSource.
  Forbidden: commercial use (unqualified); redistribution beyond the
  agreement is unverified here.
- DETERMINATION: download refused (contract acceptance this agent cannot
  verify or accept); unusable for the released-product path in any case
  (open engine + unselected game license); species mismatch (N. larvatus is
  not M. mulatta); raw CT stack (2,049 TIFF, 0.076354 mm iso, 912 MB) —
  segmentation labor entirely on this project. Nothing downloaded.

## 5. Source (c) — additional sources (recorded, none adopted)

1. Commons Pisa collection (100 members listed): all primates are
   whole-skeleton scans; no hand-only STL; same merged-mesh limitation BY
   WORKFLOW INFERENCE (measured only for C 1549).
2. Primate Phenotypes project 00000C706 (6,192 media; hands/feet
   best-covered): "open download" per the 2024 SciData paper, but the
   per-record terms measured at M84422 govern its family; per-record checks
   need a manual operator account.
3. oVert collection 000368762: reported CC0-oriented; Macaca-hand presence
   UNVERIFIED (bot wall). LEAD ONLY; manual follow-up named.
4. Visible Monkey (JKMS 2019/2020): CC BY-NC 4.0 + ETRI user certification
   gate; 167 whole-body structures; per-bone hand not demonstrated. Excluded.
5. Limblab monkeyArm model: pinned already; single hand body + envelope —
   no per-bone bones; frame/constraint source only.
6. MDPI Anatomia rhesus-hand musculature (CC BY 2024): anatomy context
   only; no 3D geometry.

## 6. What exists / what does NOT (status separation)

- IMPLEMENTED/ACQUIRED: the source (a) acquisition + license verification +
  hash-verified storage; the sealed structural inspection (one job, PASSED);
  the phase-1 records + the prereg DRAFT.
- NOT DONE (and not claimed): no per-bone segmentation (Stage 0 — gated,
  requires Lieutenant authorization + Sergeant visual review); NO instrument
  rerun (zero physics runs executed by this lane); no prediction beyond the
  preregistered UNKNOWN + battery prediction; no registration; no labeling;
  no adoption of sources (b)/(c).
- THE HONEST GO/NO-GO: CONDITIONAL GO — gated exactly on Stage 0
  (fidelity-authored segmentation under anti-tuning law, `UNRESOLVED_BONE`
  class non-verdict-bearing, independent visual review, Stage-0/ladder
  firewall). If the Lieutenant does not authorize an authored-segmentation
  stage, the honest verdict is NO-GO for the species-true ladder this phase
  (no directly usable permissive source exists; the referral's species
  question stays answered at exactly: source real, licensed, not yet
  per-bone). Full statement + the absent list in SOURCE_VERDICTS.md.

## 7. Chain position and next actions

- Chain stop 1 (this phase) is COMPLETE: prereg draft path
  `E:/ChimeraWork/monkey-coordination/species-hand/PREREGISTRATION_SPECIES_SCREEN.md`,
  bytes sha256
  `77513d085ee11bca283dfde5a1363e0b13dbfe3e4500276a27baca452a26eb18`.

### 7.1 Evidence anchoring (append)

- ANCHORED (evidence-store `anchor.py add`, card SPECIES-HAND-20261004,
  manifest rows appended, re-verify OK): the four sealed inspection
  artifacts (stl_inspect_receipt.json / stl_inspect_report.txt /
  stl_components_quantized.csv / runner_receipt.json — sha256 as section 3)
  as class numerical, and the MorphoSource M84422 license-check receipt
  (sha256 as section 3) as class source. The 124.5 MB STL itself stays in
  the research-data store referenced by hash (large-dataset law), not
  copied into the evidence store.
- NEXT (the Lieutenant, three decisions): (1) record chain-wide the (b)
  license correction (NOT CC BY-NC — no CC license, copyright undetermined);
  (2) rule on the Stage-0 authorization (GO branch) or record the NO-GO;
  (3) on GO, commit the prereg ALONE FIRST on the publication lineage
  (proposed contribution path
  `tools/monkey_campaign/contributions/SPECIES-HAND-20261004/PREREGISTRATION.md`)
  and return the commit pin; implementation packages then pin it. Sergeant
  review of THIS phase requested through the Lieutenant (no self-review; no
  picture claims from this text-only worker).
- Nothing else claimed; no other lane touched; no capacity claim made (this
  card's own CPU estimate lives in the prereg section 7).

---


# CHAIN STOP 2 — STAGE 0 (on the Lieutenant's GO + prereg pin)

## CS2.0 — the pin (verified byte-exact from the origin ref, FETCH_HEAD only)

- Commit c31227e9efcebc97fdac12389a0349ecd4a49be9 on
  origin/review/SPECIES-HAND-20261004, parent 28a110f2eb3ec6495318bb70738d4408859e4ac3
  (the astra tip); files
  tools/monkey_campaign/contributions/SPECIES-HAND-20261004/PREREGISTRATION.md
  (git cat-file blob sha256 77513d085ee11bca283dfde5a1363e0b13dbfe3e4500276a27baca452a26eb18
  — EXACT match to the lane draft) and SOURCE_VERDICTS.md (e1bd481c... —
  EXACT). The fetch touched no HEAD/index/branch/worktree.
- Implementation package species-hand/package-s0/ created at base
  c31227e9efcebc97fdac12389a0349ecd4a49be9 (2 committed files selected);
  the only new logic file stage0_segment.py.

## CS2.1 — the declared pipeline + frozen constants (recorded BEFORE execution)

- Method: coarse full-skeleton localization (H1=1.0mm vertex shell, dilate 2,
  3D fill, EDT h-maxima markers h=0.30mm above 1.2mm, nearest-marker Voronoi,
  small-part band 3-400mm^3, fan clusters >= 8 parts with AABB <= 150mm) ->
  fine per-candidate segmentation (H2=0.30mm, 16 fixed barycentric sample
  points/triangle, shell dilate 1, fill, EDT h-maxima h=0.20mm above 0.8mm,
  component-wise nearest-marker Voronoi, fragment merge < 15mm^3, per-part
  cut accounting, UNRESOLVED ceiling 0.35, marching-cubes STL export,
  deterministic renders). Robustness column h=0.10mm recorded never decisive.
- DECLARED TOOLING EXTENSION vs prereg section 7 (which governs the LADDER
  jobs): Stage-0 authoring/render jobs use stdlib+numpy+scipy+scikit-image
  0.26.0+matplotlib 3.10.8 Agg; deterministic; the ladder rerun itself stays
  stdlib+numpy/scipy.
- DECLARED WRIST CUT (added after the v3 hollow-shell finding, before the v6
  runs): plane perpendicular to the candidate box longest axis at the inner
  edge of the low-count end bin (fifths); triangles on the wrist side
  excluded (any-vertex rule); 2-voxel sealing slab; everything beyond the
  plane removed; faces toward the removed region charged as authored cuts.

## CS2.2 — selftest lineage (plumbing only, synthetic; NO results)

| version | seal (manifest prefix) | job | outcome |
|---|---|---|---|
| v1/v2 (synthetic design flaw: chain rods inside the cylinders) | 16bd6539 / ce5d584a | ac0f4dbe / 1acd4515 | PASSED but 2/5 expected markers; cause diagnosed (discrete EDT below the 0.8mm marker floor for the synthetic rods) |
| v3 (touching cylinders + disconnected rods) | d7d65344 | 2a635493 | PASSED, 4/4 markers, rods separate — GREEN |
| v4 (cap-flood fill attempt) | (superseded seal) | a97810e3 | FAILED — caps enclose the outer background; fill fills the whole box; approach abandoned, defect recorded |
| v5 (component-wise Voronoi + hollow-wall open tube) | 4b57ec1e (seal ef953f75) | 78d51515 | PASSED — 5/5 markers, open tube markerless/unassigned, sphere filled |

## CS2.3 — coarse localization (2 runs; determinism twin)

- Job 1 6e0405f2 FAILED on the missing-output law (this lane over-declared
  cand7 keeps that do not exist — 7 candidates, not 8; the lane own
  run-declaration error, recorded, artifacts preserved).
- Job 2 906697a1 PASSED (slot 2, base c31227e9..., seal d7d65344...):
  4,958 markers, 4,201 small parts, 7 candidate clusters; the four large
  candidates: cand0 (104 parts, 13,466mm^3, box 39x39x81), cand1 (98,
  16,730, 37x93x80), cand2 (65, 14,756, 67x92x50), cand3 (62, 11,435,
  46x69x68).
- DETERMINISM TWIN: the coarse receipt is BYTE-IDENTICAL across the two runs
  (sha256 a67cc3da4c7b52bf6ab6aa445a30542d555f09a3778ada206efb931a93a11249).

## CS2.4 — fine segmentation runs (the honest sequence)

| stage | seal (prefix) | jobs | findings |
|---|---|---|---|
| v3 (no plane) | 9dc10271 | cand0 dbf83080, cand1 59798eff, cand2 728595fc, cand3 6f133d02 (all PASSED, slots 2/3) | cand2: 14 parts, 24.4-1601.9mm^3, cuts 0.011-0.093 (+0.253 on the 24.4mm^3 part) — THE EXTRACTION CANDIDATE. cand0/1/3: hollow-shell collapse (1-3 parts) |
| v6 (wrist planes) | 03afff7d | cand0 b37aca3a, cand1 8a55f80b, cand2 4469be46, cand3 805e4d11 (all PASSED) | cand1/cand3 first ran with the plane direction INVERTED (kept the hand side, not the wrist) — honestly recorded (cand1: 0 parts in run 4a46aa6b); fixed with the declared keep_above flag. cand2 plane run discarded the fan (the low-count-end rule mis-picked the wrist side — Q5 for the Sergeant). cand0 STILL one fused mass |
| diag | 67b40fe4 | cand0 2607f24d, cand1 ce73052e | THE FUSED-MASS DIAGNOSIS: cand0/1 solids are HOLLOW unfilled shells — EDT deciles [0.30,0.30,0.30,0.42,0.52]mm, 1 component, exactly 1 h-maxima marker at every h in {0.05..0.50}mm. The box-sliced rims drain the interiors; fill produces a thin connected shell. cand1: 3 markers (the small parts) |

- BUSY/exit-75 handling: slot-2 lock contention observed and retried with
  >= 10s backoffs (never another lane job touched); all jobs eventually
  admitted on slots 2/3.

## CS2.5 — the Stage-0 honest state (what exists, what is UNRESOLVED)

- EXTRACTION CANDIDATE: cand2 no-plane run — 14 parts (per-part STLs +
  tables + renders), all cut fractions under the declared 0.35 ceiling,
  filled interiors (max EDT 0.735-0.949mm). WHICH candidate is a hand and
  WHAT each part is = the Sergeant visual labeling review (requested; the
  five questions are in stage0_review/REVIEW_REQUEST_VISUAL_LABELING.md).
- UNRESOLVED at extraction: cand0/cand1 (hollow fused masses — quantitative
  diagnosis above) and cand3 (2 parts after no-plane; 0 after its plane
  run). No bone from these is verdict-bearing; no labeling is attempted on
  them by this lane.
- NAMED CONTINUATION (not executed this phase — envelope discipline): the
  fill-failure mechanism is diagnosed (open rims at box faces drain the
  interiors); candidate fixes are rim-aware capping, per-axis 2D slice
  fills, or larger boxes with declared forearm cut planes; any such change
  is a NEW declared amendment with its own selftest, reviewed before any
  ladder contact.
- CPU envelope: the Stage-0 jobs (2 coarse + 12 fine + 2 diag + 5
  selftests) are within the declared <= 2 CPU-hour Stage-0 budget (bounded
  boxes; largest job minutes). No F6 overflow occurred; no budget extended.

## CS2.6 — load-bearing Stage-0 artifact hashes (twins under stage0_review/)

| artifact | sha256 |
|---|---|
| stage0_coarse_receipt.json | a67cc3da4c7b52bf6ab6aa445a30542d555f09a3778ada206efb931a93a11249 |
| stage0_diag_cand0.json | 5dc957c442bfd2393074e01cfdbe0556bc4e9cd1c6771370b6afa3f8f72a7a0f |
| stage0_diag_cand1.json | 21044a6f011b13358fba0be1ee4d6320abccfd98ac8759ad1904f1093e325a05 |
| REVIEW_REQUEST_VISUAL_LABELING.md | re-hashed at append below |

(The cand2 twin hashes: fine_receipt b78b1d153a74aa10..., parts_table
bed13743d42b2cd6..., contact_graph fd7e547e5cf06149..., part_meshes
29d8d484d45d580d... — 16-hex prefixes as twinned; full hashes live in the
runner receipt of job 728595fcf58f445b82b422d8aecbae21; the twins are
byte-copies.)

## CS2.7 — chain position

- The LADDER has NOT RUN. Nothing consumes any ladder quantity. The
  Sergeant visual labeling review is REQUESTED (through the Lieutenant) and
  gates everything downstream, per the Lieutenant ruling.
- NEXT (the Lieutenant): dispatch the Sergeant visual labeling review of
  stage0_review/ (the five questions). On its outcome: hand identified +
  labeled parts -> Stage 0-B registration (a new package pinned to this
  record); fused candidates -> the named continuation or the honest
  UNRESOLVED closure for those candidates.

## CS2.E — STAGE-0 ERRATUM (dated 2026-10-04, on the Sergeant visual verdict; the four record corrections + the five lane lessons; prior sections stand as written, corrected HERE, never edited in place)

Corrections 1-4 are driven by the Sergeant's visual verdict (PASS w/ the
gate consequence: cand2 = the RIGHT hand, cand3 = the LEFT hand,
cand0 = MUSEUM HARDWARE; 0/14 cand2 parts resolve to a single A05 bone —
all GROUP/OTHER = UNRESOLVED_BONE; bones fuse in webbing; the parts are
thin 1.5-1.9mm shells = SURFACES, not volumes) and by the lane's own
receipt re-derivation (every runner receipt re-read; the authoritative
census below).

### Correction 1 — THE FULL JOB CENSUS (27 Stage-0 jobs, not 21; +1 phase-1 = 28)

CS2.5's census ("2 coarse + 12 fine + 2 diag + 5 selftests") UNDERCOUNTED.
The authoritative census from the runner receipts (job | seal manifest
prefix | code state | state):

- selftests (7): ac0f4dbe (16bd6539, v1, PASSED), 52544d4d (ce5d584a, v2,
  PASSED), 1acd4515 (ce5d584a, v2, PASSED), 2a635493 (d7d65344, v3,
  PASSED), a97810e3 (7d06dea6, v4, FAILED — cap-flood removes everything),
  673c2231 (3b73d275, v5-first, FAILED — pad-tuple bug), 78d51515
  (4b57ec1e, v5, PASSED).
- coarse (2): 6e0405f2 (d7d65344, FAILED — missing-output law, lane's
  over-declared keep), 906697a1 (d7d65344, PASSED — the determinism twin).
- fine (12, four code states x four candidates):
  - d7d65344 (first batch; global Voronoi, no planes, no component-wise
    assignment): 68454d79 (cand0, 1 part 4,807mm^3), a5f33fef (cand1,
    3 parts 4,600/162/159), f7ff9d7e (cand2, 14 parts), a94f0c2a (cand3,
    2 parts 6,428/1,679) — ALL OMITTED from CS2.4/CS2.5 as written.
  - 4b57ec1e (component-Voronoi, no planes): dbf83080 (cand0, 1 part),
    59798eff (cand1, 3 parts), 728595fc (cand2, 14 parts — THE EXTRACTION
    CANDIDATE the Sergeant reviewed), 6f133d02 (cand3, 2 parts 6,428/
    1,679).
  - eef1f2ed (wrist planes, direction INVERTED): 6dfe541d (cand0, 1 part
    4,216 — direction happened correct for cand0), 4a46aa6b (cand1, 0
    parts — the honest inverted record), 82fac325 (cand2, 11 parts — the
    plane discarded the fan), 36652460 (cand3, 2 parts 1,012/576 — the
    plane kept the heel side).
  - f326da42 (wrist planes, keep_above fixed): b37aca3a (cand0, 1 part),
    8a55f80b (cand1, 3 parts 3,842/162/159), 4469be46 (cand2, 3 parts —
    the plane again discarded the fan), 805e4d11 (cand3, 0 parts).
- diag (2): 2607f24d (cand0), ce73052e (cand1) on seal 0b570430.
- phase-1 (1): cb5d4a64 (ccce193f, the STL structural inspection).

### Correction 2 — cand3 job attribution

The 2-part numbers quoted in the review request for cand3 ("no-plane run
job 6f133d02 | 2 (1,012.2, 576.1)") are MISATTRIBUTED. Those numbers belong
to job 36652460 (seal eef1f2ed — the INVERTED-direction plane run that kept
the heel side). Job 6f133d02 (4b57ec1e, genuinely no-plane) produced 2
parts at 6,428.1 / 1,679.2 mm^3. Neither is a resolved hand: the Sergeant's
verdict stands for the whole class.

### Correction 3 — the D-paragraph marker count

The review request's D note says "exactly ONE h-maxima marker at every h"
for cand0/cand1. Exact per candidate: cand0 = 1 marker at every h in
{0.05..0.50}mm; cand1 = 3 markers at every h (the two small parts carried
their own markers; the dominant mass never split). The fused-mass
conclusion holds for the dominant mass in both; the sentence as written
was exact for cand0 only.

### Correction 4 — the filled-interiors reword (the thin-shell finding)

CS2.5 and the review request describe cand2's parts as having "filled
interiors (max EDT 0.735-0.949mm)". REWORDED per the Sergeant's
measurement: the parts are THIN-WALLED SURFACE SHELLS (wall thickness
1.5-1.9mm; max EDT 0.735-0.949mm means no interior point ever exceeds
~1mm from background) — SURFACES, NOT VOLUMES. This is precisely why
0/14 parts resolve to a single A05 bone (all GROUP/OTHER =
UNRESOLVED_BONE): the fill never produced volume interiors for the fan,
and a surface shell cannot be a verdict-bearing bone for a volume-based
collision instrument. The "EXTRACTION CANDIDATE" status of cand2 is
DOWNGRADED accordingly: it is the best EXTRACTION ATTEMPT, and its parts
are all UNRESOLVED_BONE under the Sergeant's labeling.

### The five lane lessons (recorded as lane law)

- L1 WHOLE-BODY-CONTEXT IDENTIFICATION: a geometric candidate cluster can be
  MUSEUM HARDWARE (cand0), not anatomy. Candidate screening must include
  non-anatomical objects, and identification is a visual-review task, never
  a geometric inference.
- L2 BODY-FRAME RENDERS AS STANDARD TWINNED ARTIFACTS: every extraction's
  render set must include a whole-body-context view (the candidate located
  in the skeleton), so reviewers can orient without re-deriving pose.
- L3 PLANE-PLACEMENT ERRATUM LEVEL: an axis-aligned AABB end-bin plane
  cannot represent an oblique pose. The wrist DID sit in cand2's chosen
  bin; the plane REPRESENTATION was wrong. Pose-aligned oblique planes
  (point + normal from recorded visual identification) are required.
- L4 FULL JOB CENSUS: every launched job is enumerated with its seal and
  code state (this erratum demonstrates why — 6 jobs were silently missing
  from the first census, including an entire code-state batch).
- L5 THIN-SHELL GROUP LAW: any part whose wall thickness never reaches the
  declared minimum half-thickness of a verdict-bearing bone is THIN_SHELL —
  a surface, not a volume — and is GROUP/UNRESOLVED_BONE, never
  verdict-bearing, regardless of its cut fraction.

### Branch note (the Lieutenant's Option B ruling)

The continuation (rim-aware capping + per-axis 2D slice fills + larger
boxes with DECLARED POSE-ALIGNED OBLIQUE forearm cut planes; selftest v6
first with oblique-pose and webbed-fusion synthetic cases; thin-shell
consumption note; then re-run + re-review; ladder only after) is
AUTHORED as the amendment draft
`PREREG_AMENDMENT_CONTINUATION.md` (same directory), status DRAFT for the
Lieutenant's pin through the prereg law. THE CLOSURE fires if the
continuation's own review fails: the honest UNRESOLVED closure (0 verdict-
bearing bones from this source at this phase's method) stays recorded as
the fallback and would then close the species-true geometry question for
this source honestly.
