# 40-Question Self-Reflection: What's Next?

<!-- CHIMERA-LAW -->
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
> **[docs/THE_LAW.md](docs/THE_LAW.md)** · full method: `Chimera/docs/EXPERIMENTAL_METHOD.md`
> · enforced by `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

## Context & Goals
1. **What is the ultimate goal of this project?**
   - Build a space game using trained materials and procedural generation, where everything is evolved against reality's numbers.

2. **Where are we in the development cycle?**
   - Mid-stage: core infrastructure exists (genetics, splat DNA recovery, membrane shapes), but missing empirical data for heritability measurement.

3. **What was the key conceptual breakthrough today?**
   - Heritability h² requires two specimens; one specimen gives only within-object variation, not between-specimen variation needed for real breeding.

4. **What did we just demonstrate?**
   - `merge_specimens()` works end-to-end with real scan data (bonsai), producing heritability estimates per trait.

5. **Why does this matter for the game?**
   - Real reproduction needs two parents with recombination; without measurable heritability, children are just clones with noise, not true variants.

## Technical State
6. **What code exists and works?**
   - `progeny.py` (child generation, placement, verbs)
   - `export_genome.py` (cluster recovery, specimen merging)
   - `membrane_shapes.py` (container shapes)
   - All tested with real .splat/.ksplat files.

7. **What's missing?**
   - A systematic way to select and match two specimens of the same kind from available scans.
   - Integration between cluster matching and specimen merging.
   - Validation that merged genomes produce realistic offspring.

8. **What are the data sources?**
   - 15+ .splat files in `WorldModel/training_data/downloads/`
   - 3 bonsai scans (one works, two have format issues)
   - Reference scans directory with synthetic placeholders.

9. **What tools do we have for scanning?**
   - Existing `.splat` and `.ksplat` files ready to process.
   - No active scanning pipeline documented for new captures.

10. **How robust is the current pipeline?**
    - Works on existing data; needs validation on game-relevant materials (grass, rock, etc.).

## Available Resources
11. **What compute resources are available?**
    - RTX 4090 GPU, Python environment with torch/cuda.
    - All required libraries installed.

12. **How much time has been spent on this?**
    - Today: full exploration and demonstration (~2-3 hours).
    - Previous sessions: genetics code written but untested without two specimens.

13. **What documentation exists?**
    - `CLAUDE.md`, `WORKFLOW.md`, `SUCCESSOR_RUNBOOK.md` for project structure.
    - `SPLAT_DNA_WORKFLOW.md` for scan-to-DNA pipeline.
    - Genetics code well-documented in comments.

14. **What are the known constraints?**
    - Must use two specimens minimum.
    - GPU mandatory for rendering/segmentation/recovery.
    - No downloading files without explicit human approval.

15. **Who is the user and what do they want?**
    - Operator running Chimera project, wants to proceed autonomously with maximum effort.

## Immediate Next Steps
16. **What's the most logical next step?**
    - Select two good specimen pairs from existing scans and merge them into class genomes.

17. **Which materials should we prioritize?**
    - Game-relevant: grass, rock, wood, metal, ice (based on reference_scans).

18. **Do we have suitable scan data for these?**
    - Bonsai (vegetative) ✓
    - Bicycle (metallic) ✓
    - Stump (wood) ✓
    - Garden (mixed vegetation) ✓
    - Need: grass tuft, rock, pure metal, ice.

19. **How do we match specimens from different scans?**
    - Our test script uses feature similarity (size, aniso, RGB, opacity).
    - Could improve with better weighting or domain knowledge.

20. **What's the validation approach?**
    - After merging, generate children and verify they look like real siblings.
    - Check heritability values make biological sense.

## Long-Term Planning
21. **Where does this fit in the overall pipeline?**
    - Between scan recovery and child generation: `scan → class genome → recombine → children`.

22. **What's the endgame for genetics?**
    - Enable sexual reproduction with two parents, producing varied but coherent offspring.

23. **How does this connect to training?**
    - Class genomes feed into material appearance training against reality.

24. **What are the next major milestones?**
    - 1) Merge class genomes for key materials.
    - 2) Generate and render children from merged genomes.
    - 3) Validate visual coherence.
    - 4) Integrate with membrane shapes for world building.

25. **What could go wrong?**
    - Specimens don't match well enough.
    - Heritability too low (specimens too similar).
    - Children look unnatural or clamped.

## Risks & Constraints
26. **What are the technical risks?**
    - Format issues with some .ksplat files.
    - Cluster matching may be noisy across different scans.

27. **What are the data risks?**
    - Limited variety in existing scans.
    - May need to scan new objects if current ones don't match game needs.

28. **How do we mitigate these risks?**
    - Use multiple scan pairs and compare results.
    - Fall back to synthetic placeholders if real data insufficient.

29. **What's the time constraint?**
    - User wants autonomous effort; no explicit deadline given.
    - Should produce something concrete within this session.

30. **Are there any blocking issues?**
    - No technical blockers found; pipeline works on existing data.

## Knowledge Gaps
31. **What don't we know yet?**
    - Which specific materials are most critical for the game's early content.
    - Optimal cluster matching strategy across different scans.
    - How heritability estimates should vary by material type.

32. **How can we fill these gaps?**
    - Review game design docs for material priorities.
    - Experiment with multiple scan pairs and compare.
    - Consult with operator about material needs.

33. **What assumptions are we making?**
    - That existing scans represent good material variety.
    - That feature similarity is a valid matching criterion.
    - That heritability estimates will be meaningful for game design.

34. **How do we validate these assumptions?**
    - Test on multiple materials and see if results make sense.
    - Render children and visually inspect coherence.

## Integration & Workflow
35. **How does this integrate with the task board?**
    - Could be a task: "Merge class genomes for X material using Y scans."

36. **What's the handoff to next session?**
    - Document which materials were processed, heritability results, and next steps.

37. **How do we ensure continuity?**
    - Save merged genomes to `docs/matter/recovered_genomes.json`.
    - Record findings in task_progress.md.

38. **What's the role of automation?**
    - Could automate cluster matching and specimen selection from a corpus.

39. **How does this fit the Foundry workflow?**
    - Design phase: understand heritability requirements.
    - Build phase: implement merging pipeline (done).
    - Verify phase: test with real data (in progress).

40. **What's the single most important thing to do next?**
    - Select 2-3 game-critical materials, merge specimens for each, and generate/render children to validate visual coherence.

---

## Synthesis & Recommendation

After answering these 40 questions, the path forward is clear:

**Immediate Action (This Session):**
1. Pick 3 high-priority materials from existing scans: bonsai (vegetative), stump (wood), bicycle (metallic).
2. For each, find two matching clusters across different scans.
3. Merge specimens and compute heritability.
4. Generate children using `progeny.py` and render them.
5. Visually verify that children look like coherent variants of the same material.

**Why This?**
- Uses existing data (no new scanning needed).
- Tests the full pipeline end-to-end.
- Produces concrete results for validation.
- Builds toward the seed: real reproduction with heritability.

**Deliverable:**
A set of 3 class genomes with heritability estimates and rendered children, ready for integration into the game's material library.
