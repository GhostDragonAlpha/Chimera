# Z Code: lead-only delegation

Installed 2026-10-22 for the operator's request to prevent child agents calling
Explore or other agents and causing unnecessary model switches.

## Behavior

The lead retains `Agent` and `SendMessage`. Every child, including built-in
Explore, general-purpose, custom profiles and restored children, loses `Agent`,
its `Task` alias, `SendMessage`, `CreateWorkflow` and `AmendWorkflow` from the
model-visible tool list. The native executor also refuses these calls before
validation/dispatch, including calls retained in earlier context or invented by
the model. The restriction checks actual runtime/session identity and survives
compression and direct CLI restoration.

Children keep their ordinary scoped work tools, `RespondToCoordinator` when an
owning coordinator is attached, and their final report. A directly reopened child
without a coordinator can return a final response. Qwen decides whether another
expert is needed. Existing role-specific restrictions still apply.

The project hook now recognizes built-in and native child identities, persists
the child role, and denies peer resume through `SendMessage` too. Startup,
compression instructions and plan §11.22 carry the same rule. The saved goal and
progress were not reset. Model selection, context, quantization and services were
not changed. Running app processes were not stopped.

## Reproduction and validation

The old native CLI, tested in an isolated home with project hooks disabled,
exposed delegation tools when reopening a saved Explore child. The scripted
`Agent` call created an actual grandchild session: five sessions instead of the
expected lead and three direct children. Generic and explicitly granted child
profiles also exposed workflow-creation/amendment tools. This isolates a runtime
gap independently of our project hook.

After patching, the same fixture passed against the installed bundle:

- Three direct children: built-in Explore, general-purpose wildcard tools, and
  a custom profile explicitly requesting delegation tools.
- All five forbidden calls rejected in each initial child and after direct
  child compression/resume; no grandchild session or nested model request.
- Ordinary file read, coordinator report, lead dispatch, same-child follow-up
  and lead resume remained functional.
- Forty scripted endpoint requests; exactly four sessions; production provider
  configuration hash unchanged. No GPU/model inference was used or interrupted.
- Fifteen project-hook tests passed, including existing role, purpose, Blender,
  report and resume behavior.

Installed evidence:
`D:/Chimera-Maintenance/Runtime/zcode-goal-workflow-tests/single-level-1792690667576028600/result.json`.
Original-bundle reproduction:
`C:/Users/allen/.codex/visualizations/2026/10/10/01a125eb-1468-7723-8cf3-f4d7fb02dee0/single-level-1792690506202558100/result.json`.

The log message `Explore subagent spawned` is generic in this Z Code build; use
its `agentType` and persisted session parent to identify the actual profile and
lineage. Recent production messages with that wording identified `chimera-maya`.
The isolated reproduction proves the resume defect; it does not establish that
every reported production switch had that cause.

## Installation and maintenance

The bounded, anchor-checked bundle edit is reproducible with
`tools/zcode/patch_single_level.py`. It refuses already-patched or structurally
different bundles. It adds child tool filtering and an execution-time guard;
it preserves earlier reliability fixes. Full vendor bundles are not committed.

- Before SHA256: `d56609ba4c2036407be8f0c32d24cd8a1b2ebde46a95856307c8851b82960a93`.
- Installed SHA256: `ad544747662fe25f5424e7fb835b6ceb6c98a897ce027e23da627eca52ebec92`.
- Backups/manifest:
  `D:/Chimera-Maintenance/Runtime/zcode-two-agent/repairs/single-level-install-1792690573834377800`.
- Native fixture: `tools/zcode/test_single_level_native.py`; set
  `CHIMERA_TEST_ROOT` to an owned evidence directory, optionally set
  `CHIMERA_TEST_ENTRY` to a candidate bundle. It creates a private home and a
  loopback scripted model endpoint, not a live GPU inference request.

Close and reopen Z Code once to activate the native patch in already-running
app-server processes. A future application update can replace the bundle; check
the patch marker/hash and rerun the fixture before treating an update as ready.
This is an agent-tool policy, not an OS sandbox against a malicious child with
arbitrary shell access. Instructions also prohibit bypassing it through another
CLI or direct model request.
