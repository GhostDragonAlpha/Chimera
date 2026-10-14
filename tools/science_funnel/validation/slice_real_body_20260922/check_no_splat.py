"""check_no_splat.py -- F-SLICE-NO-SPLAT (the conformance gate, re-run).

The slice's render path is the TRIANGLE path only: /mesh_import + /verts +
/topology (client WebGL2). No splat route is reachable from any slice file:
the audit greps every slice file for the splat machinery's own names
(layer_splat_buffer, membrane_bin, splat.wgsl, /membrane) and requires ZERO
hits. Any hit = the conformance gate is RED.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SLICE = HERE.parents[3] / "tools" / "playable_slice"
FILES = ["scene_boot.py", "slice_server.py", "index.html",
         "run_slice.ps1", "PlayableSlice.bat", "mock_registry.json",
         "standing_body.obj"]
PATTERNS = ["layer_splat_buffer", "membrane_bin", "splat.wgsl", "/membrane",
            "splat_mesh", "anysplat", "bake_splat"]


def main() -> int:
    hits = []
    for name in FILES:
        text = (SLICE / name).read_text(encoding="utf-8", errors="ignore").lower()
        for pat in PATTERNS:
            if pat.lower() in text:
                hits.append({"file": name, "pattern": pat})
    # the route allowlist actually used by the slice server + its boot module
    server = chr(10).join((SLICE / f).read_text(encoding="utf-8", errors="ignore")
                          for f in ("slice_server.py", "scene_boot.py"))
    routes = sorted({r for r in (
        "/mesh_import", "/verts", "/topology", "/tick_gravity", "/tick_touch",
        "/tick_state", "/frame", "/membrane_bin")
        if f'"{r}"' in server or f"'{r}'" in server})
    splat_routes = [r for r in routes if "membrane" in r or "splat" in r]
    ok = not hits and not splat_routes
    out = {"falsifier": "F-SLICE-NO-SPLAT", "pass": ok,
           "grep_hits": hits, "patterns": PATTERNS,
           "engine_routes_referenced": routes,
           "splat_routes_referenced": splat_routes,
           "law": "the slice render path is triangles only: /mesh_import in, "
                  "/verts + /topology streamed; /membrane_bin and every splat "
                  "builder unreachable"}
    (HERE / "no_splat.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
