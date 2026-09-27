# MAT2-A02 REPORT — reconciliation of the merged U-STR / radius-consequence validation

Attempt `ce71ec9ca3d74978bd62f99a5c0fcdfe`, arrival
`arrival-138570e4c25445f88c57b28d25e29d7a`, card MAT2-A02 (planning id A02),
criteria sha256 `c5d0e02ef376f01afcab78ee81e087f3b28dd9c7f29aef1bd0375c9ac2dd7bdf`.
Candidate base: `6af853ad3be90e2f9564cb7f908fd4a202f9241c` (merged line
`origin/astra/gait-capture` tip, = MAT2-A01's merge, PR #211). PREREGISTRATION
frozen at `dc2906816b0d435042010b38fb1a9db6f7407810` (committed alone, BEFORE the
probe script or any receipt existed). **No new measurement was made; this attempt
is a reconciliation of already-merged, lead-accepted evidence, per
`MATERIAL_PLAN_ADOPTION.md` ("Old evidence may satisfy unchanged clauses after
checking exact inputs, dependencies and validity; submit that reconciliation as
the new card's contribution instead of reimplementing known-good code").**

## done_when

> Radioulnar definition, independent evidence, B4 result and before/after radius
> mapping are presented

**Outcome: all four clauses are PRESENTED by the merged ONT-A02 record
(`outcome = PRESENTED_AND_VERIFIED`, 57/57 re-measurement checks), and this
attempt re-verified that record in scope. Scoped verification 6/6 probes PASS
(`evidence/reconciliation_receipt.json`, `outcome: RECONCILED`), first run, no
probe corrections.**

## Reconcile-first: clause identity (why reuse instead of reimplement)

- MAT2-A02 and archived ONT-A02 share `definition_raw_sha256`
  `57ded6eb2f2cc6aa914d6f68c8efb55b215790fc7a9d0baa5dfd2c49fd1465c1`, and the whole
  projected `ontology_qualification.task` object (done_when, observation
  "U-ANA rejected; U-STR provisional; radius supersession not authorized",
  verification_profile with all 16 camera_required_fields, views, layers,
  falsifier, C01/C16, catalog_refs) digests identically
  (`f804c9151fda7d3c47e3ac662bdeb8cf5b5f754f188c18b1d2df93be2a2f61eb`): a
  zero-line task diff (registry read-only, scope archive `01ea5cdd…`). Only the
  envelope changed: card id, scope sha (`01ea5cdd…` → `cb5475f8…`), depends_on
  (`ONT-A01` → `MAT2-A01`).
- Criteria pin honored: `digest(spec)` of the live card recomputes to `c5d0e02e…`
  == registry == attempt value. Convention cross-check: the same computation
  reproduces MAT2-A01's recorded projected-task digest `5f121837…` exactly.

## What is presented (by the merged record, byte-bound at this base)

1. **Radioulnar definition** — the U-STR relationship as two kinematic anchors
   (ulna body_origin ↔ `elbow_R`, gap 0.0; radius body_origin ↔ `elbow_R` +
   5.1158 mm along unit(elbow→wrist)); authored offset `(0.0004, −0.011503,
   0.019999)` m = 23.0746 mm, decomposed 14.324 axial + 18.088 lateral +
   0.301 posterior mm at 51.63° to the 305.7922 mm elbow→hand axis (7.5459 %);
   binding reading: a KINEMATIC JOINT-FRAME offset, not a bone-landmark distance
   and not a radial-head position. Re-pinned exactly (probe PR-3, N1.*, 12 checks).
2. **Independent evidence** — three applicable primary human sources (London 1981;
   Brownhill 2009; Hollister 1994) place the radial head at ≈ 0 % ± 1 % of forearm
   length, outside the frozen 4–12 % band by ≥ 3.0 points (N4.band_margin 3.0):
   the anatomical reading of the re-anchoring is refuted; in-model O1 roll
   witnesses (ECU-P2 63.612…°, ANC-P2 17.552…°, TRIlat-P5 0.1535…°) unanimous
   NO-FLIP and C1's independent 10/10 ulna landmark set.
3. **B4 result** — the authorized isolated U-STR B4 diagnostic on the frozen
   candidate (U-STR + O1-resolved roll): N3.gate_cells `10 PASS`, T6
   `{PASS, banned 0}`, receipts 08/10 ok — a SOURCE-KINEMATIC FIDELITY statement
   only; R1's refutation retained, not relabeled.
4. **Before/after radius mapping (closed form, nothing executed)** — radius P
   moves `elbow_R` → `ulna.P_d` (+5.115804490107078 mm); span
   64.74489854186721 → 59.62909405176015 mm; uniform scale
   0.22170679566544982 → 0.20418868001006546 (−7.901478889180636 %); det = s³
   0.008513242115903161; G unchanged (max diff 2.220446049250313e−16); 16+16 site
   globals recomputed, max displacement 4.950983466166482 mm (`BICshort-P6`) /
   4.948423135921825 mm (`BIClong_l-P9`); source locals untouched; mechanism
   first-child shared-joint closure (`compiler.py:399-423`, `JOINT_EPS = 1e-9`).

**Radius supersession NOT authorized and NOT executed** — the card observation
stands. ONT-A03 (merged PR #187 @ `4aecbc9e`) carries the staged supersession
record on the source-kinematic basis; its approval act remains a lead
review/merge decision on that exact head. The old radius record and every failed
alternative remain preserved.

## Scoped verification (the frozen probes PR-1..PR-6, all PASS, first run)

```
cd <attempt checkout>/tools/monkey_campaign/contributions/MAT2-A02
PYTHONDONTWRITEBYTECODE=1 python -B verify_reconciliation.py   [exit 0]
  PASS PR-1: files=35 (frozen 35) identical blob sha256 across
             dadfda28 -> 970ffe1a -> 4aecbc9e -> 6af853ad
  PASS PR-2: suite exit=0; final count line='106/106 tests PASS'
             (frozen '106/106 tests PASS'); FAIL lines=0; cpu-only python -B
  PASS PR-3: outcome PRESENTED_AND_VERIFIED, 57/57 PASS (census
             {"N0": 4, "N1": 12, "N2": 30, "N3": 4, "N4": 7}), all 22 exact
             value pins + 9 structural pins reproduced, task_id A02 envelope
  PASS PR-4: task_id=A02 envelope, 6 rows = V1/V2/V3 x diagnostic/clean, all 16
             contract camera fields located on every row, PNG bytes bound
             (a728b16a…), qualification receipt binds all 4 evidence digests,
             canonical validate_manifest (base blob, play-checkout copy
             byte-identical): structurally_valid=True view_count=6;
             visual_gate.verify(task_id A02 contract): structurally_valid=True
             view_count=6
  PASS PR-5: MAT2-A01 state=DONE merged via PR #211 merge_commit=6af853ad ==
             candidate base (winner ontology_qualification task_id=A01); freeze
             commit dc290681 (parent 6af853ad, ancestor-of-HEAD=True, files=
             ['PREREGISTRATION.md']); HEAD carries contribution dir=True
  PASS PR-6: pristine passes=True; tampered (1 token:
             outcome->TAMPERED_RECORD) passes=False
outcome: RECONCILED (6/6 probes pass)
```

Final-state determinism: from the committed candidate, a second probe run is
byte-identical (`evidence/reconciliation_receipt.json` sha256 equal across runs,
outcome RECONCILED 6/6 both times).

All probes read only: git objects of this attempt checkout, the registry
(`agent_slots.sqlite3`, opened read-only), and a TEMP replica extracted under the
attempt workspace's `probe_tmp/` (outside the candidate tree). The replica suite
read two pinned external inputs from the read-only play checkout
(`monkey_birth.bin` 661076 B, `monkey_joints.bin` 296589 B; hash-pinned inside
the receipt under test) and imported `visual_capture`/`visual_gate` support
modules from the play checkout (visual_capture byte-identical to the base blob;
read-only imports, `python -B`, no bytecode writes). CPU-only, offline.

## Profile class delivery (anatomy / visible_static)

The `visible_static` class is delivered bound to committed bytes with the
CONTRACT task_id envelope: `capture_manifest.json` (`schema
chimera.visual_capture_manifest.v1`, `task_id "A02"`, `profile_id "anatomy"`)
with 6 rows = V1/V2/V3 × {diagnostic, clean}, all 16 contract camera fields
locatable on every row, diagnostic rows `mixed` occlusion / clean rows
`depth_tested` with honestly-empty layers/labels; `capture_sheet.png` bytes ==
`context.capture_sha256` == `manifest.capture_sha256` == merged qualification
receipt `evidence.visual.raw_sha256` (`a728b16a…`); the merged qualification
receipt (`chimera.ont_a02_qualification.v1`, task_id A02, done_when_verified,
profile_verified) binds numerical `2aa382a1…`, source `60241502…`, camera
`6a7957d3…` — each equal to the actual merged bytes. Canonical
`validate_manifest` and `visual_gate.verify` both structurally valid, 6 views.
No new capture was produced: the merged, review-accepted capture IS the visual
evidence. The merged capture's honesty label stands (deterministic CPU software
raster, NOT native engine frames); independent image/physics review remains
mandatory.

## What this card does not claim

- No new measurement, no re-run of the B4 gate, no production radius supersession,
  no hand fit, no training-body change, no fit search, no moment-arm/utility
  computation, no runtime/native/GPU evidence.
- The merged record's honesty items stay open exactly where they were: R1's
  refutation stands (the 7.9015 % target anchor preserves the source author's
  kinematic convention and carries NO primary-anatomical support); the A03
  anatomical decision remains where I7's DR-B left it; the target palm sign
  question belongs to the A01/A04 lane; MAT2-A01's AMBIGUITY_RECORDED arm is
  intact and not relabeled.
- If any falsifier had fired, this attempt would have stopped and reported; all
  six probes passed on the first run (`probe_corrections: []`).

## Evidence index (sha256)

| artifact | sha256 |
|---|---|
| `PREREGISTRATION.md` (freeze commit `dc290681`) | `0b3babf49a703b4de5b294e942a98fe8dd90b737f9556b433aa5479c5446ccdb` |
| `verify_reconciliation.py` | `a936c63a89d95719dca9b8998a56fd542ad7e9c515dbc4588afb48a16345c22d` |
| `reconcile_clause_map.json` | see `evidence/qualification_receipt.json` |
| `evidence/reconciliation_receipt.json` | `334d5c45e037a88c5217324ad059f07dbb94cc62412e57ff64a54d30e2b6f1e9` |
| `evidence/qualification_receipt.json` | full digests for every entry |

Merged evidence byte pins (verified identical at all four anchors, PR-1):
`numerical_receipt.json` `2aa382a15c0f005ef421fb0fa967b912486e03bdac2f75b9a50529d3ab90cce1`,
`EXTRACTION.json` `60241502ebe8f7679f4dd42f69a498a547417aa0c2342cf7571940e53f121089`,
`capture_sheet.png` `a728b16a6c0fb87170c3ce2dd6c1824bf7a9a353e4c304a5cf41966b5d4462fa`,
`capture_manifest.json` `6a7957d3d4c9aa4d0493f2ad984768bce182232f77a7909067926f7a0e8c0f6d`.

## What remains for the reviewer (and what this card does not claim)

1. **Independent review of the exact published head** — reproduce the probe run,
   inspect the merged capture pixels against the declared subjects, and **fill
   `evidence.independent_review`**: the entry in `qualification_receipt.json` is
   explicitly pending with the zero placeholder (the same shape the accepted
   A01/A02 receipts carried); the reviewer supplies the real receipt path + raw
   sha256 and pins `head_sha` to the reviewed head.
2. This card presents and reconciles; it does **not** authorize the radius
   supersession, does not execute the ONT-A03 staged mapping, and does not close
   A03.
3. No native runtime or human acceptance is claimed: the subject is anatomy
   evidence records, captured with component evidence, honestly labeled as such.
