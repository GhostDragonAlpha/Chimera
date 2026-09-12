"""evidence_output.py -- THE EVIDENCE-PRESERVATION LAW FOR TEST RUNNERS. (G01-R3, Task 3)

WHY THIS MODULE EXISTS: the surface battery's runner wrote its raw results to
a FIXED filename (`surface_energy_checks_results.json`) every run. The R2
correction pass discovered this the hard way: running the battery overwrote
the historical G01 results file, and the original had to be restored
byte-exact from the review copies. A runner that can silently destroy its own
evidence history is a hazard, not a harness. ASTRA's R3 assignment makes the
fix a LAW:

  1. By DEFAULT, a run writes its raw results to a UNIQUE, run-stamped path.
  2. A run aimed (via --out) at a path that ALREADY EXISTS refuses with the
     named reason "evidence_path_exists" and exits 2 -- it does NOT write.
  3. Overwriting requires the explicit flag --force-out. Nothing here is
     silent.

This module is imported by both battery runners and by the R3 regression
check (overdamped_descent_checks.py::r3_evidence_preservation). The check
exercises the real surface runner's main() against a pre-existing file and
asserts the refusal AND byte-identity of the preserved file.

Exit-code contract (documented for the publishers):
  0  all checks passed
  1  one or more checks FAILED
  2  evidence-path refusal (nothing written, evidence intact)
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

EVIDENCE_REFUSAL_EXIT = 2
REFUSAL_REASON = "evidence_path_exists"


def default_stamp() -> str:
    """UTC microseconds -- two runs can never share a default filename."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def resolve_evidence_path(default_dir: Path, default_stem: str, argv) -> Path:
    """The one resolution law. argv: the runner's flag list (non-flag args
    are left for the caller's own selection logic).

      (nothing)  -> default_dir / f"{default_stem}_{default_stamp()}.json"
      --out P    -> P, refusing if P exists
      --out P --force-out -> P, overwriting (the only loud path)

    Raises EvidencePathExists (a ValueError) on the refusal case. The
    runner's main() catches it, prints the named refusal, and exits 2.
    """
    argv = list(argv)
    force = "--force-out" in argv
    if "--out" in argv:
        i = argv.index("--out")
        if i + 1 >= len(argv):
            raise ValueError("--out given without a path")
        target = Path(argv[i + 1])
    else:
        target = default_dir / f"{default_stem}_{default_stamp()}.json"

    if target.exists() and not force:
        raise EvidencePathExists(
            f"{REFUSAL_REASON}: {target} already exists ({target.stat().st_size} "
            f"bytes). Evidence is never silently overwritten. Re-run with a "
            f"new --out path, or pass --force-out to overwrite EXPLICITLY.")
    return target


class EvidencePathExists(ValueError):
    """The named refusal. Carries REFUSAL_REASON as `.reason`."""
    reason = REFUSAL_REASON


def strip_flags(argv):
    """Non-flag positional args (the runners' check-name selectors)."""
    out, skip_next = [], False
    for a in argv:
        if skip_next:
            skip_next = False
            continue
        if a in ("--out",):
            skip_next = True
            continue
        if a in ("--force-out", "--json"):
            continue
        if a.startswith("-"):
            continue
        out.append(a)
    return out
