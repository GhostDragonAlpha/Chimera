# MATERIAL-VOLUME CAMPAIGN — RECOVERY RECORD (append-only)

## CHECKPOINT T0 (2026-09-24) — campaign opened

**Setup verified:** worktree E:/ChimeraWork/mvc-20260924 on branch material-volume-campaign-20260924 (base = exporter tip 3db8bc4e, clean checkout 5118 files); frozen proof rev 1af0bbde identified; 27 material-volume files in tools/; docs incl. 59/66 verification receipt + contract v0.9 (5 Astra decisions open); prior export worktree already cleaned by its own lane (branch carries everything).
**Dispatched at T0:** M01–M10 (ten background agents, exclusive dirs under material_volume_campaign/agents/).
**Parallel context:** the forearm anatomy campaign's wave-4 agents (O1/O2/R1) run concurrently in E:/PythonChimera (separate campaign, separate branch) — integrate their notifications as they land; no resource conflict (all CPU-light).
**Next:** collect M-receipts as they land -> verify -> integrate in small batches -> refill from backlog B1-B10 -> checkpoint each pass. Worktree audit each integration pass.

## CHECKPOINT T1 — M09 integrated (first mv-campaign receipt)

**Verified:** M09 suite re-run by coordinator (11/11 PASS, 3.6s); read-only proof reproduced (415 files, 0 changed); integrity clean. Implementation on the reader's public API (read_json_file, summarize_export_report, canonical_json); exit codes {0,2,4}; readiness false in all outputs; exit-4 alarm never fired.
**Finding banked (U7):** reader correct on blocked/refused; summary drops CON-4/6/7 diagnostics; CLI passes through. Coordinator disposition: candidate reader-improvement (a tools/ change) goes to the defect/change queue with M09's receipts — not executed yet (exclusive-ownership rule).
**Refill:** B2a dispatched (independent non-author review of the M09 CLI).

## CHECKPOINT T1a — M04 transient [1302] failure; probe passed; retry + B2a live
Second transient [1302] (mid-run, M04, ~23 min in; only brief.md written). Probe: PASSED 1.4 s. M04 re-dispatched from saved brief (typo in its context line noted to the agent: 3db4bc4e -> 3db8bc4e). B2a (independent review of M09 CLI, committed 7701d8db) dispatched. Pattern watch: two [1302]s at 13-agent concurrency, both mid-run — if a third lands, serialize retries one-at-a-time and consider holding the count at ~10.

## CHECKPOINT T2 — M07 integrated; M06 third [1302] -> serialized-retry protocol ACTIVE

**Verified:** M07 PASS — coordinator re-ran work/verify_propagation.py: 64/64 checks. Duplicate ownership refused by name; unassigned cells explicit; no status leakage; hash binding == independently recomputed SHA-256 in every evaluated case; C1 twice byte-identical. DECISION REQUEST MV-O1 logged (blocked-group body-level hash binds reduced doc vs full report elsewhere — contract doc silent). Harness incident preserved verbatim (agent-side, fixed, re-run clean).

**Concurrency protocol:** third [1302] (M06, mid-run, at 19 concurrent). SERIALIZED RETRIES now active: one failure-retry in flight at a time; no new backlog spawns until the cluster stops. Fleet at 17 live; M06-retry brings 18.

**Active:** M01-M05, M06-retry(pending), M08, M10, B2a, B3, B4, B5, B6, B7, B9 + anatomy O1/O2/R1.

## CHECKPOINT T3 — M10 integrated (the campaign's static consumer EXISTS)

**Verified:** M10 MET — coordinator re-ran tests/test_validator.py: 71/71 in 0.72s; integrity clean. Rules R0-R16 each cite a contract line; reader used as independent R0 cross-check (readiness hard-false pinned); CLI exits 0/1/2; preservation duty (echo blocking_cell_ids / reason_codes) verified.
**Static limit declared (L2):** a silently-diagonalized tensor with flags intact ACCEPTs static validation — pre-declared in the frozen prereg; mitigation: --admission-report recomputation refuses any non-matching supplied doc.
**Decision requests for Astra (strictest reading):** D1 readiness-claim=reject; D2 partial/unassigned=reject-always; D3 any recombination=reject; D4 any lineage field=reject; D5 source-effective masses terminal.
**M06 retry:** dispatched (resume from partial state: brief/cases.py/fixtures/matrix.md exist).

## CHECKPOINT T4 — M05 integrated

**Verified:** M05 PASS — coordinator re-ran work/compare.py (all 7 runs' input_hashes == canonical hashes of their own fixture triples); integrity clean. Physical layer bit-exact under all 5 permutations; byte layer confined to the licensed input_hashes fields; determinism byte-identical; the receipt's U6 hole (export-report-level order invariance untested) is now tested CLOSED. Decision requests MV-O2 (promise physical invariance explicitly) and MV-O3 (promise output array order) logged; UNPROMISED-OBSERVED: output arrays ID-sorted.
**M06 retry:** dispatched (resume from partial state; reuse-vs-rebuild to be recorded).
**Live fleet:** M01-M04, M06-retry, M08 + B2a, B3, B4, B5, B6, B7, B9 + anatomy O1/O2/R1 = 14 + 3.

## CHECKPOINT T5 — 4th [1302] (B3, died at 5 min — survival times shrinking: 17/23/27 -> 5 min)

**Protocol escalation (within the operator's maximum-continuous directive):** the highest SUSTAINING count, not the highest spawning count, is the maximum. Serialized retries hold (M06-retry is THE active retry; B3's retry queued behind it). No new backlog spawns; the fleet drains by completion toward ~10-12, then refills one-per-completion while watching failure spacing. All in-flight work is resumable from briefs + partial dirs; nothing is lost by a [1302].

## CHECKPOINT T5a — 5th [1302] (B5, 5.5 min — same six-agent spawn burst as B3)

**Diagnosis sharpened:** both casualties were spawned in the same simultaneous 6-agent volley; all longer-running agents survive. The burst, not the steady-state count, triggers the limit. **Standing spawn discipline: stagger new/retry spawns 1-2 at a time, never volleys.** Retry queue: B3, B5 (both behind M06-retry, serialized). Fleet drains by completion; refills staggered.

## CHECKPOINT T6 — M02 integrated (the headline outstanding case CLOSED)

**Verified:** M02 PASS 142/142 — coordinator re-ran derivation/derive_oracle.py (all gates pass; expectations regenerate); integrity clean. Multi-cell mixed-density nontrivial-offset case: exact masses, off-diagonal preservation with correct signs, no invented cross terms on isotropic rotation, whole-partition parallel-axis recombination 5.68e-14, determinism, reader acceptance. Independence triple-anchored (exact algebra / quadrature / published literals) with file-timeline-proven prereg freeze. Agent-side defects preserved (the honest pattern again).

**Fleet:** 10 live (M02 done). Serialized retry queue unchanged: B3, B5 wait for M06-retry. Strict protocol held — no spawn this pass.
