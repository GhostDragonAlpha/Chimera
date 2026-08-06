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

## THE SUCCESSOR: RADIATION (named 2026-08-06, after run 2 fired DISPERSE)

Run 2 (98,822 ticks = 10 t_ff) is the real refutation: a 1313-point clump formed by
1.5 t_ff, thermalized, and evaporated; bound fraction peaked 0.187 and settled ~0.12;
the radius grew 10 -> 127 without stopping. No flicker, no single-blob collapse — the
balance *almost* holds and cannot close, because velocity Verlet conserves energy and
a collapsing clump converts every unit of potential into heat it cannot lose.

**STATEMENT.** The balance settles only if collisions radiate. Concretely: a pair that
meets inside the wall (`|r| < r_wall`) loses radial relative kinetic energy — the
energy leaves the point set as light (a recorded radiated flux, not a new kind of
point; the identical-points doctrine stands). The wall is where the resistance reads
hardest, so the wall is where the balance shines. This is not a drag coefficient on
free flight — that is the matter-era "damping as a coefficient," rejected. Dissipation
acts only on contact, like grains in a granular gas: free flight conserves energy
exactly, collisions do not.

**THE DERIVED STRENGTH.** The damping is not free: it is critical damping of the bond
oscillator, computed from the declared force law. The bond spring
`F = K_BOND (r − r_bond)/(r_bond r)` has stiffness `k = dF/dr|r_bond = K_BOND / r_bond²`
per unit mass. A pair of identical points has reduced mass μ = 1/2, so the relative
coordinate oscillates at `omega_bond = sqrt(k/μ) = sqrt(2 K_BOND / r_bond²) ≈ 9.43/tick`
(period ≈ 0.67 ticks ≈ 1333 steps at dt — resolved). Critical damping of that coordinate
is `c_crit = 2 sqrt(μ k) ≈ 9.43`; applied as equal-and-opposite per-point forces
`∓ gamma_w v_rel_radial` (which the relative coordinate feels doubled), the per-point
strength is **gamma_w = sqrt(K_BOND / 2) / r_bond ≈ 4.71**. Underdamped is run 2 (no
settling); overdamped would freeze collisions into glass (an authored feel). Critical
damping is derived, not picked.

**PREDICTION.** Same start as runs 1-2 (N=4096, seed=20260806, box=10, VEL_SIGMA=1.0,
window = 10 t_ff): with contact radiation on, bound clusters fall from ~N to a stable
count (tens, not thousands, not one); the bound mass fraction RISES past run 2's 0.187
peak and holds; the radius stops growing (collapses, then stays bounded); edges sharpen
(edge metric above run 2's ~0.3). Radiated flux is recorded and reported — the first
light the world emits.

**FALSIFIER (any one ends this successor).**
- Still disperses (radius > 10x initial at 10 t_ff): contact radiation is too rare —
  the successor's successor is dissipation throughout the bond zone (the medium reads,
  not just the wall).
- One blob swallows >95%: radiation is too strong / overdamped — re-derive gamma_w.
- Flicker returns (cluster-count CV > 0.20 in the final 25%): dissipation destabilizes
  the balance rather than closing it — the force pair itself is judged.

## THE SUCCESSOR'S SUCCESSOR: THE FINITE PACKET (named 2026-08-06, after run 3)

Run 3's bulk settled (bound fraction 0.489, ~1850 stable clusters, half the mass in one
clump) while a few points were ejected to radius 5.6e9. Evidence it was integration
stiffness, not the force pair: the radius jumped 50 -> 709451 between ticks 34580-41990,
requiring v ~ 2e5 lu/tick where physical infall is ~10^2 (the P_rad peak of 34939
implies v_rad ~ 86). During collapse a pair at v_rel ~ 100 crosses the entire wall
depth (r_wall = 0.05 = v_rel * dt) in ONE tick; the (r_wall/r)^6/r repulsion at the
resulting deep penetration is unresolved at dt = 5e-4, and Verlet overshoot converts it
into a slingshot amplified ~10^7x over any physical ejection speed.

**STATEMENT.** The point is a packet, not a singularity — the DRAW already honors this
(EPS softening). The wall must too: two packets at FULL overlap feel a finite force,
not a divergent one. The wall branch softens as `r -> r_eff = sqrt(r^2 + s^2)`.

**THE DERIVED SOFTENING (no new free numbers).** s is fixed by the same closure that
derived DT: the timestep was chosen so the fastest resolved interaction is the wall at
r = r_wall/2, giving a_max = K_WALL * 2^(p+1) / r_wall = 2560. Set the SATURATED wall
force equal to exactly that resolvable maximum:
`K_WALL (r_wall/s)^p / s = a_max`  =>  `s = r_wall / 2 = 0.025`.
Above s the wall is unchanged (r_eff ~ r); at full overlap the force is exactly the
strongest push the integrator can resolve. The wall can never push harder than the
timestep can see — the same law, closed on itself.

**PREDICTION.** Same start, same window (10 t_ff), same verdict thresholds as runs 1-3:
radius stays bounded through collapse (no ejected outliers); bound mass fraction meets
or beats run 3's 0.489; cluster count settles and holds; edges sharpen. Radiated flux
continues to be recorded.

**FALSIFIER (any one ends this line).**
- Outliers still eject (radius > 10x initial): the ejection is physical, not numerical —
  the two-force family itself is judged; the next move is dissipation throughout the
  bond zone (the medium reads, not just the wall), as pre-named.
- One blob swallows >95% (COLLAPSE) or flicker returns (CV > 0.20): the balance fails
  as registered.

## THE FORCE LAWS (the entire physics)

Per point i, per tick, two passes over one point set:

- **DRAW (long-range, blind):** `F_draw,i = Σ_j G·m²·(r_j − r_i)/(|r_j − r_i|² + ε²)^{3/2}`
  — inverse-square with softening ε (the point is a packet, not a singularity: ε is the
  packet's size, the one geometric fact a point owns). m = 1 for all points: identical.
- **RESISTANCE (short-range, reading):** neighbor list, cutoff r_c. Per neighbor:
  - `|r| < r_wall`: strong repulsion ∝ (r_wall/r_eff)^p / r_eff with
    r_eff = sqrt(r² + s²), s = r_wall/2 — the wall; makes edges, and is finite at
    full overlap (the packet is not a singularity; derivation in THE SUCCESSOR'S
    SUCCESSOR: THE FINITE PACKET).
    Inside the wall only, the pair also radiates: an equal-and-opposite radial
    damping force `-gamma_w * v_rel_radial` on each member (gamma_w = sqrt(K_BOND / 2) /
    r_bond, critical damping of the bond oscillator — derived in THE SUCCESSOR:
    RADIATION). Momentum is conserved; radial relative kinetic energy leaves the
    point set and is recorded as radiated flux. Free flight is untouched.
  - `r_wall ≤ |r| ≤ r_bond`: the spring cushion — REPULSIVE only
    (`f = K_BOND(r − r_bond)/(r_bond·r)`, zero at r_bond, growing inward). There
    is no attractive branch: beyond r_bond the resistance is exactly zero, so all
    cohesion in this universe is DRAW. (Measured 2026-08-06: the crush series
    8..4096 — see theCushionLaw in THE_HIERARCHY.md. An earlier draft of this
    line said "attraction toward the bond distance"; the code never did that.)
  - beyond r_c: nothing (short-range by construction).
- **Integrate:** velocity Verlet, fixed dt chosen so the fastest wall interaction is
  resolved (dt from the force law, not from taste).

The fundamental constants (G, r_wall, r_bond, r_c, p, ε) are the seed's free numbers —
the light era's `FREE` dict. Their RATIOS decide whether a balance region exists at all;
they are declared here once, before the run, and the falsifier judges them as a set.

## THE OBSERVATION WINDOW (derived 2026-08-06, after run 1)

**Run 1 (1000 ticks, dt = 5e-4): verdict DISPERSE.** Diagnosis before any change: the run
simulated 0.5 time units. The free-fall time of the initial cloud is

    t_ff = 1 / sqrt(G * rho),   rho = N / BOX^3 = 4096 / 1000 = 4.096 lu^-3
    t_ff = 1 / sqrt(0.01 * 4.096) = 4.94 time units

Run 1 observed 0.10 t_ff — the draw never had time to act; the falsifier fired on the
observation window, not on the force balance. `TOTAL_TICKS=1000` had been picked, not
derived. This is the correction, recorded per the falsifier clause: **the observation
window is derived from the free-fall time** — observe for 10 t_ff (≈ 98,820 ticks at
dt = 5e-4). The FREE force constants are untouched. If DISPERSE (or COLLAPSE, or
FLICKER) fires again over 10 t_ff, the refutation is real and the named successor —
dissipation as radiated light — is the next build.

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
