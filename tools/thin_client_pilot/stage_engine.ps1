# thincli lane: stage the prebuilt engine into this worktree's slice_build dir.
# Provenance (recorded in the prereg before this step): the binary was built at
# e96eb943 (the merged playable-slice lane); git diff e96eb943..bd4bf630 -- 
# ChimeraEngine/engine/ touches only gait_controller.hpp (included by NO
# chimera_engine target file) and tests_coupled_arm/, so the chimera_engine
# target sources are byte-identical across the two commits.
$ErrorActionPreference = "Stop"
$src = "E:/ChimeraWork/slice-agent/.tmp/slice_build/Release"
$dst = "E:/ChimeraWork/thincli-agent/.tmp/slice_build/Release"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item -Force -Path (Join-Path $src "chimera_engine.exe") -Destination $dst
if (Test-Path (Join-Path $src "launch_chimera.bat")) {
  Copy-Item -Force -Path (Join-Path $src "launch_chimera.bat") -Destination $dst
}
if (Test-Path (Join-Path $src "shaders")) {
  Copy-Item -Recurse -Force -Path (Join-Path $src "shaders") -Destination $dst
}
Get-ChildItem $dst | Select-Object Name, Length | Format-Table -AutoSize
Write-Output "STAGED-OK"
