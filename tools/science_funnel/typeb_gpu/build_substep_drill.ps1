# build_substep_drill.ps1 -- build the per-substep byte-match drill pair:
#   cpp_substep_probe_instr.exe (C++ reference side, SUBFULL prints)
#   substep_probe.exe           (translated-kernels host replay side, SUBFULL prints)
# Both cl /fp:precise (default) -- isolates SOURCE-ORDER differences from the
# nvcc contraction question. Trailer Agent: GLM 5.3.
$ErrorActionPreference = "Continue"
$here = "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu"
Set-Location -LiteralPath $here
$log = "build_substep_drill.log"
$vcvars = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
cmd /v /c "call ""$vcvars"" >nul 2>&1 && cd /d $here && cl /nologo /O2 /EHsc /std:c++17 /I engine_inc cpp_substep_probe_instr.cpp /Fe:cpp_substep_probe_instr.exe && cl /nologo /O2 /EHsc /I host_shim substep_probe.cxx /Fe:substep_probe.exe" 2>&1 | Out-File -Encoding utf8 $log
"EXIT=$LASTEXITCODE"
Get-Content $log -Tail 6
