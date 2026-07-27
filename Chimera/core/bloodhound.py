"""bloodhound — when an atom flips green->red, name the commit that killed it.

Headless atoms evaluate in milliseconds — fast enough to binary-search git
history. On a flip, the hound bisects the commit range between the last green
run and the first red run INSIDE AN ISOLATED WORKTREE (the live tree is never
touched), evaluating the atom's own probe at each midpoint, and records the
guilty commit as a SurpriseMoment with full provenance. The H-31-style
archaeology that used to cost agents hours becomes a nightly reflex.

Scope guards: headless probes only; <= MAX_HUNTS flips per tend; worktree is
always removed, even on failure.

CLI: python -m core.bloodhound hunt [--max 2] [--dry-run]
Runs nightly inside dream_loop, after the rep tend.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # Chimera/
REPO = ROOT.parent                                   # git root
MAX_HUNTS = 2


def _git(args: list, cwd: Path = None) -> str:
    # cwd resolves at CALL time (module REPO may be redirected by tests);
    # a definition-time default here once sent a test bisect at the LIVE repo.
    return subprocess.run(["git", "-C", str(cwd or REPO)] + args,
                          capture_output=True, text=True, timeout=120).stdout.strip()


def fresh_flips(db_path: Path = None) -> list:
    """Atoms whose LATEST verdict is red but whose previous verdict was green:
    [{atom_id, feature, red_ts, green_ts}]."""
    from core.rep_engine import DB_PATH
    con = sqlite3.connect(db_path or DB_PATH)
    rows = con.execute(
        "SELECT feature, atom_id, ts, passed FROM reps ORDER BY atom_id, ts").fetchall()
    con.close()
    flips, last = [], {}
    for feature, atom_id, ts, passed in rows:
        prev = last.get(atom_id)
        last[atom_id] = (feature, ts, passed)
        if prev and prev[2] == 1 and passed == 0:
            flips.append({"atom_id": atom_id, "feature": feature,
                          "green_ts": prev[1], "red_ts": ts})
    # keep only atoms STILL red (their final row is a red flip)
    return [f for f in flips
            if last[f["atom_id"]][2] == 0 and last[f["atom_id"]][1] == f["red_ts"]]


def _load_atom(feature: str, atom_id: str) -> dict:
    from core.rep_engine import load_battery, all_battery_features, _safe_name
    for feat_file in all_battery_features():
        if _safe_name(feature) == feat_file:
            for a in load_battery(feat_file):
                if a["id"] == atom_id:
                    return a
    return {}


def _probe_at(atom: dict, tree_root: Path):
    """Evaluate the atom's own probe against an arbitrary tree — no rep_engine
    module surgery; probes take an explicit cache."""
    from core.rep_engine import PROBES, _FileCache
    probe = atom.get("probe") or {}
    fn = PROBES.get(probe.get("type"))
    if fn is None or atom.get("kind") != "headless":
        return None
    ok, _ev = fn({k: v for k, v in probe.items() if k != "type"},
                 _FileCache(tree_root / "Chimera"))
    return ok


def bisect_flip(flip: dict, dry_run: bool = False) -> dict:
    """Binary-search commits between the green and red run times; return
    {guilty_sha, subject, tested} or {error}."""
    import datetime as _dt
    # explicit +00:00 offsets — git parses BARE iso stamps as LOCAL time,
    # which silently shifts the window off the commits (caught by test_wave)
    green_iso = _dt.datetime.fromtimestamp(flip["green_ts"], _dt.timezone.utc).isoformat()
    red_iso = _dt.datetime.fromtimestamp(flip["red_ts"], _dt.timezone.utc).isoformat()
    shas = _git(["rev-list", "--reverse",
                 f"--since={green_iso}", f"--until={red_iso}", "HEAD"]).split()
    if not shas:
        return {"error": "no commits in the flip window (local-only change?)"}
    atom = _load_atom(flip["feature"], flip["atom_id"])
    if not atom:
        return {"error": f"atom {flip['atom_id']} not found in batteries"}
    if dry_run:
        return {"guilty_sha": "(dry-run)", "subject": f"{len(shas)} candidates",
                "tested": 0}
    wt = Path(tempfile.mkdtemp(prefix="bloodhound_")) / "wt"
    tested = 0
    try:
        _git(["worktree", "add", "--detach", str(wt), shas[-1]])
        lo, hi = 0, len(shas) - 1          # invariant: lo-1 green, hi red-side
        first_bad = shas[-1]
        while lo <= hi:
            mid = (lo + hi) // 2
            _git(["checkout", "--detach", "-q", shas[mid]], cwd=wt)
            ok = _probe_at(atom, wt)
            tested += 1
            if ok is None:
                return {"error": "probe not headless-evaluable in worktree"}
            if ok:
                lo = mid + 1
            else:
                first_bad = shas[mid]
                hi = mid - 1
        subject = _git(["log", "-1", "--format=%h %s", first_bad])
        return {"guilty_sha": first_bad, "subject": subject, "tested": tested}
    finally:
        subprocess.run(["git", "-C", str(REPO), "worktree", "remove", "--force",
                        str(wt)], capture_output=True, timeout=60)


def hunt(max_hunts: int = MAX_HUNTS, dry_run: bool = False) -> list:
    results = []
    for flip in fresh_flips()[:max_hunts]:
        verdict = bisect_flip(flip, dry_run=dry_run)
        results.append({**flip, **verdict})
        if "guilty_sha" in verdict:
            print(f"[bloodhound] {flip['feature']} atom {flip['atom_id']}: "
                  f"GUILTY {verdict['subject'][:90]} ({verdict['tested']} probes)")
            if not dry_run:
                try:
                    from core.graphify_interface import record_surprise
                    record_surprise(
                        f"rep atom {flip['atom_id']} ({flip['feature']}) flipped green->red",
                        f"bloodhound bisect names the commit: {verdict['subject']}",
                        expectation="the atom's constraint would keep holding",
                        lesson_hint="guilty commit identified mechanically; "
                                    "fix or revert with provenance",
                        source="engine")
                except Exception:
                    pass
        else:
            print(f"[bloodhound] {flip['atom_id']}: {verdict.get('error')}")
    if not results:
        print("[bloodhound] no fresh green->red flips — nothing to hunt")
    return results


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("hunt")
    h.add_argument("--max", type=int, default=MAX_HUNTS)
    h.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    hunt(a.max, a.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
