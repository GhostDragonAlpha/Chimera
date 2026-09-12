# PREREGISTRATION — fleet-docs-operating-model-01 (generation 1)

- **Worker:** subagent-worker-03 (slot 4)
- **Branch:** `astra/tasks/fleet-docs-operating-model-01`, provisioned at tip `d012b4b1`
- **Date:** 2026-09-11
- **Controller source under documentation:** `E:\ChimeraWork\control\deployments\slot-binding-d012b4b1` (git `d012b4b1`, service live since 2026-09-11)

## STATEMENT

A new agent (lead, external worker, lead-delegated subagent worker, or dedicated DYAD
reviewer) can join the fleet and continue correctly from the canonical documents alone
(`docs/THE_AGENT_FLEET.md`, `docs/AGENT_START.md`, `docs/THE_RUN_QUEUE.md`, `README.md`,
and the copy-paste prompt block in `docs/evidence/agent_fleet/OPERATING_MODEL/PROMPTS.md`)
because the documents describe the operating model actually deployed at controller
source `d012b4b1`.

## PREDICTION (unmeasured before this run)

Every fleet operation the documents name exists in the deployed controller — each will be
verified by reading `control.py`, `review_handoff.py`, and `run_queue_worker.py` at
`E:\ChimeraWork\control\deployments\slot-binding-d012b4b1` and recording the check in a
verification table (`VERIFICATION.md` in this directory). Additionally, each copy-paste
prompt names its own session/claim mechanism (session file path, owned claim, resume
semantics) and no prompt instructs Alan to relay commands between agents.

## FALSIFIER (named before the run)

The statement LOSES if any of the following is observed:

1. A documented operation (method name, refusal reason, receipt field, or cap) that does
   not exist in the deployed `control.py` / `review_handoff.py` / `run_queue_worker.py`.
2. Any prompt block that instructs Alan/the human to relay commands between agents
   (Alan-relay steps), rather than each agent acting through its own session file or
   owned claim.
3. A contradiction with AGENTS.md law (e.g., rewriting append-only historical sections,
   editing lead-owned `docs/THE_MASTER_LIST.md`, or claiming verification without
   reading the deployed source).

## SCOPE

Docs only: `docs/THE_AGENT_FLEET.md` (append-only dated section), `docs/AGENT_START.md`,
`docs/THE_RUN_QUEUE.md`, `README.md`, `docs/evidence/agent_fleet/OPERATING_MODEL/*`.
NO code changes, NO edits to `docs/THE_MASTER_LIST.md`, NO GPU/engine/DYAD work, NO
writes outside the worktree `E:\ChimeraWork\slot-04`.

## VERDICT FORM (filled in VERIFICATION.md after the run - the actual retained artifact)

- PASS: all named operations verified present; prompts self-contained; no falsifier fired.
- FAIL: any falsifier observed, with the exact operation/prompt/line named.
