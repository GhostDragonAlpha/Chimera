"""Run only with this task's engine/GPU reservation; leaves owned window open."""
import argparse
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from engine_demo import _launch, _wait_ready
from demo_runtime_verify import request
import membrane_demo_client as membrane


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase")
    args = parser.parse_args()
    out = Path(__file__).parent / args.phase
    out.mkdir(exist_ok=False)
    runtime = ROOT / ".tmp/engine_runtime" / ("studio_" + args.phase)
    os.environ["CHIMERA_MD_EDGE"] = "1"
    proc, manifest = _launch(ROOT / ".tmp/engine_build/studio01/Release/chimera_engine.exe",
                             8103, runtime)
    _wait_ready(proc, 8103)
    identity = {"pid": proc.pid, "manifest": str(manifest), "files": {}}
    for path in (ROOT / "ChimeraEngine/engine/engine.cpp",
                 ROOT / "ChimeraEngine/engine/ui.cpp", runtime / "chimera_engine.exe",
                 runtime / "shaders/membrane_demo.spv"):
        identity["files"][str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    (out / "identity.json").write_text(json.dumps(identity, indent=2))
    base = "http://127.0.0.1:8103"
    inactive = request(base, "GET", "/scene")["rows"]
    rc = membrane.gate(base, membrane.load_b2(), out, 0.35, 3.0)
    results = []
    for op in ("reset", "step", "pause", "run"):
        request(base, "POST", "/membrane_demo", {"op": op, "n_steps": 256})
        status = request(base, "GET", "/membrane_demo")
        scene = request(base, "GET", "/scene")["rows"]
        row = next((r for r in scene if r["id"] == "membrane_demo"), None)
        expected = f"6 faces, iter {status['iteration']}, {status['terminal_state'] or 'ready'}"
        preserved = [r["id"] for r in scene[:len(inactive)]] == [r["id"] for r in inactive]
        request(base, "POST", "/inspect", {"id": "membrane_demo"})
        inspector = request(base, "GET", "/inspect")
        fields = {line["k"]: line["v"] for line in inspector.get("lines", [])}
        inspector_matches = (inspector.get("id") == "membrane_demo" and
                             fields.get("iteration") == str(status["iteration"]) and
                             fields.get("accepted state") == str(status["accepted_state_id"]))
        passed = row is not None and row["detail"] == expected and row["state"] == 1 and preserved and inspector_matches
        results.append({"op": op, "status": status, "scene": scene,
                        "inspector": inspector, "inspector_matches": inspector_matches,
                        "existing_row_indices_preserved": preserved, "passed": passed})
    (out / "transitions.json").write_text(json.dumps(results, indent=2))
    # Restore the raised state for the same view as the retained baseline.
    request(base, "POST", "/membrane_demo", {"op": "reset"})
    for endpoint in ("state", "studio", "scene", "membrane_demo", "glass"):
        with urllib.request.urlopen(base + "/" + endpoint, timeout=45) as response:
            raw = response.read()
        (out / (endpoint + (".png" if endpoint == "glass" else ".json"))).write_bytes(raw)
    print(json.dumps({"pid": proc.pid, "gate_rc": rc,
                      "transitions_pass": all(r["passed"] for r in results)}))
    return 0 if rc == 0 and all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
