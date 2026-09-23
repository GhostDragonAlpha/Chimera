$here = "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu"
Set-Location -LiteralPath $here
$vcvars = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
cmd /v /c "call ""$vcvars"" >nul 2>&1 && cd /d $here && cl /nologo /O2 /fp:precise /EHsc /D__host__= /D__device__= ucrt_sweep2.c /Fe:ucrt_sweep2.exe" 2>&1 | Out-File -Encoding utf8 build_ucrt_sweep.log
"EXIT=$LASTEXITCODE"
