# Task 8 — Doc-Drift Audit (read-only)

## Method

Picked 10 claims from `AGENTS.md` and `docs/THE_LAW.md`'s rule index
(file paths, enforcer names, command lines). For each: checked file
existence, command execution, and enforcer presence in the actual repo.

## Verified Claims — 10 of 10 checked

| # | Claim (source) | What was checked | Verdict | Evidence |
|---|----------------|-----------------|---------|----------|
| 1 | `python Chimera/core/grow.py --read --depth 2` (AGENTS.md, "THE SESSION") | File exists + command runs | PASS | File exists. Runs, outputs tree structure |
| 2 | `python story/timeline.py` (AGENTS.md, "THE SESSION") | File exists + command runs | PASS | File exists. Runs, outputs timeline report |
| 3 | `python tools/methodology_gate.py` (AGENTS.md + THE_LAW.md EM-23) | File exists + command runs | PASS | File exists. Runs, outputs 42 membranes, 8 columns |
| 4 | `python tools/training_gate.py` (THE_LAW.md EM-1/EM-25) | File exists + command runs | PASS | File exists. Runs; PASS with derived targets, REFUSE with Earth targets |
| 5 | `python story/folding.py audit` (THE_LAW.md EM-23) | File exists + command runs | PASS | File exists. Runs, outputs misfold audit |
| 6 | `Chimera/docs/THE_FORMULA.md` exists | File exists | PASS | Get-ChildItem Chimera/docs lists THE_FORMULA.md |
| 7 | `Chimera/docs/EXPERIMENTAL_METHOD.md` exists | File exists | PASS | Get-ChildItem Chimera/docs lists EXPERIMENTAL_METHOD.md |
| 8 | `docs/THE_PIECES.md` exists | File exists | PASS | Test-Path returns True |
| 9 | `port_test()` at tools/port_registry.py:32 | Function exists | PASS | port_test() defined at tools/port_registry.py:32 |
| 10 | `parity_report` enforcer | Function exists where claimed | PASS | Defined at Chimera/core/matter_gpu.py:562, called from Chimera/core/matter_derive.py |

## Additional verified enforcer claims

| Enforcer | Claimed by (rule) | Actual location | Status |
|----------|-------------------|-----------------|--------|
| story/timeline.py | EM-22 | story/timeline.py | PASS — file exists, runs |
| tools/training_gate.py | EM-1, EM-25 | tools/training_gate.py | PASS — file exists, runs |
| ChimeraEngine/human_messenger.py | THE DYAD | ChimeraEngine/human_messenger.py | PASS — file exists |
| story/folding.py | EM-23 (CHECK order) | story/folding.py | PASS — file exists, runs |
| tools/chain_witness.py | EM-23 (CHECK order) | tools/chain_witness.py | PASS — file exists |
| tools/clay_check.py | EM-12 | tools/clay_check.py | PASS — file exists |
| Chimera/core/matter_gpu.py:parity_report | EM-24 | matter_gpu.py:562 | PASS — function defined + called |
| Chimera/core/preflight.py | AGENTS.md (modules) | Chimera/core/preflight.py | PASS — file exists |
| Chimera/core/task_board.py | AGENTS.md (modules) | Chimera/core/task_board.py | PASS — file exists |
| Chimera/core/postflight.py | AGENTS.md (modules) | Chimera/core/postflight.py | PASS — file exists |
| Chimera/core/circadian.py | AGENTS.md (modules) | Chimera/core/circadian.py | PASS — file exists |

## Stale / retired references

| Claim (source) | Actual state | Drift? |
|----------------|-------------|--------|
| `docs/WORKFLOW.md` (foundry) "no longer exists" (AGENTS.md) | docs/WORKFLOW.md MISSING | No — correctly marked retired |
| `docs/THE_WORKFLOW.md` is the method (AGENTS.md) | docs/THE_WORKFLOW.md exists, §0 present | No — correct |
| `docs/THE_COMPILER.md` contains "ports -> primitives -> ... -> calibration" (THE_LAW.md:114) | Confirmed: THE_COMPILER.md:15-16 | No — correct |

## Summary

**All 10 selected claims verified PASS.** The AGENTS.md and THE_LAW.md
rule index accurately reflect the repo state for file paths, command
lines, and enforcer locations. Stale references are correctly marked
as retired. Two legitimate gate findings (the 2 "units" failures in
methodology_gate) are documented in Task 10 deliverables.
