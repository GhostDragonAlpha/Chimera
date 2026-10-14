"""Pad-split channel extraction from a wave-4x instrumented walk trace (V2 obs).

THE TYPE-A HALF OF THE TYPE-B CONVERGENCE (receipt_wave47.json's bank; lane
agent/obs-split-channels-20260921, prereg frozen at 97fd15fb BEFORE this build).
The machinery computes the individual hind-pad gaps inside gap_of(e,k) --
gh (heel endpoint), gm (MP endpoint) -- and returns only min(gh, gm); every
instrument print erases the pair the same way (the wave-45 [dvfl] band view
reads gap_of TWICE at the two endpoints, which are pair-based, so g1 == g2
identically -- the band's collapsed pair). The wave-46 calibration proved the
erased DOF is the deciding one:

    split_abs(t) = 2 * (pad_y(t) - gmin(t))

with pad_y = the MEAN pad point y (the [dvfa] arch instrument: 0.5*(heel_y +
mp_y)) and gmin = the pair min (the [dvfl] band instrument). The identity
holds exactly because pad radius = plane_model_y_ = 0.004 at every GaitWalker
site (shift V{0,0,0}): gh + gm = 2*pad_y, so

    g_lo = gmin,   g_hi = 2*pad_y - g_lo,   split_abs = g_hi - g_lo.

This module turns the preserved trace outputs into V2 observation records
(pair ordering 'lohi' -- the endpoint identity is NOT in the record, so the
endpoint-signed channels are mask-declared unavailable by the schema, never
invented) and projects them through observation_schema.project_trace. The
class census (the mine_wave47.py conventions VERBATIM: LAST walk run, first
sample per (t,leg), era span [fire, ct], sref = 2*(pad_y(f) - gmin(f+1)),
lever = split_abs - sref) is computed FROM the projected channels, so the
wave-47 LIFT/STALL reproduction is a property of the channels themselves.

Read-only over the trace. Zero engine bytes. Rule 0: the falsifiers
F-CHANNELS-DISTINCT / F-CHANNELS-SEPARATE / F-CHANNELS-INERT are declared in
the prereg and measured by the lane's mine, not here.
"""
from __future__ import annotations

import hashlib
import re
from collections import defaultdict

import numpy as np

import observation_schema as oschema

WAVE47_TRACE_SHA256 = "c6f9b6c00a1d549a4bc709724d2f62f8f28b37823696de4689e1950651c37481"
KTOUCH = 1e-5   # the machinery's own contact-vs-not quantum (gait_controller.hpp:36)
PLANE_Y = 0.004  # the wave-46 calibration: plane_model_y_ = pad radius = 0.004

_LEGS = ("hl", "hr")  # hind legs; observation indices 4 (hl), 5 (hr)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_wave4x_trace(trace_path: str, expect_sha256: str | None = None) -> dict:
    """The mine_wave47.py parse convention VERBATIM: the LAST walk run
    (WALK REFUSED delimited), [dvfa]/[dvfl] first-sample-per-(t,leg),
    [hindstep] fire/td events deduped by full line text."""
    if expect_sha256 is not None:
        got = sha256_file(trace_path)
        if got != expect_sha256:
            raise ValueError(f"trace sha mismatch: got {got}, expected {expect_sha256}")
    lines = open(trace_path, encoding="utf-8", errors="replace").read().splitlines()
    idx = [i for i, l in enumerate(lines) if l.startswith("WALK REFUSED")]
    run = lines[idx[-2] + 1:idx[-1]]
    mref = re.match(r"WALK REFUSED tick (\d+): (\S+)", lines[idx[-1]])
    refusal = (int(mref.group(1)), mref.group(2))

    dvfa: dict[int, dict[int, tuple]] = defaultdict(dict)
    dvfl: dict[int, dict[int, dict]] = defaultdict(dict)
    fires, tds = [], []
    seen_ev = set()
    for l in run:
        m = re.match(r"\[dvfa\] t=(\d+) leg=(\d) br=(\w) held=(\d) sg=(\S+) c=(\S+) cmd_y=(\S+) pad_y=(\S+) plant_y=(\S+)", l)
        if m:
            t, leg = int(m.group(1)), int(m.group(2))
            if leg not in dvfa[t]:
                dvfa[t][leg] = (m.group(3), int(m.group(4)), float(m.group(5)), float(m.group(6)),
                                float(m.group(7)), float(m.group(8)), float(m.group(9)))
            continue
        m = re.match(r"\[dvfl\] t=(\d+) leg=(\d) g1=(\S+) g2=(\S+) edge=(\S+) hd=(\d) ht=(\d+) tm=(\S+) clr=(-?\d+) oth=(\d) dl=(\d+)", l)
        if m:
            t, leg = int(m.group(1)), int(m.group(2))
            rec = dict(g1=float(m.group(3)), g2=float(m.group(4)), edge=float(m.group(5)),
                       hd=int(m.group(6)), ht=int(m.group(7)), tm=float(m.group(8)),
                       clr=int(m.group(9)), oth=int(m.group(10)), dl=int(m.group(11)))
            if leg not in dvfl[t]:
                dvfl[t][leg] = rec
            continue
        if l.startswith("[hindstep]"):
            if l in seen_ev:
                continue
            seen_ev.add(l)
            m = re.match(r"\[hindstep\] fire leg=(\d) tick=(\d+) phi=\S+ class=(\S+) from=\((\S+),(\S+)\) to=\((\S+),(\S+)\) xoff=(\S+) v=(\S+) qerr=(\S+) ap=\S+ br=\S+ dl=(\d+)", l)
            if m:
                fires.append((int(m.group(2)), int(m.group(1)), m.group(3),
                              float(m.group(5)), float(m.group(10)), int(m.group(11))))
                continue
            m = re.match(r"\[hindstep\] td leg=(\d) tick=(\d+)", l)
            if m:
                tds.append((int(m.group(2)), int(m.group(1))))
                continue
    return dict(refusal=refusal, dvfa=dvfa, dvfl=dvfl, fires=fires, tds=tds,
                n_run_lines=len(run))


def reconstruct_pairs(parsed: dict) -> dict:
    """The per-(t,leg) reconstructed pair wherever BOTH instruments delivered:
    g_lo = gmin (the [dvfl] read), g_hi = 2*pad_y - g_lo (the wave-46 identity),
    split_abs = g_hi - g_lo (= 2*(pad_y - gmin), the calibrated quantity)."""
    dvfa, dvfl = parsed["dvfa"], parsed["dvfl"]
    out: dict[int, dict[int, dict]] = defaultdict(dict)
    n_band_lines = 0
    for t, legs in dvfl.items():
        for leg, b in legs.items():
            n_band_lines += 1
            a = dvfa.get(t, {}).get(leg)
            if a is None:
                continue
            pad_y = a[5]                    # the mean pad point y ([dvfa])
            gmin = min(b["g1"], b["g2"])    # the collapsed pair (g1 == g2)
            g_lo = gmin
            g_hi = 2.0 * pad_y - g_lo
            out[t][leg] = dict(pad_y=pad_y, gmin=gmin, g_lo=g_lo, g_hi=g_hi,
                               split_abs=g_hi - g_lo, hd=b["hd"])
    return dict(pairs=out, n_band_lines=n_band_lines,
                n_reconstructed=sum(len(v) for v in out.values()))


def build_records(recon: dict) -> list[dict]:
    """One V2 observation record per tick carrying any reconstructed pair.
    Ordering 'lohi' (the endpoint identity is not in the preserved outputs):
    the schema masks the endpoint-signed channels; split_abs stays live."""
    pairs = recon["pairs"]
    recs = []
    for t in sorted(pairs):
        gaps, ordering = {}, {}
        for leg_idx, key in enumerate(_LEGS):
            p = pairs[t].get(leg_idx)
            if p is not None:
                gaps[key] = [p["g_lo"], p["g_hi"]]
                ordering[key] = "lohi"
        if not gaps:
            continue
        recs.append(dict(tick=t, pad_gaps=gaps, pad_pair_ordering=ordering,
                         available_groups=["pad_split"]))
    return recs


def project_records(records: list[dict]) -> list[tuple[np.ndarray, np.ndarray]]:
    """The V2 harness over the records: identity normalization (mean 0, std 1),
    caller-owned prev_state per the schema's delta contract (the key present
    iff the previous tick delivered that channel)."""
    zero = np.zeros(oschema.OBS_DIM, dtype=np.float32)
    one = np.ones(oschema.OBS_DIM, dtype=np.float32)
    out = []
    prev: dict = {}
    for rec in records:
        obs, mask = oschema.project_trace(rec, zero, one, prev)
        out.append((obs, mask))
        # maintain prev: the delivered pad channel values, popped when the
        # channel went unavailable (a delivery gap masks the next delta)
        gaps = rec.get("pad_gaps") or {}
        ordering = rec.get("pad_pair_ordering") or {}
        for leg in _LEGS:
            pair = gaps.get(leg)
            if pair is None:
                for base in ("pad_g_heel_", "pad_g_mp_", "pad_split_abs_", "pad_split_"):
                    prev.pop(base + leg, None)
                continue
            signed = ordering.get(leg, "heel_mp") == "heel_mp"
            a, b = float(pair[0]), float(pair[1])
            vals = {"pad_g_heel_" + leg: a, "pad_g_mp_" + leg: b,
                    "pad_split_abs_" + leg: abs(b - a)}
            if signed:
                vals["pad_split_" + leg] = b - a
            for k, v in vals.items():
                prev[k] = v
    return out


def channel_split_abs_series(records: list[dict],
                             projections: list[tuple[np.ndarray, np.ndarray]]) -> dict:
    """Per (t,leg): the PROJECTED pad_split_abs value + mask (the round-trip
    source of truth for the census)."""
    i_abs = {leg: oschema.FIELD_NAMES.index(f"pad_split_abs_{leg}") for leg in _LEGS}
    ser: dict[int, dict[int, float]] = defaultdict(dict)
    masks: dict[int, dict[int, float]] = defaultdict(dict)
    for rec, (obs, mask) in zip(records, projections):
        t = rec["tick"]
        for leg_idx, key in enumerate(_LEGS):
            if rec["pad_gaps"].get(key) is not None:
                ser[t][leg_idx] = float(obs[i_abs[key]])
                masks[t][leg_idx] = float(mask[i_abs[key]])
    return dict(series=ser, masks=masks)


def era_census(parsed: dict, chan: dict) -> list[dict]:
    """The mine_wave47.py census VERBATIM, computed from the PROJECTED
    pad_split_abs channel series: per era lever = split_abs - sref with
    sref = 2*(pad_y(f) - gmin(f+1)); era class by the wave-41..46 DEL
    convention; never-crossed via the band's own hd flag."""
    dvfa, dvfl = parsed["dvfa"], parsed["dvfl"]
    series = chan["series"]
    rows = []
    for (ft, leg, cls, fy, qerr, dl) in parsed["fires"]:
        comp = next(((t, l) for (t, l) in parsed["tds"] if l == leg and t >= ft), None)
        ct = comp[0] if comp else max(t for t in dvfa if leg in dvfa[t] and t > ft)
        a0 = dvfa.get(ft, {}).get(leg)
        if a0 is None:
            continue
        fy_pad = a0[5]
        b0 = dvfl.get(ft + 1, {}).get(leg)
        g0 = min(b0["g1"], b0["g2"]) if b0 else float("nan")
        sref = 2.0 * (fy_pad - g0)
        ser = []   # (t, split_abs, lever) -- lever FROM the projected channel
        for t in range(ft + 1, ct + 1):
            v = series.get(t, {}).get(leg)
            if v is None:
                continue
            ser.append((t, v, v - sref))
        if not ser:
            continue
        maxlev = max(s[2] for s in ser)
        span = ct - ft
        incs = [(ser[0][0], ser[0][2])]
        for i in range(1, len(ser)):
            incs.append((ser[i][0], ser[i][2] - ser[i - 1][2]))
        maxinc = max(v for _, v in incs)
        cmd_peak = -1e9
        del_peak = -1e9
        for t in range(ft, ct + 1):
            a = dvfa.get(t, {}).get(leg)
            if a is None:
                continue
            cmd_y, pad_y = a[4], a[5]
            cmd_peak = max(cmd_peak, (cmd_y - fy) * 1e3)
            del_peak = max(del_peak, (pad_y - fy) * 1e3)
        era_class = "STALL" if del_peak < 1.0 else "LIFT"
        bser = [dvfl[t][leg] for t in range(ft + 1, ct + 1) if leg in dvfl.get(t, {})]
        cross = next((ft + 1 + i for i, b in enumerate(bser) if b["hd"] == 0), None)
        rows.append(dict(ft=ft, ct=ct, leg=leg, era_class=era_class, cls=cls,
                         span=span, n=len(ser), maxlev=maxlev, maxinc=maxinc,
                         rate_span=maxlev / span, cross=cross, ser=ser, incs=incs,
                         del_peak=del_peak))
    return rows
