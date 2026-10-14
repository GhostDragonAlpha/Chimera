# GAIT / OBSERVATION INTAKE — 2026-09-17

Lane INTAKE-GAIT (GLM 5.3, worktree `E:\ChimeraWork\intake-gait-20260917`, branch
`lane/intake-gait-20260917` off 5a180eb4). The gait/observation slice of the
2026-09-17 database hunt, admitted through the batch pipeline with one receipt.

## RULE 0 (stated before the build)

**STATEMENT** — A wild-primate stride observation is admittable only as a
species-tagged, substrate-tagged row whose every measured value sits inside a
declared envelope; a deferred Dryad file is admittable only as a digest-pinned
identity claim that says on its face that the bytes are absent and exactly why.

**PREDICTION** — All 386 real stride rows of the pinned Janisch CSV admit
carrying species + substrate tags and pass the class checks; the 2.1 GB video
archive admits nothing; 387 fetched == 386 admitted + 1 quarantined.

**FALSIFIER** — One corrupted stride row (species, one angle, or substrate)
quarantines exactly itself while every neighbouring stride stays admitted; the
count identity closes with zero silent drops.

## WHAT WAS ADMITTED (one run, one receipt)

`python -B -m tools.creature_graph.batch_qualify --reprove all --admit
janisch_wildprimate_kin,granatosky_gait,higurashi_gait --apply --train exercise
--out tools/science_funnel/validation/batch_gait_20260917/receipt.json`

- **janisch_wildprimate_kin** — Janisch et al. 2024 wild primate limb joint
  kinematics, figshare `10.6084/m9.figshare.23231366` v1, CC BY 4.0. CSV
  `new_mergedkinematicdata.csv` (229,396 bytes) downloaded via direct
  ndownloader; sha256 `d0048076a68de3a881304884a0bf5e3fa87a37392ae567b16be8ec
  acf001608` matches the lane pin and the figshare API md5 context is pinned
  with it. **386 stride records** (14 species; the four quadrupedal
  cercopithecoids Papio, Chlorocebus, Cercopithecus, Lophocebus = 145 strides
  are the macaque-analog reference), each carrying species/sex/age tags,
  substrate tags (diameter m, orientation deg, plus height/compliance/tree
  species where measured), body mass, and every measured joint angle, mean,
  yield and excursion. The single all-NA row (file line 28) quarantines by
  design. Class `batch.observation.janisch_stride` (14 mechanical checks).
- **granatosky_gait** — Wimberly/Slater/Granatosky tetrapod gait database,
  Dryad `10.5061/dryad.z08kprrd5` v3, CC0. API v2 dataset + version file
  records pinned; **12 file-identity records** (11 analytic tables deferred,
  `Gait_Videos.zip` 2.1 GB `excluded_by_policy` per the intake order). Class
  `batch.deferred.dryad_file`.
- **higurashi_gait** — Higurashi & Kumakura Japanese macaque gait, Dryad
  `10.5061/dryad.fj6q573tc` v4, CC0. **2 file-identity records**
  (`Dataset_macaque-gait.xlsx` 23,042 B pinned to Dryad's declared sha-256,
  `Readme_macaque-gait.xlsx`), both deferred. Same class.

Totals in the receipt: 4,221 records verified across 8 connectors (5 legacy
re-proves byte-identical + 3 admissions), 0 contract failures, count identity
closed. The rebuilt store: 8,368 objects (+403), 12,979 relations, graph hash
`dbf302a4726f5abd45fb092933f89bc85ae330756d3027579ba04e0105610693`;
graphify consumer roundtrip HONEST (7 checks); the exact same admission command
re-run adds 0 objects and reproduces the hash (command-level idempotency,
receipt kept out of tree). Training gate: closed-proven-library-state, exercise
completed (wiring only, no policy claim).

## THE DRYAD DEFERRAL (recorded with cause)

The task's constraint: attempt the API; if scripted download needs a token I
cannot register, pin what the API gives and defer the bytes. Probed live
2026-09-17, evidence bodies committed in each connector data dir:

- `https://datadryad.org/api/v2/files/<id>/download` → **401** `{"error":
  "Unauthorized, must have current bearer token"}` (first-hand for mammal_gait
  / 863883 and for the Higurashi dataset zip download; pinned verbatim).
- `https://datadryad.org/downloads/file_stream/<id>` → **Anubis bot challenge**
  (the `.within.website` validation interstitial; 4,306-byte HTML pinned; no
  file bytes).
- Dataset and version metadata endpoints are authless and were pinned in full:
  title, authors, abstract, license (both CC0), version ids, and the complete
  file lists with Dryad-declared sha-256 digests and sizes.

A free Dryad API token (requires an account registration this agent cannot
perform) or one browser download by a human unblocks the bytes; until then the
admitted records are the byte-identity pins any future download must match.
Recorded honestly: Dryad's digests are API claims, unverified by download.

## FALSIFIER EVIDENCE (as tests, in the funnel suite)

`tools/science_funnel/tests/test_batch_gait.py` (19 tests, all passing):

- three corruption modes (species outside vocabulary, one angle at 999 deg,
  substrate diameter at -5) each quarantine exactly row 4 while row 28's
  pre-existing junk quarantine is untouched — 385 admitted + 2 quarantined;
- the whole-artifact membrane: dropping one row refuses the parse
  (`stride_row_count_changed`), never silently re-basing the count;
- bundle-level: the corrupted CSV through the full intake pipeline yields
  385 accepted + 2 quarantined in the bundle receipt;
- contract-level: mutating one admitted record's species flags exactly that
  record under the class contract; all 386 admitted records and all 14 Dryad
  records pass their contracts.

## SEAMS THIS LANE ADDED (shared-file edits, minimal and additive)

- `batch/contract.py`: two generic check kinds — `field_in` (string vocabulary)
  and `numeric_tree_range` (envelope over every numeric leaf of a payload
  subtree).
- `batch/connectors.py`: lane-module auto-load tail (`connectors_*.py` merge
  their CONNECTORS; duplicate connector ids refuse). This lane's modules are
  the first users; the convention exists so parallel intake lanes never edit
  each other's connector files.
- `batch/reprove.py`: the blob-index search dirs now derive from the merged
  connectors, so future re-proofs find lane data dirs without editing the list.
- `adapters.py` untouched (lane adapters live in `adapters_gait.py` and
  register into the shared ADAPTERS dict in place).

## BYTE-STABILITY DEFECT FOUND AND REPAIRED (pre-existing, in this lane's path)

Verifying staged blobs against receipt pins (a check this lane adds to its own
commit discipline) found that the 2026-09-17 batch had committed the
Copernicus EOXML **CRLF-stripped**: the git blob held 43,891 bytes where the
receipt pins 44,729 — under `* text=auto`, any fresh clone would fail
`pin_drift` on the copernicus re-proof (the admitting worktree masked it by
never re-checking the file out). Repaired here, under the same byte-stability
law the repo already established for evidence trees:

- `.gitattributes` gains one broad rule, `tools/science_funnel/data/** -text`
  (last match wins over `* text=auto`), covering every batch-connector data
  dir including the two 2026-09-17 ones that lacked per-dir rules.
- The drifted file was re-downloaded from its receipt-pinned S3 URL and
  verified byte-identical to the pin (sha256 `6e48b2289132d316fc05ca1df47e8
  ae4844d36a91f2ad1cee70a813cc2ce4527`, 44,729 bytes), restored, and the
  source re-proven: `copernicus.dem_glo30.n18w066`, 8 records byte-identical,
  zero contract failures.
- All 14 files staged by this lane were blob-verified against their receipt
  pins before commit (byte-exact in the index).

## HONEST LIMITS

- Admitted records stay `extracted`; batch admission is proven intake, never
  verification. No visual or physical reduction of the gait data is claimed.
- The Janisch angle conventions (sagittal-plane degrees at TD/MID/LO) are
  defined by the source R code, which is not machine-pinned; the phylogenetic
  eigenvectors PE_1..13 are omitted as derivable from the pinned consensus
  tree nexus attachment.
- Primate row-level coverage of the Granatosky analytic tables is unverified
  until the deferred bytes arrive.
- No macaque species is in the Janisch sample; the cercopithecoid rows are an
  analog, flagged on every record's source gaps.
