"""regen_wiring.py -- the lane's AUTHORING helper (membrane-ground).

Re-derives the whole pin chain after any edit to the spec or the member
modules, in dependency order (the packetgen law: ONE authoritative source --
the spec -- and generated artifacts carrying byte identities):

  1. hash the spec; rewrite the spec sha pin in BOTH member modules'
     PINNED_INPUTS tables (token-targeted, byte-preserving otherwise);
  2. hash both member modules; rewrite module_sha256 + wraps.sha256 in the
     implementation-binding manifest;
  3. DELETE + regenerate BOTH generated artifacts from scratch with the
     frozen graph_wiring_generate (identical inputs -> byte-identical
     artifacts);
  4. print every identity.

This file is an authoring tool of the lane; it never runs in the runner jobs
(the harness re-checks regeneration identity itself, chk.1 law).
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent
SPEC_REL = "spec/ground_walk_contact.spec.v1.json"
MANIFEST_REL = "abi_binding_manifest.ground_walk.v1.json"
MODULES = ("membrane_ground.py", "membrane_hand_fixture_stub.py")
GEN = ("generated/bindings.ground_walk.v1.py",
       "generated/assembly_wiring_graph.ground_walk.v1.py")


def sha(path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def main() -> int:
    spec_sha = sha(ROOT / SPEC_REL)
    for mod in MODULES:
        p = ROOT / mod
        text = p.read_text(encoding="utf-8")
        new_text, n = re.subn(
            r'("spec/ground_walk_contact\.spec\.v1\.json":\s*\n\s*")[0-9a-f]{64}(")',
            r'\g<1>' + spec_sha + r'\g<2>', text)
        if n != 1:
            print(f"FAIL: expected exactly one spec pin in {mod}, found {n}")
            return 1
        if new_text != text:
            p.write_text(new_text, encoding="utf-8")
            print(f"pinned spec sha in {mod}")
        else:
            print(f"spec pin already current in {mod}")
    module_shas = {m: sha(ROOT / m) for m in MODULES}
    mp = ROOT / MANIFEST_REL
    manifest = json.loads(mp.read_text(encoding="utf-8"))
    for entry in manifest["implementations"]:
        s = module_shas[entry["module_file"]]
        entry["module_sha256"] = s
        entry["wraps"]["sha256"] = s
    mp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                  encoding="utf-8")
    print("manifest pinned")
    for rel in GEN:
        (ROOT / rel).unlink(missing_ok=True)
    sys.path.insert(0, str(ROOT))
    import graph_wiring_generate
    receipt = graph_wiring_generate.generate_graph_wiring(
        ROOT, SPEC_REL, MANIFEST_REL, out_dir=ROOT / "generated")
    print("spec                ", spec_sha)
    for m, s in module_shas.items():
        print(f"{m:32s}", s)
    for row in receipt["outputs"]:
        print(f"{pathlib.Path(row['path']).name:32s}", row["sha256"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
