# Chimera — Build System Reference

## NEW AGENT? START HERE (in order)
1. `cd E:\PythonChimera\Chimera` then `python -m core.preflight` — live state: graph health, GPA, loop board, pending research, last run, environment, and **[4.5] Inheritance** (previous generation's Will, open phantom pains, Dream Report count, Observation queue). Preflight now OPENS with the **CAPCOM operator channel** (agent-agnostic; `core/capcom.py`) — unread signals pushed by subsystems and the human. `python -m core.capcom brief` is the standalone read for any agent/harness; leave the operator a note via `python -m core.capcom tell "..."` or by editing `Chimera/docs/OPERATOR_INBOX.md`.
2. Read `E:\PythonChimera\task_progress.md` — session handoff log; the top **NEXT** section is your work list.
3. Work under the Contract (below): typed recording only (`record_*` helpers), fix generator templates never generated C++, and answer the Frame Audit (`Chimera/docs/RESULT_GRADING_RUBRIC.md`) before declaring anything complete.
4. Finish with `python -m core.postflight --phase "..." --result "<UBT verbatim>" --inheritance "<=3 sentences" --phantom-pain "..." --pain-verdict "<id>:confirmed|refuted|still-open"` and update `task_progress.md` for the next agent.

## Generation Protocol (mandatory rhythm — full spec: Chimera/docs/GENERATION_PROTOCOL.md)
- **Fork before researching** (preferred): `python -m core.spiral_forks --feature X --use-lm` — 3 briefs (conservative/alternative/wild), winner proceeds after citation verification, losers autopsied. Forks never touch live state.
- **Capture surprises live**: `python -m core.graphify_record surprise --context "..." --reality "..." --source human|agent|engine` on any correction, dead-end, or expectation violation.
- **`verified` is the system's PRELIMINARY measurement.** Observation is the true collapse: `graphify_record observe --feature X --verdict accepted|rejected --notes "..." --loop N`. **Full automation amendment (2026-07-07, see "Sleepwalker & Rehearsal" / "No-blockers" below): automated processes MAY record an Observation, but only through the attribution-gated path `core/collapse_proxy.py` uses** — `derived_from=<simtest_id>` plus either `quote`=the specific simulation evidence naming that feature, or `tacit=True` for exercised-but-unindicted (enforced in `_mutate_observation()`, `graphify_interface.py`; a free-form/un-derived automated write is rejected). A rejection indicts ONLY the features simulation evidence actually names — never a mass sweep. The human's direct verdict remains a first-class override at any time, but note that "override anytime" is a documented convention (a notes-string recorded to the graph), not a hard runtime lock — nothing currently blocks a later automated write, so the convention depends on agents honoring it. Accepted → `observed`; rejected → `needs_refinement` with the notes as first-priority dream fodder. Boards show `[DONE*]` until observed.
- **The human Gardener approves EVERY heuristic** before it enters the constitution (`Chimera/docs/PENDING_HEURISTICS.md`; pending = inert; vetoed entries stay as tombstones).
- **Nightly**: `python -m core.dream_loop` — distills ≤2 candidates, previews compaction, writes `Chimera/docs/DREAM_REPORT.md`.

## Canonical Project Structure

```
E:\PythonChimera\Chimera\
├── Chimera.uproject
├── Source\Chimera\
│   ├── Chimera.Build.cs              # Do NOT regenerate
│   ├── Chimera.Target.cs
│   ├── ChimeraEditor.Target.cs
│   └── ProceduralGenerated\          # All generated code
│       ├── Combat\ AI\ Flight\ PCG\
│       ├── Stations\ Missions\ Factions\
│       ├── Save\ GameMode\ Ships\ Scripts\
├── Content\Levels\
├── Config\
└── core\dna\                         # Graphify DNA system
```

**Module**: `Chimera` | **API macro**: `CHIMERA_API` | **Dependencies**: Core, CoreUObject, Engine, InputCore, EnhancedInput, PCG, AIModule, GameplayAbilities, Niagara, NiagaraCore

**File ownership under `ProceduralGenerated/`** — generator-owned files (Flight, Ship, GameMode, PCGVolumeManager, Missions, Docking, QuantumTravel, Factions, Economy, Save, Combat suite, PirateAI) are regenerated every pipeline run: fix their generator template in `core/game_code_generator.py`, never the C++. Loop-built manual files (Tools, Interactions, Sound, UI, NPC AI, InventoryTradeComponent, ChimeraMovementComponent, StationActor) have no template and are safe to hand-edit.

## The Pipeline (Primary Build Mechanism)

```
cd E:\PythonChimera\Chimera
python run_deep_space_trader_pipeline.py
```

Runs: DSL Parse → Code Generation → Build → Playtest → Report → Visual Verification.
The Pipeline is the authoritative build mechanism. MCP is for discovery when the Pipeline encounters an unknown DSL term. Once MCP discovers how to build something, it records the pathway to the Graph and—where applicable—as a DSL mapping so the Pipeline can build it directly next time.

## Spiral Growth Pattern

Complete all features in Loop N before starting Loop N+1. Each loop's verified output becomes the foundation for the next.

```
Loop 0: The Player (character, suit, lighting)          → The seed
Loop 1: The Ground (sand, rock, metal, footprints)      → Touch
Loop 2: Basic Verbs (look, step, pick up, drop, shovel) → Interaction
Loop 3: The Sky (Earth, Moon, Sun, starfield)           → Scale
Loop 4: Tools (shovel, scanner, weapon)                 → Purpose
Loop 5: Other Dots (NPCs, creatures, trade, conflict)   → Society
Loop 6: Shelter (habitat, station, base)                → Home
Loop 7: Travel (vehicles, ships, quantum jump)          → Freedom
Loop 8: Systems (economy, factions, missions)           → Consequence
Loop 9: The Universe (planets, moons, asteroids)        → Infinity
```

## Research Agent Invocation Protocol (chimera-research mode)

Any agent mode can invoke on-demand web research without going through the Orchestrator. The Research Agent is a dedicated specialist whose ONLY job is to research questions, perform web searches, gather documentation, and return structured findings — it never writes code or implements features.

**Spawn via new_task (preferred):**
```python
new_task(mode="chimera-research", message="Research: <your question here>")
```

**Or spawn via Roo subagent pattern:**
```
Agent(subagent_type: "mode-research", prompt: "Research: <your query here>")
```

**What the Research Agent does:**
1. Queries DNA graph first (`g.query("pathway", ...)`, `g.query("feature", ...)`) — if answer exists, reports it and stops
2. Reviews mandatory docs (AGENTS.md known bugs/traps, GENERATION_PROTOCOL.md, MCP_PATHWAYS.md)
3. Performs Google search via Playwright MCP with minimum 3 sources
4. Classifies source types: official_docs, community, video_tutorial, technical_blog, general_web
5. Cross-references parameters across at least 2 independent sources
6. Searches for failure cases (what doesn't work) — minimum 1 failure source
7. Records findings to DNA graph via `record_research_summary()` when applicable
8. Returns structured markdown report with confidence ratings per finding

**Tier mapping (updated 2026-07-10):**
- **Quick (Tier 1):** DNA query + single search, ≥3 domains if web search performed, ~5 min max
- **Standard (Tier 2):** Multi-source verification + cross-reference, ≥5 domains + ≥3 source types, ~15 min max
- **Deep (Tier 3):** Source diversity (all 5 types) + failure research + multi-site (≥8 domains), ~30 min max

**Fallback chain:** Playwright MCP → DNA graph cache only → report gaps for manual review. If LM Studio is down, returns raw search results without analysis.

**Full spec:** [`.roo/modes/research-agent.md`](.roo/modes/research-agent.md) — complete role definition, capabilities, protocol steps, and known MCP traps.

### Context Exhaustion Controls (added 2026-07-10)

Every research task has minimum source requirements per tier (documented in [`.roo/modes/research-agent.md`](.roo/modes/research-agent.md)). The Research Agent MUST NOT report results until all context exhaustion checks pass:

| Check | Requirement |
|-------|-------------|
| Actual page visits | ≥2 real content pages (not just Google snippets) |
| Domain diversity | ≥3 different domains from different providers |
| Failure research | At least 1 source on what doesn't work |
| Related query follow-up | "People also ask" explored and followed up |

**Orchestrator validation:** The orchestrator validates that the returned report meets minimum thresholds before accepting it as complete. If a report fails validation, the orchestrator re-delegates to the Research Agent with explicit instructions to dig deeper, citing which thresholds were not met. See [`Chimera/core/research_enforcement.py:validate_research_depth()`](Chimera/core/research_enforcement.py) for programmatic enforcement.

## Feature Ledger (60+ Features)

Tracked in Graphify. Each feature node: name, type, loop, status (`not_started` → `researching` → `verified` → `encoded`), parameters, references, iteration history.

**Full feature list**: See `docs/THE_COMPLETE_CHIMERA_DEVELOPMENT_CYCLE.md` § Feature Ledger.

## The Contract (MANDATORY)

### Pre-Flight — one command
```
cd E:\PythonChimera\Chimera
python -m core.preflight
```
Prints graph health, GPA trend, spiral loop board, pending technical_research,
last pipeline run, environment reachability (Vision/Testing Model / UE / DNA API), junk count.
Report findings. Only then proceed. (Granular fallbacks: `g.query("health")`,
`g.query("pattern", task)`, `g.query("mutation", task)`, `g.query("gpa", "trend")`.)

### Post-Flight — one command
```
python -m core.postflight --phase "<what you did>" --result "<UBT output verbatim>" [--feature X --loop N --status S]
```
Records PhaseComplete (+ optional FeatureUpdate) and prints the closing checklist.

**Research Mandate compliance (Phase 3 Pipeline Integration):** After postflight, record a ResearchSummary for the completed phase:
```python
from core.graphify_interface import record_research_summary
record_research_summary(
    task_name="<phase name>",
    tier=<1|2|3>,
    sources_count=<N>,
    domains_visited=<M>,
    confidence_rating="high",
    source_table=[{"type": "primary_docs", "url_or_path": "...", "confidence": "high"}],
    discrepancies_resolved=["..."],
)
```

1. Report exact UBT output verbatim. Never summarize.
2. Update Feature Ledger. Record all MCP pathway results.
3. If GPA falling, report with corrective action. (Build failures auto-grade F,
   non-pass visual verifications auto-grade C — a falling GPA is real signal.)

### Recording convention (all mutations)
**Never hand-write `g.mutate` detail dicts** — mis-keyed dicts are rejected with a
`rejected_*` string (nothing recorded). Use the typed helpers from
`core/graphify_interface.py`: `record_feature`, `record_pathway`, `record_loop`,
`record_phase`, `record_grade`, `record_build`, `record_research_summary`, `record_documentation_review`, `record_pathway_attempt` — or the CLI
`python -m core.graphify_record {feature|pathway|loop|phase|grade} ...`.
Backfilling history? Add `backfilled=True` / `--backfilled`; never fake timestamps.
Every node is auto-stamped with `recorded_by` + per-process `run_id`.

### Research Mandate Quick Reference (added 2026-07-10)
**Full spec**: [`Chimera/docs/RESEARCH_MANDATE.md`](Chimera/docs/RESEARCH_MANDATE.md)

| Tier | Complexity | Requirements |
|------|-----------|--------------|
| 1 | Simple, single MCP tool call | DNA query + pathway follow (5 min max) |
| 2 | Multiple tools, new combination | DNA query + multi-source research + summary required |
| 3 | New feature/architecture | Tier 2 + reference images + >=3 domains + failure research |

**Enforcement**: [`Chimera/core/research_enforcement.py`](Chimera/core/research_enforcement.py) — `classify_task_tier()`, `validate_research_completed()`, `check_documentation_review()`, `build_subtask_message()`
**Dry-run tests**: `python -m core.test_research_enforcement` (validates tier classification, subtask builder, doc review checker on 5 mandatory docs)

## The Ralph Loop (Iterative Verification)

Pick feature → Research → Professor grades → Apply → Screenshot → Vision/Testing Model compares → Refine → Repeat until verified.

### Professor Review
Submit research summary to the Vision/Testing Model for verification before any MCP calls. Grade gates: A/B → proceed. C/F → return to research. Record grade via `g.mutate("professor_grade", {...})`.

### Research Depth Protocol (Gates)
Research is not complete until all gates are passed:

1. **Source Diversity** — minimum 3 source types (primary photography, technical docs, community, video, 3D scans, historical)
2. **Multi-Site Verification** — minimum 3 different domains (not pages on same site)
3. **Cross-Reference Confirmation** — 2 independent sources per parameter. If no second source exists, document absence, mark confidence Low, proceed.
4. **Failure Research** — minimum 1 source on what doesn't work (degradation, edge cases, abandoned designs)
5. **Campus Discovery** — every new source recorded via `g.mutate("research_discovery", {...})`. Uncapped. No limit.
6. **Research Summary** — source inventory, parameter table with citations, discrepancies resolved, confidence rating per parameter

Record metrics to DNA: sources_consulted, websites_visited, parameters_cross_referenced, new_campus_discoveries, failure_sources, research_confidence.

## Graphify Knowledge Graph

| Endpoint | Purpose |
|----------|---------|
| `docs/chimera_dna_graph.json` | Persistent DNA storage |
| `core/graphify_interface.py` | Query/mutate functions + typed helpers (`record_*`) |
| `core/preflight.py` | `python -m core.preflight` — one-command Pre-Flight report |
| `core/postflight.py` | `python -m core.postflight` — one-command Post-Flight recorder |
| `core/capcom.py` | **CAPCOM operator channel** (agent-agnostic push feed): `python -m core.capcom brief` / `tell "..."` / `post_safe(...)`; signals in `docs/world/capcom.db`. Human inbox: `docs/OPERATOR_INBOX.md`. Led into preflight; posted by postflight + task_board. |
| `core/graphify_record.py` | `python -m core.graphify_record` — typed mutation CLI |
| `core/dna/pattern_validator.py` | Blocks known-bad patterns before generation |
| `core/dna/auto_fixer.py` | Auto-fix brace errors |
| `core/dna/query_api.py` | FastAPI at `localhost:8766` (/dna/errors, /dna/health) |
| `dna_dashboard.py` | Streamlit dashboard |
| `docs/dna_graph_quarantine_unknown_nodes.json` | Archive of quarantined junk nodes |

**DNA Node Types**: Mutation, Error, Fix, Health, Pathway, FeatureUpdate, VisualVerification, ProfessorGrade, ProfessorGPA, TechnicalDiscovery, ResearchDiscovery, PhaseComplete, LoopComplete, ResearchSummary, PathwayAttempt, DocumentationReview

## MCP Pathway Rule

1. **Before any MCP call**: `g.query("pathway", "what_you_want_to_do")`
2. **Pathway exists** → follow exactly. **No pathway** → test simplest approach, record result.
3. **After every MCP call**: record as pathway_attempt mutation.

See `docs/MCP_PATHWAYS.md` for 14 working pathways with exact parameter schemas.

## Subagent Workflow

The Orchestrator compiles a context package and delegates to autonomous subagents:

1. **Context Package**: DSL block + Graph context (pathways, mutations, patterns) + reference images + campus sources + required endpoints
2. **Subagent Autonomy**: Research → Discover → Test → Record. Full authority to try 5+ parameter combinations before reporting blocked.
3. **Report Back**: Feature status update (verified/blocked) + what was discovered + what was recorded to Graph + what DSL mappings were created
4. **Discovery Recording**: Every new MCP pathway, research source, parameter set → recorded to Graph. If applicable → DSL mapping created so Pipeline can build it next time.

## Recursive Self-Improvement

Unknown MCP action → try 5+ parameter combos → record all attempts → spawn technical_research → move to next feature. When solved: record pathway → unblock features → next agent inherits discovery. Never ask for human help. Never mark "requires manual steps."

## Critical Technical Reminders

### Screenshots for Verification
**MCP `control_editor screenshot mode=editor_viewport` is the live, only screenshot path** (heuristic H-2, `docs/PENDING_HEURISTICS.md`, promoted 2026-07-07: "Never verify from desktop screenshots — capture via MCP control_editor screenshot mode=editor_viewport, which renders the viewport regardless of window focus." Confirmed in code: zero live `pyautogui.screenshot()` calls exist anywhere in `core/` or `Python/`; the `HAS_PYAUTOGUI` flag in `ralph_loop_harness.py` is set but never read). MCP `game_viewport` mode uses the default pawn camera (not your placed CameraActor); both modes can still produce small (1048x462) low-resolution images — a real limitation, but not a reason to fall back to desktop capture, which is what caused 41 wasted verification cycles from window-focus roulette before H-2 was promoted.

**Verification pipeline** — `core/visual_verifier.py`, `core/ralph_loop_harness.py`, `core/sleepwalker.py`, `Chimera/Python/verification_studio_runner.py` (all cite the H-2 prohibition in comments), which enforces:
1. AppActivate 'Unreal Editor' + 2s settle
2. **Foreground-window guard**: capture aborts (recording `aborted_wrong_window`) unless
   the foreground window title contains "Unreal Editor" — past runs graded a screenshot
   of the Vision/Testing Model interface itself
3. Verify file size > 100000 bytes
4. Send to Vision/Testing Model for verification — prefer **checklist mode**:
   `run_visual_verification(project_path, checklist=["criterion", ...], feature="Name")`
   does strict per-item YES/NO (unanswered = NO) instead of keyword sniffing

If the UE5 viewport renders black after MCP operations, reset with:
- `control_editor.set_view_mode("Lit")`
- `control_editor.set_game_view(enabled=False)`
- `control_editor.focus_actor("VerificationItem_Current")`

### Material Parameters via MCP
- `manage_asset.add_vector_parameter` creates **orphaned nodes** — NOT connected to material output pins
- `manage_asset.add_scalar_parameter` also creates **orphaned nodes**
- **Correct approach**: Use `system_control.execute_python` with single-line UE Python.
- The `execute_python` handler crashes on multi-line scripts at line ~22 — ALL code must be single-line semicolon-separated.

### Automatic Research Scheduling
After 2 failed attempts on any feature, automatically create a technical_research task in the Feature Ledger, record pathway_attempt mutations, and move to the next feature. See `Chimera/ORCHESTRATOR_PROMPT.md` § AUTOMATIC RESEARCH SCHEDULING. Future agents must query technical_research tasks before starting work.

## Research Mandate (2026-07-10)

**Every task requires research before execution.** Full policy: [`Chimera/docs/RESEARCH_MANDATE.md`](Chimera/docs/RESEARCH_MANDATE.md).

### Quick Reference
1. **Before any MCP call:** Query DNA graph + check MCP_PATHWAYS.md for traps
2. **Tier 1 tasks:** DNA query → follow pathway (5 min max)
3. **Tier 2+ tasks:** Complete research summary (§5 template in mandate doc), multi-source verification
4. **Post-execution:** Read-back verify, record deviations as surprises

### Enforcement
- Orchestrator validates research checklist before delegation
- Subtask `message` parameter MUST include embedded research summary for Tier 2+
- Postflight cannot declare phase complete without research compliance note
- New mutation types: `ResearchSummary`, `PathwayAttempt`, `DocumentationReview` (see §7.3 in mandate doc)

## Known Fixed Bugs

| # | Bug | Template | Fix | Category |
|---|-----|----------|-----|----------|
| 1 | Stale directories | build_orchestrator | Single canonical path | module_dependency |
| 2 | DEEPSPACETRADER_API | game_code_generator | CHIMERA_API | macro_error |
| 3 | AIController.h | build_orchestrator | Added AIModule | include_path |
| 4 | NiagaraFunctionLibrary.h | build_orchestrator | Added NiagaraCore | include_path |
| 5 | PCGVolume.h path | game_code_generator | Remove PCG/ prefix | include_path |
| 6 | Missing BeginPlay `}` | game_code_generator | Added closing brace | brace_mismatch |
| 7 | Duplicate code | game_code_generator | Replaced template | brace_mismatch |
| 8 | TickComponent/Tick mismatch | game_code_generator | Fixed to Tick(float) | signature_error |
| 9 | PCGVolumeManager APIs | game_code_generator | Removed runtime calls | module_dependency |
| 10 | GameMode redefinition | game_code_generator | Added scoping braces | signature_error |
| 11 | TEXT() dereference | game_code_generator | Removed stray `*` | macro_error |
| 12 | DockingComponent ctor | game_code_generator | Added empty ctor body | signature_error |
| 13 | g.mutate key mismatch → unknown_* junk | graphify_interface | Key aliases + rejection guards + typed record_* helpers | interface_contract |
| 14 | UBT output never captured (capture_output=False) | ubt_builder | Capture stdout+stderr; store excerpt + error lines in graph | build_observability |
| 15 | CommodityData price formula no-op (S/(S+1)−D/(D+1)≈0) | Economy/CommodityData | price = Base×clamp(pow(D/S, elasticity), 0.25, 4.0) | logic_error |
| 16 | FactionComponent TMap::operator[] assert crash + tier names seeded as factions | game_code_generator (faction template) | FindOrAdd + RelationshipForStanding ladder + DSL faction seeding, fixed at generator level | crash |
| 17 | Faction generation gated on narrative.factions; DSL defines game.factions | game_code_generator | Gate reads game.factions with narrative fallback | dsl_mapping |
| 18 | SaveGame/LoadGame were timestamp-only stubs | game_code_generator (save templates) | Real save/restore of InventoryTrade/Mission/Faction state + player transform | feature_gap |

## Key File Paths

| File | Purpose |
|------|---------|
| `docs/THE_COMPLETE_CHIMERA_DEVELOPMENT_CYCLE.md` | Full methodology, 13 schools, phases |
| `docs/chimera_dna_graph.json` | DNA graph (mutations, pathways, features) |
| `docs/MCP_PATHWAYS.md` | Working MCP tool sequences |
| `core/graphify_interface.py` | `g.query()` / `g.mutate()` interface |
| `core/game_generation_orchestrator.py` | Pipeline orchestrator |
| `run_deep_space_trader_pipeline.py` | Pipeline entry point |


## Sleepwalker & Rehearsal (added 2026-07-07)

When the NEXT list is empty, duty cycles run branch C2 before the pipeline fallback:
`python -m core.rehearsal --candidates-file docs/rehearsal_candidates.json --decide`
(veto-table decision -> recipe-carrying NEXT item). The game also plays itself:
`python -m core.sleepwalker --beats docs/beats/<demo>.beats.json --session <name>`
(PIE beat scripts, SimPlaytest evidence, CHIMERA_AGENT_SIM=1 sentinel — automation can
never record a human observation). Sim signals rank below human rejections everywhere.
Spec: Chimera/docs/SLEEPWALKER_DESIGN.md; new MCP pathways 22-26 in docs/MCP_PATHWAYS.md.

## No-blockers & anti-idle toolkit (2026-07-07)
Known blockers: `python -m core.unblock --ensure all`. Unknown: `python -m core.solver
--blocker "..." --context "<verbatim>"` (fix-or-draft). Heuristics: `python -m core.gardener
--tend` (delegated; human veto-after). Observation: `python -m core.collapse_proxy` (whole-
experience sweeps + provisional collapse — never ask the human per-feature). Docs-vs-code:
`python -m core.doc_audit`. Laws digest: GENERATION_PROTOCOL.md; full text CYCLE_PROMPT.md.

## Windows Shell & Command Reference (added 2026-07-09)

This machine runs coding agents (Pi, Claude Code) **natively on Windows** — not inside WSL.
Chimera's Python pipeline is installed against **native Python 3.14** (`C:\Python314\python.exe`).
WSL exists on this machine and has its own separate Python 3.12 with none of this project's
dependencies — if a command silently routes through WSL, `python -m core.X` imports will fail
or behave unpredictably even though the command "looks right." Pi's `bash` tool is explicitly
configured (`.pi/settings.json` → `shellPath`) to use **Git Bash**, not WSL's `system32\bash.exe`.
Do not "fix" that back to a bare `bash`/`/usr/bin/bash` value — on native Windows there is no
`/usr/bin/` root, so that path resolves to nothing and silently falls back to WSL.

### Two path formats — know which tool expects which
- **Pi/Claude built-in tools** (`read`, `write`, `edit`, `grep`, `find`, `ls`): native Windows
  paths. `E:\PythonChimera\Chimera\core\preflight.py` or `E:/PythonChimera/Chimera/core/preflight.py`
  (forward slashes are accepted and safer to type — no escaping).
- **Anything run through the `bash` tool** (Git Bash): POSIX-mounted paths. Drive `E:` becomes
  `/e/`, `C:` becomes `/c/`. So `E:\PythonChimera` → `/e/PythonChimera`.
- **Never use `/mnt/e/...`** — that is WSL's drive-mount convention. Git Bash mounts drives at
  `/e/`, not `/mnt/e/`. A command written for WSL will not resolve under Git Bash and vice versa.

### Python & git
- Always `python`, never `python3` — native Windows Python registers only as `python`.
- Invoke Chimera's `core/` tools as modules from the `Chimera/` directory, exactly as documented
  elsewhere in this file: `cd /e/PythonChimera/Chimera && python -m core.preflight`.
- `git` on this machine is PortableGit, already on PATH — no `/usr/bin/git` path exists natively.

### Writing files that contain backticks or `${...}` (template literals)
**Never** write a `.ts`/`.js` file containing template literals via a bash heredoc
(`cat > file <<'EOF' ... EOF`). Backticks trigger command substitution in POSIX shells —
anything between `` ` `` `...` `` ` `` gets *executed*, and its output silently splices into the
file in place of the intended literal text. This is exactly what happened to
`.pi/extensions/chimera-tools.ts`: every `execSync(\`cd ... && python3 ...\`)` call lost its
template-literal contents this way, leaving syntactically broken `let cmd = ;` lines. Use a
real file-write tool (Pi's/Claude's `write`/`edit`) instead — it writes literal bytes with no
shell interpretation in between.

### Executing native Windows things from Git Bash
- `.bat` / `.exe` files run directly by path: `./Chimera/lm.bat`. If a `.bat` needs `cmd.exe`'s
  own argument parsing, use `cmd //c script.bat` — note the **doubled** `//c`; a single `/c` gets
  mangled by Git Bash's automatic POSIX-to-Windows path conversion.
- UBT builds (`Build.bat ...`) run the same way — native batch files execute fine from Git Bash.

### What NOT to assume about Git Bash
It is MSYS2 userland on top of Windows, not a real Linux kernel: no `systemd`, no real `/proc`,
no `sudo`. Common coreutils (`ls`, `grep`, `find`, `rm`, `mv`, `cp`, `cat`, `sed`, `awk`) are real
(Git for Windows bundles them) and behave as expected. One real gotcha hit directly: `node -e`
with a POSIX path embedded inside the script string (e.g. `node -e "require('fs').readFileSync('/e/...')"`)
can get mangled by MSYS's automatic path conversion in a way a bare path argument wouldn't be —
use native Windows-style paths (`E:/...`) inside inline `node -e`/`python -c` script bodies, not `/e/...`.

## LSP servers for Pi/pi-shazam (added 2026-07-09)

All languages Shazam detects now have a real, working LSP server — portable installs, same
pattern as Node/Go above (download official release, extract, add to PATH):

| Language | Server | Install location |
|---|---|---|
| C++ (the actual game code) | clangd 22.1.6 | `C:\Users\allen\clangd-portable\clangd_22.1.6\bin\` |
| C# (`.Build.cs`/`.Target.cs`) | csharp-ls 0.25.0 | `dotnet tool` (`~\.dotnet\tools\`) |
| Rust | rust-analyzer 1.93.1 | `rustup component` (was a dangling shim before — `rustup component add rust-analyzer` actually installed it) |
| Go | gopls v0.22.0 | needed the Go toolchain installed first: `C:\Users\allen\go-portable\go1.26.5\` |
| Python | pyright-langserver | npm global (`pyright` package) |
| TypeScript | typescript-language-server 5.3.0 | npm global |
| JSON | vscode-json-language-server | npm global (`vscode-langservers-extracted`) |
| YAML | yaml-language-server 1.24.0 | npm global |

**clangd needs `Chimera/compile_commands.json` to understand UE macros/includes** — without it,
clangd can't resolve engine headers at all. Generated via UBT's VS Code project mode (works
without a separate Clang compiler install; `-Mode=GenerateClangDatabase` needs one, this doesn't):
```
"/c/Program Files/Epic Games/UE_5.8/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.exe" \
  -Mode=GenerateProjectFiles -VSCode -Project="E:/PythonChimera/Chimera/Chimera.uproject" -Game
cp Chimera/.vscode/compileCommands_Default.json Chimera/compile_commands.json
```
**Regenerate this after adding/removing source files or modules** — it's a snapshot, not live.
clangd will still report a handful of errors on UHT-reflected classes (`UCLASS`/`GENERATED_BODY`
mismatches) even with a correct database — that's expected: clangd doesn't run UnrealHeaderTool,
so it sees slightly different class shapes than the real UBT+UHT+MSVC build does. UBT/Build.bat
remains the authoritative compiler; clangd is for navigation/completion, not the gate.
