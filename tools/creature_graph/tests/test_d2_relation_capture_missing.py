"""DEFECT 2 -- build_graph.py:64 captures object content_versions only; relations
are absent from the capture, so relation removal/changes never stale evidence.

Contract: evidence is "test results tied to an implementation version"
(schema.py docstring) and validation staleness exists so that "a physics-
relevant INPUT changed" flips the record (store.py:26-29).  A measurement that
covered a signal PATH measured the RELATION (sensor -carries_signal_to->
pathway), not just the two endpoint objects -- yet ev["captured"] is a dict of
{dep_oid: content_version} over OBJECTS ONLY (build_graph.py:59-64), and no
relation identity (existence, direction, type) is captured anywhere.

EXPECTED-HONEST: removing the measured carries_signal_to relation MUST stale
evidence whose measurement covered that path.
OBSERVED (base a12bfbcc): after a full rebuild on authored inputs with the
relation deleted, the evidence's captured dict is unchanged, refresh_validation
flips nothing, and validation stays "passing" -- the build does not even warn.
"""

import json

import harness


def run():
    with harness.TempWorkspace() as ws:
        # measurement-time world: the signal path exists
        adir_with = harness.authored_copy(ws, "authored_with_rel")
        g1 = harness.build_from(adir_with)
        ev1 = g1.get("ev.reflex_path")
        assert ev1["validation"] == "passing"
        captured_at_measurement = dict(ev1["captured"])
        rels_at_measurement = [
            (r["src"], r["rel"], r["dst"]) for r in g1.relations
            if r["rel"] == "carries_signal_to"
        ]
        assert rels_at_measurement, "fixture must contain the signal path"

        # the world changes: the relation is REMOVED (objects byte-identical)
        adir_without = harness.authored_copy(ws, "authored_without_rel")
        harness.rewrite_authored_file(
            adir_without, "relations.json",
            lambda rels: [r for r in rels if r["rel"] != "carries_signal_to"])
        g2 = harness.build_from(adir_without)

        ev2 = g2.get("ev.reflex_path")
        rels_after = [
            (r["src"], r["rel"], r["dst"]) for r in g2.relations
            if r["rel"] == "carries_signal_to"
        ]
        captured_after = dict(ev2["captured"])
        flipped = g2.refresh_validation()
        ev_after = g2.get("ev.reflex_path")

        reproduced = (
            rels_after == []
            and captured_after == captured_at_measurement
            and flipped == []
            and ev_after["validation"] == "passing"
        )
        return harness.verdict(
            defect="D2",
            title="capture records object content_versions only; removing "
                  "carries_signal_to cannot stale",
            expected_honest="removing a relation that the evidence's measurement "
                            "covered MUST stale that evidence",
            observed="relation removed from authored inputs and full rebuild run; "
                     "captured unchanged (objects only); refresh_validation "
                     "flipped []; validation remains 'passing'; no warning raised",
            reproduced=reproduced,
            evidence={
                "relation_at_measurement": rels_at_measurement,
                "relation_after": rels_after,
                "captured_at_measurement": captured_at_measurement,
                "captured_after_rebuild": captured_after,
                "refresh_flipped": flipped,
                "validation_after": ev_after["validation"],
                "capture_structure": "dict {object_id: content_version} -- no "
                                     "relation identity is representable",
            },
            contract_refs=["build_graph.py:57-64", "store.py:26-29",
                           "store.py:166-189"],
        )


def test_defect_2_reproduced():
    assert run()["verdict"] == "REPRODUCED"


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))
