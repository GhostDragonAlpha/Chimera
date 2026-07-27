"""membrane — run any command inside a sealed copy of the studio.

THE PRIMITIVE (2026-07-14, the human's insight). A boundary is what makes a cause
ATTRIBUTABLE.

  In biology, the vesicle is what lets a replicator KEEP what it makes. Without an
  inside and an outside, whatever a proto-cell manufactures diffuses into the ocean
  and benefits its competitors as much as itself — no individual, therefore nothing
  for selection to act ON. Compartmentalisation is not a wall added to life; it is
  the thing that makes chemistry into a cell.

  In engineering, the same boundary is what lets you attribute an outcome to a
  CHANGE rather than to the world. Without an inside and an outside there is no
  isolated variable, therefore nothing to falsify.

Same operation, two substrates. A membrane is the precondition for attribution —
and attribution is what this entire studio is built on (result_grader, the Frame
Audit, the COIN's heads/tails, the witness gate, elimination nodes).

The studio was already full of unnamed membranes: spiral_forks ("forks never touch
live state"), --dry-run on the compactor and distiller, worktree isolation for
agents, agent_tunnel footprints, editor_scheduler locks, PIE, malcolm's envelope.
Seven implementations of one idea, none sharing a mechanism, none named.

And where one was MISSING, we got burned. On 2026-07-14 `core.solver --no-execute`
was run as an infrastructure probe with an INVENTED blocker. `--no-execute` stops
solver EXECUTING its plan — not WRITING it. It prepended a fabricated fix-plan to
task_progress.md, the auto-flush committed and pushed it, and the `pi` agent
harness read it and began working a blocker that never existed. Ten minutes. No
malice, no bug, no broken rule — just no boundary.

    python -m core.membrane run -- python -m core.solver --blocker "X"

WHAT IT DOES
------------
1. SEAL   a git worktree (detached, at your CURRENT tree including uncommitted
          changes) PLUS a copy of docs/world/ — which is gitignored, so a worktree
          alone would leave the DNA graph, rep ledger, history and CAPCOM stores
          SHARED WITH LIVE. That is the difference between a membrane and a
          costume. Every path in the studio derives from __file__, so running
          inside the worktree redirects everything automatically; the CHIMERA_*
          env overrides are belt-and-braces on top.
2. RUN    your command, cwd inside the membrane.
3. DIFF   what the command actually wrote (tracked files + the world stores).
4. PROVE  re-fingerprint the LIVE side. If ANYTHING outside the membrane moved,
          say so LOUDLY. A membrane you cannot verify is a membrane you must not
          trust — so this one measures its own containment instead of asserting it.
5. DECIDE `apply` it back, or `burn` it. Default is neither: it just tells you.

NOT ISOLATED: the network. LM Studio calls, MCP, and `git push` still reach the
world. This is a cell wall, not a Faraday cage. The leak check will catch a moved
ref, but it cannot un-send a packet.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]              # E:\PythonChimera
CHIMERA_SUBDIR = "Chimera"
WORLD_SUBDIR = f"{CHIMERA_SUBDIR}/docs/world"           # gitignored -> must be copied

MEMBRANE_DIR = Path(os.environ.get(
    "CHIMERA_MEMBRANE_DIR", REPO.parent / "chimera_membranes"))

MANIFEST = ".membrane.json"


# --- plumbing ---------------------------------------------------------------

def _git(args: list, cwd: Path = REPO, check: bool = True) -> str:
    p = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if check and p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: "
                           f"{(p.stderr or p.stdout).strip()[:300]}")
    return (p.stdout or "").strip()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _world_hashes(root: Path) -> dict:
    """Hash every gitignored world store under `root`."""
    w = root / WORLD_SUBDIR
    if not w.is_dir():
        return {}
    return {p.name: _sha256(p) for p in sorted(w.glob("*.db")) if p.is_file()}


def fingerprint(root: Path = REPO) -> dict:
    """Everything that must NOT change while a membrane runs.

    Tracked state via git (HEAD, refs, dirty set) + the gitignored world stores.
    Comparing this before and after is what PROVES containment rather than
    claiming it."""
    return {
        "head": _git(["rev-parse", "HEAD"], root),
        "master": _git(["rev-parse", "master"], root, check=False),
        "status": _git(["status", "--porcelain"], root),
        "world": _world_hashes(root),
    }


def _leaks(before: dict, after: dict) -> list:
    """What escaped. Empty list = the membrane held."""
    out = []
    for k in ("head", "master", "status"):
        if before.get(k) != after.get(k):
            out.append(f"live {k} changed")
    for name in sorted(set(before["world"]) | set(after["world"])):
        if before["world"].get(name) != after["world"].get(name):
            out.append(f"live docs/world/{name} was WRITTEN")
    return out


# --- the membrane ------------------------------------------------------------

def seal(name: str = None) -> Path:
    """Create a sealed copy of the studio. Returns its path.

    Uses `git stash create` so the membrane reflects your CURRENT working tree,
    uncommitted changes and all — a probe of a clean HEAD would be a probe of a
    studio you are not actually running."""
    name = name or f"m{int(time.time())}"
    mem = MEMBRANE_DIR / name
    if mem.exists():
        raise RuntimeError(f"membrane {name} already exists at {mem}")
    MEMBRANE_DIR.mkdir(parents=True, exist_ok=True)

    # the working tree as it stands right now (dangling commit; the stash list is
    # untouched). Empty output = tree is clean -> just use HEAD.
    snapshot = _git(["stash", "create"]) or _git(["rev-parse", "HEAD"])

    _git(["worktree", "add", "--detach", str(mem), snapshot])

    # THE PART A WORKTREE ALONE GETS WRONG: docs/world/ is gitignored, so it does
    # not come across. Without this copy the membrane would happily write to the
    # LIVE DNA graph while looking perfectly sealed.
    live_world = REPO / WORLD_SUBDIR
    mem_world = mem / WORLD_SUBDIR
    if live_world.is_dir():
        mem_world.mkdir(parents=True, exist_ok=True)
        for p in live_world.iterdir():
            if p.is_file():
                shutil.copy2(p, mem_world / p.name)

    (mem / MANIFEST).write_text(json.dumps({
        "name": name,
        "sealed_from": snapshot,
        "seeded_world": _world_hashes(mem),   # to diff against later
        "repo": str(REPO),
    }, indent=2))
    return mem


def env_for(mem: Path) -> dict:
    """Environment that pins every studio path INSIDE the membrane.

    Mostly redundant — the studio derives its roots from __file__, which is already
    inside the worktree — but a CHIMERA_* var exported in the live shell would
    otherwise punch straight through the wall. Belt and braces."""
    env = os.environ.copy()
    root = mem / CHIMERA_SUBDIR
    env.update({
        "CHIMERA_MEMBRANE": mem.name,
        "CHIMERA_ROOT": str(mem),
        "CHIMERA_DNA_DB": str(root / "docs" / "world" / "dna.db"),
        "CHIMERA_DNA_SNAPSHOT": str(root / "docs" / "chimera_dna_graph.json"),
        "CHIMERA_WORLD_DB": str(root / "docs" / "world" / "world.db"),
        "CHIMERA_CAPCOM_DB": str(root / "docs" / "world" / "capcom.db"),
        "CHIMERA_SPIRAL_DIR": str(root / "docs" / "spiral"),
        "CHIMERA_GAUNTLET_DIR": str(root / "docs" / "gauntlet"),
    })
    return env


def changes(mem: Path) -> list:
    """What the command wrote INSIDE the membrane. (label, detail) pairs."""
    out = [("file", line.strip())
           for line in _git(["status", "--porcelain"], mem).splitlines()
           if line.strip()]
    seeded = json.loads((mem / MANIFEST).read_text()).get("seeded_world", {})
    now = _world_hashes(mem)
    for name in sorted(set(seeded) | set(now)):
        if seeded.get(name) != now.get(name):
            out.append(("store", f"docs/world/{name} written"))
    return out


def burn(mem: Path) -> None:
    """Remove the membrane. Nothing it did survives."""
    _git(["worktree", "remove", "--force", str(mem)], check=False)
    if mem.exists():
        shutil.rmtree(mem, ignore_errors=True)


def apply_back(mem: Path) -> tuple:
    """Bring the membrane's changed FILES into the live tree. Returns
    (refused_stores, copied_paths).

    COPIES rather than patches. `git apply` was the obvious choice and it was
    wrong: piping a patch through text round-trips it through CRLF translation
    and re-encoding, so a docstring with an em-dash in it comes back as
    "trailing whitespace" errors and the apply dies. A membrane is a WORKBENCH,
    not just a probe — the work has to come out intact, and a byte-for-byte copy
    of the files git says changed is both simpler and exact. It also handles new
    files and deletions, which `git diff HEAD` alone silently drops.

    Deliberately refuses the world stores: clobbering a live DNA graph with a
    membrane's copy is exactly the substrate contamination this module exists to
    prevent. Copy those by hand if you truly mean it."""
    stores = [d for k, d in changes(mem) if k == "store"]
    _git(["add", "-A", "--", ".", f":!{MANIFEST}"], mem)
    names = _git(["diff", "--name-only", "HEAD", "--", ".", f":!{MANIFEST}"],
                 mem).splitlines()

    copied = []
    for rel in (n.strip() for n in names):
        if not rel:
            continue
        src, dst = mem / rel, REPO / rel
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(rel)
        elif dst.exists():
            dst.unlink()                       # deleted inside the membrane
            copied.append(f"{rel} (deleted)")
    return stores, copied


def run(cmd: list, name: str = None, then: str = "keep") -> int:
    """Seal, run `cmd` inside, diff it, PROVE nothing leaked, report."""
    before = fingerprint()
    mem = seal(name)
    print(f"[membrane] sealed {mem.name} -> {mem}")
    print(f"[membrane] $ {' '.join(cmd)}\n")

    t0 = time.time()
    p = subprocess.run(cmd, cwd=str(mem / CHIMERA_SUBDIR), env=env_for(mem))
    took = time.time() - t0

    after = fingerprint()
    leaked = _leaks(before, after)
    wrote = changes(mem)

    print(f"\n[membrane] exit {p.returncode} in {took:.1f}s")
    print(f"\n  WROTE (inside the membrane):")
    if wrote:
        for kind, detail in wrote:
            print(f"    {kind:<6} {detail}")
    else:
        print("    (nothing — the command is genuinely read-only)")

    print(f"\n  CONTAINMENT (the live studio, measured before and after):")
    if leaked:
        print("    *** BREACHED — the membrane did NOT hold ***")
        for l in leaked:
            print(f"    !!! {l}")
        print("    (network, absolute paths, or a concurrent writer such as the")
        print("     auto-flush job. Investigate before trusting this result.)")
    else:
        print("    HELD — nothing outside the membrane changed.")

    if then == "burn":
        burn(mem)
        print(f"\n[membrane] burned. Nothing survives.")
    else:
        print(f"\n  next:  python -m core.membrane apply {mem.name}"
              f"   (bring tracked changes into the live tree)")
        print(f"         python -m core.membrane burn  {mem.name}"
              f"   (throw it all away)")
    return 1 if leaked else p.returncode


# --- CLI ---------------------------------------------------------------------

def _main() -> int:
    import argparse
    ap = argparse.ArgumentParser(
        prog="python -m core.membrane",
        description="Run any command in a sealed copy of the studio, and PROVE "
                    "it touched nothing outside.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="seal, run a command inside, diff, prove")
    r.add_argument("--name", default=None)
    r.add_argument("--burn", action="store_true",
                   help="destroy the membrane afterwards (a pure probe)")
    r.add_argument("argv", nargs=argparse.REMAINDER,
                   help="-- then the command to run")

    sub.add_parser("list", help="live membranes")
    d = sub.add_parser("diff", help="what a membrane wrote"); d.add_argument("name")
    b = sub.add_parser("burn", help="destroy a membrane"); b.add_argument("name")
    a = sub.add_parser("apply", help="bring a membrane's tracked changes into live")
    a.add_argument("name")

    args = ap.parse_args()

    if args.cmd == "run":
        cmd = [a for a in args.argv if a != "--"]
        if not cmd:
            print("nothing to run. usage: membrane run -- python -m core.solver ...")
            return 2
        return run(cmd, args.name, then="burn" if args.burn else "keep")

    if args.cmd == "list":
        if not MEMBRANE_DIR.is_dir() or not any(MEMBRANE_DIR.iterdir()):
            print("(no membranes)")
            return 0
        for m in sorted(MEMBRANE_DIR.iterdir()):
            if (m / MANIFEST).exists():
                n = len(changes(m))
                print(f"  {m.name:<16} {n} change(s)   {m}")
        return 0

    mem = MEMBRANE_DIR / args.name
    if not (mem / MANIFEST).exists():
        print(f"no such membrane: {args.name}")
        return 2

    if args.cmd == "diff":
        for kind, detail in changes(mem) or [("", "(nothing)")]:
            print(f"  {kind:<6} {detail}")
        return 0

    if args.cmd == "burn":
        burn(mem)
        print(f"burned {args.name}")
        return 0

    if args.cmd == "apply":
        refused, copied = apply_back(mem)
        print(f"applied {args.name} -> live tree ({len(copied)} file(s))")
        for c in copied:
            print(f"  + {c}")
        for s in refused:
            print(f"  REFUSED (copy by hand if you mean it): {s}")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(_main())
