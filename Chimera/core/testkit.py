"""testkit — the universal test sandbox: no test may touch a live store.

Born from surprise_e3944cb57b2994f0 (a decomposer test sandboxed the board
and the batteries but not graphify — four junk Decomposition nodes landed in
the LIVE DNA graph; the History Book's search caught the leak in seconds).
The lesson: sandboxing one store is not sandboxing. This module redirects
EVERY persistent seam in one call, so the failure class is impossible rather
than merely guarded against.

Usage (top of any core test, before exercising code):

    import tempfile
    from pathlib import Path
    from core.testkit import sandbox
    tmp = Path(tempfile.mkdtemp(prefix="mytest_"))
    graph = sandbox(tmp)          # -> the in-memory graph dict, inspectable

Everything after that call reads/writes only under `tmp` (board, batteries,
rep ledger, envelope, decomposition templates, Book index) and against an
in-memory DNA graph. The typed record_* helpers stay REAL — they exercise
their validation logic and land in the returned dict, so tests can assert on
recorded nodes without ever risking the live graph.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def sandbox(tmp: Path) -> dict:
    """Redirect every persistent store into `tmp`. Returns the in-memory DNA
    graph dict that load/save now operate on. Call ONCE, before the code
    under test constructs anything."""
    tmp = Path(tmp)
    tmp.mkdir(parents=True, exist_ok=True)

    # --- DNA graph: in-memory seam. record_* helpers keep their real logic;
    # load/save just stop touching disk/SQLite.
    import core.graphify_interface as gi
    graph = {"nodes": [], "edges": []}
    gi.load_dna_graph = lambda: json.loads(json.dumps(graph))
    def _save(g):
        graph["nodes"] = list(g.get("nodes", []))
        graph["edges"] = list(g.get("edges", []))
    gi.save_dna_graph = _save

    # --- task board (already env-aware — use its own seam)
    os.environ["CHIMERA_TASK_BOARD_STATE"] = str(tmp / "board.json")
    os.environ["CHIMERA_TASK_BOARD_LOCK"] = str(tmp / "board.lock")
    try:
        import core.task_board as tb
        tb.STATE_PATH = tmp / "board.json"
        tb.LOCK_PATH = tmp / "board.lock"
        tb.BOARD_MD = tmp / "TASK_BOARD.md"
    except Exception:
        pass

    # --- rep engine: batteries + ledger + pie manifest
    try:
        import core.rep_engine as re_mod
        re_mod.BATTERY_DIR = tmp / "rep_batteries"
        re_mod.PIE_MANIFEST = re_mod.BATTERY_DIR / "pie_manifest.json"
        re_mod.DB_PATH = tmp / "world" / "reps.db"
        re_mod.CLAUDE_MD = tmp / "CLAUDE_ABSENT.md"
    except Exception:
        pass

    # --- the container
    try:
        import core.malcolm as m
        m.ENVELOPE_PATH = tmp / "envelope.json"
        m.SOURCE_TREE = tmp / "gen"
        m.TELEMETRY_LAST = tmp / "world" / "telemetry_last.json"
    except Exception:
        pass

    # --- decomposer templates
    try:
        import core.decomposer as dc
        dc.TEMPLATES_PATH = tmp / "decomposition_templates.json"
    except Exception:
        pass

    # --- the Book
    try:
        import core.history_book as hb
        hb.BOOK_MD = tmp / "HISTORY_BOOK.md"
        hb.INDEX_DB = tmp / "world" / "history.db"
        hb.REPS_DB = tmp / "world" / "reps.db"
        hb.DRIFT_JSON = tmp / "rep_batteries" / "dsl_drift.json"
        hb.CLAUDE_MD = tmp / "CLAUDE_ABSENT.md"
    except Exception:
        pass

    return graph
