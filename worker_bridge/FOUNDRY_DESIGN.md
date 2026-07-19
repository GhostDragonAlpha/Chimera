# Gaussian Foundry — Autonomous AI Game Development System

**Status: IMPLEMENTED AND OPERATIONAL** (July 2026)

## Architecture Overview

```
                          +-----------------------+
                          |     COUNCIL (Tier 1)  |
                          |  Strategic dialectic   |
                          |  2 agents, Q&A cycle  |
                          +----------+-----------+
                                     | design decisions
                                     | implementation specs
                                     v
  +-----------------------------------------------------------+
  |                  WORKSHOP (Tier 2)                         |
  |  Implementation pipeline                                   |
  |                                                            |
  |  +----------+   +----------+   +-------------+             |
  |  |  Writer   |-->| Builder  |-->|  Reviewer   |            |
  |  |  (edits)  |   |  (syntax)|   |  (diff+deps)|            |
  |  +----------+   +----------+   +------+------+             |
  |                                       |                    |
  |                                       v                    |
  |                              +------------------+          |
  |                              |  Sleepwalker     |          |
  |                              |  (beat tests)    |          |
  |                              +------------------+          |
  +-----------------------------------------------------------+
                                     | results
                                     v
  +-----------------------------------------------------------+
  |              PROVING GROUND (Tier 3)                       |
  |  Build status, model state, session health checks          |
  +-----------------------------------------------------------+
                                     | evidence data
                                     v
  +-----------------------------------------------------------+
  |              DNA GRAPH (Chimera)                            |
  |  FeatureUpdate nodes, SimPlaytest evidence,                |
  |  pathway_attempt records, GPA grades                      |
  +-----------------------------------------------------------+
```

## The Three Tiers

### Tier 1: Council — Strategic Dialectic (IMPLEMENTED)

**dialogos.py** — Two roles in a continuous Q&A cycle:

| Role | Function | Output |
|------|----------|--------|
| **Worker** (Asks) | Probes architecture, tradeoffs, edge cases | 10 questions |
| **Main** (Answers) | Responds with technical depth, code references | 10 answers |

Then roles swap: Main asks, Worker answers. Each turn produces 4 chronicle files.

**Results from operational runs:**
- 6 completed cycles (3 full 2-turn runs)
- Topics covered: splat LOD, depth quantization, variance correction, CONTAIN metric, Dyad router, streaming protocol, Vulkan backend, mobile porting, VR stereo fusion, bus-factor mitigation, CI gate design
- Each cycle deepens — questions build on prior answers
- Errors in arithmetic and assumptions are caught by iterative probing

### Tier 2: Workshop — Implementation (IMPLEMENTED)

**forge.py** — Four-stage gated pipeline:

| Stage | Tool | Gate |
|-------|------|------|
| Writer | Worker PI agent | Edits applied |
| Builder | Python syntax check | 0 syntax errors |
| Reviewer | Convention check | No blockers |
| Beats | Sleepwalker (PIE) | 3/5 beats reached |

**Results:**
- Writer produced 23 file changes (1,530 insertions) in one productive cycle
- Changes to `splat_emit.py`, `splat_gpu.py`, `fractal_zoom_sweep.py`, docs, config
- Builder verifies 626 Python files with 0 errors
- Beats achieves 3/5 reach on regolith_yard simulation

### Tier 3: Proving Ground (PARTIAL)

Status checks and basic evaluation. Full visual SSIM comparison requires a baseline reference frame.

## Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI server wrapping `pi --mode rpc` (REST + WebSocket) |
| `dialogos.py` | Council: automated dialectical Q&A loop |
| `council_to_forge.py` | Bridge: extract spec from chronicle |
| `forge.py` | Workshop: Writer->Builder->Reviewer->Beats |
| `run.py` | Unified entry point for pipeline |
| `worker_client.py` | Python SDK for REST API |
| `launch.ps1` | PowerShell launcher |

## Pipeline Flow

```
python run.py --turns 2

  1. COUNCIL:  2 turns x 4 phases = 8 prompts
     - Worker asks 10 questions
     - Main answers 10
     - Main asks 10 questions
     - Worker answers 10
     -> chronicle/turn_001_*.txt ... turn_002_*.txt

  2. BRIDGE:  Extract spec from latest turn
     -> specs/spec_turn_002.json

  3. WORKSHOP:
     - Writer: reads spec, applies edits via worker PI
     - Builder: syntax check on 626 Python files
     - Reviewer: convention check on diff
     - Beats: sleepwalker beat tests in PIE
     -> chronicle/forge_result_*.json

  4. PROVING GROUND: Status check
     -> chronicle/proving_ground_report.json
```

## Key Principles

1. **No code without questioning** — Every change survives at least one Q&A cycle
2. **Build pass is table stakes** — 626 Python files, 0 errors
3. **Beats pass is verification** — 3/5 sleepwalker beats minimum
4. **Chronicle = memory** — All decisions written to chronicle files
5. **Human is the terminal** — No human bottlenecks, only human terminals for taste
