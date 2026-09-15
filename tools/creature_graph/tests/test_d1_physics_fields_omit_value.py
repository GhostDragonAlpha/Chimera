"""DEFECT 1 -- schema.py:141 PHYSICS_FIELDS omits top-level value/units/source/applicability.

Contract (schema.py:139-142): "the PHYSICS-RELEVANT fields: a change to any of
these stales dependent validation evidence."  A SELECTED parameter's physical
VALUE lives at top level (schema.validate_object:212-216 requires exactly
units/source/applicability at top level, and the seed authors `value` there
too) -- so it is physics-relevant by the schema's own definition, yet
content_projection() drops it, content_version() never sees it, and
store.stale_evidence (store.py:185) cannot fire.

EXPECTED-HONEST: changing a parameter's top-level `value` MUST change its
content_version and MUST stale evidence captured against it.
OBSERVED (base a12bfbcc): content_version identical, stale_evidence() == [],
refresh_validation() flips nothing, validation stays "passing".
"""

import harness


def run():
    import schema
    from store import content_version

    with harness.TempWorkspace() as ws:
        adir = harness.authored_copy(ws)
        g = harness.build_from(adir)

        ev = g.get("ev.conservation")
        assert ev["validation"] == "passing"
        captured_before = dict(ev["captured"])
        assert "param.water_compressibility" in captured_before

        param = g.get("param.water_compressibility")
        ver_before = content_version(param)
        value_before = param["value"]

        # THE MUTATION: the physical constant changes (4.6e-10 -> 9.9e-10 Pa^-1)
        param["value"] = 9.9e-10
        ver_after = content_version(param)

        mismatches = g.stale_evidence("ev.conservation")
        flipped = g.refresh_validation()
        ev_after = g.get("ev.conservation")

        reproduced = (
            ver_after == ver_before
            and mismatches == []
            and flipped == []
            and ev_after["validation"] == "passing"
        )
        return harness.verdict(
            defect="D1",
            title="PHYSICS_FIELDS omits top-level value/units/source/applicability; "
                  "physical-value changes never stale evidence",
            expected_honest="a physical-value change MUST change content_version "
                            "and MUST stale dependent evidence (validation -> stale, "
                            "last_result keeps 'passing' visible)",
            observed="content_version unchanged after value 4.6e-10 -> 9.9e-10; "
                     "stale_evidence() == []; refresh_validation() flipped []; "
                     "validation remains 'passing'",
            reproduced=reproduced,
            evidence={
                "value_before": value_before,
                "value_after": param["value"],
                "content_version_before": ver_before,
                "content_version_after": ver_after,
                "stale_evidence": mismatches,
                "refresh_flipped": flipped,
                "validation_after": ev_after["validation"],
                "captured_at_build": captured_before,
                "PHYSICS_FIELDS": list(schema.PHYSICS_FIELDS),
            },
            contract_refs=["schema.py:139-142", "schema.py:220-223",
                           "store.py:37-40", "store.py:176-189"],
        )


def test_defect_1_reproduced():
    assert run()["verdict"] == "REPRODUCED"


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=1, default=str))
