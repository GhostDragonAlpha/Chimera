"""Tests for core.membrane — run: python core/test_membrane.py

The tests that matter are the CONTAINMENT ones. A membrane that merely LOOKS
sealed is worse than none, because you would trust it.
"""

import sys
import sqlite3
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import core.membrane as mb  # noqa: E402

PASS = TOTAL = 0


def check(name, cond):
    global PASS, TOTAL
    TOTAL += 1
    print(("  ok  " if cond else "FAIL  ") + name)
    PASS += bool(cond)


def main():
    live_world = mb.REPO / mb.WORLD_SUBDIR
    live_dna = live_world / "dna.db"

    before = mb.fingerprint()
    mem = mb.seal("t_selftest")
    try:
        # 1: the seal actually copied the GITIGNORED stores. Without this a
        #    worktree would silently share the live DNA graph.
        mem_dna = mem / mb.WORLD_SUBDIR / "dna.db"
        check("gitignored world stores were copied into the membrane",
              mem_dna.exists() and live_dna.exists()
              and mb._sha256(mem_dna) == mb._sha256(live_dna))

        # 2: a tracked-file write lands INSIDE and nowhere else
        subprocess.run([sys.executable, "-c",
                        "open('MEMBRANE_PROBE.txt','w').write('x')"],
                       cwd=str(mem / mb.CHIMERA_SUBDIR), env=mb.env_for(mem),
                       capture_output=True)
        inside = (mem / mb.CHIMERA_SUBDIR / "MEMBRANE_PROBE.txt").exists()
        outside = (mb.REPO / mb.CHIMERA_SUBDIR / "MEMBRANE_PROBE.txt").exists()
        check("a file written inside exists inside", inside)
        check("...and does NOT exist in the live tree", not outside)
        check("changes() reports it",
              any("MEMBRANE_PROBE" in d for _, d in mb.changes(mem)))

        # 3: THE ONE THAT MATTERS — write to the DNA graph inside the membrane and
        #    prove the LIVE graph is untouched. This is the substrate-contamination
        #    guard; if it ever fails, the membrane is a costume.
        live_dna_before = mb._sha256(live_dna)
        subprocess.run(
            [sys.executable, "-c",
             "import sqlite3; c = sqlite3.connect('docs/world/dna.db'); "
             "c.execute('CREATE TABLE IF NOT EXISTS membrane_probe(x)'); "
             "c.commit(); c.close()"],
            cwd=str(mem / mb.CHIMERA_SUBDIR), env=mb.env_for(mem),
            capture_output=True)
        con = sqlite3.connect(str(mem_dna))
        wrote_inside = con.execute(
            "SELECT count(*) FROM sqlite_master WHERE name='membrane_probe'"
        ).fetchone()[0] == 1
        con.close()
        check("the DNA graph WAS written inside the membrane", wrote_inside)
        check("*** the LIVE DNA graph is byte-identical (no contamination) ***",
              mb._sha256(live_dna) == live_dna_before)
        check("changes() reports the store write",
              any(k == "store" and "dna.db" in d for k, d in mb.changes(mem)))

        # 4: the leak detector agrees nothing escaped
        check("leak detector: membrane HELD", mb._leaks(before, mb.fingerprint()) == [])

        # 5: and it can actually SEE a leak (write to live on purpose)
        probe = live_world / "leak_probe.db"
        probe.write_bytes(b"x")
        try:
            check("leak detector CATCHES a real leak (not just always-clean)",
                  mb._leaks(before, mb.fingerprint()) != [])
        finally:
            probe.unlink(missing_ok=True)

    finally:
        mb.burn(mem)

    check("burn removes the membrane", not mem.exists())
    check("live tree unchanged across the whole test",
          mb._leaks(before, mb.fingerprint()) == [])

    print(f"\n{PASS}/{TOTAL} tests passed")
    return 0 if PASS == TOTAL else 1


if __name__ == "__main__":
    raise SystemExit(main())
