"""parallel.py — run independent episodes across PROCESSES.

The witnesses are dominated by sweeps: 8 randomised starts, 7 slope angles, 6 co-contraction
levels, 3 push magnitudes. Every one of those is an independent rollout, so they are embarrassingly
parallel -- and this box has 32 cores that were sitting idle while one of them ground through them
in sequence.

PROCESSES, not threads. The inner loop is small-matrix numpy plus Python-level recursion, which
holds the GIL almost the whole time; threads would buy nothing. Separate interpreters do.

The worker function and its arguments must be picklable, so workers are module-level functions
taking plain data -- not closures. That constraint is why the witnesses define their episodes as
top-level `_case(...)` functions rather than nested ones.
"""
from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor


def workers(cap: int = 16) -> int:
    """Leave a couple of cores for the OS (and for whatever else the operator is running)."""
    return max(1, min(cap, (os.cpu_count() or 2) - 2))


def pmap(fn, items, cap: int = 16, chunk: int = 1):
    """map(fn, items) across processes, order preserved.

    Falls back to a serial map if the pool cannot start (frozen interpreter, restricted sandbox,
    a non-picklable argument) -- a witness that refuses to run is worse than a slow one, and the
    RESULTS are identical either way, so the fallback cannot quietly change an answer.
    """
    items = list(items)
    n = workers(cap)
    if n <= 1 or len(items) <= 1:
        return [fn(x) for x in items]
    try:
        with ProcessPoolExecutor(max_workers=n) as ex:
            return list(ex.map(fn, items, chunksize=chunk))
    except Exception as e:                       # pragma: no cover - environment dependent
        print(f"      [parallel] pool unavailable ({type(e).__name__}), running serially")
        return [fn(x) for x in items]
