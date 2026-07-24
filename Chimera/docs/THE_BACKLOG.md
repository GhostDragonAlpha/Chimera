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
- [x] **Split brain** (THE_ORDER #8) ✅ INVESTIGATED — the "imports cross both ways" premise
  was FALSE. The graph is acyclic (Chimera/core imports nothing upward). The one real defect:
  13 files hardcoded `sys.path.insert(0, "E:/PythonChimera")` (only ran on this machine) --
  now file-relative (`parents[1]`), portable to any clone. Two homes with a clean one-way
  dependency is normal layering; no migration and no guard needed. *Verified, not gold-plated.*
- [x] **Two undocumented genome schemas** (THE_ORDER #9) ✅ DOCUMENTED at the owner
  (`export_genome.save_library`): single-specimen (mean+p10..p90) vs class (adds
  between_std/within_std); a reader distinguishes by the presence of `between_std`.
- [x] **"47 satisficers"** ✅ RESOLVED — investigated: they are auto-decomposed FEASIBILITY
  objectives ("satisfy the parent's walls in composition"), for which satisficing is the
  CORRECT semantics — the first feasible point is the answer. The R6 lint was over-strict (same
  as it first was for `target`-fitting objectives); `objective_lint` now exempts feasibility
  objectives and reports 0 real satisficers. Not a bug — a mischaracterization, corrected.
- [ ] **UE-era generated training artifacts** (found while investigating the above) — ~10 of
  the 60 `core/trainables/generated/` domains reference retired UE concepts (pixelstream,
  uanimnode, metahuman, pcg). The trainer does not import `generated/` (it is `auto_decomposer`
  output), so they are dead scaffolding. *Prune with care — some grep matches (e.g. "blueprint"
  in prose) may be false; verify per-file before deleting. Delicate because it is live-generator
  output.*
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
- [x] **Wire `grown_arrangement` into `build_child` / `bricks`** ✅ DONE — `build_child(form='grown')`
  grows an irreducible Cellular-Potts lattice, extracts pos+dirs (local long axis, same ruler as
  a real scan), and wears the material genome's splat shape. Deterministic per seed. A brick
  carrying `form='grown'` flows through `to_splats`, so the loop places grown matter. Caveats:
  ~23x slower than the parametric form (the grow cost; ~10ms warm/brick) and voxel-blocky; kept
  OPT-IN, not the default. Realizes the session's biggest finding (grown hits reality's band 98%
  vs the parametric 1%).
- [ ] **Grow the OTHER rungs irreducibly** — the reducibility finding generalises: a
  parametric emitter can never surprise. The shaker, sandpile and GPU shaker already exist.
  *Candidates: terrain relief, vegetation, debris fields.*

## 🟢 T3 — THE -OLOGY BOARD (staff the two terminals; see TERMINOLOGY.md §11)

> PHYSICS is fully staffed (8). THE SPAN and THE HUMAN are nearly empty. That imbalance is
> why the vocabulary scored CUTSCENE against its own emotion test until sociology was hired.

- [x] **Sociology → taste as a class genome** ✅ BUILT — `core/taste_population.py`: groups
  = populations, individuals = specimens, taste axes = traits, so the SAME heritability formula
  (V_between/V_within) splits taste into CULTURAL (a group sample predicts it) vs PERSONAL (ask
  the individual). `fit_individual` uses the real `PreferenceModel`; `heritability_split` does
  the split. Verified: on a synthetic 2-group demo built with a KNOWN split, it recovers it
  (punishes_naive h2 0.998 CULTURAL, learnability 0.007 PERSONAL). The first THE-HUMAN hire.
  Machinery real; group DATA synthetic until real preferences are elicited per market.
- [ ] **Perceptual psychology (THE SPAN)** — attention, salience, what a player notices at all.
- [ ] **Metaphysics (THE SPAN)** — observer boundedness; partially used, not formalised.
- [ ] **Anthropology / psychology / linguistics (THE HUMAN)** — ritual & meaning, motivation
  & flow, naming & story-grammar. Not recruited.
- [ ] **evo-devo / phylogenetics (PHYSICS)** — which forms can exist at all; which ancestors
  a lineage must pass through. Named, not used.

## 🔵 T4 — THE MISSING GENOMES ✅ COMPLETE (every port kind now served)

- [x] **Emissive genome** ✅ BUILT — `core/emissive.py`: the light family over {colour,
  intensity, falloff, elongation, core_gradient, lifetime}, four physics-grounded archetypes
  (laser, plasma_bolt, fire, engine_glow). The `energy` port returns candidates (was 0);
  `render_world` gained an emissive path (skip Lambert, boost by intensity) so light GLOWS
  instead of rendering as dull grey. Verified: laser = a bright bolt, fire = a white-hot-core
  blob. AUTHORED from physics (the legitimate second intake); measured-from-.splatv is a
  future upgrade (the 4D format is a 396KB-header parse).
- [x] **Fluid genome** ✅ BUILT — `core/fluid.py`: the liquid family over {colour,
  transparency, depth_tint, surface_gloss, flow, viscosity, emission}, five archetypes (water,
  ocean, lava, mud, coolant). The `fluid` port returns candidates (was 0). Renders correctly:
  water = a flat translucent blue pool (you see through it), lava = a mounded opaque glowing
  orange one (molten fluids carry an emission, reusing the emissive render path). Authored, not
  measured; no refraction (a future upgrade). Uses the existing translucent-Lambert render.
- [x] **Atmospheric genome** ✅ BUILT — the atmosphere genome added to `core/atmosphere.py`:
  the scattering coefficients ARE the DNA. Five archetypes (earth/mars/titan/venus/thin);
  `apply_atmosphere` drives the physical `sky_colour` from a genome. Verified by looking:
  Earth comes out blue, Mars butterscotch, thin near-black -- none of it chosen, it falls out
  of beta ~ 1/lambda^4. The `atmospheric` port returns candidates. NOT a placeable blob -- the
  medium ("you don't make the sky, you make the clouds"); it drives the sky, clouds stay
  separate matter/fluid. **T4 COMPLETE: every port kind (structural/substrate/gravitational/
  energy/fluid/atmospheric) is now served -- no empty sets left.**

## 🟣 T5 — SYNTHETIC DATA (the operator's "Holy Ghost" — knowledge from disagreement)

- [x] **Multi-source disagreement** ✅ BUILT — `core/disagreement.py`: puts the truck scan
  (truth), the grown shaker, and the parametric emitter on ONE ruler, keeps the divergence
  (does not average -- that hides the signal), and attributes each source's characteristic
  bias. Real result: alignment is CONCORD (all agree, validated); the parametric emitter is
  +54% too elongated on aspect; the grown shaker is +66% too clustered. Each bias is a lever.
  The operator's "knowledge from disagreement" made concrete on real measurements.
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

> **UE untangling — SCOPED 2026-07-24** (`docs/UE_UNTANGLING_SCOPE.md`). The "huge entangled
> UE subsystem" is really a ~12k-LOC C++ **generation backend** that is nearly an island (helm/
> rep_engine/trainer/matter do NOT import it). The game-spec DSL and the general guards stay.
> One focused session removes the backend; the UE-string cleanup in current infra is a separate,
> optional pass. Pre-delete gate: `python tools/ue_ring_check.py`. Not started -- scoped only.

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
