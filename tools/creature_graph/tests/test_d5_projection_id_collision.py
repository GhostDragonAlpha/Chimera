"""DEFECT 5 -- graphify_projection.py:36-41 `_sanitize` is not injective and the
export loop (lines 48-74) performs NO duplicate check, while the docstring at
line 37 claims "collision-safe".  Distinct stable ids collapse to one node id.

EXPECTED-HONEST: the projection must preserve object identity across the
boundary (the module's own contract, lines 9-12: "verified by acceptance.py");
either the sanitizer is injective or export refuses/renames a collision
EXPLICITLY.  Silent duplicate node ids break every downstream multigraph
consumer (two nodes share one id; edges become ambiguous).
OBSERVED (base a12bfbcc): "probe/a.b" and "probe_a_b" both export as node id
"probe_a_b"; the projection carries two nodes with identical ids and an id_map
that folds two originals into one sanitized id -- no error, no warning.
"""

import json
import os

import harness


def run():
    import graphify_projection

    g = harness.min_store(
        objects=[
            {"id": "probe/a.b", "kind": "region", "name": "probe region (slash.dot)",
             "status": "specified", "priority": "P1"},
            {"id": "probe_a_b", "kind": "region", "name": "probe region (underscores)",
             "status": "specified", "priority": "P1"},
        ],
        relations=[
            ("probe/a.b", "inside", "probe_a_b",
             "edge between two objects whose sanitized ids collide"),
        ],
    )

    with harness.TempWorkspace() as ws:
        # NEVER write the real projection dir: repoint the module constants
        proj_dir = ws.child("graphify_projection")
        saved_dir, saved_path = graphify_projection.PROJ_DIR, graphify_projection.PROJ_PATH
        graphify_projection.PROJ_DIR = proj_dir
        graphify_projection.PROJ_PATH = os.path.join(proj_dir, "projection.json")
        try:
            report = graphify_projection.export(g)
        finally:
            graphify_projection.PROJ_DIR, graphify_projection.PROJ_PATH = saved_dir, saved_path

        with open(report["path"], encoding="utf-8") as f:
            projection = json.load(f)

    node_ids = [n["id"] for n in projection["nodes"]]
    duplicates = sorted({nid for nid in node_ids if node_ids.count(nid) > 1})
    edges_ambiguous = [
        {"source": e["source"], "target": e["target"], "relation": e["relation"]}
        for e in projection["edges"]
        if e["source"] in duplicates or e["target"] in duplicates
    ]

    reproduced = (
        len(node_ids) == 2
        and len(set(node_ids)) == 1
        and duplicates == ["probe_a_b"]
        and projection["id_map"]["probe/a.b"] == "probe_a_b"
        and projection["id_map"]["probe_a_b"] == "probe_a_b"
    )
    return harness.verdict(
        defect="D5",
        title="regex sanitizer + no duplicate check -- node ids collide while "
              "the docstring claims collision-safe",
        expected_honest="projection node ids MUST be unique: injective sanitize "
                        "or an explicit collision refusal/rename at export time",
        observed="export succeeded; 2 nodes both carrying id 'probe_a_b'; id_map "
                 "folds both originals to the same sanitized id; the inside-edge "
                 "now has identical source and target",
        reproduced=reproduced,
        evidence={
            "original_ids": ["probe/a.b", "probe_a_b"],
            "exported_node_ids": node_ids,
            "duplicate_node_ids": duplicates,
            "id_map": projection["id_map"],
            "edges_on_collided_ids": edges_ambiguous,
            "export_report_sha256": report["sha256"],
            "docstring_claim": "graphify_projection.py:37 'collision-safe'",
        },
        contract_refs=["graphify_projection.py:9-12", "graphify_projection.py:36-41",
                       "graphify_projection.py:48-74"],
    )


def test_defect_5_reproduced():
    assert run()["verdict"] == "REPRODUCED"


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))
