# build_dll2.ps1 -- rebuild walker_env.dll (final fix set: fk_eval seed +
# chain propagation + pre-update product law + store-bisection slot).
$nvcc = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin\nvcc.exe"
$cl = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\cl.exe"
$here = "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu"
Set-Location -LiteralPath $here
& $nvcc -shared -arch=sm_89 -lineinfo -ccbin $cl -I. -std=c++17 --expt-relaxed-constexpr walker_env.cu -o walker_env.dll -Xcompiler "/EHsc" 2>&1 | Out-File -Encoding utf8 build_dll9.log
"NVCC_EXIT=$LASTEXITCODE"
