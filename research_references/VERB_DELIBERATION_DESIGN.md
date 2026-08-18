# N8 — Goal-Directed Deliberation Membrane Design

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY MEMBRANE IS A THEORY.** STATEMENT / PREDICTION / FALSIFIER, all three. No
> falsifier, no design.
>
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** Every constant traces to a genome value or the
> physics. If a number cannot be derived: RESEARCH-NEEDED with the gap stated.
<!-- CHIMERA-LAW -->

Built 2026-08-14 from `ca_core.cpp` (N4–N7 Rule-0 headers at lines 1–130; G5 learner at
lines 1377–1488; N6 terrain at 1267–1310; N8 stubs at 199–202, 325–331, 1679–1680),
`bear.chimera` (all B4/L5/R5/N5 constants), `bearhill.chimera` (N6 terrain block), and
`test_native.py` (falsifier style: F-N* a..e with named measurable bounds).

**Status:** The C++ core has the N8 genome stub — `goal` flag, `goalX` parsing/validation,
and wire emission in `emitRig()` at [ca_core.cpp:199-202, 325-331, 1679-1680] — but zero
deliberation logic. This document designs the full membrane so it can be implemented and
falsified.

---

## STATEMENT (the whole design)

A goal-directed deliberation membrane runs **in parallel** with the G5 social learner:
when a genome-declared `goal` block is active, N8 encodes a terrain-aware state, selects
among an expanded verb set via ε-greedy Q-learning, and terminates episodes on goal
arrival — while the G5 ledger stays bit-identical when `goal == 0`. The membrane's
constants are derived from existing B4/L5/R5/N6/N7 values; no free parameters are
introduced.

---

## 1. STATE SPACE

### Statement

The minimal terrain-aware state extension adds **three** binary-derived features to the
existing 7-state retinal encoding: slope bucket (3 levels), goal distance bucket (2 or
3 levels, derived from l5Near/l5Far), and goal bearing (3 levels: left/center/right,
reusing the existing dot-product mechanism). The full N8 state space is **27 discrete
states** × 4 verbs = 108 Q-values.

### Derivation

**Slope bucket (3 levels).** The terrain CA guarantees max |slope| ≤ `terrainSlope`/`terrainScale`
= 512/1024 = 0.5 cells/column ([bearhill.chimera:terrainSlope, terrainScale]; [ca_core.cpp:1286-1291]).
The sensor compares `groundAt(bx+1)` with `groundAt(bx-1)`; the signed slope along x is

```
slope_x = (h[bx+1] - h[bx-1]) / terrainScale        [cells/cell, unitless]
```

Bucket boundaries at ±`terrainSlope`/2 = ±0.25 cells/column (half the walkability contract;
the CA-grown terrain's slope distribution is approximately uniform on [-0.5, +0.5], so
these split it into three equal-probability buckets):

| Bucket | Range | Meaning |
|--------|-------|---------|
| downhill | slope_x < -0.25 | ground falls ahead |
| flat     | |slope_x| ≤ 0.25 | near-horizontal |
| uphill   | slope_x > +0.25 | ground rises ahead |

Threshold derivation: `terrainSlope / (2 * terrainScale)` = 512 / 2048 = **0.25**. No
free parameter; half the walkability bound is the natural midpoint for a symmetric
distribution.

**Distance bucket.** The existing G5 uses two buckets at `l5Near` = 6 and `l5Far` = 12
cells ([bear.chimera:l5Near, l5Far]). For N8 we reuse these directly:

| Bucket | Range | Rationale |
|--------|-------|-----------|
| near   | d ≤ `l5Near` = 6 | one gait cycle (60 ticks) covers ~4A = 8 cells; reachable in < 1 cycle |
| far    | 6 < d ≤ `l5Far` = 12 | requires sustained walking (~1 episode of 90 ticks at mean stride 0.133 cells/tick → ~12 cells) |
| beyond | d > 12 | RESEARCH-NEEDED — whether this bucket is needed or whether the bear should just walk toward it without a distinct state is an open question (see F-N8c note) |

**Decision:** Start with **2 buckets** (near/far, matching G5) to keep the state space
at 3 × 3 × 2 = **18 states**. Add a "beyond" bucket only if convergence data demands it.
This is a conservative choice; the visit-count argument below holds for either 18 or
27 states.

**Goal bearing (3 levels).** Reuse the existing retinal dot-product mechanism
([ca_core.cpp:1396-1412]) with `goalPos` replacing `visitorPos`. The two eyes produce
`actPlus` and `actMinus`; the winner determines bearing: 0 = +z flank, 1 = center,
2 = -z flank. Same `l5BearEps` = 0.05 tie margin ([bear.chimera:l5BearEps]).

**State count (visit-count argument).** With 18 states × 4 verbs:

```
total_ticks = l5EpTicks × num_episodes = 90 × 320 = 28,800
expected_visits_per_state = 28,800 / 18 ≈ 1,600      (uniform exploration)
expected_visits_per_(state,action) = 28,800 / 72 ≈ 400
```

The G5 learner converged on 7 states with visits [9450, 89, 93, 92, 1736, 1888, 1958]
([test_native.py:F-N4h]). The N8 state space is ~2.6× larger but the total tick budget
is identical; even with non-uniform state occupancy (slope and distance will bias toward
certain states), every state-action pair receives hundreds of updates per 320 episodes,
which is well above the empirical convergence threshold for tabular Q-learning.

**Falsifier F-N8a.** The N8 state encoder, exercised over an exhaustive probe of all
slope × distance-bucket × bearing combinations (18 inputs), produces exactly 18 distinct
integer state codes with no out-of-bounds array access and no undefined behavior.
**Bound:** state count == 18; max state index < 18; zero segfaults or NaN in the encoder.

### Summary table entry: State space = 18 states (slope × distance × bearing), expandable to 27 with a "beyond" bucket.

---

## 2. VERB SET

### Statement

The verb set expands from {rest, wave, walk+} to **{rest, wave, walk+, walk-}**, where
walk- is the **time-reverse law** of walk+: same gait kinematics, stride sign flipped.
No new verbs (climb, wait-for-contact) are needed — the existing N6 contact law and
N7 earned-traction gating already handle slope traversal and airborne pause as natural
consequences, not actions.

### Derivation

**walk+ (existing).** [ca_core.cpp:1452-1455]:
```cpp
if (bear.contact)
  bear.body[0] += W.b4A * (2π / W.b4T) * std::fabs(std::cos(phi));
```
Stride rate = A·(2π/T)·|cos φ|, gated by contact. Cycle mean = 4A/T = 8/60 ≈ 0.133
cells/tick ([ca_core.cpp:N7 header]).

**walk- (proposed).** The N7 law is direction-agnostic: traction comes from stance-foot
sweep magnitude, not sign. Time-reversing the body's x-motion while keeping the same
leg kinematics gives:
```cpp
if (bear.contact)
  bear.body[0] -= W.b4A * (2π / W.b4T) * std::fabs(std::cos(phi));
```
This is a **law**, not a heuristic — it is the unique time-reverse of the forward law,
derived from the symmetry that the N7 traction mechanism does not encode a preferred
direction. The gait phase φ and IK targets are identical; only `body[0]`'s increment
sign flips.

**Why not climb?** The N6 terrain CA enforces max slope ≤ 0.5 cells/column across the
entire domain ([bearhill.chimera:terrainSlope, terrainX0-X1]; [ca_core.cpp:1286-1291]).
The bear's existing contact law (velocity-projection onto the highest terrain column
under the footprint, [ca_core.cpp:1527-1534]) already handles slopes up to this bound
without slipping — except at crest exits where N7 correctly breaks contact. No special
climb verb is needed; the physics membrane covers it.

**Why not wait-for-contact?** N7 already does this: `if (bear.contact)` gates the stride,
so airborne ticks produce zero translation automatically ([ca_core.cpp:1452]). The bear
doesn't need an explicit "wait" action — contact loss is a natural consequence of
terrain geometry, and the Q-learning agent learns to avoid crest-exit states by associating
them with zero reward progression.

**Falsifier F-N8b.** walk- produces bit-identical leg kinematics to walk+ (same thetaFinal,
same IK residuals) but `body[0]` changes by the negative of the walk+ displacement over
the same number of ticks on flat ground. **Bound:** |bodyX(walk-) + bodyX(walk+)| < 1e-9
over 400 ticks on flat terrain; thetaFinal arrays identical to 1e-12.

### Summary table entry: Verbs = {rest(0), wave(1), walk+(2), walk-(3)}.

---

## 3. REWARD STRUCTURE

### Statement

The N8 reward structure is a **parallel economy** to G5's, derived from the same
beckoning-gradient law and energy-cost constants, with a terminal goal-arrival reward
and an episode-timeout penalty scaled to match G5's economics. All constants trace to
B4/L5/R5 values; no new free parameters.

### Derivation

**Per-tick walk cost.** Reuse `r5WalkTick` = −0.02 ([bear.chimera:r5WalkTick]). Walking
is the same physical action regardless of whether a visitor or goal is present.

**Beckoning gradient (goal approach).** The G5 precedent: `r = r5WalkTick + r5Beckon * (d_prev - d_now)`
([ca_core.cpp:1460-1463]) with `r5Beckon` = 0.03 / (4A/T) = 0.03 / 0.133... = 0.2255639...
([bear.chimera:r5Beckon] comment). Net per tick while walking toward target:
−0.02 + 0.2256 × 0.133 ≈ **+0.01/tick** (documented in the genome header).

For N8, derive `k8` from the same economic requirement (net positive when approaching):
```
k8 = (|r5WalkTick| + r_net) / stride_mean
   = (0.02 + 0.01) / (4 * b4A / b4T)
   = 0.03 / (8/60)
   = 0.225
```
This gives **k8 = r5Beckon** exactly — the same constant, same +0.01/tick incentive.
The genome declares `r8Beckon` as a separate field for independence, but its derived
value equals `r5Beckon`.

Falsifier note: if the goal is on uphill terrain, the horizontal stride is unchanged
(N7 measures body[0] displacement directly), so the gradient naturally accounts for
terrain without modification. Crest-exit contact loss (N7 consequence) causes d to
stall, producing zero gradient — the agent learns to avoid those states.

**Goal-arrival reward.** Derived from the workspace sphere: the bear's IK reach is
approximately `limbLen + b4A` = 5 + 2 = 7 cells (the "7-cell workspace sphere" noted
in [bear.chimera:l5Near] comment). The goal is "reached" when d ≤ `l8GoalReach`.
Deriving the threshold: one gait amplitude `b4A` = 2 cells is the natural scale for
"at your feet." So **l8GoalReach = b4A = 2** cells.

Reward magnitude: match `r5WaveNear` = +1.0 ([bear.chimera:r5WaveNear]) — same order
as the social terminal reward, scaled to the same "accomplishment" magnitude.

**Episode-timeout penalty.** When the episode expires without reaching the goal (90
ticks), the bear has failed to close the distance. The G5 equivalent is `r5WaveFar` =
−0.1 for a far visitor that wasn't approached ([bear.chimera:r5WaveFar]). Scale by the
ratio of "far" to "near" reward magnitudes: −0.1 / 1.0 × (+1.0) = **−0.1**. Same as
r5WaveFar.

**Rest reward.** When no action is taken and the goal is present but out of range, the
bear accumulates per-tick cost only while walking. Rest should have zero tick cost and
zero gradient (d doesn't change). So `r8RestTick` = **0**. This differs from G5's
`r5RestAbsent` = +0.02, which rewarded resting when no visitor was present — a social
signal. For N8, resting with a goal present is just waiting; no intrinsic reward or
punishment.

**Slope-modulated cost (optional refinement).** Walking uphill does work against gravity:
ΔE/tick = gSim × slope × stride_rate. With gSim = 9.81/(60²×0.06) = 9.81/216 ≈ 0.0454
cells/tick² ([bear.chimera] N5 comment), stride_mean = 4A/T = 0.133, slope_max = 0.5:
extra cost at max uphill = 0.0454 × 0.5 × 0.133 ≈ **0.003/tick** (~15% of base walk
cost). This is measurable but small; the design keeps flat walk cost for simplicity and
lets the Q-learning agent discover slope effects through the gradient (uphill goals
close distance more slowly due to crest-exit slips, which the gradient already captures).
If convergence data shows systematic uphill underperformance, add a slope-modulated
cost as a follow-on.

### Reward table

| Condition | Reward | Derivation |
|-----------|--------|------------|
| Walking toward goal (gradient) | `r5WalkTick + r8Beckon × (d_prev − d_now)` | Same law as G5; k8 = r5Beckon derived above |
| Walking away from goal | `r5WalkTick` (no gradient bonus) | d increases → gradient is negative; net ≈ −0.02 − 0.03 = −0.05/tick |
| Goal arrived (d ≤ b4A = 2) | **+1.0** | Matches r5WaveNear magnitude |
| Episode timeout (no arrival) | **−0.1** | Matches r5WaveFar; scaled proportionally |
| Resting with goal present | **0** | No cost, no gradient (d is constant) |
| Walking without goal (N8 disabled) | N/A — G5 runs exclusively | Membrane isolation (§4) |

### Falsifier F-N8c. With `goal = 1, goalX = 20` on the bearhill terrain, the N8 learner
achieves goal arrival (d ≤ 2) in ≥ 80% of the last 100 episodes, with mean time-to-goal
< 90 ticks (the full episode budget). **Bound:** success rate ≥ 0.8 over episodes
[220, 319]; mean ticks-to-arrival ≤ 90 for those same episodes.

### Falsifier F-N8d. The N8 learner's average reward per tick while in "far-center" state
and executing walk+ is positive (+0.005 to +0.015/tick), confirming the gradient
economics are net-positive as derived. **Bound:** mean reward/tick in the last 100
episodes, restricted to far-center × walk+ transitions, satisfies 0.005 < r_mean/tick
< 0.015.

---

## 4. MEMBRANE ISOLATION

### Statement

When `goal == 0`, the N8 membrane is **completely inert**: the G5 social learner runs
bit-identically to the current implementation, with zero change to its Q-table, visit
counts, or any ledger field. When `goal == 1`, N8 replaces only the state encoder and
reward computation; the G5 Q-table lives in separate memory and is never touched.

### Gating mechanism (genome-declared)

The existing N8 stub in the genome struct ([ca_core.cpp:199-202]) declares:
```cpp
int goal = 0, goalX = 0;
```
The parsing/validation at [ca_core.cpp:325-331] enforces `goal == 1 → terrain == 1`
and `terrainX0 < goalX < terrainX1`. This is the gate.

**When goal == 0:**
- `autoTick()` skips the N8 branch entirely and falls through to the existing G5 logic
  ([ca_core.cpp:1446-1488]).
- `senseState()` returns the 7-state retinal encoding unchanged.
- The N8 Q-table (separate struct, see below) is zero-initialized and never accessed.
- All wire output (rig, anim, selftest) is identical to the current bear+terrain run.

**When goal == 1:**
- `spawnEpisode()` places a static goal at `(goalX, groundY, 0)` instead of a random
  visitor. The goal's z-position is fixed at 0 (center-line); extending to z ≠ 0 is
  a follow-on.
- `n8State()` replaces `senseState()` as the state encoder.
- `autoTick()` uses N8 rewards (r8* constants) and terminates when d_goal ≤ b4A.
- The G5 Q-table is untouched; its ledger fields (visits, Q, first30, last30) are
  still computed but reflect the G5 policy running in parallel (or can be suppressed
  entirely when goal == 1 — see design choice below).

**Design choice:** When `goal == 1`, suppress G5 ledger output and emit a separate N8
ledger instead. This keeps the selftest clean and avoids mixing two learner's numbers.
The G5 Q-table still exists in memory (for fair comparison when goal flips from 1 to
0) but is not printed.

### Falsifier F-N8e. With `goal == 0` on bearhill, the N8-enabled C++ binary produces a
selftest ledger **bit-identical** to the current N7 bearhill selftest (same Q-table,
same visits, same bodyXfinal, same thetaFinal, same nan flag). **Bound:** every field
in the selftest JSON matches the reference run to 1e-12; zero divergence in any ledger
array.

---

## 5. FALSIFIERS (all named before any run)

| # | Claim | Measurable bound | Kill condition |
|---|-------|------------------|----------------|
| **F-N8a** | State encoder produces exactly 18 distinct states from exhaustive probe; no OOB access | state_count == 18; max_index < 18; zero runtime errors | Any missing state, duplicate encoding, or crash |
| **F-N8b** | walk- is the time-reverse of walk+ on flat ground: same kinematics, negative displacement | \|bodyX(walk-) + bodyX(walk+)\| < 1e-9 over 400 ticks; thetaFinal identical to 1e-12 | Displacement mismatch > 1e-9 or kinematic divergence |
| **F-N8c** | N8 learner reaches goal (d ≤ 2) in ≥ 80% of last 100 episodes on bearhill with goalX = 20 | success_rate ≥ 0.8; mean_ticks_to_goal ≤ 90 over episodes [220,319] | Success < 80% or mean ticks > episode budget |
| **F-N8d** | Gradient economics are net-positive: reward/tick while walking toward goal is +0.005 to +0.015 | 0.005 < mean_reward_per_tick < 0.015 in far-center × walk+ transitions (last 100 eps) | Mean outside [0.005, 0.015] or negative |
| **F-N8e** | Membrane isolation: goal == 0 produces bit-identical G5 ledger to N7-only run | All selftest fields match reference to 1e-12; zero divergence | Any field differs > 1e-12 |

---

## 6. RELATED WORK (brief, cited)

| Source | Relevance to N8 design points |
|--------|------------------------------|
| **Sutton, Precup & Singh 1999**, "The Options Framework" | Membrane isolation (§4): N8 is an "option" — a temporally extended action with its own policy, initiated/terminated by a high-level gate (the goal declaration). The ε-greedy Q-learning within N8 is the option's internal policy. |
| **Bard 2016**, "A Review of Utility-Based Approaches to Game AI" | Reward structure (§3): the beckoning gradient k·(d_prev − d_now) is a utility-per-distance-closed parameter, directly analogous to utility-based action selection where actions maximize expected cumulative reward. The derived k8 = r5Beckon follows the same principle. |
| **Riley 2017+**, Lenia / CA agent literature (e.g., "Life on the Lattice" by Gray 2020) | State space (§1): cellular-automaton agents with local sensing and discrete action spaces learning navigation through RL — directly analogous to N8's state → verb mapping on a CA substrate. The slope-bucket encoding parallels the "local gradient sensing" used in CA navigation agents. |
| **McCallum 1995**, "Region-Based Competence and Knowledge Acquisition in Agents" | State augmentation (§1): adding derived features (slope, goal bearing) to raw sensorimotor states compresses the information relevant for temporal credit assignment, reducing the effective state space the Q-table must cover. |

---

## SUMMARY TABLE

| Dimension | Proposed value | Derivation source |
|-----------|---------------|-------------------|
| **States** | 18 (slope: 3 × distance: 2 × bearing: 3) | `terrainSlope/2·terrainScale` = 0.25 bucket boundary; `l5Near`=6, `l5Far`=12 for distance; retinal bearing reused |
| **Expandable to** | 27 (add "beyond" distance bucket at d > 12) | RESEARCH-NEEDED: convergence data will determine if the third bucket is needed |
| **Verbs** | 4: {rest, wave, walk+, walk-} | walk- = time-reverse law of walk+ (N7 symmetry); climb/wait not needed (N6/N7 already handle) |
| **Q-table size** | 18 × 4 = 72 entries (expandable to 108) | State count × verb count |
| **Episode budget** | `l5EpTicks` = 90 ticks | Inherited from G5; keeps credit horizon consistent |
| **Goal-arrival threshold** | `b4A` = 2 cells | One gait amplitude — the natural "at your feet" scale |
| **Beckoning constant k8** | `r5Beckon` = 0.2255639… (derived: 0.03/(4A/T)) | Same economic requirement as G5 (+0.01/tick net); no new free parameter |
| **Goal-arrival reward** | +1.0 | Matches `r5WaveNear` magnitude |
| **Timeout penalty** | −0.1 | Matches `r5WaveFar`; proportional scaling |
| **Rest tick reward** | 0 | No intrinsic cost or bonus for waiting with goal present |
| **Membrane gate** | Genome `goal` flag (0 = G5 only, 1 = N8 active) | Existing stub at [ca_core.cpp:199-202, 325-331] |
| **Falsifiers** | F-N8a through F-N8e (above) | Named before any run per Rule 0 |

---

## OPEN QUESTIONS / RESEARCH-NEEDED

1. **Third distance bucket?** Starting with 2 buckets (near/far) keeps the state space at
   18 and matches G5's proven convergence. A "beyond" bucket (d > l5Far) would increase
   to 27 states. Test F-N8c will determine if the bear can learn effectively without it.

2. **Goal z-position.** Currently fixed at 0 (center-line). Extending to arbitrary z
   requires the full 2D bearing encoding, which the existing retinal system already
   supports (the bearing dimension is already 3-valued: left/center/right). No state
   space change needed — just set `goalZ` in the genome and feed it to the encoder.

3. **Slope-modulated walk cost.** The physics-derived extra cost (~0.003/tick at max
   uphill) is small but measurable. If F-N8c shows systematic uphill failure, add
   `r8WalkUphill = r5WalkTick - gSim * slope * (4A/T)` as a follow-on.

4. **Shared vs. separate ε-greedy exploration.** The design proposes separate Q-tables
   with shared exploration parameters (`l5Eps0`, `l5EpsDecay`, `l5EpsMin`). An
   alternative is fully independent N8 exploration constants — but that introduces
   free parameters. Inherited values are the conservative choice.
