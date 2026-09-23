# build_co5_hostloop.ps1 -- closeout-5: rebuild the plain host replay
# (host_loop.exe from walker_kernels.cuh) with the working quoting pattern
# (build_host_loop.ps1's nested-quote form broke the vcvars environment).
# Trailer Agent: GLM 5.3.
$ErrorActionPreference = "Continue"
$here = "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu"
Set-Location -LiteralPath $here
$log = "build_co5_hostloop.log"
$vcvars = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
cmd /v /c "call ""$vcvars"" >nul 2>&1 && cd /d $here && cl /nologo /O2 /EHsc /I host_shim host_loop.cxx /Fe:host_loop.exe" 2>&1 | Out-File -Encoding utf8 $log
"EXIT=$LASTEXITCODE"
Get-Content $log -Tail 4
