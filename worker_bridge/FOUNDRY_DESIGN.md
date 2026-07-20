# Gaussian Foundry — Architecture

**Status: BUILD MODE** (Council retired after 10 cycles)

## Architecture

```
Human → Agent → Worker Bridge (pi --mode rpc) → Workshop (forge.py)
                                                   │
                                          Writer → Builder → Reviewer → Beats
                                                                ↓
                                                           Commit
```

## What Changed

The Council (dialogos.py) — the automated Q&A loop between two simulated roles — ran for
10 cycles and completed its purpose. It designed the methodology, mapped the architecture,
and taught the asker to ask its own questions. It is retired.

The system now operates in BUILD mode:
- Human gives direction to the lead agent
- Lead agent sends design briefs to the worker via the bridge
- Worker produces designs and code
- Forge (forge.py) implements, builds, reviews, and tests
- Lead agent reports results
- Results are committed

## Workshop (forge.py)

Four-stage gated pipeline:

| Stage | What | Gate |
|-------|------|------|
| Writer | Reads spec, applies edits via worker | Edits applied |
| Builder | Python syntax verification | 0 errors |
| Reviewer | Convention check | No blockers |
| Beats | Sleepwalker PIE tests | 3/5 beats minimum |

The builder uses Python syntax check as its primary gate. Full UE5 compilation
has pre-existing issues in generated code that are addressed separately.

## Worker Bridge (main.py)

FastAPI server wrapping `pi --mode rpc`. REST + WebSocket endpoints.

Port 8888 by default. See README.md for full API reference.

## Cleanup

The following were deleted in July 2026 cleanup:
- `dialogos.py` — Council retired
- `council_to_forge.py` — depended on Council
- `run.py` — tied Council + Forge together
- `fractal_zoom_sweep.py` — stale copy (real one in Chimera/core/)
- `launch.py` — unused (replaced by .bat launchers)
