# MATERIAL-VOLUME CAMPAIGN — END-OF-CAMPAIGN CONSOLIDATION (B10)

**Campaign:** complete the material-volume exporter's outstanding static validation and build a tested static consumer. 24-hour continuous execution.
**Outcome: EVERY AUTHORIZED TASK COMPLETE.** 19 agent receipts (M01–M10, B2a, B3–B7, B8, B9, B7x), every one coordinator-verified by fresh re-run before integration. Zero exporter implementation defects. Two campaign-built tools, independently reviewed and defect-fixed. Eleven decision requests queued for the architect.

## 1. Integrated revisions and artifact identities

- **Campaign branch:** `material-volume-campaign-20260924` (worktree `E:/ChimeraWork/mvc-20260924`), base = exporter tip `3db8bc4e`; frozen proof revision `1af0bbde` audited without substitution. Commit chain `0c5cbbf0 … (this commit)`; every integration checkpointed (see RECOVERY.md T0–T19).
- **Untouched, as ordered:** `tools/` and `Chimera/docs/matter/` — porcelain-clean at every receipt (415-file read-only proofs in M09/B8/B2a receipts). The exporter stack itself was never modified; all fixes landed in campaign-owned code.
- **Campaign tools (in-tree, promotion = architect's call):** `agents/M09_diagnostic/material_volume_diagnostic.py` (17/17 after B8 fixes) and `agents/M10_validator/rigid_body_mass_consumption_validator.py` (71/71).

## 2. Independently verified capabilities (the exporter's validation thesis, now proven)

| capability | receipt | headline number |
|---|---|---|
| independent reproduction of frozen proofs | M01 | SI 5/5, FC 8/8, verify 7/7 ×2; 66/66 identities re-derived |
| multi-cell mixed-density grouping | M02 | 142/142; off-diagonals preserved, exact-algebra oracle |
| non-unit scale_to_m | M03 | laws 39/39 exact; origin_m affine-not-scaled (1.2e-16) |
| rigid-motion covariance | M04 | both paths green; Monte-Carlo ground truth confirms |
| input-order invariance | M05 | physical bit-exact 5/5; byte layer licensed-only; U6 closed |
| malformed-input refusal discipline | M06 | 62 cases, 95 named refusals, 0 critical |
| ownership/status propagation | M07 | 64/64; hash binding independently recomputed |
| numerical robustness | M08 | 45/45 rungs; offset-invariant to 1e15; gates at declared tolerance |
| subdivision conservation | B5 | 44/44 + 60/60; rounding-scale across 128× cell growth |
| tensor physics | B6 | symmetry bit-exact; recombination exactly 0.0 relative |
| reproducibility law | B4 | blob OID + LF-canonical SHA-256 = portable identity; 182 comparisons, 0 unexpected |
| documentation truth | B9 | 54 examples, 0 broken; DR-1 digest construction reproduced |
| static consumption validation | M10 + B7x | R0–R16 (71/71); closes 4/9 measured consumption-time gaps |
| diagnostic CLI | M09 + B2a + B8 | reviewed ACCEPT-WITH-NOTES → 3 defects fixed failing-first → 17/17 |

## 3. Fired falsifiers, defects fixed, unresolved findings

- **Falsifiers fired: 6.** Every one traced to AGENT-SIDE instrumentation and preserved with its diagnostic trail: M03 (own anchor slips, ERRATA), M04 (own comparator trace-term error, MC sided with exporter), B6 (own L²-cancellation tolerance), B7 (falsifier HELD — nothing predicted-detectable passed), M06 (first-pass FALSE critical diagnosed + preserved), B3 (summary-layer drops = a real FINDING, not a defect of instrumentation). **Zero exporter defects.**
- **Defects fixed:** B8 fixed M09-CLI D1/D2/D3 (hostile-input only; failing-tests-first; genuine outputs byte-identical pre/post, SHA-256 on record).
- **Unresolved (honest residuals):** the wrong-but-consistent VALUE class passes every consumption-time check (B7/B7x — needs a regeneration-diff or value oracle: architectural); the reader SUMMARY projection drops contract-mandated fields (M09's CON-4/6/7 diagnostics on blocked/refused; B3's CON-12 provenance + body_frame + top hash on complete reports — one mechanism, disjoint field sets); `unsupported` status exports at exit 0 carrying its named refusal (M06 E03/G10 — exit-class question).

## 4. Remaining coverage gaps and architectural decisions (the decision-request ledger)

1. **MV-VALUE (from B7+B7x):** consumption-time value oracle — accept the residual, mandate regeneration-diff, or build an oracle. The single most consequential open item.
2. **MV-B3-1 / U7-family (from B3+M09):** the reader summary's projection contract — specify which fields a summary must carry (CON-4/6/7/12) or bless the raw-mapping path the CLI uses.
3. **MV-O1 (M07):** blocked-group body-level hash binds the reduced document; all other paths bind the full report — doc silent.
4. **MV-B4-1 (B4):** canonize or declare pretty-form for the 16 non-report JSONs.
5. **MV-O2/O3 (M05):** promise physical invariance and output array order explicitly (currently implemented but unpromised).
6. **M06-H04:** matrix-erratum exit class for named-refusal-via-reader (exit 2 vs 1).
7. **DR-2 (M01):** the receipt's "legacy tests cover unsupported" parenthetical is imprecise.
8. **M10's five contract spots** (readiness, partial, recombination, lineage, source-effective masses) — strictest reading implemented, Astra owns the relaxations.
9. **Promotions:** the two campaign tools into `tools/` (or their long-term home).
10. **M01-F1:** the verify battery's 7/7 is checkout-materialization-dependent — decide whether the battery should pin blob-form inputs (B4's law provides the mechanism).
11. **B7-M13:** ragged-tensor corruption escapes as a numpy traceback, not a named refusal.

## 5. Exact recovery instructions

- The board (`TASK_BOARD.md`) is the live index: every row carries status, verdict, and receipt path. RECOVERY.md T0–T19 is the checkpoint log.
- Re-run any receipt: each agent dir is self-contained (brief → prereg → scripts → receipts); all code runs from `work/` module copies with `PYTHONDONTWRITEBYTECODE=1`; nothing depends on session state.
- Worktree `E:/ChimeraWork/mvc-20260924` (branch `material-volume-campaign-20260924`) holds everything committed; the six dirty legacy trees elsewhere on the machine remain untouched per the corrected cleanup law; the 11 live worktree registrations were audited this pass (no removals — all referenced or locked or deliberately spared).
- The exporter's own artifacts (frozen `1af0bbde`, tip `3db8bc4e`) are byte-stable on their branch; blob-form identity per B4's law: `git cat-file blob` + LF-canonical SHA-256.
- Parallel campaign context: the forearm anatomy campaign is COMPLETE and decision-blocked (its receipt: `E:/PythonChimera/forearm_package/USTR_DIAGNOSTIC_RECEIPT.md`, branch `forearm-package-20260924` @ `b04a3acd`).

**Operational notes for the record:** five transient provider `[1302]` failures, all recovered by probe-then-serialized-retry with saved briefs (the honest-resume pattern held every time: brief survival checks, reconstructions marked, post-freeze edits audited); spawn volleys identified as the trigger — stagger discipline adopted; two doc-lint false-positives on data receipts committed via the hook's own `--no-verify` branch with logged explanations.
