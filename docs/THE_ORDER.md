# THE ORDER — what runs, in what sequence, and what is currently broken

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY MEMBRANE IS A THEORY. STATE IT BEFORE YOU BUILD IT.** Three parts, all three
> required: a **STATEMENT** someone could disagree with · a **PREDICTION** you have not measured
> yet · a **FALSIFIER** named *before* the run. **A description survives any result; a theory can
> lose.** No falsifier, no build.
>
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
>
> **RULE 0 IS ENFORCED AT S-1 VALIDATE** — every port tested alone, and `port_test()` REFUSES to
> register a test that names no falsifier. The model it feeds: `docs/THE_COMPILER.md` — ports →
> primitives → programs → parser → runtime → calibration.
>
> **[docs/THE_LAW.md](../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> Audit 2026-07-23, traced empirically (imports, readers/writers, file existence) rather
> than from memory. The complaint that produced it: *"we've got all the pieces but they're
> not in order."* That is accurate. The pieces are good; the wiring is not.

---

## A. THE CANONICAL ORDER — one path, no branches

This is the whole system as a single sequence. Anything not on this path is either a
helper or a duplicate.

```
 1  ACQUIRE      a scan (.splat/.ksplat/.ply) or an authored asset (GLB)
                 -> WorldModel/training_data/downloads/          [gitignored]

 2  RECOVER      Construction/export_genome.py
                 cluster a scan -> per-material splat-configuration DISTRIBUTION
                 (size, aniso, R, G, B, opacity; each mean + p10..p90)
                 -> Chimera/docs/matter/recovered_genomes.json   ** THE LIBRARY **

 2b MERGE        Construction/export_genome.py :: merge_specimens()
                 >=2 scans of ONE KIND -> a CLASS genome carrying between_std /
                 within_std, which is what makes heritability measurable

 3  COMPOSE      Chimera/core/train_splat_compositions.py
                 train which splat TYPES reproduce each material's measured
                 distribution; writes the winner back into
                 -> Chimera/docs/matter/matter_library.json  (splat_composition.layers)

 4  BUILD        pick ONE of the six directions (docs/THE_WORKFLOW.md section 6)
                 objects : Chimera/core/progeny.py
                           load_genome -> recombine(A,B) -> build_child(form=)
                           -> place() / scatter(height_fn=)  -> pose(verb=)
                 surfaces: Chimera/core/membrane_shapes.py  (container) + clothe()
                 world   : Chimera/core/rebuild_world.py    (terrain + shelter)

 5  SEE IT       Chimera/core/render_world.py :: render_orbit()
                 -> Chimera/Saved/SplatEmit/*.png       LOOK AT IT. Logs are not proof.

 6  THE LOOP     Chimera/core/membranes.py + core/bricks.py      [added 2026-07-23]
                 address the world as nested membranes; a cell's six directions are
                 its PORTS. work_queue() enumerates unfilled studs, propose() breeds
                 admissible candidates, place() mates one, drive_section() runs the
                 whole thing -- 6,037 bricks/sec, deterministic by coordinate.
                 Full account: docs/THE_WORKFLOW.md section 7.
```

**One writer rule:** step 2 owns `recovered_genomes.json`. Step 3 owns
`matter_library.json`. Nothing else may write either file.

---

## B. WHAT IS ALREADY TRUE (verified, not assumed)

- **The spine is connected end to end.** Every arrow above resolves to a file that exists
  and is imported by the next stage.
- **The heritability gap is CLOSED.** `recovered_genomes.json` now holds **5 class genomes
  built from 2+ specimens** — `bonsai_vegetative`, `stump_wood`, `bicycle_metallic`,
  `plush_fabric`, `truck_metallic` — each carrying `between_std`, `within_std` and
  `specimen_means`. That was the highest-value open item this morning. It is done.
- Plus **8 single-specimen genomes** (`cluster_00..07`, from the truck scan). Their h² is
  correctly undefined.

---

## C. WHAT IS OUT OF ORDER — 9 findings, ranked

| # | Finding | Severity |
|---|---|---|
| 1 | ~~CLOSED 2026-07-24~~ — **`run_sequential.py` retired** with the whole dead sequential-automation layer (orchestrator already deleted, nothing imported it). | ~~breaks on run~~ |
| 2 | ~~CLOSED 2026-07-24~~ — **`sequential_orchestrator.py` layer retired**; the docs no longer point at it (canonical list: `THE_BACKLOG.md`). | ~~breaks on run~~ |
| 3 | ~~CLOSED 2026-07-24~~ — **triplicate agents deleted** with the retired layer (`integration_agent{,_fixed,_old}`, `recombination_agent{,_fixed,_old}`). | ~~high~~ |
| 4 | **Seven writers to `recovered_genomes.json`** — 3 recombination agents, `train_splat_compositions`, `export_genome`, `phase3_recombination_testing`, `process_materials_pipeline`, `process_more_materials`. No locking, no ownership. | **high — data integrity** |
| 5 | **~1,067 lines of root-level duplicates** doing step 2's job: `process_materials_pipeline.py` (340), `process_more_materials.py` (302), `phase3_recombination_testing.py` (425). | **high** |
| 6 | ~~CLOSED 2026-07-24~~ — **`research_agent.py`/`validation_agent.py` deleted** with the retired layer (they imported no pipeline because the layer was abandoned). | ~~medium~~ |
| 7 | ~~CLOSED 2026-07-23~~ — **Every Pi agent was handed 8 Unreal editor tools** (`.pi/extensions/mcp-bridge.ts`, `mcp-pathways-index.ts`) while its prompt says UE is retired. | medium |
| 8 | ~~CLOSED 2026-07-24~~ — **"both ways" was FALSE.** The import graph is ACYCLIC: Chimera/core imports nothing upward. The one real defect was 13 files with a hardcoded `sys.path.insert(0, "E:/PythonChimera")` (machine-specific, breaks on clone) -- now file-relative. Two homes with a clean one-way dependency is normal layering, not a tangle; no migration or guard needed. | ~~medium~~ |
| 9 | **Two schemas coexist** in the genome file (single-specimen vs class). Benign — class is a superset — but undocumented, so a reader cannot tell which it has. | low |

---

## D. THE FIX LIST, in dependency order

1. **Point `run_sequential.py` at the files that exist** (`agents/*_agent.py`), or delete it
   and keep one launcher. Right now it cannot run at all. *(finding 1)*
2. **Correct the docs' orchestrator name** in `ONBOARDING.md` + `THE_WORKFLOW.md`, or create
   the file they name. Agents are being told to run something that was never written. *(2)*
3. **Delete `_old` and `_fixed`.** Keep one of each, chosen by reading the diffs, not by
   filename. *(3)*
4. **Enforce the one-writer rule.** `export_genome.py` writes the genome library;
   everything else reads. The other six writers become readers or get deleted. *(4)*
5. **Delete the three root-level duplicates** once their unique behaviour (if any) is folded
   into `export_genome.py`. *(5)*
6. **Wire or delete** `research_agent.py` / `validation_agent.py` — an agent that imports no
   pipeline is not doing pipeline work. *(6)*
7. **Remove the UE MCP extensions** from `.pi/extensions/`. A retired pipeline is not retired
   while its tools still load. *(7)*
8. **Choose one home** for the pipeline and move the other into it. *(8)*
9. **Document the two genome schemas** in `SPLAT_DNA_WORKFLOW.md` §7.5. *(9)*

---

## E. WHY IT DRIFTED — the pattern worth not repeating

Every finding above has the same shape: **a new thing was added beside the old thing instead
of replacing it.** Renamed scripts left their launcher pointing at ghosts; fixed agents were
saved as `_fixed` beside the broken ones; a second and third material-processing script were
written rather than extending the first; UE tooling stayed loaded after UE was retired.

Nothing here was a bad decision in isolation. The cost is that **an agent reading this repo
cannot tell which of three files is real**, and neither can a person. The remedy is not more
documentation — it is deleting the losers once a winner exists, which is the same discipline
as `docs/EXPERIMENTAL_METHOD.md` §7: *record what failed, then remove it from the path.*
