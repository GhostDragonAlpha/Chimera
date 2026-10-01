import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SRC = "ChimeraEngine/engine/tests_p1"
BUILD = ".tmp/p1_inventory_build"
EXE = Path(ROOT) / BUILD / "Release" / "test_p1_inventory.exe"
RESULT = Path(ROOT) / ".tmp" / "p1_inventory_result.txt"


def _run(cmd):
    return subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)


def build_and_run():
    if shutil.which("cmake") is None:
        raise RuntimeError("cmake not found on PATH")
    r = _run(["cmake", "-S", SRC, "-B", BUILD,
              "-G", "Visual Studio 17 2022", "-A", "x64"])
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        raise RuntimeError(f"cmake configure failed rc={r.returncode}")
    r = _run(["cmake", "--build", BUILD, "--config", "Release"])
    print(r.stdout[-20000:])
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        raise RuntimeError(f"cmake build failed rc={r.returncode}")
    if not EXE.exists():
        raise RuntimeError(f"test exe missing: {EXE}")
    r = subprocess.run([str(EXE), str(RESULT)], cwd=str(ROOT),
                       capture_output=True, text=True)
    print(r.stdout)
    if r.stderr:
        print(r.stderr, file=sys.stderr)
    return r


def test_p1_inventory():
    r = build_and_run()
    assert r.returncode == 0, (
        f"test_p1_inventory failed rc={r.returncode} "
        f"(see {RESULT} and stdout above)")


if __name__ == "__main__":
    sys.exit(build_and_run().returncode)
