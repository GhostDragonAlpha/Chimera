#!/usr/bin/env python3
"""Reproducible membrane CPU/GPU verification runner.

Normal mode never starts, stops, replaces, or contacts the engine. It creates a
unique evidence directory, records source/toolchain/device/hash metadata,
runs the frozen CPU verifier separately, builds the standalone Vulkan probe
outside ChimeraEngine/engine/build/, then runs the probe if the host can launch
it. GPU launch failures are recorded as NOT_TESTED, never as PASS.

Engine-window mode is manifest-only: --engine-window <manifest.json> validates
an operator-created scoped-session manifest and copies no captures. The runner
never exposes or calls the engine HTTP API.
"""
from __future__ import annotations
import argparse, hashlib, json, os, platform, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools" / "membrane_gpu_probe"
EVIDENCE = ROOT / "docs" / "evidence" / "membrane_gpu_probe"

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def run(cmd, cwd, out, env=None):
    try:
        p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=180)
        out.write_text((p.stdout or "") + ("\n[stderr]\n" + p.stderr if p.stderr else ""), encoding="utf-8")
        return p.returncode
    except Exception as e:
        out.write_text(f"runner exception: {type(e).__name__}: {e}\n", encoding="utf-8")
        return 127

def git(*args):
    p = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    return p.stdout, p.returncode

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine-window", type=Path, help="operator-created scoped-session manifest; no API is contacted")
    args = ap.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    outdir = EVIDENCE / stamp
    outdir.mkdir(parents=True, exist_ok=False)
    result = {"schema":"chimera-membrane-verification-v1", "utc":stamp,
              "repository":str(ROOT), "engine_window":"NOT_TESTED", "checks":{}}
    head,_ = git("rev-parse","HEAD"); result["source_commit"] = head.strip()
    status,_ = git("status","--short","--branch"); (outdir/"git_status.txt").write_text(status, encoding="utf-8")
    result["tracked_modifications"] = status
    result["toolchain"] = {"python":sys.version, "platform":platform.platform(),
        "cmake":shutil.which("cmake"), "glslc":shutil.which("glslc"),
        "compiler":shutil.which("g++") or shutil.which("c++")}
    for cmd,name in [(["vulkaninfo","--summary"],"vulkaninfo_summary.txt"),(["cmake","--version"],"cmake_version.txt"),(["glslc","--version"],"glslc_version.txt")]:
        if shutil.which(cmd[0]): run(cmd, ROOT, outdir/name)
    result["vulkan_device_evidence"] = str(outdir/"vulkaninfo_summary.txt") if (outdir/"vulkaninfo_summary.txt").exists() else "NOT_TESTED"
    result["files"] = {}
    for p in [PROBE/"probe.cpp", PROBE/"membrane.comp", PROBE/"CMakeLists.txt", ROOT/"tools/gpu_fixtures_verify.py"]:
        result["files"][str(p.relative_to(ROOT))] = sha256(p)
    cpu = outdir/"cpu_reference.txt"
    rc = run([sys.executable,"tools/gpu_fixtures_verify.py"], ROOT, cpu)
    result["checks"]["cpu_reference"] = {"state":"PASS" if rc==0 else "FAIL", "exit_code":rc, "raw":str(cpu.relative_to(ROOT))}
    builddir = ROOT/".tmp"/"membrane_gpu_probe_runner"/stamp
    builddir.mkdir(parents=True, exist_ok=False)
    brc = run(["cmake","-S",str(PROBE),"-B",str(builddir),"-G","MinGW Makefiles"], ROOT, outdir/"build_configure.txt") if shutil.which("cmake") else 127
    if brc == 0: brc = run(["cmake","--build",str(builddir),"--parallel","2"], ROOT, outdir/"build.txt")
    exe = builddir/"membrane_gpu_probe.exe"; spv=builddir/"membrane.comp.spv"
    result["checks"]["build"] = {"state":"PASS" if brc==0 else "FAIL", "exit_code":brc}
    if exe.exists(): result["files"][str(exe.relative_to(ROOT))] = sha256(exe)
    if spv.exists(): result["files"][str(spv.relative_to(ROOT))] = sha256(spv)
    gpu_env = os.environ.copy()
    mingw_bin = Path("C:/ProgramData/mingw64/mingw64/bin")
    if mingw_bin.exists():
        gpu_env["PATH"] = str(mingw_bin) + os.pathsep + gpu_env.get("PATH", "")
    if brc==0 and exe.exists() and spv.exists():
        grc=run([str(exe),"--fixtures",str(ROOT/"docs/evidence/gpu_fixtures"),"--shader",str(spv)],ROOT,outdir/"gpu_comparison.txt",gpu_env)
        state="PASS" if grc==0 else ("NOT_TESTED" if grc==127 else "FAIL")
        result["checks"]["gpu_comparison"]={"state":state,"exit_code":grc,"raw":str((outdir/"gpu_comparison.txt").relative_to(ROOT))}
    else: result["checks"]["gpu_comparison"]={"state":"NOT_TESTED","exit_code":None,"reason":"build did not produce executable"}
    if args.engine_window:
        data=json.loads(args.engine_window.read_text(encoding="utf-8")); result["engine_window"]={"state":"RECORDED","manifest":str(args.engine_window),"camera_ids":data.get("camera_ids",[]),"state_ids":data.get("state_ids",[]),"captures":data.get("captures",[])}
    (outdir/"result.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    summary=outdir/"summary.md"; summary.write_text("# Membrane verification\n\n"+"\n".join(f"- **{k}:** {v['state']} (exit={v.get('exit_code')})" for k,v in result["checks"].items())+f"\n- **Engine window:** {result['engine_window']}\n- **Source:** `{result['source_commit']}`\n",encoding="utf-8")
    print(json.dumps({"evidence":str(outdir),"result":str(outdir/"result.json"),"checks":result["checks"]},indent=2))
    return 0 if all(v["state"]=="PASS" for v in result["checks"].values()) else 1
if __name__ == "__main__": raise SystemExit(main())
