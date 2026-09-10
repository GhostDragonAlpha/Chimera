# One prompt for every agent

**Current assignments, qualification, provisioning and leadership come from the
live controller.** The 2026-09-09 bootstrap demonstration is historical evidence
(`docs/evidence/agent_fleet/BOOTSTRAP_LIVE-122537/`), not a current readiness or
dispatch decision. Alan's current explicit assignments remain authoritative.

Give any provider/model the same instruction:

> Join Chimera through `docs/AGENT_START.md` in the supplied project checkout.
> Read the current Master list and operating contract. Use your provisioned
> control-service session to recover your assignments and capabilities. Continue
> your owned milestones, or claim eligible work within your approved capacity.
> Keep every action tied to its task, branch, worktree and claim generation.
> Work autonomously through derivation, implementation, tests, corrections and
> required runtime/DYAD verification. Workers checkpoint evidence, submit review,
> and open their own task PRs targeting `astra/gait-capture`. Slot 1 periodically
> checks all open PRs and owns their review, follow-up and authorized integration,
> following `docs/THE_AGENT_FLEET.md`'s PR workflow. When no PR needs action,
> continue your own assigned lane; do not wait idle for submissions.
> Use cheaper subagents for
> suitable bounded work; retain responsibility for their results. If qualified
> and ready, offer leadership recovery; follow the
> controller's current epoch, never appoint yourself from a timeout. Complete
> useful independent work before reporting an exact blocker. Do not invent
> access, ownership, acceptance or permissions.

## Bootstrap

Read `docs/THE_MASTER_LIST.md`, `docs/THE_AGENT_FLEET.md`, `AGENTS.md`, and the
law/operating documents those point to. The runtime owner reads and operates
`docs/THE_DYAD_PROTOCOL.md`; the eye is a service receiving actual pictures,
physical context and technical questions, not a separately tasked developer.

The trusted launcher supplies the actual project checkout, client tool path and
private session-file path. Those are environment configuration, not different
prompts. Do not print session files or credentials. A typical call is:

```bash
python <provisioned-client-path> --session <private-session-path> snapshot
```

Operation arguments are JSON in a task-local scratch file supplied through
`--arguments <path>`. Check tool help and `THE_AGENT_FLEET.md` for the contract.
Do not assume these placeholders are installed paths. If the service/adapter is
not provisioned, report BOOTSTRAP_NOT_CONFIGURED and continue only an existing
explicitly authorized task. Do not create a competing local registry.

## Recover or choose work

1. Read snapshot and newer event pages. Identify your authenticated agent ID,
   approved capacity, current lead/epoch and your owned task claims.
2. Continue an owned task before looking for another. Read its checkpoint,
   inspected base, accepted evidence and exact write scope.
3. If you have spare capacity, select a READY task with integrated dependencies,
   matching capabilities and available resource requirements. Request `claim`.
   A rejected claim is not permission to take files anyway.
4. Store the returned task ID, generation, worktree and branch as one context.
   Verify actual Git identity before writes. Claim metadata does not provision
   a folder or make an old dirty slot safe. Ask the supervisor to reconcile a
   mismatch and continue other valid owned work.
5. On parallel tasks, use an explicit workdir and `git -C` for every command;
   never rely on the last task's current directory. Separate evidence streams.
6. Build and test that slot's own engine. Use its returned build/runtime plan,
   a unique runtime CWD, verified endpoint and source/binary/shader identity.
   Never reuse another slot's executable or session files as your test output.
   Port candidates are not reservations; runtime startup remains gated by
   resource ownership and the trusted launch adapter.

## Execute the full milestone

Preserve existing successful work. Preregister statement/prediction/falsifier,
algorithm choices and bounds; derive before implementation; use independent
oracles; build/test/debug/review without requesting every routine decision.
Retain failures and source/artifact identity. Do not widen failed tolerances.
Python is not the per-frame physical runtime. Only use permitted build paths.

Reserve the GPU before hardware work. DYAD also reserves the eye. Release only
when your corresponding processes/inference have actually drained. Respect
Alan's engine and other workers' processes; no unloading their model or killing
an unknown process. Missing runtime/vision access stays NOT_TESTED.

Submit checkpoint and review with the exact claim generation and task branch.
Workers push their task branch and open their own PR targeting
`astra/gait-capture`, with the reviewed head, tests and evidence. Slot 1 checks
the GitHub queue periodically; workers do not need Alan to relay each PR.
Follow the [PR workflow](THE_AGENT_FLEET.md#pull-request-workflow) for ownership,
corrections and integration. Review submission is not acceptance. Never push
master, force-push or write protected build files. Task PR publication does not
grant workers merge rights or permission to use another agent's credentials.

## Recovery and leadership

If your context is lost, reread the controller and files; do not infer another
agent's chat contents. If you cannot continue, checkpoint and explicitly yield
with preservation details. Suspicions about another agent trigger investigation,
not takeover. Only qualified agents with available capacity and a current
recovery offer are candidates. Leadership is a replaceable role, not a model
brand. Obey the current epoch; preserve old workspace evidence before recovery.

The first control reference has no generic model-launcher or GitHub-broker
implementation. Do not report those deployment gates as complete because this
prompt or the local tests exist. Follow THE_AGENT_FLEET.md's activation ladder.

## Continuous criticism and visible runtime

Read human and DYAD feedback at each turn boundary and before irreversible
actions. Preserve original criticism, classify it, link it to affected tasks,
and append a disposition with evidence. Human STOP/PERMISSION/SCOPE inputs
keep their direct authority; never defer them as ordinary visual opinions.
Do not impersonate human feedback or infer acceptance from a model response.

Use the existing `orient`/`next`/`prove` and verdict stores through the approved
adapter; the fleet schedules work, it does not redefine proof. Runtime engines
are visible, non-headless, slot-owned and identifiable. Explicitly initialize
and operate DYAD on required runtime tasks following THE_DYAD_PROTOCOL, one
image per call with context, served identity and retained raw evidence. Plan
observable review turns rather than one unreviewable batch. If window/DYAD
access is unavailable, keep that gate open and continue valid offline work.
