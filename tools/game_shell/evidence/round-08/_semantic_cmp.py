"""Semantic comparison of two creature_graph.json files (order-insensitive)."""
import json
import sys

pa, pb = sys.argv[1], sys.argv[2]
a = json.load(open(pa, encoding="utf-8"))
b = json.load(open(pb, encoding="utf-8"))

ka, kb = list(a["objects"]), list(b["objects"])
print("objects: count", len(ka), len(kb))
print("objects: same key set      :", set(ka) == set(kb))
print("objects: same insertion order:", ka == kb)
only_a = [k for k in ka if k not in b["objects"]]
only_b = [k for k in kb if k not in a["objects"]]
print("objects only in A:", only_a[:5], " only in B:", only_b[:5])
diffvals = [k for k in ka if k in b["objects"] and a["objects"][k] != b["objects"][k]]
print("objects with different value:", len(diffvals), diffvals[:5])
if diffvals:
    k = diffvals[0]
    oa, ob = a["objects"][k], b["objects"][k]
    for f in sorted(set(oa) | set(ob)):
        if oa.get(f, "<absent>") != ob.get(f, "<absent>"):
            print("  field differs:", k, "->", f)

ra = sorted(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in a["relations"])
rb = sorted(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in b["relations"])
print("relations: count", len(a["relations"]), len(b["relations"]))
print("relations: multiset equal:", ra == rb)
print("relations: same order    :", a["relations"] == b["relations"])
print("layout: equal:", a.get("layout") == b.get("layout"))
print("--- meta A ---")
print(json.dumps(a["meta"], indent=1, ensure_ascii=False))
print("--- meta B ---")
print(json.dumps(b["meta"], indent=1, ensure_ascii=False))
