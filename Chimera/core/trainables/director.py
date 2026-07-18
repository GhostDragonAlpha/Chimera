"""director -- UDirectorSubsystem's encounter ecology, as a trainable domain.

THE COMPOSITIONAL WORLD MODEL, rung 1 (docs/THE_COMPOSITIONAL_WORLD_MODEL.md Sec.4):
"UDirectorSubsystem | stranger cadence, SCENARIOS mix, can_pay fraction, pirate trigger |
An ecology: encounter pressure inside active_dots [2,24]; the design rules stay invariant
under training (first stranger of a generation cannot pay; pirates only bother the visibly
rich during storms) -- those are HARD gates, not tunables."

THE GENOME IS LIFTED VERBATIM FROM CHIMERA_VISION.py's UDirectorSubsystem (class body starts
line 3871) -- THE DSL/VISION IS THE GENOME, same discipline as core/trainables/economy.py.
Every genome field below cites the exact vision line it was read from. Nothing here is
invented; where the vision leaves a number to the PLAYER's pacing rather than a stated
constant (a stranger's wait for a response has no timeout -- Task_PointAtNeed just holds
"encounter" forever), a modelling assumption stands in for a competent/attentive player,
labelled exactly as such -- the same discipline economy.py uses for its "greedy arbitrageur".

THIS MODULE REPORTS FACTS, NOT OPINIONS. It never says a concurrent-dot count or a pirate
spawn is GOOD or BAD -- that judgement lives entirely in docs/objectives/director.json.

WHAT THE DIRECTOR ACTUALLY DOES (TickDirector, CHIMERA_VISION.py:3913-3934)
-----------------------------------------------------------------------
    every tick:
        if now >= next_stranger_day:
            spawn a "stranger" on a golden-angle bearing 260m out, with a random need
            from SCENARIOS; the FIRST stranger of a generation can NEVER pay (Law 2 --
            the Yard teaches you to help before it lets you trade); every later one can
            pay with probability 0.35
        if now >= next_trader_day:
            spawn a "trader" near a station who always can_pay
        if credits > 200 and storm_active and roll(0.02 * dt):
            spawn a "pirate" -- ONLY reachable through that exact conjunction

A dot lives from spawn until its FSM reaches "gone" (Task_Leave, walked >300m away) --
the Mass entity is destroyed at that point (UMassActorSpawnerSubsystem.SyncActorization).
That lifetime, integrated over the whole world at any instant, IS "concurrent dots" --
the quantity Malcolm's `active_dots [2,24]` wall governs.

THE TWO DESIGN RULES ARE ENCODED AS **REACHABLE GENOME LOCI**, NOT ASSERTIONS
------------------------------------------------------------------------------
The vision writes both rules as unconditional Python, with no tunable number at all:
    can_pay = (False if first_of_gen else self.rng.random() < 0.35)
    if game.credits > 200 and game.weather.storm_active and self.rng.random() < 0.02*dt:

TRAINING_PROTOCOL.md Sec.6, the dead-gene trap: "A locus the optimiser cannot reach is a
locus that does not exist." A hard gate that mutate() can never actually trip is a comment,
not a test. So each rule gets a probability locus SEEDED AT THE VISION'S VALUE (0.0 --
exactly what the unconditional `if` does) that mutate() can walk away from zero:
    first_stranger_can_pay_fraction    (seed 0.0)
    pirate_storm_gate_bypass_fraction  (seed 0.0)
    pirate_wealth_gate_bypass_fraction (seed 0.0)
Only because these loci are reachable does docs/objectives/director.json's hard gate mean
anything -- it has something real to catch, not just a rule that was never going to break.
"""

from __future__ import annotations

import copy
import heapq
import math
import random

# =============================================================================
# GENOME vs SIM CONSTANTS -- exactly the split economy.py draws ("sim settings (NOT
# genome: these are the test conditions, not the game)"). Everything in this section is
# either a fixed vision fact the genome does not own (the day length; another subsystem's
# weather clock -- a SEAM explicitly deferred to joint training later, THE_COMPOSITIONAL_
# WORLD_MODEL.md Sec.5), or a labelled test-harness assumption needed to run ANY simulation
# at all (how many generations to sample; a stand-in for how fast a player responds).
# =============================================================================

DAY_LENGTH_HOURS = 27.0            # CHIMERA_VISION.py:3551 DAY_LENGTH_HOURS = 27.0

# --- test-harness sizing (NOT genome) ---------------------------------------------------
N_GENERATIONS = 10                  # generations (lives) simulated per restart
DAYS_PER_GENERATION = 9.0           # a plausible life span between Wills
N_RESTARTS = 6                      # honest eval, worst-of-N (TRAINING_PROTOCOL Sec.3.5).
                                     # walker.py uses 4 and says so plainly: this is a
                                     # declared compromise against wall-clock cost, not a
                                     # silent one -- 6 restarts x 10 generations already
                                     # gives every hard gate 60 independent lives to break.
EVAL_SEED = 20260717
MAX_EVENTS = 20_000                 # totality ceiling per restart: a `for`, never a
                                     # `while True` -- no genome, however adversarial its
                                     # mutated cadence, can hang the trainer.

# --- weather clock: ANOTHER subsystem's data (WIND, CHIMERA_VISION.py:1724), fixed here
# as an exogenous driver exactly like economy.py's SIM_HOURS. The director x weather seam
# is named for later JOINT training (Sec.5); rung 1 trains the director alone and still
# needs a storm clock to exercise the pirate gate honestly on both sides. ------------------
STORM_PERIOD_MIN_DAYS = 5.0                  # WIND["storm_period_days"] = (5.0, 9.0)
STORM_PERIOD_MAX_DAYS = 9.0
STORM_DURATION_MIN_H = 18.0 / 60.0           # WIND["storm_duration_min"] = (18.0, 45.0) MIN
STORM_DURATION_MAX_H = 45.0 / 60.0

# --- player wealth: CHIMERA_VISION.py facts the director reads but does not own ---------
START_CREDITS = 40.0                # ChimeraGame.__init__: self.credits = 40.0 (line 4164)
GEN_CREDIT_CARRY = 0.5              # UGenerationSubsystem.EndLife: credits = round(credits*0.5)
                                     # (line 3859) -- the heir starts poorer (a DIFFERENT
                                     # trainable's rule; used here only so wealth realistically
                                     # dips across generations instead of climbing forever)

# --- Mass-entity walk geometry, lifted verbatim from the vision's own crowd code, not
# invented: the ambient speed and the archetypes' own spawn offsets / leave threshold. ---
AMBIENT_SPEED_MPS = 1.2                       # UMassMovementProcessor.Execute: vel = to_t*1.2
STRANGER_SPAWN_DIST_M = 260.0                  # TickDirector: ppos + bearing * 260.0
_PIRATE_SPAWN_OFFSET_M = (180.0, 40.0)         # TickDirector: ppos + FVector(180, 40, 0)
PIRATE_SPAWN_DIST_M = math.hypot(*_PIRATE_SPAWN_OFFSET_M)   # ~184.4 m
LEAVE_GONE_DIST_M = 300.0                      # Task_Leave: loc.Dist2D(ptr) > 300.0
PIRATE_DEMAND_SECS = 8.0                       # Task_PirateDemand: DemandTimer > 8.0 -> Flee


def _hours_to_cover(distance_m: float) -> float:
    return (distance_m / AMBIENT_SPEED_MPS) / 3600.0


WALK_IN_STRANGER_DAYS = _hours_to_cover(STRANGER_SPAWN_DIST_M) / DAY_LENGTH_HOURS
WALK_IN_PIRATE_DAYS = _hours_to_cover(PIRATE_SPAWN_DIST_M) / DAY_LENGTH_HOURS
WALK_OUT_DAYS = _hours_to_cover(LEAVE_GONE_DIST_M) / DAY_LENGTH_HOURS
PIRATE_DEMAND_DAYS = (PIRATE_DEMAND_SECS / 3600.0) / DAY_LENGTH_HOURS

# A "day" in every cadence above is a DAY_LENGTH_HOURS=27 REAL-hour unit (CHIMERA_VISION.py's
# own `now_days = sun.day + sun.time_h/DAY_LENGTH_HOURS`), NOT a 24h calendar day -- so
# converting a duration FROM day-units TO real seconds (needed for the pirate rate, which is
# denominated in real seconds: `rng.random() < 0.02*dt`) must multiply by this, not by 86400.
DAY_UNIT_SECONDS = DAY_LENGTH_HOURS * 3600.0

# --- THE genuine modelling assumption (labelled, exactly like economy.py's "greedy
# arbitrageur"): the vision leaves a stranger's dwell entirely to the PLAYER's own pacing --
# Task_PointAtNeed holds "encounter" with NO timeout until the player gestures back (there is
# no "Erisaid, forever listening" flavour text by accident -- CHIMERA_VISION.py:1953 uses the
# identical FSM state for a shrine NPC that waits with no clock at all). A stand-in patient
# player is needed to get a concurrent-dot count at all, and it must be GENEROUS: a player
# who rushes every stranger within minutes would empty the world by construction regardless
# of what the director does, which would make Malcolm's active_dots FLOOR unreachable by any
# cadence mutate() can reach (verified: even at mutate()'s densest allowed cadence, a 3-hour
# mean response left concurrent_dots_p95 pinned at 1.0 -- the floor was structurally
# unreachable, not merely untrained). A full day-night cycle of patience is the conservative
# reading of "no timeout", not an invented mechanic.
RESPONSE_MEAN_DAYS = 1.0                             # ~1 day-night cycle (27h) of patience
TRADER_DWELL_MEAN_DAYS = 0.4 / DAY_LENGTH_HOURS      # ~24 minutes to be noticed + wave --
                                                      # traders do NOT wait (BT_TRADER's
                                                      # selector falls straight to Task_Leave
                                                      # the instant "within 60m and not yet
                                                      # greeted" is false), so this stays short

SCENARIO_KEYS = ("o2", "parts", "water", "warmth", "burial", "ride")   # SCENARIOS, line 3876


# =============================================================================
# seed() -- the live UDirectorSubsystem numbers
# =============================================================================

def seed() -> dict:
    """The live vision numbers. Verbatim where the vision gives them; the three
    design-rule loci seeded at 0.0 -- exactly what the vision's unconditional `if`s do --
    so mutate() can walk them away from zero and the hard gates have something to catch."""
    return {
        # UDirectorSubsystem.Bind (line 3886): self.stranger_cadence_days = (1.0, 2.2).
        # REAL GAME value -- the demo-only override at __main__ (line 4510, (0.004, 0.010))
        # is explicitly commented "demo compression" and is not the design number.
        "stranger_cadence_min_days": 1.0,
        "stranger_cadence_max_days": 2.2,

        # TickDirector (line 3926): self._next_trader_day = now + rng.uniform(0.7, 1.5)
        "trader_cadence_min_days": 0.7,
        "trader_cadence_max_days": 1.5,

        # SCENARIOS (line 3876): rng.choice() over an unweighted 6-item list IS a uniform
        # categorical with 6 equal weights -- restating it explicitly changes nothing about
        # current behaviour, it only makes the mix a locus mutation can reach.
        "scenario_weights": {k: 1.0 for k in SCENARIO_KEYS},

        # TickDirector (line 3923): can_pay = (False if first_of_gen else rng.random()<0.35)
        "can_pay_fraction": 0.35,

        # THE DEAD-GENE-TRAP LOCI (2026-07-17) -- see module docstring.
        "first_stranger_can_pay_fraction": 0.0,
        "pirate_storm_gate_bypass_fraction": 0.0,
        "pirate_wealth_gate_bypass_fraction": 0.0,

        # TickDirector (line 3932): credits > 200 and storm_active and rng.random()<0.02*dt
        "pirate_wealth_threshold": 200.0,
        "pirate_spawn_rate_per_sec": 0.02,
    }


# =============================================================================
# mutate() -- every locus reachable (TRAINING_PROTOCOL Sec.6, the dead-gene trap)
# =============================================================================

def mutate(g: dict, rng: random.Random) -> dict:
    d = copy.deepcopy(g)

    def jit(v, frac, lo, hi):
        return max(lo, min(hi, v * (1.0 + rng.uniform(-frac, frac))))

    def jit_prob(v, delta, lo=0.0, hi=1.0):
        return max(lo, min(hi, v + rng.uniform(-delta, delta)))

    if rng.random() < 0.5:
        d["stranger_cadence_min_days"] = jit(d["stranger_cadence_min_days"], 0.25, 0.2, 4.0)
    if rng.random() < 0.5:
        d["stranger_cadence_max_days"] = jit(d["stranger_cadence_max_days"], 0.25, 0.3, 6.0)
    if d["stranger_cadence_min_days"] > d["stranger_cadence_max_days"]:
        d["stranger_cadence_min_days"], d["stranger_cadence_max_days"] = (
            d["stranger_cadence_max_days"], d["stranger_cadence_min_days"])

    if rng.random() < 0.5:
        d["trader_cadence_min_days"] = jit(d["trader_cadence_min_days"], 0.25, 0.2, 4.0)
    if rng.random() < 0.5:
        d["trader_cadence_max_days"] = jit(d["trader_cadence_max_days"], 0.25, 0.3, 6.0)
    if d["trader_cadence_min_days"] > d["trader_cadence_max_days"]:
        d["trader_cadence_min_days"], d["trader_cadence_max_days"] = (
            d["trader_cadence_max_days"], d["trader_cadence_min_days"])

    for k in d["scenario_weights"]:
        if rng.random() < 0.4:
            d["scenario_weights"][k] = max(0.05, jit(d["scenario_weights"][k], 0.35, 0.05, 5.0))

    if rng.random() < 0.5:
        d["can_pay_fraction"] = jit_prob(d["can_pay_fraction"], 0.08)

    # THE DEAD-GENE TRAP, PAID: these three MUST be reachable unconditionally, not jittered
    # "only if already > 0" (the exact seg_taper mistake TRAINING_PROTOCOL.md Sec.6 records) --
    # otherwise the paired hard gate in the objective is a decoration, never a test.
    if rng.random() < 0.3:
        d["first_stranger_can_pay_fraction"] = jit_prob(d["first_stranger_can_pay_fraction"], 0.06)
    if rng.random() < 0.3:
        d["pirate_storm_gate_bypass_fraction"] = jit_prob(d["pirate_storm_gate_bypass_fraction"], 0.06)
    if rng.random() < 0.3:
        d["pirate_wealth_gate_bypass_fraction"] = jit_prob(d["pirate_wealth_gate_bypass_fraction"], 0.06)

    if rng.random() < 0.4:
        d["pirate_wealth_threshold"] = jit(d["pirate_wealth_threshold"], 0.3, 20.0, 2000.0)
    if rng.random() < 0.4:
        d["pirate_spawn_rate_per_sec"] = jit(d["pirate_spawn_rate_per_sec"], 0.3, 0.0005, 0.15)

    return d


# =============================================================================
# measure() -- FACTS only. Bounded (a `for`, never a `while True`). Deterministic per seed.
# =============================================================================

def _weighted_choice(weights: dict, rng: random.Random) -> str:
    total = sum(max(0.0, v) for v in weights.values())
    if total <= 0.0:
        return SCENARIO_KEYS[0]
    r = rng.uniform(0.0, total)
    upto = 0.0
    for k in SCENARIO_KEYS:
        upto += max(0.0, weights.get(k, 0.0))
        if r <= upto:
            return k
    return SCENARIO_KEYS[-1]


def _poisson_bounded(rate_per_sec: float, dt_secs: float, rng: random.Random, cap: int = 200) -> int:
    """Knuth's algorithm, BOUNDED: a `for` over `cap+1` draws, never a `while`, so no
    adversarially-mutated rate can hang the trainer. `cap` is a totality safeguard, not a
    design number -- it is far above anything a sane genome should ever approach."""
    if rate_per_sec <= 0.0 or dt_secs <= 0.0:
        return 0
    lam = rate_per_sec * dt_secs
    if lam > 700.0:            # exp(-lam) underflows to 0.0 well before this
        return cap
    limit = math.exp(-lam)
    k, p = 0, 1.0
    for _ in range(cap + 1):
        k += 1
        p *= rng.random()
        if p <= limit:
            return min(k - 1, cap)
    return cap


def _weighted_percentile(hist: list, q: float) -> float:
    """Time-weighted percentile over (duration, concurrent_count) intervals -- the honest
    way to summarise a step function of counts sampled at irregular event times, rather than
    letting busy periods (many short intervals) outvote quiet ones (few long intervals)."""
    if not hist:
        return 0.0
    ordered = sorted(hist, key=lambda kv: kv[1])
    total = sum(dur for dur, _ in ordered)
    if total <= 0.0:
        return 0.0
    target = q * total
    cum = 0.0
    for dur, count in ordered:
        cum += dur
        if cum >= target:
            return float(count)
    return float(ordered[-1][1])


def _simulate_once(g: dict, rng: random.Random) -> dict:
    """One realisation of the encounter stream: event-driven (bounded by MAX_EVENTS), never
    a fixed-timestep tick loop -- storms (18-45 real minutes) and multi-day spawn cadences
    span four orders of magnitude, so a fixed dt is either too coarse to see a storm or too
    fine to be fast. Every event boundary is an exact moment a rate could have changed."""
    stranger_band = (g["stranger_cadence_min_days"], g["stranger_cadence_max_days"])
    trader_band = (g["trader_cadence_min_days"], g["trader_cadence_max_days"])
    scenario_weights = g["scenario_weights"]
    can_pay_fraction = g["can_pay_fraction"]
    first_pay_frac = g["first_stranger_can_pay_fraction"]
    storm_bypass = g["pirate_storm_gate_bypass_fraction"]
    wealth_bypass = g["pirate_wealth_gate_bypass_fraction"]
    pirate_threshold = g["pirate_wealth_threshold"]
    pirate_rate = g["pirate_spawn_rate_per_sec"]

    now = 0.0
    last_t = 0.0
    next_stranger = rng.uniform(0.0, stranger_band[1])       # phase-offset first arrival,
    next_trader = rng.uniform(0.0, trader_band[1])           # matching Bind's 0.5 / 0.8 offsets
    storm_active = False
    next_storm_change = rng.uniform(STORM_PERIOD_MIN_DAYS, STORM_PERIOD_MAX_DAYS)
    generation = 0
    gen_end = DAYS_PER_GENERATION
    gen_first_sent = False
    credits = START_CREDITS

    heap: list = []       # (gone_day, seq, archetype) -- min-heap, O(log n) next-despawn
    seq = 0
    live = 0

    weighted_sum = 0.0
    hist: list = []                    # (duration, concurrent_count)
    last_encounter = None
    gaps: list = []
    scenario_counts = {k: 0 for k in SCENARIO_KEYS}
    pirate_correct = 0
    pirate_violations = 0
    first_total = 0
    first_paid = 0

    for _ in range(MAX_EVENTS):
        events = [(next_stranger, "stranger"), (next_trader, "trader"),
                 (next_storm_change, "storm"), (gen_end, "gen_end")]
        if heap:
            events.append((heap[0][0], "gone"))
        t, kind = min(events, key=lambda e: e[0])

        dur = t - last_t
        if dur > 0.0:
            weighted_sum += live * dur
            hist.append((dur, live))

            wealthy = credits > pirate_threshold
            stormy = storm_active
            wealth_ok = wealthy or (rng.random() < wealth_bypass)
            storm_ok = stormy or (rng.random() < storm_bypass)
            if wealth_ok and storm_ok and pirate_rate > 0.0:
                n_pirates = _poisson_bounded(pirate_rate, dur * DAY_UNIT_SECONDS, rng)
                if n_pirates:
                    for _p in range(n_pirates):
                        seq += 1
                        gone = t + WALK_IN_PIRATE_DAYS + PIRATE_DEMAND_DAYS + WALK_OUT_DAYS
                        heapq.heappush(heap, (gone, seq, "pirate"))
                    live += n_pirates
                    if wealthy and stormy:
                        pirate_correct += n_pirates
                    else:
                        pirate_violations += n_pirates
        last_t = t
        now = t

        if kind == "gone":
            heapq.heappop(heap)
            live -= 1
        elif kind == "storm":
            if storm_active:
                storm_active = False
                next_storm_change = now + rng.uniform(STORM_PERIOD_MIN_DAYS, STORM_PERIOD_MAX_DAYS)
            else:
                storm_active = True
                dur_h = rng.uniform(STORM_DURATION_MIN_H, STORM_DURATION_MAX_H)
                next_storm_change = now + dur_h / DAY_LENGTH_HOURS
        elif kind == "gen_end":
            generation += 1
            gen_end = now + DAYS_PER_GENERATION
            gen_first_sent = False
            credits *= GEN_CREDIT_CARRY
            if generation >= N_GENERATIONS:
                break
        elif kind == "stranger":
            next_stranger = now + rng.uniform(*stranger_band)
            need = _weighted_choice(scenario_weights, rng)
            scenario_counts[need] += 1
            is_first = not gen_first_sent
            gen_first_sent = True
            if is_first:
                first_total += 1
                can_pay = rng.random() < first_pay_frac
                if can_pay:
                    first_paid += 1
            else:
                can_pay = rng.random() < can_pay_fraction
            dwell = WALK_IN_STRANGER_DAYS + rng.expovariate(1.0 / RESPONSE_MEAN_DAYS) + WALK_OUT_DAYS
            seq += 1
            heapq.heappush(heap, (now + dwell, seq, "stranger"))
            live += 1
            if can_pay:
                credits += rng.uniform(8.0, 40.0)     # ambient trade income -- see docstring
            if last_encounter is not None:
                gaps.append(now - last_encounter)
            last_encounter = now
        elif kind == "trader":
            next_trader = now + rng.uniform(*trader_band)
            dwell = rng.expovariate(1.0 / TRADER_DWELL_MEAN_DAYS) + WALK_OUT_DAYS
            seq += 1
            heapq.heappush(heap, (now + dwell, seq, "trader"))
            live += 1
            credits += rng.uniform(8.0, 40.0)          # traders always resolve as a sale
            if last_encounter is not None:
                gaps.append(now - last_encounter)
            last_encounter = now

    total_time = now if now > 0.0 else 1e-6
    concurrent_mean = weighted_sum / total_time
    concurrent_p95 = _weighted_percentile(hist, 0.95)
    concurrent_max = max((c for _, c in hist), default=0)

    if gaps:
        gap_mean = sum(gaps) / len(gaps)
        gap_min = min(gaps)
        gap_var = sum((x - gap_mean) ** 2 for x in gaps) / len(gaps)
        gap_cv = (gap_var ** 0.5) / gap_mean if gap_mean > 0 else 0.0
    else:
        gap_mean = gap_min = gap_cv = 0.0

    total_scn = sum(scenario_counts.values())
    if total_scn > 0:
        ent = 0.0
        for c in scenario_counts.values():
            if c > 0:
                p = c / total_scn
                ent -= p * math.log2(p)
        ent_norm = ent / math.log2(len(SCENARIO_KEYS))
    else:
        ent_norm = 0.0

    return {
        "concurrent_dots_mean": concurrent_mean,
        "concurrent_dots_p95": concurrent_p95,
        "concurrent_dots_max": float(concurrent_max),
        "encounter_gap_mean_days": gap_mean,
        "encounter_gap_min_days": gap_min,
        "encounter_gap_cv": gap_cv,
        "scenario_entropy_norm": ent_norm,
        "pirate_spawns_correct": float(pirate_correct),
        "pirate_gate_violations": float(pirate_violations),
        "pirate_spawns_total": float(pirate_correct + pirate_violations),
        "first_stranger_paid_fraction": (first_paid / first_total) if first_total > 0 else 0.0,
        "generations_completed": float(generation),
        "days_simulated": total_time,
    }


def measure(g: dict) -> dict:
    """WORST of N_RESTARTS independent encounter-stream realisations (TRAINING_PROTOCOL
    Sec.3.5: "score every genome from N randomized initial conditions and keep the WORST").

    Unlike a physical gait, an encounter ecology has no privileged "restart 0" -- the
    vision's own director runs on its OWN independent RNG (`random.Random(seed ^ 0x5EED)`,
    CHIMERA_VISION.py:4206), so every restart here re-draws the WHOLE stochastic spawn /
    storm / scenario stream from a fresh seed. A single realisation is itself a coin toss on
    tail events (does a stranger and a trader ever pile up three deep at once?), so all
    N_RESTARTS are genuinely independent draws and the WORST is kept, per measure, in the
    direction that is actually bad for that measure:
      - hard design-rule violations (pirate gate, first-stranger-pay) -> MAX across restarts:
        any restart that breaks the rule condemns the genome, exactly as walker.py keeps a
        single exploded/degenerate restart as the whole verdict.
      - a two-sided band (concurrent dots, encounter gap) is reported as its two one-sided
        extremes (worst_low, worst_high) rather than picked via an internal band check --
        keeping the domain innocent of what counts as "in band" (that is the OBJECTIVE's
        job; see TRAINING_PROTOCOL.md Sec.1's three-part split).
      - scenario diversity -> MIN across restarts (least diverse draw is the worst one).
    """
    runs = [_simulate_once(g, random.Random(EVAL_SEED + 104729 * i)) for i in range(N_RESTARTS)]

    p95s = [r["concurrent_dots_p95"] for r in runs]
    means = [r["concurrent_dots_mean"] for r in runs]
    gap_means = [r["encounter_gap_mean_days"] for r in runs]

    return {
        "concurrent_dots_p95_worst_low": min(p95s),
        "concurrent_dots_p95_worst_high": max(p95s),
        "concurrent_dots_mean_of_restarts": sum(means) / len(means),
        "concurrent_dots_max_ever": max(r["concurrent_dots_max"] for r in runs),

        "encounter_gap_mean_worst_low": min(gap_means),
        "encounter_gap_mean_worst_high": max(gap_means),
        "encounter_gap_min_days_ever": min(r["encounter_gap_min_days"] for r in runs),
        "encounter_gap_cv_mean": sum(r["encounter_gap_cv"] for r in runs) / len(runs),

        "scenario_entropy_norm": min(r["scenario_entropy_norm"] for r in runs),

        "pirate_gate_violations": float(max(r["pirate_gate_violations"] for r in runs)),
        "pirate_spawns_correct_total": float(sum(r["pirate_spawns_correct"] for r in runs)),
        "pirate_spawns_total": float(sum(r["pirate_spawns_total"] for r in runs)),

        "first_stranger_paid_fraction": max(r["first_stranger_paid_fraction"] for r in runs),

        "generations_completed_min": float(min(r["generations_completed"] for r in runs)),
        "days_simulated_min": min(r["days_simulated"] for r in runs),
    }
