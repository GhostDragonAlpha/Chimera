# THE KERNEL — RULE 0 for the first light-era build

*2026-08-06. Named BEFORE the build, per the law. If the run refutes the statement,
the refutation is the result — and the successor gets named here, not patched in.*

## STATEMENT (someone could disagree)

Identical points — same mass, same charge, one rule each — under exactly two forces:
a **blind long-range draw** (gravity: reads only mass and distance) and a **reading
short-range resistance** (electromagnetism: a bond at mid-range, a wall at close range) —
will, from a structureless start, **self-organize into persistent bounded clumps with
edges**. No clump, edge, or structure is authored; the balance of the two forces is the
only mechanism. This is the seed's claim made testable: *matter is the balance of the
draw and the resistance.*

## PREDICTION (not yet measured)

Starting from N ≈ 4096 identical points distributed without structure in a bounded
region:

1. **Clumps form**: the number of bound clusters (defined by the same neighbor list the
   resistance pass uses — no other criterion) falls from ~N toward a small stable count
   (tens, not thousands, not one).
2. **They persist**: the cluster count and total bound mass vary by less than a named
   tolerance over the final 25% of the run — the balance HOLDS, it does not flicker.
3. **They have edges**: mean density inside a clump exceeds mean density just outside its
   boundary by a named factor — a viewer (light) would see a surface.

## FALSIFIER (named before the run — any one ends the build)

- **Collapse**: everything merges into one blob (the draw wins outright — no balance).
- **Dispersal**: points fly apart or stay a homogeneous gas (the resistance wins, or no
  force reads).
- **Flicker**: clusters form and dissolve without settling (no stable balance exists in
  this force pair as parameterized).
- **A picked constant that hides**: any force parameter adjusted AFTER seeing a failure,
  without the adjustment being derived and recorded here. First failure is data; silent
  retuning is the end of the method.

The successor, if refuted: the balance needs a dissipation channel (the matter era's own
lesson — *damping is the medium, not a coefficient*: a balance cannot settle if energy
has nowhere to go). Dissipation enters as light: energy the balance radiates away.

## THE FORCE LAWS (the entire physics)

Per point i, per tick, two passes over one point set:

- **DRAW (long-range, blind):** `F_draw,i = Σ_j G·m²·(r_j − r_i)/(|r_j − r_i|² + ε²)^{3/2}`
  — inverse-square with softening ε (the point is a packet, not a singularity: ε is the
  packet's size, the one geometric fact a point owns). m = 1 for all points: identical.
- **RESISTANCE (short-range, reading):** neighbor list, cutoff r_c. Per neighbor:
  - `|r| < r_wall`: strong repulsion ∝ (r_wall/|r|)^p — the wall; makes edges.
  - `r_wall ≤ |r| ≤ r_bond`: attraction toward the bond distance — the bond; holds the
    balance.
  - beyond r_c: nothing (short-range by construction).
- **Integrate:** velocity Verlet, fixed dt chosen so the fastest wall interaction is
  resolved (dt from the force law, not from taste).

The fundamental constants (G, r_wall, r_bond, r_c, p, ε) are the seed's free numbers —
the light era's `FREE` dict. Their RATIOS decide whether a balance region exists at all;
they are declared here once, before the run, and the falsifier judges them as a set.

## THE REFEREE (the dyad for numbers)

Two independent implementations of the same declared laws — the GPU kernel (fast, the
game's) and a NumPy referee (slow, exact, the witness) — run identical micro-scenarios
(two points, three points, one wall collision) with pre-registered agreement tolerances
BEFORE the full run. If kernel and referee disagree beyond tolerance: the formula is
wrong, not the tuning. Stop and re-derive.

## THE RENDER (light, the reader)

The point set IS the splat buffer: `ParticleEngine.FullGPUPipeline` renders the same
positions the physics integrates — light reading the edges the resistance makes. Frames
are dumped at named instants and judged: a blind eye should see blobs with edges against
dark, not a uniform haze and not a single point.

## THE GATE

```bash
python -m pytest LightEngine/tests -q          # referee agreement + conservation checks
python LightEngine/demo_seed.py                # the run: prints cluster metrics + falsifier verdict
```

## THE HARDWARE BUDGET (measured machine, 2026-08-06)

RTX 4090 (24 GB, compute 8.9): 16,384 FP32 cores, ~82.6 TFLOPS peak (~45–50 effective),
FP64 at 1/64 rate (physics is FP32 on GPU; the referee is float64 on CPU — the dyad
meets at a pre-registered tolerance), ~1 TB/s, 24 GB VRAM (point state ~48 B → memory
is never the wall; FLOPs per tick are).

At ~20 FLOPs per force pair and a 16.6 ms frame budget:

| points | direct all-pairs | tree (N log N) |
|---|---|---|
| 16,384 | ~0.1 ms | overkill |
| 65,000 | ~2 ms | overkill |
| 130,000 | ~8 ms (borderline) | trivial |
| 1,000,000 | ~0.45 s (dead) | ~1–3 ms — REALTIME |

Consequences: v1 (direct) is honest to ~100k points — enough to judge the falsifier.
The tree (with the modifier folded into its deep walks) unlocks the millions; the
modifier is nearly free because it awakens only in the near field. numba-CUDA suffices
for the direct pass; a tuned Barnes–Hut at 1M+ likely wants CUDA C++ — the v2 decision.
