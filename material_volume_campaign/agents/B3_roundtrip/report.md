# B3 REPORT — reader/exporter round-trip: off-diagonals, provenance, explicit frames

**Agent:** B3 (`material_volume_campaign/agents/B3_roundtrip/`) · **Date:** 2026-09-24
**Worktree:** `E:/ChimeraWork/mvc-20260924`, branch `material-volume-campaign-20260924` (base `3db8bc4e`; HEAD at run time `cbe611aa`)
**Targets:** `tools/material_volume_body_export.py` (writer) ↔ `tools/material_volume_body_export_reader.py` (`read_json_file`, `summarize_export_report`, `canonical_json`) · Contract v0.9 (`Chimera/docs/matter/rigid_body_mass_export_consumption_contract_v1_proposal.md`)
**Verdict: VERDICTED — the parse layer is an exact round-trip (falsifiers F-B3-1/F-B3-3/F-B3-4 held); the reader's SUMMARY layer fires F-B3-2 with 42 DROPs / 0 DIFFs: contract §1 authoritative content (per-cell provenance, body_frame, volume, provenance pair member `material_mass_source_provenance`, mass invariance/unit fields, top-level admission binding) does not survive the summary projection on complete/exported reports — the U7 drop mechanism, hitting the exported-body path.**

---

## 1. Provenance of this run

The original B3 dispatch died in the campaign's 4th transient `[1302]` before any B3
artifact landed (the B3 dir was found empty; RECOVERY.md T5). This lane was rebuilt
from the coordinator's restatement: `brief.md` was reconstructed and marked as a
reconstruction, then **PREREG.md was frozen BEFORE any fixture, run, or measurement**
(receipt `00_prereg_freeze.txt`: PREREG sha256 `758f910b0495f716deaab8d329aff92db867f4967ebc7c987bc4e165c562a9ae`,
mtime 14:19:54; every fixtures/, work/, receipts/01+ artifact is younger). All
falsifiers, predictions, tolerance, and the stop rule below are the frozen ones; the
prereg file was never edited after freeze.

## 2. Fixtures (both genuine exporter inputs; files inside this dir only)

| fixture | bodies | frames exercised | why |
|---|---|---|---|
| `rotcoupon` (authored by B3) | body-R, body-S | body-R: **generic proper rotation R = Rz(37°)·Rx(23°)**, origin (0.1, −0.2, 0.3); body-S: identity, origin (10,0,0) | the required **nonzero-off-diagonals-via-rotated-authored-frame** fixture; rotation residual max\|RᵀR−I\| = 5.55e-17 vs exporter check 1e-10 |
| `shipped_example` (byte-for-byte copies of the shipped tools example triple) | coupon-body-A, coupon-body-B | identity; 90° z-rotation, origin (3,−2,1) | reuse law; second rotated-frame class; shipped off-diagonals (0.025 / 0.0125) |

Fixture identity: `receipts/01_fixture_hashes.txt` (e.g. rotcoupon groups sha256
`f2eef2df…aa09d2`). Both exports are genuine `export_status:"complete"` outputs.

## 3. Verdict matrix — invariant × fixture × layer

192 scored rows (receipts/03): **150 PASS_EXACT / 42 DROP / 0 DIFF**, identical for
both fixtures (2 bodies each; per-body rows ×4 bodies total). Tolerance: exact `==`
on parsed values, elementwise; every PASS row is bit-level (`float.hex` recorded on
any mismatch — none occurred). The full sub-field matrix is in
`receipts/03_verdict_matrix.{csv,json}`; aggregate:

| invariant (sub-fields) | L-WRITE | L-PARSE | L-SUMMARY |
|---|---|---|---|
| **I1 tensor** — all 9 entries, unit, 3 contract flags | — | **PASS ×20** (parsed == emitted object) | **PASS ×20** (all 9 entries exact incl. off-diagonals) |
| **I2 COM** — value[3], unit, coordinate_frame | — | **PASS ×12** | **PASS ×12** |
| **I3 frames** — body_frame (5 fields), tensor frame fields, mass/volume frame fields | — | **PASS ×36** | **8 PASS / 36 DROP** |
| **I4 per-cell provenance** — cell_id, owner, region, material, density, source, conditions | — | **PASS ×4** | **4 DROP** (all rows) |
| **I5 admission** — status + sha256, top + per-body | — | top sha **PASS ×2** | **10 PASS / 2 DROP** (top-level sha256 dropped) |
| **I6 readiness** — `dynamics_readiness_claimed` false | — | **PASS ×2** (report) | **PASS ×2** (pinned false) |
| canonical transport (report text, parse roundtrip, reader-output re-read) | **PASS ×2** | **PASS ×2** (canonical_json(parsed) == emitted canonical string) | L-REREAD **PASS ×2** |

Per-body summary survivors (PASS): the 9 tensor entries bit-exact (off-diagonals
included — e.g. body-R `Ixy = 0x1.564dfb84708b7p-3` survives parse→summary unchanged),
tensor `coordinate_frame`/`basis` + the three flags, COM value/unit/frame,
`admission_status` + `admission_report_sha256` **per body**, `owned_cell_ids`,
`unassigned_cell_ids`, `input_hashes` (exact; addendum 09), `mass_kg` (exact value;
×4 bodies), readiness pinned false. **No DIFF anywhere: nothing that survived came
through altered — the finding is purely about what is absent.**

Off-diagonal observation (P3, receipt 07): body-R (rotated) 9/9 entries nonzero,
6/6 off-diagonals nonzero and pairwise-equal (symmetric); body-S 9/9 nonzero —
correction recorded in §5: the right-tet domain tensor is already off-diagonal
about its COM, and body-R's values differ from body-S's, evidencing the rotation mix.

## 4. The fired falsifier (F-B3-2), classified

Per prereg taxonomy. The 42 DROPs decompose as:

1. **DEFECT-CLASS (contract-contradicting information loss; U7-sibling, defect/change queue — NOT fixed here, tools/ read-only):**
   - `cell_provenance` — 4/4 bodies. Contract line 28: *"travels with the body;
     **never summarized away**"*; CON-12: *"stripping provenance voids the
     contract"*. A summary-built consumer cannot satisfy CON-8 (ownership verbatim
     from `cell_provenance`).
   - `material_mass_source_provenance` — 4/4 bodies (receipt 09 addendum: present in
     every report body, absent from every summary body). CON-12 names it as the
     other half of the provenance pair.
   - `body_frame` (frame_id, handedness, coordinate_unit, rotation, origin_m) —
     4/4 bodies, no surrogate key anywhere in the summary. Contract line 27 lists it
     as authoritative; CON-10's convention (`x_domain = R·x_body + origin_m`) is
     unverifiable from the summary alone.
   - `volume` — value/unit/frame-invariance dropped entirely (§1 line 24).
2. **UNPROMISED (structural drops with the information still reachable; decision request):**
   - tensor `frame_id` — dropped as a key, but the summary's `coordinate_frame`
     carries the identical string (×4 bodies, receipt 09). No information loss; the
     summary is simply not §1-shaped.
   - `mass` struct flattening to `mass_kg` — value bit-exact ×4, but `unit:"kg"` and
     `frame_invariant:true` flags gone.
   - top-level `admission_report_sha256` — dropped; per-body sha256 survives, so
     CON-13 verification remains possible per body, but the report-level binding is
     gone from the summary.
   - `admission_reason_codes`, `all_supplied_cells_assigned`, `reason_codes`,
     `mass_authority`, `validation_only`, `production_wired`,
     `anatomical_completeness_certified` (+ admission twin),
     `source_effective_segment_payloads_consumed`, `surface_mass_overlay_generated`
     — the safety-flag class is not surfaced (empty/vacuous in these complete
     fixtures, so no information lost *here*, but a `partial`-class consumer of the
     summary would not see them).
3. **RECURRENCE (banked elsewhere, not claimed new):** top-level `unassigned_cells`
   rows dropped — this is M09's CON-7 finding recurring on complete reports;
   `unassigned_cell_ids` (the id list) IS preserved exactly.

**Disposition:** same lane as M09's U7 — a reader-improvement candidate for the
defect/change queue with this receipt as evidence (exclusive-ownership fix task;
B3 executes no tools/ change). Decision request **MV-B3-1**: should
`summarize_export_report` be §1-complete (or declare itself a display projection
that MUST NOT be used as a consumption source)? Until adjudicated, the conservative
reading is M10's: only the raw report is a consumption document (M10's R-rules read
the raw report, so the campaign's static consumer is unaffected).

## 5. Predictions vs measurements (receipt 05)

| prediction | disposition |
|---|---|
| P1 parse layer exact (both fixtures) | **SUPPORTED** — 94/94 L-PARSE rows + canonical text identity |
| P2 summary projection map | **PARTIALLY REFUTED** — all predicted DROPs confirmed and all predicted survivors confirmed EXCEPT tensor `frame_id`: predicted to survive, measured DROP (value still preserved via `coordinate_frame`). Also P2 named `material_mass_source_provenance` as a drop while the frozen I4 sub-field list did not — measured post-run in receipt 09, frozen matrix untouched |
| P3 rotated fixture all-9-nonzero | **SUPPORTED** for body-R; body-S sub-claim corrected (domain tensor already off-diagonal; identity rotation preserves, rotation mixes) |
| P4 CRLF smudge, canonical identity | **SUPPORTED** — 4/4 stages: 1 CRLF pair (trailing newline), normalized bytes == canonical string |
| P5 reader output re-parses to itself | **SUPPORTED** — L-REREAD PASS ×2 |

**Falsifier ledger: F-B3-1 held · F-B3-2 FIRED (42 rows, classified §4) · F-B3-3 held · F-B3-4 held.**

## 6. Byte-layer findings (B4-law compliant)

Per the known context, byte-layer verdicts use the exporter's/reader's own
`canonical_json`, never raw file bytes (receipt 04):
- All 4 CLI stages (2 fixtures × exporter+reader): raw piped stdout carries exactly
  1 CRLF pair (the single trailing `\n` smudged by the Windows pipe); newline-
  normalized bytes are IDENTICAL to the canonical string. This is B4's smudge layer
  observed at the CLI boundary — EXPECTED, no new defect.
- Parse stability: `canonical_json(read_json_file(report.json))` == the exporter's
  canonical output string, both fixtures (F-B3-4 held) — the writer and the reader's
  parser agree bit-for-bit through the disk round-trip, including on my authored
  fixture's non-trivial trig floats. The reader's own output likewise re-parses to
  an identical canonical string.
- The gap M09 banked (U7) is therefore NOT a byte/parse problem — the bytes survive
  perfectly; the loss is entirely in the summary projection of §6 of the reader.

## 7. Relation to M09's U7 finding (CON-4/6/7) — adjacent, not duplicating

M09 measured the reader's **summary vs diagnostics on `blocked`/`refused` reports**:
`blocking_cell_ids`/`blocking_assignment_statuses`/`admission_reason_codes` (CON-4),
top-level `reason_codes`/`detail` (CON-6), per-cell `unassigned_cells` rows (CON-7).
B3 measures the **`complete`/`exported` path against the §1 authoritative fields** —
a disjoint field set (per-cell provenance, material provenance, body_frame, volume,
mass invariance flags, top-level admission binding, the non-claim flag class).
Same mechanism (the summary is a hand-built projection, not a §1 view), different
content class, complementary status classes; together they bound the gap: **the
reader's summary is faithful exactly where it flattens numerics (tensor/COM/mass
values, bit-exact) and drops contract content everywhere else.** Only the CON-7
`unassigned_cells` row-drop overlaps, and it is marked recurrence, not a new claim.

## 8. Incidents (preserved per campaign law; receipt 08)

1. Fixture-generator v1 crash: `abs()` over an unsummed generator (TypeError).
2. Fixture-generator v1 path bug: `parents[1]` instead of `parents[2]` for `tools/`.
3. **First execution produced a genuine BLOCKED report** (`bad_schema` →
   `reconstructed_mass_admission_required`, both bodies `not_exported`): B3 authored
   a manifest-style partition. Diagnosed via the admission adapter's detail
   (`partition.cells[0]: unknown fields ['component_id']`), fixed in the GENERATOR
   only. The blocked report is preserved verbatim
   (`receipts/08_blocked_first_attempt.report.json`) — incidentally a genuine
   exporter refusal document.
4. Runner v1 crashed on that blocked body (`mass_properties=None`); rewritten
   table-driven; non-exported bodies record N_A instead of crashing.
5. Reproduction-driver v1 used a stripped env (exit=1); re-executed normally.

**Reproduction (receipt 10):** second full execution under the normal environment →
all five verdict receipts byte-identical (e.g. matrix sha256 `e20e765b…cf7504`),
tally 150/42/0 — measurement stable; the stop rule's "no verdict changes" held.

## 9. Integrity paste

```
$ git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- tools Chimera/docs/matter
(empty; exit 0, stdout_bytes=0)
__pycache__ under tools/: 0 dirs, 0 *.pyc
```
Full receipt: `receipts/06_integrity.txt`. tools/ and docs/ untouched; all B3 writes
inside `material_volume_campaign/agents/B3_roundtrip/`.

## 10. Receipts

| file | content |
|---|---|
| `00_prereg_freeze.txt` | prereg freeze hashes/mtimes (before all execution) |
| `01_fixture_hashes.txt` | fixture identity (canonical JSON bytes) |
| `02_run_io/<fixture>/` | exporter/reader stdout bytes, stderr, exit codes |
| `03_verdict_matrix.{csv,json}` | the 192-row invariant × fixture × layer matrix |
| `04_byte_layer.txt` | CRLF/canonical records + findings |
| `05_predictions.json` | P1–P5 dispositions |
| `06_integrity.txt` | integrity paste + worktree context |
| `07_offdiag_observation.json` | nonzero-entry counts + off-diagonal hex |
| `08_fixture_incidents.txt` + `08_blocked_first_attempt.report.json` | incident log + preserved blocked first attempt |
| `09_con12_addendum.json` | CON-12 pair + full key-set diff (logged post-freeze extension) |
| `10_reproduction.txt` | reproduction hash comparison |

Artifacts: `fixtures/rotcoupon/` (authored triple + `report.json` + `summary.json`),
`fixtures/shipped_example/` (copies + outputs), `work/{make_fixtures,run_roundtrip,addendum_con12}.py`.

**Lane verdicted. STOPPING here per the brief: no tools/ changes executed; findings
queued (§4) for coordinator disposition alongside the U7/B8 queue.**
