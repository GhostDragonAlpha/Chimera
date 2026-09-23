# build_co5_fdlibm.ps1 -- closeout-5: build the fdlibm host probe (route 1 of
# Target B): the netlib fdlibm sources + trig_fdlibm.cxx driver under the same
# cl/UCRT the reference uses. /fp:precise (default); no fast-math anywhere.
# Trailer Agent: GLM 5.3.
$ErrorActionPreference = "Continue"
$here = "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu"
Set-Location -LiteralPath $here
$log = "build_co5_fdlibm.log"
$vcvars = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
cmd /v /c "call ""$vcvars"" >nul 2>&1 && cd /d $here && cl /nologo /O2 /EHsc /D__LITTLE_ENDIAN /I fdlibm_ref trig_fdlibm.cxx fdlibm_ref\s_sin.c fdlibm_ref\s_cos.c fdlibm_ref\e_atan2.c fdlibm_ref\e_acos.c fdlibm_ref\e_hypot.c fdlibm_ref\e_rem_pio2.c fdlibm_ref\k_rem_pio2.c fdlibm_ref\k_sin.c fdlibm_ref\k_cos.c /Fe:trig_fdlibm.exe" 2>&1 | Out-File -Encoding utf8 $log
"EXIT=$LASTEXITCODE"
Get-Content $log -Tail 8
