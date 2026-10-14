# PREREGISTRATION — wk-evidence-package VALIDATION-ONLY battery (2026-10-02)

Lane: wk-evidence-package (chimera-worker under the main Lieutenant).
Scope: the PACKAGE FORMAT + TOOLING for the GOAL's final evidence package.
This lane runs NO NEW PHYSICS: the battery replays EXISTING sealed store bytes
(MAT2-W08, the commanded-seam walk card) through the builder. No gated run,
no engine run, no capture. Records/tooling only.

## What is being measured

Whether `chimera.evidence_package.v1` (build_package.py + PACKAGE_SPEC.md)
assembles and verifies an evidence package over a sealed continuous run, and
whether the format's falsifiers all fire:

## Predictions (frozen before the sealed runner run)

- PR1 (positive build): over the pinned W08 store artifacts, `build` produces a
  VALIDATION-ONLY package with: tick domain [0,10499] contiguous (10500 rows);
  60 frames tick-resolved from `sheet_layout.frame_files` (sorted key=int);
  403 input events; 10 frozen bindings; video<->trace identity proven via
  capture_validation_receipt; energy class DECLARED-ABSENT with reason;
  package_sha256 over canonical body.
- PR2 (verify): all 10 bindings re-hash clean; sync law + no-teleport /
  no-hidden-anchor / no-reset re-proven; result VERIFIED.
- PR3 (inspect): content address intact.
- PR4 (probe A1): a capture-manifest copy with a frame tick moved outside the
  domain refuses `sync_frame_outside_tick_domain`.
- PR5 (probe A2): a duplicated frame tick refuses
  `sync_frame_ticks_not_unique_monotonic`.
- PR6 (probe B1): a post-freeze one-bit change to a bound artifact refuses
  `freeze_violation` at verify.
- PR7 (probe B2): an edited package body refuses `package_tampered`.
- PR8 (probes C1-C3): injected wrong_script event / applied-command rewrite
  with zero saturation / injected "teleport" intervention row each refuse
  `input_assertion_violation` (detail classes wrong_script / teleport / teleport).
- PR9 (probe C4): an event tick outside the domain refuses
  `input_event_outside_domain`.
- PR10 (probes C5-C6): a deleted row refuses
  `records_tick_domain_not_contiguous`; a duplicated tick refuses
  `records_duplicate_tick` (the reset-class desync surface).
- PR11 (probe D): a trace with decisions removed refuses
  `input_log_not_expressible`.

## Falsifier

Any probe that does NOT refuse with its exact named code (i.e. the format
accepts a desync, a post-freeze modification, or a prohibited input
injection), or any positive-path failure, falsifies the format claim; the
battery exits nonzero and the format is NOT proven. A probe that refuses with
a DIFFERENT named code than predicted is recorded as a deviation (the battery
flags it) and routed to the Lieutenant with the artifacts.

## Identity pins

- Store card: evidence-store/MAT2-W08 (16 rows in store MANIFEST.json; 10 bound).
- Authoring identity pins cross-checked at run: trace_commanded.json
  ee3413d1...; capture_commanded.mkv 3d991a8b...; PREREGISTRATION.md 00a04e08...;
  capture_receipt.json 32f56d59....
- LV-1 citation (requirement lead from the lineage lane, under review):
  lineage-verify/REPORT.md sha256 79aa499755eed5619969deaf8b69044dfb0d0a83662cdd9f850c892c58aab148.
- Execution: task_package.py slots 2/3 only; base = the cached origin/master
  ref resolved at package creation (recorded in package.json; a cached ref is
  not a claim of remote freshness).

## AMENDMENT 1 (REV2, 2026-10-03, post-SGT-review; the REV1 bytes above stand as sealed history in package/sealed/bcb14b60..4769e31b)

- F1 (material): every LV-1 citation now names the OWNING lane's CURRENT
  authority, lineage-verify/REPORT.md sha256
  b7801ce08b53f9f16edbbf67607406e48cdd919d95b44fc6f7f5055e3fbe384f
  (supersedes the prior round 79aa4997...; the owning lane's EVIDENCE line 94
  names the supersession). The citation is BOUND as the `lineage_report`
  frozen binding (re-hashed at run, build and verify) — REV1's citation-only
  sha had escaped every re-hash gate by design; that is the recorded lesson.
- F2 (moderate): the no_reset session clause and the no_hidden_anchor
  command-name clause are now MECHANICAL: the session census is byte-derived
  only (sink_records + decisions' own source fields; the assembly's
  source_default is attested separately, never counted) and refuses
  `input_assertion_violation` class `multi_source_session` unless
  `allowed_sources` is declared; event COMMAND names are token-scanned and
  refuse prohibited anchor/weld/teleport/reset classes. Spec section (c) now
  maps every clause to its check.
- F3 (minor): the A2 alias example is '0300' == tick 300 (the first
  numerically-sorted sheet key), not '01310'/'1310'.
- Amended predictions: PR1 now expects 11 frozen bindings (the bound
  lineage_report) and session_sources == [u01_input_mapper];
  NEW PR12: an assembly citing the superseded prior-round sha refuses
  `freeze_citation_stale`; NEW PR13: an assembly naming an unbound citation
  refuses `freeze_citation_unbound`. All other REV1 predictions stand.
- The validation package is REBUILT under the immutability law (new content
  address; REV1's 0c56bb95... is preserved as history).

## What this does NOT claim

No physics qualification, no acceptance, no merge authority. The validation
package is labeled VALIDATION-ONLY and is never the final demonstration. The
K02/landing candidates were evaluated and NOT used: K02's capture frames were
not preserved as declared keeps (only summary hashes survive) and its frames
carry no tick keys (`render_k02.py` drops frame_id); the landing lane's run is
records-only (prereg consistency), with no physics run or video. W08 is the
sealed store card that carries BOTH continuous video and continuous records
plus the input-event log.
