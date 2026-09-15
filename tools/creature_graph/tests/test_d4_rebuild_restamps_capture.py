"""DEFECT 4 -- build_graph.py:64 re-stamps `captured` unconditionally while
validation and captured_utc stay untouched: a rebuild rewrites the HISTORICAL
capture and the timestamp is left describing versions it no longer names.

The seed carries captured_utc "2026-09-15T13:47:00Z" -- the moment the
measurement was taken.  build_graph.py:59-64 overwrites ev["captured"] with
CURRENT content_versions on every build, never touches captured_utc, and never
stales on the diff it just erased.

EXPECTED-HONEST: the capture is a MEASUREMENT RECORD.  A rebuild must not
rewrite what the evidence measured; if it re-stamps (e.g. as an explicit
recapture operation), it MUST update captured_utc and/or flip the validation
state -- the stored (captured, captured_utc) pair must never become a lie.
OBSERVED (base a12bfbcc): after a physics-relevant dep change (a PHYSICS_FIELDS
member: spatial.v0_m3) and rebuild, captured silently moves to the NEW version,
captured_utc still reads 2026-09-15T13:47:00Z, validation still "passing", and
a subsequent refresh_validation reports nothing -- the change is now
undetectable through the store API.
"""

import json

import harness
from store import content_version


def run():
    with harness.TempWorkspace() as ws:
        # measurement-time world
        adir_v1 = harness.authored_copy(ws, "authored_v1")
        g1 = harness.build_from(adir_v1)
        ev1 = g1.get("ev.conservation")
        captured_v1 = dict(ev1["captured"])
        captured_utc_seed = ev1["captured_utc"]
        ver_v1 = content_version(g1.get("inst.band.feet"))
        assert captured_utc_seed == "2026-09-15T13:47:00Z"

        # the world changes IN A PHYSICS FIELD (spatial is PHYSICS_FIELDS[1])
        adir_v2 = harness.authored_copy(ws, "authored_v2")
        harness.rewrite_authored_file(adir_v2, "instances.json", _bump_v0)
        g2 = harness.build_from(adir_v2)

        ev2 = g2.get("ev.conservation")
        captured_v2 = dict(ev2["captured"])
        ver_v2 = content_version(g2.get("inst.band.feet"))
        flipped = g2.refresh_validation()
        ev_final = g2.get("ev.conservation")

        reproduced = (
            ver_v2 != ver_v1
            and captured_v2["inst.band.feet"] != captured_v1["inst.band.feet"]
            and ev_final["captured_utc"] == "2026-09-15T13:47:00Z"
            and flipped == []
            and ev_final["validation"] == "passing"
        )
        return harness.verdict(
            defect="D4",
            title="unconditional re-stamp rewrites historical capture; "
                  "validation/captured_utc untouched",
            expected_honest="a rebuild MUST NOT rewrite the historical capture; "
                            "if it re-stamps it MUST update captured_utc and/or "
                            "stale the evidence -- (captured, captured_utc) must "
                            "never describe two different moments",
            observed="rebuild rewrote captured to the new versions while "
                     "captured_utc kept 2026-09-15T13:47:00Z; refresh_validation "
                     "flipped []; validation remains 'passing'; the v0 change is "
                     "now undetectable via the store API",
            reproduced=reproduced,
            evidence={
                "captured_v1": captured_v1,
                "captured_v2": captured_v2,
                "content_version_dep_v1": ver_v1,
                "content_version_dep_v2": ver_v2,
                "captured_utc_before_and_after": ev_final["captured_utc"],
                "refresh_flipped": flipped,
                "validation_after": ev_final["validation"],
                "mutation": "instances.json inst.band.feet spatial.v0_m3 "
                            "0.287914 -> 0.5 (a PHYSICS_FIELDS member)",
                "real_world_instance": "ev.band_seal_conservation re-committed by "
                                       "the 14:31:44Z rebuild recorded in "
                                       "DISCOVERY_EVIDENCE D5",
            },
            contract_refs=["build_graph.py:57-64", "store.py:191-208",
                           "seed/build_seed.py (captured_utc 13:47:00Z)"],
        )


def _bump_v0(payload):
    for obj in payload:
        if obj["id"] == "inst.band.feet":
            obj["spatial"]["v0_m3"] = 0.5
    return payload


def test_defect_4_reproduced():
    assert run()["verdict"] == "REPRODUCED"


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))
