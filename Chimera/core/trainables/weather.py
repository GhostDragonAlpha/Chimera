"""weather — the UWeatherSubsystem storm/gust cadence, as a trainable domain.

The genome is lifted straight out of the WIND table in CHIMERA_VISION.py
(UWeatherSubsystem.Bind / TickWeather, lines 3641-3698). THE DSL IS THE GENOME —
same discipline as core/trainables/economy.py: these numbers currently change only
when a human edits them by hand, so they are DATA and can be TRAINED.

WHAT UWeatherSubsystem ACTUALLY DOES (CHIMERA_VISION.py:3641-3698)
--------------------------------------------------------------------
Gusts fire every `gust_period_s` seconds (a brief bump to WIND["gust"]); wind
otherwise lerps toward `breeze` by day / `calm` by night. Roughly every
`storm_period_days` days a storm begins, lasting `storm_duration_min` minutes at
wind speed ~WIND["storm"]. When a storm ENDS, EVERY footprint whose surface is not
METAL is wiped UNCONDITIONALLY:

    game.footprints = [fp for fp in game.footprints if fp[2] == "METAL"]
    game.event_bus.OnStorm.Broadcast(FStormEvent("passed", before - len(game.footprints)))

That is Law 4's memento mori made mechanical: sand (and BASIN — SURFACE_TABLE,
CHIMERA_VISION.py:3559) footprints are not permanent; METAL ones are. THE LAW-4
TENSION (docs/THE_COMPOSITIONAL_WORLD_MODEL.md S4): erasure must happen often
enough to ACHE (footprints are not a permanent scrapbook) and rarely enough that
prints MATTER (a player can walk out, come back, and still find their own tracks)
— a relationship between how long a footprint survives and how often storms recur,
not a single number either an LLM or a human could just assert.

THE ANCHOR RULE (read carefully — this is where a naive port gets it wrong): the
source draws the NEXT storm's day by adding a fresh period sample to the CURRENT
`_next_storm_day` (`self._next_storm_day += rng.uniform(*WIND["storm_period_days"])`,
CHIMERA_VISION.py:3689) — i.e. the gap between consecutive storm STARTS is exactly
`uniform(*storm_period_days)`, independent of how long any storm itself lasted.
This module anchors the same way (`next_storm_day = storm_start_day + uniform(period)`);
anchoring off the storm's END instead would silently inflate every gap by the
storm's own duration and invent a coupling the source does not have.

THIS MODULE REPORTS FACTS, NOT OPINIONS. It measures. docs/objectives/weather.json
(LLM-authored) says which facts are GOOD.

THE SIMULATED PLAYER is a modestly active wanderer leaving sand/basin footprints as
a Poisson process at a fixed rate (PRINT_RATE_PER_DAY — a SIM SETTING, like
economy.py's SIM_HOURS/STATIONS, not a genome locus): frequent enough that storm
CADENCE, not player idleness, is what is actually being tested. A footprint's
lifetime is measured from its creation to the moment the storm that follows it
ENDS (when the unconditional wipe actually fires) — not to when that storm begins.

HONEST EVAL (TRAINING_PROTOCOL.md S3.5): the storm/gust process is genuinely
stochastic (`rng.uniform` draws every cycle), so a single run is a coin toss.
measure() runs N_RESTARTS independent, FIXED-SEED simulations of SIM_DAYS each and
pools/worst-cases across them — mean for context, worst for what the objective
must actually bind (the same distance / distance_worst / robustness split used by
core/trainables/brain_gpu.py). Fixed seeds (EVAL_SEED + r), not genome-derived ones,
so every genome is tested against the identical set of restarts — otherwise the
comparison across the population would itself be a lottery.
"""

from __future__ import annotations

import copy
import math
import random

# --- sim settings (NOT genome: these are the test conditions, not the game) ----
HOURS_PER_DAY = 27.0            # CHIMERA_VISION.py:3551 DAY_LENGTH_HOURS
NIGHT_FRACTION = 0.40           # IsNight(): t < 0.20 or t > 0.80 -> 40% of every day
                                 # (CHIMERA_VISION.py:3624-3626) is the "calm" baseline
GUST_PULSE_HOURS = 8.0 / 3600.0  # assumed perceptual decay time of one gust's
                                 # whoosh (~ the seed's OWN gust_period_s floor,
                                 # 8s) before wind reads as "resting" again — a
                                 # SIM CONSTANT for the audio/vfx read, not part
                                 # of WIND; documented, not invented as physics.
PRINT_RATE_PER_DAY = 30.0        # a modestly active wanderer's sand-footprint rate
SIM_DAYS = 250.0                 # in-game 27h days simulated PER RESTART
MAX_STORM_CYCLES = 1000          # for-loop bound -- TOTAL, never a while. Covers
                                 # even the mutated floor of ~0.5 days/storm twice over.
N_RESTARTS = 16                  # honest eval: N randomized seeds, keep the WORST
                                 # (same N as brain_gpu.py's precedent)
EVAL_SEED = 20260717             # fixed base; restarts are EVAL_SEED+r for every
                                 # genome alike, so "worst of N" compares apples to apples


def seed() -> dict:
    """The live WIND table, CHIMERA_VISION.py:1724-1726:

        WIND = dict(calm=2.0, breeze=6.0, gust=12.0, storm=24.0,
                    gust_period_s=(8.0, 30.0), storm_duration_min=(18.0, 45.0),
                    storm_period_days=(5.0, 9.0))

    Flattened so every bound is its OWN mutable locus — mutate() must reach lo
    AND hi of each pair independently, or half the genome is a dead gene.
    """
    return {
        "calm": 2.0,
        "breeze": 6.0,
        "gust": 12.0,
        "storm": 24.0,
        "gust_period_s_lo": 8.0,
        "gust_period_s_hi": 30.0,
        "storm_duration_min_lo": 18.0,
        "storm_duration_min_hi": 45.0,
        "storm_period_days_lo": 5.0,
        "storm_period_days_hi": 9.0,
    }


def _jit(v: float, frac: float, lo: float, hi: float, rng: random.Random) -> float:
    return max(lo, min(hi, v * (1.0 + rng.uniform(-frac, frac))))


def mutate(g: dict, rng: random.Random) -> dict:
    """Every one of the ten loci is jittered UNCONDITIONALLY on every call — no
    dead genes: all start nonzero and every field always has a nonzero chance to
    move in EITHER direction from wherever it currently sits, so the optimiser can
    reach anywhere from the seed (TRAINING_PROTOCOL.md S6's dead-gene trap: a locus
    only jittered when already nonzero, or only ever pushed one way, is a locus
    that cannot actually be searched).

    Ordering is re-clamped after jitter: calm<=breeze<=gust<=storm, and every
    lo<=hi pair. That is a DEFINITIONAL invariant of what these labels mean (a
    "gust" slower than the ambient "breeze" is not a gust) — the same discipline
    as economy.py's "a station never pays more than it charges: that is a free
    bug, not a design choice, so it is not in the search space." It is not taste.
    """
    d = copy.deepcopy(g)

    d["calm"] = _jit(d["calm"], 0.25, 0.2, 10.0, rng)
    d["breeze"] = _jit(d["breeze"], 0.25, 1.0, 20.0, rng)
    d["gust"] = _jit(d["gust"], 0.25, 2.0, 40.0, rng)
    d["storm"] = _jit(d["storm"], 0.25, 5.0, 80.0, rng)
    d["breeze"] = max(d["breeze"], d["calm"] + 0.1)
    d["gust"] = max(d["gust"], d["breeze"] + 0.1)
    d["storm"] = max(d["storm"], d["gust"] + 0.1)

    d["gust_period_s_lo"] = _jit(d["gust_period_s_lo"], 0.30, 2.0, 120.0, rng)
    d["gust_period_s_hi"] = _jit(d["gust_period_s_hi"], 0.30, 2.0, 300.0, rng)
    d["gust_period_s_hi"] = max(d["gust_period_s_hi"], d["gust_period_s_lo"] + 1.0)

    d["storm_duration_min_lo"] = _jit(d["storm_duration_min_lo"], 0.30, 3.0, 240.0, rng)
    d["storm_duration_min_hi"] = _jit(d["storm_duration_min_hi"], 0.30, 3.0, 480.0, rng)
    d["storm_duration_min_hi"] = max(d["storm_duration_min_hi"], d["storm_duration_min_lo"] + 1.0)

    d["storm_period_days_lo"] = _jit(d["storm_period_days_lo"], 0.30, 0.5, 60.0, rng)
    d["storm_period_days_hi"] = _jit(d["storm_period_days_hi"], 0.30, 0.5, 90.0, rng)
    d["storm_period_days_hi"] = max(d["storm_period_days_hi"], d["storm_period_days_lo"] + 0.1)

    return d


def _simulate_one(g: dict, rng: random.Random) -> dict:
    """One restart: SIM_DAYS of in-game time, event-driven per STORM CYCLE (never
    per-tick — a storm cycle is the natural grain of this genome; nothing here
    needs 8-30 SECOND resolution to report day-scale statistics honestly).

    TOTAL: bounded `for _cycle in range(MAX_STORM_CYCLES)`, never a `while`.
    """
    day_phase_start = 0.0
    next_storm_day = rng.uniform(g["storm_period_days_lo"], g["storm_period_days_hi"])

    gaps: list = []              # days between successive storm STARTS
    durations_h: list = []       # storm durations, hours
    erasure_fracs: list = []     # fraction of pre-existing sand/basin prints wiped, per storm
    lifetimes_days: list = []    # age (days, creation -> the wipe at storm END) of the
                                 # oldest surviving print erased by each storm
    storm_hours_total = 0.0
    prev_storm_start = None
    mean_gust_h = ((g["gust_period_s_lo"] + g["gust_period_s_hi"]) * 0.5) / 3600.0

    for _cycle in range(MAX_STORM_CYCLES):
        if day_phase_start >= SIM_DAYS:
            break

        storm_start_day = next_storm_day
        phase_days = max(0.0, storm_start_day - day_phase_start)

        # Footprints laid during this calm/breeze/gust phase: a Poisson arrival
        # process at PRINT_RATE_PER_DAY. The FIRST print's arrival after the phase
        # starts is Exponential(rate) -- so the oldest surviving print's age is
        # (phase_days - first_arrival), or there simply were NONE if the phase is
        # shorter than the wait for a first footstep. That is the concrete Law-4
        # "too often" failure mode: a phase so short nothing gets laid down before
        # the next wipe -- not asserted, MEASURED (had_prints can be False).
        first_arrival = rng.expovariate(PRINT_RATE_PER_DAY)
        had_prints = first_arrival <= phase_days
        oldest_age_at_storm_start = (phase_days - first_arrival) if had_prints else 0.0

        dur_min = rng.uniform(g["storm_duration_min_lo"], g["storm_duration_min_hi"])
        dur_days = (dur_min / 60.0) / HOURS_PER_DAY
        durations_h.append(dur_min / 60.0)
        storm_hours_total += dur_min / 60.0

        if prev_storm_start is not None:
            gaps.append(storm_start_day - prev_storm_start)
        prev_storm_start = storm_start_day

        storm_end_day = storm_start_day + dur_days
        if had_prints:
            # CHIMERA_VISION.py:3675 -- `fp[2] == "METAL"` is the ONLY survivor
            # clause: every sand/basin print present is wiped, unconditionally.
            # That is a measured FACT of the shipped mechanic, not a choice made
            # here (see the module docstring / this file's closure report).
            erasure_fracs.append(1.0)
            lifetimes_days.append(oldest_age_at_storm_start + dur_days)

        # ANCHOR RULE: matches CHIMERA_VISION.py:3689 exactly -- the next period
        # sample is added to THIS storm's START day, not its end.
        next_storm_day = storm_start_day + rng.uniform(
            g["storm_period_days_lo"], g["storm_period_days_hi"])
        day_phase_start = storm_end_day

    sim_end_day = max(day_phase_start, 1e-6)
    storm_time_fraction = min(1.0, storm_hours_total / max(sim_end_day * HOURS_PER_DAY, 1e-6))
    non_storm_fraction = 1.0 - storm_time_fraction
    gust_occupancy = min(1.0, GUST_PULSE_HOURS / max(mean_gust_h, 1e-9))
    dead_calm_fraction = max(0.0, min(1.0,
        non_storm_fraction * NIGHT_FRACTION * (1.0 - gust_occupancy)))

    return {
        "gaps": gaps, "durations_h": durations_h,
        "erasure_fracs": erasure_fracs, "lifetimes_days": lifetimes_days,
        "storm_time_fraction": storm_time_fraction,
        "dead_calm_fraction": dead_calm_fraction,
        "storms_observed": float(len(durations_h)),
    }


def measure(g: dict) -> dict:
    """N_RESTARTS independent FIXED-seed runs of SIM_DAYS each; pool the raw
    per-storm samples for the day-to-day statistics and keep BOTH the mean (for
    context) and the worst-case across restarts (what an objective must actually
    bind) for every measure that names a failure mode -- the distance /
    distance_worst / robustness pattern from TRAINING_PROTOCOL.md S3.5.

    TOTAL: `for r in range(N_RESTARTS)`, never a `while`. Pure function of `g` —
    all randomness is internally, deterministically seeded (EVAL_SEED + r), so
    this is safe to call from any worker process and always returns the same
    facts for the same genome.
    """
    all_gaps: list = []
    all_durations: list = []
    all_erasure: list = []
    all_lifetimes: list = []
    dead_calm_per_restart: list = []
    storm_time_per_restart: list = []
    storms_per_restart: list = []

    for r in range(N_RESTARTS):
        rng = random.Random(EVAL_SEED + r)
        out = _simulate_one(g, rng)
        all_gaps.extend(out["gaps"])
        all_durations.extend(out["durations_h"])
        all_erasure.extend(out["erasure_fracs"])
        all_lifetimes.extend(out["lifetimes_days"])
        dead_calm_per_restart.append(out["dead_calm_fraction"])
        storm_time_per_restart.append(out["storm_time_fraction"])
        storms_per_restart.append(out["storms_observed"])

    def mean(xs: list) -> float:
        return sum(xs) / len(xs) if xs else 0.0

    def var(xs: list) -> float:
        if len(xs) < 2:
            return 0.0
        m = mean(xs)
        return sum((x - m) ** 2 for x in xs) / len(xs)

    gap_mean = mean(all_gaps)
    gap_min = min(all_gaps) if all_gaps else 0.0
    gap_max = max(all_gaps) if all_gaps else 0.0
    life_mean = mean(all_lifetimes)
    life_max = max(all_lifetimes) if all_lifetimes else 0.0

    gust_mean_s = (g["gust_period_s_lo"] + g["gust_period_s_hi"]) * 0.5
    gust_std_s = (g["gust_period_s_hi"] - g["gust_period_s_lo"]) / math.sqrt(12.0)
    gust_cv = gust_std_s / max(gust_mean_s, 1e-9)

    return {
        # "mean/var days between storms"
        "storm_interval_days_mean": gap_mean,
        "storm_interval_days_var": var(all_gaps),
        "storm_interval_days_min": gap_min,
        "storm_interval_days_max": gap_max,
        # "storm duration"
        "storm_duration_hours_mean": mean(all_durations),
        "storm_duration_hours_max": max(all_durations) if all_durations else 0.0,
        # "fraction of sand footprints erased per storm" -- see the module
        # docstring: this is expected to sit at exactly 1.0, because the source
        # mechanic is an unconditional wipe, not a WIND-tunable rate.
        "sand_erasure_fraction_mean": mean(all_erasure),
        "sand_erasure_fraction_min": min(all_erasure) if all_erasure else 0.0,
        # "longest footprint lifetime"
        "longest_footprint_lifetime_days": life_max,
        "mean_footprint_lifetime_days": life_mean,
        "lifetime_period_ratio": life_mean / max(gap_mean, 1e-6),
        # "dead-calm fraction"
        "dead_calm_fraction_mean": mean(dead_calm_per_restart),
        "dead_calm_fraction_worst": max(dead_calm_per_restart) if dead_calm_per_restart else 0.0,
        # "no permanent storm"
        "storm_time_fraction_mean": mean(storm_time_per_restart),
        "storm_time_fraction_worst": max(storm_time_per_restart) if storm_time_per_restart else 0.0,
        # "gust interval distribution"
        "gust_interval_mean_s": gust_mean_s,
        "gust_interval_cv": gust_cv,
        # context / anti-lottery diagnostics
        "storms_observed": mean(storms_per_restart),
        "robustness": (gap_min / max(gap_mean, 1e-6)) if all_gaps else 0.0,
    }
