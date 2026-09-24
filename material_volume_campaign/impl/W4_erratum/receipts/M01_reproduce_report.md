# M01 report — independent reproduction and audit of frozen `1af0bbde`, reconciled against tip receipt `3db8bc4e`

Agent M01, 2026-09-24. Workspace `E:/ChimeraWork/mvc-20260924` (branch
`material-volume-campaign-20260924`, HEAD `0c5cbbf0`, exporter tip `3db8bc4e`).
Frozen revision under audit: `1af0bbdee68d6ddfdd02bf9bd948f7b22f914d56`.
All work confined to `material_volume_campaign/agents/M01_reproduce/`; `tools/`
and `docs/` untouched (integrity paste at the end).

**HEADLINE: the frozen revision reproduces today, independently. All 66 test
identities pass from fresh blob extraction; the one deviation is a
pre-declared, 1-byte, checkout-materialization artifact in a single verify
assertion, with byte-identical JSON content. The tip receipt's 59/66
adjudication, its canonical artifact hashes, and its OPEN-items inventory are
accurate — with three minor characterization notes and one decision request.**

---

## Acceptance verdict 1 — extraction manifest + hashes: MET

27 files extracted via `git show 1af0bbde:tools/<path>` (raw blob bytes,
LF-canonical, immune to `core.autocrlf=true`) into `work/tools/`, flat as the
suite layout requires; 3 frozen docs into `work/docs/`. Every extracted file
verified `BYTE-EXACT` against `git cat-file blob <oid>` sha256. Import closure
of the three proof suites: `material_volume.py`, `material_volume_admission.py`,
`material_volume_body_export.py`, `material_volume_body_export_reader.py`,
the three legacy check suites, the three proof/verify scripts, plus 12 JSON
fixtures/schemas/example-report and the prereg derivation script.

Manifest (path | git blob OID | sha256 of extracted bytes = sha256 of blob bytes):

```
material_volume.py                                            | 3d46b030e75d6200a1764aadf72d81be9942bcdc | a4eb96e6d59c51d9...
material_volume_admission.py                                  | 41615ec7d3f1488007fcd30e3d887702c6b51290 | 7d05774ad09af0bd...
material_volume_admission_checks.py                           | cb709f3b0271dedadabefb6867b6c9852c0cf831 | 09e592781c6860b2...
material_volume_admission_manifest_example.json               | c31ca8e449faa2c51e9ce4eb583a21fdc84298d4 | ce94883a6ceb6855...
material_volume_admission_partition_example.json              | 4fc6a55784c9c45cfafd1d0bbd86e661a064810e | 4f4f6bb3c2ee2ed0...
material_volume_admission_schema.json                         | de5e0c02df03338b3a3d7e2f77f770ce611eb306 | d7bf52072da57254...
material_volume_body_export.py                                | f6fd2af161705371cb9a59df941460ca2b8e2b84 | f80f6dcfe1d64bb2...
material_volume_body_export_checks.py                         | e050bd6e83f39ba72b9184838ddb236d9eb37e56 | e4ac8736eb9e5e36...
material_volume_body_export_example_report.json               | 2091bee63193f029b4adf7a9e4bc88a2ce1f277b | 5485c8c4fe73d679...
material_volume_body_export_groups_example.json               | cb8514ee1c9816c03f5d10b6fd325bf986762eb0 | ae6f83483743ac70...
material_volume_body_export_manifest_example.json             | c6acf49f221ec87a8b5d055ed30316fdc2e630c1 | 8211dae58c3b1ef8...
material_volume_body_export_partition_example.json            | 3b6e4f5265b486fb4f4d357e9e7dc905d9959c5b | f07e44a23b6400fb...
material_volume_body_export_reader.py                         | 8a30267f557512f6faf705e470f593313643dea5 | 5e08daa950ac2767...
material_volume_body_export_schema.json                       | 0dd4207e2cfb090d3bb023e2d64c340b4f92db15 | bae683cf3857adc9...
material_volume_checks.py                                     | 339ba5b4f4bf6e15601f642429a9c4e5ca7316ba | 821ff45d3835d5ec...
material_volume_example.json                                  | b2d741ecf9060e86612568e55f6072d4ed09899e | 20d15d859ca9fe04...
material_volume_export_proof_prereg_derivation.py             | dd99d073fd943966420a8bf57ec4a1e0f4d708ce | 15a42e3d21357350...
material_volume_export_proof_verify.py                        | 96ff4ac6a756781f7d44323d32d7024805664a6a | 282bc52bfa997c6c...
material_volume_frame_composition_groups_composed_example.json| 18a268d319fdb0a3a005eb3b6decb00891c5c061 | ba2e894398e75a89...
material_volume_frame_composition_groups_shared_example.json  | 324d4d8fe69dcf02042459e9e17be0bdb171d11f | 4cdc1552382ad62e...
material_volume_frame_composition_manifest_example.json       | 8460a504416acce1851ea6f1ac7d62f726cea5bd | dd4ab31fe17b9dde...
material_volume_frame_composition_partition_example.json      | 77fc64e3d100ef8e3c4c7f308c62ddcbb2215558 | bcd1aac13d990275...
material_volume_frame_composition_proof.py                    | 9462f32ecebeb540ad3febf26df930a0dd20bc20 | a5d762daefb136a0...
material_volume_shared_interface_groups_example.json          | 0b772bfe71398b52cdceb6bc247bc016d9dbb5ba | 7980c68af57d33c1...
material_volume_shared_interface_manifest_example.json        | 0ac49985993a86763644dc95931ee962b07b1a17 | ce43101ce85d31a2...
material_volume_shared_interface_partition_example.json       | 51f8ea76d2b46486095e9d90e1fbe80cf780ca92 | 9cacff65362ca04b...
material_volume_shared_interface_proof.py                     | dc6b507794941a4b3d0019afed6c4c39d2aa0f8d | 844170e92bd4cf82...
```

(docs: `work/docs/material_volume_export_proof_prereg_shared_interface.md`
sha256 `546c943d585cab6b…`, `…_frame_composition.md` `e5bf32fd94dcfd7f…`,
`…_proof_results.md` `d190eae0791277d1…`.)

The sha256[:16] values of the five proof-suite/tool files and the example
report match the tip receipt's "canonical artifact manifest" table row for row.
No later revision was substituted anywhere; the receipt's tip-only artifact
(`material_volume_export_verification_receipt.md`, the V1–V3 prereg, the
consumption-contract proposal) was read from `3db8bc4e` for reconciliation
only.

## Acceptance verdict 2 — preregistration frozen before runs: MET

`receipts/M01_preregistration.md` written (and the independent derivation
`work/m01_independent_derivation.py` authored) BEFORE any suite execution.
It freezes expectations E1–E8, the falsifiers F-M01-1…6, the stop rule (two
attempts per script), and — critically — the environment-sensitivity branch
HYP, derived from two pre-run measurements: (a) the example-report blob is
LF-authored (0 CRLF, 1 LF, 5472 bytes), (b) this Windows interpreter writes
`\r\n` to piped stdout. HYP predicted: from a raw-blob LF extraction,
`test_cli_determinism_and_saved_example_bytes` fails at exactly
`assertEqual(out1, saved)` with a 1-byte trailing-newline difference and
otherwise-identical JSON; from a checkout-equivalent CRLF materialization,
the author's 7/7 must reproduce.

Falsifier status: **none fired.** F-M01-1…6 all quiet. The HYP branch was
confirmed in every particular (that is the pre-declared "finding candidate"
outcome, not a reproduction failure).

## Acceptance verdict 3 — reproduction receipts (counts, determinism, wall time): MET

Environment: Windows 10.0.26200 x64, CPU-only, Python 3.14.3 (MSC 1944),
numpy 2.2.6, `PYTHONDONTWRITEBYTECODE=1` everywhere. Two materializations:

- **Set A = raw-blob LF extraction** (`work/tools/`) — my canonical form.
- **Set B = same blobs materialized CRLF** (`work/tools_crlf/`) — what
  `core.autocrlf=true` (this repo's setting, verified) produces on checkout,
  i.e. the author's conditions.

| script | Set A run1 / run2 | Set B run1 / run2 | wall time (A) |
|---|---|---|---|
| material_volume_shared_interface_proof.py | exit 0, `Ran 5 tests`, OK ×2 | exit 0, `Ran 5 tests`, OK ×2 | 0.309 s / 0.289 s |
| material_volume_frame_composition_proof.py | exit 0, `Ran 8 tests`, OK ×2 | exit 0, `Ran 8 tests`, OK ×2 | 0.299 s / 0.306 s |
| material_volume_export_proof_verify.py | exit 1, `Ran 7 tests`, **FAILED (failures=1)** ×2 | exit 0, `Ran 7 tests`, OK ×2 | 1.911 s / 1.989 s |
| material_volume_checks.py (standalone) | exit 0, `Ran 17 tests`, OK ×2 | — | — |
| material_volume_admission_checks.py (standalone) | exit 0, `Ran 21 tests`, OK ×2 | — | — |
| material_volume_body_export_checks.py (standalone) | exit 0, `Ran 8 tests`, OK ×2 | — | — |
| material_volume_export_proof_prereg_derivation.py | exit 0, "PREREGISTRATION CROSS-CHECK OK (H == Q == R2 within 1e-12)" | — | — |

The single Set-A failure is exactly the pre-declared HYP branch
(`receipts/setA_material_volume_export_proof_verify_run{1,2}.txt`): the
`assertEqual(out1, saved)` line; byte-level analysis (receipt
`setA_cli_example_raw.bin`) shows CLI length 5473 vs saved 5472, exactly one
differing byte at offset 5471 (`\r` vs `\n`), and newline-normalized equality.
All other six verify tests — including both nested-leaf-suite tests asserting
17/21/8/5/8 — passed inside Set A as well.

Determinism: all nine run-pairs (3 scripts × 2 sets + 3 legacy suites) are
byte-identical after normalizing the single unittest duration token
`in <float>s`; `--dump-observed` outputs byte-identical across two invocations
for both coupons; the in-test CLI out1==out2 assertions passed everywhere.
Case-execution totals by me: 59 leaf identities × (2 direct + 4 nested) + 7
verification identities × 4 = 382 executions, of which the only failures are
the two predicted Set-A executions of identity #63.

Observed-vs-frozen (`--dump-observed` against the prereg decimal literals):
Δmass = 0 everywhere; worst ΔCOM 1.11e-16; worst Δinertia 9.437e-16 —
reproducing the frozen results doc's delta table **to the last printed digit**
(2.78e-17, 1.39e-17, 5.55e-17, 9.44e-16, 1.67e-16, 8.88e-16, 1.80e-16).

## Acceptance verdict 4 — audit findings: MET (weak assertions named)

Independence beyond re-running (falsifier F-M01-5): I re-derived every frozen
analytic expectation from first principles, stdlib-only, in
`work/m01_independent_derivation.py` — exact rational unit-simplex monomial
integration plus exact affine maps (no `(m/20)(Σpp+SSᵀ)` vertex formula, no
Hammer–Stroud, no tensor congruence), with frame composition done exactly in a
hand-rolled Q(√3) quadratic-field type on **transformed vertices**. Result:
all rational expectations (SI bodies + recombination, FC domain cells +
combined, interface area 1/2) bit-exact (Δ = 0.0); composed-frame
rotations/origins bit-exact; run expectations in rotated frames within
9.159e-16 (float conversion of exact values). The frozen tables are correct
mathematics, not just internally consistent code. I also verified the
exporter's `_integrate_cells` algebra (central tet second moment
`(m/20)Σrrᵀ` + parallel-axis shift) is the exact analytic tetrahedron formula
by the same independent route.

Weak assertions named (audit, not just re-run):

- **W-1 (tautological flags).** `full_symmetric_tensor`,
  `off_diagonal_terms_preserved`, `principal_axis_transform_applied` are
  hardcoded literals the exporter writes into its own report
  (`_body_mass_properties`); the F4 flag assertions therefore partly test
  "the exporter declares what it always declares". Not load-bearing — the
  tensor VALUES are independently pinned by frozen-literal comparison, and the
  reader re-checks symmetry numerically — but the flags would not catch a
  future code path that computes them dishonestly.
- **W-2 (materialization-sensitive assertion — new finding M01-F1).**
  `test_cli_determinism_and_saved_example_bytes` byte-compares CLI stdout to a
  working-copy file, so the battery's 7/7 is checkout-materialization
  dependent on Windows/autocrlf (7/7 from a CRLF checkout; 6/7 with a 1-byte
  trailing-newline difference from LF bytes). The receipt's own M-1a lesson
  ("working-copy hashes are not portable identities") applies to its own V1
  battery. Content-equal; no acceptance criterion depends on the newline; but
  "Ran 7 tests OK" is an environment-conditioned fact, and future receipts
  should state the materialization (or the reader/verify should normalize
  trailing newlines).
- **W-3 (textual import audit).** The verify suite's oracle-independence audit
  is regex/token-based with a heuristic oracle-block detector; as a guard it
  can false-negative. The substantive independence evidence is the frozen
  literals plus (now) my independent derivation, not this textual check.
- **W-4 (minimal perturbation test).** The anti-coincidence check perturbs one
  density in one coupon and asserts only the mass (13/6 kg). Sufficient
  against constant-table coincidence; a tensor-level perturbation check would
  be stronger.
- **W-5 (T_PROTECTED gate scope).** "Off-diagonals survive" is only enforced
  for terms with |expected| > 0.002. In these coupons every off-diagonal is
  protected (smallest 0.0045753), so nothing is excluded here — but the
  mechanism would not re-fire for a silently dropped near-zero off-diagonal in
  a future coupon.
- **W-6 (M-1a wording).** The receipt's parenthetical "the example report is
  CRLF-authored" is wrong about the blob: the `1af0bbde` blob is LF-authored
  (0 CRLF; my sha256 `5485c8c4…` equals the receipt's own canonical LF hash).
  What was "CRLF" was the recorded working-copy hash (`d71f7621…`). M-1a's
  substance is correct and its mechanism reproduced (see verdict 5).

Strengths acknowledged: expectations frozen pre-execution with hand rationals
cross-checked by two other routes; oracles file-local with different
mathematics (vertex-transforming quadrature vs the exporter's `RᵀIR`); falsifier
F7 actively asserts schema flatness and the smuggled-`parent_frame` refusal;
failures (C-0…C-6, V3-F) are preserved in the open rather than tuned away.

## Acceptance verdict 5 — full 66-row reconciliation: MET

V2 inventory fully reproduced: 66 unique identities; per-module counts and
`listing-sha256[:16]` match the receipt exactly (newline-joined sorted
qualified names): checks 17 / `838d5bf26e7eb88d`, admission 21 /
`3b230e19d1e95da9`, export checks 8 / `f02f7f4b4ff01133`, SI proof 5 /
`3366b8c609c51d5d`, FC proof 8 / `25507952edb39d51`, verify 7 /
`489fdeabce8367d6`. Full listing: `receipts/v2_identity_listing.txt`.

Legend: **REP** = REPRODUCED-MYSELF (identity ran and passed today from frozen
blob bytes, receipt file cited). All 66 rows are REP; row 63 carries the
pre-declared materialization annotation. Zero rows are TRUSTED-RECEIPT-ONLY at
test level. (Historical execution-record claims about *d2c23741-era* runs R1–R5
are marked TRUSTED where they describe runs I did not witness, but the three
legacy suites are same-blob across `d2c23741`→`1af0bbde`, so my standalone runs
directly reproduce R1's module counts on identical bytes.)

| # | module.test (short) | row | verdict |
|---|---|---|---|
| 1-17 | material_volume_checks (compiler): json-safety/refusals; degenerate/inverted/open/nonmanifold refusals; duplicate mass owner; independent simplex oracle w/ heterogeneous density; schema volume-source; density change; overlapping/disconnected; shared-interface cancellation + closure; stiffness not mass input ×2; subdivision invariance; thin-sheet/effective-skeletal exclusion; translation invariance; bipyramid interface; scaling laws m³/I⁵; unit simplex vs analytic; unresolved/conflicting defaults | leaf | REP — `setA_material_volume_checks_run{1,2}.txt` (17/17 OK ×2) |
| 18-37 | material_volume_admission_checks: reorder invariance; duplicate ownership; unit equivalence; subdivision identity; one mass authority; canonical admit report; missing cell; missing density; relabeling; removed component; rigid transform; scale declaration; schema/examples valid; shared-face orientation; source-effective ×2; surface overlay; touching vs overlapping; uniform scale laws; unresolved retained; vertex bijection | leaf | REP — `setA_material_volume_admission_checks_run{1,2}.txt` (21/21 OK ×2) |
| 38-45 | material_volume_body_export_checks: authored transform of COM+full tensor; duplicate ownership refusal; missing-density blocked; untrusted passed-flag/nonrigid/reflected refusal; hashes+CLI deterministic+finite; unsupported authority without mass reads; two groups recombine to partition total; unassigned cells surfaced | leaf | REP — `setA_material_volume_body_export_checks_run{1,2}.txt` (8/8 OK ×2) |
| 46-50 | shared_interface_proof: F1 exported bodies vs frozen; F1 recombination vs partition total; F2 interface no-duplicate-material; F4 off-diagonals retained; F5 quadrature vs frozen rationals | leaf | REP — `setA_material_volume_shared_interface_proof_run{1,2}.txt` (5/5 OK ×2) |
| 51-58 | frame_composition_proof: F1 run masses; F3 shared-run COM+inertia; F3 composed-run COM+inertia; F3 direct-vs-composed routes; F3 cross-run domain recovery; F4 off-diagonals retained; F5 quadrature vs frozen domain; F7 schema blocker stands + smuggled parent_frame refused | leaf | REP — `setA_material_volume_frame_composition_proof_run{1,2}.txt` (8/8 OK ×2) |
| 60 | export_proof_verify.test_audit_perturbation_tracking_agrees_with_quadrature | verif | REP — passes in all 4 runs |
| 61 | …test_audit_proof_oracles_do_not_import_shared_code | verif | REP — passes in all 4 runs |
| 62 | …test_audit_quadrature_oracles_are_file_local | verif | REP — passes in all 4 runs |
| 63 | …test_cli_determinism_and_saved_example_bytes | verif | REP-with-finding M01-F1/W-2 — Set A: FAILED ×2 exactly as pre-declared (1-byte `\r\n` vs `\n`; JSON equal); Set B: passes ×2 (`setB_material_volume_export_proof_verify_run{1,2}.txt`) |
| 64 | …test_proof_suites_pass | verif | REP — passes in all 4 runs (nested 5+8 green) |
| 65 | …test_reader_accepts_example_and_coupon_reports | verif | REP — passes in all 4 runs |
| 66 | …test_reproduced_legacy_suites_are_17_21_8 | verif | REP — passes in all 4 runs (nested 17/21/8 green) |

(Verify rows are numbered per the canonical alphabetical listing in
`receipts/v2_identity_listing.txt`, matching the receipt's identity order.)

**Receipt-level checks (beyond the 66):**

| receipt claim | verdict |
|---|---|
| V1 battery reproduction (7/7, nested 17/21/8/5/8) | REPRODUCED-MYSELF in Set B (author's materialization); Set A 6/7 per M01-F1 |
| V2 inventory + listing hashes | REPRODUCED-MYSELF (exact match, all 6 modules) |
| V3 M-1a mechanism (blob OIDs stable; working-copy CRLF-dependent) | REPRODUCED-MYSELF: `git ls-files --eol` shows `i/lf w/crlf` for lane files in this worktree; blob OID of the example report byte-identical to my extraction |
| V3 canonical sha256 table (8 key artifacts) | REPRODUCED-MYSELF, all 8 rows exact |
| V3 aggregate 33-blob digest `ee27dcd2…` | **NOT REPRODUCED — DECISION REQUEST DR-1.** My natural 33-file set (27 `tools/material_volume*` + 6 `Chimera/docs/matter/material_volume*`, count matches) with sorted-OID serializations (LF/CRLF, trailing/no-trailing, path-annotated, comma/JSON forms) does not yield `ee27dcd2…`. The receipt does not record the serialization or the exact file list. Per-file identities all reproduce, so this is an aggregate convenience hash only — but the receipt should record its construction. |
| C-1 adjudication | REPRODUCED-MYSELF: `d2c23741` example (277-line pretty JSON, 8399 bytes) vs `1af0bbde` (5472-byte canonical single line) — json-equal confirmed by my diff; the two preregs + 7 fixtures + derivation script are diff-empty across the same range, so no frozen criterion changed |
| C-2 adjudication | REPRODUCED-BY-INSPECTION + RUN: committed SI proof labels self-consistent (`mass_kg` family throughout); suite 5/5 ×4 |
| C-3 adjudication | REPRODUCED-BY-INSPECTION: verify `allowed_roots` contains `"__future__"`; suite 7/7 under author conditions |
| V3-F / C-5 | TRUSTED-RECEIPT-ONLY for C-5's transcription-typo narrative (pre-C-5 artifact not in git history to diff); V3-F "not rescinded" is consistent with M-1a as reproduced |

**OPEN items — each verified real and characterized:**

1. **Independent-reproduction character — RESOLVED BY THIS RUN.** The receipt
   left "executed as author-side reproduction (independent character OPEN)".
   My characteristics: different author session (M01; original by
   glm53-lead-02/Codebuff sessions), no shared session state, extraction
   directly from git objects with per-file BYTE-EXACT verification (never the
   author's working tree), fresh interpreter processes on Python 3.14.3 /
   numpy 2.2.6 (author's interpreter unrecorded — no count or value deviation
   observed), same machine and object store (identity pinned by blob OIDs).
   Independent *mathematics* supplied by my from-scratch derivation (F-M01-5,
   all literals confirmed). Residual non-independence: same hardware/repo; my
   audit reads the author's code (inevitable). Claim now supportable:
   "export arithmetic verified on the tested coupons AND independently
   reproduced (M01, 2026-09-24); independent-reproduction item CLOSED."
2. **Proof audit not executed — EXECUTED BY THIS REPORT** (verdict 4): weak
   assertions W-1…W-6 named; no incorrect assertion found; M01-F1 added.
3. **C-1/C-2/C-3 adjudication — ADJUDICATED ABOVE:** all three preserved the
   frozen acceptance criteria (prereg/fixture diff-empty; content-equal C-1).
4. **U7 reader-on-blocked/refused — REAL, parenthetical imprecise (DR-2).**
   Verified by inspection: the reader (`summarize_export_report`) is referenced
   only by the verify suite, only on `complete` reports; **zero** reader
   references in any legacy suite — so "(legacy tests cover `unsupported`)" is
   wrong if read as reader coverage; what legacy tests cover is the
   *exporter's* unsupported status. The reader's blocked/refused/`not_exported`
   group branches (including `blocked_group_has_mass`) exist and are untested.
   Request: reword U7's parenthetical in the receipt.
5. **U1–U10 each checked:** U1 real (every groups fixture = 1 cell per body);
   U2 real (all four manifests `scale_to_m: 1.0`); U3 real (exactly one shared
   face in the only interface coupon); U4 real (no large-coordinate /
   near-degenerate / extreme-ratio export fixtures; density ratios only 2:1);
   U5 real (scaling-law tests exist at compiler/admission level only); U6 real
   (reorder invariance tested at admission level only); U7 as above; U8/U9
   real (no consumer exists; contract is a proposal at tip); U10 real (scope
   statements in every artifact). The receipt's U-item inventory is accurate.

## Acceptance verdict 6 — integrity: MET

```
$ git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- tools Chimera/docs/matter
(empty)
```

Failures preserved verbatim: `receipts/setA_material_volume_export_proof_verify_run{1,2}.txt`
(2 predicted failures), plus one mid-authoring defect in my own tooling, fixed
before any frozen-rev run (derivation monomial formula and moment assembly
corrected; the corrected file is what confirmed the frozen literals).

## Decision requests

- **DR-1:** record in the tip receipt the exact serialization + file list of
  the 33-blob digest `ee27dcd2…` (or replace it with the per-file manifest,
  which reproduces exactly).
- **DR-2:** reword U7's "(legacy tests cover `unsupported`)" — no legacy test
  exercises the reader; exporter-side unsupported status is what is covered.

## Artifacts

- `brief.md` (verbatim brief) · `receipts/M01_preregistration.md` (pre-run)
- receipts: `setA_*` (6 suite scripts × 2 runs, derivation, CLI raw bytes,
  2×2 dumps), `setB_*` (3 scripts × 2 runs), `v2_identity_listing.txt`
- work: `tools/` (27 frozen blobs), `tools_crlf/` (Set B), `docs/`,
  `m01_independent_derivation.py`

STOP — all six acceptance criteria verdicted.
