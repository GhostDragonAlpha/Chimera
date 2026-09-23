# build_d41.ps1 -- the tick-41 device drill DLL (closeout-8).
$nvcc = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin\nvcc.exe"
$cl = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\cl.exe"
$here = "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu"
Set-Location -LiteralPath $here
& $nvcc -shared -arch=sm_89 -lineinfo -fmad=false -ccbin $cl -I. -std=c++17 -DUCRT_MATH_DEVICE --expt-relaxed-constexpr walker_env_d41.cu -o walker_env_d41.dll -Xcompiler "/EHsc" 2>&1 | Out-File -Encoding utf8 build_d41.log
"NVCC_EXIT=$LASTEXITCODE"
