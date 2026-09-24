# B7x — M10 static validator vs B7's nine MISSED mutations

Agent: B7x_validator_probe · 2026-09-24 · worktree `E:/ChimeraWork/mvc-20260924`
(branch `material-volume-campaign-20260924`) · CPU-only · no git writes · all writes
confined to `material_volume_campaign/agents/B7x_validator_probe/`. B7's and M10's
directories and `agents/M09_diagnostic` untouched (integrity paste in §6).

**Question:** does the campaign's own static consumer (M10's
`rigid_body_mass_consumption_validator.py`, rules R0–R16) close the consumption-time
detection gaps B7 measured?

**Answer in one line: 4 of 9 closed (M08, M10, M11, M12-as-frozen), 5 remain open
(M02, M04, M06, M07, M09) — and the five that remain open are exactly the
wrong-but-well-formed value class M10 pre-declared as its static limit (L2).**

## 1. Method (preregistration-gated)

`work/preregistration.md` frozen BEFORE any validator run (sha256
`d22900dda4f318a9…`, hashed into `work/results.json` by the runner): per-row
predicted rule, falsifier, stop rule. The runner (`work/probe_run.py`) staged B7's
frozen fixtures read-only into `fixtures/b7_frozen/`, regenerated all nine mutants
from `fixtures/valid_report.json` per B7's frozen matrix into
`fixtures/regenerated/`, proved **all nine regenerated mutants deep-equal B7's
frozen corpus files** (`regeneration_matches_b7_frozen: true` ×9), and invoked M10's
validator via its CLI with `PYTHONDONTWRITEBYTECODE=1`. Validator sha256
`94c2ee772c4a15db…` — byte-identical to M10's implementation receipt; module never
modified. Baseline sanity: B7's clean report **ACCEPT, exit 0**. One pass; stop rule
met (nine verdicted).

## 2. The 9-row verdict table

| Mutation | Predicted detector (frozen before run) | Actual outcome (exit / rules) | Closes gap |
|---|---|---|---|
| M02 inertia diagonal edit (body-B [0][0]→0.076, symmetric, flags intact) | ACCEPT — residual (L2 class); R9 is form/symmetry/flags only | **ACCEPT, exit 0, no rules violated** (frozen + regenerated) | **N** |
| M04 mass 2.0→2.5 (body-A) | ACCEPT — residual; R6 finite/>0/kg/frame-invariant only, no value oracle | **ACCEPT, exit 0** | **N** |
| M06 COM shift x 0.25→0.75 (body-A) | ACCEPT — residual; R8 shape/unit/frame only | **ACCEPT, exit 0** | **N** |
| M07 density 12→13 in provenance, mass left 2.0 (inconsistent) | ACCEPT — residual; R11 requires density finite >0 only; no density·volume==mass cross-rule | **ACCEPT, exit 0** | **N** |
| M08 dropped `material_mass_source_provenance` (body-A) | REJECT — R11 `source_provenance_missing` (CON-12) | **REJECT, exit 1, R11 source_provenance_missing** | **Y** |
| M09 impostor `mass_owner_id` → `owner-IMPOSTOR` in provenance AND `mass_owner_ids` (consistent rename) | ACCEPT — residual; R11 enforces internal consistency only (non-empty, bijection, no conflicts, set equality — all satisfied); no external ownership reference exists statically | **ACCEPT, exit 0** | **N** |
| M10 root `complete`→`partial`, `unassigned_cell_ids` empty | REJECT — R2 `partial_rejected` (strictest D2), not B7's imagined consistency cross-check | **REJECT, exit 1, R2 partial_rejected** | **Y** |
| M11 `dynamics_readiness_claimed` false→true | REJECT — R12 on the RAW report (reader-only would silently neutralize) | **REJECT, exit 1, R12 ×2 (root flag + recursive claim scan) + R13 safety_flag_not_false** | **Y** |
| M12 body-A `admission_report_sha256` → 64 zeros (root/body-B unchanged) | REJECT — R4 `hash_binding_mismatch` (root↔body consistency, CON-13 tamper signal) | **REJECT, exit 1, R4 hash_binding_mismatch** | **Y (as-frozen)** |

Tally: **5 ACCEPT / 4 REJECT — every outcome matched its prediction; falsifier
held (§4); zero surprises.** Per-row verdict JSON: `receipts/verdict_M*_frozen.json`;
full evidence incl. regenerated-copy runs: `work/results.json`; run log:
`receipts/run_log.txt`.

## 3. Consolidated answer — which B7 gaps M10 closes, which stay open

**CLOSED by M10 at static consumption time:**

- **F2 (M08) — closed.** The report artifact finally has a schema-ish gate for the
  provenance contract: R11 refuses an exported body whose
  `material_mass_source_provenance` is missing (CON-12: stripping provenance voids
  the contract). The reader's looseness no longer matters for this class.
- **F3 (M10) — closed, and more strictly than B7 asked.** B7 asked for a
  partial↔unassigned consistency check; M10 instead rejects `partial` outright
  (R2, strictest D2: silent partial assembly FORBIDDEN). The inverse direction B7
  did not mutate — `complete` with non-empty `unassigned_cell_ids` — is separately
  rejected by R14 (M10 test T-R14a). Both halves of the status-consistency gap are
  covered.
- **F4 (M11) — closed.** The readiness tamper is no longer invisible: the validator
  reads the RAW document, so a tampered `true` is a named REJECT (R12 root flag +
  recursive claim scan; R13 independently flags it as a fixed-v1 safety-flag
  deviation). B7's "silent neutralization" decision request is superseded at the
  static layer.
- **F5 (M12) — closed as-frozen, one residual sub-case (see residual list).** A
  body whose hash diverges from the root binding is a named tamper signal (R4(b)).
  M10 upgraded the digest from inert to checked-for-binding-consistency.

**OPEN — the honest residual for the decision queue (all five ACCEPT, exit 0):**

- **F1 value class survives intact: M02 (tensor diagonal), M04 (mass), M06 (COM),
  M07 (density-vs-mass inconsistency), M09 (self-consistent impostor owner).** This
  is precisely M10's pre-declared static limit L2 generalized: any mutation that
  keeps every field well-formed and internally consistent is indistinguishable from
  an honest report without reference documents. Two nuances worth recording:
  - **M09 is narrowed, not closed:** R11 *does* catch internally inconsistent
    ownership corruption (mass_owner_ids≠provenance owners, conflicting duplicates,
    stripped provenance — M10 tests T-R11a/c/d) — B7's specific fixture was a
    consistent wholesale rename, which passes. The remaining exposure is "a
    coherent liar", not "a sloppy liar".
  - **R4(d)'s recomputation path does not rescue the value class:** the hash binds
    the admission *document*, not the report's mass values — editing body values
    leaves the binding valid. Only a regeneration-diff (B7 measured it would flag
    15/15 report-level mutations) or an independent value oracle closes F1; neither
    exists at consumption. The decision B7 queued stands unchanged.
- **F5 residual sub-case:** a tamper applied UNIFORMLY to root and all body hashes
  (or to `input_hashes`) passes R4's static form/consistency checks; catching it
  requires R4(d) with the admission document actually delivered alongside the
  report (M10 LIMIT 1). If the campaign makes document delivery mandatory, this
  residual closes; as deployed (document optional) it stays open.

## 4. Falsifier verdict

**HELD.** No predicted-REJECT row passed (M08/M10/M11/M12 all REJECT, each naming
its predicted rule); no predicted-ACCEPT row was rejected (all five residuals
ACCEPT with zero rule failures); the baseline ACCEPTed. The only prediction delta
is a superset, not a divergence: M11 was also flagged by R13 (predicted R12 only) —
the same flag enforced a second time under fixed-v1 safety-flag semantics.

## 5. L2-limit cross-check

Fixture `fixtures/regenerated/L2_diagonalized.json` (body-B off-diagonals zeroed,
symmetry and all three tensor flags kept — M10's adversarial A5 shape): **ACCEPT,
exit 0, no rules violated** (`receipts/verdict_L2_diagonalized.json`). Confirms
M10's declared limit holds exactly as preregistered — the diagonalized-tensor class
still ACCEPTs, so M10's report claim is reproducible from B7's corpus baseline.

## 6. Integrity

```
$ git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- tools
(empty)
$ git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- docs
(empty)
$ git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- Chimera/docs
(empty)
$ git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- material_volume_campaign/agents/M10_validator
(empty)
$ git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- material_volume_campaign/agents/B7_faultinjection
(empty)
$ git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- material_volume_campaign/agents/M09_diagnostic
(empty)
```

No `tools/__pycache__` or `M10_validator/__pycache__` exists (bytecode suppression
held). No commits made; no git writes.

## 7. Artifacts

- `brief.md` — task brief, verbatim
- `work/preregistration.md` — predictions + falsifier + stop rule, frozen before the run
- `work/probe_run.py` — preregistration-gated runner (read-only toward B7/M10)
- `work/results.json` — full per-row evidence (frozen + regenerated runs, hashes)
- `fixtures/b7_frozen/` — staged copies of B7's baseline + 9 corrupt fixtures
- `fixtures/regenerated/` — my regeneration of the 9 mutants (all deep-equal B7's) + L2 probe
- `receipts/run_log.txt`, `receipts/verdict_M{02,04,06,07,08,09,10,11,12}_frozen.json`,
  `receipts/verdict_L2_diagonalized.json`
