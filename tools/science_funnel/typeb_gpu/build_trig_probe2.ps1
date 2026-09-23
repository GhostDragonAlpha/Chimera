# build_trig_probe2.ps1 -- the ucrt_math reconstruction adoption probe.
# Trailer Agent: GLM 5.3.
$ErrorActionPreference = "Continue"
$here = "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu"
Set-Location -LiteralPath $here
$log = "build_trig_probe2.log"
$vcvars = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
cmd /v /c "call ""$vcvars"" >nul 2>&1 && cd /d $here && cl /nologo /O2 /fp:precise /EHsc ucrt_math.c trig_probe2_host.cxx /Fe:trig_probe2_host.exe" 2>&1 | Out-File -Encoding utf8 $log
"EXIT=$LASTEXITCODE"
Get-Content $log -Tail 4
