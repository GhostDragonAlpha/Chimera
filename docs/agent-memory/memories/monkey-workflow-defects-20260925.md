---
name: monkey-workflow-defects-20260925
description: Workflow bug report 2026-09-25 (c95e session) + resolution status —
  startup crash-atomicity and reproducer paths FIXED by astra-0029; NEW serious
  defect: attempt-workspace isolation not enforced (another worker modified my
  submitted workspace and their PR shipped the file)
metadata:
  node_type: memory
  type: project
  originSessionId: sess_c54806df-1a14-46a8-ba72-970193f85ce3
---

Reported to the operator at the end of the
[[monkey-continuous-session-20260925-c95e]] session (findings only; nothing
fixed). Triage:

**Real defects:**
1. **worker_start.py startup is not crash-atomic against interrupted stdout.**
   First run claimed D-FOREST-RUNTIME-FOLLOWUP (checkout created), output
   piped through `head -c` died, retry with `--arrival-id` returned a
   DIFFERENT card (I-R02) — one arrival left an orphan attempt dir + checkout
   on a card it never worked. Arrival ID sits at the END of a ~150 KB JSON
   response. Fix suggested: sidecar identity file in the attempt dir.
2. **Lead CHANGES_REQUIRED messages cite reproducer files with no path**
   ("Reproducer: probes.py in the lead evidence directory", "probe124.py") —
   unretrievable; workers must reconstruct reproducers from prose.
3. **Two divergent copies of monkey_completion_map.json**: play worktree is
   stale (33a8fb72-era) vs canonical E:/PythonChimera (01ea5cdd) — ONT-P01's
   own identity oracle REFUSES against the play worktree (correctly, but
   looks like a contract defect to any worker there).
4. **Unsubmitted candidates from dead attempts are invisible**: D-W04-FOLLOWUP
   prior attempt left a complete proposed.patch + evidence at CARD level with
   no publication request; only manual scavenging recovered it. No
   "orphaned candidate bytes" notice at assignment time.
5. **Merged-PR content unreachable from worker checkouts** (#117–#120 merge
   commits in no local object store; review checkouts worked only because
   pre-fetched at assigned heads; no worker fetch guidance).

**Design friction:** no backpressure (one arrival queued 15 PENDING
publication requests while lead publication is the bottleneck); dead-attempt
checkouts accumulate (disk is the named constraint); ontology packets
inconsistent (some full briefs, some kind:null/owned_files:null generic
templates); stale read_first pointers (pr-review-20260925/REVIEW.md absent);
stale STATUS.json (astra-0006-era) at the coordination root; loose
owned_files/artifact validation. Operator-priority recommendation: fix #1
(atomic startup + sidecar identity file) and #2 (deliverable reproducers)
first.

**Self-litter disclosed:** scratch captures startup_c95e.json, reqpr2..15_c95e.json,
review1/2_c95e.json written into E:/ChimeraWork/monkey-coordination root (mine,
deletable).

---

## Resolution status (observed 2026-09-26 continuation, revision astra-0029)

**FIXED:**
- **#1 startup crash-atomicity** — startup now emits a `CHIMERA_STARTUP_RECOVERY`
  sidecar receipt (startup-receipts/<sha>.json) before the JSON body; rerunning
  with `--arrival-id` recovered cleanly with no orphan claim.
- **#2 reproducer paths** — the lead clarified exact reproducer paths in the task
  inbox after the report (E:/Chimera/queue-review-20260925/probes.py,
  E:/Chimera/zcode-quality-20260925/independent_probes.py, decisions in
  queue-review-20260925/REVIEW.md). Reproducers are now runnable.

**STILL OPEN (from the original list):** #3 stale play-worktree completion map,
#4 orphaned-candidate invisibility, #5 merged-PR content unreachable, all design
friction items.

**NEW — SERIOUS #6: attempt-workspace isolation is not enforced.** During the
2026-09-25→26 continuation, another worker (attempt fedb0b8b, arrival
fa11c6b3) MODIFIED FILES INSIDE MY submitted attempt workspace 32070971 AFTER
my publication request: PREREGISTRATION.md replaced with text describing THEIR
generic verifier (sha 71dd118f), proposed.patch overwritten (5f0567cf),
candidate.diff added — and their PR #129 then shipped the modified prereg
byte-identical out of my workspace. The lead's hash audit
(E:/Chimera/attempt-identity-audit/AUDIT.md) caught the mismatch between the
recorded request hashes and the workspace files. Recovery pattern that worked:
the original PREREGISTRATION was reconstructed byte-exactly from the author's
frozen source text and VERIFIED against the request's recorded sha (e4e1cd0c),
and proposed.patch regenerated from the unchanged files and verified against
ecf66f5a — hash-bound publication requests make tampering fully recoverable,
which is why per-attempt workspace write isolation should also be enforced
mechanically.
