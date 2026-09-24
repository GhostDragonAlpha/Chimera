@echo off
rem build_gpu_probe.cmd -- GPU-leg build of the TIE2 boundary harness.
rem BROKER-GATED BUILD+RUN: nvcc compilation itself is CPU-side, but the whole
rem step is queued behind the broker because it is GPU-lane work; run only with
rem broker clearance (never during the operator's gaming session).
rem Mirrors the frozen build_dll_v2.ps1 flags. Trailer: Agent: GLM 5.3
set HERE=%~dp0
set FROZEN=E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu
"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin\nvcc.exe" -shared=no -arch=sm_89 -lineinfo -fmad=false -ccbin "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\cl.exe" -I"%FROZEN%" -std=c++17 -DUCRT_MATH_DEVICE --expt-relaxed-constexpr "%HERE%tie_boundary_probe_gpu.cu" -o "%HERE%tie_boundary_probe_gpu.exe" -Xcompiler "/EHsc" 2>&1
echo NVCC_EXIT=%ERRORLEVEL%
