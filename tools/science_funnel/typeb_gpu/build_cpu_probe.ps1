# build_cpu_probe.ps1 -- rebuild the C++ reference walk driver (closeout-8).
$here = "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu"
Set-Location -LiteralPath $here
$vcvars = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
cmd /v /c "call ""$vcvars"" >nul 2>&1 && cd /d $here && cl /nologo /O2 /EHsc /std:c++17 /I engine_inc cpu_probe.cpp /Fe:cpu_probe.exe" 2>&1 | Out-File -Encoding utf8 build_cpu_probe.log
"EXIT=$LASTEXITCODE"
Get-Content build_cpu_probe.log -Tail 3
