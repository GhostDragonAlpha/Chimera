# Universal-prompt release gate

Status: **HOLD**, 2026-09-09. Alan is waiting to dispatch until documentation
is reconciled. This gate does not cancel existing explicit worker assignments.
The draft PR and passing controller tests do not activate the fleet.

## Release requirements

1. Review documentation coverage against its exact inspected commit. Every
   document is classified as current instruction, design, reference, evidence,
   history or unresolved. A heading index is not a completed prose review.
2. Reconcile all instructions reachable from onboarding: authority, scope,
   task selection, branch/publishing rules, runtime, DYAD, evidence and recovery.
3. Explain historical supersession where agents encounter it. Preserve records;
   do not silently rewrite historical failures or revive retired workflows.
4. Trace prescribed commands to actual source and resources. Commands called
   read-only must be checked for constructor/import side effects and hidden
   state paths, not merely accepted from their docstrings.
5. Identify the active canonical stores and implemented adapters. Unavailable
   adapters result in explicit manual coordination, not competing local stores.
6. Test the joining path on an isolated, provisioned environment, including
   missing service, wrong checkout, stale task, absent eye and occupied port.
7. The authorized lead records release with exact source revision, coverage,
   outstanding scope limits and integration evidence. No self-declared ready.

Full-documentation review: **INCOMPLETE**. Five-engine Windows deployment,
provider/process observer, authoritative-store adapter and GitHub publication
broker: **NOT IMPLEMENTED/NOT TESTED** as described in THE_AGENT_FLEET.md.
No change to these states follows merely from this document existing.

## Additional source-backed findings

| Finding | Required joining behavior |
|---|---|
| `docs/AGENT_TASK_TEMPLATE.md` forbids reports and new modules; `docs/FOUNDATION_AGENT_TASKS.md` requires them | The generic position/direction template is a bounded construction procedure, not a universal prohibition. Follow the current explicit task envelope; do not suppress required evidence or invent permission to widen scope. |
| The template says a float64 grid can always be subdivided | Fixed-precision coordinates have finite representable spacing. State local-frame/precision/error budgets; do not promise unlimited resolution. |
| The template treats only artifact measurements as answers | Preserve source-reviewed, derived, measured, executed and inferred evidence classes. Source inspection can establish what code says, not that an engine run passed. |
| Foundation revision-1 dispatch tables still call G01 ready and I01 unassigned | These are historical assignments; they must not override current claims or restart completed work. |
| `tools/orient.py` reads module-relative `engine_state.json` and `verdict_registry.json`, not a live Vulkan endpoint | Its output describes that checkout's stores. It does not identify the currently displayed engine or prove shared fleet authority. An adapter must bind store identity and source revision. |
| `Engine._load()` reconciles saved hierarchy with generated terms in memory | Orient output can differ from raw saved JSON. Record generated terms identity as well as state file identity; do not call it a byte-for-byte snapshot of the original file. |
| A fresh worktree carries its own copies of those JSON stores | Five copies must not independently become the authoritative verdict ledger. Before writes, use a designated serialized owner/adapter. |

Scope of this pass: full-text review of AGENT_TASK_TEMPLATE and
FOUNDATION_AGENT_TASKS; source review of orient.py, Engine constructor/load/
reconcile/save and VerdictLedger constructor/load/save/new. No engine command,
model inference, ledger mutation or simulation ran. Additional documents remain
in the indexed review queue. Source base: bf0a62162008c8415b88091c671ac180dbb50193.
