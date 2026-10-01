"""falsifiers.py -- the receipt's rule_0 block, read ONLY (F-DIAGNOSIS-LEAK).

The packet's receipt reader consumes rule_0 {statement, prediction, falsifier}
and the pass flag.  It NEVER touches the receipt's measurements sections or any
mine_* artifact -- those are the human mine's outputs and are admitted only
AFTER generation, as the scoring key (evaluate_heldout.py, a separate tool).

The preregistered letters carry their own numeric bounds in their own text
(e.g. f37_rung: "refusal > 300 banks the rung", "the ledger trend bounded by
32.861605 J"); the evaluator parses those bounds and evaluates them against the
run's stdout census.  Letters whose bounds cannot be parsed are reported
UNKNOWN -- never guessed.
"""
from __future__ import annotations

import json
import re


class Receipt:
    """The leak-guarded view of a wave receipt."""

    def __init__(self, path: str):
        with open(path, encoding="utf-8") as f:
            full = json.load(f)
        self.path = path
        self.lane = full.get("lane")
        self.base = full.get("base")
        self.pass_flag = full.get("pass")
        self.rule_0 = full.get("rule_0", {})
        self._banned_touched = False  # hard assertion surface for the leak audit

    # -- the ONLY fields the packet may see ---------------------------------
    def falsifier_letters(self) -> "dict[str, str]":
        f = self.rule_0.get("falsifier", {})
        if isinstance(f, dict):
            return dict(f)
        return {"f": str(f)}


_R_RUNG_GT = re.compile(r"refusal\s*>\s*=?\s*(\d+)")
_R_LEDGER_BOUND = re.compile(r"ledger[^.\n]{0,80}?bounded by\s*([0-9]+\.[0-9]+)", re.IGNORECASE)
_R_LEDGER_LE = re.compile(r"ledger[^.\n]{0,80}?<=\s*([0-9]+\.[0-9]+)")
_R_LEDGER_MAX = re.compile(r"ledger[^.\n]{0,80}?max[^\n]{0,20}?([0-9]+\.[0-9]+)", re.IGNORECASE)


def evaluate_letters(letters: dict, census: dict) -> list:
    """Evaluate EVERY numeric clause in each preregistered letter against the
    census (one letter can carry several -- e.g. f37_rung carries both the rung
    bar and the ledger bound).

    rung clause:   the letter banks the rung iff refusal > N  -> FIRED iff refused_tick <= N
    ledger clause: the trend is bounded by N J (<=)           -> FIRED iff worst_ledger_J >  N
    The letter's verdict is FIRED iff any of its clauses fired; declaration
    order is preserved (dict order = the receipt's freeze order).
    """
    out = []
    for name, text in letters.items():
        clauses = []
        m = _R_RUNG_GT.search(text)
        if m and census.get("refused_tick") is not None:
            bound = int(m.group(1))
            clauses.append(dict(kind="rung", bound=bound, measured=census["refused_tick"],
                                clause=m.group(0),
                                verdict="FIRED" if census["refused_tick"] <= bound else "PASSED"))
        led = None
        for pat in (_R_LEDGER_BOUND, _R_LEDGER_LE, _R_LEDGER_MAX):
            led = pat.search(text)
            if led:
                break
        if led and census.get("worst_ledger_J") is not None:
            bound = float(led.group(1))
            clauses.append(dict(kind="ledger", bound=bound, measured=census["worst_ledger_J"],
                                clause=led.group(0),
                                verdict="FIRED" if census["worst_ledger_J"] > bound else "PASSED"))
        if clauses:
            entry = dict(letter=name,
                         verdict="FIRED" if any(c["verdict"] == "FIRED" for c in clauses) else "PASSED",
                         clauses=clauses,
                         # convenience view of the decisive clause (fired first, else the first)
                         kind=(next((c["kind"] for c in clauses if c["verdict"] == "FIRED"), clauses[0]["kind"])),
                         bound=(next((c["bound"] for c in clauses if c["verdict"] == "FIRED"), clauses[0]["bound"])),
                         measured=(next((c["measured"] for c in clauses if c["verdict"] == "FIRED"), clauses[0]["measured"])),
                         clause=(next((c["clause"] for c in clauses if c["verdict"] == "FIRED"), clauses[0]["clause"])))
        else:
            entry = dict(letter=name, verdict="UNKNOWN", kind=None, clause=None, bound=None,
                         measured=None, clauses=[],
                         clause_note="(no numeric clause this reader can evaluate; reported UNKNOWN)")
        out.append(entry)
    return out


def first_fired(evals: list):
    for e in evals:
        if e["verdict"] == "FIRED":
            return e
    return None
