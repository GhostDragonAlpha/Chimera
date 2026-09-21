"""L5 fixtures + the replayable executable twin (constraint-ledger lane
agent/cl-L5-transitive-20260921).

The fixtures are DECLARED SYNTHETIC (schema-valid chimpl records; provenance
says so): they exercise the CALCULATOR, not the machinery. The twin is the
ground-truth semantics of the DECLARED physics universe — the replayable
counterfactual that discharges F-MISSED-COUPLING against the predicted
cones (the real-trace leg lives in l5_real_trace.py).

Fixture SHARED_CARRIER (the spec's fixture 1): two DISTINCT force outputs
(leg.force.a from force_law_a, leg.force.b from force_law_b) and a later
load-share law (load_share_law) whose ONLY read is sensor.load_share. The
first-order calculator sees zero overlap on (A,C) and (B,C). The declared
physics carries both forces into ONE accumulated net force (the shared
carrier) -> body state -> contact guard -> sensor, so the transitive
propagation must flag them THROUGH the physics edges. audit_logger writes a
terminal sink from control.step only — it keeps the fixture from collapsing
(usefulness witness inside the closed loop).

Fixture READ_READONLY (the spec's fixture 2): alarm_watch and audit_watch
share ONE delayed read (contact.clamp); their writes are terminal sinks no
record reads and no physics stage consumes. Both the first-order calculator
and the propagation must return INDEPENDENT with no write-write class —
shared reads are harmless; the physics must NOT fabricate a conflict.

Fixture DEGENERATE: the SHARED_CARRIER records with an EMPTY physics
declaration — the v1 world. Useful (narrow cones) but UNSOUND: the twin
counterfactual escapes its cones (measured, expected-red), which is exactly
the gap F-MISSED-COUPLING exists to catch and the reason the physics
summaries must be declared.
"""
from __future__ import annotations

import copy
import math

from . import expr as X
from .interference2 import PhysicsModel, PropGraph, build_graph
from .schema import load

LANE = 'agent/cl-L5-transitive-20260921'
SYN_PROV = {'receipt': 'synthetic (L5 fixture, declared synthetic)', 'commit': 'n/a'}

# ── the shared declared-physics quantity declarations ──────────────────────
PHYS_DECLS = {
    'body.y': {'entity': 'body', 'frame': 'world, plane-up axis', 'unit': 'm',
               'dtype': 'f64', 'phase': 'tick-start', 'role': 'external-input'},
    'body.vy': {'entity': 'body', 'frame': 'world, plane-up axis', 'unit': 'm/s',
                'dtype': 'f64', 'phase': 'tick-start', 'role': 'external-input'},
    'contact.clamp': {'entity': 'contact_guard', 'frame': 'controller state',
                      'unit': 'bool', 'dtype': 'bool', 'phase': 'tick-start',
                      'role': 'external-input'},
    'sensor.load_share': {'entity': 'load_share_sensor', 'frame': 'ratio',
                          'unit': '1', 'dtype': 'f64', 'phase': 'tick-start',
                          'role': 'external-input'},
}


def _force_rec(name, write, expr, reads, consts,
               entity='actuator', frame='actuation', unit='N', dtype='f64'):
    quantities = {write: {'entity': entity, 'frame': frame,
                          'unit': unit, 'dtype': dtype, 'phase': 'tick-start',
                          'role': 'state'}}
    for q in reads:
        quantities[q] = dict(PHYS_DECLS[q])
    return {
        'name': name, 'kind': 'definition', 'lane': LANE,
        'provenance': dict(SYN_PROV),
        'falsifier': 'L5 (synthetic fixture; F-MISSED-COUPLING / F-VACUOUS-CONE)',
        'params': {}, 'quantities': quantities,
        'assign': [{'write': write, 'expr': expr}],
        'constants': {k: {'value': v, 'provenance': 'synthetic L5 fixture'}
                      for k, v in consts.items()},
        'initial': {write: 0.0},
    }


FORCE_LAW_A = _force_rec('force_law_a', 'leg.force.a', 'body.y * kSpringA',
                         ['body.y'], {'kSpringA': 12.0})
FORCE_LAW_B = _force_rec('force_law_b', 'leg.force.b',
                         'if contact.clamp then kPushB else 0',
                         ['contact.clamp'], {'kPushB': 2.0})
LOAD_SHARE_LAW = _force_rec('load_share_law', 'leg.force.c',
                            'kShareTarget - sensor.load_share',
                            ['sensor.load_share'], {'kShareTarget': 0.5})

AUDIT_LOGGER = {
    'name': 'audit_logger', 'kind': 'definition', 'lane': LANE,
    'provenance': dict(SYN_PROV),
    'falsifier': 'L5 (synthetic fixture; terminal sink, usefulness witness)',
    'params': {},
    'quantities': {'audit.flag': {'entity': 'audit', 'frame': 'controller state',
                                  'unit': 'bool', 'dtype': 'bool',
                                  'phase': 'tick-start', 'role': 'state'}},
    'assign': [{'write': 'audit.flag', 'expr': 'control.step > 0'}],
    'constants': {}, 'initial': {'audit.flag': False},
}

ALARM_WATCH = _force_rec('alarm_watch', 'alarm.a',
                         'if contact.clamp then kAlarmOne else kAlarmOne - 1',
                         ['contact.clamp'], {'kAlarmOne': 1.0},
                         entity='alarm', frame='controller state', unit='bool')
AUDIT_WATCH = _force_rec('audit_watch', 'audit.count',
                         'if contact.clamp then kAuditOne else kAuditOne - 1',
                         ['contact.clamp'], {'kAuditOne': 1.0},
                         entity='audit', frame='controller state', unit='count')


def shared_carrier_specs() -> list[dict]:
    return [FORCE_LAW_A, FORCE_LAW_B, LOAD_SHARE_LAW, AUDIT_LOGGER]


def read_readonly_specs() -> list[dict]:
    return [ALARM_WATCH, AUDIT_WATCH]


def load_fixture(specs) -> list:
    return [load(s) for s in specs]


# ── the declared physics model (the summaries under test) ──────────────────
def shared_physics() -> PhysicsModel:
    """Two distinct force outputs -> ONE accumulated net force (the shared
    carrier) -> body state -> contact guard -> sensor. The loop the later
    law closes by writing a force back."""
    return PhysicsModel(
        force_outputs=('leg.force.a', 'leg.force.b', 'leg.force.c'),
        body_states=('body.y', 'body.vy'),
        contact_guards=('contact.clamp',),
        sensors=('sensor.load_share',),
    )


def empty_physics() -> PhysicsModel:
    return PhysicsModel()


# ── the replayable executable twin ─────────────────────────────────────────
TWIN_INITIAL = {
    'body.y': 0.1, 'body.vy': 0.0, 'contact.clamp': False,
    'sensor.load_share': 0.1,        # y * kSensorGain
    'leg.force.a': 0.0, 'leg.force.b': 0.0, 'leg.force.c': 0.0,
    'alarm.a': 0.0, 'audit.count': 0, 'audit.flag': False,
}
TWIN_CFG = {'dt': 0.1, 'kSensorGain': 1.0, 'kSensorClamp': 0.0}
TWIN_TICKS = 12


def twin_tick(state: dict, records: list, cfg: dict, step: int) -> dict:
    """One tick of the declared universe. Laws evaluate with DELAYED reads
    (tick-start values, one row back — the pilot's tick convention), then
    the declared physics stages run on THIS tick's force writes:
    accumulate -> integrate -> guard -> sense. This tick body IS the
    declared physics summaries, executable."""
    same: dict = {}
    for rec in records:
        for a in rec.assignments:
            if a.ast is None:
                a.ast = X.parse(a.src)
            consts = {k: v['value'] for k, v in rec.constants.items()}
            consts['control.step'] = step
            same[a.write] = X.evaluate(a.ast, state, same, consts)
    # force-accumulation: the SHARED CARRIER is one sum of all declared
    # force outputs — this is the physical edge the first-order graph lacks
    net = sum(same[q] for q in
              ('leg.force.a', 'leg.force.b', 'leg.force.c') if q in same)
    nxt = dict(state)
    for q in same:
        nxt[q] = same[q]
    if net or 'body.y' in state:
        # body-state integration (semi-implicit Euler, the declared summary)
        vy = state['body.vy'] + net * cfg['dt']
        y = state['body.y'] + vy * cfg['dt']
        # contact guard (restitutionless floor at y=0, the declared summary)
        if y < 0.0:
            clamp, y, vy = True, 0.0, max(vy, 0.0)
        else:
            clamp = False
        # sensor (the declared summary: reads the guarded state)
        load_share = cfg['kSensorClamp'] if clamp else y * cfg['kSensorGain']
        nxt.update({'body.vy': vy, 'body.y': y, 'contact.clamp': clamp,
                    'sensor.load_share': load_share})
    return nxt


def replay(records: list, cfg: dict = None, ticks: int = TWIN_TICKS,
           overrides: dict | None = None) -> list[dict]:
    """TICKS+1 snapshots (index 0 = the initial state)."""
    cfg = dict(TWIN_CFG if cfg is None else cfg)
    recs = copy.deepcopy(records)
    if overrides:
        for r in recs:
            if r.name in overrides:
                for k, v in overrides[r.name].items():
                    r.constants[k] = {'value': v, 'provenance': 'perturbed'}
    state = dict(TWIN_INITIAL)
    snaps = [dict(state)]
    for t in range(1, ticks + 1):
        state = twin_tick(state, recs, cfg, t)
        snaps.append(dict(state))
    return snaps


def perturb_one_ulp(records: list, law_name: str, const_key: str):
    """The small perturbation: one ulp upward on ONE law's constant."""
    out = {}
    for r in records:
        if r.name == law_name:
            v = r.constants[const_key]['value']
            out[r.name] = {const_key: math.nextafter(v, math.inf)}
    return out


def counterfactual(records: list, law_name: str, const_key: str,
                   cfg: dict = None, ticks: int = TWIN_TICKS) -> dict:
    """The replayable counterfactual: base vs one-ulp-perturbed replay.
    Returns the CHANGED-observable set (quantity names differing at ANY
    tick) — the Obs() the cone must cover (F-MISSED-COUPLING)."""
    base = replay(records, cfg, ticks)
    pert = replay(records, cfg, ticks,
                  overrides=perturb_one_ulp(records, law_name, const_key))
    changed = set()
    witness = {}
    for q in base[0]:
        for t in range(len(base)):
            if base[t][q] != pert[t][q]:
                changed.add(q)
                witness[q] = {'first_tick': t,
                              'base': base[t][q], 'pert': pert[t][q]}
                break
    return {'law': law_name, 'constant': const_key,
            'changed': changed, 'witness': witness,
            'unchanged_perturbation': not changed}
