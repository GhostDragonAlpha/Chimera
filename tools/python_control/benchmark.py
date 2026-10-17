"""Owned-native benchmark: existing direct HTTP vs typed control and batching.

All samples use one private engine, the pinned B2 fixture and identical native
physical laws. This measures orchestration, not a Python rendering replacement.
"""
import argparse
import hashlib
import json
import random
import shutil
import socket
import statistics
import subprocess
import time
from pathlib import Path
from .client import EngineControl, NativeRefusal
from .__main__ import run_scenario
from tools.membrane_demo_client import load_b2, md01_packet, http_req, FIX


def unwrap(result): return result.get("status", result)

def summary(samples):
    ordered = sorted(samples)
    return {"median_ms": statistics.median(samples), "p95_ms": ordered[int(.95*(len(ordered)-1))],
            "min_ms": min(samples), "max_ms": max(samples), "samples_ms": samples}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--launch", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8813)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rounds", type=int, default=6)
    args = parser.parse_args()
    if not 2 <= args.rounds <= 30: parser.error("Use 2..30 paired rounds")
    args.output.mkdir(parents=True, exist_ok=False)
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", args.port)) == 0:
            raise RuntimeError("Private port occupied; existing renderer will not be touched")
    native = args.output/"native"
    native.mkdir()
    exe = native/args.launch.name
    shutil.copy2(args.launch, exe)
    shutil.copytree(args.launch.parent/"shaders", native/"shaders")
    base = f"http://127.0.0.1:{args.port}"
    checks, samples, phases = [], {"direct": [], "python": [], "batch": []}, []
    result = {"scope": "Experimental control overhead and tiny B2 GPU membrane parity, not whole-game qualification",
              "native_exe_source": str(args.launch), "native_exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest(),
              "fixture_sha256": hashlib.sha256((FIX/"manifest.json").read_bytes()).hexdigest(),
              "port": args.port, "checks": checks, "phases": phases,
              "environment": "Existing renderer, local model and Kimi transfer may run concurrently; hidden 640x360 window"}
    def check(name, passed, *, fatal=True, **details):
        checks.append(dict(name=name, passed=bool(passed), **details))
        if not passed and fatal: raise AssertionError(checks[-1])
    def direct(method, path, data=None):
        payload = json.dumps(data).encode() if data is not None else None
        status, raw = http_req(base, method, path, payload)
        if status != 200: raise NativeRefusal(f"HTTP {status}: {raw!r}")
        reply = json.loads(raw)
        if reply.get("ok") is False: raise NativeRefusal(str(reply))
        return reply
    proc = None
    try:
        with (args.output/"native.stdout.log").open("wb") as stdout, (args.output/"native.stderr.log").open("wb") as stderr:
            proc = subprocess.Popen([str(exe), str(args.port), "--hidden", "640", "360", "--no-restore"],
                                    cwd=native, stdout=stdout, stderr=stderr,
                                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            result["owned_pid"] = proc.pid
            ready = False
            for _ in range(150):
                if proc.poll() is not None: raise RuntimeError(f"Private native engine exited: {proc.returncode}")
                try:
                    direct("GET", "/matter"); ready = True; break
                except (OSError, RuntimeError): time.sleep(.2)
            if not ready: raise RuntimeError("Private native readiness timeout")
            with EngineControl(base) as engine:
                fixture = load_b2()
                initial = unwrap(engine.membrane.upload(md01_packet(fixture, 1.0)))
                check("fixture_energy", abs(initial["energy"]-fixture["E_ref"]) < 2e-6,
                      native=initial["energy"], reference=fixture["E_ref"])
                doubled = unwrap(engine.membrane.tension(2.0))
                check("material_tension_changes_native_energy", abs(doubled["energy"]-2*initial["energy"]) < 4e-6)
                check("material_tension_changes_native_force", abs(doubled["centre_force"][2]-2*initial["centre_force"][2]) < 2e-6)
                engine.membrane.reset()
                # No per-frame vertices go through Python; all relaxation stays native.
                check("native_relaxation_moves_matter", unwrap(engine.membrane.step())["centre"][2] < initial["centre"][2])
                engine.membrane.reset()
                telemetry_idle = []
                for _ in range(6):
                    time.sleep(.25); telemetry_idle.append(engine.telemetry())
                result["idle_native_telemetry"] = telemetry_idle
                # Fast read-only route separates wrapper cost from GPU/frame scheduling.
                reads = {"direct": [], "python": []}
                for i in range(200):
                    order = ("direct", "python") if i % 2 == 0 else ("python", "direct")
                    for mode in order:
                        start=time.perf_counter_ns()
                        reply = direct("GET", "/matter") if mode == "direct" else engine.matter.state()
                        reads[mode].append((time.perf_counter_ns()-start)/1e6)
                result["readonly_request"] = {k: summary(v) for k,v in reads.items()}
                check("readonly_wrapper_overhead_below_1ms",
                      statistics.median(reads["python"])-statistics.median(reads["direct"]) <= 1.0, fatal=False)
                rng = random.Random(20261013)
                for round_index in range(args.rounds):
                    order = ["direct", "python", "batch"]; rng.shuffle(order)
                    states = {}
                    for mode in order:
                        engine.membrane.reset()
                        start=time.perf_counter_ns()
                        if mode == "batch": reply=engine.membrane.step(12)
                        else:
                            for _ in range(12):
                                reply = direct("POST", "/membrane_demo", {"op":"step","n_steps":1}) if mode == "direct" else engine.membrane.step()
                        duration = (time.perf_counter_ns()-start)/1e6
                        samples[mode].append(duration)
                        states[mode]=unwrap(reply)
                        phases.append({"round":round_index,"mode":mode,"elapsed_ms":duration,
                                       "state":states[mode],"native_telemetry":engine.telemetry()})
                    reference=states["direct"]
                    for mode in ("python", "batch"):
                        candidate=states[mode]
                        check(f"round_{round_index}_{mode}_physics_parity",
                              candidate["iteration"]==reference["iteration"] and
                              abs(candidate["energy"]-reference["energy"]) < 2e-6 and
                              max(abs(a-b) for a,b in zip(candidate["centre"],reference["centre"])) < 1e-7 and
                              candidate["accepted_state_id"]==reference["accepted_state_id"] and
                              max(abs(a-b) for a,b in zip(candidate["centre_force"],reference["centre_force"])) < 2e-6,
                              iteration=candidate["iteration"], accepted_state_id=candidate["accepted_state_id"])
                result["native_12_steps"]={k:summary(v) for k,v in samples.items()}
                result["batch_speedup_vs_direct"]=statistics.median(samples["direct"])/statistics.median(samples["batch"])
                check("batch_faster_than_12_http_steps", result["batch_speedup_vs_direct"] > 1)
                scenario=json.loads((Path(__file__).parent/"membrane_experiment.json").read_text())
                result["scenario_results"]=run_scenario(engine,scenario)
                (args.output/"native-frame.png").write_bytes(engine.frame())
                check("native_frame_captured", (args.output/"native-frame.png").stat().st_size > 100)
                result["final_native_telemetry"]=engine.telemetry()
                # Exercise the actual construction/rigid-physics scene as well.
                from tools.construction_packet.b2_scene_gen import make_stack, box_document
                engine.assembly.admit(make_stack())
                engine.assembly.pause()
                check("native_assembly_three_material_parts", len(engine.assembly.state()["parts"]) == 3)
                part=box_document("python_block", .34, .40, -.01, .03, .12, .18, 600, .3)
                engine.assembly.place(part)
                check("python_places_reusable_native_part", len(engine.assembly.state()["parts"]) == 4)
                before_hash=engine.assembly.state_hash()
                try: engine.assembly.place(part)
                except NativeRefusal: refused=True
                else: refused=False
                check("duplicate_part_refused_atomically", refused and engine.assembly.state_hash()==before_hash)
                engine.assembly.patch(id="python_block", mu=.4)
                check("material_patch_changes_native_state", engine.assembly.state_hash()!=before_hash)
                engine.assembly.remove("python_block")
                check("native_part_removal", len(engine.assembly.state()["parts"])==3)
                engine.assembly.pause(False)
                clock_before=engine.assembly.clock()
                time.sleep(.2)
                clock_after=engine.assembly.clock()
                check("physics_clock_advances_without_python_stepping", clock_after["sim_s"] > clock_before["sim_s"])
                result["assembly_clock_before"]=clock_before
                result["assembly_clock_after"]=clock_after
                engine.assembly.pause()
                # Same paused native scene, same polling workload, alternate order.
                frame_phases=[]
                for mode in ["direct","python","python","direct"]:
                    first=engine.telemetry();wall=time.perf_counter();timings=[]
                    while time.perf_counter()-wall < 1.0:
                        t=time.perf_counter_ns()
                        if mode=="direct": direct("GET","/tick_b2_state")
                        else: engine.assembly.state()
                        timings.append((time.perf_counter_ns()-t)/1e6)
                        time.sleep(.01)
                    last=engine.telemetry();new=last["pushes"]-first["pushes"]
                    ring=last["ring"][-min(new,len(last["ring"])):] if new else []
                    frame_phases.append({"mode":mode,"wall_s":time.perf_counter()-wall,
                         "requests":len(timings),"request_ms":summary(timings),"native_frame_ms":ring,
                         "frame_sample_count":len(ring),"native_fps_reported":last["fps"]})
                result["assembly_frame_comparison"]=frame_phases
                medians={mode: statistics.median([x for phase in frame_phases if phase["mode"]==mode
                         for x in phase["native_frame_ms"]]) for mode in ["direct","python"]}
                result["native_frame_median_ms"]=medians
                result["native_frame_change_percent"]=(medians["python"]/medians["direct"]-1)*100
                result["frame_regression_exceeds_preregistered_10_percent"]=result["native_frame_change_percent"]>10
                (args.output/"native-assembly.png").write_bytes(engine.frame())
                result["passed"]=all(c["passed"] for c in checks)
    except Exception as error:
        result.update(passed=False, error=repr(error))
        raise
    finally:
        if proc and proc.poll() is None:
            proc.terminate()
            try: proc.wait(timeout=10)
            except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=5)
        (args.output/"receipt.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"passed":result["passed"],"receipt":str(args.output/"receipt.json"),
                      "readonly_request":{k: v["median_ms"] for k,v in result["readonly_request"].items()},
                      "native_12_steps":{k: v["median_ms"] for k,v in result["native_12_steps"].items()},
                      "batch_speedup":result["batch_speedup_vs_direct"]},indent=2))

if __name__ == "__main__": main()
