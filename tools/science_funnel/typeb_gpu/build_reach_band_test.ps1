$here = "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu"
Set-Location -LiteralPath $here
$vcvars = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
cmd /v /c "call ""$vcvars"" >nul 2>&1 && cd /d $here && cl /nologo /O2 /fp:precise /EHsc reach_band_test.c /Fe:reach_band_test.exe" 2>&1 | Out-File -Encoding utf8 build_reach_band_test.log
"EXIT=$LASTEXITCODE"
