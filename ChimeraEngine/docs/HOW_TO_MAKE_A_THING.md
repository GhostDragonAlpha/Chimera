# HOW TO MAKE A THING — the construction method, end to end, with the teddy as the worked example

> Read this when you want to add ANY new object/creature/mechanism ("membrane")
> to the engine. Every step names its tool, its command, and the number that
> proves the step worked. If a step has no number, it did not happen.
>
> The law that governs every step: [../../docs/THE_LAW.md](../../docs/THE_LAW.md)
> (Rule 0: statement + prediction + falsifier BEFORE you build.
> Rule 1: derive constants, never sweep them.)

## 0. The one idea

The engine has exactly two poles:

- **The Barnes-Hut tree** talks across distance — every additive point-source
  field (gravity, light, charge, heat, acoustics) is one tree traversal
  (`engine/kernel_dsl.py`, one declaration per field).
- **The cellular automaton** decides what to BE — structure is a cell set
  grown by rules, and motion is cells added/removed (a muscle is a column
  that shortens; a joint is voxels removed around an axis of incidence).

A splat IS a cell. Rendering is Gaussian splats bound to sim cells. If you
are drawing circles, you have left the engine.

## 1. The construction order (operator law, 2026-08-16)

**Shape first, rig second, movement third, goals fourth.** Never train
movement on an unverified shape. Physical correctness of the shape is
MEASURED (paws coplanar, COM projection inside the paw hull with margin
≥ 1 cell) before any gait exists.

## 2. The pipeline — six steps, each with its proof

### Step 1 — Reference image (ambient light ONLY)

Generate candidate images (local image model, e.g. SDXL-Turbo via the
`models/imagegen/` setup). The image MUST be ambient-lit: shadows baked into
the texture become permanent dark patches on the 3D model, because the splat
renderer treats texture color as albedo. Verify ambient capture before
proceeding (`models/imagegen/_ambient_check.png` exists because a shadowed
teddy taught this lesson).

Proof: a human (or the judge model) looks at the pick sheet
(`_pick_sheet*.png`) and chooses. Taste is a legal terminal — but only a
human's taste, recorded.

### Step 2 — 3D model (TRELLIS)

Feed the chosen image to TRELLIS (`models/trellis/`, run logs
`_trellis_*.log` in `models/imagegen/`). Output: a `.ply` mesh.

Proof: the mesh is not brown noise. (The T1 teddy FAILED here silently —
its source mesh was a mutated blob; the physics faithfully animated a bad
statue for days. LOOK at the model before voxelizing.)

### Step 3 — Voxelize onto the CA lattice

```
cd ChimeraEngine/native
python voxelize_teddy.py ../models/trellis/teddy.ply <stem> <body_h>
```

Emits `genomes/<stem>.cells` (occupancy + rig chains, DATA) and
`genomes/<stem>.chimera` (the genome table).

**The scale is derived, not picked.** Canon teddy proportions: head ≈ 0.45
of height, eye ≈ 1/6 of head → an eye spans `H·0.45/6` cells; an eye needs
≥ 2 cells to exist → **H ≥ 26.7 → H = 28**. If your creature has a smallest
feature that must exist, derive H from it the same way.

Proof: render the cell set BEFORE rigging; check orientation and feature
legibility with your eyes.

### Step 4 — Shape training (the pre-movement gate)

```
cd ChimeraEngine/native
python shape_train.py <stem>
```

Grows support pillars from the torso underside to the ground until the COM
ground projection sits inside the paw hull with **margin ≥ 1.0 cell** (one
lattice step of discretization slack — the derived bound; sub-cell stability
is unrepresentable on a CA substrate). Never trims the scan; the trainable
DOF is support placement only.

Measured on the teddy: margin −0.043 (tips over) → **+1.637** after one
pillar pass. Output: `genomes/<stem>_s1.cells`.

### Step 5 — The genome table (data, not code)

A `.chimera` file is key=value DATA. The core is the reader; you never touch
C++ to add a creature. Worked example (`genomes/teddystandmuscle.chimera`):

```
kind      = vox                 # imported body: cells + chains from file
cellsFile = teddy_stand_s1.cells
embodiment = 1                  # physics + command loop on
tickMs    = 30                  # anim tick wall-clock
cell      = 0.06                # metres per cell (SI everywhere)
vmGait    = 1                   # voxel-muscle gait: legs ARE the rig chains
vmStride  = 2                   # cells advanced per shift (earned, gated on contact)
vmLift    = 1                   # cells the muscle shortens on LIFT
gravity   = 9.81                # SI; the core derives g_sim = g/(tickHz²·cell)
tickHz    = 60
```

Every constant needs a derivation comment in the file. If you cannot say
where a number comes from, the number is wrong.

### Step 6 — Run, command, verify

Build once (MinGW g++, zero warnings is the bar):

```
cd ChimeraEngine/native
g++ -O2 -std=c++17 -Wall -o ca_core.exe ca_core.cpp
```

Selftest (the fast net — drop law, energy ledger, 400-tick walk, airwalk
falsifier, all in one shot, no browser):

```
./ca_core.exe 30 genomes/<stem>.chimera selftest
```

Serve to the human viewer:

```
python native/relay.py 30 8799 native/genomes/<stem>.chimera
# open http://127.0.0.1:8799/        (unified hub: /hub, scoreboard: /scoreboard)
```

Commands (buttons or keys): WAVE 1 · WALK 2 (toggle) · REST 3 · AUTO 4 ·
DROP 5 · NAV 6 · ROM 9. Switch genome live: POST `genome:<name>` to `/cmd`.

Proof, measured on the standing teddy (2026-08-17): selftest walk
`bodyX=114` cells / 400 ticks, 57 shifts, 0 slips, 0 support-gated shifts,
airwalk displacement bit-exact 0.0; live wire walk 0 → 108 cells with the
client watching (relay backlog fix, below).

## 3. The testing doctrine

- **Fast probes first.** `selftest` mode and short Python wire probes answer
  most questions in seconds. The full suite is for phase completions, not
  iteration.
- **The wire is under test, not the page's belief.** The relay logs every
  frame to `native/native_stream_<port>.log`; oracles recompute the world
  from that log independently (`engine/test_native.py` pattern).
- **Headed browser tests are last** and must be gated (`T_HEADED`); the
  browser stack wedges on this machine — pixel proof goes through wgpu-py
  offscreen (`engine/scratch/_render_t12.py` pattern).
- **Never trust a green-looking exit.** Verify numbers against an oracle or
  a measured ledger. A file existing is not proof — you wrote the file.

## 4. Scoring (visual + physics, each 0–100)

Two scores per artifact: PHYSICS (ledger/falsifier numbers) and VISUAL (what
a human would say it looks like — lumpy, noisy, smeared are honest words).
The acceptable band is set by saturation: you push toward it until
improvement stalls against resistance, and the human's taste and the judge
model's taste are equally legal terminals. `engine/score_saturation.py add`
records every round; `engine/score_ledger.json` is the standing record.

## 5. Known traps (each cost real hours — do not re-pay)

1. **Relay replay backlog** (fixed 2026-08-17, `relay.py`): an embodiment
   session emits ~17 KB of anim frame per tick forever. A connecting viewer
   used to replay from frame 0 — after 6 h that is a 12.5 GB backlog and the
   page renders the deep past, looking frozen while the sim walks on without
   it. Late joiners now get the header + the newest anim frame + live.
   **Ops note:** the wire log and in-memory buffer still grow while a
   session runs — restart the relay daily on long sessions.
2. **A statue with a rig is still a statue.** Imported bodies
   (`kind = vox`) carry their rig chains as DATA. `vmInit` adopts those
   chains as leg columns — if the chains don't reach the ground, the gait
   stalls with zero errors and zero motion. Check `chains[i].path` spans
   hip→paw at ground level (rig line in the selftest output).
3. **Gait constants are scale-relative.** A stride trained at H=8 does not
   transfer to H=28. Re-derive or re-train per body (`vmStride`/`vmLift`
   headers say which teddy they were trained on).
4. **Shadows are albedo.** Any directional light in the source image bakes
   into the model forever. Ambient only.
5. **The fossil files are frozen.** `teddy.cells`, `teddy_stand*.cells`,
   `*_shell.json` are reference artifacts. New work writes new stems.
6. **Windows traps:** static-link native tools (the system
   `libstdc++-6.dll` ABI-mismatches MinGW g++ 15); `cmd /c start` mangles
   paths through Git Bash (use PowerShell `Start-Process` on a `.cmd`).

## 6. Where everything lives

| What | Path |
|---|---|
| The C++ core (CA + physics + rig + learner) | `ChimeraEngine/native/ca_core.cpp` |
| Genome tables (DATA) | `ChimeraEngine/native/genomes/*.chimera` |
| Voxelizer / shape trainer | `ChimeraEngine/native/voxelize_teddy.py`, `shape_train.py` |
| Relay + viewer | `ChimeraEngine/native/relay.py`, `ChimeraEngine/engine/spiace_native.html` |
| Wire oracles / tests | `ChimeraEngine/engine/test_native.py` |
| Kernel DSL (tree fields) | `ChimeraEngine/engine/kernel_dsl.py` |
| Scores | `ChimeraEngine/engine/score_saturation.py`, `score_ledger.json` |
| The session contract for agents | `ChimeraEngine/AGENT_PROTOCOL.md` |
| The plan / phase ledger | `ChimeraEngine/engine/SPIACE_RPG_PLAN.md` |
