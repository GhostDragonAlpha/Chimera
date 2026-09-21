"""trace_io.py -- parse a GAIT_EVENT_TRACE run (stderr) + its stdout census.

Read-only.  Mirrors the declared first-walk extraction every wave mine uses
(run counter increments on "[dv] t=0"; only the first walk run is kept).
"""
from __future__ import annotations

import hashlib
import json
import re


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


_HINDSTEP_PATTERNS = (
    ("fire", re.compile(r"\[hindstep\] fire leg=(\d) tick=(\d+) phi=([\d.e+-]+) class=(\w+)")),
    ("td", re.compile(r"\[hindstep\] td leg=(\d) tick=(\d+)")),
    ("waivefire", re.compile(r"\[hindstep\] waivefire leg=(\d) tick=(\d+) dl=(\d+)")),
    ("unloadgate", re.compile(r"\[hindstep\] unloadgate leg=(\d) tick=(\d+) dl=(\d+) class=(\w+)")),
    ("standhold", re.compile(r"\[hindstep\] standhold leg=(\d) tick=(\d+)")),
    ("holdreturn", re.compile(r"\[hindstep\] holdreturn leg=(\d) tick=(\d+) t=(\d+) pairmin=([\d.e+-]+)")),
    ("hindgate", re.compile(r"\[hindstep\] hindgate leg=(\d) tick=(\d+)")),
    ("guardblock", re.compile(r"\[hindstep\] guardblock leg=(\d) tick=(\d+)")),
)

_DVP = re.compile(r"\[dvp\] t=(\d+) k=(\d) gap=([\d.e+-]+) rxn=([\d.e+-]+) frc=([\d.e+-]+) slip=([\d.e+-]+)")
_DVQ = re.compile(r"\[dvq\] t=(\d+) k=(\d+) tau=([\d.e+-]+) cap=([\d.e+-]+)")
_DVJ = re.compile(r"\[dvj\] t=(\d+) k=(\d) ang=([\d.e+-]+) tgt=([\d.e+-]+) spd=([\d.e+-]+)")
_DV = re.compile(r"\[dv\] t=(\d+) ")
_LEDGER10 = re.compile(r"\[ledger10\] tick (\d+) (\{.*\})")
_LEDGER = re.compile(
    r"\[ledger\] tick (\d+) bal=([\d.e+-]+) stor=([\d.e+-]+) \| KE=([\d.e+-]+) grav=([\d.e+-]+) "
    r"work=([\d.e+-]+) damp=([\d.e+-]+) imp=([\d.e+-]+) fric=([\d.e+-]+) brake=([\d.e+-]+) ext=([\d.e+-]+)")
_LEDGER_FIRST = re.compile(r"\[ledger\] first breach tick (\d+):")
_REFUSAL = re.compile(r"\[refusal\] tick=(\d+) refusal=(\S+)")
_FAMILIES = ("[dv]", "[dvp]", "[dvj]", "[dvq]", "[dvf]", "[hindstep]", "[dvfire]",
             "[ledger]", "[ledger10]", "[pt]", "[trunk]", "[fore]", "[body]", "[refusal]")


class Trace:
    """A parsed first-walk GAIT_EVENT_TRACE run."""

    def __init__(self, path: str):
        self.path = path
        self.sha256 = sha256_file(path)
        self.first_walk_line = None  # raw line at which the first walk run begins
        self.runs_seen = 0
        self.fires = []
        self.tds = []            # (leg, tick)
        self.waivefires = []     # (leg, tick, dl)
        self.unloadgates = []    # (leg, tick, dl, cls)
        self.standholds = []     # (leg, tick)
        self.guardblocks = []    # (leg, tick)
        self.holdreturns = []    # (leg, tick, t, pairmin)
        self.gaps = {}           # tick -> [g0..g3] (hind pads, first walk)
        self.rxn = {}            # tick -> [r0..r3]
        self.frc = {}            # tick -> [f0..f3]
        self.dvq = {}            # (tick,k) -> (tau, cap)
        self.dvj = {}            # (tick,k) -> (ang, tgt, spd)
        self.ledger10 = {}       # tick -> full energy dict
        self.ledger = []         # per-tick adaptive breach rows
        self.ledger_first_breach = None
        self.refusals = []       # (tick, refusal)
        self.events_by_tick = {}  # tick -> [(family, line)]
        self._ingest()

    def _keep(self, run: int) -> bool:
        return run <= 1

    def _ingest(self) -> None:
        run = 0  # mirrors the wave mines exactly: keep while run <= 1
        with open(self.path, encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("[dv] "):
                    m = _DV.match(line)
                    if m and int(m.group(1)) == 0:
                        run += 1
                        self.runs_seen = run
                        if self.first_walk_line is None:
                            self.first_walk_line = line
                if not self._keep(run):
                    continue
                if line.startswith("[hindstep]"):
                    for kind, pat in _HINDSTEP_PATTERNS:
                        m = pat.match(line)
                        if not m:
                            continue
                        g = m.groups()
                        if kind == "fire":
                            self.fires.append((int(g[0]), int(g[1]), float(g[2]), g[3], line.rstrip()))
                        elif kind == "td":
                            self.tds.append((int(g[0]), int(g[1])))
                        elif kind == "waivefire":
                            self.waivefires.append((int(g[0]), int(g[1]), int(g[2]), line.rstrip()))
                        elif kind == "unloadgate":
                            self.unloadgates.append((int(g[0]), int(g[1]), int(g[2]), g[3]))
                        elif kind == "standhold":
                            self.standholds.append((int(g[0]), int(g[1])))
                        elif kind == "guardblock":
                            self.guardblocks.append((int(g[0]), int(g[1])))
                        elif kind == "holdreturn":
                            self.holdreturns.append((int(g[0]), int(g[1]), int(g[2]), float(g[3])))
                        self.events_by_tick.setdefault(int(g[1]), []).append(("[hindstep]", line.rstrip()))
                        break
                    continue
                m = _DVP.match(line)
                if m:
                    t, k = int(m.group(1)), int(m.group(2))
                    self.gaps.setdefault(t, [None] * 8)[k] = float(m.group(3))
                    self.rxn.setdefault(t, [None] * 8)[k] = float(m.group(4))
                    self.frc.setdefault(t, [None] * 8)[k] = float(m.group(5))
                    self._tick_line(t, "[dvp]", line.rstrip())
                    continue
                m = _DVQ.match(line)
                if m:
                    self.dvq[(int(m.group(1)), int(m.group(2)))] = (float(m.group(3)), float(m.group(4)))
                    self._tick_line(int(m.group(1)), "[dvq]", line.rstrip())
                    continue
                m = _DVJ.match(line)
                if m:
                    self.dvj[(int(m.group(1)), int(m.group(2)))] = (float(m.group(3)), float(m.group(4)), float(m.group(5)))
                    self._tick_line(int(m.group(1)), "[dvj]", line.rstrip())
                    continue
                m = _LEDGER10.match(line)
                if m:
                    self.ledger10[int(m.group(1))] = json.loads(m.group(2))
                    self._tick_line(int(m.group(1)), "[ledger10]", line.rstrip())
                    continue
                m = _LEDGER.match(line)
                if m:
                    g = [float(x) for x in m.groups()]
                    self.ledger.append(dict(tick=int(g[0]), bal=g[1], stor=g[2], KE=g[3], grav=g[4],
                                            work=g[5], damp=g[6], imp=g[7], fric=g[8], brake=g[9], ext=g[10]))
                    self._tick_line(int(g[0]), "[ledger]", line.rstrip())
                    continue
                if _LEDGER_FIRST.match(line):
                    self.ledger_first_breach = int(_LEDGER_FIRST.match(line).group(1))
                    continue
                m = _REFUSAL.match(line)
                if m:
                    self.refusals.append((int(m.group(1)), m.group(2)))
                    self._tick_line(int(m.group(1)), "[refusal]", line.rstrip())
                    continue

    def _tick_line(self, t: int, family: str, line: str) -> None:
        self.events_by_tick.setdefault(t, []).append((family, line))

    # -- convenience -------------------------------------------------------
    def max_tick(self) -> int:
        return max(self.events_by_tick) if self.events_by_tick else 0

    def pairmin(self, t: int, leg: int):
        row = self.gaps.get(t)
        if row is None or row[2 * leg] is None or row[2 * leg + 1] is None:
            return None
        return min(row[2 * leg], row[2 * leg + 1])

    def carrier_rxn(self, t: int, leg: int):
        """Max vertical reaction across leg's two hind pads at tick t."""
        row = self.rxn.get(t)
        if row is None or row[2 * leg] is None or row[2 * leg + 1] is None:
            return None
        return max(row[2 * leg], row[2 * leg + 1])


def parse_stdout_census(path: str) -> dict:
    """The stdout census: the JSON head + the measured F-G lines."""
    out = dict(path=path, sha256=sha256_file(path), json_head={}, measured=[],
               refused_tick=None, refusal=None, worst_ledger_J=None, reds=[], checks=None)
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    # the stdout is a JSON document with a trailing plain section; take the
    # leading balanced object if present, else scan line-wise.
    head = {}
    try:
        dec = json.JSONDecoder()
        obj, end = dec.raw_decode(text.lstrip())
        if isinstance(obj, dict):
            head = obj
    except ValueError:
        start = text.find("{")
        if start >= 0:
            try:
                head = json.JSONDecoder().raw_decode(text[start:])[0]
            except ValueError:
                head = {}
    out["json_head"] = {k: head.get(k) for k in ("checks", "cycle_ticks", "bw_N") if k in head}
    out["checks"] = head.get("checks")
    for key in ("measured", "red_falsifiers", "reds"):
        v = head.get(key)
        if isinstance(v, list):
            out["measured"].extend(str(x) for x in v)
    for line in out["measured"]:
        if "WALK refused_tick=" in line:
            m = re.search(r"refused_tick=(\d+) worst_ledger_J=([\d.e+-]+)", line)
            if m:
                out["refused_tick"] = int(m.group(1))
                out["worst_ledger_J"] = float(m.group(2))
            m2 = re.search(r"refusal=(\S+)", line)
            if m2:
                out["refusal"] = m2.group(1)
        m = re.match(r"RED falsifier: (\S+)", line)
        if m:
            out["reds"].append(m.group(1))
    out["n_reds"] = len(out["reds"])
    return out
