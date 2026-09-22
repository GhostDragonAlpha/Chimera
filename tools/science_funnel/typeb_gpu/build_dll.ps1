# build_dll.ps1 -- rebuild walker_env.dll from the regenerated walker_kernels.cuh.
# Toolchain per TAKEOVER_HANDOFF (CUDA 12.8 + VS2022 BuildTools cl, sm_89).
$nvcc = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin\nvcc.exe"
$cl = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\cl.exe"
$here = "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu"
Set-Location -LiteralPath $here
Copy-Item walker_env.dll walker_env.dll.pre_chainfix -Force
# -fmad=false: the byte-match lever (closeout-2). The cl-compiled reference
# (/fp:precise) never contracts a*b+c; nvcc's default fmad=true does, which
# flips the degenerate cone-mask/lam decisions the walk rides on.
& $nvcc -shared -arch=sm_89 -lineinfo -fmad=false -ccbin $cl -I. -std=c++17 --expt-relaxed-constexpr walker_env.cu -o walker_env.dll -Xcompiler "/EHsc" 2>&1 | Out-File -Encoding utf8 build_dll_fmad0.log
"NVCC_EXIT=$LASTEXITCODE"
Get-Content build_dll8.log -Tail 4
