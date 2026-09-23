# extract_ucrt_math2.ps1 -- closeout-5: extract lsincos_array.obj (the
# __Lsinarray/__Lcosarray polynomial tables) + the remaining math objects.
# Trailer Agent: GLM 5.3.
$ErrorActionPreference = "Continue"
$here = "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu"
Set-Location -LiteralPath (Join-Path $here "ucrt_objs")
$log = "../co5_ucrt_extract2.log"
$libexe = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\lib.exe"
$libucrt = "C:\Program Files (x86)\Windows Kits\10\Lib\10.0.26100.0\ucrt\x64\libucrt.lib"
$noti = "d:\os\obj\amd64fre\minkernel\crts\ucrt\src\appcrt\dll\mt\..\..\tran"
# (member suffix dir, member name, out name)
$pairs = @(
  @("mt\objfre\amd64", "lsincos_array.obj", "lsincos_array_mt.obj"),
  @("noti386\mt\objfre\amd64", "hypot.obj", "hypot_mt.obj")
)
foreach ($p in $pairs) {
  $member = "$noti\$($p[0])\$($p[1])"
  & $libexe ("/extract:" + $member) ("/out:" + $p[2]) $libucrt 2>&1 | Out-File -Append -Encoding utf8 $log
}
Get-ChildItem *.obj | ForEach-Object { "{0} {1}" -f $_.Name, $_.Length } | Tee-Object -FilePath $log -Append
"EXIT=$LASTEXITCODE"
