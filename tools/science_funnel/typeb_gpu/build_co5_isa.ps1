# build_co5_isa.ps1 -- build the ISA-dispatch check. Trailer Agent: GLM 5.3.
$ErrorActionPreference = "Continue"
$here = "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu"
Set-Location -LiteralPath $here
$log = "build_co5_isa.log"
$vcvars = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
cmd /v /c "call ""$vcvars"" >nul 2>&1 && cd /d $here && cl /nologo /O2 /EHsc ucrt_sin_probe.cxx /Fe:ucrt_isa_check.exe" 2>&1 | Out-File -Encoding utf8 $log
"EXIT=$LASTEXITCODE"
Get-Content $log -Tail 4
