"""Generate docs/LEDGER_GRAPH.json - the cohesive development ledger as a graph.

Geometric by construction: the five training pillars anchor the layout as a
simplex; features sit in their tier rings; laws fence everything; evidence
and dyad verdicts hang off what they prove or judge. Portable nodes/edges
JSON - importable into any graph system (Graphy included) without change.
Positions are computed here (deterministic), not by the renderer.
"""
import json, math
from pathlib import Path

ROOT = Path(r"E:\ChimeraWork\slot-05")
OUT = ROOT / "docs" / "LEDGER_GRAPH.json"

nodes, edges = [], []

def node(nid, kind, label, status="", refs=None, pos=(0, 0, 0), note=""):
    nodes.append({"id": nid, "kind": kind, "label": label, "status": status,
                  "refs": refs or [], "pos": [round(x, 3) for x in pos], "note": note})
    return nid

def edge(a, b, kind):
    edges.append({"from": a, "to": b, "kind": kind})

# --- the five pillars (the anchors; simplex vertices) ------------------------
pillars = [
    ("P1", "SCENARIO", "the episode each material/body must survive, falsifier named first"),
    ("P2", "MEASURED-TRUTH", "recorded reality to imitate - never taste (download data FIRST)"),
    ("P3", "FAST-FIELD", "the differentiable GPU triangle lattice - the training ground"),
    ("P4", "LOSS-IN-LAWS", "behavior match inside the fences: energy<1%, welds never split"),
    ("P5", "JUDGE", "the dyad eye first, math second, the human override always"),
]
R = 5.0
ppos = {}
for i, (pid, name, note) in enumerate(pillars):
    ang = 2 * math.pi * i / 5
    ppos[pid] = (R * math.cos(ang), 2.2, R * math.sin(ang))
    node(pid, "pillar", name, "law", pos=ppos[pid], note=note)

# --- the laws (the fences - never trained) -----------------------------------
laws = [
    ("L0", "RULE 0", "every membrane is a theory: statement/prediction/falsifier before build"),
    ("L1", "RULE 1", "derive before train; a sweep is the confession"),
    ("LK", "KITCHEN", "C++ frozen; one named appliance in series; Python is the language of ideas"),
    ("LD", "BLIND DYAD", "scenario+goal only; unprompted words decide; one picture per call"),
    ("LM", "MULTIPLAYER-MINDED", "every client serves the world; no client owns it; dual purpose"),
    ("LT", "TRANSLATION", "meshes author; the sampled field is truth; mass conserved exactly"),
    ("LR", "RELATIVE FRAME", "no global frame; origin = CoG; force is the only mover"),
]
for j, (lid, name, note) in enumerate(laws):
    ang = 2 * math.pi * j / len(laws)
    node(lid, "law", name, "fence", pos=(3.0 * math.cos(ang), -2.0, 3.0 * math.sin(ang)), note=note)
    for pid, _, _ in pillars:
        if (lid, pid) in (("L0", "P1"), ("L1", "P2"), ("LK", "P3"), ("LT", "P3"),
                          ("LR", "P3"), ("L0", "P4"), ("L1", "P4"), ("LD", "P5")):
            edge(lid, pid, "fences")

# --- the feature inventory (tiers as rings) ----------------------------------
tiers = [
    (0, "FROZEN+PROVEN", ["1 creature renders", "2 truthful HUD", "3 choreography",
                          "4 camera fit", "5 HTTP viewer"], 7.5),
    (1, "LOCOMOTION [CURRENT]", ["6 walks and travels", "7 feet plant no slide",
                                 "8 arms counter-swing + bob"], 9.5),
    (2, "FLUIDS", ["9 water as a body", "10 downhill flow", "11 buoyancy"], 11.5),
    (3, "MATERIALS", ["12 squash/spring", "13 cloth bend", "14 fracture", "15 freeze",
                      "16 melt", "17 burn"], 13.5),
]
fids = {}
for t, tname, feats, radius in tiers:
    y = 0.9 - 0.9 * t
    for k, f in enumerate(feats):
        fid = f"T{t}.{k}"
        ang = 2 * math.pi * k / len(feats) + 0.35 * t
        status = "proven" if t == 0 else ("current" if t == 1 else "queued")
        fids[fid] = node(fid, "feature", f, status, pos=(radius * math.cos(ang), y, radius * math.sin(ang)))
        edge("LM" if t == 7 else "L1", fid, "orders") if False else None
for a, b in [("T1.0", "T1.1"), ("T1.1", "T1.2"), ("T1.0", "T2.0")]:
    edge(a, b, "requires")

# --- the current front: the TRAINED WALK (replaces the puppet takes) ---------
wnode = node("WALK-TRAIN", "lane", "the body learns to walk by its own force",
             "current", refs=["external/myo_sim", "walker.py", "ppo_policy.pt",
                              "tools/training_gate.py", "docs/THE_WALK_PROGRAM.md"],
             pos=(0, 3.4, 0),
             note="begin=standing end=across the room; targets derived (Froude+pendulum); "
                  "learned gait renders through the engine for the dyad")
for pid in ("P1", "P2", "P3", "P4", "P5"):
    edge(wnode, pid, "trains-under")
edge(wnode, "T1.0", "unfolds")

# --- evidence on record (today's honest trail) --------------------------------
ev = [
    ("E-battery", "root parity battery: P1/P4 PASS (thetas untouched; pixel-exact round-trip); P2/P3 FAIL recorded",
     ["docs/evidence/agent_fleet/ENGINE_ROOT_TRANSLATION"]),
    ("E-v3c", "full-frame take: commanded-vs-rendered gap closed on the joint path (dyad-verified motion)",
     ["E:/ChimeraWork/concept_proof/walk3c"]),
    ("E-crash", "take-4 crash bisect: engine innocent; three heavy clients starved it - observer yields law born",
     ["E:/ChimeraWork/concept_proof/bisect_crash.py"]),
    ("E-puppet", "the linear root velocity was AUTHORED, not trained - operator caught it; the law it broke is LR",
     []),
]
for i, (eid, note, refs) in enumerate(ev):
    ang = 2 * math.pi * i / len(ev)
    node(eid, "evidence", eid.replace("E-", ""), "recorded", refs=refs,
         pos=(2.2 * math.cos(ang), 4.6, 2.2 * math.sin(ang)), note=note)
    edge(eid, "LR" if eid == "E-puppet" else wnode, "proves" if eid != "E-puppet" else "violated")

doc = {
    "name": "CHIMERA - the development ledger",
    "law": "THE_ALIGNMENT.md; THE_GAME.md; THE_LAW.md",
    "geometry": "pillars anchor a simplex; laws fence; tiers ring outward; the front rises",
    "nodes": nodes,
    "edges": edges,
}
OUT.write_text(json.dumps(doc, indent=1), encoding="utf-8")
print("wrote", OUT, "| nodes:", len(nodes), "edges:", len(edges))
