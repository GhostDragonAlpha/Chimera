# W4 REPORT — append-only erratum: falsifier count rebuilt, coverage claims narrowed, DR-2 executed

**Agent:** W4_erratum · 2026-09-24 · worktree `E:/ChimeraWork/mvc-20260924`
(branch `material-volume-campaign-20260924`, HEAD at W4 start `d1c99335`) · CPU-only ·
no execution runs (receipt reading + cross-checking only) · no git writes (nothing committed).

**Verdict: ACCEPTANCE MET (all five items).** The ERRATUM is appended to
`material_volume_campaign/CAMPAIGN_REPORT.md` as the section
`# ERRATUM (W4 — APPEND-ONLY, 2026-09-24)`; nothing above the append point was edited
(git diff: 81 insertions, 0 deletions, single hunk `@@ -59,0 +60,81 @@`). All 87 quoted
fragments were machine-verified verbatim (whitespace-normalized for receipt line wraps)
against archived receipt copies by `verify_quotes.py` — **87 checked, 0 failures**.

## 1. What was done

1. Brief copied verbatim to `impl/W4_erratum/brief.md` (first action).
2. Read all 18 assigned receipts (`agents/M01…M10, B2a, B3–B7, B7x, B8`) plus M03's
   `ERRATA.md` and the DR-2 target `Chimera/docs/matter/material_volume_export_verification_receipt.md`
   (read-only). B9 is quoted in a clearly-marked scope note (it is in the report's
   "19 agent receipts" count but outside W4's assigned source list; only its own
   falsifier line is quoted).
3. Built the falsifier ledger (E.1 of the ERRATUM): one row per receipt, exact
   falsifier IDs, outcome and classification quoted AS THE RECEIPT STATES THEM.
4. Appended the ERRATUM with the ledger + five corrections (E.2–E.6), each superseding
   its target sentence by reference.
5. Archived statement copies of all quoted receipts under `impl/W4_erratum/receipts/`
   (21 files) and wrote `verify_quotes.py`; ran it to verdict acceptance item 4.

## 2. The rebuilt count (what the receipts support — ledger is the count, no single number)

- **Receipts recording a FIRED falsifier: 4** — M03 (frozen falsifier fired on 7
  quantities; ERRATA: "agent-side anchor derivation errors, NOT exporter defects"),
  M04 (fired once, iteration 2, against the agent's own expectation code; Monte Carlo
  sided with the exporter), B6 (fired on 1 of 13 frozen-bound cells; "Instrument/
  tolerance defect: YES"), B3 (F-B3-2 FIRED, 42 rows — reader summary DEFECT-CLASS,
  genuine, NOT agent-side instrumentation).
- **Two of the original six record NO fire:** B7 — falsifier "HELD"
  ("8 detected / 9 missed / 0 surprises / 0 falsified"); M06 — "falsifier did NOT trip"
  (first-pass CRITICAL-DEFECT = preserved harness artifact F-1).
- **Preserved fire-events the six did not count:** M02's F6 fired spuriously twice
  (C-M02-1, C-M02-2, comparator defects; final outcome "NOT FIRED (after comparator
  corrections)"); M08's three frozen-rule DEFECT-CANDIDATEs (S0/S1 derivation omission,
  E7 invalid rung, E1f harness bug — all diagnosed agent-side, verdicts preserved);
  and pre-campaign V3-F in the exporter verification receipt (M-1a + C-5).

## 3. The corrections (all in the ERRATUM, each superseding by reference)

- **E.2 (correction 1):** supersedes §3's "Falsifiers fired: 6." sentence — wrong on
  both claims (two of its six held/not-tripped; one genuine fire is not instrumentation).
- **E.3 (correction 2):** narrows "Zero exporter implementation defects." /
  "**Zero exporter defects.**" to *none found in the tested scopes* (synthetic coupons
  and malformed-input matrices; M08: "no anatomical mesh is tested"; receipt U10),
  and distinguishes READER defect classes (B7-M13/F6 uncaught ValueError path; B3
  F-B3-2 summary drops; M09/B2a CON-4/6/7 thinning — recorded, not fixed, tools/
  read-only) from CAMPAIGN-TOOL defects (B2a D1/D2/D3, fixed failing-first by B8,
  17/17, outputs byte-identical) from the EXPORTER-CLI EXIT-CLASS itemization
  (M06 D-1: E03/G10 — "NOT mass leakage", decision-requested). No producer
  value-computation defect found in any tested scope.
- **E.4 (correction 3):** narrows the §2 row's "closes 4/9 measured consumption-time
  gaps": M10 R4 = "presence, 64-lowercase-hex, root↔body consistency on `complete`,
  optional recomputation against a supplied admission document" — it does NOT recompute
  `manifest_sha256`/`partition_sha256`/`body_groups_sha256` (B7 F5: digests "copied
  through unverified at consumption"; B7x: uniform tamper passes R4 as deployed) and
  does NOT validate mass values ("the hash binds the admission *document*, not the
  report's mass values"). Full source-bound verification is W1's separate work
  (`impl/W1_source_verify`, DISPATCHED/in flight per TASK_BOARD.md).
- **E.5 (correction 4):** replaces the "structurally unclosable" framing with the
  precise limit — a report alone cannot authenticate self-consistent values (B7x:
  "any mutation that keeps every field well-formed and internally consistent is
  indistinguishable from an honest report without reference documents") — while
  recording that trusted source comparison IS possible without running dynamics
  (B7: "A regeneration-diff would have flagged 15/15 report-level mutations"; the
  campaign's exact rational oracles in M02/M03/B5/B6; M10's `--admission-report`
  tamper-refusal path).
- **E.6 (DR-2):** lists the ACTUAL unsupported-status tests — legacy exporter-side
  coverage only ("unsupported authority without mass reads" in
  `material_volume_body_export_checks`; M01: "no legacy test exercises the reader");
  M06 E01 (DOC-CONFIRMED) + E03/G10 (exit-signal defects D-1); M09 T5 (+T10 exit pins);
  B2a exit-code reproduction; M10 R2 REJECTs `unsupported` — each row scoped to exactly
  what its receipt names; no blanket coverage claim.

## 4. Acceptance verdicts

1. **Complete falsifier ledger with per-receipt citations — MET** (E.1: 18 rows + B9
   scope note; every row cites its receipt path).
2. **All four corrections + DR-2 in the ERRATUM, each superseding by reference — MET**
   (E.2–E.6; originals untouched above the append point).
3. **Zero edits above the append point — MET.** Proof (pasted):
   ```
   $ git diff --stat -- material_volume_campaign/CAMPAIGN_REPORT.md
    material_volume_campaign/CAMPAIGN_REPORT.md | 81 +++++++++++++++++++++++++++++
    1 file changed, 81 insertions(+)
   $ git diff -U0 -- material_volume_campaign/CAMPAIGN_REPORT.md | grep "^@@"
   @@ -59,0 +60,81 @@
   $ git diff -- material_volume_campaign/CAMPAIGN_REPORT.md | grep -c "^-[^-]"
   0
   ```
4. **Every quote verified — MET.** `python verify_quotes.py` →
   `87 quotes checked, 0 failures` (whitespace-normalized match against
   `receipts/` copies; three initial mismatches were fixed to byte-exact receipt
   fragments before verdicting: M01 double-quoted "finding candidate", B7's
   "**HELD.**" bold markers, B7x's "**R4(d)'s …**" bold heading).
5. **Integrity: changes ONLY in CAMPAIGN_REPORT.md (append) + W4 dir — MET.**
   ```
   $ git status --porcelain   (post-work)
    M material_volume_campaign/CAMPAIGN_REPORT.md
    M tools/material_volume_export_proof_verify.py
   ?? material_volume_campaign/impl/
   ```
   The `tools/material_volume_export_proof_verify.py` modification is **NOT W4's**:
   W4's pre-edit snapshot (`git status --porcelain` at HEAD `d1c99335`, before the
   append) showed only `?? material_volume_campaign/impl/`; that file is W1's
   ownership ("W1 … owns tools/material_volume_export_proof_verify.py", TASK_BOARD.md)
   and W1 is DISPATCHED/in flight — concurrent parallel-agent work observed mid-task
   (61 insertions, characterized read-only via `git diff --stat`). W4 wrote nothing
   outside `CAMPAIGN_REPORT.md` (append) and `impl/W4_erratum/`.

## 5. Files (all under `impl/W4_erratum/` unless noted)

- `brief.md` — task brief, verbatim (first action)
- `report.md` — this report
- `verify_quotes.py` — machine quote verification (rerunnable)
- `receipts/` — 21 archived statement copies of every quoted receipt (M01–M10 reports,
  M03 ERRATA, B2a, B3, B4, B5, B6, B7, B7x, B8 fixes.md, B9, exporter verification receipt)
- Appended (owned): `material_volume_campaign/CAMPAIGN_REPORT.md` — ERRATUM section only

STOP — acceptance verdicted.
