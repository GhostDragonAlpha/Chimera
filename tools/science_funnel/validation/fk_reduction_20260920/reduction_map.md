# THE FK REDUCTION MAP — per-candidate classification by law
(lane/fk-reduction-20260920 · base 4a241439 · the classification is SOURCE-DERIVED,
the measured columns are from this lane's runs in `raw/` and `receipt_input.json`;
Rule 1: every number below is measured or derived by the shown arithmetic — none is taste.)

The consumption context (tick_cost_attribution_20260920): fk.evaluate = 87.9% of the
tick INCLUSIVE at 286.586 calls/tick (86549 hits / 302 ticks), per-evaluate cost
40.8315/286.586 = **0.14244 ms** at the tickcost-matrix machine state
(**0.06998 ms** at the receipt state, ×22.40/45.59 = 0.4913); budget 3.33 ms/tick.

────────────────────────────────────────────────────────────────────────────────
## THE RECONCILED CENSUS (F1: EXACT — 86549 = 86549)

Per walk (302 ticks), from the amended site instrument (census3/census4, identical
counts ×2, stdout fence GREEN):

| class | site(s) | hits/walk | /tick | % of E | source structure |
|-------|---------|-----------|-------|--------|------------------|
| the RK4 floor | S_RATE 35520 + S_FSE0 8880 + S_FSP0 8880 + S_FSP1 8880 | 62160 | 205.83 | 71.82% | 7 evaluates × 8880 free_steps: 4 rate() substages + e0(plane check) + p0 + p1 |
| the bisection gap | S_BISECT_GAP | 6216 | 20.58 | 7.18% | line 1909: `gap_of(evaluate(free_step(start,mid,tau,probe)),k)` — 148 contact-event searches × 42 probes |
| impact pair | S_IMP 3443 + S_PCEC 3443 | 6886 | 22.80 | 7.96% | impact base + the unconditional poscorr `ec`, per impact() call |
| advance pair | S_ES 2395 + S_EE 2395 | 4790 | 15.86 | 5.53% | estart + eend per entry reaching them (3300 entries − 904 caught-returns − 1 sub-ε-h) |
| poscorr extras | S_PCUB 1273 + S_PCAR 1384 + S_PCDU 1272 | 3929 | 13.01 | 4.54% | u_before + per-pen-point rows + du, per poscorr fire (1273 fires; du missing exactly 1 = the tick-302 REFUSING fire, thrown at the dq_max budget before du) |
| controller laws | S_LAWFE 969 + S_CAP 1 + S_FORE 1 | 971 | 3.22 | 1.12% | planted-strut IK lazy evals + entry capture + fore clock |
| stages | S_REFLEX 303 + S_HULL 303 + S_SAT 243 + S_STATUS 304 + S_U0 304 | 1457 | 4.83 | 1.68% | per-tick stage evals (status is the harness observation) |
| crossing check | S_CROSS | 140 | 0.46 | 0.16% | the localized crossing's gap require |
| clamps | S_PIN1/S_PIN2 | 0 | 0 | 0 | no clamp events fired in the walk |
| **TOTAL** | | **86549** | **286.586** | 100% | == the pinned tickcost counter, EXACT |

Cross-identities, all EXACT: R = 4·F (35520 = 4×8880); F = 2395 main + 126
drive-bisection (3 events × 42) + 6216 contact-bisection (148 × 42) + 140
crossings + 3 wall = 8880; I = 3300 entries + 140 + 3 event impacts = 3443;
advance entries 3300 = 1209 outermost trials + 2091 recursions (280 from 140
contact events × 2 children + 3 wall + 1808 = 2×904 caught-impact recursions);
store-bisection and retry advances = 0 (no store violations in the median walk).

────────────────────────────────────────────────────────────────────────────────
## CLASS (a) — BYTE-NEUTRAL (bit-identical outputs; provable; fenced)

THE PROOF BASIS (shared by every (a) candidate): `Model::evaluate(q, v, gravity)`
(coupled_articulation.hpp:82-91) is a PURE function — it reads only its arguments
and the immutable body table built once in the constructor; no statics, no RNG, no
caching, no I/O; deterministic IEEE-754. Two calls with identical (q, v, gravity)
produce BIT-IDENTICAL `Evaluation`s, and replacing one with a read of the other
cannot move a byte. Each candidate adds a NO-MUTATION proof for its reuse window.
The fence is the empirical backstop (F2/F3).

| id | candidate | proof (window) | evals saved (measured) | status |
|----|-----------|----------------|------------------------|--------|
| R1 | rate-a reuses the state's Evaluation | rate-a evaluates the SAME `start` free_step's e0 evaluated; `start` unmutated between | 1 × 8880 = 8880 | IMPLEMENTED |
| R2 | estart (1890) feeds every free_step of the advance (e0/rate-a/p0 — including all 42-probe bisections) | `start` const&, never mutated after impact() (which runs BEFORE estart); shifted() copies; event search reads only | 2 × 8880 = 17760 | IMPLEMENTED |
| R2b | clamp's `evaluate(start)` → estart | `start` unmutated across the advance body | 0 here (no clamps fired; ≤1/clamp) | IMPLEMENTED (no-op this walk) |
| R3 | poscorr reuses `ec` for u_before + arows | pen scan reads only; du still evaluates AFTER the q correction | 1273 + 1384 = 2657 | IMPLEMENTED |
| R4 | impact base reused as ec when nothing mutated | needs a v_mutated flag; ≤1 × 3443 ceiling | ≤ 3443 (11.4/tick, 4.0%) | recorded, NOT implemented |
| R5 | stage reuse: hull e → sat census; reflex e → hull | clock-only writes between (provable per stage) | ≤ 2/tick (0.7%) | recorded |
| R6 | status()'s u0 `evaluate(defaults,0)` is a walker constant | constant arguments + purity | 1/tick (0.3%) | recorded |
| R7 | rate(): rown[k] (1726) re-derived as rn (1751) | same e, same k; pure row build | sub-1% | recorded |

NOT (a), named so it is never misfiled (F3): impact's base evaluate CANNOT feed
estart (impact mutates v and q between them — different inputs); rates b/c/d and
p1 and every bisection-probe state are genuinely new evaluations. The charter's P2
intuition ("most evals have genuinely changing inputs inside RK4") is correct for
the substages themselves but wrong about the scaffold: 3 of the 7 evaluates per
free_step are the SAME state.

**IMPLEMENTED: R1 + R2 + R2b + R3. MEASURED: 29297 evals/walk removed (97.01/tick,
33.9% of all FK evaluates), stdout byte-identical ×3, stderr byte-identical ×3,
trace identical over the full common window (F2/F3 GREEN — the fence held).**

────────────────────────────────────────────────────────────────────────────────
## CLASS (b) — PHYSICS-COMPATIBILITY (bytes change; LAWFUL ONLY through the
## certificate/requalification process — tools/policy_compat, lane/cert-dryrun-
## 20260920: the 5-tuple (policy bundle, physics build, runtime profile,
## body/domain, test suite) -> certificate; the validator recomputes validity
## from the certificate bytes; production class requires the complete
## restart-state inventory with zero unresolved gaps, a hash-chained replay,
## and a derivation string per margin)

| id | candidate | lever (derived from the census) | requalification bill |
|----|-----------|----------------------------------|----------------------|
| B1 | 42-iteration event bisection → bracketing Newton/regula-falsi on the SAME event functions | probes = 6342 free_steps/walk (21.0/tick) carrying 5 evals each post-(a); 42 linear-convergence iterations is a BOUND, not a derivation; Newton on the smooth gap/stop functions converges quadratically (~6 iters to 1e-12): saves ~36/42 of probe work ≈ 90 evals/tick after (a) ≈ 6.3 ms/tick at the receipt state | event-localization ticks MOVE → every downstream byte moves → ALL frozen anchors re-derive (refusal_tick 302, worst_moving_ledger_J 30.970714, red_falsifiers 49/173, stdout/stderr/trace fences); closed-loop requalification reruns the F-G1..G8 suite + the qualified coupled classes (shared-law siblings) + a NEW physics-build identity in the 5-tuple + a derivation string per margin |
| B2 | mass-matrix factorization (inverse_spd) reuse across RK4 substages | inverse_spd = 1.87% of the tick; ≤3/4 of it ≈ 1.4% — and it is an APPROXIMATION (mass differs across substages) | same bill as B1 for ≤1.4% — REJECTED BY PROPORTIONALITY |
| B3 | bracket warm-start across advances | subsumed by B1 (first probe differs → bytes move) | B1's bill |
| B4 | row-assembly hoisting inside rate() | (a)-class if bitwise-identical reuse is provable (R7); else B1's bill | per classification |

The B-class IS the material NEXT lever only through B1 (the bisection probes carry
21.0/189.6 of the post-(a) evaluates); its bill is the FULL certificate — correctly,
because event localization decides contact, and contact decides the gait.

────────────────────────────────────────────────────────────────────────────────
## CLASS (c) — STRUCTURAL (changes the equation count; ARCHITECTURE CHANGE
## REQUESTS, not near-term lane items)

| id | candidate | equation count reached | numerical-analysis basis |
|----|-----------|------------------------|---------------------------|
| C1 | Tiered FK: gap-only probes (one chain's frames, no mass/bias/Jacobians) for the pure gap reads (S_BISECT_GAP 6216, S_EE-scan, impact touching, poscorr scan, S_STATUS gaps) | a frames-only pass is the O(depth) product chain vs the O(n·bodies) Jacobian+mass assembly — ~50-70% of each such evaluate | root-finding on g(q(t)) needs only g's value; the mass matrix is dead weight in a gap scan (Bisection/Newton are derivative-or-value-only methods) |
| C2 | Integration order: RK4 → semi-implicit (symplectic) Euler | rate calls 117.6 → 29.4/tick; with (a), free_step falls 4 → ~2 evaluates | 1st-order/1-stage vs 4th-order/4-stage; stability at dt=1/300 for the stiff contact-legged system must be RE-DERIVED; the tickcost receipt's rejected F2 candidate, re-derived as lawful-only-here |
| C3 | Incremental/recurrent FK (Featherstone RNEA/CRBA class) replacing the from-scratch Jacobian-product assembly | CRBA computes the SAME mass matrix in O(n) vs the current O(n·bodies) per-body n-column Jacobian products — per-evaluate constant ÷3-10 at n=18 | Featherstone (2008); FP reassociation moves bits → NOT byte-neutral → certificate path with anchors moving; the biggest CPU lever that keeps RK4 |
| C4 | (deployment) GPU batched FK kernels across the fleet | moves the equation count off the CPU tick entirely | the deployment decision's existing shape |

────────────────────────────────────────────────────────────────────────────────
## THE DERIVED BOUNDS vs the 3.33 ms/tick budget

Eval-count deltas are the state-independent currency (measured); ms use the
measured per-eval cost (0.14244 ms tickcost-matrix state / 0.06998 receipt state).
Loop ms: 46.45 (tickcost matrix) / 23.26 (receipt).

| composition | evals/tick | FK ms/tick (matrix / receipt) | loop ms/tick (matrix / receipt) | x budget (receipt) |
|-------------|-----------|-------------------------------|--------------------------------|---------------------|
| baseline | 286.59 | 40.83 / 20.06 | 46.45 / 23.26 | 7.0x |
| **(a) implemented [MEASURED]** | **189.58** | **27.01 / 13.27** | **32.63 / 16.47** | **4.9x** |
| (a) + remaining (a)-class (R4/R5/R6/R7 ceilings) | ~173 | 24.7 / 12.1 | 30.3 / 15.3 | 4.6x |
| (a)+(b) [B1 at ~6 Newton iters, derived] | ~99.6 | 14.2 / 7.0 | 19.8 / 10.2 | 3.1x |
| (a)+(b)+(c2) [semi-implicit, derived] | ~65 | 9.3 / 4.5 | 14.9 / 7.7 | 2.3x |
| (a)+(b)+(c2)+(c3) [O(n) FK ÷3, derived] | — | ~3.1 / 1.5 | ~8.3 / ~4.7 | 1.4x |
| (a)+(b)+(c2)+(c3) [O(n) FK ÷10] | — | ~0.9 / 0.45 | ~6.1 / ~3.6 | 1.1x |
| C4 (GPU batched FK — off the CPU tick) | — | — | — | < 1x |

**THE VERDICT (plainly): no composition of (a) and (b) reaches the 3.33 ms
budget — (a) is implemented and measured at 33.9% of FK evaluates (4.9x budget at
the receipt state); adding B1's full certificate work reaches only ~3.1x. The
budget is reached ONLY by the (c)-class stack — an integration-order change PLUS
an O(n) recurrent FK, i.e. an engine architecture change through the full
certificate — or by C4, the GPU batched kernels. The CPU engine's role therefore
STAYS reference/oracle while production throughput rides the GPU batched path:
the deployment split is CONFIRMED, not refuted.**

Prediction grading (prereg P1-P4): P1 GREEN (exact reconciliation, 0 difference —
after F1 fired on the missing site and was resolved); P2 REFUTED (the (a)-class
is 33.9%, not single-digit); P3 CONFIRMED IN SUBSTANCE (the material next lever is
the bisection class, ~2.3x loop-level with (a), still short of budget alone — the
factorization-reuse member of the class is ≤1.4% and rejected by proportionality);
P4 CONFIRMED (only (c) reaches budget).
