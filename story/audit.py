"""audit.py -- does the chain actually carry, or is somebody typing the answer?

A rule nothing checks is prose. These are the two mechanical checks for the two ways a derivation
quietly stops being one, both of which shipped into this tree and both of which the operator caught
by eye before any tool did.

    python story/audit.py            both checks
    python story/audit.py --typed    only the literal scan (fast, no re-derive)
    python story/audit.py --slider   only the response test

── CHECK 1: TYPED ─────────────────────────────────────────────────────────────────────────────
A number that enters `derive()`'s returned dict as a bare literal did not come from the parent.
Sometimes that is right -- a measured constant, a law's exponent, a boolean. Sometimes it is
`"T_star_surface": 5772.0` under a comment claiming it was inherited, which is another membrane's
field copied by hand because the language had no way to say it. This lists them so a human decides.

── CHECK 2: SLIDER ────────────────────────────────────────────────────────────────────────────
The real test, and the one that convicts. Move a FREE number at the top of a subtree and re-derive
everything below it in memory. Every descendant that depends on that dial MUST move. A descendant
that reports zero changed numbers is either genuinely independent of it -- or is typing a value it
should be inheriting. Before the fix, moving `M_system` changed the snow line and left the planets'
sunlight at exactly 5772.0 K, forever: a physically impossible pair that nothing was watching for.
"""
from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Literals that are legitimately typed: laws, measured constants, flags. Anything whose key says
# it is a ratio/exponent/flag, plus 0 and 1, which are almost always structural.
_FINE = ("_frac", "_ratio", "_exponent", "_share", "flag", "_is_", "is_", "has_", "n_", "_count")


def _load(py: Path):
    spec = importlib.util.spec_from_file_location(f"m_{abs(hash(py))}", py)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def membranes(folder: Path = None, out: list = None) -> list:
    """Every membrane folder, parents before children."""
    out = [] if out is None else out
    folder = folder or ROOT
    if (folder / "physics.py").exists():
        out.append(folder)
    for c in sorted(d for d in folder.iterdir() if d.is_dir() and not d.name.startswith((".", "_"))):
        if (c / "story.md").exists() or (c / "physics.py").exists():
            membranes(c, out)
    return out


# ── CHECK 1 ─────────────────────────────────────────────────────────────────────────────────────
def typed_literals(folder: Path) -> list:
    """Keys in derive()'s return dict whose value is a bare number."""
    py = folder / "physics.py"
    try:
        tree = ast.parse(py.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return []
    found = []
    for fn in tree.body:
        if not (isinstance(fn, ast.FunctionDef) and fn.name == "derive"):
            continue
        for node in ast.walk(fn):
            if not isinstance(node, ast.Return) or not isinstance(node.value, ast.Dict):
                continue
            for k, v in zip(node.value.keys, node.value.values):
                if not isinstance(k, ast.Constant) or not isinstance(k.value, str):
                    continue
                key = k.value
                if isinstance(v, ast.Constant) and isinstance(v.value, (int, float)) \
                        and not isinstance(v.value, bool):
                    if v.value in (0, 1) or any(s in key for s in _FINE):
                        continue
                    found.append((key, v.value, v.lineno, "literal"))
        # THE DISGUISED FORM, and it is the one that hides longest: `parent.get("k", 86400.0)`.
        # It reads as defensive programming. What it actually does is serve a typed number the
        # moment the parent stops carrying the real one -- silently, forever, with no error. That
        # is how theTerrain ran a 24-hour day at every setting of the rotation dial. If the parent
        # MUST supply it, write `parent["k"]` and let it fail loudly.
        for node in ast.walk(fn):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "get" and len(node.args) == 2):
                continue
            src = node.func.value
            if not (isinstance(src, ast.Name) and src.id == "parent"):
                continue
            k, d = node.args
            if isinstance(k, ast.Constant) and isinstance(d, ast.Constant) \
                    and isinstance(d.value, (int, float)) and not isinstance(d.value, bool) \
                    and d.value not in (0, 1):
                found.append((k.value, d.value, node.lineno, "get-default"))
    return found


# ── CHECK 2 ─────────────────────────────────────────────────────────────────────────────────────
def _free_of(folder: Path) -> dict:
    try:
        tree = ast.parse((folder / "physics.py").read_text(encoding="utf-8", errors="replace"))
        for st in tree.body:
            if isinstance(st, ast.Assign) and getattr(st.targets[0], "id", "") == "FREE":
                return ast.literal_eval(st.value)
    except Exception:
        pass
    return {}


def _rederive(folder: Path, parent: dict, free_override: dict) -> dict | None:
    """Re-derive this membrane in memory, with its own trained.json unless overridden."""
    tj = folder / "trained.json"
    free = json.loads(tj.read_text()) if tj.exists() else {}
    free.update(free_override.get(folder.name, {}))
    try:
        return _load(folder / "physics.py").derive(parent, free)
    except Exception:
        return None


def _walk(folder: Path, parent: dict | None, free_override: dict, acc: dict) -> None:
    nums = _rederive(folder, parent, free_override) if parent is not None or folder == ROOT else None
    if nums is None:
        try:
            nums = _load(folder / "physics.py").derive(parent, {})
        except Exception:
            return
    acc[folder.name] = nums
    for c in sorted(d for d in folder.iterdir() if d.is_dir() and not d.name.startswith((".", "_"))):
        if (c / "physics.py").exists():
            _walk(c, nums, free_override, acc)


def _changed(a: dict, b: dict) -> int:
    n = 0
    for k, va in a.items():
        vb = b.get(k)
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)) and not isinstance(va, bool):
            if abs(va - vb) > 1e-12 * max(1.0, abs(va)):
                n += 1
        elif va != vb:
            n += 1
    return n


def slider_test(seed: Path) -> list:
    """For every FREE dial in the tree, nudge it and report which descendants moved."""
    rows = []
    for folder in membranes():
        free = _free_of(folder)
        if not free:
            continue
        for name, spec in free.items():
            local = spec.get("local")
            base, pert = {}, {}
            _walk(seed, None, base, base_acc := {})
            lo, hi = float(spec.get("lo", 0.5)), float(spec.get("hi", 2.0))
            cur = float(spec.get("default", 0.5 * (lo + hi)))
            nudged = cur * 1.35 if cur * 1.35 <= hi else max(lo, cur * 0.7)
            _walk(seed, None, {folder.name: {name: nudged}}, pert_acc := {})
            # only descendants of `folder` are in scope
            chain, node = [], folder
            desc = [m for m in membranes() if folder in m.parents or m == folder]
            for m in desc:
                a, b = base_acc.get(m.name), pert_acc.get(m.name)
                if a is None or b is None:
                    continue
                rows.append((folder.name, name, m.name, _changed(a, b), len(a), local))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--typed", action="store_true")
    ap.add_argument("--slider", action="store_true")
    args = ap.parse_args()
    both = not (args.typed or args.slider)
    seed = ROOT / "theZero"
    bad = 0

    if args.typed or both:
        print("NUMBERS THAT DID NOT COME FROM THE PARENT")
        print("  literal      a bare number in derive()'s return -- fine for a law or a")
        print("               measurement, NOT fine for a copy of a sibling's field")
        print("  get-default  parent.get(k, N) -- a typed number wearing defensive clothing.")
        print("               It serves N silently the moment the parent stops carrying k.")
        any_found = False
        for folder in membranes():
            lits = typed_literals(folder)
            if lits:
                any_found = True
                print(f"\n  {folder.name}")
                for key, val, line, kind in lits:
                    tag = "literal    " if kind == "literal" else "get-default"
                    print(f"     line {line:>4}  {tag}  {key:<26} = {val!r}")
        if not any_found:
            print("  none.")
        print()

    if args.slider or both:
        print("SLIDER TEST -- move a FREE dial; every descendant that depends on it MUST move")
        rows = slider_test(seed)
        if not rows:
            print("  no free dials found.")
        cur = None
        for owner, dial, child, moved, total, local in rows:
            if (owner, dial) != cur:
                cur = (owner, dial)
                # A DECLARED-LOCAL DIAL IS NOT A FAILURE -- it is a written claim that this number
                # has no business downstream, with the reason attached. A silent non-propagation is
                # indistinguishable from a bug; a stated one can be argued with.
                note = f"   [declared local: {local}]" if local else ""
                print(f"\n  {owner}.{dial}{note}")
            mark = ""
            if not moved and not local:
                mark = "<-- DID NOT MOVE"
                if child != owner:
                    bad += 1
            print(f"     {child:<22} {moved:>3}/{total:<3} numbers changed  {mark}")
        print()
        if bad:
            print(f"  {bad} membrane(s) did not respond to a dial above them.")
            print("  Either they are genuinely independent of it, or they are typing a value")
            print("  they should be inheriting. Check the literals listed above. If a dial really")
            print("  is local, say so in its FREE entry -- add  \"local\": \"<the reason>\"  -- so the")
            print("  claim is written down and reviewable instead of being a silent absence.")
        else:
            print("  every descendant responded to every dial above it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
