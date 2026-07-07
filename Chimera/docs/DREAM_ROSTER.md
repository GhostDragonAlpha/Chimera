# The Dream Roster — a full studio's cast and crew as Chimera organs

> Commissioned by the Gardener 2026-07-07: "we need the whole cast and crew of the company —
> it's not creating new ideas, it's not judging what we should do, and I haven't seen it do
> any research at all." This roster maps every seat a studio like Activision fills onto the
> proven organ architecture (one `core/<organ>.py` + at most four touchpoints — see
> GENERATION_PROTOCOL). Status: **HIRED** (exists), **PARTIAL** (half the job), **EMPTY** (missing).
>
> The three named gaps are Tier 1: the system executes and verifies superbly, but nothing
> INVENTS (ideation), nothing JUDGES SHOULD-WE (taste/direction), and nothing RESEARCHES
> (sources are never consulted — fork "research" is the local model reciting its memory).

## The crew already hired (consider what we have)

| Studio seat | Organ | Status / gap |
|---|---|---|
| Production coordinator (dailies, handoffs) | preflight / postflight / task_progress | HIRED |
| Retrospective facilitator | dream_loop + heuristic_distiller | HIRED |
| Process & standards owner | gardener (delegated authority) | HIRED |
| QA smoke playtester | sleepwalker + witness + beats | HIRED — happy-path only |
| Sprint planner (next move) | rehearsal (priors, veto table, freshness) | HIRED — single-step horizon |
| IT / DevOps / firefighter | unblock + solver | HIRED |
| UX research ops (attribution) | collapse_proxy (whole-experience sweeps) | HIRED |
| QA lead (grading rubric) | result_grader (zero-LM) | HIRED |
| Technical writer / auditor | doc_audit | HIRED |
| R&D prototyper | spiral_forks | PARTIAL — briefs come from model memory, not sources |
| Build engineer | build_orchestrator + pipeline | HIRED |
| Gameplay programmer (template-driven) | game_code_generator | HIRED — new systems need capable sessions |
| Archivist | graph_compactor | HIRED |
| Performance analyst | telemetry_probe | PARTIAL — fps/crash/growth only |
| Balance analyst | chimera-balance mode | PARTIAL — read-only analysis, proposes nothing |
| Engineering modes (code/debug/ue5/architect/orchestrate) | .roomodes + Claude modes | HIRED |

---

## TIER 1 — the named gaps (hire first)

### 1. THE SCHOLAR — Research department (`core/scholar.py`)  **EMPTY — the loudest gap**
Nothing has ever consulted a source. The constitution says "research writes the exam"; in
practice the exam gets invented from parametric memory.
- **Charter**: given a feature/topic: fetch and READ real sources — Research Campuses
  (docs/RESEARCH_CAMPUSES.md), web (capable sessions with WebSearch/WebFetch), and a LOCAL
  REFERENCE CORPUS (`research_corpus/` — cached pages/papers/docs) so local duty agents can
  research offline via retrieval. Output: the feature's EXAM (declared acceptance criteria,
  numeric parameters WITH CITATIONS), recorded as research_discovery nodes + the study guide
  on the feature node.
- **Wiring**: spiral_forks consumes scholar output instead of raw LM briefs; the pending
  `technical_research` queue becomes the scholar's inbox; rehearsal gains research-type
  candidates (weak-OK when corpus-backed, capable when web-backed).
- **First milestone**: clear the pending item (procedural dust-accumulation mask) with 3+
  cited sources and a written exam; seed `research_corpus/` with the campus list.

### 2. THE MUSE — Ideation / game design (`core/muse.py`)  **EMPTY**
The system has never created a new idea; every feature came from the original DSL or the
human. Rehearsal picks among knowns; nothing widens the candidate pool.
- **Charter**: generate NEW feature/mechanic/content proposals from (a) playtest + witness
  evidence (what players do/miss), (b) the DSL and STORY_BIBLE, (c) scholar research on the
  genre. Each proposal lands as a rehearsal candidate WITH recipe + a `proposal` record —
  never self-executing. Wild-tier ideas explicitly welcomed (the fork system's "wild" seed
  generalized to whole features).
- **Wiring**: nightly (after dream) or on-demand; visionkeeper judges its output before it
  enters the candidates file.
- **First milestone**: 5 proposals for the Regolith Yard / Titan Run arc, each with a one-cycle
  recipe, judged and ranked.

### 3. THE VISIONKEEPER — Creative direction / taste (`core/visionkeeper.py`)  **EMPTY**
Everything judges CAN-we (gates, grades, priors); nothing judges SHOULD-we. Rehearsal would
happily build a technically-perfect wrong thing.
- **Charter**: hold the vision (STORY_BIBLE "Those who love", the two Design Laws, the DSL's
  intent, the human's recorded temperatures) and SCORE every candidate/proposal for vision
  fit before rehearsal ranks it: `vision_fit` multiplier (0.2–1.5) with a one-line judgment,
  recorded. Also runs a taste pass on evidence (screenshots vs art direction) flagging drift
  ("the pads read as void-black, the bible says regolith-grey"). Never a hard gate — the
  human's sentence outranks it; a visionkeeper veto is one more line in the veto table.
- **Wiring**: rehearsal calls it during scoring; muse proposals must carry its judgment;
  nightly taste pass on new screenshots.
- **First milestone**: score the current candidate file + judge the 8 provisionally-collapsed
  features' screenshots against the art bible.

---

## TIER 2 — the departments that make it a real studio

### 4. BRIDGE ENGINEER (`core/bridge_engineer.py` + capable cycles)  **PARTIAL (backlog exists, nobody owns it)**
The McpAutomationBridge NOT_IMPLEMENTED/facade backlog (add_anim_notify, get_anim_sequence_info,
Niagara authoring, exec-chain quirks) blocks whole departments (VFX, animation). One failed
reverted attempt exists. Charter: own the backlog as a queue, implement handler-by-handler with
UBT verbatim evidence, read-back verification, pathway records. Every fix un-demotes dead-end
candidates automatically (no-dead-ends law already wired).

### 5. CHAOS TESTER (`core/chaos.py`)  **EMPTY**
Sleepwalker walks the happy path. Chaos walks everything else: random-input fuzzing in PIE,
boundary probing (walk off the world, spam interactions, alt-tab storms), soak-with-abuse.
Output: SimPlaytest-style records with crash/hang evidence; every crash becomes a beat in the
regression suite. Weak-OK once written (pure MCP).

### 6. REGRESSION CURATOR (`core/regression.py`)  **EMPTY**
Every human rejection, chaos crash, and solver fix should automatically become a permanent
beat/test. Charter: mine rejections + fixed blockers nightly, emit/extend beat scripts and
FeatureAcceptanceTests entries, keep the suite pruned (freshness law applies to tests too).

### 7. AUDIO SOURCER (`core/audio_sourcer.py`)  **EMPTY — kills a standing BLOCKED-ON-ASSETS**
Ground_Sand_Sound has waited on a human CC0 import for days. Charter: search/download license-safe
audio (CC0 packs), verify license, import via editor automation, record provenance. Capable
sessions with web; the license ledger is non-negotiable (records the source + license per asset).

### 8. LIGHTING ARTIST (`core/lumen_rig.py`)  **EMPTY — the dark-pads pain is its first ticket**
Mood-driven light rigs per scene (key/fill/rim recipes already proven in L_VerificationStudio
pathways), exposure sanity checks on screenshots, day/night variants. Declared pain
phase_4d2da4e032a4aa07:P1 (pads read near-black) is its first work item.

### 9. PRODUCER (`core/producer.py`)  **EMPTY**
Rehearsal is a sprint-picker; nobody plans a milestone. Charter: hold the roadmap (Demo 1 →
Session B → Titan Run → beyond) as a dependency graph, measure velocity from phase records,
forecast, and re-order the candidates file weekly so rehearsal's single-step choices serve a
multi-week arc. Reports in one table; the human steers with one sentence.

### 10. PERFORMANCE ENGINEER (`core/perf_engineer.py`)  **PARTIAL → deep**
telemetry_probe reads fps/crash/growth. Charter: per-system budgets (Niagara, anim, draw calls
via `stat` captures + Unreal Insights traces), regression detection between builds, budget
table per feature. Its findings become rehearsal priors automatically.

### 11. ART DIRECTOR (`core/art_director.py`)  **EMPTY**
Style-bible enforcement: palette extraction from screenshots vs the DSL's color_palette,
composition checks on demo shots, reference-matching (research_references/ finally gets used).
Vision-LM tertiary layer, engine hard-facts first (material/palette read-backs).

### 12. TRAILER DIRECTOR (`core/trailer.py`)  **EMPTY, cheap, morale-critical**
Every clean sleepwalk can end with a beauty pass: BugItGo cinematic path, screenshot sequence,
ffmpeg into a nightly 20-second gif/mp4 dropped in Saved/Trailers/. The human wakes to a daily
trailer of what the game became overnight — the single best lure for whole-experience
temperatures.

---

## TIER 3 — hire as the game grows

| Seat | Organ sketch |
|---|---|
| Level designer | `level_smith.py` — composes spaces from beat requirements + scholar reference; greybox via proven geometry pathways, save-proof ritual |
| Narrative designer | `narrator.py` — quests/dialogue from STORY_BIBLE; first consumer of the cinematic-resonance workflow when invoked |
| Systems/economy designer | promote chimera-balance from analyst to designer: proposes DSL parameter changes as candidates with simulated outcomes |
| UX designer | `ux_smith.py` — HUD/menu/onboarding heuristics; consumes witness confusion signals (backtracking, idle spikes) |
| Character/anim engineer | blocked on bridge engineer (anim handlers); then gait/notify authoring with read-backs |
| VFX artist | blocked on bridge engineer (Niagara authoring facade); until then spawn-only palette |
| Localization | far future; strings audit organ |
| Compatibility/cert | packaged-build (not PIE) nightly verification once a shippable target exists |
| Community/analytics | witness chronicles → funnels/heatmaps when there is more than one player |

---

## Casting rule (how every hire happens)

Each seat = one `core/<organ>.py` following the organ recipe (CLI convention, typed records,
--dry-run, exit-0, doc_audit-clean) + at most: one dream_loop call, one preflight line, one
candidates entry, one CYCLE_PROMPT constant. Tier-1 organs are LM-heavy (capable sessions
write them; local agents run them). Nothing self-executes into the game without the existing
gates; nothing outranks the human's sentence. The roster is itself a rehearsal input: the
three Tier-1 hires are seeded as candidates.
