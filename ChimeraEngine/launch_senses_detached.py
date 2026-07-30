"""launch_senses_detached.py -- start the senses server with REAL file handles and the
CUDA vendor runtime on PATH.

Two hard-won fixes (2026-07-29):
1. PowerShell Start-Process -RedirectStandard* stalls the child on a full pipe once the
   starting shell exits. Python subprocess with open file handles writes to real OS files.
2. LM Studio's llama-server.exe dies instantly with STATUS_DLL_NOT_FOUND (0xC0000135) when
   launched bare -- LM Studio normally prepends its vendor CUDA runtime (cudart/cublas)
   to PATH when it spawns these binaries. We do the same. NOTE: the msys/git-bash loader
   misreports this as a missing api-ms-win-crt DLL; the real gap is the CUDA runtime dir.
"""
import os
import subprocess

BACKEND = r"C:\Users\allen\.lmstudio\extensions\backends\llama.cpp-win-x86_64-nvidia-cuda12-avx2-2.27.1"
VENDOR = r"C:\Users\allen\.lmstudio\extensions\backends\vendor\win-llama-cuda12-vendor-v2"
MODEL = r"C:\Users\allen\.lmstudio\models\unsloth\Qwen2.5-Omni-7B-GGUF\Qwen2.5-Omni-7B-Q4_K_M.gguf"
MMPROJ = r"C:\Users\allen\.lmstudio\models\unsloth\Qwen2.5-Omni-7B-GGUF\mmproj-F32.gguf"

cmd = [os.path.join(BACKEND, "llama-server.exe"),
       "-m", MODEL, "--mmproj", MMPROJ, "--no-mmproj-offload",
       "-ngl", "99", "--host", "127.0.0.1", "--port", "1235", "-c", "4096"]

env = dict(os.environ)
env["PATH"] = BACKEND + os.pathsep + VENDOR + os.pathsep + env.get("PATH", "")

DETACHED_PROCESS = 0x00000008
CREATE_NO_WINDOW = 0x08000000

with open("senses_out.log", "wb") as out, open("senses_err.log", "wb") as err:
    p = subprocess.Popen(cmd, stdout=out, stderr=err, env=env, cwd=BACKEND,
                         creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW)
print(f"launched pid={p.pid}")
