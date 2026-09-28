"""MAT2-U03 focus-loss / input-release policy over the U01 pinned seam.

Card done_when: "Alt-tab, disconnect and key release clear or age commands
under a declared policy; no stuck movement."

This module WRAPS the U01 input seam (input_mapper.InputMapper, vendored
byte-exact under pinned_seam/ at hashes recorded in PREREGISTRATION.md) and
adds exactly one thing: the declared release policy for the three triggers.

  * KEY RELEASE   -> upstream floor unchanged: the demand ages through the
                     U01 decay tail and lands on EXACTLY 0.0 at or before
                     release+100 ms (RELEASE_DECAY_MS), then emission stops.
  * FOCUS LOSS    -> 'clear_held_age_to_zero': upstream release_all() clears
                     every held key; any live demand AGES to exactly 0.0
                     through the same tail (the tail is never gated -- landing
                     on zero is mandatory); then new demands are HELD while
                     focus is absent: presses and mouse counts are refused BY
                     NAME in the trace, never silently.
  * DISCONNECT    -> the same declared action as focus loss, one policy id.
  * RESUME        -> refocus/reconnect lifts the gate; the next press starts a
                     fresh 50 ms grid; NOTHING from the gated window is
                     replayed (there is nothing held to replay).
  * NO STUCK MOVEMENT (consumer side) -> effective_demand() applies the
                     upstream aging floor (InputMapper.is_expired,
                     VALID_MS = 100 ms = 30 physics ticks @ 300 Hz, strict '>'):
                     a consumer holding a stale record is INERT from age 31
                     ticks even if no producer tick ever arrives again.

The policy NEVER touches state, never reads a wall clock (all times are
injected integer milliseconds), never manipulates real OS focus, and never
redeclares an upstream constant: INTERVAL_MS / RELEASE_DECAY_MS / VALID_MS /
EXPIRY_TICKS / V_MAX_IN_BAND_M_S are read from the vendored seam module at
import time by the caller and pinned by the tests. Refusals are named codes,
following the U01 trace discipline ("refusing by name, not clamping").
"""
from __future__ import annotations

POLICY_ID = 'u03_focus_release_policy.v1'
FOCUS_LOSS_ACTION = 'clear_held_age_to_zero'
DISCONNECT_ACTION = 'clear_held_age_to_zero'
KEY_RELEASE_ACTION = 'age_decay_to_zero'        # the U01 floor, unchanged
GATE_ACTION = 'hold_new_demands_while_gated'
RESUME_ACTION = 'fresh_grid_no_replay'

POLICY = {
    'id': POLICY_ID,
    'focus_loss': FOCUS_LOSS_ACTION,
    'disconnect': DISCONNECT_ACTION,
    'key_release': KEY_RELEASE_ACTION,
    'gate': GATE_ACTION,
    'resume': RESUME_ACTION,
}

_METHODS = ('press', 'release', 'release_all', 'tick')


class FocusPolicy:
    """The declared release policy wrapped around a U01 InputMapper.

    The mapper must expose the U01 interface: press(name, now_ms),
    release(name, now_ms), release_all(now_ms), tick(now_ms), held, and the
    static is_expired(record, now_ms). A wrapper object missing any member is
    refused at construction ('upstream_interface_missing:<member>') -- the
    policy is only lawful ON the pinned seam.
    """

    def __init__(self, mapper):
        for name in _METHODS:
            if not callable(getattr(mapper, name, None)):
                raise ValueError('upstream_interface_missing:' + name)
        if not callable(getattr(mapper, 'is_expired', None)):
            raise ValueError('upstream_interface_missing:is_expired')
        if not isinstance(getattr(mapper, 'last_trace', None), dict):
            raise ValueError('upstream_interface_missing:last_trace')
        try:
            mapper.held
        except Exception:
            raise ValueError('upstream_interface_missing:held')
        self._m = mapper
        self._gated = False
        self._last_record = None          # the consumer's latest held record
        self.last_trace = {}              # policy-level trace (named events)

    # ── trace discipline: every transition and refusal is named ─────────────
    def _event(self, kind, now_ms, **detail):
        row = {'event': kind, 'now_ms': (None if now_ms is None else int(now_ms))}
        row.update(detail)
        self.last_trace.setdefault('events', []).append(row)
        return row

    # ── state ────────────────────────────────────────────────────────────────
    @property
    def gated(self):
        return self._gated

    @property
    def held(self):
        return self._m.held

    @property
    def last_record(self):
        return self._last_record

    # ── the declared triggers ────────────────────────────────────────────────
    def focus_lost(self, now_ms):
        """Alt-tab / window focus loss: clear held keys, age any live demand
        to exactly 0.0, gate new demands while focus is absent. Idempotent."""
        self._m.release_all(int(now_ms))
        already = self._gated
        self._gated = True
        self._event('focus_lost', now_ms, action=FOCUS_LOSS_ACTION,
                    already_gated=already, held_after=sorted(self._m.held))
        return FOCUS_LOSS_ACTION

    def disconnected(self, now_ms):
        """Input-source disconnect: the same declared action as focus loss."""
        self._m.release_all(int(now_ms))
        already = self._gated
        self._gated = True
        self._event('disconnect', now_ms, action=DISCONNECT_ACTION,
                    already_gated=already, held_after=sorted(self._m.held))
        return DISCONNECT_ACTION

    def focus_gained(self, now_ms):
        """Refocus: lift the gate; the next press starts a fresh grid; the
        gated window is never replayed."""
        was = self._gated
        self._gated = False
        self._event('focus_gained', now_ms, action=RESUME_ACTION,
                    resumed=was, replayed=0)
        return RESUME_ACTION

    def reconnected(self, now_ms):
        """Reconnect: the same resume action as refocus."""
        was = self._gated
        self._gated = False
        self._event('reconnect', now_ms, action=RESUME_ACTION,
                    resumed=was, replayed=0)
        return RESUME_ACTION

    # ── input forwarding (gated inputs are refused BY NAME) ─────────────────
    def press(self, name, now_ms):
        if self._gated:
            self._event('press_refused_while_gated', now_ms, name=name)
            return None
        return self._m.press(name, int(now_ms))

    def mouse(self, dx_counts, now_ms=None):
        if self._gated:
            self._event('mouse_refused_while_gated', now_ms,
                        counts=float(dx_counts))
            return None
        return self._m.mouse(dx_counts)

    def release(self, name, now_ms):
        # Releasing is always lawful (also while gated): the U01 floor handles
        # the aging; the wrapper adds nothing and hides nothing.
        return self._m.release(name, int(now_ms))

    # ── the 20 Hz boundary: forwarded ALWAYS so the aging tail completes ────
    def tick(self, now_ms):
        records = self._m.tick(int(now_ms))
        if records:
            self._last_record = records[-1]
        return records

    # ── consumer-side semantics: the no-stuck-movement read ──────────────────
    def effective_demand(self, now_ms, last_record=None):
        """The ONLY lawful consumer read on this floor.

        Returns ('inert', None) when there is no record at all or the held
        record is EXPIRED by the upstream aging floor (is_expired, strict
        '>': age 30 ticks is still lawful, 31 is not); otherwise
        ('commanded', record). A consumer that acts on anything else can get
        stuck movement; a consumer using this read cannot.
        """
        record = last_record if last_record is not None else self._last_record
        if record is None:
            self._event('demand_inert', now_ms, reason='no_record')
            return ('inert', None)
        if self._m.is_expired(record, int(now_ms)):
            self._event('demand_inert', now_ms, reason='expired_record',
                        issued_tick=int(record.issued_tick))
            return ('inert', None)
        return ('commanded', record)
