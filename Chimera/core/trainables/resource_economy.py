"""resource_economy — the EXTRACTION economy as a trainable domain (the mining faucet).

Sibling to economy_engine (the market/trade economy). This one is where wealth ENTERS the
game: what you dig up and what it is worth. The numbers I hand-set all session in
planet_layers.DEPOSITS -- abundance, mineral_frac, price -- are DATA, and this is their domain.

THE SIMULATED PLAYER (how "a good economy" becomes physics, not taste): a GREEDY MINER who
reads a wiki. At every moment they mine the best value-per-hour resource their current tools
can reach, and upgrade tools the instant they can afford it. The economy either survives that
miner or it does not:
  - if one resource dominates value-per-hour, the miner only ever digs THAT -- the others are
    ghost content and the "economy" is a single resource (top_resource_share, resources_mined).
  - if the deepest tool earns no more than a shovel, there is no reason to progress -- the tool
    ladder is dead content (progression_gain).
  - if deep mining is 100x a shovel, the early game is pointless -- skip to the end (also
    progression_gain, capped above).
  - if the faucet is a money printer or a starvation trap, the game has no pace
    (credits_per_hour band, hours_to_next_tool).

FIXED here is the GEOLOGY + ENGINEERING (the PROGRAM tier -- depths, which tool reaches what,
scoop masses): those are laws, not knobs. TRAINED is the ECONOMY (abundance/frac/price), each
BOUNDED near physical reality so the search refines within reality instead of inverting it
(diamond stays worth more per kg than iron). Scored as the WORST of N regions (rule 7: a rich
region is luck; the economy must hold in the poor ones too).
"""
from __future__ import annotations

import copy
import math
import random

T_HOURS = 60.0                 # a play session
N_REGIONS = 5                  # score the WORST region (rule 7), not the luckiest
GRADE = 0.5                    # representative ore grade (geology; fixed)

# --- FIXED: geology + engineering (PROGRAM tier, not trained) -----------------
# (name, depth_m, tool_tier)  tier 0 shovel · 1 excavator · 2 deep mine
RESOURCES = [
    ('gold_placer', 1.0, 0),
    ('iron_ore',   30.0, 1),
    ('coal',       30.0, 1),
    ('copper_vein', 1500.0, 2),
    ('diamond',     900.0, 2),
]
# (scoop_mass_kg per dig, dig_hours per dig, base cost to BUY this tool)
# Costs calibrated (rule 1: probed) so a miner can progress through ALL THREE tiers within a
# 60 h session -- otherwise the deep mine is unreachable and tier-2 resources are dead content.
TOOLS = [
    dict(scoop_kg=1.0e3,  dig_h=0.05, cost=0.0),        # shovel: owned at start
    dict(scoop_kg=2.0e4,  dig_h=0.5,  cost=1.2e3),      # excavator
    dict(scoop_kg=3.0e6,  dig_h=6.0,  cost=2.5e4),      # deep mine
]
PROFIT_BAND = 0.55            # a rational miner mines everything within this frac of the best rate

# --- TRAINED: the economy numbers, bounded near physical reality --------------
# per resource: (abundance lo/hi, mineral_frac lo/hi, price lo/hi [cr/kg mineral])
BOUNDS = {
    'gold_placer': dict(ab=(0.02, 0.12), mf=(1e-6, 8e-6), pr=(40e3, 80e3)),
    'iron_ore':    dict(ab=(0.15, 0.40), mf=(0.30, 0.60), pr=(0.05, 0.30)),
    'coal':        dict(ab=(0.10, 0.30), mf=(0.70, 0.95), pr=(0.03, 0.12)),
    'copper_vein': dict(ab=(0.04, 0.16), mf=(0.005, 0.03), pr=(4.0, 12.0)),
    'diamond':     dict(ab=(0.005, 0.03), mf=(3e-7, 9e-7), pr=(2e5, 6e5)),
}
TOOL_COST_SCALE = (0.5, 2.0)   # a single global lever on how expensive upgrades are


def seed(rng=None):
    rng = rng or random.Random()
    g = {'tool_cost_scale': rng.uniform(*TOOL_COST_SCALE), 'res': {}}
    for name, _, _ in RESOURCES:
        b = BOUNDS[name]
        g['res'][name] = {
            'abundance': rng.uniform(*b['ab']),
            'mineral_frac': math.exp(rng.uniform(math.log(b['mf'][0]), math.log(b['mf'][1]))),
            'price': math.exp(rng.uniform(math.log(b['pr'][0]), math.log(b['pr'][1]))),
        }
    return g


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def mutate(g, rng=None):
    rng = rng or random.Random()
    g = copy.deepcopy(g)
    if rng.random() < 0.5:
        g['tool_cost_scale'] = _clamp(g['tool_cost_scale'] * math.exp(rng.uniform(-0.2, 0.2)),
                                      *TOOL_COST_SCALE)
    for name, _, _ in RESOURCES:
        b = BOUNDS[name]
        r = g['res'][name]
        if rng.random() < 0.5:
            r['abundance'] = _clamp(r['abundance'] * math.exp(rng.uniform(-0.2, 0.2)), *b['ab'])
        if rng.random() < 0.5:
            r['mineral_frac'] = _clamp(r['mineral_frac'] * math.exp(rng.uniform(-0.25, 0.25)), *b['mf'])
        if rng.random() < 0.5:
            r['price'] = _clamp(r['price'] * math.exp(rng.uniform(-0.25, 0.25)), *b['pr'])
    return g


def _rate_per_hour(name, depth, tier, r, tool):
    """Value-per-hour a greedy miner earns from ONE resource with a given tool: the payload
    value divided by the time to find (prospect ~ 1/abundance digs) and extract it."""
    payload_kg = GRADE * tool['scoop_kg'] * r['mineral_frac']
    value = payload_kg * r['price']
    prospect_digs = 1.0 / max(r['abundance'], 1e-4)
    hours = (prospect_digs + 1.0) * tool['dig_h']
    return value / max(hours, 1e-6)


def _simulate(g, richness) -> dict:
    """Run the greedy miner for T_HOURS in a region with per-resource `richness` multipliers.
    The miner mines every resource within 70% of the best REACHABLE rate (a rational player
    diversifies across what pays), upgrading tools the moment credits allow."""
    res = {}
    for name, depth, tier in RESOURCES:
        r = dict(g['res'][name])
        r['abundance'] = _clamp(r['abundance'] * richness[name], 1e-4, 0.95)
        res[name] = (depth, tier, r)

    owned_tier = 0
    credits = 0.0
    time_h = 0.0
    earned = {name: 0.0 for name, _, _ in RESOURCES}
    earned_by_tier = {0: 0.0, 1: 0.0, 2: 0.0}
    hours_to_next_tool = 999.0
    rate_at_tier = {}
    dt = 0.5

    while time_h < T_HOURS:
        # best reachable rate at the current tool, and everything within PROFIT_BAND of it
        rates = {}
        for name, (depth, tier, r) in res.items():
            if tier <= owned_tier:
                rates[name] = _rate_per_hour(name, depth, tier, r, TOOLS[owned_tier])
        if not rates:
            break
        best = max(rates.values())
        rate_at_tier[owned_tier] = max(rate_at_tier.get(owned_tier, 0.0), best)
        active = {n: rt for n, rt in rates.items() if rt >= PROFIT_BAND * best and rt > 0}
        tot = sum(active.values())
        for n, rt in active.items():
            share = rt / tot
            gained = rt * dt * share            # time split by rate; credited by that resource
            credits += gained
            earned[n] += gained
            earned_by_tier[res[n][1]] += gained
        time_h += dt
        # upgrade the instant it is affordable
        if owned_tier + 1 < len(TOOLS):
            cost = TOOLS[owned_tier + 1]['cost'] * g['tool_cost_scale']
            if credits >= cost:
                credits -= cost
                owned_tier += 1
                if hours_to_next_tool > 900:
                    hours_to_next_tool = time_h

    total = sum(earned.values()) or 1.0
    shares = {n: v / total for n, v in earned.items()}
    mined = [n for n, v in earned.items() if v > total * 0.02]     # >2% of income = actually used
    prog = (rate_at_tier.get(max(rate_at_tier), 0.0) / rate_at_tier.get(0, 1e-9)
            if rate_at_tier.get(0, 0) > 0 else 1.0)
    top = max(shares.values())
    return {
        'credits_per_hour': total / T_HOURS,
        'resources_mined': len(mined),
        'top_resource_share': top,
        'evenness': 1.0 - top,                                     # 0..0.8; more even = more diverse
        'idle_resources': sum(1 for v in shares.values() if v < 0.02),
        'tiers_used': sum(1 for v in earned_by_tier.values() if v > total * 0.05),
        'progression_gain': prog,
        'hours_to_next_tool': hours_to_next_tool,
    }


def measure(g) -> dict:
    """Worst region wins (rule 7). The maximize targets (evenness, resources_mined, tiers_used)
    are naturally positive and O(1) -- no ref-scaling trap; the search gets real gradient."""
    rng = random.Random(4242)
    runs = []
    for _ in range(N_REGIONS):
        richness = {name: rng.uniform(0.55, 1.5) for name, _, _ in RESOURCES}
        runs.append(_simulate(g, richness))
    worst = {
        'credits_per_hour': min(r['credits_per_hour'] for r in runs),
        'resources_mined': min(r['resources_mined'] for r in runs),
        'top_resource_share': max(r['top_resource_share'] for r in runs),
        'evenness': min(r['evenness'] for r in runs),
        'idle_resources': max(r['idle_resources'] for r in runs),
        'tiers_used': min(r['tiers_used'] for r in runs),
        'progression_gain': min(r['progression_gain'] for r in runs),
        'hours_to_next_tool': max(r['hours_to_next_tool'] for r in runs),
    }
    # physical price ordering preserved (reality guard): diamond > copper > iron per kg
    pr = g['res']
    worst['price_order'] = 1.0 if (pr['diamond']['price'] > pr['copper_vein']['price']
                                   > pr['iron_ore']['price']) else 0.0
    return worst
