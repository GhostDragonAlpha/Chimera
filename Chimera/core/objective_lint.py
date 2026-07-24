"""objective_lint — enforce the objective-design method so it is never relearned.

THE METHOD is docs/OBJECTIVE_DESIGN.md: seven rules for writing a trainer objective the
optimiser will not exploit, each paid for by a worked failure. A method in a document can be
ignored; this makes the mechanically-checkable rules a gate, the same way core/bind_guard.py
made "bind localhost" a gate.

IT CHECKS WHAT CAN BE CHECKED WITHOUT RUNNING THE DOMAIN, and prints the rest as a checklist
rather than pretending it verified them. Passing means you did not make the four mechanical
mistakes -- not that your physics is right. The lint is a floor, not a ceiling.

    python -m core.objective_lint docs/objectives/arrangement.json
    python -m core.objective_lint --all           # every objective in docs/objectives/
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Quantities that are a BAND in reality and must NOT appear in `maximize` (Rule 5). A band
# quantity maximized drives the winner to reality's extreme, not its typical. Extend this as
# new banded facts are added; an unknown term is not flagged (the lint never guesses physics).
KNOWN_BAND_QUANTITIES = {
    'clustering', 'aspect', 'verticality', 'alignment', 'density', 'coverage',
    'temperature', 'occupancy',
}

# Terms that are legitimate maximize targets because they never saturate (Rule 5's answer).
NEVER_SATURATES = {'robustness', 'band_margin', 'seen_margin', 'margin', 'coverage_margin'}

# Convention: a "band error" term (distance outside a measured band) ends in _off or _error.
def _is_band_error(name: str) -> bool:
    return name.endswith('_off') or name.endswith('_error')


def _weighted_mean_no_floor(name: str, spec: dict) -> bool:
    """R3 heuristic: a margin-style maximize with no hard floor on the same field.

    seen_margin is a weighted mean; without a floor the optimiser zeroes a low-weight
    component. We can only guess statically -- flag a *_margin maximize that has no hard
    constraint anywhere on a *_margin field.
    """
    if 'margin' not in name:
        return False
    for c in spec.get('constraints', []):
        f = c.get('field', '')
        if 'margin' in f and c.get('min') is not None:
            return False           # a floor on a margin field exists (soft counts) -> satisfied
    return True


def lint(spec: dict) -> dict:
    """Return {'errors': [...], 'warnings': [...], 'reminders': [...]}."""
    errors, warnings, reminders = [], [], []

    maximize = spec.get('maximize', []) or []
    minimize = spec.get('minimize', []) or []
    constraints = spec.get('constraints', []) or []

    # R6 -- a pure SATISFICER stops at the first feasible point. But "no maximize" is not the
    # same as "satisficer": a `target` constraint (hit a measured value) or a `minimize` term
    # is a GRADIENT the optimiser follows to a point -- a value-fit, not a search for
    # "good enough". Verified against 52 objectives the first version wrongly refused: they
    # calibrate a parameter to a real number (o2_drain_time = 360) and legitimately have no
    # maximize. R6 fires only when there is NOTHING to optimise: no maximize, no minimize, and
    # only bound-style constraints (at_most/at_least/band) that leave a whole feasible RANGE.
    kinds = {c.get('kind') for c in constraints}
    has_gradient = bool(maximize) or bool(minimize) or 'maximize' in kinds \
        or 'minimize' in kinds or 'target' in kinds
    # A FEASIBILITY objective is legitimately maximize-free. The auto_decomposer generates
    # "does a sub-rung configuration SATISFY the parent's walls in composition" objectives --
    # a satisfaction problem, where the first feasible point IS the answer, not "almost never
    # where you wanted it". Verified against 47 auto-decomposed objectives: their walls are
    # "property must be trainable" / "satisfies parent constraints", pure feasibility. This is
    # the same refinement as the `target` exemption above -- R6 is about OPTIMISATION goals, and
    # a feasibility check is a different, valid category. Signalled by the auto-decomposition
    # provenance or by every constraint carrying a `wall` (i.e. decomposed from a parent wall).
    prov = str(spec.get('_provenance', '')).lower()
    is_feasibility = ('auto-decompos' in prov or 'sub-rung' in prov
                      or (bool(constraints) and all('wall' in c for c in constraints)))
    if not has_gradient and constraints and not is_feasibility:
        errors.append("R6: no maximize, no minimize, no target -- only bounds. This is a "
                      "SATISFICER: it stops at the first point inside the bounds, which is "
                      "almost never where you wanted it. Add a maximize, or a target to fit.")

    # R5 -- a band quantity must not be maximized directly.
    for m in maximize:
        base = m.replace('_worst', '')
        if base in KNOWN_BAND_QUANTITIES and not _is_band_error(base):
            errors.append(f"R5: `{m}` is a BAND quantity in `maximize`. Maximizing it chases "
                          f"reality's extreme, not its typical -- a band wearing a maximize's "
                          f"clothes. Make it a band-error to minimize, and maximize robustness "
                          f"or a margin instead.")

    # R2 -- if you minimize band-errors, you should maximize a margin (else the winner parks
    # on an edge).
    has_band_errors = any(_is_band_error(x) for x in minimize)
    has_margin_max = any(x in NEVER_SATURATES or 'margin' in x for x in maximize)
    if has_band_errors and not has_margin_max:
        warnings.append("R2: this minimizes band-errors but maximizes no MARGIN. The winner "
                        "will park on a band edge (inside reality by zero) and its children "
                        "fall out. Add a *_margin maximize (measured 38% -> 81% child survival).")

    # R3 -- a weighted-mean margin maximize with no hard floor.
    for m in maximize:
        if _weighted_mean_no_floor(m, spec):
            warnings.append(f"R3: `{m}` looks like a weighted mean with no hard floor. The "
                            f"optimiser will zero a low-weight component to buy a high-weight "
                            f"one. Add a hard `min` on the minimum component (e.g. band_margin).")

    # Normalisation reminder if there are multiple band-errors of very different natural scale.
    if sum(1 for x in minimize if _is_band_error(x)) >= 2:
        reminders.append("NORMALISE each band-error by its own band width before summing, or "
                         "the widest-ranging fact dominates ~58x for no physical reason.")

    # The three rules that need the domain to RUN -- never silently skipped.
    reminders.append("R1 PROBE REACHABILITY: before trusting any hard gate, measure what N "
                     "random genomes actually reach. 0/140 reaching a gate = no gradient.")
    reminders.append("R4 HARD-GATE SURVIVAL: if a component must exist in the result, gate its "
                     "survival (min_frac), not just its presence. Partial failure hides in means.")
    reminders.append("R7 SCORE N RESTARTS, KEEP THE WORST: one rollout is a coin toss. Report "
                     "robustness = worst/mean; a fraud is ~0, a real limit cycle ~1.")

    return {'errors': errors, 'warnings': warnings, 'reminders': reminders}


def _load(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e:
        print(f"  [objective-lint] {path.name}: cannot parse ({e})")
        return None


def check_file(path: Path) -> int:
    spec = _load(path)
    if spec is None:
        return 1
    if 'scenario' in spec and 'maximize' not in spec and 'constraints' not in spec:
        return 0                        # a scenario stub, not an executable objective yet
    r = lint(spec)
    if r['errors']:
        print(f"\n  [objective-lint] {path.name}: REFUSED")
        for e in r['errors']:
            print(f"      ERROR  {e}")
        for w in r['warnings']:
            print(f"      warn   {w}")
        return 1
    tag = 'PASS' if not r['warnings'] else 'PASS (with warnings)'
    print(f"  [objective-lint] {path.name}: {tag}")
    for w in r['warnings']:
        print(f"      warn   {w}")
    return 0


def _staged_objectives() -> list:
    """Staged objective JSONs, as absolute paths. For the pre-commit hook."""
    import subprocess
    root = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                          capture_output=True, text=True).stdout.strip()
    out = subprocess.run(['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
                         capture_output=True, text=True).stdout.splitlines()
    keep = []
    for f in out:
        if 'docs/objectives/' in f.replace('\\', '/') and f.endswith('.json') \
                and not f.endswith('.trained.json') and not f.endswith('.systems.json'):
            keep.append(Path(root) / f)
    return keep


def main() -> int:
    args = sys.argv[1:]
    # Module-relative, NOT git-root-relative: git root is the repo parent while objectives
    # live under Chimera/docs/objectives. Resolving from __file__ is location-proof, and it
    # is why --all silently found nothing the first time.
    objectives_dir = Path(__file__).resolve().parents[1] / 'docs/objectives'

    if '--staged' in args:
        # ENFORCEMENT PATH (pre-commit). Only objectives being CHANGED are checked, so the
        # method is enforced on new work without a retroactive migration of the 47 pre-existing
        # satisficers. Editing an old one triggers the block -- the boy-scout nudge to fix it.
        staged = _staged_objectives()
        if not staged:
            return 0
        rc = 0
        for p in staged:
            rc |= check_file(p)
        if rc:
            print("\n  An objective being committed violates the method "
                  "(docs/OBJECTIVE_DESIGN.md). Fix it, or --no-verify if you truly mean it.")
        return rc

    if '--all' in args or not args:
        objs = sorted(objectives_dir.glob('*.json'))
        objs = [p for p in objs if not p.name.endswith('.trained.json')
                and not p.name.endswith('.systems.json')]
        rc = 0
        for p in objs:
            rc |= check_file(p)
        # print the reminders once at the end, not per-file
        print("\n  The three rules the lint CANNOT check statically (run the domain to verify):")
        for rem in lint({}).get('reminders', []):
            print(f"      - {rem}")
        return rc
    rc = 0
    for a in args:
        rc |= check_file(Path(a))
    r = lint(_load(Path(args[0])) or {})
    if r['reminders']:
        print("\n  Cannot be linted statically -- verify by running the domain:")
        for rem in r['reminders']:
            print(f"      - {rem}")
    return rc


if __name__ == '__main__':
    raise SystemExit(main())
