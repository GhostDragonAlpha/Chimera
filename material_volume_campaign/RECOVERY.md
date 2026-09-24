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

## CHECKPOINT T7 — B7 integrated (the consumption-time gap is MEASURED)

**Verified:** B7 frozen matrix structure confirmed (17 rows + preregistration + predicted_tally, frozen before runs); integrity clean; falsifier HELD (nothing predicted-detectable passed silently).
**Findings banked (F1-F6):** reader = only consumption-time validator; no value oracle (wrong-but-symmetric numbers, mass edits, COM shifts, impostor owner ids all flow through at exit 0); dropped provenance invisible; complete->partial with empty unassigned accepted; readiness tamper neutralized-but-invisible (decision request); admission_report_sha256 + input_hashes inert at consumption; M13 ragged tensor escapes as numpy traceback (named-refusal contract gap).
**Cross-connection:** M10's validator (R0-R16) is the campaign's own static consumer — B7's 9 missed mutations are the perfect adversarial corpus for it. QUEUED as B7x (behind retry queue B3/B5).
**Fleet:** 9 live. Serialized protocol still holds (M06-retry in flight).

## CHECKPOINT T8 — M01 integrated (the frozen foundation REPRODUCES independently)

**Verified:** M01's extraction re-runs clean (coordinator re-ran the SI proof from its git-show blob extraction: 5/5 OK); integrity clean. Frozen 1af0bbde reproduces: SI 5/5, FC 8/8, verify 7/7 (CRLF-materialized) x2; deltas reproduce the results-doc table to the last digit (worst 9.4e-16 <= 1e-12). All 66 receipt identities reproduced independently; independent-reproduction OPEN item CLOSED by this run; proof audit executed with 6 named weak assertions; C-1 adjudicated by independent diff (json-equal), C-2/C-3 confirmed; U1-U10 all real.
**New:** M01-F1 (7/7 is materialization-dependent; raw-LF -> 6/7 at one byte) — connects to B4's three-layer matrix. DR-1 (aggregate digest construction unrecorded), DR-2 (U7 parenthetical imprecise) -> decision queue.
**Fleet:** 8 live (M04-retry, M06-retry, M08, B2a, B4, B6, B9 + O1/O2). Serialized protocol holds.

## CHECKPOINT T9 — B2a integrated (first independent review: ACCEPT-WITH-NOTES)

**Verified:** B2a probes re-run by coordinator (exit-2 collisions confirmed live); M09 claims all reproduced by a non-author; U7 independently verified. M06-retry confirmed ALIVE (fixtures building within the last 20 min) — serialized gate holds.
**Defect queue:** D1 (argparse exit-2 collision with frozen reader-rejected code), D2 (string-row crash in human mode), D3 (per-char mangle of string unassigned_cell_ids) — all hostile-input-only, none reachable from genuine exporter output. B8 (fix + regression tests, exclusive ownership) QUEUED behind retry queue.
**Fleet:** 7 live. Queues: retries B3, B5 -> then B8 -> then B7x.

NOTE (T9a): B2a's snapshot receipts are DATA (415-file sha256+mtime inventories of tools/); doc-lint flags two path-shaped strings inside them (probe_core.h, engine.h) as broken pointers — false positive on data, not documentation. Committed via the hook's --no-verify branch WITH this logged explanation; receipt bytes preserved unmodified (extension rename .json->.json.txt attempted first, lint scans text regardless).

## CHECKPOINT T10 — B4 integrated (the three-layer reproducibility law is written)

**Verified:** B4 verdict matrix re-run by coordinator (182 rows, 0 unexpected); integrity clean. KEY LAW: portable identity = blob OID + SHA-256 over LF-canonical bytes; disk bytes and git-archive extracts are BOTH the smudged CRLF layer (0/37 extract==blob) — reproducibility work must materialize blobs via cat-file/git show. M-1a (C-1) reproduced live to the hex digit; M01-F1's mechanism now fully explained. Run behavior byte-identical across materializations. MV-B4-1 decision request: canonize or declare pretty-form for the 16 non-report JSONs.
**Fleet:** 6 live (M04-retry, M06-retry, M08, B6, B9 + O1/O2). Queues: B3, B5 (retries) -> B8 -> B7x.

NOTE (T10a): B4's work/blob_extract + work/archive_extract (derived full-tools/ materializations, regenerable by the committed work/b4_matrix.py scripts; blob OIDs recorded in receipts/04) were REMOVED before commit to keep the campaign tree receipt-only — the evidence (matrix, verdicts, scripts, hashes) is fully preserved.

## CHECKPOINT T11 — M06 integrated (retry #1 resolved); serialized slot freed -> B3 dispatched

**Verified:** M06 full matrix re-run by coordinator — identical tally (95 NAMED-REFUSAL / 2 DOC-CONFIRMED / 2 SILENT-PASS / 1 WRONG-NAME / 1 EXIT-DEVIATION, 0 critical). Findings D-1/D-2/D-3 banked; E03+G10 silent-passes (unsupported-status exit class) added to the B8 fix queue. The resumed session's audit chain (post-freeze edit caught+re-frozen; false critical preserved; harness defects repaired) is the honest-failure discipline working under crash-recovery conditions.
**Serialized slot freed: B3 retry dispatched (single staggered spawn).**

## CHECKPOINT T12 — M08 integrated (the conditioning map is complete)

**Verified:** M08 ladder re-run by coordinator (45 rungs; E7 defect-candidate + E7b coverage refusal reproduce; PASS rungs exact); integrity clean. Zero implementation defects; the conditioning story is now quantitative (offset invariance to 1e15 via Sterbenz; linear u*X inertia degradation within derived bounds; gates at their declared tolerance; bitwise compiler-exporter agreement).
**Fleet:** 4 live (M04-retry, B6, B9, B3-retry). Queue: B5 -> B8 -> B7x.

## CHECKPOINT T13 — B9 integrated (docs verified; DR-1 resolved)

**Verified:** B9 inventory-driven check; coordinator independently reproduced the DR-1 digest reconstruction (33 ls-tree lines -> ee27dcd2..., True); integrity clean. 54 examples 0 broken; two minor doc drifts (F-B9-1 phantom path citation; F-B9-2 CON-15 rounding slip, substantively irrelevant). M01's DR-1 decision request CLOSED with the construction recorded.
**Fleet:** 3 live (M04-retry, B6, B3-retry). Queue: B5 -> B8 -> B7x.

NOTE (T13a): lint flagged B9's backticked citations of the phantom surface-energy path (the F-B9-1 path string) — that phantom path IS finding F-B9-1 (the doc cites a nonexistent path; B9 quotes it as evidence). Rewording would weaken a drift finding. Committed via --no-verify with this explanation (same documented false-positive class as T9a: quoted/quoted-data paths vs doc pointers).

## CHECKPOINT T14 — B6 integrated (tensors verified to exactness)

**Verified:** B6 verify + route-C self-check re-run by coordinator (FAIL reproduces; measured 2.936e-12 <= corrected bound 8.634e-12 True); integrity clean. Cellwise parallel-axis recombination = 0.0 relative vs exporter; symmetry bit-exact; principal moments strictly physical. The single falsifier = agent-side tolerance derivation (L^2 cancellation at 101 m offsets), self-diagnosed with the scaling law; exporter exonerated.
**Fleet:** 2 live (M04-retry, B3-retry). Queue: B5 -> B8 -> B7x.

## CHECKPOINT T15 — M04 integrated: ALL TEN CORE ASSIGNMENTS COMPLETE

**Verified:** M04 compare re-run by coordinator (ALL_PASS; float crosschecks reproduce); integrity clean. Covariance holds on both transform paths; the fired falsifier was agent-side (trace-term error, exactly diagnosed at -15825 = sum of per-cell traces), exporter confirmed by Monte-Carlo ground truth. Refusal discipline also incidentally verified (non_manifold_vertex_link, duplicate_vertex_position honored on the agent's first invalid fixture).

**CAMPAIGN MILESTONE: M01-M10 ALL DONE.** Core validation complete: reproduction (M01), multi-cell (M02), scaling (M03), covariance (M04), order invariance (M05), malformed inputs (M06), ownership propagation (M07), robustness (M08), diagnostic CLI (M09), static validator (M10) — zero exporter defects found by any of them; every fired falsifier traced to agent-side instrumentation, honestly preserved. Plus B2a/B4/B6/B7/B9 integrated.
**Fleet:** 1 live (B3-retry). Queue: B5 -> B8 -> B7x.

## CHECKPOINT T16 — B3 integrated; B5 retry dispatched

**Verified:** B3 scoring re-run by coordinator (drops reproduce at the summary layer); integrity clean. Round-trip: parse layer BIT-PERFECT; summary layer drops 42 fields incl. CON-12 provenance ("never summarized away") — MV-B3-1 decision request joins the U7/M09 projection-mechanism family (disjoint field sets: complete/exported vs blocked/refused diagnostics). B4's smudge law holds at the CLI boundary.
**Fleet:** 1 live (B5-retry — the active serialized retry). Queue after B5: B8 -> B7x.

## CHECKPOINT T17 — B5 integrated; retry queue EMPTY; B8 + B7x dispatched (2 staggered)

**Verified:** B5 verdict tally re-verified by coordinator (44 PASS); integrity clean. Conservation through subdivision proven at rounding scale across 128x cell growth; derived law matched (characterized conditioning, zero defects).
**All [1302] casualties recovered:** O2, M04, M06, B3, B5 — every retry landed complete with the honest-resume pattern (brief survival checks, reconstructions marked, post-freeze edits audited).
**Fleet:** 2 live (B8: M09 CLI defect fixes with exclusive ownership; B7x: B7's missed mutations vs M10's validator). These are the final two tasks before consolidation.

## CHECKPOINT T18 — B7x integrated (the cross-check question answered)

**Verified:** B7x probe re-run by coordinator — frozen + regenerated corpora agree on all nine verdicts; integrity clean (incl. M10's dir untouched). M10 closes 4/9 gaps by predicted rules; the value class is the honest open residual (needs regeneration-diff or value oracle — a DECISION REQUEST for the architect, not something static validation can conjure); L2 reproduced.
**Fleet:** 1 live (B8 — the last task before consolidation).

## CHECKPOINT T19 — FINAL. B8 integrated; CAMPAIGN COMPLETE (B10 delivered)

**Verified:** B8 suite re-run by coordinator (17/17; read-only proof 415 files 0 changed); integrity clean. All 19 receipts integrated; every task in the directive's opening table AND the authorized follow-on backlog is DONE or dispositioned (B1 suite-reviews: B2a covered M09; the other suites' independent reviews are folded into the coordinator's fresh re-runs + B7x's cross-check — noted as residual optional work, not authorized-blocking).
**CAMPAIGN_REPORT.md written** — the 24h directive's five terminal deliverables: integrated revisions + artifact identities; 14-row verified-capability table; 6 fired falsifiers (all agent-side, all preserved) + B8's fixes + honest residuals; the 11-item decision ledger; exact recovery instructions.
**Worktree audit (standing rule):** 11 registrations, all durably referenced/locked/deliberately-spared; no removals needed; six dirty legacy trees untouched.
**FINAL STATE:** both campaigns terminal — mv-campaign COMPLETE (this report); anatomy campaign COMPLETE and decision-blocked (USTR_DIAGNOSTIC_RECEIPT). No agents running. No spin.

## CHECKPOINT U0 — BOUNDED IMPLEMENTATION PHASE opened (operator directive + Astra memo §3)

**Scope fingerprint verified** via Invoke-MonkeyCampaign.ps1 -Action validate: 33a8fb72... matches pin; 83/76. Memo read in full; the main checkout's contract doc records v1.0 with D1-D5 DECIDED (the mv worktree's 3db8bc4e copy is the older v0.9 — W6 reads the main checkout's version, read-only).
**Campaign evidence preserved** — all corrections append-only; no history rewrite.
**Dispatched (staggered pair 1):** W1 (source-bound regeneration verifier, owns the proof-verify battery for M01-F1's blob-form entry) + W3 (reader M13 repair — the first authorized narrow tools/ change on this branch). Queued: W4, W5, W6 + reviews R1-R3.
**After this bounded work lands and integrates:** capacity returns to the playable path (walking, controls, forest, grasp on the approved list) per MONKEY_RUN.md.

NOTE (U1): W4 integration — lint flagged the archived B9 receipt copy's quoted phantom-path evidence (F-B9-1), same documented class as T13a. Committed via --no-verify with this note; archive verbatim, receipts byte-preserved.
