# build_co5_drill_cdb.ps1 -- closeout-5: rebuild the instrumented host replay
# with /Zi (PDB) so cdb can name the tick-42 faulting source line. No source
# change: same probe_kernels.cuh, same driver. Trailer Agent: GLM 5.3.
$ErrorActionPreference = "Continue"
$here = "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu"
Set-Location -LiteralPath $here
$log = "build_co5_drill_cdb.log"
$vcvars = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
cmd /v /c "call ""$vcvars"" >nul 2>&1 && cd /d $here && cl /nologo /O2 /EHsc /Zi /I host_shim substep_probe.cxx /Fe:substep_probe_cdb.exe" 2>&1 | Out-File -Encoding utf8 $log
"EXIT=$LASTEXITCODE"
Get-Content $log -Tail 4
