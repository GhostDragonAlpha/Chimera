"""The two pilot law-records, from the SHIPPED walk controller.

Law 1  touch_band       — the wave-22 TOUCH LAW (GaitWalker::leg_contact):
                          contact at pair-min gap <= kTouch; released only
                          when the pair-min gap exceeds kTouch+kReleaseBand
                          (the genuine-departure bound 1.1e-5 m); inside the
                          hysteresis band the previous state HOLDS.
Law 2  stand_first_hold — the hind-step hold's arming predicate: at a step
                          fire the hold arms (the touching-class slot read,
                          the floor-anchor capture = the pads' liftoff
                          height), releases at the band exit, completes at
                          the wave-31 band entry.

NOTE (preregistration, "named deviation"): the brief's "wave-33" is BANKED,
not shipped (receipt_wave32.json); this record set compiles the SHIPPED law
the wave-33 bank builds on.

Source: ChimeraEngine/engine/gait_controller.hpp @ 6ea2702c (READ-ONLY).
Constants are the machinery's own — ZERO new numbers (Rule 1).
"""
from __future__ import annotations

from .schema import load as _load

BASE_COMMIT = '6ea2702c23c191ff1d3f14bc895ba668f4586dac'
LANE = 'agent/constraint-ledger-20260921'
SRC = 'ChimeraEngine/engine/gait_controller.hpp'
RECEIPT_DIR = 'tools/science_funnel/validation/gait_zero_20260919'

# quantity phase semantics (the registered tick convention): 'tick-start'
# quantities are read one row back (the tick-start evaluation is the
# end-of-previous-step state); 'decision' quantities are bound on the
# decision row itself (the fire flag, the post-update clock phase).
EXTERN_DECLS = {
    'gait.hind.pairmin_gap.{leg}': {
        'entity': 'gait_walker.hind_pads', 'frame': 'world, plane-up axis',
        'unit': 'm', 'dtype': 'f64', 'phase': 'tick-start',
        'role': 'external-input'},
    'gait.hind.mode.{leg}': {
        'entity': 'gait_walker.hind_step_clock', 'frame': 'controller state',
        'unit': 'enum(0 stance,1 glide)', 'dtype': 'int', 'phase': 'tick-start',
        'role': 'external-input'},
    'gait.hind.t.{leg}': {
        'entity': 'gait_walker.hind_step_clock', 'frame': 'controller state',
        'unit': 'tick', 'dtype': 'int', 'phase': 'tick-start',
        'role': 'external-input'},
    'gait.hind.heel_y.{leg}': {
        'entity': 'gait_walker.hind_heel_pad', 'frame': 'world, plane-up axis',
        'unit': 'm', 'dtype': 'f64', 'phase': 'tick-start',
        'role': 'external-input'},
    'gait.hind.mp_y.{leg}': {
        'entity': 'gait_walker.hind_mp_pad', 'frame': 'world, plane-up axis',
        'unit': 'm', 'dtype': 'f64', 'phase': 'tick-start',
        'role': 'external-input'},
    'gait.fire.{leg}': {
        'entity': 'gait_walker.hind_step_scheduler', 'frame': 'controller state',
        'unit': 'bool', 'dtype': 'bool', 'phase': 'decision',
        'role': 'external-input'},
    'gait.hind.phase.{leg}': {
        'entity': 'gait_walker.hind_clock', 'frame': 'controller state',
        'unit': 'turns (mod 1)', 'dtype': 'f64', 'phase': 'decision',
        'role': 'external-input'},
}

TOUCH_BAND = {
    'name': 'touch_band',
    'kind': 'definition',
    'lane': LANE,
    'provenance': {
        'receipt': f'{RECEIPT_DIR}/receipt_wave22.json',
        'commit': BASE_COMMIT,
        'symbol': 'chimera::multibody::GaitWalker::leg_contact',
        'lines': '564-576',
        'constant_sources': {
            'kTouch': f'{SRC}:36 (kTouch=1e-5)',
            'kReleaseBand': f'{SRC}:52 (kReleaseBand=1e-6, receipt_wave22 '
                            'genuine-departure bound; sum 1.1e-5)'},
    },
    'falsifier': 'P2 (touch class per tick, bit-exact; nextafter boundary fixtures)',
    'params': {'leg': ['left', 'right']},
    'quantities': {
        'gait.hind.pairmin_gap.{leg}': EXTERN_DECLS['gait.hind.pairmin_gap.{leg}'],
        'gait.touch.{leg}': {
            'entity': 'gait_walker.leg_contact_state', 'frame': 'controller state',
            'unit': 'bool', 'dtype': 'bool', 'phase': 'tick-start', 'role': 'state'},
    },
    'constants': {
        'kTouch': {'value': 1e-5,
                   'provenance': f'{SRC}:36 — the machinery touch quantum'},
        'kReleaseBand': {'value': 1e-6,
                         'provenance': f'{SRC}:52 — the solver gap quantum '
                                       '(receipt_wave22.json); no new constant'},
    },
    'initial': {'gait.touch.{leg}': False},
    'assign': [
        {'write': 'gait.touch.{leg}',
         'expr': 'if gait.hind.pairmin_gap.{leg} <= kTouch then true '
                 'else if gait.hind.pairmin_gap.{leg} > kTouch + kReleaseBand then false '
                 'else gait.touch.{leg}'},
    ],
}

STAND_FIRST_HOLD = {
    'name': 'stand_first_hold',
    'kind': 'definition',
    'lane': LANE,
    'provenance': {
        'receipt': f'{RECEIPT_DIR}/receipt_wave31.json, {RECEIPT_DIR}/receipt_wave28b.json',
        'commit': BASE_COMMIT,
        'symbol': 'GaitWalker::step() hind-step hold block (arming/release/completion)',
        'lines': '2069-2100 (release + band-entry completion), 2200-2202 '
                 '(arming + floor-anchor capture), 2118 (the touching-class read)',
        'deviation_note': 'the brief quote "wave-33 STAND-FIRST HOLD" is BANKED, not '
                          'shipped (receipt_wave32.json); this compiles the shipped '
                          'hold law the wave-33 bank builds on',
        'constant_sources': {
            'TOE_OFF': f'{SRC}:58 (TOE_OFF=0.68)',
            'tair': 'the machinery air time ceil((T_CYCLE-DUTY_SAMPLED)/dt), '
                    'dumped by the trace harness from the C++ expression'},
    },
    'falsifier': 'P2 (hold arming per tick, band exits = clear_tick, fire_class, '
                 'anchor bits; exact)',
    'params': {'leg': ['left', 'right']},
    'quantities': {
        'gait.hind.pairmin_gap.{leg}': EXTERN_DECLS['gait.hind.pairmin_gap.{leg}'],
        'gait.hind.mode.{leg}': EXTERN_DECLS['gait.hind.mode.{leg}'],
        'gait.hind.t.{leg}': EXTERN_DECLS['gait.hind.t.{leg}'],
        'gait.hind.heel_y.{leg}': EXTERN_DECLS['gait.hind.heel_y.{leg}'],
        'gait.hind.mp_y.{leg}': EXTERN_DECLS['gait.hind.mp_y.{leg}'],
        'gait.fire.{leg}': EXTERN_DECLS['gait.fire.{leg}'],
        'gait.hind.phase.{leg}': EXTERN_DECLS['gait.hind.phase.{leg}'],
        'gait.touch.{leg}': {
            # THE COMPOSITION: the hold's arming reads the touch record's
            # SAME-TICK write (role record-input — produced by another
            # record of the set, never by this one).
            'entity': 'gait_walker.leg_contact_state', 'frame': 'controller state',
            'unit': 'bool', 'dtype': 'bool', 'phase': 'tick-start',
            'role': 'record-input'},
        'gait.hold.armed.{leg}': {
            'entity': 'gait_walker.hind_hold', 'frame': 'controller state',
            'unit': 'bool', 'dtype': 'bool', 'phase': 'tick-start', 'role': 'state'},
        'gait.hold.anchor_y.{leg}': {
            'entity': 'gait_walker.hind_hold', 'frame': 'world, plane-up axis',
            'unit': 'm', 'dtype': 'f64', 'phase': 'tick-start', 'role': 'state'},
        'gait.hold.release_tick.{leg}': {
            'entity': 'gait_walker.hind_hold', 'frame': 'controller state',
            'unit': 'tick', 'dtype': 'int', 'phase': 'tick-start', 'role': 'state'},
        'gait.hold.fire_class.{leg}': {
            'entity': 'gait_walker.hind_hold', 'frame': 'controller state',
            'unit': 'enum(0 slot,1 alternation)', 'dtype': 'int',
            'phase': 'tick-start', 'role': 'state'},
    },
    'constants': {
        'TOE_OFF': {'value': 0.68, 'provenance': f'{SRC}:58 (TOE_OFF)'},
        'tair': {'value': 9, 'provenance': 'trace-harness-dumped from the C++ '
                 'ceil((T_CYCLE-DUTY_SAMPLED)/dt) at tick_hz=300 (=9)'},
        'kTouch': TOUCH_BAND['constants']['kTouch'],
        'kReleaseBand': TOUCH_BAND['constants']['kReleaseBand'],
    },
    'initial': {
        'gait.hold.armed.{leg}': False,       # hind_step_held_ {false,false}
        'gait.hold.anchor_y.{leg}': 0.0,      # hind_step_plant_y_ {0,0}
        'gait.hold.release_tick.{leg}': -1,   # hind_step_clear_tick_ {-1,-1}
        'gait.hold.fire_class.{leg}': 0,      # hind_step_alt_ {0,0}
    },
    'assign': [
        # THE ARMING (fire) + the touching-class slot read (now: THE COMPOSITION
        # with the touch record's same-tick write) + the floor-anchor capture.
        {'write': 'gait.hold.anchor_y.{leg}',
         'expr': 'if gait.fire.{leg} then (gait.hind.heel_y.{leg} + gait.hind.mp_y.{leg}) / 2 '
                 'else gait.hold.anchor_y.{leg}'},
        {'write': 'gait.hold.release_tick.{leg}',
         'expr': 'if gait.fire.{leg} then -1 '
                 'else if gait.hold.armed.{leg} and '
                 'gait.hind.pairmin_gap.{leg} > kTouch + kReleaseBand then control.step '
                 'else gait.hold.release_tick.{leg}'},
        {'write': 'gait.hold.fire_class.{leg}',
         'expr': 'if gait.fire.{leg} then '
                 '(if now:gait.touch.{leg} and gait.hind.phase.{leg} >= TOE_OFF then 0 else 1) '
                 'else gait.hold.fire_class.{leg}'},
        # THE RELEASE (the genuine-departure band exit) and THE COMPLETION
        # (the wave-31 band entry: mode==1, t+1>=tair — the C++ tests the
        # incremented t).
        {'write': 'gait.hold.armed.{leg}',
         'expr': 'if gait.fire.{leg} then true '
                 'else if gait.hold.armed.{leg} and '
                 'gait.hind.pairmin_gap.{leg} > kTouch + kReleaseBand then false '
                 'else if gait.hind.mode.{leg} == 1 and gait.hind.t.{leg} + 1 >= tair '
                 'and gait.hind.pairmin_gap.{leg} <= kTouch then false '
                 'else gait.hold.armed.{leg}'},
    ],
}

TRUNK_VAULT_INVARIANT = {
    # Family B for the parallel demonstration: the wave-8 trunk-vault
    # membrane's SHIPPED invariant (the min-max demand/cap bound), a real
    # invariant-kind record — disjoint writes from the pilot definitions,
    # one SHARED READ (the clock phase) to exercise "shared reads harmless".
    'name': 'trunk_vault_capacity',
    'kind': 'invariant',
    'lane': LANE,
    'provenance': {
        'receipt': f'{RECEIPT_DIR}/trunk_vault.json, {RECEIPT_DIR}/receipt_wave8.json',
        'commit': BASE_COMMIT,
        'symbol': f'{SRC}:71-79 (the trunk-vault table comment: min-max demand/cap '
                  'ratio 0.881 <= 1 at every single-support node)',
    },
    'falsifier': 'P3 (store invariant preservation under concurrent merge)',
    'params': {},
    'quantities': {
        'posture.demand_ratio.max': {
            'entity': 'gait_walker.trunk_posture', 'frame': 'ratio',
            'unit': '1', 'dtype': 'f64', 'phase': 'decision',
            'role': 'external-input'},
    },
    'constants': {'kVaultCap': {'value': 0.881,
                                'provenance': 'derived trunk_vault.json (wave 8); '
                                              'the measured min-max ratio'}},
    'initial': {},
    'assign': [],
    'invariant_expr': 'posture.demand_ratio.max <= kVaultCap',
    'invariant_note': 'invariants conjoin (Models(R+{c}) = Models(R) ^ Models(c)); '
                      'they carry no write effects and never enter the '
                      'one-writer rule',
}


def pilot_records() -> list[dict]:
    return [TOUCH_BAND, STAND_FIRST_HOLD]


def load_pilot():
    """Load + validate the two pilot records (template form)."""
    return [_load(TOUCH_BAND), _load(STAND_FIRST_HOLD)]
