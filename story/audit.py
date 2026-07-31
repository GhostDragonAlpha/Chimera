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
            # NO 0-OR-1 EXEMPTION HERE, and the asymmetry with the literal scan above is deliberate.
            #
            # A bare 0 or 1 in a return dict is usually a flag or a trivially-true count, so the
            # literal check skips it to stay readable. A 0 or 1 as a `parent.get()` DEFAULT is the
            # opposite: it is the most dangerous value there is, because it reads as "nothing" while
            # being physically loaded. `parent.get("S_earth", 1.0)` serves a full Earth's insolation.
            # `parent.get("scale_height_m", 0.0)` makes the thermal wind INFINITE.
            #
            # This exemption made the instrument lie. With it in place the audit reported ZERO
            # get-defaults while SEVEN were live in the tree -- including theTerrain's
            # `parent.get('ice_fraction', 0.0)`, the direct upstream of the one just hardened in
            # aTerrain, where a 0.0 would pin carving_class to "River" forever and move the terrain
            # to 45 degrees latitude. A checker that says "clean" when it is not is worse than no
            # checker, because it is trusted.
            k, d = node.args
            if isinstance(k, ast.Constant) and isinstance(d, ast.Constant) \
                    and isinstance(d.value, (int, float)) and not isinstance(d.value, bool):
                found.append((k.value, d.value, node.lineno, "get-default"))
    return found


# ── CHECK 3 ─────────────────────────────────────────────────────────────────────────────────────
# The form that hid longest, because it looks like good practice: a module-level constant, named in
# capitals, used inside derive(). `rho = RHO_B_NOW * one_plus_z ** 3` reads as clean code. What it
# actually was: a second, independently measured statement of a number the PARENT already carried
# (eta), reachable only by going out to the present day and back. Neither of the first two checks
# sees it -- it is not a literal in the return dict and not a .get() default.
#
# This cannot decide which constants are legitimate; most are. A membrane is allowed to assert
# measured facts -- the crushing strength of rock, the helium fraction. What it lists is the
# ASSUMPTION MANIFEST: everything this membrane states on its own authority rather than inheriting.
# Read it and ask of each one: does my parent already know this?

# Laws of nature and unit conversions -- asserting these is not an assumption about anything.
_UNIVERSAL = {
    "G", "C", "C_LIGHT", "KB", "K_B", "HBAR", "H", "H_PLANCK", "EV", "AMU", "M_E", "M_H", "M_P",
    "M_N", "SIGMA_SB", "SIGMA", "PI", "TWO_PI", "N_A", "R_GAS", "ALPHA", "E_CHARGE",
    "M_SUN", "R_SUN", "L_SUN", "T_SUN", "M_EARTH", "R_EARTH", "AU", "PC", "KPC", "LY", "KM",
    "YEAR", "YEAR_S", "DAY", "SECOND", "T_FREEZE", "T_BOIL", "RHO_WATER",
}


def asserted_constants(folder: Path) -> list:
    """Module-level numeric constants that derive() actually uses, minus the universal ones."""
    py = folder / "physics.py"
    try:
        tree = ast.parse(py.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return []
    consts = {}
    for st in tree.body:
        if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name):
            nm = st.targets[0].id
            if nm.isupper() and nm not in ("FREE", "LENS"):
                try:
                    v = ast.literal_eval(st.value)
                except Exception:
                    continue
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    consts[nm] = v
    used = []
    for fn in tree.body:
        if isinstance(fn, ast.FunctionDef) and fn.name == "derive":
            for node in ast.walk(fn):
                if isinstance(node, ast.Name) and node.id in consts and node.id not in _UNIVERSAL:
                    if node.id not in [u[0] for u in used]:
                        used.append((node.id, consts[node.id], node.lineno))
    return used


# ── CHECK 4 ─────────────────────────────────────────────────────────────────────────────────────
# THE ENGINE HAS NO PARENT, so none of the checks above reach it -- they all walk membranes and read
# derive(). Yet the engine is where the story's numbers become a game, and a number typed there is
# exactly as false as one typed in a membrane. It is also HARDER to catch: there is no `parent` to
# compare against, so "did this come from above?" has no mechanical answer.
#
# Three real defects lived in ChimeraEngine/walker.py behind that gap:
#     a slope gate of 38.0 under a comment reading "the ground's own repose angle" -- and theGround
#         derives 40.03 while aTerrain derives 33.0, so it was neither;
#     an eye height of `0.94 * height`, human anatomy asserted inside a viewer;
#     a clipmap step commented "~half a stride" when half a stride is 0.324 and the value was 0.90.
#
# So this check reports two things it can be CERTAIN of and judges neither.
ENGINE_DIR = ROOT.parent / "ChimeraEngine"
# floats that are structure rather than physics: identities, halves, percentages of nothing
_STRUCTURAL = {0.0, 1.0, -1.0, 0.5, 2.0, 100.0, 1000.0, 360.0, 180.0, 60.0, 24.0}


def engine_files() -> list:
    """Engine modules that actually consume the story -- the ones where a typed number competes with
    a derived one. A file that never opens numbers.json is not in scope; it has nothing to duplicate."""
    out = []
    if not ENGINE_DIR.is_dir():
        return out
    for py in sorted(ENGINE_DIR.glob("*.py")):
        try:
            src = py.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "numbers.json" in src:
            out.append(py)
    return out


def claims_provenance(comment: str, keys: set, names: set) -> str:
    """Does this line's comment NAME something the story derives?

    THIS IS THE HIGH-SIGNAL CHECK, and it is the one that would have caught the slope gate. A bare
    number in engine code is usually fine -- a frame rate, a margin, an instrument setting. A bare
    number whose own comment says "the ground's own repose angle" is CLAIMING to have come from the
    story, and that claim is checkable against the story's published keys.

    It cannot tell whether the claim is TRUE -- 38.0 and 40.03 are both just numbers. What it can do
    is put every number that makes a claim in front of a human, which is a list short enough to read."""
    low = comment.lower()
    if not low:
        return ""
    for k in keys:
        stem = k.rsplit("_", 1)[0] if "_" in k else k
        if len(stem) >= 5 and stem.lower() in low:
            return k
    for n in names:
        if len(n) >= 6 and n.lower() in low:
            return n
    return ""


def engine_literals(py: pathlib.Path) -> list:
    """Every float literal in the file, with the comment on its line.

    THE COMMENT IS PRINTED BESIDE THE NUMBER ON PURPOSE. Nothing can check whether a comment is true --
    that is the one failure in this project with no mechanical tell at all. What a tool CAN do is put
    the claim and the number on the same row, so a human reading the report sees "0.90 # ~half a
    stride" and can go and check that a stride is 0.649 m. That is how the false one was caught."""
    try:
        src = py.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src)
    except (OSError, SyntaxError):
        return []
    lines = src.splitlines()
    found = []
    seen = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant):
            continue
        v = node.value
        if not isinstance(v, float) or isinstance(v, bool):
            continue          # ints are usually counts, indices and shapes -- too noisy to be useful
        if v in _STRUCTURAL or (node.lineno, v) in seen:
            continue
        seen.add((node.lineno, v))
        raw = lines[node.lineno - 1] if node.lineno <= len(lines) else ""
        comment = raw.split("#", 1)[1].strip() if "#" in raw else ""
        found.append((node.lineno, v, comment[:58]))
    return sorted(found)


def engine_reads(files: list) -> set:
    """Every story key the engine names -- `d["k"]`, `d.get("k")`, or a bare "k" string. Deliberately
    generous: a false POSITIVE here (thinking a key is read when it is not) only removes a row from
    the report, and this check exists to raise questions, not to accuse."""
    keys = set()
    for py in files:
        try:
            tree = ast.parse(py.read_text(encoding="utf-8", errors="replace"))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                keys.add(node.value)
    return keys


def story_keys() -> dict:
    """Every key the story publishes, and which membrane publishes it."""
    import json
    out = {}
    for folder in membranes():
        nj = folder / "numbers.json"
        if not nj.is_file():
            continue
        try:
            for k in json.loads(nj.read_text(encoding="utf-8")):
                out.setdefault(k, []).append(folder.name)
        except Exception:
            continue
    return out


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
    ap.add_argument("--assumes", action="store_true")
    ap.add_argument("--engine", action="store_true")
    args = ap.parse_args()
    both = not (args.typed or args.slider or args.assumes or args.engine)
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

    if args.assumes or both:
        print("ASSUMPTION MANIFEST -- module constants derive() uses on its own authority")
        print("  (universal constants and unit conversions excluded; most of what is left is")
        print("   legitimate. Of each one ask: DOES MY PARENT ALREADY KNOW THIS?)")
        for folder in membranes():
            a = asserted_constants(folder)
            if a:
                print(f"\n  {folder.name}")
                for nm, val, line in a:
                    print(f"     line {line:>4}  {nm:<24} = {val!r}")
        print()

    if args.engine or both:
        print("ENGINE AUDIT -- numbers typed where no parent can be checked against")
        print("  The engine has no parent, so --typed cannot reach it. Three real defects lived")
        print("  behind that gap in walker.py. This REPORTS and does not judge: of each literal ask")
        print("  DOES THE STORY ALREADY DERIVE THIS? -- and read the comment beside it, because a")
        print("  false comment is the one failure with no mechanical tell.")
        files = engine_files()
        if not files:
            print("\n  (no engine file reads numbers.json)")
        for py in files:
            lits = engine_literals(py)
            print(f"\n  {py.name}  -- {len(lits)} float literal(s)")
            for line, val, comment in lits:
                tail = f"   # {comment}" if comment else ""
                print(f"     line {line:>4}  {val!r:<22}{tail}")
        # keys the story offers that the engine never names
        offered = story_keys()
        named = engine_reads(files)
        unread = sorted(k for k in offered if k not in named)
        print(f"\n  STORY KEYS THE ENGINE NEVER NAMES -- {len(unread)} of {len(offered)}")
        print("  Not a fault by itself: most of the story is not the engine's business. But an")
        print("  unread key beside a bare literal is the signature of a typed number -- the slope")
        print("  gate was 38.0 while `repose_deg` sat here unread.")
        for k in unread[:40]:
            print(f"     {k:<34} published by {', '.join(offered[k][:3])}")
        if len(unread) > 40:
            print(f"     ... and {len(unread) - 40} more")
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
