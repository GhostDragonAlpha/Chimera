"""Pull space-game-relevant objects from Objaverse (allenai, UNGATED, CC-licensed).
LVIS gives us category labels -> known specimens, which is what the DNA library needs.
Usage: python Construction/objaverse_fetch.py [per_category_cap]"""
import gzip, json, os, sys, urllib.request

D = "E:/PythonChimera/WorldModel/training_data/downloads/objaverse"
lvis = json.load(gzip.open(os.path.join(D, "lvis-annotations.json.gz")))
paths = json.load(gzip.open(os.path.join(D, "object-paths.json.gz")))
BASE = "https://huggingface.co/datasets/allenai/objaverse/resolve/main/"

CATS = ["space_shuttle", "fighter_jet", "jet_plane", "cargo_ship", "army_tank",      # hulls
        "antenna", "dish_antenna", "radar", "pipe", "canister", "cylinder",          # greebles
        "barrel", "crate", "generator", "machine_gun", "gun", "armor", "helmet",
        "drill", "wrench"]
CAP = int(sys.argv[1]) if len(sys.argv) > 1 else 25

tot = n = 0
for c in CATS:
    uids = lvis.get(c, [])[:CAP]
    outdir = os.path.join(D, "glb", c); os.makedirs(outdir, exist_ok=True)
    got = 0
    for uid in uids:
        p = paths.get(uid)
        if not p: continue
        out = os.path.join(outdir, uid + ".glb")
        if os.path.exists(out) and os.path.getsize(out) > 0:
            got += 1; continue
        try:
            urllib.request.urlretrieve(BASE + p, out)
            got += 1; n += 1; tot += os.path.getsize(out)
        except Exception:
            pass
    print(f"  {c:16}{got:>5} objects", flush=True)
print(f"DONE: {n} new files, {tot/1e6:.0f} MB", flush=True)
