"""gpu_check.py - report CUDA/GPU readiness of the fleet venv, honestly.

Checks (in order): torch import, torch CUDA build, cuda.is_available(),
device name / capability / VRAM. When torch or CUDA is missing, prints the
exact one-command operator action (we never install silently).

    python tools/gpu_check.py [--json]
"""
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_PY = Path(r"E:\PythonChimera\.venv-hy3d\Scripts\python.exe")

ONE_COMMAND_INSTALL = (
    "pip install torch --index-url https://download.pytorch.org/whl/cu124"
)


def check():
    info = {"venv_python": str(DEFAULT_PY if DEFAULT_PY.exists() else sys.executable)}
    try:
        import torch
    except Exception as exc:  # ImportError or broken install
        info.update({
            "torch": "missing",
            "cuda_available": False,
            "needed": ONE_COMMAND_INSTALL,
            "note": "one-command operator action; do not install silently",
            "error": f"{type(exc).__name__}: {exc}",
        })
        return info, 1
    info["torch"] = torch.__version__
    info["torch_cuda_build"] = torch.version.cuda
    available = bool(torch.cuda.is_available())
    info["cuda_available"] = available
    if available:
        props = torch.cuda.get_device_properties(0)
        info["device_name"] = props.name
        info["cuda_capability"] = f"{props.major}.{props.minor}"
        info["total_vram_gb"] = round(props.total_memory / 2**30, 2)
        free, total = torch.cuda.mem_get_info(0)
        info["free_vram_gb"] = round(free / 2**30, 2)
        info["multiprocessors"] = props.multi_processor_count
    else:
        info["needed"] = ONE_COMMAND_INSTALL
        info["note"] = "torch present but CUDA unavailable; check driver"
    return info, 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args()
    info, rc = check()
    print(json.dumps(info, indent=2))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
