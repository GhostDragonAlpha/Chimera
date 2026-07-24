# THE BACKLOG — everything we know needs doing, in one place

> Built 2026-07-23 because "there's so many things" and they were scattered across
> THE_ORDER.md, a corrupted task_progress.md, code TODOs, and a long session's worth of
> threads that lived only in chat. This is the single canonical list. When something here
> is done, mark it and say where the proof is — the same discipline as everything else.
>
> **Ordered by how much it is on fire**, not by how interesting it is. T0 breaks on run.
> T7 is the game shipping. Do the fires first.
>
> Machine-readable siblings: `docs/THE_ORDER.md` (the pipeline-wiring audit this draws from),
> `docs/terminology.json` (the vocabulary), `docs/objectives/*.json` (what is trained).

---

## ✅ DONE THIS SESSION (2026-07-23) — so the list shows progress, not just debt

- **Arrangement is trainable and trained** — `core/trainables/arrangement.py`, four rounds,
  each an objective repair. Landed inside all four measured bands. (`b1996f5`…`33c5f91`)
- **Arrangement grown, not computed** — `grown_arrangement.py`. Untrained genomes land in
  reality's clustering band **98% vs the parametric 1%**. (`306ff6f`)
- **The negative-space seam closes alignment** — grain emerges from the environment, not
  from the genome. (`5ea3693`)
- **GPU shaker determinism fixed** — two bugs, one silently breaking the volume constraint
  for every run. Now bit-identical, CPU parity 0.3–1%. (`c04f24c`)
- **The terminology + spine** — 108 terms, every one with a recorded *because* reaching
  PHYSICS or THE HUMAN. `python -m core.terms`, `python -m core.spine`. (`209b940`…`0d6a5c8`)
- **Psychophysics hired** — `core/perception.py`. Found we were optimising invisible
  precision. (`33c5f91`)
- **Security: two commit gates** — `core/bind_guard.py` (no server binds the LAN) +
  attribution (every commit says who wrote it). Three exposed servers fixed. (`6c96a0b`)
- **T1 #4 (genome-library integrity) — SOLVED & ENFORCED** — recovered_genomes.json now has
  ONE atomic writer (`export_genome.save_library`: tmp+os.replace, merge, lockfile). The
  three writers left after the T0 deletions (export_genome + 2 processors) route through it;
  `core/library_guard.py` in the pre-commit hook refuses any new direct writer. The two
  schemas (#9) are documented at the owner. (this session)
- **T0 (Broken Now) — CLOSED: the dead sequential-automation layer retired** — 22 files
  deleted (launchers pointing at deleted files, 9 orphan agents incl. the _old/_fixed
  triplicates, the doc-agent that corrupted task_progress.md). task_progress.md truncated
  9-copies -> a 10-line pointer to this backlog. Closed THE_ORDER findings 1, 2, 3, 6. (this session)
- **Objective design — SOLVED & ENFORCED** — the complete 7-rule method for a trainer
  objective the optimiser won't exploit (`docs/OBJECTIVE_DESIGN.md`), enforced by
  `core/objective_lint.py` in the pre-commit hook. Each rule proved by a worked failure.
  Surfaced 47 existing satisficers (below). (this session)
- **GLM-5.2 REMOVED ENTIRELY** — a 744 GB, 0.26 tok/s, unauditable local liability that spin-waited a core unnoticed. 714.8 GB reclaimed (357×2 mirrors). Local-LM tier is now LM Studio only. (this commit)

---

## 🔴 T0 — BROKEN NOW (a fresh agent hits these on day one)

- [x] **`task_progress.md` corruption** ✅ FIXED — root cause was `documentation_agent.py`
  prepending a fixed block every run, never truncating. That agent is deleted; the file is
  now a 10-line pointer to this backlog.
- [x] **`run_sequential.py` dead** ✅ FIXED — deleted with the retired layer (it launched 5
  deleted files and nothing ran it).
- [x] **`sequential_orchestrator.py` references** ✅ FIXED — the layer is retired and the docs
  (THE_WORKFLOW.md) no longer point at it.

> **T0 is now EMPTY** — a fresh agent no longer trips on broken entry points on day one.

## 🟠 T1 — INTEGRITY (nothing breaks today, but the ground is soft)

- [x] **Seven writers to `recovered_genomes.json`** (THE_ORDER #4) ✅ SOLVED — 3 were deleted
  in the T0 retirement; the rest route through the single atomic owner `save_library`, and
  `library_guard` (pre-commit) refuses new direct writers. Atomic (tmp+os.replace) + merge +
  lock, so a crash or a concurrent write can no longer corrupt or silently truncate the library.
- [ ] **~1,067 lines of root-level duplicate processors** (THE_ORDER #5) —
  `process_materials_pipeline.py`, `process_more_materials.py`,
  `phase3_recombination_testing.py`, all doing step 2's job three different ways.
  *Fix: fold any unique behaviour into `export_genome.py`, delete the rest.*
- [x] **Triplicate agents + pipeline-less agents** (THE_ORDER #3, #6) ✅ DELETED with the
  retired sequential-automation layer (`integration_agent{,_fixed,_old}`, `recombination_agent
  {,_fixed,_old}`, `research_agent`, `validation_agent`).
- [ ] **Split brain** (THE_ORDER #8) — the pipeline lives in `Construction/` + `WorldModel/`
  at the repo root AND `core/` under `Chimera/`, imports crossing both ways. *Choose one home.*
- [x] **Two undocumented genome schemas** (THE_ORDER #9) ✅ DOCUMENTED at the owner
  (`export_genome.save_library`): single-specimen (mean+p10..p90) vs class (adds
  between_std/within_std); a reader distinguishes by the presence of `between_std`.
- [ ] **47 objectives are satisficers** (surfaced by `objective_lint --all`) — bounds only,
  no maximize/minimize/target, so the trainer stops at the first feasible point. ~36 are
  auto-generated scenario forks (likely obsolete — triage for deletion); ~11 are base
  (`biome_resources`, `composition`, `npc_social`, `planet_surface`, `shelter_form`, …).
  *Fix each with a maximize or a target, or delete the dead forks. Method: `docs/OBJECTIVE_DESIGN.md`.*
- [ ] **The 4 UE-era `# TODO` stubs** — `asset_providers/*.py`, `game_code_generator.py`.
  UE is retired; these are dead intentions. *Decide keep-or-kill and record it.*

## 🟡 T2 — THE ARRANGEMENT THREAD (live work, closest to paying off)

- [x] **Range-debias the bands** ✅ DONE — `targets()` now widens each raw band to a 95%
  coverage interval on the liability scale, keyed on the region count (auto-shrinks as scans
  are added). Bands 1.5–2.1× wider. The parametric winner's `band_margin` went **0.15 → 0.584**
  with no retraining — the binding constraint that limited the arrangement work all session
  is gone. Monte-Carlo verified (d2 2.328 vs 2.326). Raw data untouched; correction is in code.
- [ ] **Measure arrangement on a 2nd scan** — bicycle has 194 camera poses, the multi-view
  target. Widens the narrow verticality/alignment bands with real data instead of statistics.
- [ ] **`grown_arrangement` clustering runs hot** — 9.255 vs the *debiased* ceiling 8.719
  (was 8.172). Over by 0.54 on a band now 5.3 wide. Confirmed a REAL property (grown matter
  clusters slightly more than the truck), not a measurement artifact. *Accept, or nudge down
  with a retrain — marginal either way.*
- [ ] **Wire `grown_arrangement` into `build_child` / `bricks`** as a selectable form, so the
  loop can place grown matter, not only computed matter.
- [ ] **Grow the OTHER rungs irreducibly** — the reducibility finding generalises: a
  parametric emitter can never surprise. The shaker, sandpile and GPU shaker already exist.
  *Candidates: terrain relief, vegetation, debris fields.*

## 🟢 T3 — THE -OLOGY BOARD (staff the two terminals; see TERMINOLOGY.md §11)

> PHYSICS is fully staffed (8). THE SPAN and THE HUMAN are nearly empty. That imbalance is
> why the vocabulary scored CUTSCENE against its own emotion test until sociology was hired.

- [ ] **Sociology → taste as a class genome** — the machinery exists (`taste.py`,
  `preference.py`, `preference_elicit.py`); the population-structure step (cultural vs
  personal variance = the heritability formula) is not built. *The first real THE-HUMAN hire.*
- [ ] **Perceptual psychology (THE SPAN)** — attention, salience, what a player notices at all.
- [ ] **Metaphysics (THE SPAN)** — observer boundedness; partially used, not formalised.
- [ ] **Anthropology / psychology / linguistics (THE HUMAN)** — ritual & meaning, motivation
  & flow, naming & story-grammar. Not recruited.
- [ ] **evo-devo / phylogenetics (PHYSICS)** — which forms can exist at all; which ancestors
  a lineage must pass through. Named, not used.

## 🔵 T4 — THE MISSING GENOMES (ports that return zero candidates today)

- [ ] **Emissive genome** — light is not matter: a laser/engine-glow EMITS, so
  albedo/roughness/metalness are meaningless. `{colour, intensity, falloff, elongation, core
  gradient, lifetime}`. `flame.splatv`/`sear.splatv` are real captured references.
- [ ] **Fluid genome** — the `fluid` port is an honest empty set in `bricks.py`.
- [ ] **Atmospheric genome** — same. `core/atmosphere.py` exists (scattering) but is not a
  placeable genome.

## 🟣 T5 — SYNTHETIC DATA (the operator's "Holy Ghost" — knowledge from disagreement)

- [ ] **Multi-source disagreement** — one ruler across the truck scan, the sandpile, the
  shaker and the emitter. Where they *agree*, nothing learned; where they *disagree*, that
  gap is real information neither held alone. *This is the daydream made concrete.*
- [ ] **Empirical Bayes across the codebook** — 13 class genomes + 489 CC objects. A new
  material with n=1 borrows the typical band width from the population. Textbook-correct
  handling of one specimen, and we already own the corpus.
- [ ] **Physics as an unlimited data source** — `granular.py` grew a real 40° repose angle
  nobody coded. Grow-and-measure on the GPU instead of scanning. Electricity, not trips.
- [ ] **JND-tolerance per viewing distance** — psychophysics answers "how precise does this
  need to be" as "what a person resolves at that range." Collapses the LOD precision problem.

## ⚫ T6 — HOUSEKEEPING & HYGIENE

- [ ] **The auto-flush daemon appends to `task_progress.md` forever** — root cause of the T0
  corruption. *Give it an append-safe target or a rotation.*
- [ ] **`STOP DS4.cmd` may have the `/proc` bug** the GLM stop script had (fixed 2026-07-23).
  DS4 is superseded by `council.py`; verify its stop script actually stops, or remove it.
- [ ] **`core/ds4_brain.py` is SUPERSEDED** by `council.py` but still present. *Keep as stub
  (documented) or remove.*

> **GLM-5.2/colibri REMOVED 2026-07-23** (operator: liability). 714.8 GB reclaimed. Do not
> re-add — the local-LM tier is LM Studio only. See `pi-servers/README.md`.

## ⚪ T7 — THE LONG ARC (the game itself; each is a project, not a task)

- [ ] **Close the extraction loop on REAL data** — `docs/matter/reference_scans/` is
  SYNTHETIC PLACEHOLDERS ("supersede on sight"). The loop is not closed until real scans land.
  *This is THE magic sauce per CLAUDE.md, and it is the one thing still on placeholders.*
- [ ] **The compositional ladder, end to end, with grown rungs** — sand → star → planet →
  climate → matter-under-boots, each handing the next its averages.
- [ ] **The story / gate system** — spine → beats → gates. A gate is a dial held until a
  measured condition holds. The player is the second terminal.
- [ ] **Release-as-gate** — ship when the cultural-timeline condition crosses, not on a date.
- [ ] **The player character + a world to stand in** — the human at the boundary.

---

## HOW TO USE THIS

Pick the **highest fire** you can actually finish, not the most interesting one. Mark it done
here with its commit SHA when the proof exists. If you find a new thing, add it to the right
tier rather than starting a fifth planning doc — that drift is literally THE_ORDER.md's whole
lesson. When T0 and T1 are empty, this project stops tripping new agents, which is worth more
than any single feature in T2–T7.
