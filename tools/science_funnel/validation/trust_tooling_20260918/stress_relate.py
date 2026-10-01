"""Stress harness for the unreproduced store relate() anomaly.

Attempts to reproduce `TypeError: 'set' object is not subscriptable` at
tools/creature_graph/store.py in relate() via many rapid builds with varied
record sets, plus adversarial injection proving the failure shape.

Honest paths must stay green; injected set/list/str edges must either raise
the raw TypeError (pre-guard, proving the shape) or the named StoreRefusal
(post-guard, proving the hardening).

Writes only to temp dirs + a log JSON under the trust_tooling validation dir.
Never touches the canonical STORE_PATH, E:\\PythonChimera, port 8127, or
SharedBody*.json.
"""
import copy
import json
import os
import random
import sys
import tempfile
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
GRAPH_DIR = os.path.normpath(os.path.join(HERE, "..", "..", "..", "creature_graph"))
if GRAPH_DIR not in sys.path:
    sys.path.insert(0, GRAPH_DIR)

from store import CreatureGraph  # noqa: E402

LOG_PATH = os.path.join(HERE, "stress_relate_log.json")


def honest_build(rng, n_objects=20, n_relations=30):
    g = CreatureGraph()
    for i in range(n_objects):
        g.add({"id": "stress.obj.%d" % i, "kind": "region",
               "name": "stress %d" % i, "status": "specified",
               "priority": "P0"})
    rels = ["inside", "contains", "attached_to", "derived_from"]
    for _ in range(n_relations):
        src = "stress.obj.%d" % rng.randrange(n_objects)
        dst = "stress.obj.%d" % rng.randrange(n_objects)
        g.relate(src, rng.choice(rels), dst, note="stress")
    # duplicate edges to exercise the ordinal path
    for _ in range(5):
        g.relate("stress.obj.0", "derived_from", "stress.obj.1", note="dup")
    return g


def file_roundtrip(g):
    tmp = tempfile.mkdtemp(prefix="stress_relate_")
    try:
        path = os.path.join(tmp, "store.json")
        g.save(path)
        g2 = CreatureGraph.load(path)
        assert g2.graph_hash() == g.graph_hash(), "roundtrip hash drift"
        return True
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    rng = random.Random(20260918)
    attempts = {"honest_builds": 0, "roundtrips": 0, "honest_failures": [],
                "injections": {}}
    # 1. honest rapid builds with varied record sets
    for n_obj, n_rel in [(10, 15), (20, 30), (50, 80), (100, 150), (5, 50)]:
        for rep in range(20):
            try:
                g = honest_build(rng, n_obj, n_rel)
                attempts["honest_builds"] += 1
                if rep % 4 == 0:
                    file_roundtrip(g)
                    attempts["roundtrips"] += 1
            except Exception:
                attempts["honest_failures"].append(traceback.format_exc(limit=3))
    # 2. adversarial injection: prove the failure shape at the used= line
    for label, bad in [("set_edge", {"rid", "src"}),
                       ("list_edge", ["rid", "src"]),
                       ("str_edge", "rid-string")]:
        g = honest_build(rng, 5, 5)
        g.relations.append(bad)  # corrupt the list as an unguarded path could
        try:
            g.relate("stress.obj.0", "derived_from", "stress.obj.1", note="after-corrupt")
            attempts["injections"][label] = "NO-RAISE (unexpected)"
        except TypeError as ex:
            attempts["injections"][label] = "TypeError: %s" % ex
        except Exception as ex:
            attempts["injections"][label] = "%s: %s" % (type(ex).__name__, ex)
    # 3. corrupt load path: relations replaced wholesale (as load() does)
    g = honest_build(rng, 5, 5)
    g.relations = list(g.relations) + [{"rid", "src"}]
    try:
        g.relate("stress.obj.0", "derived_from", "stress.obj.1")
        attempts["injections"]["load_shape_set"] = "NO-RAISE (unexpected)"
    except TypeError as ex:
        attempts["injections"]["load_shape_set"] = "TypeError: %s" % ex
    except Exception as ex:
        attempts["injections"]["load_shape_set"] = "%s: %s" % (type(ex).__name__, ex)
    total = attempts["honest_builds"]
    print("honest_builds=%d roundtrips=%d honest_failures=%d" % (
        total, attempts["roundtrips"], len(attempts["honest_failures"])))
    print("injections=%s" % json.dumps(attempts["injections"], sort_keys=True))
    with open(LOG_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"attempts": attempts,
                   "conclusion": "honest-green" if not attempts["honest_failures"] else "honest-FAILED"},
                  f, indent=1)
    print("log=" + LOG_PATH)
    if attempts["honest_failures"]:
        print("HONEST-FAILURE sample:")
        print(attempts["honest_failures"][0][:2000])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
