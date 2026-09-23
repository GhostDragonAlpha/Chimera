# extract_ucrt_math3.ps1 -- closeout-5: extract the FMA3-path reduction helper
# (remainder_piby2_forfma3.obj, which holds __remainder_piby2_fma3 and
# __remainder_piby2_fma3_bdl) plus the plain remainder_piby2.obj for reference.
# Trailer Agent: GLM 5.3.
$ErrorActionPreference = "Continue"
$here = "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu"
Set-Location -LiteralPath (Join-Path $here "ucrt_objs")
$log = "../co5_ucrt_extract3.log"
$libexe = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\lib.exe"
$libucrt = "C:\Program Files (x86)\Windows Kits\10\Lib\10.0.26100.0\ucrt\x64\libucrt.lib"
$noti = "d:\os\obj\amd64fre\minkernel\crts\ucrt\src\appcrt\dll\mt\..\..\tran"
$pairs = @(
  @("mt\objfre\amd64", "remainder_piby2_forfma3.obj", "rempiby2_fma3.obj"),
  @("noti386\mt\objfre\amd64", "remainder_piby2.obj", "rempiby2.obj")
)
foreach ($p in $pairs) {
  $member = "$noti\$($p[0])\$($p[1])"
  & $libexe ("/extract:" + $member) ("/out:" + $p[2]) $libucrt 2>&1 | Out-File -Append -Encoding utf8 $log
}
Get-ChildItem *.obj | ForEach-Object { "{0} {1}" -f $_.Name, $_.Length } | Tee-Object -FilePath $log -Append
"EXIT=$LASTEXITCODE"
