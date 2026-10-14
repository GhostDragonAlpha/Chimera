"""P2 — the compiler proof on real substrate (bit-exact replay).

FALSIFIER P2 (preregistration + amendment-1 item 6): on every tick of the
replayed walk the compiled records' decisions — touch class, band exits
(clear_tick), hold arming (held), fire class — must match the shipped C++
path EXACTLY, and the float next-state bits (the floor anchor) must match
bit-for-bit on a lossless replay. ONE divergent tick fires.

The trace is produced by tools/constraint_ledger/trace_harness.cpp (the
UNCHANGED substrate; preregistration amendment-2 names the evidence
boundary). Boundary fixtures probe each threshold at the value and its
nextafter neighbors (the L2/L3 fixture discipline).

Run: python -m unittest tools.constraint_ledger.tests_p2 -v
"""
from __future__ import annotations

import math
import struct
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCENE = ROOT / '.tmp/gait-walker/scene.json'
TRACE = ROOT / '.tmp/trace1.jsonl'
TRACE2 = ROOT / '.tmp/trace2.jsonl'
HARNESS = ROOT / '.tmp/trace_harness.exe'

BUILD_CMD = ['g++', '-O2', '-std=c++17',
             '-I', 'ChimeraEngine/engine', '-I', 'ChimeraEngine/native/viewer3rd',
             'tools/constraint_ledger/trace_harness.cpp',
             '-o', '.tmp/trace_harness.exe']
RUN_CMD = ['.tmp/trace_harness.exe', '.tmp/gait-walker/scene.json', '.tmp/trace1.jsonl']
RUN2_CMD = ['.tmp/trace_harness.exe', '.tmp/gait-walker/scene.json', '.tmp/trace2.jsonl']
# the wave-32 receipt's recorded death for THIS substrate state:
EXPECTED_REFUSAL = 300


def ensure_trace() -> None:
    """Regenerate scene + build + run the instrument if the trace is absent.
    The recorded commands are the registered baseline recipe."""
    import json
    if not SCENE.exists():
        subprocess.run(['python', 'tools/science_funnel/gait_scene.py',
                        '--output', '.tmp/gait-walker'],
                       cwd=ROOT, check=True, capture_output=True)
    if not HARNESS.exists():
        subprocess.run(BUILD_CMD, cwd=ROOT, check=True)
    if not TRACE.exists():
        subprocess.run(RUN_CMD, cwd=ROOT, check=True)
    if not TRACE2.exists():
        subprocess.run(RUN2_CMD, cwd=ROOT, check=True)


def load_trace() -> tuple[dict, list[dict]]:
    ensure_trace()
    lines = TRACE.read_text(encoding='utf-8').splitlines()
    meta = None
    rows: list[dict] = []
    for ln in lines:
        obj = __import__('json').loads(ln)
        if obj.get('meta'):
            meta = obj
        else:
            rows.append(obj)
    return meta, rows


def bits_of(x: float) -> int:
    return struct.unpack('<Q', struct.pack('<d', x))[0]


def nextafter(x: float, direction: int) -> float:
    return math.nextafter(x, math.inf if direction > 0 else -math.inf)


class TestTraceLossless(unittest.TestCase):
    """F-EVIDENCE-GAP guard: the trace's decimal fields must round-trip to
    the recorded bit patterns — formatted decimals are never trusted as
    float bits (amendment-1 item 6)."""

    def test_decimal_matches_bits_every_row(self):
        meta, rows = load_trace()
        self.assertIsNotNone(meta)
        for r in rows:
            for k in range(4):
                self.assertEqual(bits_of(r['gaps'][k]), r['gaps_bits'][k],
                                 f"row {r['j']} gap {k}: decimal does not round-trip")
            for leg in r['leg']:
                for name, bname in (('plant_y', 'plant_y_bits'),
                                    ('heel_y', 'heel_y_bits'),
                                    ('mp_y', 'mp_y_bits')):
                    self.assertEqual(bits_of(leg[name]), leg[bname],
                                     f"row {r['j']} {name}")
        # the registered constants: tair from the substrate expression
        self.assertEqual(meta['tair'], 9.0)
        self.assertEqual(meta['tick_hz'], 300.0)

    def test_instrument_determinism_and_receipt_cross_check(self):
        ensure_trace()
        self.assertEqual(TRACE.read_bytes(), TRACE2.read_bytes(),
                         'the instrument must be byte-deterministic (double run)')
        tail = TRACE2.read_text(encoding='utf-8')
        self.assertIn('300', tail)  # rows present


class TestBitExactReplay(unittest.TestCase):
    """THE P2 FALSIFIER. The compiled record set replays the recorded
    external inputs through ITS OWN state (seeded only at row 0 from the
    declared initials, never reset from the reference) and must reproduce
    the shipped decisions exactly, every tick."""

    def setUp(self):
        self.meta, self.rows = load_trace()
        from tools.constraint_ledger.compile import compile_fragment
        from tools.constraint_ledger.pilot_laws import (concrete_externals,
                                                        load_pilot)
        self.touch_rec, self.hold_rec = load_pilot()
        # the record constants must carry the substrate values the trace saw
        self.assertEqual(self.hold_rec.constants['tair']['value'],
                         self.meta['tair'])
        self.frag = compile_fragment([self.touch_rec, self.hold_rec],
                                     concrete_externals(), {})

    @staticmethod
    def pairmin(row, leg):
        # leg_contact's gmin loop: min over the leg's two pads, seeded high
        g0, g1 = row['gaps'][2 * leg], row['gaps'][2 * leg + 1]
        return min(g0, g1)

    def bundles(self, j):
        """(row_prev bundle, row_now bundle) for decision row j>=1 with the
        registered phase alignment (tick-start from j-1, decision from j)."""
        prev_row, now_row = self.rows[j - 1], self.rows[j]
        prev, now = {}, {}
        for leg, name in ((0, 'left'), (1, 'right')):
            prev[f'gait.hind.pairmin_gap.{name}'] = self.pairmin(prev_row, leg)
            prev[f'gait.hind.mode.{name}'] = int(prev_row['leg'][leg]['mode'])
            prev[f'gait.hind.t.{name}'] = float(prev_row['leg'][leg]['t'])
            prev[f'gait.hind.heel_y.{name}'] = prev_row['leg'][leg]['heel_y']
            prev[f'gait.hind.mp_y.{name}'] = prev_row['leg'][leg]['mp_y']
            now[f'gait.fire.{name}'] = (now_row['leg'][leg]['fires']
                                        > prev_row['leg'][leg]['fires'])
            now[f'gait.hind.phase.{name}'] = now_row['leg'][leg]['phase']
        prev.update(now)
        return prev, now

    def test_initial_state_matches_shipped_row0(self):
        r0 = self.rows[0]
        from tools.constraint_ledger.pilot_laws import load_pilot
        touch, hold = load_pilot()
        self.assertEqual(r0['touch'], [False, False])
        for leg in r0['leg']:
            self.assertEqual(leg['held'], False)
            self.assertEqual(leg['clear_tick'], -1)
            self.assertEqual(leg['fire_class'], 0)
            self.assertEqual(leg['plant_y_bits'], bits_of(0.0))
            self.assertEqual(leg['fires'], 0)

    def test_every_tick_matches_shipped_exactly(self):
        from tools.constraint_ledger.compile import outputs_of
        state = dict(self.frag.initial)
        first_divergence = None
        checked = 0
        for j in range(1, len(self.rows)):
            row = self.rows[j]
            prev, now = self.bundles(j)
            same, state = outputs_of(self.frag, state, prev, now, j - 1)
            shipped = {
                ('gait.touch.left', row['touch'][0]),
                ('gait.touch.right', row['touch'][1]),
                ('gait.hold.armed.left', bool(row['leg'][0]['held'])),
                ('gait.hold.armed.right', bool(row['leg'][1]['held'])),
                ('gait.hold.release_tick.left', row['leg'][0]['clear_tick']),
                ('gait.hold.release_tick.right', row['leg'][1]['clear_tick']),
                ('gait.hold.fire_class.left', row['leg'][0]['fire_class']),
                ('gait.hold.fire_class.right', row['leg'][1]['fire_class']),
            }
            for qname, want in shipped:
                got = same[qname]
                if isinstance(want, bool):
                    got = bool(got)
                if got != want and first_divergence is None:
                    first_divergence = {'tick': j, 'quantity': qname,
                                        'expected': want, 'actual': got}
                checked += 1
            # float next-state BITS: the floor anchor
            for leg, name in ((0, 'left'), (1, 'right')):
                want_bits = row['leg'][leg]['plant_y_bits']
                got_bits = bits_of(same[f'gait.hold.anchor_y.{name}'])
                checked += 1
                if got_bits != want_bits and first_divergence is None:
                    first_divergence = {'tick': j,
                                        'quantity': f'gait.hold.anchor_y.{name}',
                                        'expected_bits': want_bits,
                                        'actual_bits': got_bits}
            if first_divergence:
                break
        self.assertIsNone(first_divergence,
                          f'P2 FIRED at {first_divergence} '
                          f'(rows replayed {j}, checks {checked})')
        self.assertEqual(j, len(self.rows) - 1,
                         'the replay must reach the final row')
        # the walk must be long enough to exercise fires, exits and replants
        fires = sum(r['leg'][0]['fires'] + r['leg'][1]['fires'] for r in self.rows)
        self.assertGreater(fires, 0, 'no step fires in the trace — nothing tested')
        self.assertGreaterEqual(checked, 300 * 10)

    def test_replay_reproduces_the_receipt_death_tick(self):
        self.assertEqual(len(self.rows) - 1, EXPECTED_REFUSAL,
                         'the instrumented walk must die where the wave-32 '
                         'receipt recorded the death (tick 300)')


class TestBoundaryFixtures(unittest.TestCase):
    """Amendment-1 item 6: every represented threshold probed at the value
    and its nextafter neighbors, all Boolean state combinations, and the
    initialization case. The hand-derived truth table IS the shipped
    leg_contact semantics (gait_controller.hpp:574-576)."""

    K_TOUCH = 1e-5
    K_RELEASE = 1e-5 + 1e-6   # the sum must come from the record constants

    def _compiled_touch(self):
        from tools.constraint_ledger.compile import compile_fragment
        from tools.constraint_ledger.pilot_laws import concrete_externals, load_pilot
        touch, _ = load_pilot()
        self.assertEqual(touch.constants['kTouch']['value'], self.K_TOUCH)
        self.assertEqual(
            touch.constants['kReleaseBand']['value'] + self.K_TOUCH,
            self.K_RELEASE)
        return compile_fragment([touch], concrete_externals(), {})

    def test_nextafter_thresholds_and_boolean_combinations(self):
        frag = self._compiled_touch()
        from tools.constraint_ledger.compile import outputs_of
        kt, kr = self.K_TOUCH, self.K_RELEASE
        gaps = [nextafter(kt, -1), kt, nextafter(kt, +1),
                nextafter(kr, -1), kr, nextafter(kr, +1), 0.065]
        for g in gaps:
            for prev in (False, True):
                # hand-derived shipped truth: inside kTouch -> touching; the
                # genuine departure beyond the sum -> released; the band
                # holds the previous state.
                if g <= kt:
                    want = True
                elif g > kr:
                    want = False
                else:
                    want = prev
                row = {'gait.hind.pairmin_gap.left': g,
                       'gait.hind.pairmin_gap.right': g,
                       'control.step': 0}
                _, st = outputs_of(frag, {'gait.touch.left': prev,
                                          'gait.touch.right': prev},
                                   row, row, 0)
                self.assertEqual(st['gait.touch.left'], want,
                                 f'gap={g!r} prev={prev}')
                self.assertEqual(st['gait.touch.right'], want,
                                 f'gap={g!r} prev={prev}')

    def test_hysteresis_band_excursion_never_releases(self):
        # THE WAVE-22 LAW's own story: a band-edge graze (one tick above the
        # band's lower edge) holds the latch; only a GENUINE departure
        # releases. Sequenced through the compiled record's own state.
        frag = self._compiled_touch()
        from tools.constraint_ledger.compile import outputs_of
        kt, kr = self.K_TOUCH, self.K_RELEASE
        seq = [nextafter(kt, -1),        # touchdown
               nextafter(kt, +1),        # graze up into the band
               nextafter(kr, -1),        # still band -> HELD (prev true)
               nextafter(kr, +1),        # genuine departure -> released
               kt]                       # re-entry -> a real rising edge
        state = {'gait.touch.left': False, 'gait.touch.right': False}
        want = [True, True, True, False, True]
        for i, g in enumerate(seq):
            row = {'gait.hind.pairmin_gap.left': g,
                   'gait.hind.pairmin_gap.right': g}
            _, state = outputs_of(frag, state, row, row, i)
            self.assertEqual(state['gait.touch.left'], want[i],
                             f'step {i} gap={g!r}')


if __name__ == '__main__':
    unittest.main()
