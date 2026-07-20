"""erisaid_mirror — the universal interface as a trainable state machine.

CHIMERA_VISION.py §10: the Erisaid is the moral center. Design Law 3: wordless.
Design Law 2: the bad ending is a costless life, taught through consequence.

The mirror IS the menu. Every player interaction with it is a state transition
driven by physical proximity and light. There are no text labels — only reflections,
brightness, bearing, and the player's own position relative to the shell.

ELEMENTS (the irreducible building blocks):
  - REFLECTION_TYPES: star (past life), pain (open phantom), sacrifice (last act),
    self (current state), call (unresolved NPC need)
  - PROXIMITY_ZONES: distant (>30m), approaching (10-30m), near (3-10m), touching (<3m)
  - LIGHT_LEVELS: dim (costless), quiet (some sacrifice), bright (generous), blinding (legend)
  - BEARING: golden-angle distribution around the shell (no two reflections crowd)

PRINCIPLES (the rules that combine elements):
  - Proximity governs state: farther = see more, closer = see detail
  - Brightness = total sacrifice weight of reflected object
  - Bearing = golden angle * object index (phyllotaxis for even distribution)
  - Twinkle = unresolved phantom pain count
  - Nothing observed is lost: every approached reflection stays unlocked
  - The self-reflection is always at bearing 0 (directly ahead)

THE STATE MACHINE:
  IDLE → APPROACHING → BROWSING → FOCUSED → SELECTED → TRANSITIONING → IDLE

MEASURABLE PHYSICS (what GOOD means in measurement, not opinion):
  - comprehension_time: steps from IDLE to SELECTED (lower = clearer interface)
  - information_per_step: distinct reflections visible per zone (higher = richer)
  - state_discrimination: can an observer tell which state the player is in? (0-1)
  - navigation_efficiency: total distance traveled to reach target reflection
  - costless_visibility: can a costless player see their own dim reflection? (binary)
  - generous_readability: does a generous player's bright star dominate? (0-1)
  - pain_bearing_fidelity: are phantom pains spatially distinguishable? (0-1)
  - proximity_consistency: does each zone show the expected count of reflections?

THIS MODULE REPORTS FACTS, NOT OPINIONS. It never says a menu SHOULD be fast —
it measures comprehension_time and information_per_step. What GOOD means lives
in docs/objectives/erisaid_mirror.json, written from Design Laws 2+3 as physics.
"""

from __future__ import annotations

import copy
import math
import random

# --- simulation constants (NOT genome: these are the test conditions) ---
EVAL_SEED = 42                   # deterministic genome -> measurement
N_PLAYERS = 200                  # simulated player sessions per genome
MAX_STEPS = 80                   # maximum player steps before giving up
MIN_REFLECTIONS = 3              # minimum reflections visible from any zone
MAX_REFLECTIONS = 24             # maximum total reflections
GOLDEN_ANGLE_RAD = math.radians(137.50776405003785)


def seed(rng: random.Random | None = None) -> dict:
    """Random genome for the Erisaid mirror state machine.

    The genome IS the mirror configuration: how many reflections of each type,
    what brightness curve parameters, what proximity thresholds, what bearing
    distribution. Every value is a trainable parameter.
    """
    rng = rng or random.Random()
    return {
        # Proximity zone thresholds (meters from shell center)
        "zone_distant": rng.uniform(30.0, 60.0),       # > this = distant
        "zone_approaching": rng.uniform(15.0, 30.0),     # > this = approaching
        "zone_near": rng.uniform(5.0, 15.0),             # > this = near
        # < this = touching

        # Reflection counts per type
        "n_stars": rng.randint(3, 12),                  # past lives visible
        "n_pains": rng.randint(0, 8),                   # unresolved questions
        "n_sacrifices": rng.randint(1, 6),              # last acts
        "n_calls": rng.randint(0, 6),                   # NPC needs

        # Brightness curve: brightness = 1 - exp(-weight / k)
        "brightness_k": rng.uniform(1.0, 20.0),         # steepness of brightness curve

        # Bearing distribution
        "bearing_spread": rng.uniform(0.5, 2.0),        # how tightly packed (1.0 = golden angle)

        # Transition costs (steps per state change)
        "step_cost_idle_approach": rng.uniform(1.0, 8.0),
        "step_cost_approach_browse": rng.uniform(1.0, 6.0),
        "step_cost_browse_focus": rng.uniform(1.0, 5.0),
        "step_cost_focus_select": rng.uniform(1.0, 4.0),

        # Visibility thresholds
        "baseline_brightness": rng.uniform(0.01, 0.15),
        "min_brightness_visible": rng.uniform(0.0, 0.3),  # below this = invisible
        "twinkle_threshold": rng.uniform(0, 5),            # pain count above which star twinkles

        # Self-reflection properties
        "self_reflection_brightness_scale": rng.uniform(0.5, 2.0),

        # Dwell probabilities: chance of lingering in BROWSING/FOCUSED (skip movement)
        "dwell_browsing": rng.uniform(0.0, 0.6),
        "dwell_focused": rng.uniform(0.0, 0.6),

        # Selection probabilities (replaces hardcoded 0.1/0.4/0.7)
        "selection_prob_approach": rng.uniform(0.02, 0.3),
        "selection_prob_browse": rng.uniform(0.1, 0.5),
        "selection_prob_focus": rng.uniform(0.3, 0.8),
    }


def mutate(genome: dict, rng: random.Random | None = None) -> dict:
    """Mutate a genome. Small perturbations to continuous params, occasional
    step-changes to integer params. Returns a deep copy."""
    rng = rng or random.Random()
    g = copy.deepcopy(genome)

    # Continuous params: perturb by ±20% (log-normal multiplicative)
    continuous_keys = [
        "zone_distant", "zone_approaching", "zone_near",
        "brightness_k", "bearing_spread", "baseline_brightness",
        "step_cost_idle_approach", "step_cost_approach_browse",
        "step_cost_browse_focus", "step_cost_focus_select",
        "min_brightness_visible", "self_reflection_brightness_scale",
        "dwell_browsing", "dwell_focused",
        "selection_prob_approach", "selection_prob_browse", "selection_prob_focus",
    ]
    for k in continuous_keys:
        if rng.random() < 0.5:
            factor = math.exp(rng.uniform(-0.2, 0.2))
            g[k] = max(0.001, g[k] * factor)

    # Integer params: occasional ±1
    int_keys = ["n_stars", "n_pains", "n_sacrifices", "n_calls", "twinkle_threshold"]
    for k in int_keys:
        if rng.random() < 0.3:
            delta = rng.choice([-1, 1])
            g[k] = max(1 if k == "n_stars" else 0, g[k] + delta)

    # Clamp integer counts
    g["n_stars"] = min(MAX_REFLECTIONS, max(MIN_REFLECTIONS, g["n_stars"]))
    g["n_pains"] = min(MAX_REFLECTIONS // 2, max(0, g["n_pains"]))
    g["n_sacrifices"] = min(MAX_REFLECTIONS // 2, max(1, g["n_sacrifices"]))
    g["n_calls"] = min(MAX_REFLECTIONS // 2, max(0, g["n_calls"]))

    # Clamp zone values so multiplicative mutation doesn't explode them
    g["zone_distant"] = max(5.0, min(100.0, g["zone_distant"]))
    g["zone_approaching"] = max(3.0, min(95.0, g["zone_approaching"]))
    g["zone_near"] = max(1.0, min(90.0, g["zone_near"]))

    # Zone ordering invariant: distant > approaching > near > touching (0)
    # Sort descending then enforce minimum gaps so zones never collapse
    zones = sorted([g["zone_distant"], g["zone_approaching"], g["zone_near"]], reverse=True)
    g["zone_distant"] = zones[0]
    g["zone_approaching"] = max(zones[0] - 2.0, zones[1])
    g["zone_near"] = max(g["zone_approaching"] - 2.0, min(zones[2], g["zone_approaching"] - 1.0))
    if g["zone_near"] < 1.0:
        g["zone_near"] = 1.0

    # Clamp dwell params to [0, 1] so they stay valid probabilities
    g["dwell_browsing"] = max(0.0, min(1.0, g["dwell_browsing"]))
    g["dwell_focused"] = max(0.0, min(1.0, g["dwell_focused"]))

    # Clamp selection probs to [0, 1]
    g["selection_prob_approach"] = max(0.01, min(1.0, g["selection_prob_approach"]))
    g["selection_prob_browse"] = max(0.01, min(1.0, g["selection_prob_browse"]))
    g["selection_prob_focus"] = max(0.01, min(1.0, g["selection_prob_focus"]))

    return g


# ---------------------------------------------------------------------------
# Simulated player: walks toward the mirror, browses reflections, selects one.
# Not one scripted path — a stochastic SPREAD of archetypes, like memorial.py.
# ---------------------------------------------------------------------------

class _Player:
    """One simulated player approaching the Erisaid mirror."""
    def __init__(self, rng: random.Random, archetype: str, total_sacrifice_weight: float,
                 pain_count: int, has_held_item: bool):
        self.rng = rng
        self.archetype = archetype          # costless, quiet, generous
        self.total_sacrifice_weight = total_sacrifice_weight
        self.pain_count = pain_count
        self.has_held_item = has_held_item
        self.position = rng.uniform(35.0, 60.0)  # start in distant zone
        self.state = "IDLE"
        self.steps_taken = 0
        self.reflections_seen: set[int] = set()
        self.selected_index: int | None = None
        self.distance_traveled = 0.0


def _brightness(weight: float, k: float, baseline: float = 0.05) -> float:
    """baseline + (1-baseline)*(1 - exp(-w/k)). A costless life (w=0) -> baseline brightness."""
    curve = 1.0 - math.exp(-max(0.0, weight) / max(0.001, k))
    return baseline + (1.0 - baseline) * curve


def _zone(position: float, g: dict) -> str:
    """Which proximity zone is the player in?"""
    if position > g["zone_distant"]:
        return "distant"
    elif position > g["zone_approaching"]:
        return "approaching"
    elif position > g["zone_near"]:
        return "near"
    else:
        return "touching"


def _visible_count(g: dict, zone: str) -> int:
    """How many reflections are visible from this zone? Closer = more detail."""
    total = g["n_stars"] + g["n_pains"] + g["n_sacrifices"] + g["n_calls"]
    if zone == "distant":
        return max(1, total // 4)
    elif zone == "approaching":
        return max(2, total // 2)
    elif zone == "near":
        return max(3, total * 3 // 4)
    else:  # touching
        return total


def _step_player(player: _Player, g: dict) -> None:
    """One step of the state machine.

    State transitions are stochastic, driven by genome params:
    - step_cost_* controls how long before transition is allowed
    - dwell_* controls lingering (skip movement) in BROWSING/FOCUSED
    - selection_prob_* controls likelihood of selecting a reflection
    """
    if player.state == "SELECTED":
        return  # selection is terminal for this encounter

    z = _zone(player.position, g)

    # Determine proposed state from zone (proximity physics)
    if z == "distant":
        proposed = "IDLE"
    elif z == "approaching":
        proposed = "APPROACHING"
    elif z == "near":
        proposed = "BROWSING"
    else:  # touching
        proposed = "FOCUSED"

    # Step-cost-driven transition resistance: higher cost = harder to leave current state
    if player.state == "IDLE" and proposed != "IDLE":
        cost = g.get("step_cost_idle_approach", 4.0)
        if player.rng.random() > 1.0 / max(1.0, cost):
            proposed = player.state  # resist transition
    elif player.state == "APPROACHING" and proposed not in ("IDLE", "APPROACHING"):
        cost = g.get("step_cost_approach_browse", 3.0)
        if player.rng.random() > 1.0 / max(1.0, cost):
            proposed = player.state
    elif player.state == "BROWSING" and proposed == "FOCUSED":
        cost = g.get("step_cost_browse_focus", 2.0)
        if player.rng.random() > 1.0 / max(1.0, cost):
            proposed = player.state

    # Dwell inertia: once IN a dwell state, resist leaving it
    dw_browse = g.get("dwell_browsing", 0.3)
    dw_focus = g.get("dwell_focused", 0.5)

    if player.state == "BROWSING" and proposed != "BROWSING" and player.rng.random() < dw_browse:
        proposed = player.state  # linger — resist transition out of BROWSING
    elif player.state == "FOCUSED" and proposed != "FOCUSED" and player.rng.random() < dw_focus:
        proposed = player.state  # linger — resist transition out of FOCUSED

    player.state = proposed

    # Move toward mirror: dwell params reduce step size per zone
    # High dwell_browsing = slower movement in near zone = longer BROWSING dwell
    # High dwell_focused = slower movement in touching zone = longer FOCUSED dwell
    step_mult = 1.0
    if z == "near":
        step_mult = max(0.15, 1.0 - g.get("dwell_browsing", 0.3))
    elif z == "touching":
        step_mult = max(0.15, 1.0 - g.get("dwell_focused", 0.5))
    step = abs(player.rng.gauss(3.0 * step_mult, 1.5))
    old_pos = player.position
    player.position = max(0.5, player.position - step)
    player.distance_traveled += abs(player.position - old_pos)
    player.steps_taken += 1

    # See reflections in current zone
    visible = _visible_count(g, z)
    for i in range(visible):
        player.reflections_seen.add(i)

    # Selection: genome-driven probabilities per state
    if player.state in ("APPROACHING", "BROWSING", "FOCUSED") and player.selected_index is None:
        if player.state == "APPROACHING":
            prob = g.get("selection_prob_approach", 0.1)
        elif player.state == "BROWSING":
            prob = g.get("selection_prob_browse", 0.4)
        else:
            prob = g.get("selection_prob_focus", 0.7)
        if player.rng.random() < prob:
            visible = _visible_count(g, z)
            if visible > 0:
                player.selected_index = player.rng.randint(0, visible - 1)
                player.state = "SELECTED"


def measure(genome: dict) -> dict:
    """Simulate N_PLAYERS approaching the mirror. Report FACTS, not opinions.

    Returns a dict of measurements. Every value is a number derived from physics
    of the simulation — no adjectives, no scores, no "good"/"bad."
    """
    rng = random.Random(EVAL_SEED)
    g = genome

    # Generate reflection objects
    n_total = g["n_stars"] + g["n_pains"] + g["n_sacrifices"] + g["n_calls"]
    reflection_brightnesses = []
    for i in range(n_total):
        # Distribute brightness based on type
        if i < g["n_stars"]:
            w = rng.uniform(0.5, 10.0)  # stars have meaningful weight
        elif i < g["n_stars"] + g["n_pains"]:
            w = 0.0  # pains have no weight but twinkle
        elif i < g["n_stars"] + g["n_pains"] + g["n_sacrifices"]:
            w = rng.uniform(0.1, 5.0)  # recent sacrifices
        else:
            w = rng.uniform(0.0, 2.0)  # NPC calls
        b = _brightness(w, g["brightness_k"], g.get("baseline_brightness", 0.05))
        reflection_brightnesses.append(b)

    # Run player sessions
    archetypes = ["costless"] * (N_PLAYERS // 3) + ["quiet"] * (N_PLAYERS // 3) + ["generous"] * (N_PLAYERS // 3)
    rng.shuffle(archetypes)

    results = {
        "comprehension_times": [],
        "completed_selections": 0,
        "info_per_step": [],
        "navigation_efficiencies": [],
        "costless_visible": [],
        "generous_dominance": [],
        "zone_consistency": {"distant": [], "approaching": [], "near": [], "touching": []},
        "state_dwell_times": {"IDLE": [], "APPROACHING": [], "BROWSING": [], "FOCUSED": [], "SELECTED": []},
    }

    for arch in archetypes:
        if arch == "costless":
            weight = 0.0
            pains = rng.randint(3, 8)  # costless lives have more unresolved
            has_item = rng.random() < 0.2
        elif arch == "quiet":
            weight = rng.uniform(1.0, 5.0)
            pains = rng.randint(1, 4)
            has_item = rng.random() < 0.5
        else:  # generous
            weight = rng.uniform(5.0, 15.0)
            pains = rng.randint(0, 2)
            has_item = rng.random() < 0.8

        player = _Player(rng, arch, weight, pains, has_item)
        state_history = []

        for _ in range(MAX_STEPS):
            _step_player(player, g)
            state_history.append(player.state)
            if player.state == "TRANSITIONING":
                break

        # Measurements
        steps_to_select = player.steps_taken if player.selected_index is not None else MAX_STEPS
        if player.selected_index is not None:
            results["comprehension_times"].append(steps_to_select)
            results["completed_selections"] = results.get("completed_selections", 0) + 1

        info = len(player.reflections_seen) / max(1, player.steps_taken)
        results["info_per_step"].append(info)

        eff = steps_to_select / max(0.001, player.distance_traveled)
        results["navigation_efficiencies"].append(eff)

        # Can a costless player see their dim reflection?
        # Phantom pains dim the self-reflection (twinkle distracts) — makes this trainable
        if arch == "costless":
            pain_penalty = max(0.2, 1.0 - player.pain_count * 0.08)
            self_brightness = _brightness(0.0, g["brightness_k"], g.get("baseline_brightness", 0.05)) * g["self_reflection_brightness_scale"] * pain_penalty
            results["costless_visible"].append(1.0 if self_brightness >= g["min_brightness_visible"] else 0.0)

        # Does a generous player's star dominate?
        if arch == "generous" and reflection_brightnesses:
            max_b = max(reflection_brightnesses[:g["n_stars"]]) if g["n_stars"] > 0 else 0
            results["generous_dominance"].append(max_b)

        # Zone consistency: count what's visible per zone
        for z in ["distant", "approaching", "near", "touching"]:
            results["zone_consistency"][z].append(_visible_count(g, z))

        # State dwell times (fraction of total steps in each state)
        total = len(state_history) or 1
        for state in ["IDLE", "APPROACHING", "BROWSING", "FOCUSED", "SELECTED"]:
            count = state_history.count(state)
            results["state_dwell_times"][state].append(count / total)

    # Aggregate: report robust (worst-case) and mean
    def _robust(vals: list) -> float:
        return min(vals) if vals else 0.0

    def _mean(vals: list) -> float:
        return sum(vals) / len(vals) if vals else 0.0

    def _zone_report(z: str) -> dict:
        vals = results["zone_consistency"][z]
        return {"mean": _mean(vals), "min": _robust(vals), "max": max(vals) if vals else 0}

    selections = results.get("completed_selections", 1)
    return {
        # Core usability metrics
        "comprehension_time": _mean(results["comprehension_times"]),
        "comprehension_time_worst": _robust(results["comprehension_times"]) if results["comprehension_times"] else MAX_STEPS,
        "selection_rate": selections / N_PLAYERS,
        "information_per_step": _mean(results["info_per_step"]),
        "navigation_efficiency": _mean(results["navigation_efficiencies"]),

        # Accessibility: can a costless life be seen?
        "costless_self_visible_fraction": _mean(results["costless_visible"]),

        # Readability: does a generous star dominate?
        "generous_star_brightness": _mean(results["generous_dominance"]),

        # Zone behavior
        "zone_distant_visible": _zone_report("distant"),
        "zone_approaching_visible": _zone_report("approaching"),
        "zone_near_visible": _zone_report("near"),
        "zone_touching_visible": _zone_report("touching"),

        # State distribution
        "dwell_idle": _mean(results["state_dwell_times"]["IDLE"]),
        "dwell_approaching": _mean(results["state_dwell_times"]["APPROACHING"]),
        "dwell_browsing": _mean(results["state_dwell_times"]["BROWSING"]),
        "dwell_focused": _mean(results["state_dwell_times"]["FOCUSED"]),
        "dwell_selected": _mean(results["state_dwell_times"]["SELECTED"]),

        # Genome snapshot
        "genome_summary": {
            "n_reflections": n_total,
            "brightness_k": g["brightness_k"],
            "zones": f"d>{g['zone_distant']:.0f}>a>{g['zone_approaching']:.0f}>n>{g['zone_near']:.0f}>t",
        },
    }
