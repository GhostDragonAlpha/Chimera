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
| --- | --- | --- |
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
| Research department | scholar | HIRED 2026-07-07 — standalone; not yet wired into spiral_forks |
| Ideation / game design | muse | HIRED 2026-07-07 — standalone; proposals not yet merged into rehearsal_candidates.json |
| Creative direction / taste | visionkeeper | HIRED 2026-07-07 — standalone; not yet called from rehearsal's own scoring pass |

---

## TIER 1 — the named gaps (hire first)

> **Status update 2026-07-07**: all three named gaps below are now HIRED (see each entry's
> Evidence line) — the original commission's "nothing invents / judges / researches" is no
> longer true of the codebase, only of how the organs are *wired together*. What remains is
> integration (spiral_forks -> scholar, muse -> rehearsal_candidates.json, rehearsal ->
> visionkeeper), tracked per-entry below as "Wiring gap (honest, not yet done)". The heading
> and the Gardener's original quote above are kept as-is for history.

### 1. THE SCHOLAR — Research department (`core/scholar.py`)  **HIRED 2026-07-07**

(Doc-drift fix, same date: this entry said EMPTY after the organ was already built and
running — see commit `0762c63` "Implement Scholar organ (DREAM_ROSTER #1): research
retrieval system". Caught during `roster_and_bridge_progress` task processing.)
Nothing had ever consulted a source. The constitution says "research writes the exam"; in
practice the exam got invented from parametric memory.

- **Charter**: given a feature/topic: fetch and READ real sources — Research Campuses
  (docs/RESEARCH_CAMPUSES.md), web (capable sessions with WebSearch/WebFetch), and a LOCAL
  REFERENCE CORPUS (`research_corpus/` — cached pages/papers/docs) so local duty agents can
  research offline via retrieval. Output: the feature's EXAM (declared acceptance criteria,
  numeric parameters WITH CITATIONS), recorded as research_discovery nodes + the study guide
  on the feature node.
- **Evidence**: `core/scholar.py` (433 lines) — `retrieve_campus`, `retrieve_corpus`,
  `retrieve_web` (stub, capable-session WebSearch/WebFetch), `build_discovery_node`,
  `write_study_guide`, `scholar_brief_from_research`; CLI `--feature --topic --campus
  --technical-research --generate-brief --dry-run`. `graphify_interface.record_research()`
  typed helper + `graphify_record research` CLI subcommand added alongside it. Real, repeated
  execution evidence in the graph: **34 ResearchDiscovery nodes** as of this entry.
  `research_corpus/` seeded with 3 docs (dust-accumulation mask, lunar regolith reference,
  Niagara particle systems). First milestone (clear the pending dust-accumulation-mask
  `technical_research` item with 3+ cited sources) achieved — commit message reports 16+
  cited sources (12 campus + 4 corpus).
- **Wiring gap (honest, not yet done)**: `core/spiral_forks.py` does not import or call
  `core.scholar` yet — the "spiral_forks consumes scholar output instead of raw LM briefs"
  wiring below is still aspirational. Scholar runs standalone today; connecting it to
  spiral_forks is the remaining integration step.
- **Wiring (target, not yet built)**: spiral_forks consumes scholar output instead of raw LM
  briefs; the pending `technical_research` queue becomes the scholar's inbox; rehearsal gains
  research-type candidates (weak-OK when corpus-backed, capable when web-backed).

### 2. THE MUSE — Ideation / game design (`core/muse.py`)  **HIRED 2026-07-07**

(Doc-drift fix, same date: this entry said EMPTY after the organ was already built and
running — file committed at HEAD as of commit `3e08d14`. Caught during
`roster_and_bridge_progress` task processing.)
The system had never created a new idea; every feature came from the original DSL or the
human. Rehearsal picks among knowns; nothing widened the candidate pool.

- **Charter**: generate NEW feature/mechanic/content proposals from (a) playtest + witness
  evidence (what players do/miss), (b) the DSL and STORY_BIBLE, (c) scholar research on the
  genre. Each proposal lands as a rehearsal candidate WITH recipe + a `proposal` record —
  never self-executing. Wild-tier ideas explicitly welcomed (the fork system's "wild" seed
  generalized to whole features).
- **Evidence**: `core/muse.py` (156 lines) — `generate_proposals`, `record_proposals_to_graph`
  (via `graphify_interface.record_proposal()`), `write_proposals_to_candidates_file`; CLI
  `--dry-run`. Real execution evidence: **5 Proposal nodes** in the graph, matching the First
  milestone below exactly, plus `docs/muse_proposals.json` present on disk (proposals include
  "Regolith Dust Accumulation Visual Feedback", "Titan Run Gravity Shift Mechanics", "The
  Erisaid Audio Attunement Minigame", "Costless Life Bad Ending Trigger", and a fifth).
- **First milestone**: 5 proposals for the Regolith Yard / Titan Run arc, each with a one-cycle
  recipe — DONE, judged by visionkeeper (see #3) and ranked.
- **Wiring gap (honest, not yet done)**: `docs/muse_proposals.json` is a separate staging file
  — none of its 5 titles appear in `docs/rehearsal_candidates.json` yet, so `core.rehearsal
  --decide` cannot select them. The "enters the candidates file" wiring below has not run.
- **Wiring (target, not yet built)**: nightly (after dream) or on-demand; merge judged
  proposals into `docs/rehearsal_candidates.json` with vision_fit_multiplier applied.
- **Status update 2026-07-09**: wiring gap CLOSED — `core/muse.py::merge_muse_proposals_to_candidates()`
  implemented. Run `python -m core.muse --merge` to merge judged proposals into candidates file.
  `muse_proposals.json` entries into `rehearsal_candidates.json` so rehearsal can pick them.

### 3. THE VISIONKEEPER — Creative direction / taste (`core/visionkeeper.py`)  **HIRED 2026-07-07**

(Doc-drift fix, same date: this entry said EMPTY after the organ was already built and
running — file committed at HEAD as of commit `3e08d14`. Caught during
`roster_and_bridge_progress` task processing.)
Everything judged CAN-we (gates, grades, priors); nothing judged SHOULD-we. Rehearsal would
happily build a technically-perfect wrong thing.

- **Charter**: hold the vision (STORY_BIBLE "Those who love", the two Design Laws, the DSL's
  intent, the human's recorded temperatures) and SCORE every candidate/proposal for vision
  fit before rehearsal ranks it: `vision_fit` multiplier (0.2–1.5) with a one-line judgment,
  recorded. Also runs a taste pass on evidence (screenshots vs art direction) flagging drift
  ("the pads read as void-black, the bible says regolith-grey"). Never a hard gate — the
  human's sentence outranks it; a visionkeeper veto is one more line in the veto table.
- **Evidence**: `core/visionkeeper.py` (224 lines) — `score_candidate_for_vision_fit` scoring
  against the encoded `VISION_STORY_BIBLE` (core phrase, both Design Laws, failure ending, art
  bible palette, drift warning), `graphify_interface.record_visionkeeper_judgment()` typed
  helper. Real execution evidence: **14 VisionKeeperJudgment nodes** in the graph, scoring both
  rehearsal candidates (e.g. `Demo_Phase2_DemoTerminal` -> vision_fit 1.0, "System
  infrastructure; supports the vision but doesn't directly express it.") and muse proposals
  (e.g. "Costless Life Bad Ending Trigger" -> vision_fit 1.3, "Directly embodies Design Law #2
  / Observation Collapse; resonant with 'Those who love'.").
- **First milestone**: score the current candidate file + judge muse's proposals against the
  art bible — DONE for muse proposals and rehearsal candidates; the 8 provisionally-collapsed
  features' screenshots have not yet been run through a taste pass.
- **Wiring gap (honest, not yet done)**: `core/rehearsal.py` does not call `core.visionkeeper`
  — judgments exist but are not yet a multiplier inside rehearsal's own scoring pass, and there
  is no nightly taste pass on screenshots yet.
- **Wiring (target, not yet built)**: rehearsal calls it during scoring; muse proposals must
  carry its judgment before entering the candidates file; nightly taste pass on new
  screenshots.

---

## TIER 2 — the departments that make it a real studio

### 4. BRIDGE ENGINEER (`core/bridge_engineer.py` + capable cycles)  **PARTIAL — 2/4 named backlog items fixed + COMMITTED 2026-07-07; Niagara authoring (3rd item) diagnosed but NOT fixed 2026-07-08; still no dedicated organ**

(Status update 2026-07-07, `roster_and_bridge_progress` task: the line below describing "one
failed reverted attempt" is now stale for `add_anim_notify`/`get_anim_sequence_info` — kept
below for history, corrected here.)
The McpAutomationBridge NOT_IMPLEMENTED/facade backlog (add_anim_notify, get_anim_sequence_info,
Niagara authoring, exec-chain quirks) blocks whole departments (VFX, animation).

- **Fixed, independently re-verified live twice, and now COMMITTED**:
  `add_anim_notify` and `get_anim_sequence_info` are real implementations now (not facades) in
  `McpAutomationBridge_AnimationAuthoringHandlers.cpp` — the handler actually reached via
  `IsAnimationAuthoringAction()` routing through the `animation_physics` tool — with matching
  fixes also applied in `McpAutomationBridge_AnimationHandlers.cpp` for consistency. First
  landed and live-verified by the session that wrote the fix (`pathway_attempt_6b3829ef3f6ea25d`,
  `pathway_attempt_bc47c3c55923ccd0`; see MCP_PATHWAYS.md #27). Independently RE-verified from
  scratch by a later `roster_and_bridge_progress` subagent (did not trust the log — re-derived):
  confirmed the compiled `UnrealEditor-McpAutomationBridge.dll` (mtime 18:57:19) postdates both
  edited source files (18:55:34, 18:48:06), then ran a fresh live round trip against the running
  editor — baseline `get_anim_sequence_info` (0 notifies) → `add_anim_notify` with an explicit
  `time` param and a distinctly-named test marker → read-back (1 notify, correct time preserved,
  not silently zeroed) → disk-mtime-confirmed persistence → `git checkout --` revert →
  full editor restart to resync in-memory state → final read-back confirms clean (0 notifies
  again, git status clean). Recorded as `pathway_attempt_4bf27f49ed497dd1` and
  `pathway_attempt_f938ca71b7dd2a7c`. **Update 2026-07-08 (`roster_and_bridge_progress`, 3rd
  dispatch)**: the "fix exists only uncommitted" risk this entry warned about twice is resolved —
  `git show HEAD --stat` confirms both `.cpp` files landed in commit `2c074d5` ("chore: add wind
  system, dust accumulation materials... update DNA graph and documentation"), alongside this
  file and `MCP_PATHWAYS.md`. `git status`/`git diff` at session start showed these files clean
  (not `M`), and the current HEAD source still contains the real (non-stub) `add_notify`/
  `add_anim_notify` and `get_anim_sequence_info` branches — re-confirmed by reading the live file,
  not just trusting the commit message. This was almost certainly landed by the project's own
  perpetual orchestrator (per CLAUDE.md's "Perpetual orchestrator v2" commits, active in this
  window), not by a human `git commit`, but it is genuinely durable now either way.
- **Niagara authoring (backlog's 3rd named item) — DIAGNOSED with fresh live evidence 2026-07-08,
  still NOT FIXED; do not read the paragraph below as a fix.** SUCCESSOR_RUNBOOK's TRAP text
  ("create_niagara_system / add_emitter_to_system / add_*_module / set_niagara_parameter all
  return success and do NOTHING. get_niagara_info reports emitterCount=0 even for working
  systems. validate_niagara_system says isValid for broken ones.") was re-tested live against the
  actually-running editor rather than trusted at face value (confirmed first that the compiled
  `UnrealEditor-McpAutomationBridge.dll`, mtime 2026-07-07T18:57:19, postdates
  `McpAutomationBridge_NiagaraAuthoringHandlers.cpp`/`_EffectHandlers.cpp`, both untouched since
  2026-06-30 — the live editor is running the code on disk today, not something stale). Three
  live MCP round trips against the running editor (`manage_effect`), each with disk/asset
  read-back, not just `success:true`:
  1. `get_niagara_info` on the **known-good engine template** `FountainLightweight` (proven to
     render real particles via `spawn_niagara`, MCP_PATHWAYS.md #21b) reports `emitterCount=0,
     emitters=[]` — reproducing the TRAP's "lying instruments" claim on a system that is
     definitely NOT empty. (`pathway_attempt_f02d476674795953`)
  2. `create_niagara_system` (name+path under a scratch `/Game/_McpProbe*/` folder, deleted after
     each test) returns `success:true` and genuinely creates a loadable `NiagaraSystem` asset
     (confirmed via `manage_asset search_assets`) that `spawn_niagara` can place in the level as a
     real `NiagaraActor` with a `NiagaraComponent0` (confirmed via `control_actor
     get_components`) — no error anywhere in the chain. (`pathway_attempt_5e56a84a847139dc`,
     result recorded as `success_unverified`, not `success` — see point 4.)
  3. `get_niagara_info` on that SAME freshly-created system (which the C++ at
     `NiagaraAuthoringHandlers.cpp:344-373` explicitly attaches one `DefaultEmitter` handle to,
     via `AddEmitterHandleDirect`, before returning success) **also** reports `emitterCount=0`.
     Tested both the undotted (`/Game/.../Name`) and fully-qualified dotted
     (`/Game/.../Name.Name`) path forms — identical result either way, ruling out path format as
     a confound. `validate_niagara_system` on the same asset returns `isValid:true` but
     `warnings:["System has no emitters."]` — it calls the exact same
     `System->GetEmitterHandles()` accessor as `get_niagara_info`, so this is the same bug
     surfacing twice, not independent confirmation. (`pathway_attempt_f02d476674795953`,
     `pathway_attempt_7c9316ed7278b9d9`)
  4. **Conclusion, precisely scoped**: `get_niagara_info`/`validate_niagara_system`'s
     `GetEmitterHandles()`-based introspection is unreliable/always-empty regardless of the
     underlying system's real state — reproduced on a definitely-non-empty engine template AND a
     freshly-authored system in the same test run. This means the TRAP's original framing
     (create_niagara_system "does nothing") is **not proven** by the evidence gathered — the
     write path visibly does something real (asset exists, loads, spawns, attaches a component)
     — but it is also **not disproven**: whether the attached `DefaultEmitter` handle is a
     functionally real, particle-emitting emitter or a cosmetically-attached empty one could not
     be determined this session, because the only introspection tools available are the ones just
     proven unreliable. Resolving that needs a foregrounded `editor_viewport` screenshot
     comparing the authored system's spawn against a known-working template's spawn side by side
     (H-2/pathway 25 discipline) — genuinely the next step, not attempted this session (scope
     stop, not an oversight: two distinct introspection-layer bugs were already confirmed live,
     matching SUCCESSOR_RUNBOOK PRIME DIRECTIVE 6's "stop after two, do not invent a third"
     spirit, and a screenshot-based render check plus any actual C++ fix is a materially bigger
     unit of work than one dispatch should improvise blind). **No code was changed for Niagara
     authoring this session** — this paragraph is diagnosis only, sharper and live-dated evidence
     replacing the previous vague TRAP citation, not a landed fix. Root cause of the
     `GetEmitterHandles()` unreliability itself remains OPEN (candidate hypotheses considered but
     not confirmed: async/deferred load state, a "lightweight" template using a different
     internal representation than classic `EmitterHandles`, or a genuine `AddEmitterHandleDirect`
     write-path defect — engine header at
     `Engine/Plugins/FX/Niagara/Source/Niagara/Classes/NiagaraSystem.h` confirms
     `GetEmitterHandles()`/`EmitterHandles` are plain always-present UPROPERTYs, not
     editor-only-gated, so the accessor itself is not obviously wrong by inspection alone).
- **Honestly still open**: (1) Niagara authoring's actual fix (see above — diagnosis only, still
  broken). (2) "exec-chain quirks" (4th named item) — not investigated by any session yet; status
  unknown. (3) No `core/bridge_engineer.py` organ file exists — every fix/diagnosis so far has
  been a direct capable-session effort, not output of a dedicated queue-owning organ per the
  Casting Rule; the backlog still has no systematic owner.
Charter (unchanged): own the backlog as a queue, implement handler-by-handler with
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

### 13. THE CRITIC — Games critic / benchmark analyst (`core/critic.py`)  **HIRED 2026-07-07**

result_grader.py/ProfessorGPA measure pure technical correctness (test pass rate, stability,
design checklist, spec fidelity) and never comparative enjoyment — nothing answers "does this
feel like a AAA game, or a tech demo?" Charter: given a feature, pull its real recorded
evidence (latest record_grade letter + reasoning, FeatureUpdate parameters, SurpriseMoments,
Observation verdicts, ResearchDiscovery criteria) and hand it to an LM Studio call that names
2-4 genre-appropriate reference titles from the project's benchmark pool (Elite Dangerous, No
Man's Sky, Star Citizen, EVE Online, Subnautica) and scores seven axes — the design-standard
checklist's five (Feedback, Consistency, Meaningful Parameters, Fail-safety, Balance Sanity)
plus two critic-only axes (Production Polish, Moment-to-Moment Feel) — producing an
`overall_percentage` (estimated player-enjoyment percentile vs. the named set, not a
commercial-success odds) with named comparisons and a rationale. ADVISORY ONLY — every print
and every recorded node carries "ADVISORY ONLY — LM-generated estimate, does not gate the
pipeline, does not substitute for human observation"; it never blocks result_grader, GPA, or
any gate, exactly like visionkeeper's vision_fit score. Wiring: one preflight.py line
surfacing the latest judgment (feature, percentage, top benchmark title); recorded as
CriticJudgment nodes via `record_critic_judgment`. First milestone: judge Ground_Sand_Particles
— its B 79.3 technical grade next to it visibly reading as a white fountain, not sand, is
exactly the proxy-vs-target gap this organ exists to surface in plain percentage terms.

---

## TIER 3 — hire as the game grows

| Seat | Organ sketch |
| --- | --- |
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
