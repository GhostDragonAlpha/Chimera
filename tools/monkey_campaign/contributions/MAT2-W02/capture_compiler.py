#!/usr/bin/env python -B
"""MAT2-W02 toolchain identity capture (CPU-only, no compilation of pinned sources).

Records which compiler the frozen gate actually used: the vcvars64.bat path selected by the
reused driver, `where cl.exe`, and the `cl /Bv` banner. Written to
../build_gate/compiler_identity.txt so the numerical receipt names its toolchain instead of
assuming it matches any earlier attempt's compiler.
"""
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ATTEMPT_ROOT = HERE.parents[4]
BUILD = ATTEMPT_ROOT / "build_gate"

VCVARS_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat",
    r"C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat",
]


def main():
    vcvars = next((v for v in VCVARS_CANDIDATES if Path(v).is_file()), None)
    if vcvars is None:
        print("NO_COMPILER_FOUND")
        return 1
    bat = BUILD / "capture_compiler.bat"
    text = "\r\n".join(["@echo off",
                       f'call "{vcvars}" >nul 2>&1',
                       "where cl.exe",
                       "cl /Bv 2>&1"]) 
    bat.write_bytes((text + "\r\n").encode("ascii"))
    proc = subprocess.run(["cmd", "/c", str(bat)], cwd=str(BUILD),
                          capture_output=True, text=True, shell=False)
    out = (proc.stdout or "") + (proc.stderr or "")
    record = BUILD / "compiler_identity.txt"
    record.write_text(f"vcvars64.bat: {vcvars}\nexit: {proc.returncode}\n{out}", encoding="utf-8")
    print(record.read_text(encoding="utf-8")[:1200])
    return 0 if proc.returncode == 0 else 1


if __name__ == "__main__":
    main()
