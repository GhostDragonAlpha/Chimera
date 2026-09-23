# build_ucrt_gate.ps1 -- compile the on-device UCRT gate (nvcc, sm_89, -fmad=false:
# the reconstruction carries its own explicit fma(); contraction must stay OFF).
$ErrorActionPreference = "Continue"
$here = "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu"
Set-Location -LiteralPath $here
$log = "build_ucrt_gate.log"
$nvcc = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin\nvcc.exe"
$vcvars = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
cmd /c "call ""$vcvars"" >nul 2>&1 && ""$nvcc"" -arch=sm_89 -O2 -fmad=false -Xcompiler ""/EHsc /utf-8"" ucrt_gate.cu -o ucrt_gate.exe" 2>&1 | Out-File -Encoding utf8 $log
"EXIT=$LASTEXITCODE"
Get-Content $log -Tail 8
