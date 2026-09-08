#!/usr/bin/env python3
"""STEP-GPU-02 mutation and stale-buffer verification.

Rule-0 membrane (preregistered before implementation):
STATEMENT: the standalone membrane probe detects each specified temporary
mutation through a numerical or validity gate, while the unmodified control
passes.
PREDICTION: clean execution passes; six compiled/executed controls are
rejected on WSL Vulkan, including true stale-buffer reuse.
FALSIFIER: a clean failure, compile-only "detection", accepted mutation, or
accepted stale output falsifies the claim.

This controller never edits committed fixtures or production probe sources.
Each source mutation is built from a temporary copied probe tree. The stale
control uses the probe's explicit test mode and reuses one uploaded buffer.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools" / "membrane_gpu_probe"
FIXTURES = ROOT / "docs" / "evidence" / "gpu_fixtures"
EVIDENCE = ROOT / "docs" / "evidence" / "membrane_gpu_mutations"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_hashes(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)).replace("\\", "/"): sha256(p)
            for p in sorted(root.rglob("*")) if p.is_file()}


def git(*args: str) -> tuple[str, int]:
    p = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True,
                       text=True)
    return (p.stdout or "") + ("\n[stderr]\n" + p.stderr if p.stderr else ""), p.returncode


def run(cmd: list[str], cwd: Path, raw: Path, timeout: int = 300) -> int:
    raw.parent.mkdir(parents=True, exist_ok=True)
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                           timeout=timeout)
        raw.write_text((p.stdout or "") +
                       ("\n[stderr]\n" + p.stderr if p.stderr else ""),
                       encoding="utf-8")
        return p.returncode
    except Exception as exc:
        raw.write_text(f"runner exception: {type(exc).__name__}: {exc}\n",
                       encoding="utf-8")
        return 127


def write_command(path: Path, cmd: list[str], cwd: Path) -> None:
    path.write_text("cwd: " + str(cwd) + "\ncommand: " +
                    " ".join(cmd) + "\n", encoding="utf-8")


def mutate_shader(path: Path, name: str) -> None:
    text = path.read_text(encoding="utf-8")
    replacements = {
        "reverse_force_sign": [
            ("vec4(-g * ga, 0.0)", "vec4(g * ga, 0.0)"),
            ("vec4(-g * gb, 0.0)", "vec4(g * gb, 0.0)"),
            ("vec4(-g * gc, 0.0)", "vec4(g * gc, 0.0)"),
        ],
        "permuted_corner_ownership": [
            ("out_face.corner0 = vec4(-g * ga, 0.0);\n    out_face.corner1 = vec4(-g * gb, 0.0);",
             "out_face.corner0 = vec4(-g * gb, 0.0);\n    out_face.corner1 = vec4(-g * ga, 0.0);"),
        ],
        "zero_force_positive_gamma": [
            ("out_face.corner0 = vec4(-g * ga, 0.0);\n    out_face.corner1 = vec4(-g * gb, 0.0);\n    out_face.corner2 = vec4(-g * gc, 0.0);",
             "out_face.corner0 = vec4(0.0);\n    out_face.corner1 = vec4(0.0);\n    out_face.corner2 = vec4(0.0);"),
        ],
        "incorrect_normal": [
            ("out_face.normal_area = vec4(n, area);",
             "out_face.normal_area = vec4(-n, area);"),
        ],
    }
    pairs = replacements.get(name, [])
    if not pairs:
        raise ValueError(f"not a shader mutation: {name}")
    for old, new in pairs:
        if old not in text:
            raise RuntimeError(f"mutation anchor absent for {name}: {old!r}")
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def mutate_fixture(path: Path) -> None:
    import numpy as np
    p = path / "b2" / "geometry" / "indices_u32.npy"
    arr = np.load(p, allow_pickle=False).copy()
    arr[0, 1] = arr[0, 0]
    np.save(p, arr, allow_pickle=False)


def source_manifest(source_root: Path, build_dir: Path, exe: Path, spv: Path) -> dict:
    return {
        "source_root": str(source_root),
        "source_hashes": tree_hashes(source_root),
        "executable": str(exe) if exe.exists() else None,
        "executable_sha256": sha256(exe) if exe.exists() else None,
        "spirv": str(spv) if spv.exists() else None,
        "spirv_sha256": sha256(spv) if spv.exists() else None,
        "build_dir": str(build_dir),
    }


def control(name: str, stamp_dir: Path, mutation: str | None,
            stale: bool = False) -> dict:
    out = stamp_dir / name
    out.mkdir(parents=True, exist_ok=False)
    shader_mutations = {"reverse_force_sign", "permuted_corner_ownership", "zero_force_positive_gamma", "incorrect_normal"}
    source_root = PROBE if mutation is None or mutation not in shader_mutations else out / "probe"
    fixture_root = FIXTURES if mutation != "invalid_face_gamma0" else out / "fixtures"
    if source_root != PROBE:
        shutil.copytree(PROBE, source_root)
        mutate_shader(source_root / "membrane.comp", mutation)  # type: ignore[arg-type]
    if fixture_root != FIXTURES:
        shutil.copytree(FIXTURES, fixture_root)
        mutate_fixture(fixture_root)
    build = out / "build"
    build.mkdir()
    configure = ["cmake", "-S", str(source_root), "-B", str(build)]
    write_command(out / "configure.command.txt", configure, ROOT)
    crc = run(configure, ROOT, out / "build_configure.txt")
    if crc == 0:
        build_cmd = ["cmake", "--build", str(build), "--parallel", "2"]
        write_command(out / "build.command.txt", build_cmd, ROOT)
        brc = run(build_cmd, ROOT, out / "build.txt")
    else:
        brc = crc
    exe = build / ("membrane_gpu_probe.exe" if os.name == "nt"
                   else "membrane_gpu_probe")
    spv = build / "membrane.comp.spv"
    result = {
        "name": name,
        "mutation": mutation or ("stale_buffer_reuse" if stale else "none"),
        "source_to_executable": source_manifest(source_root, build, exe, spv),
        "fixture_hashes": tree_hashes(fixture_root),
        "build": {"state": "PASS" if brc == 0 else "FAIL",
                  "exit_code": brc, "raw": str((out / "build.txt").relative_to(ROOT))
                  if (out / "build.txt").exists() else str((out / "build_configure.txt").relative_to(ROOT))},
    }
    if brc != 0 or not exe.exists() or not spv.exists():
        result["execution"] = {"state": "NOT_TESTED", "exit_code": None,
                                "reason": "compile/build did not produce runnable artifacts"}
        (out / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result
    args = [str(exe), "--fixtures", str(fixture_root), "--shader", str(spv)]
    if stale:
        args.append("--stale-reuse")
    write_command(out / "run.command.txt", args, ROOT)
    rrc = run(args, ROOT, out / "run.txt")
    raw = (out / "run.txt").read_text(encoding="utf-8", errors="replace")
    if stale:
        detected = rrc == 0 and "STALE_REUSE_RESULT DETECTED" in raw
    elif name == "clean":
        detected = rrc == 0 and "GPU_RESULT PASS" in raw
    elif name == "invalid_face_gamma0":
        detected = rrc != 0 and "validity=0" in raw and "FAIL" in raw
    else:
        detected = rrc != 0 and "GPU_RESULT FAIL" in raw and "GPU_RESULT NOT_TESTED" not in raw
    result["execution"] = {
        "state": "PASS" if detected else "FAIL",
        "exit_code": rrc,
        "detected": detected,
        "raw": str((out / "run.txt").relative_to(ROOT)),
        "compile_failure_is_detection": False,
    }
    (out / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    out = EVIDENCE / stamp
    out.mkdir(parents=True, exist_ok=False)
    status, _ = git("status", "--short", "--branch")
    head, _ = git("rev-parse", "HEAD")
    (out / "git_status.txt").write_text(status, encoding="utf-8")
    (out / "source_diff.txt").write_text(
        git("diff", "--", "tools/membrane_gpu_probe", "tools/run_membrane_verification.py")[0],
        encoding="utf-8")
    controls = [
        ("clean", None, False),
        ("reverse_force_sign", "reverse_force_sign", False),
        ("permuted_corner_ownership", "permuted_corner_ownership", False),
        ("zero_force_positive_gamma", "zero_force_positive_gamma", False),
        ("incorrect_normal", "incorrect_normal", False),
        ("invalid_face_gamma0", "invalid_face_gamma0", False),
        ("stale_buffer_reuse", None, True),
    ]
    results = [control(name, out, mutation, stale) for name, mutation, stale in controls]
    top = {
        "schema": "chimera-membrane-mutation-v1",
        "utc": stamp,
        "source_commit": head.strip(),
        "branch_and_status": status,
        "platform": platform.platform(),
        "python": sys.version,
        "preregistered": {
            "statement": "The standalone probe detects each specified temporary mutation through a numerical or validity gate, while the unmodified control passes.",
            "prediction": "Clean execution passes; six compiled/executed controls are rejected on WSL Vulkan, including true stale-buffer reuse.",
            "falsifier": "A clean failure, compile-only detection, accepted mutation, or accepted stale output falsifies the claim.",
        },
        "device_evidence": str(out / "clean" / "run.txt"),
        "controls": results,
        "all_pass": all(r["execution"]["state"] == "PASS" for r in results),
    }
    (out / "result.json").write_text(json.dumps(top, indent=2), encoding="utf-8")
    (out / "summary.md").write_text("# STEP-GPU-02 mutation verification\n\n" +
        "\n".join(f"- **{r['name']}:** {r['execution']['state']} "
                  f"(exit={r['execution'].get('exit_code')}, detected={r['execution'].get('detected')})"
                  for r in results) +
        f"\n- **Source:** `{head.strip()}`\n- **All controls:** `{top['all_pass']}`\n",
        encoding="utf-8")
    print(json.dumps({"evidence": str(out), "result": str(out / "result.json"),
                      "all_pass": top["all_pass"]}, indent=2))
    return 0 if top["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
