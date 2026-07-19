# Gaussian Foundry — Autonomous AI Game Development System

## Architecture Overview

```
                          ┌──────────────────────┐
                          │     COUNCIL (Tier 1)  │
                          │  Strategic dialectic   │
                          │  2 agents, Q&A cycle  │
                          └──────┬───────────────┘
                                 │ design decisions
                                 │ implementation specs
                                 ▼
  ┌─────────────────────────────────────────────────────┐
  │                  WORKSHOP (Tier 2)                   │
  │  Implementation pipeline                             │
  │                                                      │
  │  ┌──────────┐   ┌──────────┐   ┌───────────────┐    │
  │  │  Writer   │──►│ Builder  │──►│  Reviewer     │    │
  │  │  (edits)  │   │  (UBT)   │   │  (diff + deps)│    │
  │  └──────────┘   └──────────┘   └──────┬─────────┘    │
  │                                       │              │
  │                                       ▼              │
  │                              ┌──────────────────┐    │
  │                              │  Sleepwalker     │    │
  │                              │  (beat tests)    │    │
  │                              └──────────────────┘    │
  └─────────────────────────────────────────────────────┘
                                 │ results
                                 ▼
  ┌─────────────────────────────────────────────────────┐
  │              PROVING GROUND (Tier 3)                 │
  │                                                      │
  │  ┌────────────┐  ┌────────────┐  ┌───────────────┐  │
  │  │  Visual IQ │  │  Profiler  │  │  Telemetry    │  │
  │  │  (SSIM)    │  │  (GPU ms)  │  │  (FPS, mem)   │  │
  │  └────────────┘  └────────────┘  └───────────────┘  │
  └─────────────────────────────────────────────────────┘
                                 │ evidence data
                                 ▼
  ┌─────────────────────────────────────────────────────┐
  │              DNA GRAPH (Chimera)                     │
  │  FeatureUpdate nodes, SimPlaytest evidence,         │
  │  pathway_attempt records, GPA grades               │
  └─────────────────────────────────────────────────────┘
```

## The Three Tiers

### Tier 1: Council — Strategic Dialectic

**Purpose:** Never write code until the design has been stress-tested by a questioning agent.

Two roles, cycling perpetually:

| Role | Function | Output |
|------|----------|--------|
| **Architect** | Asks probing questions about design, tradeoffs, edge cases | 10 questions |
| **Engineer** | Answers with technical depth, references actual code | 10 answers |

**Cycle:**
1. Architect asks 10 questions about the NEXT task on the board
2. Engineer answers (may require code spelunking via bash)
3. Engineer asks 10 questions about feasibility, test strategy, failure modes
4. Architect answers
5. If no objections remain → spec is locked and passed to Tier 2
6. If objections remain → repeat with deeper questions

**Gate:** A task cannot enter Tier 2 until Council produces a `spec_manifest.json`.

### Tier 2: Workshop — Implementation

**Purpose:** Write, build, and validate code changes autonomously.

Four stages, each gated:

```
    spec_manifest.json
          │
          ▼
  ┌──────────────┐
  │  1. Writer   │  Reads spec, makes file edits
  │  (pi agent)  │  Produces: git diff
  └──────┬───────┘
         │ diff exists
         ▼
  ┌──────────────┐
  │  2. Builder  │  Runs UBT compile
  │  (bash UBT)  │  Produces: pass/fail + error log
  └──────┬───────┘
         │ pass
         ▼
  ┌──────────────┐
  │  3. Reviewer │  Reads diff, checks deps, convention
  │  (pi agent)  │  Produces: review_verdict.json
  └──────┬───────┘
         │ approved
         ▼
  ┌──────────────┐
  │  4. Beats    │  Runs sleepwalker beat tests
  │  (PIE)       │  Produces: sim_evidence.json
  └──────┬───────┘
         │ beats pass
         ▼
    workshop_result.json  →  Tier 3
```

**Failure recovery:**
- Build fail → error sent back to Council as context for a special "postmortem" cycle
- Review rejected → Writer gets a specific diff-sited review comment
- Beats fail → forwarded to Council: "did we miss an edge case in the spec?"

### Tier 3: Proving Ground — Evaluation

**Purpose:** Measure whether the change actually improved things.

| Probe | What it measures | Threshold |
|-------|-----------------|-----------|
| **Visual IQ** | SSIM vs reference frame | >= 0.97 |
| **Profiler** | GPU sort/alpha/blend timestamps | No regression >5% |
| **Splat counter** | Splat count within tolerance | ±5% of expected |
| **FPS probe** | Frame rate at target resolution | >= 30 FPS |
| **Telemetry** | Crash-free rate | 100% |

**Output:** `proving_ground_report.json` → recorded to DNA graph as FeatureUpdate.

---

## Implementation Plan

### Phase 1: The Council (immediate — we already have this)

1. ✅ PI Worker Bridge (FastAPI + pi --mode rpc)
2. ✅ DialogOS loop (Worker→Main / Main→Worker Q&A cycle)
3. [NEW] `Council spec_manifest.json` output format

### Phase 2: The Workshop (build next)

1. `forge.py` — Orchestra that takes a spec and runs Writer→Builder→Reviewer→Beats
2. Writer agent: reads spec, plans edits, executes them via the Worker Bridge's API
3. Builder: runs `chimera_build_project` via the Chimera pipeline
4. Reviewer: reads the diff via the Worker Bridge, checks against convention
5. Beat runner: triggers sleepwalker

### Phase 3: The Proving Ground (build after Workshop)

1. `anvil.py` — Runs all evaluation probes
2. Visual IQ via `researchengine` / screenshot comparison
3. Profiler integration with GPU telemetry
4. DNA graph recording

### Phase 4: Autonomous Loop (full integration)

```
Council ──► Workshop ──► Proving Ground ──► DNA Graph
   ▲                                               │
   └───────────────────────────────────────────────┘
                (results feed next cycle)
```

---

## Spec Manifest Format

The bridge between Council and Workshop:

```json
{
  "spec_version": "1.0.0",
  "task_id": "tb-N",
  "title": "Short description",
  "target_files": ["path/to/file.py"],
  "change_type": "fix | feature | refactor | perf",
  "design_rationale": "Why this approach was chosen (from Council Q&A)",
  "rejected_alternatives": ["What wasn't chosen and why"],
  "edit_plan": [
    {
      "file": "path/to/file.py",
      "line_range": [42, 67],
      "what": "Replace the sort key computation with hybrid depth",
      "how": "Change __clz-based log quantization to use top 3 mantissa bits"
    }
  ],
  "test_strategy": "Which beat scripts to run",
  "regression_risk": "LOW | MEDIUM | HIGH",
  "council_dialectic_ref": "chronicle/turn_002_phase_A.txt"
}
```

---

## Key Principles

1. **No code without questioning** — Every change must survive at least one Q&A cycle
2. **Build pass is table stakes** — A change that doesn't compile is not a change, it's noise
3. **Perceptual regression = veto** — SSIM loss is grounds for rejection even if the logic is correct
4. **Chronicle = memory** — All decisions are written to the chronicle, not to agent memory
5. **Council can override Workshop** — If the builder can't implement the spec, it goes back to Council, not to a human
6. **Human is the terminal, not the bottleneck** — Humans review only when the system hits a blocked state it cannot resolve
