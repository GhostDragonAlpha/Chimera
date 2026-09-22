"""Fixture builder for the janitor postcondition test (lane agent/workflow-rules-conversion-20260922).

Builds two git repos under E:/ChimeraWork:
  conv-janitor-test   -- quiet working tree, but .git/FRESH_MARKER has mtime=NOW
                         (the pre-fix janitor would SPARE it as 'active'; post-fix it must not)
  conv-janitor-test2  -- same, plus held.txt that a second process holds open
                         (deletion must FAIL honestly, never log 'deleted')
All other mtimes are set 6h old so the 3h quiet window passes.
"""
import os
import subprocess as sp
import time

ROOT = r"E:\ChimeraWork"
OLD = time.time() - 6 * 3600


def build(name, with_held):
    path = os.path.join(ROOT, name)
    if os.path.exists(path):
        raise SystemExit(f"exists: {path}")
    os.makedirs(os.path.join(path, "work"))
    with open(os.path.join(path, "work", "lane.py"), "w") as f:
        f.write("print('fixture lane')\n")
    g = lambda *a: sp.run(("git",) + a, cwd=path, check=True, capture_output=True, text=True)
    g("init", "-b", "conv-test-branch")
    g("add", ".")
    g("-c", "user.email=fixture@lane", "-c", "user.name=fixture", "commit", "-m", "fixture")
    # age everything (including .git internals) to 6h old
    for dirpath, dirnames, filenames in os.walk(path):
        for n in dirnames + filenames:
            p = os.path.join(dirpath, n)
            try:
                os.utime(p, (OLD, OLD))
            except OSError:
                pass
    # the .git-internal churn that mimics a fetch/gc/commit
    fresh = os.path.join(path, ".git", "FRESH_MARKER")
    with open(fresh, "w") as f:
        f.write("now\n")
    # FRESH_MARKER keeps mtime=NOW (default)
    if with_held:
        with open(os.path.join(path, "held.txt"), "w") as f:
            f.write("held open by a live process\n")
        os.utime(os.path.join(path, "held.txt"), (OLD, OLD))
    st = sp.run(("git", "status", "--porcelain"), cwd=path, capture_output=True, text=True)
    print(f"{name}: built, status={st.stdout.strip()!r} (empty=clean)")
    return path


build("conv-janitor-test", False)
build("conv-janitor-test2", True)
print("fixtures ready")
