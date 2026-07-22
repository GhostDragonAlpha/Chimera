"""photo_to_tree.py — THE WHOLE WORKFLOW in one command.

Photo in, textured 3D tree out.  Every design decision is already in the code;
this just runs the steps in the one correct order so a weak agent (or a tired one)
cannot take a wrong turn.  See Construction/REFERENCE_TO_NOUN.md.

    python Construction/photo_to_tree.py --photo <ABSOLUTE path to a tree photo> [--name oak]

Steps (each is also runnable on its own — see the recipe):
  1. EXTRACT   the photo's descriptors  (core.trainables.tree_appearance extract)
  2. TRAIN     the template's params to the photo  (core.trainer)
  3. CROSS     template markers x photo patches -> textured 3D tree  (Construction.cross)

You get the reference photo yourself first (browser + curl with headers — the
recipe has the exact command); everything after that is this one script.
"""
from __future__ import annotations
import argparse, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # E:\PythonChimera
CHIM = os.path.join(ROOT, "Chimera")


def run(cmd, cwd, name):
    env = dict(os.environ, PYTHONPATH=CHIM + os.pathsep + ROOT)
    print(f"\n=== {name} ===\n>> {' '.join(cmd)}  (cwd={cwd})")
    subprocess.check_call(cmd, cwd=cwd, env=env)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo", required=True, help="ABSOLUTE path to a tree photo (JPEG)")
    ap.add_argument("--name", default="oak", help="reference name (namespaces the descriptors)")
    ap.add_argument("--lod", default="1.0", help="template level-of-detail (marker density)")
    ap.add_argument("--pop", default="200"); ap.add_argument("--gens", default="60")
    a = ap.parse_args()
    photo = os.path.abspath(a.photo)
    if not os.path.isfile(photo):
        sys.exit(f"photo not found: {photo}")
    os.environ["CHIMERA_TREE_REF"] = a.name            # namespaces steps 1+2
    py = sys.executable
    trained = "docs/objectives/tree_appearance.trained.json"

    run([py, "-m", "core.trainables.tree_appearance", "extract", "--photo", photo],
        cwd=CHIM, name="1. EXTRACT descriptors")
    run([py, "-m", "core.trainer", "--domain", "core.trainables.tree_appearance",
         "--objective", "docs/objectives/tree_appearance.json",
         "--pop", a.pop, "--gens", a.gens, "--out", trained],
        cwd=CHIM, name="2. TRAIN template params to the photo")
    out = f"Construction/renders/{a.name}_tree"
    run([py, "-m", "Construction.cross", "--photo", photo,
         "--genome", os.path.join("Chimera", trained), "--out", out, "--lod", a.lod],
        cwd=ROOT, name="3. CROSS markers x photo patches")
    print(f"\nDONE -> {out}_0.png (front) + {out}_1.png (angle).  Read them to judge by eye.")


if __name__ == "__main__":
    main()
