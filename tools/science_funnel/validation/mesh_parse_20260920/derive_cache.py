"""derive_cache.py -- THE ADMISSION-TIME PREPROCESSING, run once (lane
mesh-parse-20260920). Derives, from the committed bytes:

  1. standing_body.glb  -- the pinned payload's text->raw conversion, the
     engine's own kind-'G' front door (scene_boot.derive_import_glb);
  2. ghost_standing.obj -- the ghost's exact composed bytes (the unchanged
     compose, run fresh);
  3. boot_cache_manifest.json -- both pins, plus the ghost compose's exact
     input file set (captured from the opens of a fresh compose, hashed) so a
     future input change is a REFUSAL, never a stale serve.

F4 (determinism) is enforced HERE before anything is written: three fresh
derivations of each artifact must be byte-identical. Everything this script
writes lands beside the slice; it writes nothing else.
"""
from __future__ import annotations

import builtins
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "tools" / "playable_slice"))
sys.path.insert(0, str(ROOT))

import scene_boot as sb  # noqa: E402


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def capture_opens():
    """Record the absolute paths of every file opened for reading inside the
    with-block (the ghost compose's exact input set)."""
    opened: list[str] = []
    real_open = builtins.open

    def tracking_open(file, *a, **k):
        try:
            mode = a[0] if a else k.get("mode", "r")
        except IndexError:
            mode = k.get("mode", "r")
        p = Path(file)
        if not p.is_absolute():
            p = Path.cwd() / p
        opened.append(str(p.resolve()))
        return real_open(file, *a, **k)

    return opened, tracking_open


def main() -> int:
    out = {"what": "admission-time cache derivation, lane "
                   "mesh-parse-20260920",
           "started": time.time()}
    obj, rec = sb.build_real_body()
    out["payload"] = {"sha256": rec["sha256"], "vertices": rec["vertices"],
                      "triangles": rec["triangles"]}

    # 1. the import GLB: three fresh derivations, byte-stable or refuse
    glbs = [sb.derive_import_glb(obj) for _ in range(3)]
    if not (glbs[0] == glbs[1] == glbs[2]):
        out["glb_deterministic"] = False
        print(json.dumps(out, indent=1))
        return 1
    glb_path = ROOT / "tools" / "playable_slice" / "standing_body.glb"
    glb_path.write_bytes(glbs[0])
    out["glb_deterministic"] = True
    out["glb"] = {"path": glb_path.as_posix(), "sha256": sha(glbs[0]),
                  "bytes": len(glbs[0])}
    print("glb:", out["glb"])

    # 2. the ghost bytes: the UNCHANGED compose, run fresh three times, with
    #    the first run's file opens captured for the input digest
    opened, tracker = capture_opens()
    real_open = builtins.open
    builtins.open = tracker
    try:
        runs = []
        for i in range(3):
            sb._LAYER_CACHE = None          # each run pays the full compose
            t0 = time.perf_counter()
            raw, grec = sb._build_ghost_obj_fresh()
            runs.append((raw, grec))
            print(f"fresh compose {i}: {time.perf_counter() - t0:.2f} s, "
                  f"{len(raw)} bytes")
    finally:
        builtins.open = real_open
    raw0, grec0 = runs[0]
    if not (runs[0][0] == runs[1][0] == runs[2][0]):
        out["ghost_deterministic"] = False
        print(json.dumps(out, indent=1))
        return 1
    ghost_path = ROOT / "tools" / "playable_slice" / "ghost_standing.obj"
    ghost_path.write_bytes(raw0)
    out["ghost_deterministic"] = True
    out["ghost"] = {"path": ghost_path.as_posix(), "sha256": sha(raw0),
                    "bytes": len(raw0), "rec": grec0}
    print("ghost:", {k: out["ghost"][k] for k in
                     ("path", "sha256", "bytes")})

    # 3. the manifest: both pins + the compose's exact recorded input set
    inputs = []
    seen = set()
    for p in opened:
        pp = Path(p)
        try:
            rel = pp.relative_to(ROOT)
        except ValueError:
            continue                      # outside the worktree: not an input
        if rel in seen or not pp.is_file():
            continue
        seen.add(rel)
        inputs.append({"path": rel.as_posix(), "sha256": sha(pp.read_bytes())})
    inputs.sort(key=lambda e: e["path"])
    out["compose_inputs"] = inputs
    print(f"compose inputs recorded: {len(inputs)} files")

    man = {
        "schema": "chimera.playable_slice.boot_cache.v1",
        "lane": "lane/mesh-parse-20260920",
        "import_glb": {
            "path": "tools/playable_slice/standing_body.glb",
            "kind": "G",
            "sha256": out["glb"]["sha256"],
            "bytes": out["glb"]["bytes"],
            "verts": rec["vertices"], "tris": rec["triangles"],
            "derived_from": {
                "payload": "tools/playable_slice/standing_body.obj",
                "payload_sha256": rec["sha256"]},
            "derivations": 3, "byte_identical": True,
        },
        "ghost_obj": {
            "path": "tools/playable_slice/ghost_standing.obj",
            "sha256": out["ghost"]["sha256"],
            "bytes": out["ghost"]["bytes"],
            "compose_record": grec0,
            "compose_inputs": inputs,
            "composes": 3, "byte_identical": True,
        },
        "refusal_contract": "a cache file off its pin, or a compose input off "
                            "its recorded digest, is refused BY NAME; a missing "
                            "cache derives fresh in-process (deterministic, "
                            "byte-identical, route recorded in the boot rec)",
    }
    man_path = ROOT / "tools" / "playable_slice" / "boot_cache_manifest.json"
    man_path.write_text(json.dumps(man, indent=1) + "\n", encoding="utf-8")
    out["manifest"] = man_path.as_posix()
    out["ok"] = True
    (HERE / "derive_cache_receipt.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("ok", "glb_deterministic",
                                          "ghost_deterministic",
                                          "manifest")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
