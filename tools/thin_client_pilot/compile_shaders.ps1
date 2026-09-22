# thincli lane: compile this worktree's shader sources to SPIR-V next to the
# staged engine exe, mirroring the CMakeLists derived-shader rule:
#   every .vert/.frag/.comp/.glsl in ChimeraEngine/engine/shaders/ compiles;
#   naming: stem.spv for comp/glsl stages, name.spv (with extension) otherwise.
$ErrorActionPreference = "Stop"
$glsl = "C:/VulkanSDK/1.4.328.1/Bin/glslangValidator.exe"
if (-not (Test-Path $glsl)) { throw "glslangValidator not found" }
$srcDir = "E:/ChimeraWork/thincli-agent/ChimeraEngine/engine/shaders"
$dstDir = "E:/ChimeraWork/thincli-agent/.tmp/slice_build/Release/shaders"
New-Item -ItemType Directory -Force -Path $dstDir | Out-Null
$n = 0
Get-ChildItem $srcDir | Where-Object { $_.Extension -in ".vert", ".frag", ".comp", ".glsl" } | ForEach-Object {
  $name = $_.Name
  $stem = $_.BaseName
  $ext = $_.Extension.TrimStart(".")
  if ($ext -eq "comp" -or $ext -eq "glsl") { $out = Join-Path $dstDir "$stem.spv" }
  else { $out = Join-Path $dstDir "$name.spv" }
  $stage = $ext
  if ($ext -eq "glsl") { $stage = "comp" }
  & $glsl -S $stage -V $_.FullName -o $out
  if ($LASTEXITCODE -ne 0) { throw "shader compile failed: $name" }
  $n++
}
Write-Output "COMPILED $n shaders -> $dstDir"
