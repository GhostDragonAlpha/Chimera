# build_substep_hostonly.ps1 -- rebuild only the kernels host replay
# (substep_probe.exe) after a probe_kernels.cuh regeneration. The C++ drill
# side is unchanged (it is the reference). Trailer Agent: GLM 5.3.
$ErrorActionPreference = "Continue"
$here = "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu"
Set-Location -LiteralPath $here
$log = "build_substep_xfix.log"
$vcvars = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
cmd /v /c "call ""$vcvars"" >nul 2>&1 && cd /d $here && cl /nologo /O2 /EHsc /I host_shim substep_probe.cxx /Fe:substep_probe.exe" 2>&1 | Out-File -Encoding utf8 $log
"EXIT=$LASTEXITCODE"
Get-Content $log -Tail 4
