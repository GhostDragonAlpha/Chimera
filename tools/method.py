"""method.py -- the ONE stable CLI facade over the Chimera development method.

The workflow docs name scattered scripts (tools/orient.py, tools/verdict.py,
tools/training_gate.py, tools/methodology_gate.py, tools/chain_witness.py, the
port/primitive/action tests, ChimeraEngine/gallery.py ...). When one is renamed or
deleted, every doc that named it rots -- that is how the agent modes died. This facade
exposes STABLE names so the docs reference one thing that will not vanish under them,
and folds in the two diagnostics the method asks for but never made first-class:

  orient        the one live read (engine + verdicts + git)
  prove <term>  run the PROVE gates through the Engine
  check         the CHECK sequence, in its required order
  dyad <term>   the HUMAN half: render + the mandated cheap blind second-read
  findzero      locate which factor of HIERARCHY x PHYSICS x HUMAN is at zero
  work-queue    enumerate the world's to-do (every open term + its next gate)
  gates <term>  print the PROVE gates for a term
  lint          run the broken-pointer linter (tools/doc_lint.py)
  shot <term>   capture ONE screenshot of a term through the engine (/frame) -> .jpg
  view [term]   open the live gallery in a browser (term -> that term's frame)

Run:  python tools/method.py <command> [args]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
sys.path.insert(0, str(ROOT / "tools"))


def _run(args: list[str], cwd: Path = ROOT) -> int:
    return subprocess.run([sys.executable, *args], cwd=cwd).returncode


def _orient(json_mode: bool) -> int:
    return _run(["tools/orient.py"] + (["--json"] if json_mode else []))


def _prove(term: str) -> int:
    from engine_state import Engine
    print(Engine().prove(term, via="api"))
    return 0


def _check() -> int:
    steps = [
        (["tools/chain_witness.py"], "chain_witness"),
        (["tools/port_tests.py"], "port_tests"),
        (["tools/primitive_tests.py"], "primitive_tests"),
        (["tools/action_tests.py"], "action_tests"),
        (["tools/verdict.py", "status"], "verdict status"),
        (["tools/methodology_gate.py"], "methodology_gate"),
        (["tools/orient.py"], "orient"),
    ]
    rc = 0
    for args, name in steps:
        print(f"\n--- CHECK: {name} ---")
        r = _run(args)
        if r != 0:
            rc = r
            print(f"  [{name}] REFUSED (exit {r})")
    if rc == 0:
        print("\nCHECK: PASS -- grow -> witness -> folding -> gate -> timeline -> slider, in order.")
    else:
        print("\nCHECK: a step refused. Fix it before COMMIT; do not skip the close.")
    return rc


def _dyad(term: str, blind: bool) -> int:
    from engine_state import Engine
    print(Engine().render(term))
    if blind:
        print("\n--- DYAD: mandated cheap blind second-read (tools/blind_read.py) ---")
        r = _run(["tools/blind_read.py"])
        if r == 2:
            print("BLIND READ REFUSED: the senses eye is dark. Summon the operator; "
                  "no verdict is written without a reader.")
        elif r == 3:
            print("BLIND READ REFUSED: the prompt leaks the answer -- fix the prompt, not the log.")
        elif r == 0:
            print("BLIND READ: second independent reading recorded (ChimeraEngine/output/blind_read/).")
        else:
            print(f"BLIND READ: exited {r} (see output above).")
        return r if r not in (0,) else 0
    return 0


def _findzero(term: str | None) -> int:
    from engine_state import Engine
    eng = Engine()
    name = term or eng.state.get("current")
    if not name or name not in eng.state["hierarchy"]:
        print("findzero: no such term and no current term set.")
        return 1
    ctx = eng.context(name)
    h = eng.state["hierarchy"]

    def _terminal_of(v):
        return v.get("terminal") if isinstance(v, dict) else v

    def factor_at_zero() -> str:
        if any(h.get(n, {}).get("status") not in ("proven", "decided") for n in ctx[:-1]):
            return "HIERARCHY"
        gates = dict((g, (ok, d)) for g, ok, d in eng.gates(name))
        s2b = gates.get("S2b SATURATION", (True, ""))
        s5 = gates.get("S5 WHY-TERMINAL", (True, ""))
        if not s2b[0] or not gates.get("S0 FRAME", (True, ""))[0] or not s5[0]:
            return "PHYSICS"
        if any(_terminal_of(v) == "THE HUMAN" for v in eng._term(name)["classification"].values()):
            if name not in h or h[name]["status"] != "decided":
                return "HUMAN"
        return "NONE"

    f = factor_at_zero()
    print(f"FIND THE ZERO -- term: {name}")
    print(f"  context (seed -> term): {' > '.join(ctx)}")
    print(f"  gate trail:")
    for g, ok, d in eng.gates(name):
        print(f"    [{'x' if ok else ' '}] {g}: {d}")
    if f == "NONE":
        print("\n  No factor at zero -- the membrane is complete at this resolution.")
    else:
        print(f"\n  >>> {f} is at ZERO. That factor sinks the result; fix it before anything else.")
        print("      (HIERARCHY=0: prove the parent first. PHYSICS=0: derive/measure, "
              "do not hand-tune. HUMAN=0: a taste call is undecided -- ask the operator.)")
    return 0 if f == "NONE" else 1


def _work_queue() -> int:
    from engine_state import Engine
    eng = Engine()
    h = eng.state["hierarchy"]
    open_terms = [n for n, v in h.items() if v.get("status") not in ("proven", "decided")]
    print(f"WORK QUEUE -- {len(open_terms)} open term(s) (the world's to-do, enumerated not authored):")
    for n in open_terms:
        print(f"  - {n}: {eng.next_action(n)}")
    if not open_terms:
        print("  the hierarchy is complete at this resolution.")
    return 0


def _gates(term: str) -> int:
    from engine_state import Engine
    eng = Engine()
    if term not in eng.state["hierarchy"]:
        print(f"gates: no such term '{term}'.")
        return 1
    for g, ok, d in eng.gates(term):
        print(f"  [{'PASS' if ok else 'FAIL'}] {g}: {d}")
    return 0


def _lint(staged: bool, modes: bool, docs: bool) -> int:
    args = ["tools/doc_lint.py"]
    if staged:
        args.append("--staged")
    if modes:
        args.append("--modes")
    if docs:
        args.append("--docs")
    return _run(args)


_GALLERY_PORT = 8765
_GALLERY_URL = f"http://127.0.0.1:{_GALLERY_PORT}"


def _shot(term: str) -> int:
    out = ROOT / "ChimeraEngine" / "output" / "shots"
    out.mkdir(parents=True, exist_ok=True)
    url = f"{_GALLERY_URL}/frame?term={term}"
    try:
        with urllib.request.urlopen(url, timeout=35) as r:
            data = r.read()
    except urllib.error.URLError as e:
        print(f"shot: cannot reach the engine gallery ({e}).")
        print("  start it first:  python ChimeraEngine/gallery.py")
        return 1
    if not data or data[:2] != b"\xff\xd8":
        print("shot: engine returned no JPEG for that term (does the scene exist?).")
        return 1
    path = out / f"{term}.jpg"
    path.write_bytes(data)
    print(f"shot: {path.relative_to(ROOT).as_posix()}  ({len(data)} bytes)")
    print(f"  view:  python tools/method.py view {term}")
    return 0


def _view(term: str | None) -> int:
    url = f"{_GALLERY_URL}/frame?term={term}" if term else f"{_GALLERY_URL}/"
    print(f"view: {url}")
    try:
        webbrowser.open(url)
        print("  (opened in default browser; if headless, paste the URL.)")
    except Exception as e:
        print(f"  browser launch failed ({e}); use the URL above.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="the stable CLI facade over the Chimera method")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("orient", help="the one live read")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("prove", help="run PROVE gates for a term")
    p.add_argument("term")

    sub.add_parser("check", help="the CHECK sequence, in order")

    p = sub.add_parser("dyad", help="render + mandated blind second-read")
    p.add_argument("term")
    p.add_argument("--no-blind", action="store_true", help="skip the blind_read step")

    p = sub.add_parser("findzero", help="which factor of HxPxH is at zero")
    p.add_argument("term", nargs="?")

    sub.add_parser("work-queue", help="enumerate open terms + next gate")
    p = sub.add_parser("gates", help="print PROVE gates for a term")
    p.add_argument("term")

    p = sub.add_parser("lint", help="broken-pointer linter")
    p.add_argument("--staged", action="store_true")
    p.add_argument("--modes", action="store_true")
    p.add_argument("--docs", action="store_true")

    p = sub.add_parser("shot", help="capture one screenshot of a term via the engine")
    p.add_argument("term")
    p = sub.add_parser("view", help="open the live gallery (optionally a term's frame)")
    p.add_argument("term", nargs="?")

    a = ap.parse_args()

    if a.cmd == "orient":
        return _orient(a.json)
    if a.cmd == "prove":
        return _prove(a.term)
    if a.cmd == "check":
        return _check()
    if a.cmd == "dyad":
        return _dyad(a.term, not a.no_blind)
    if a.cmd == "findzero":
        return _findzero(a.term)
    if a.cmd == "work-queue":
        return _work_queue()
    if a.cmd == "gates":
        return _gates(a.term)
    if a.cmd == "lint":
        return _lint(a.staged, a.modes, a.docs)
    if a.cmd == "shot":
        return _shot(a.term)
    if a.cmd == "view":
        return _view(a.term)
    return 1


if __name__ == "__main__":
    sys.exit(main())
