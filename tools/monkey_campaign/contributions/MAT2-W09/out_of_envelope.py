#!/usr/bin/env python3
"""MAT2-W09: the DECLARED out-of-envelope supervisor (prereg section 2).

The controller's explicit response when the observed state leaves the
walking envelope. Physical-authority law: the supervisor owns NO physics —
it cannot write scene state, pose, velocity, phase or contacts; its only
output is the certified 8-command limiter path plus a declared event
ledger. Every envelope constant here is DERIVED from the pinned scene's own
declared constants / the frozen manifest (none tuned):

  supported tick     at least one foot contact in the seam
  unsupported tick   both foot channels 0 (all pad gaps >= contact_threshold)
  FALL_AFTER_TICKS   the scene's own declared reflex horizon
                     (REFLEX_TRIP_TICKS = 90 ticks = 0.3 s at 300 Hz)
  R1 drive cut       stride channels -> manifest bounds_lo (the certified
                     MINIMUM drive 0.2; the limiter forbids zero)
  R2 neutral + fall  all 8 channels -> manifest center; fall event ONCE
  R3 terminal        outcome declaration + final state hash; the only
                     restart instrument is the declared COMPLETE-snapshot
                     restore, recorded in the ledger

Detectors (seam-only; the falsifiers bite on tampered arms and stay green
on clean arms): the fresh-seed PCG64 micro-terrain draw chain, the phase
recursion, the velocity recursion (the inertia law: velocity moves ONLY by
the declared equation — never frozen or canceled), the
observations-from-solved-state equality, and the R1 coverage audit.

Preregistration sha256 is bound by every receipt (verify_inputs.prereg_sha256).
"""
from __future__ import annotations

import copy
import hashlib
import json

import numpy as np

STRIDE_INDICES = (1, 5)          # the declared drive channels (manifest)
CONTACT_CHANNELS = (4, 5)        # foot_contacts / foot_forces seam slots
SEAM_VELOCITY_WINDOW = 1e-5      # declared float32-seam window (m/s)
ENERGY_WINDOW = 1e-5             # declared per-unit-mass window (J; the
                                 # seam's warm observability at micro-
                                 # marginal crossings bounds the account at
                                 # this level -- amendment A7: the recorded
                                 # max residuals are ~2.4e-6)
PHASE_WINDOW = 1e-9              # declared phase recursion window (cycles)
DRAW_WINDOW = 1e-9               # declared micro-terrain window (m)


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def record_sha256(rec: dict) -> str:
    """The SEAM record's own hash (the declared pre-state basis)."""
    return hashlib.sha256(canonical(rec)).hexdigest()


def derive_constants(params: dict, manifest: dict) -> dict:
    """Every envelope/response constant, derived from the pinned inputs."""
    return {
        "contact_threshold_m": params["contact_threshold"],
        "ground_clearance_m": params["ground_clearance"],
        "lift_gain": params["lift_gain"],
        "stride_gain": params["stride_gain"],
        "mp_phase_offset": params["mp_phase_offset"],
        "cycle_ticks": params["cycle_ticks"],
        "dt_s": params["dt"],
        "damping_per_s": params["damping"],
        "warm_damp_lo": params["warm_damp_lo"],
        "warm_damp_span": params["warm_damp_span"],
        "warm_rise": params["warm_rise"],
        "warm_decay_air": params["warm_decay_air"],
        "micro_terrain_amp": params["micro_terrain_amp"],
        "fall_after_ticks": params["reflex_trip_ticks"],
        "fall_after_basis": "REFLEX_TRIP_TICKS (the scene's declared reflex "
                            "horizon; derived, not tuned)",
        "bounds_lo": [float(v) for v in manifest["action"]["bounds_lo"]],
        "bounds_hi": [float(v) for v in manifest["action"]["bounds_hi"]],
        "center": [float(v) for v in manifest["action"]["center"]],
        "stride_indices": list(STRIDE_INDICES),
        "contact_channels": list(CONTACT_CHANNELS),
    }


# ----------------------------------------------------------------- monitor
class EnvelopeMonitor:
    """Classifies ticks from the DECLARED observation seam ONLY."""

    def __init__(self, consts: dict):
        self.consts = consts

    def classify(self, rec: dict) -> dict:
        fc = rec["foot_contacts"]
        supported = bool(fc[self.consts["contact_channels"][0]] == 1.0
                         or fc[self.consts["contact_channels"][1]] == 1.0)
        cls = "SUPPORTED" if supported else "UNSUPPORTED"
        return {"tick": rec["tick"], "class": cls, "supported": supported,
                "foot_contacts": [float(v) for v in fc],
                "basis": "seam foot_contacts channels "
                         + repr(self.consts["contact_channels"])}


class StaleSupportMonitor(EnvelopeMonitor):
    """The FB4 TAMPER monitor: keeps claiming support (a stale verdict).

    Declared tamper class (G07 FB5's stale stick verdict, task-owned):
    the audit must fire because unsupported seam ticks go unresponded."""

    def classify(self, rec: dict) -> dict:
        out = super().classify(rec)
        out.update({"class": "SUPPORTED", "supported": True,
                    "tamper": "stale_support_verdict"})
        return out


class InjectionMonitor(EnvelopeMonitor):
    """The A2 DECLARED injection: fabricated unsupported verdicts on the
    monitor input path for ticks [t0, t0+ticks). The scene's own seam stays
    supported; `seam_truth` always carries the true class; the receipt
    labels the arm monitor_input_injection."""

    def __init__(self, consts: dict, t0: int, ticks: int):
        super().__init__(consts)
        self.t0 = int(t0)
        self.ticks = int(ticks)

    def classify(self, rec: dict) -> dict:
        out = super().classify(rec)
        truth = out["class"]
        if self.t0 <= out["tick"] < self.t0 + self.ticks:
            out.update({"class": "UNSUPPORTED", "supported": False,
                        "injected": True, "seam_truth": truth})
        else:
            out.update({"seam_truth": truth})
        return out


# -------------------------------------------------------------- supervisor
class OutOfEnvelopeSupervisor:
    """The declared response stack. apply() NEVER touches scene state."""

    def __init__(self, consts: dict, monitor: EnvelopeMonitor | None = None):
        self.c = consts
        self.monitor = monitor or EnvelopeMonitor(consts)
        self.streak = 0
        self.fall_declared_tick = None
        self.fell = False
        self.ledger: list[dict] = []
        self.classes: list[str] = []
        self._r1_active = False

    # -- response vectors (pure functions of the declared constants) -----
    def _r1_vector(self, applied):
        out = [float(v) for v in applied]
        for i in self.c["stride_indices"]:
            out[i] = self.c["bounds_lo"][i]     # certified MINIMUM drive
        return out

    def _r2_vector(self):
        return [float(v) for v in self.c["center"]]

    # -- the declared saturation rule ------------------------------------
    def _sat_for(self, applied_in, applied_out, sat_in):
        """Policy limiter saturation passes through on untouched channels;
        supervisor overrides are within bounds by construction -> slot 0."""
        out = [float(v) for v in sat_in]
        for i, (a, b) in enumerate(zip(applied_in, applied_out)):
            if a != b:
                lo, hi = self.c["bounds_lo"][i], self.c["bounds_hi"][i]
                out[i] = 0.0 if lo <= b <= hi else out[i]
        return out

    def apply(self, tick: int, rec: dict, applied, sat_in):
        """One controller tick: classify -> respond -> ledger. Returns
        (applied_vector, saturation_vector, events_this_tick).

        R2 LATCH (prereg amendment A3): once a fall is declared the neutral
        response holds until the terminal declaration — the fallen episode
        does not resume in-envelope control."""
        verdict = self.monitor.classify(rec)
        self.classes.append(verdict["class"])
        if verdict["supported"]:
            self.streak = 0
        else:
            self.streak += 1

        events = []
        out = [float(v) for v in applied]
        if self.fell:
            out = self._r2_vector()                              # R2 latch
            return out, self._sat_for(applied, out, sat_in), events
        if not verdict["supported"] and self.streak < self.c["fall_after_ticks"]:
            out = self._r1_vector(applied)                       # R1
            if not self._r1_active:
                events.append(self._event(tick, rec, "R1_engage",
                                          verdict, out))
                self._r1_active = True
        else:
            if self._r1_active:
                events.append(self._event(tick, rec, "R1_release",
                                          verdict, out))
                self._r1_active = False
        if not verdict["supported"] \
                and self.streak >= self.c["fall_after_ticks"]:
            out = self._r2_vector()                              # R2
            self.fell = True
            self.fall_declared_tick = tick
            events.append(self._event(tick, rec, "R2_fall_declared",
                                      verdict, out))
        return out, self._sat_for(applied, out, sat_in), events

    def _event(self, tick, rec, kind, verdict, out_vector):
        row = {"tick": tick, "event": kind, "streak": self.streak,
               "pre_state_sha256": record_sha256(rec),
               "pre_state_basis": "canonical seam observation_record",
               "monitor_class": verdict["class"],
               "applied_vector": [float(v) for v in out_vector]}
        self.ledger.append(row)
        return row

    def terminal(self, rec: dict, horizon: int) -> dict:
        """R3: the explicit post-failure declaration (no concealed end)."""
        outcome = "fall_declared" if self.fell else "completed"
        row = {"tick": horizon - 1, "event": "R3_terminal", "outcome": outcome,
               "fall_declared_tick": self.fall_declared_tick,
               "final_state_sha256": record_sha256(rec),
               "final_state_basis": "canonical seam observation_record",
               "restart_instrument": "declared COMPLETE-snapshot restore "
                                     "(ledgered); none performed",
               "recovery_skill": "none (optional per card observation; "
                                 "no product contract requires it)"}
        self.ledger.append(row)
        return row


# --------------------------------------------------------------- detectors
def warm_at_step(records: list[dict], consts: dict) -> tuple[list, list]:
    """W[t]: the warm value USED by scene step t (t = 0..H-2), reconstructed
    by the DECLARED SEAM LAW (amendment A7): on a contact tick the seam
    itself reports `foot_force == 0.25 * warm` — anchor on it; while
    airborne the warm is unobservable and the declared decay recursion runs
    from the last anchored value. This is exact at every contact tick and
    recursion-exact across airborne spans; the micro-marginal crossing
    ambiguity of the pre-amendment flag-chain reconstruction is gone. The
    reconstruction is validated independently by the velocity and energy
    identities, whose d_eff consumes it."""
    c = consts
    ff = c["_front_force"]
    wl = wr = 0.0
    out_l, out_r = [], []
    for t in range(len(records) - 1):
        rec_n = records[t + 1]
        fc_n = rec_n["foot_contacts"]
        ffn = rec_n["foot_forces"]
        wl = ffn[4] / ff if fc_n[4] == 1.0 else wl * c["warm_decay_air"]
        wr = ffn[5] / ff if fc_n[5] == 1.0 else wr * c["warm_decay_air"]
        out_l.append(wl)
        out_r.append(wr)
    return out_l, out_r


def warm_force_crosscheck(records: list[dict], consts: dict) -> dict:
    """The declared seam law binds `foot_forces == 0.25 * warm` on contact
    ticks (prereg amendment A7): steady-contact ticks at the exact window;
    at a transition tick the recomputed contact can disagree with the
    previous step's contact flag by the scene's own observation law, so
    transition ticks carry the declared 1e-3 window."""
    c = consts
    wl, wr = warm_at_step(records, c)
    violations = []
    worst = 0.0
    steady = 0
    for t in range(len(records) - 1):
        rec_n = records[t + 1]
        fc_n = rec_n["foot_contacts"]
        fc_c = records[t]["foot_contacts"]
        ff = rec_n["foot_forces"]
        for leg, warm_v, ch in (("left", wl[t], 4), ("right", wr[t], 5)):
            if fc_n[ch] != 1.0:
                continue
            if fc_c[ch] == 1.0:
                window = 1e-6
                steady += 1
            else:
                window = 1e-3
            res = abs(ff[ch] - c["_front_force"] * warm_v)
            if window == 1e-6:
                worst = max(worst, res)
            if res > window:
                violations.append({"tick": rec_n["tick"], "leg": leg,
                                   "residual": res,
                                   "kind": "steady" if window == 1e-6
                                   else "transition"})
    return {"max_steady_residual": worst, "violations": violations,
            "window_steady": 1e-6, "window_transition": 1e-3,
            "steady_ticks_checked": steady,
            "front_force": c["_front_force"]}


def velocity_recursion_check(records: list[dict], applied_per_tick: list,
                             consts: dict) -> dict:
    """The inertia law: v moves ONLY by the declared equation. Returns the
    per-tick residuals; a concealed force breaks it (FB2), a concealed
    reset breaks it (FB1)."""
    c = consts
    dt = c["dt_s"]
    warm_l, warm_r = warm_at_step(records, c)
    residuals = []
    worst = 0.0
    violations = []
    for t in range(len(records) - 1):
        v = float(records[t]["com_vel"][0])
        vn = float(records[t + 1]["com_vel"][0])
        a = c["stride_gain"] * 0.5 * (applied_per_tick[t][1]
                                      + applied_per_tick[t][5])
        d = c["damping_per_s"] * (c["warm_damp_lo"]
                                  + c["warm_damp_span"]
                                  * 0.5 * (warm_l[t] + warm_r[t]))
        pred = v + dt * (a - d * v)
        res = abs(vn - pred)
        residuals.append(res)
        worst = max(worst, res)
        if res > SEAM_VELOCITY_WINDOW:
            violations.append({"tick": t, "residual": res})
    return {"max_residual_m_s": worst, "violations": violations,
            "window_m_s": SEAM_VELOCITY_WINDOW,
            "law": "v(t+1) = v(t) + dt*(a_com - d_eff*v(t)); a_com from the "
                   "recorded applied strides; d_eff from the declared warm "
                   "recursion of the recorded contacts"}


def phase_recursion_check(records: list[dict], applied_per_tick: list,
                          consts: dict) -> dict:
    """The phase clock law (prereg amendment A5): each tick's recovered
    phase delta must be EXACTLY one of the scene's two declared rates
    {1/cycle_ticks, 0.5/cycle_ticks} (the trip reflex is seam-invisible, so
    a single-rate law would false-fire on declared trips). A concealed
    reset produces a delta matching neither and FIRES. Also reports the
    observed half-rate tick count per leg (the trip evidence)."""
    c = consts
    rate = 1.0 / c["cycle_ticks"]
    violations = []
    worst = 0.0
    half = {"left": 0, "right": 0}
    for t in range(1, len(records) - 1):
        off_l = applied_per_tick[t - 1][0]
        off_r = applied_per_tick[t - 1][4]
        pl = (records[t]["phase_left"] - off_l) % 1.0
        pr = (records[t]["phase_right"] - off_r) % 1.0
        off_ln = applied_per_tick[t][0]
        off_rn = applied_per_tick[t][4]
        pln = (records[t + 1]["phase_left"] - off_ln) % 1.0
        prn = (records[t + 1]["phase_right"] - off_rn) % 1.0
        for name, a, b in (("left", pl, pln), ("right", pr, prn)):
            d = (b - a) % 1.0
            res_full = abs(d - rate)
            res_half = abs(d - rate / 2.0)
            res = min(res_full, res_half)
            if res <= PHASE_WINDOW:
                if res_half <= PHASE_WINDOW:
                    half[name] += 1
            elif (1.0 - res) > PHASE_WINDOW:
                violations.append({"tick": t, "leg": name, "residual": res,
                                   "delta": d})
                worst = max(worst, res)
    return {"max_residual_cycles": worst, "violations": violations,
            "window_cycles": PHASE_WINDOW,
            "rate_full_per_tick": rate,
            "rate_half_per_tick": rate / 2.0,
            "half_rate_ticks": half}


def micro_draw_chain_check(records: list[dict], applied_per_tick: list,
                           consts: dict, seed: int) -> dict:
    """The fresh-seed PCG64 draw chain: record(t)'s pad gaps embed the micro
    drawn at step(t-1) (record 0 carries the primed 0.0). A concealed
    snapshot rewind repeats the stream and FIRES here (FB1)."""
    c = consts
    rng = np.random.Generator(np.random.PCG64(int(seed)))
    horizon = len(records)
    amp = c["micro_terrain_amp"]
    stream = [float(rng.uniform(-amp, amp)) for _ in range(horizon)]
    violations = []
    worst = 0.0
    for t in range(1, horizon):
        eff_l = records[t]["phase_left"] % 1.0
        swing_l = max(0.0, float(np.sin(2.0 * np.pi * eff_l)))
        lift_l = applied_per_tick[t - 1][2]
        micro = (records[t]["pad_gaps"]["hl"][0] - c["ground_clearance_m"]
                 - lift_l * swing_l)
        res = abs(micro - stream[t - 1])
        if res > DRAW_WINDOW:
            violations.append({"tick": t, "residual": res})
            worst = max(worst, res)
    return {"max_residual_m": worst, "violations": violations,
            "window_m": DRAW_WINDOW,
            "law": "micro in record(t) == fresh-seed PCG64 draw t-1; one "
                   "draw per step, no rewinds"}


def observations_from_solved_state(records_delivered, records_solved) -> dict:
    """The animation-substitution detector: every delivered record must be
    byte-equal to the scene's own observation_record() at that tick."""
    mismatches = []
    for t, (a, b) in enumerate(zip(records_delivered, records_solved)):
        if canonical(a) != canonical(b):
            mismatches.append(t)
    return {"mismatch_ticks": mismatches,
            "law": "delivered record == scene.observation_record() "
                   "(canonical bytes) at every tick"}


def r1_coverage_audit(truth_classes: list[str],
                      supervisor: OutOfEnvelopeSupervisor,
                      fall_after_ticks: int) -> dict:
    """The wrong-command-response audit, on the TRUE seam classes (a plain
    EnvelopeMonitor's verdicts, never the audited monitor's own): every
    unsupported interval must open with a declared R1_engage (or carry R2
    at the horizon); a stale support verdict leaves gaps and FIRES (FB4)."""
    intervals = []
    active_start = None
    for t, cl in enumerate(truth_classes):
        if cl == "UNSUPPORTED" and active_start is None:
            active_start = t
        if cl != "UNSUPPORTED" and active_start is not None:
            intervals.append([active_start, t - 1])
            active_start = None
    if active_start is not None:
        intervals.append([active_start, len(truth_classes) - 1])
    uncovered = []
    for lo, hi in intervals:
        if supervisor.fall_declared_tick is not None \
                and lo >= supervisor.fall_declared_tick:
            continue    # R2 latch covers every post-fall interval (A3)
        opened = any(row["event"] in ("R1_engage", "R2_fall_declared")
                     and lo <= row["tick"] <= hi
                     for row in supervisor.ledger)
        if not opened:
            uncovered.append([lo, hi])
    return {"unsupported_intervals": intervals,
            "uncovered_intervals": uncovered,
            "fall_declared_tick": supervisor.fall_declared_tick,
            "fall_after_ticks": fall_after_ticks,
            "law": "every unsupported interval must open with a declared "
                   "R1_engage (or R2_fall_declared at the horizon)"}


def energy_account(records: list[dict], applied_per_tick: list,
                   consts: dict) -> dict:
    """C13 on the declared model (per unit mass; prereg amendment A5): the
    exact discrete identity `KE' - KE == dW - dL + dv^2/2` with
    `dW = a_com*v*dt`, `dL = d_eff*v^2*dt`, `dv` the declared recursion
    increment."""
    c = consts
    dt = c["dt_s"]
    warm_l, warm_r = warm_at_step(records, c)
    worst = 0.0
    violations = []
    total_work = 0.0
    total_loss = 0.0
    for t in range(len(records) - 1):
        v = float(records[t]["com_vel"][0])
        vn = float(records[t + 1]["com_vel"][0])
        a = c["stride_gain"] * 0.5 * (applied_per_tick[t][1]
                                      + applied_per_tick[t][5])
        d = c["damping_per_s"] * (c["warm_damp_lo"]
                                  + c["warm_damp_span"]
                                  * 0.5 * (warm_l[t] + warm_r[t]))
        dv = dt * (a - d * v)
        ke0, ke1 = 0.5 * v * v, 0.5 * vn * vn
        work = a * v * dt
        loss = d * v * v * dt
        res = abs((ke1 - ke0) - (work - loss + 0.5 * dv * dv))
        worst = max(worst, res)
        total_work += work
        total_loss += loss
        if res > ENERGY_WINDOW:
            violations.append({"tick": t, "residual": res})
    return {"max_residual_J": worst, "violations": violations,
            "window_J": ENERGY_WINDOW, "drive_work_J": total_work,
            "damping_loss_J": total_loss,
            "identity": "KE' - KE == dW - dL + dv^2/2",
            "model": "per unit mass; KE = v^2/2; no vertical body dynamics, "
                     "gravity or floor body in this declared surrogate "
                     "(impact traces stay downstream work, G07 record)"}


def support_force_removed_check(records: list[dict], consts: dict) -> dict:
    """Removing support removes its force: whenever a foot contact channel
    is 0, its force channel is exactly 0.0 (the seam's own law)."""
    violations = []
    for rec in records:
        fc = rec["foot_contacts"]
        ff = rec["foot_forces"]
        for ch in consts["contact_channels"]:
            if fc[ch] == 0.0 and ff[ch] != 0.0:
                violations.append({"tick": rec["tick"], "channel": ch,
                                   "force": ff[ch]})
    return {"violations": violations,
            "law": "foot_forces channel == 0.0 exactly whenever the matching "
                   "foot contact channel is 0"}


def structural_no_pose_write(module_source: str) -> list[str]:
    """Structural arm of the animation-substitution law: the supervisor's
    module contains no scene-state mutation channel (no attribute writes to
    scene state, no restart instrument). The declared restart instrument
    appears ONLY in the declared FB1 tamper hook of the driver, never here.
    (Banned tokens are assembled from fragments so this scanner's own
    source cannot trip it.)"""
    banned = ["." + "v =", "." + "x =",
              ".phase_" + "l =", ".phase_" + "r =",
              ".warm_" + "l =", ".warm_" + "r =",
              ".trip_" + "l =", ".trip_" + "r =",
              ".draws_" + "consumed =",
              "restore_" + "snapshot",
              "forced_re" + "store_snapshot"]
    hits = [b for b in banned if b in module_source]
    return hits
