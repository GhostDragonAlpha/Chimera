"""Shared harness for the F2 graph-regression reproduction tests.

RULES OF THIS HARNESS (enforced by construction):
  * TEST-ONLY: nothing here ever writes inside tools/creature_graph/data/
    (the canonical store path STORE_PATH is never used; save() is always
    called with an explicit tmp path).
  * Inputs are IMMUTABLE: fixtures live in tests/fixtures/ (committed); every
    mutation happens on a copy in a per-test temp directory.
  * The machinery under test is the graph's OWN code: schema / store /
    build_graph / graphify_projection / engine_live / gaps / queries, imported
    from tools/creature_graph exactly as they ship at the base commit.

Verdict convention (documented in REPRODUCTION_REPORT.md):
  REPRODUCED  -- observed behavior differs from the architectural contract
                 (expected-honest); the defect is live.
  REFUTED     -- observed behavior matches the contract; the defect does NOT
                 reproduce (an exoneration is a measured finding).
Each run() returns a verdict dict; each module also exposes a pytest-style
test_* wrapper asserting verdict == "REPRODUCED", so the suite is GREEN on the
defective base and turns RED the moment a repair lands (the signal to update
the report and the packet).
"""

import json
import os
import shutil
import sys
import tempfile

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
GRAPH_DIR = os.path.dirname(TESTS_DIR)          # tools/creature_graph
FIXTURES_DIR = os.path.join(TESTS_DIR, "fixtures")
AUTHORED_MIN = os.path.join(FIXTURES_DIR, "authored_min")

if GRAPH_DIR not in sys.path:
    sys.path.insert(0, GRAPH_DIR)

import build_graph  # noqa: E402
from store import CreatureGraph, content_version  # noqa: E402


class TempWorkspace:
    """A per-test temp dir; never touches the canonical data directory."""

    def __init__(self):
        self.path = tempfile.mkdtemp(prefix="f2_graph_tests_")

    def child(self, name):
        return os.path.join(self.path, name)

    def cleanup(self):
        shutil.rmtree(self.path, ignore_errors=True)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.cleanup()


def authored_copy(workspace, name="authored"):
    """Copy the immutable authored_min fixture into the workspace."""
    dst = workspace.child(name)
    shutil.copytree(AUTHORED_MIN, dst)
    return dst


def rewrite_authored_file(authored_dir, fname, transform):
    """Apply a deterministic transform to ONE authored file of a workspace
    copy (the committed fixture is never touched)."""
    path = os.path.join(authored_dir, fname)
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    payload = transform(payload)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1, ensure_ascii=False)
    return path


def build_from(authored_dir):
    """Run the REAL build_graph.build() against a fixture authored dir by
    patching the module constant (restored afterwards)."""
    saved = build_graph.AUTHORED_DIR
    build_graph.AUTHORED_DIR = authored_dir
    try:
        return build_graph.build()
    finally:
        build_graph.AUTHORED_DIR = saved


def save_store(g, workspace, name="store.json"):
    """save() with an EXPLICIT path -- never the canonical STORE_PATH."""
    path = workspace.child(name)
    g.save(path)
    return path


def min_store(objects, relations=()):
    """In-memory CreatureGraph built through the store's own add/relate API."""
    g = CreatureGraph()
    for obj in objects:
        g.add(obj)
    for src, rel, dst, note in relations:
        g.relate(src, rel, dst, note)
    return g


def verdict(defect, title, expected_honest, observed, reproduced, evidence,
            contract_refs=()):
    return {
        "defect": defect,
        "title": title,
        "expected_honest": expected_honest,
        "observed": observed,
        "verdict": "REPRODUCED" if reproduced else "REFUTED",
        "evidence": evidence,
        "contract_refs": list(contract_refs),
        "base_commit": "a12bfbcc494a273b4739f86a83e19001343ee70c",
    }
