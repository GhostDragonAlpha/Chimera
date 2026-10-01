# install_torch_cuda.ps1 - ONE-COMMAND OPERATOR ACTION (not run by agents).
#
# Installs the CUDA-enabled PyTorch build into the fleet venv. Only needed if
# tools/gpu_check.py reports torch missing or CUDA unavailable.
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\install_torch_cuda.ps1
param(
    [string]$Python = "E:\PythonChimera\.venv-hy3d\Scripts\python.exe"
)
& $Python -m pip install torch --index-url https://download.pytorch.org/whl/cu124
& $Python tools\gpu_check.py
