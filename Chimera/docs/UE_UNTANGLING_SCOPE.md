# UE untangling — SCOPE + EXECUTION LOG

> **BACKEND REMOVED 2026-07-24.** 12 modules, 12,659 LOC deleted; every survivor imports
> cleanly; zero dangling imports (verified). What follows is the scope that guided it, kept
> as the record. ONE scope correction, found during execution: `generator_guard` was NOT the
> general guard the scope assumed — it guarded `Source/Chimera/ProceduralGenerated/` (the UE
> C++ output dir) specifically, so with the generator gone it was a no-op. It was removed too,
> and preflight/postflight de-referenced (their generator-guard blocks were fail-safe
> try/except, excised cleanly). The DSL was KEPT (operator's call), as recommended.

---


> Scoped 2026-07-24. The backlog carried "remove the UE-era subsystem" as a large, scary
> item. Before touching it, this maps what is actually there. The headline: **it is far
> smaller and more separable than the label implied.** "The UE code" is essentially one
> thing — a C++ **generation backend** — and it is nearly an island. The game-spec DSL and
> the general guards around it are engine-agnostic and stay.
>
> This is a plan, verified against the real import graph, not a proposal to start deleting.

---

## The finding that reframes it

The naive signal (UE-C++ marker density) is USELESS for separation: the whole project was
UE-native until 2026-07-23, so current infrastructure is saturated with UE references in
strings, enums, and comments. `graphify_interface.py` (the DNA graph API, imported by **67**
modules) and `rep_engine.py` (the rep gate) both score "UE-heavy" and are unambiguously
current. **You cannot find the UE subsystem by grepping for UE words.**

The signal that DOES separate it: which modules **emit C++ syntax** (`GENERATED_BODY()`,
`UCLASS(`, `CreateDefaultSubobject`, `#include "`). By that test there is exactly **one**
true generator, and a small ring of build/orchestrate/fix modules around it.

---

## The map

### REMOVE — the C++ generation backend (~11,650 LOC, ~7 modules)
These exist only to turn a game spec into Unreal C++ and build it. UE is retired; they are dead.

| module | LOC | role |
|---|---|---|
| `core/game_code_generator.py` | 9,477 | emits the UE C++ (the one true generator) |
| `core/build_orchestrator.py` | 727 | drives UBT builds |
| `core/game_generation_orchestrator.py` | 629 | orchestrates spec → C++ → build |
| `core/incremental_generator.py` | 275 | incremental C++ regen |
| `core/build_validator.py` | 271 | validates a UBT build |
| `core/code_generation_orchestrator.py` | 272 | a second orchestration layer |
| `core/dna/auto_fixer.py` | 166 | fixes generator-owned C++ after a failed build |

Plus the demos/utilities that exist only to drive them (die with the ring):
`code_generation_demo.py`, `game_generation_demo.py`, `restore_deleted_files.py`.

### RETAIN — engine-agnostic, wrongly lumped in
| module | why it stays |
|---|---|
| `core/dsl_game_parser.py` (967) + `dsl_grammar_validator.py`, `dsl_mcp_bridge.py` | the DSL is the **game-spec language** (narrative/gameplay/world/ui/audio) — a concept, not an engine. Its UE-C++ *backend* goes; the spec parser is reusable for any backend (including the matter/genome pipeline). **Decision needed:** keep the DSL as the spec front-end, or retire it too? |
| ~~`core/generator_guard.py`~~ | **CORRECTED + REMOVED.** On inspection it guarded `Source/Chimera/ProceduralGenerated/` (UE C++ output) specifically, not generated files in general — a no-op once the generator went. Deleted; preflight/postflight de-referenced. |

### RETAIN — current infra that merely *references* UE (a SEPARATE, later pass)
`graphify_interface`, `rep_engine`, `helm`, `wellspring`, `preflight`, `postflight`, the gates,
`why`, `council`, … These carry UE-flavored strings/enums from the project's history. They are
**not** part of the generation ring and none of them import it (helm/wellspring do NOT reach
into the generators). Cleaning their UE *wording* is a delicate, larger, string-level pass —
**not** deletion, and explicitly out of scope for the backend removal.

---

## The cut points (verified against the import graph)

Only these current modules reach INTO the ring, and each resolves cleanly:

| edge | disposition |
|---|---|
| `preflight.py` → `generator_guard.deterministic_flags` | **keep** — generator_guard stays (generalized) |
| `postflight.py` → `generator_guard.check/enforced` | **keep** — same |
| `dsl_grammar_validator.py`, `dsl_mcp_bridge.py` → `dsl_game_parser` | **keep** — dsl_game_parser stays |
| `code_generation_demo.py`, `game_generation_demo.py`, `restore_deleted_files.py` → the generators | **remove** — the demos die with the ring |

**There is NO edge from load-bearing current infra (helm, rep_engine, the trainer, matter,
the genome pipeline) into the C++ generators.** The ring is an island reached only by demos,
the DSL tooling (which stays), and generator_guard (which stays). That is why this is
tractable.

---

## Safe order of operations (when the work is greenlit)

1. **Decide the DSL question** (the one real design call): keep `dsl_game_parser` as the
   engine-agnostic spec front-end, or retire the DSL with its backend? This changes the
   blast radius. Recommendation: KEEP it — a spec language that produces matter-genome
   directives instead of C++ is exactly the kind of front-end the current pipeline could use.
2. **Sever generator_guard from the C++ specifics** — make it guard "generated-owned files"
   generally (it already half-does; the auto-decomposer domains are generated). preflight/
   postflight keep working unchanged.
3. **Delete the demos/utilities** (`*_demo.py`, `restore_deleted_files.py`).
4. **Delete the generation ring** (the 7 REMOVE modules). Nothing current imports them now
   that steps 1–3 are done. Run the import-graph check (`tools/ue_ring_check.py`) to confirm zero
   dangling imports before committing.
5. **Retire `game_generation_orchestrator` from any launcher/doc** that still names it.
6. **Later, separately:** the UE-string de-referencing pass across current infra — a careful,
   string-level cleanup that does NOT delete modules. Its own scope; not bundled here.

---

## Honest estimate

- **The backend removal (steps 1–5): one focused session.** ~12k LOC deleted across ~10
  files, ~4 cut points to resolve, all verified severable. Low risk with the import-graph
  check as the gate.
- **The UE-string cleanup (step 6): a larger, more delicate pass** touching 60+ current-infra
  files at the string/enum/comment level. Higher care, lower urgency (it is cosmetic/naming,
  not correctness), and genuinely separate work.

The scary version — "a huge entangled UE subsystem woven through current infrastructure" —
is not what the graph shows. There is a clean ~12k-LOC island and a separate, optional
naming cleanup. The verification (`tools/ue_ring_check.py`) is the proof, and should be re-run
as the pre-delete gate.
