"""material_elements.py — THE ELEMENTS. One joint codebook over EVERY real captured
3DGS object in the collection, so one genome ID means the same material no matter
which scan it was measured from.

THE RULE (the operator, 2026-07-31, verbatim): "you have to use 3DS objects and then
extract the shape and texture data" / "extract certain elements and then train them
all together. You have to decide what portion of the total that we have" / "this is
how the entire game is supposed to be made."

THE PORTION DECISION (mine, as instructed — recorded so it can be overruled):
  INCLUDE — real captures, grouped by the element vocabulary they carry:
    METAL/HULL   truck, train, bicycle      painted steel, chrome, rust, rubber, glass
    GROUND       garden, stump, treehill    grass, stone, soil/forest floor, moss, bark
    VEGETATION   garden_tree, ChristmasTree, bonsai_tree   real tree scans (.ply)
    INTERIOR     kitchen, counter, playroom, room7k, bonsai, drjohnson  wood, plaster,
                 plastic, ceramic, fabric
    SOFT         nike, plush                rubber, foam, fabric
  EXCLUDE — with reasons (an exclusion is a decision, so it is written down):
    gen_tree_*.ply, warp_gen_*.ply, molds/tree_type_*.ply — SYNTHETIC, our own output.
        Training on our own output is a monad: the answer would need no observer.
    fx/{birthday,flame,sear}.splatv — fire volumetrics: not surface materials, and a
        different (video) format this reader does not handle.
    inria/<scene>/ — the SOURCE PHOTOS these very splats were trained from; the
        Gaussians already encode them. Training on them twice weights them twice.
    inria_models.zip (14.7 GB) — archive of the same trained models, already extracted.
    objaverse/ — GLB meshes, not 3DGS Gaussians: no per-primitive shape/opacity to
        extract. A different pipeline, not this one.
    truck.ply / truck_test.ply / dyl truck_7k.ply / bonsai_7k.ply /
    bonsai_point_cloud_*.ply — duplicate captures of scenes already represented by the
        one file chosen per scene below.
    bonsai_tree.ply — MEASURED DEGENERATE (2026-07-31 probe): its scale fields are
        placeholders (loaded median exactly 1.0, raw outliers to e^88 that overflow
        float32), so it carries no usable SHAPE data — and its scene is already covered
        by dyl/bonsai_bonsai-7k.splat's 1.16M proper Gaussians.

UNITS — measured, then fixed: log_size is in each capture's OWN units and is NOT
cross-scene comparable raw (medians ranged -6.5 plush to -4.25 bonsai: a small-object
scan and a room scan). What travels across captures is grain size RELATIVE to the
capture's own typical grain, so the clustering feature is per-scene-median-normalised
(`log_size_rel`); the raw per-scene stats are persisted alongside for provenance.

FEATURES — the house set (codebook.py, space_materials.py): per-splat CONFIGURATION,
not position: log_size (median axis), anisotropy, R,G,B, opacity, greenness. Only
OPAQUE surface splats (opacity > 0.5) — haze is not a material.

HONESTY: capture lighting is baked into R,G,B. These are APPEARANCE genomes —
measured shape + measured texture exactly as the operator defined — not PBR
(roughness/metalness are not recoverable from a splat's colour; that was
material_dna.py's note and it still stands).

Run:  C:\\Python314\\python.exe Construction/material_elements.py
"""
import sys, json, datetime
import numpy as np
import torch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from Construction.ksplat_io import load_any

dev = "cuda"
K = 32                     # the vocabulary: ~10 metal + ground/stone/soil + vegetation
                           # + wood/plaster/plastic/fabric/ceramic/glass elements
PER = 400_000              # per-scan opaque-sample cap (space_materials' number)

D = "E:/PythonChimera/WorldModel/training_data/downloads"
T = "E:/PythonChimera/WorldModel/training_data"
SRC = [
    # METAL/HULL
    ("truck",         f"{D}/truck.splat"),
    ("train",         f"{D}/train.splat"),
    ("bicycle",       f"{D}/bicycle.splat"),
    # GROUND
    ("garden",        f"{D}/garden.splat"),
    ("stump",         f"{D}/stump.splat"),
    ("treehill",      f"{D}/treehill.splat"),
    # VEGETATION
    ("garden_tree",   f"{T}/garden_tree.ply"),
    ("christmas_tree", f"{D}/ChristmasTree.ply"),
    # INTERIOR
    ("kitchen",       f"{D}/dyl/kitchen_kitchen-7k.splat"),
    ("counter",       f"{D}/dyl/counter_counter-7k.splat"),
    ("playroom",      f"{D}/dyl/playroom_playroom-7k.splat"),
    ("room7k",        f"{D}/dyl/room-7k.splat"),
    ("bonsai",        f"{D}/dyl/bonsai_bonsai-7k.splat"),
    ("drjohnson",     f"{D}/dyl/drjohnson_7k.ply"),
    # SOFT
    ("nike",          f"{D}/nike.splat"),
    ("plush",         f"{D}/plush.splat"),
]
FEATURE_NAMES = ["log_size", "aniso", "R", "G", "B", "opacity", "greenness"]


def features(rgb, op, sc, idx):
    """Per-splat CONFIGURATION features (shape + texture — never position)."""
    ss = np.sort(sc[idx], 1)
    return np.stack([np.log(ss[:, 1] + 1e-6),
                     1 - ss[:, 0] / (ss[:, 2] + 1e-9),
                     rgb[idx][:, 0], rgb[idx][:, 1], rgb[idx][:, 2],
                     op[idx],
                     rgb[idx][:, 1] - np.maximum(rgb[idx][:, 0], rgb[idx][:, 2])], 1)


def main():
    rng = np.random.default_rng(0)
    F_all, S_all = [], []
    names = []
    scene_units = {}
    for name, p in SRC:
        pos, rgb, op, sc, q = load_any(p, full=True)
        solid = np.where(op > 0.5)[0]           # only OPAQUE surface splats
        idx = rng.choice(solid, min(PER, len(solid)), replace=False)
        f = features(rgb, op, sc, idx).astype(np.float32)
        scene_units[name] = {"median_log_size_raw": float(np.median(f[:, 0]))}
        f[:, 0] -= scene_units[name]["median_log_size_raw"]   # UNITS: relative grain
        F_all.append(f)
        S_all.append(np.full(len(idx), len(names)))
        names.append(name)
        print(f"  {name:15}{len(pos):>10,} splats -> sampled {len(idx):,}")
    F = np.concatenate(F_all)
    S = np.concatenate(S_all)
    raw = F.copy()
    Fz = (F - F.mean(0)) / (F.std(0) + 1e-9)
    X = torch.tensor(Fz, device=dev)

    # Joint GPU k-means — ONE fit over ALL scans, so genome IDs are comparable
    # everywhere (chunked cdist: 6M x K float32 per call would be ~800 MB a pop).
    g = torch.Generator(device=dev).manual_seed(0)
    C = X[torch.randperm(len(X), generator=g, device=dev)[:K]].clone()
    CHUNK = 1_000_000
    for it in range(60):
        lab = torch.empty(len(X), dtype=torch.long, device=dev)
        for s in range(0, len(X), CHUNK):
            lab[s:s + CHUNK] = torch.cdist(X[s:s + CHUNK], C).argmin(1)
        for k in range(K):
            m = lab == k
            if m.any():
                C[k] = X[m].mean(0)
    lab = lab.cpu().numpy()

    print(f"\nMATERIAL ELEMENTS — {K} genomes, ONE codebook over {len(SRC)} real scans")
    print("(size = grain size RELATIVE to its own capture's median: 1.0 = typical)\n")
    print(f"{'id':4}{'%':>7}{'size×':>8}{'aniso':>7}{'opacity':>9}{'colour':>22}   dominant sources")
    print("-" * 78)
    genomes = []
    for k in np.argsort([-(lab == k).mean() for k in range(K)]):
        m = lab == k
        r = raw[m]
        c = r[:, 2:5].mean(0)
        mix = np.bincount(S[m], minlength=len(names)) / max(1, m.sum())
        dom = " ".join(f"{names[i]} {100 * mix[i]:.0f}%"
                       for i in np.argsort(-mix)[:3] if mix[i] > 0.10)
        print(f"#{k:<3}{100 * m.mean():>6.1f}%{np.exp(r[:, 0]).mean():>8.3f}"
              f"{r[:, 1].mean():>7.2f}{r[:, 5].mean():>9.2f}"
              f"   [{c[0]:.2f} {c[1]:.2f} {c[2]:.2f}]{'':>4}   {dom}")
        feat = {}
        for j, fn in enumerate(FEATURE_NAMES):
            feat[fn] = {"mean": float(r[:, j].mean()), "std": float(r[:, j].std()),
                        "p10": float(np.percentile(r[:, j], 10)),
                        "p90": float(np.percentile(r[:, j], 90))}
        genomes.append({"id": int(k), "fraction": float(m.mean()), "n_splats": int(m.sum()),
                        "features": feat,
                        "dominant_source": {names[i]: float(mix[i])
                                            for i in np.argsort(-mix) if mix[i] > 0.10}})

    # PERSIST, or the library evaporates at process exit (the 2026-07-31 lesson).
    out = {
        "source": f"Construction/material_elements.py — GPU k-means (K={K}), ONE joint "
                  f"fit over {len(SRC)} real captured 3DGS objects (opaque splats only)",
        "the_rule": "the operator, 2026-07-31: the game is made from 3DGS objects — "
                    "extract the shape and texture data, train them all together",
        "scans": {n: p for n, p in SRC},
        "excluded": {
            "gen_tree_*/warp_gen_*/molds": "SYNTHETIC — our own output; training on it is a monad",
            "fx/*.splatv": "fire volumetrics — not surface materials, different format",
            "inria/<scene>/": "source photos of these very splats — already encoded",
            "inria_models.zip": "archive of the same models, already extracted",
            "objaverse/": "GLB meshes, not 3DGS Gaussians — different pipeline",
            "duplicate captures": "one file per scene, listed in scans",
        },
        "feature_names": ["log_size_rel"] + FEATURE_NAMES[1:],
        "scene_units": scene_units,
        "honesty": "APPEARANCE genomes: capture lighting is baked into R,G,B. Measured "
                   "shape + measured texture, not PBR — no roughness/metalness is "
                   "recoverable from splat colour. log_size_rel is per-scene-median-"
                   "normalised (raw per-scene medians in scene_units).",
        "written": str(datetime.date.today()),
        "genomes": genomes,
    }
    dst = Path(__file__).resolve().parents[1] / "story" / "data" / "material_genomes.json"
    dst.write_text(json.dumps(out, indent=1))
    print(f"\npersisted {len(genomes)} genomes -> {dst}")


if __name__ == "__main__":
    main()
