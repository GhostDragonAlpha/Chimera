"""DEFECT 3 -- store.py:180 `captured = ev.get("captured") or {}` lets an EMPTY
capture pass staleness checking.

The seed itself authors "captured": {} (seed/build_seed.py:807, mirrored in the
committed fixture) and relies on build time to fill it -- but the STORE API
must be safe on its own: any evidence that reaches stale_evidence() with an
empty capture (older store, hand-authored store, interrupted build) asserts
"no staleness" from ZERO information.

EXPECTED-HONEST: an empty capture MUST NOT pass.  Staleness is UNKNOWABLE
without the captured versions; honest behavior is to refuse the assertion --
treat the record as stale-by-unknown (with a named reason) or raise, never a
silent clean bill of health.
OBSERVED (base a12bfbcc): with captured == {} the record survives BOTH a
physics-relevant dep mutation AND complete deletion of the dep object;
refresh_validation flips nothing; validation stays "passing".
"""

import json

import harness
from store import content_version


def run():
    with harness.TempWorkspace() as ws:
        adir = harness.authored_copy(ws)
        g = harness.build_from(adir)

        # Reset the evidence to exactly what the seed AUTHORS (build_seed.py:807):
        # captured == {} -- e.g. a store saved before the build capture ran.
        ev = g.get("ev.conservation")
        assert ev["captured"], "build must have filled the capture"
        ev["captured"] = {}
        path = harness.save_store(g, ws)
        del g

        # reload through the store API (the only state the store can see)
        g2_path = path
        from store import CreatureGraph
        g = CreatureGraph.load(g2_path)
        assert g.get("ev.conservation")["captured"] == {}

        # mutate a dep's physics-relevant content, then DELETE the dep entirely
        ver_before = content_version(g.get("inst.band.feet"))
        g.get("inst.band.feet")["spatial"]["v0_m3"] = 0.5
        ver_after = content_version(g.get("inst.band.feet"))
        mismatches_mutated = g.stale_evidence("ev.conservation")
        flipped_mutated = g.refresh_validation()
        val_mutated = g.get("ev.conservation")["validation"]

        del g.objects["inst.band.feet"]
        mismatches_deleted = g.stale_evidence("ev.conservation")
        flipped_deleted = g.refresh_validation()
        val_deleted = g.get("ev.conservation")["validation"]

        reproduced = (
            ver_after != ver_before                    # the change WAS physics-relevant
            and mismatches_mutated == []
            and flipped_mutated == []
            and val_mutated == "passing"
            and mismatches_deleted == []
            and flipped_deleted == []
            and val_deleted == "passing"
        )
        return harness.verdict(
            defect="D3",
            title="`captured or {}` -- empty capture passes; even dep deletion "
                  "is invisible",
            expected_honest="an empty capture MUST NOT pass: staleness is "
                            "unknowable, so the record must flip to stale "
                            "(reason 'capture missing/empty') or the API must "
                            "refuse, never report clean",
            observed="captured={} record stayed 'passing' through a physics-"
                     "relevant mutation (spatial.v0_m3 0.287914 -> 0.5) AND "
                     "through deletion of the dep object; zero mismatches "
                     "reported in both cases",
            reproduced=reproduced,
            evidence={
                "captured_as_authored": {},
                "content_version_before": ver_before,
                "content_version_after": ver_after,
                "stale_evidence_after_mutation": mismatches_mutated,
                "refresh_flipped_after_mutation": flipped_mutated,
                "validation_after_mutation": val_mutated,
                "stale_evidence_after_deletion": mismatches_deleted,
                "refresh_flipped_after_deletion": flipped_deleted,
                "validation_after_deletion": val_deleted,
                "provenance": "seed authors captured:{} at seed/build_seed.py:807",
            },
            contract_refs=["store.py:176-189", "store.py:191-208",
                           "seed/build_seed.py:807"],
        )


def test_defect_3_reproduced():
    assert run()["verdict"] == "REPRODUCED"


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))
