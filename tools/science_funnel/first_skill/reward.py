"""First-skill reward: the frozen shaping terms (runnable form of run_manifest.json).

RULE-0 STATUS: this file is the executable half of the prereg frozen at
tools/science_funnel/validation/first_skill_prestage_20260922/run_manifest.json
(branch agent/first-skill-prestage-20260922, frozen BEFORE any training exists).
Its constants are banked measurements or derived inequalities, never taste:

  V_SEED      0.7636247890 m/s  -- the walk's own measured envelope ceiling
                                    (command_adapter receipt seed_v_m_s; the
                                    scene-derived no-slip entry speed the ship
                                    walk demonstrably carries)
  T_DECISION  15/300 s          -- the banked 20 Hz decision clock over 300 Hz
                                    physics (ZOH value-only, F-ZOH-CLOCK)
  D_WP        0.5 m             -- reachable inside the eval window at the banked
                                    in-band mid command (see the manifest)
  W_HEAD      0.1               -- the largest declared candidate satisfying the
                                    frozen SUBORDINATION INEQUALITY (below)

SHAPING ONLY, NEVER ACCEPTANCE. The hard conditions (no fall, reach, CoT band)
live in acceptance.py and nowhere else. There is NO alive bonus (the crouch
disease), NO terminal term (acceptance leaking into the reward), NO effort term
(unmeasured Joule scale), NO absolute speed target (the contradictory-reward
failure training_gate.py exists to refuse).
"""
from __future__ import annotations

import math

# --- frozen constants (each traceable to a banked receipt; see manifest) ---
V_SEED = 0.7636247890          # m/s, command_adapter receipt (R-band ceiling)
PHYSICS_HZ = 300               # banked clock
HOLD_TICKS = 15                # banked decision clock (policy_hz * hold == physics)
T_DECISION = HOLD_TICKS / PHYSICS_HZ            # 0.05 s
PROGRESS_QUANTUM = V_SEED * T_DECISION          # 0.0381812394 m per decision
D_WP = 0.5                     # m, the skill-1 waypoint distance
W_HEAD = 0.1                   # dimensionless, subordination-derived
W_HEAD_CANDIDATES = (0.05, 0.1, 0.2, 0.5, 1.0)  # the declared candidate set
N_DECISIONS_PER_EPISODE = 20   # 300-tick cap / 15-tick hold
SUBORDINATION_SHARE = 1.0 / 3.0


def progress_quantum() -> float:
    """One decision of travel at the walk's own measured ceiling."""
    return PROGRESS_QUANTUM


def subordination_ok(w_head: float = W_HEAD) -> bool:
    """THE FROZEN SUBORDINATION INEQUALITY.

    The heading term's worst-case episode total (2 * w * N_dec, the term is in
    [-2w, 0] per decision) must not exceed SUBORDINATION_SHARE of the progress
    term's reach-scale total (D_WP / PROGRESS_QUANTUM): no amount of heading
    shaping can buy a non-reaching episode above a reaching one.
    """
    heading_worst = 2.0 * w_head * N_DECISIONS_PER_EPISODE
    progress_reach_scale = D_WP / PROGRESS_QUANTUM
    return heading_worst <= SUBORDINATION_SHARE * progress_reach_scale


def derived_w_head() -> float:
    """Largest declared candidate satisfying the subordination inequality.

    Frozen derivation: pick from W_HEAD_CANDIDATES; ties to the larger. This is
    a derivation over a declared order, not a sweep over rewards -- one
    inequality, evaluated once, before any run.
    """
    ok = [w for w in sorted(W_HEAD_CANDIDATES) if subordination_ok(w)]
    if not ok:
        raise ValueError("subordination inequality unsatisfiable over the declared candidates")
    return ok[-1]


def r_progress(prev_com_x_along: float, com_x_along: float, d_wp: float = D_WP) -> float:
    """Waypoint-progress shaping for one decision.

    Displacement along the body-to-waypoint axis, normalized by one decision of
    seed-speed travel, clipped to [-1, 1]. Reads exactly +1 per decision at the
    banked seed speed. Normalized to O(1) by construction.
    """
    delta = (com_x_along - prev_com_x_along) / PROGRESS_QUANTUM
    return max(-1.0, min(1.0, delta))


def r_heading(com_vel_x_heading: float, com_vel_y_heading: float,
              w_head: float = W_HEAD) -> float:
    """Heading-alignment shaping for one decision.

    psi_err = angle of the CoM velocity vector off the body-to-waypoint axis.
    For skill-1 the waypoint is dead ahead on the heading axis, so psi_err is
    the velocity's off-axis angle from the declared obs channels
    (com_vel_x_heading, com_vel_y_heading). Term = w_head * (cos(psi_err) - 1)
    in [-2*w_head, 0]: strictly a penalty for off-axis steering effort, zero at
    perfect alignment. Zero-velocity decisions align by convention (cos(0)=1:
    a stopped body claims no off-axis steering error).
    """
    speed = math.hypot(com_vel_x_heading, com_vel_y_heading)
    if speed == 0.0:
        psi_err = 0.0
    else:
        psi_err = math.atan2(com_vel_y_heading, com_vel_x_heading)
    return w_head * (math.cos(psi_err) - 1.0)


def shaping(prev_com_x_along: float, com_x_along: float,
            com_vel_x_heading: float, com_vel_y_heading: float,
            d_wp: float = D_WP, w_head: float = W_HEAD) -> float:
    """The complete per-decision shaping reward: progress + heading. Nothing else."""
    return (r_progress(prev_com_x_along, com_x_along, d_wp)
            + r_heading(com_vel_x_heading, com_vel_y_heading, w_head))
