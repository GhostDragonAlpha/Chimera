"""feature-walk-realism-01 — probe B rerun, clean: march ONLY vs a /joint write.

Probe B as run inside product_features_walk_realism.render was contaminated:
the composed stride was still active+playing from probe A, so the pose stayed
the stride's regardless of the write (steps_total advanced because the CPG
oscillator is independent of pose ownership). This rerun isolates the declared
probe: engage the CPG march ALONE (hinge+gait, stride off), then POST /joint
neck=15, then read knees + steps + neck over consecutive frames.

Prereg pointer: PREREGISTRATION.md, "The composition probes". Prediction:
the editor owner preempts the hinge (engine.cpp frame() else-if), the knee
march freezes, the neck theta lands. Firing-counter: the march continues.

Zero C++ edits. Runs on the same task resources (rtx4090 + engine_demo).
"""
from __future__ import annotations

import json
import struct
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
from engine_demo import _launch, _wait_ready, _stop_owned, _port_busy  # noqa: E402
import product_features_walk as v1                                      # noqa: E402

EVIDENCE = ROOT / "docs/evidence/agent_fleet/FEATURE_WALK_REALISM"


def main() -> int:
    port = next(p for p in (8105, 8115, 8125) if not _port_busy(p))
    BASE = f"http://127.0.0.1:{port}"

    def request(method, path, body=None, ctype="application/json", timeout=60.0):
        import urllib.request
        req = urllib.request.Request(BASE + path, data=body, method=method)
        if body is not None:
            req.add_header("Content-Type", ctype)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()

    def jreq(method, path, payload=None):
        body = json.dumps(payload).encode() if payload is not None else None
        st, raw = request(method, path, body)
        return json.loads(raw.decode("utf-8", "replace"))

    import os
    os.environ["CHIMERA_ENGINE_URL"] = BASE
    import cpp_bridge

    runtime = ROOT / f".tmp/engine_runtime/probeb-clean-{time.strftime('%Y%m%d-%H%M%S')}"
    exe = ROOT / ".tmp/engine_build/walkrealism/Release/chimera_engine.exe"
    proc, _ = _launch(exe, port, runtime)
    _wait_ready(proc, port)
    try:
        cpp_bridge.load_mesh_bin(str(ROOT / "Saved/meshes/monkey_birth.bin"), timeout=120)
        request("POST", "/joints_bin",
                (ROOT / "Saved/meshes/monkey_joints.bin").read_bytes(),
                "application/octet-stream", timeout=120)

        # march ONLY: hinge + gait; the stride lane is never engaged
        hinge_blob, _ = v1.build_hinge_blob()
        request("POST", "/hinge_bin", hinge_blob, "application/octet-stream", timeout=60)
        request("POST", "/gait_bin", v1.build_gait_payload(), "application/octet-stream", timeout=60)
        jreq("POST", "/gait", {"on": True, "steps": v1.GAIT_STEPS, "omega": v1.OMEGA_REF})
        time.sleep(1.0)

        def snap(tag):
            g = jreq("GET", "/gait")
            tj = {str(j.get("name")): float(j.get("theta", 0.0))
                  for j in (jreq("GET", "/joints").get("joints") or [])}
            return {"tag": tag, "steps_total": g.get("steps_total"),
                    "thetaL": g.get("thetaL"), "thetaR": g.get("thetaR"),
                    "knee_L": tj.get("knee_L"), "knee_R": tj.get("knee_R"),
                    "neck": tj.get("neck"), "shoulder_L": tj.get("shoulder_L")}

        series = [snap("march_solo_before_write")]
        for k in range(3):
            time.sleep(0.4)
            series.append(snap(f"march_solo_{k}"))

        st, resp = request("POST", "/joint", json.dumps({"joint": "neck", "theta": 15.0}).encode())
        series.append({"tag": "posted_neck_15", "http": st,
                       "resp": resp[:80].decode("utf-8", "replace")})
        for k in range(3):
            time.sleep(0.4)
            series.append(snap(f"after_write_{k}"))

        jreq("POST", "/gait", {"on": False})
        request("POST", "/hinge_bin", struct.pack("<I", 0), "application/octet-stream", timeout=60)

        g_steps = [s.get("steps_total") or 0 for s in series if "steps_total" in s]
        necks = [s.get("neck") for s in series if "neck" in s]
        verdict = {
            "steps_series": g_steps,
            "march_continued_after_write": g_steps[-3:] == sorted(g_steps[-3:])
                                           and g_steps[-1] > g_steps[-4],
            "neck_series": necks,
            "neck_landed": any(abs(n - 15.0) < 0.5 for n in necks[4:] if n is not None),
            "knee_L_series": [s.get("knee_L") for s in series if "knee_L" in s],
        }
        verdict["owner_preempted_march"] = not verdict["march_continued_after_write"]
        (EVIDENCE / "probeB_clean_march_vs_joint.json").write_text(json.dumps(
            {"series": series, "verdict": verdict}, indent=1))
        (EVIDENCE / "probeB_clean_march_vs_joint.txt").write_text(
            "\n".join(json.dumps(s, default=str) for s in series)
            + "\n\nVERDICT: " + json.dumps(verdict, default=str) + "\n", encoding="utf-8")
        print(json.dumps(verdict, default=str))
        _stop_owned(proc)
        return 0
    finally:
        if proc.poll() is None:
            _stop_owned(proc)


if __name__ == "__main__":
    raise SystemExit(main())
