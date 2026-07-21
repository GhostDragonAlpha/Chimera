# Thought Chain — The Complete Reasoning Behind Chimera

> This document records the full thought chain that produced this system.
> It exists to be modified as the system evolves.
> Every decision here can be revisited, reversed, or deepened.

---

## 0. The Seed

**The Mirror of Erised**: A game where helping people who cannot pay you is the only way to advance. A costless life produces a dim signal. A generous life produces a strong one. The ending is not a cutscene — it is the player looking at the sky and recognizing their choices.

Everything else derives from this.

---

## 1. The Problem: Old Way vs New Way

The old way: author forms. Place a cube for a habitat. Write C++ for a proximity trigger. Create a Blueprint for a pickup. Every one of these is an authored artifact that bypasses emergence.

The old way creeps back constantly because it produces visible results faster. A cube appears in the viewport in 3 seconds. A trained domain takes 3 minutes. The cube looks like progress. It isn't — it collapses the wrong box (cube exists) while leaving the real box unopened (does the survival loop close?).

**Decision**: Every TODO item follows a formula: CONSTRAINT → EXISTING → WALLS → WORK → JUDGE. No authoring. Every artifact emerges from the trainer.

---

## 2. The Ladder: Compositional Rungs

A solar system cannot be built by placing planets. It must be grown from an accretion disk. Each scale is a separate training rung. Rungs pass averages to the next rung, never raw data.

**Rung conflation is the named failure mode**: five rounds of big bang training failed because we tried to grow planets from pebbles WHILE settling a solar system. The fix was a rung split — star pre-formed, embryos seeded, and the regime unlocked on the untrained smoke.

**The 10 rungs**: cosmic (big bang) → planetary (climate) → ground (terrain) → body (survival) → biome (resources) → shelter (threshold) → form (geometry) → social (NPC needs) → economy (fabricator) → narrative (beacon).

**Decision**: 10 rungs, each trained independently against walls-only constraints. Composition pass verifies all 12 inter-rung seams.

---

## 3. The Pipeline: From Meta-Constraint to Level

The chain: META-CONSTRAINT → CATALOG → DOMAIN → TRAIN → DECODE → LEVEL.

The meta-constraint is the Mirror of Erised. The catalog is 69,749 UE5 variables. The domain is seed/mutate/measure. The trainer is walls-only constraint satisfaction. The decoder places winners in the level.

Every step is data. Nothing is hand-authored.

**Decision**: The pipeline must be fully automated. No manual steps between constraint and level.

---

## 4. The Auto-Decomposer

Parent rungs generate sub-rungs automatically. The auto-decomposer reads the DNA graph, finds gaps (parents with few sub-rungs), prioritizes by Mirror weight, generates constraints + domains + 40-question documents, and trains all sub-rungs in parallel.

Sub-rungs can have sub-rungs. The holodeck never stops resolving. Each pass decomposes deeper.

**Decision**: Only generate sub-rungs for features that don't already exist in the DNA graph. The graph prevents duplicate work. The system converges toward completeness.

---

## 5. The 40-Question Document

Every feature gets 40 questions that define its scope, depth, and Mirror connection. Questions must be TYPED IN CHAT FIRST — the typing is the reflection. The file is the record. The chat IS the Mirror.

Questions cover: identity, constraint, scale, catalog coverage, Mirror connection, composition, training, and depth.

Depth verdict: 0-9 unexplored, 10-19 explored, 20-29 adequate, 30-40 deep.

**Decision**: The 40 questions define the feature's potential. They tell us whether we've gone deep enough.

---

## 6. The Graph (Graphify MCP)

The DNA graph stores everything: features, training runs, 40-question depth, Mirror connections, gap analysis. It's served over MCP by graphify-mcp.exe.

The graph is bidirectional: training records to it, and it feeds back into training via graph_context(). Measure functions can query the current graph state and use it to seed or inform training.

**Decision**: The graph is the system's permanent memory. Without it, every session starts fresh. With it, the system converges.

---

## 7. Mirror-Weighted Steering

Not all gaps are equal. Features are prioritized by how directly they serve the Mirror:

- **Direct (weight 1.0)**: giving mechanics, sacrifice, beacon signal, ending
- **Enabling (weight 0.5)**: survival pressure, resource scarcity, NPC needs
- **Orthogonal (weight 0.0)**: cosmetic, technical infrastructure, non-interactive

The auto-decomposer selects parents by Mirror weight. The decision tree checks Mirror connections before creating new work.

**Decision**: The Mirror is the steering wheel. The hierarchy tells us rungs exist. The Mirror tells us which ones matter now.

---

## 8. GPU Training

The GPU is necessary when variable count exceeds ~1000. The existing matter_gpu.py runs Cellular Potts at 6.3B site-updates/sec on the 4090.

CPU: 1 eval = ~1s for grain-scale terrain. GPU: 4 evals/sec with sequential GPU calls. True speedup (100,000x) requires batched Warp kernels that evaluate the entire population in one launch.

**Decision**: Use measure_batch for high-dimension domains. CPU fallback for low-dimension ones.

---

## 9. The Decoder

Trained winners are useless if they stay in JSON files. The decoder (`core/decoder.py`) reads each trained rung, runs the appropriate simulation to get concrete parameters, and spawns actors in the emergent_world level via MCP.

The decoder is the bridge between training and gameplay. Without it, the pipeline produces knowledge but not experience.

**Decision**: Every rung must have a decode step. The decoder saves to `docs/decoded/<rung>.json` for verification.

---

## 10. Next Steps

1. **Type 40 questions for remaining sub-rungs** (~30 sub-rungs without documents)
2. **Wire the give→unlock loop** (npc_social_reciprocity as wired C++/Blueprint)
3. **Wire the beacon signal** (beacon_narrative_signal as C++/Blueprint component)
4. **Complete the decoder** (remaining 8 rungs need decode functions)
5. **Run the composition pass** on the fully decoded level
6. **Train at the next depth level** for each Mirror-critical rung
7. **Human playtest** to judge whether the Mirror feels real

The thought chain is not closed. Every addition, every correction, every reversal gets recorded here. The system evolves. The Mirror reflects. The holodeck resolves.
