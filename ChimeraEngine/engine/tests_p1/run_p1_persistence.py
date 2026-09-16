#!/usr/bin/env python3
"""P1 persistence (worker 5): build + run the seal-state save/restore tests.

Mirrors the tests_p1 shim pattern:
    cmake -S ChimeraEngine/engine/tests_p1 -B .tmp/p1_persistence_build
    cmake --build .tmp/p1_persistence_build --config Release
    run test_p1_persistence, results -> .tmp/p1_persistence_results.txt

Exit code propagates the test binary's exit code (nonzero on any FAIL).
"""

import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))  # worktree root
SRC_DIR = os.path.relpath(HERE, ROOT)
BUILD = os.path.join(ROOT, ".tmp", "p1_persistence_build")
RESULTS = os.path.join(ROOT, ".tmp", "p1_persistence_results.txt")
EXE = "test_p1_persistence"


def find_exe():
    candidates = [os.path.join(BUILD, "Release", EXE + ".exe"),
                  os.path.join(BUILD, "Debug", EXE + ".exe"),
                  os.path.join(BUILD, EXE + ".exe")]
    hits = [c for c in candidates if os.path.isfile(c)]
    if hits:
        return hits[0]
    hits = glob.glob(os.path.join(BUILD, "**", EXE + ".exe"), recursive=True)
    return hits[0] if hits else None


def run(cmd, **kw):
    print("+ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd, **kw).returncode


def main():
    rc = run(["cmake", "-S", SRC_DIR, "-B", os.path.relpath(BUILD, ROOT)],
             cwd=ROOT)
    if rc != 0:
        print("CONFIG FAILED (rc=%d)" % rc)
        return rc
    rc = run(["cmake", "--build", os.path.relpath(BUILD, ROOT),
              "--config", "Release"], cwd=ROOT)
    if rc != 0:
        print("BUILD FAILED (rc=%d)" % rc)
        return rc
    exe = find_exe()
    if not exe:
        print("EXE NOT FOUND after build")
        return 2
    print("results -> " + RESULTS, flush=True)
    rc = subprocess.run([exe, RESULTS]).returncode
    print("%s exited rc=%d" % (EXE, rc))
    return rc


if __name__ == "__main__":
    sys.exit(main())
