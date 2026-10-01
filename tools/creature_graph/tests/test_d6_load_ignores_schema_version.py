"""DEFECT 6 -- store.py:247-248 `load` records `loaded_schema_version` WITHOUT
ever comparing it to SCHEMA_VERSION: a store written by any schema version
loads silently; there is no refusal and no migration path.

EXPECTED-HONEST: load() MUST refuse (or explicitly migrate) a store whose
schema_version is not supported; writing the version into meta is bookkeeping,
not a check.  The schema module itself carries SCHEMA_VERSION and
SCHEMA_VERSION_LEGACY precisely so the supported set is decidable.
OBSERVED (base a12bfbcc): a store rewritten to "0.0.9-from-the-future" loads,
serves all 1,482-object-shaped content (here: its fixture objects) with no
error and no warning; meta merely notes the version it was never asked about.
"""

import json

import harness
from store import CreatureGraph, SCHEMA_VERSION


def run():
    with harness.TempWorkspace() as ws:
        g = harness.min_store(
            objects=[
                {"id": "region.probe", "kind": "region", "name": "probe region",
                 "status": "specified", "priority": "P1"},
            ],
        )
        path = harness.save_store(g, ws)

        # rewrite the persisted schema_version to an UNSUPPORTED value
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
        foreign = "0.0.9-from-the-future"
        payload["schema_version"] = foreign
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=1, ensure_ascii=False)

        error_raised = None
        try:
            g2 = CreatureGraph.load(path)
        except Exception as exc:  # noqa: BLE001 -- the refusal IS the honest path
            error_raised = repr(exc)
            g2 = None

        observed = {
            "schema_version_supported": SCHEMA_VERSION,
            "persisted_schema_version": foreign,
            "load_error": error_raised,
        }
        if g2 is not None:
            observed.update({
                "loaded_schema_version_in_meta": g2.meta.get("loaded_schema_version"),
                "objects_served": sorted(g2.objects.keys()),
                "layout_served": g2.layout,
            })

        reproduced = (
            error_raised is None
            and g2 is not None
            and g2.meta.get("loaded_schema_version") == foreign
            and "region.probe" in g2.objects
        )
        return harness.verdict(
            defect="D6",
            title="load records loaded_schema_version without comparing; "
                  "unsupported schema versions load",
            expected_honest="load MUST refuse (or explicitly migrate) a store "
                            "whose schema_version is outside the supported set",
            observed="load succeeded with no error; meta.loaded_schema_version "
                     "recorded '0.0.9-from-the-future'; all objects served "
                     "as-is; no migration performed",
            reproduced=reproduced,
            evidence=observed,
            contract_refs=["store.py:238-249", "schema.py:135-137"],
        )


def test_defect_6_reproduced():
    assert run()["verdict"] == "REPRODUCED"


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))
