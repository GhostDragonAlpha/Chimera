# build_cpp_drill.ps1 -- rebuild the C++ reference drill side (closeout-8).
$here = "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu"
Set-Location -LiteralPath $here
$vcvars = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
cmd /v /c "call ""$vcvars"" >nul 2>&1 && cd /d $here && cl /nologo /O2 /EHsc /std:c++17 /I engine_inc cpp_substep_probe_instr.cpp /Fe:cpp_substep_probe_instr.exe" 2>&1 | Out-File -Encoding utf8 build_cpp_drill.log
"EXIT=$LASTEXITCODE"
Get-Content build_cpp_drill.log | Select-String -Pattern "error" | Select-Object -First 8
