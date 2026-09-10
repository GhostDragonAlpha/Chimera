"""Run the existing controller contract suites against ReviewHandoffControl.

The source suite modules bind ``Control`` at import time, so this isolated runner
rebinds those fixture globals to the exact subclass used by the proposed service.
It never opens the live registry; every suite creates a TemporaryDirectory.
"""
from __future__ import annotations

import importlib
import importlib.util
import os
from pathlib import Path
import sys
import unittest


CANDIDATE = Path(__file__).resolve().parent
BASE = Path(os.environ["FLEET_CONTROL_ROOT"]).resolve()
sys.path[:0] = [str(CANDIDATE), str(BASE)]

from review_handoff import ReviewHandoffControl  # noqa: E402


MODULES = (
    "test_control",
    "test_bootstrap",
    "test_resources",
    "test_resource_lifecycle",
)


def main() -> int:
    loaded = []
    for name in MODULES:
        if importlib.util.find_spec(name) is None:
            continue
        module = importlib.import_module(name)
        if hasattr(module, "Control"):
            module.Control = ReviewHandoffControl
        loaded.append(module)

    # ResourceLifecycleTests borrows methods whose globals live in test_resources.
    fixtures = sys.modules.get("test_resources")
    if fixtures is not None:
        fixtures.Control = ReviewHandoffControl

    suite = unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromModule(module) for module in loaded
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
