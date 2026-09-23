# extract_ucrt_math.ps1 -- closeout-5 Target B route (2): extract the ACTUAL
# UCRT math objects (sin/cos/atan2/acos/hypot, SSE2 + FMA variants) from the
# static libucrt.lib the reference links, for disassembly and constant
# extraction. The DLL/lib on disk is the ground truth. Trailer Agent: GLM 5.3.
$ErrorActionPreference = "Continue"
$here = "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu"
Set-Location -LiteralPath $here
$log = "co5_ucrt_extract.log"
$libexe = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\lib.exe"
$libucrt = "C:\Program Files (x86)\Windows Kits\10\Lib\10.0.26100.0\ucrt\x64\libucrt.lib"
New-Item -ItemType Directory -Force -Path ucrt_objs | Out-Null
Set-Location -LiteralPath (Join-Path $here "ucrt_objs")
# the exact member names as lib.exe //LIST printed them (backslash form)
$members = @{
  "sin.obj"   = "sin_mt.obj"
  "cos.obj"   = "cos_mt.obj"
}
$noti = "d:\os\obj\amd64fre\minkernel\crts\ucrt\src\appcrt\dll\mt\..\..\tran"
foreach ($k in $members.Keys) {
  $member = "$noti\mt\objfre\amd64\$k"
  & $libexe ("/extract:" + $member) ("/out:" + $members[$k]) $libucrt 2>&1 | Out-File -Append -Encoding utf8 $log
}
foreach ($k in $members.Keys) {
  $member = "$noti\noti386\mt_fma\objfre\amd64\$k"
  $out = $members[$k].Replace("_mt.obj", "_fma.obj")
  & $libexe ("/extract:" + $member) ("/out:" + $out) $libucrt 2>&1 | Out-File -Append -Encoding utf8 $log
}
$fmas = @("atan2.obj", "acos.obj", "hypot.obj")
foreach ($k in $fmas) {
  $member = "$noti\noti386\mt\objfre\amd64\$k"
  $out = $k.Replace(".obj", "_mt.obj")
  & $libexe ("/extract:" + $member) ("/out:" + $out) $libucrt 2>&1 | Out-File -Append -Encoding utf8 $log
  $member = "$noti\noti386\mt_fma\objfre\amd64\$k"
  $out = $k.Replace(".obj", "_fma.obj")
  & $libexe ("/extract:" + $member) ("/out:" + $out) $libucrt 2>&1 | Out-File -Append -Encoding utf8 $log
}
Get-ChildItem *.obj | ForEach-Object { "{0} {1}" -f $_.Name, $_.Length } | Tee-Object -FilePath $log -Append
"EXIT=$LASTEXITCODE"
