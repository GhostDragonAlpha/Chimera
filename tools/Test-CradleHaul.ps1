param([Parameter(Mandatory=$true)][string]$Output,[ValidateSet('author','run','reopen','gui')][string]$Mode='run')
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$studio=Split-Path -Parent $root
$env:CHIMERA_STUDIO_ROOT=$root
$env:BLENDER_USER_CONFIG=Join-Path $root '.user/cradle-haul-config'
$env:BLENDER_USER_EXTENSIONS=Join-Path $studio 'Libuipc/profile/extensions'
$env:BLENDER_USER_SCRIPTS=Join-Path $root '.user/scripts'
$out=[IO.Path]::GetFullPath($Output)
if (-not $out.StartsWith((Join-Path $root 'evidence')+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Use owned Studio evidence output' }
$blend=Join-Path $out 'Rescue cradle haul.blend'
$test='test_cradle_haul_workflow.py'
$file=$blend
$a=@('--factory-startup','--app-template','ChimeraStudio')
if ($Mode -eq 'author') {
  if (Test-Path $blend) { throw 'Owned output already exists; the authoring script refuses to overwrite' }
  $test='create_cradle_haul.py'
  $a=@('--factory-startup')
  $file=''
} elseif ($Mode -eq 'reopen') {
  if (-not (Test-Path (Join-Path $out 'checks.json'))) { throw 'Run the workflow mode first; reopen reads checks.json' }
  $test='test_cradle_haul_reopen.py'
} elseif ($Mode -eq 'gui') {
  if (-not (Test-Path (Join-Path $out 'checks.json'))) { throw 'Run the workflow mode first; the GUI reads checks.json' }
  if (Test-Path (Join-Path $out 'gui')) { throw 'gui/ output already exists' }
  $a=@('--factory-startup','--app-template','ChimeraStudio')
  $test='test_cradle_haul_gui.py'
}
if ($Mode -ne 'author') { $a=@('--background')+$a }
if ($Mode -ne 'author') { $a+=@($file) }
if ($Mode -eq 'gui') { $env:CHIMERA_CRADLE_GUI_OUT=$out }
$a+=@('--python-exit-code','1','--python',(Join-Path $studio 'Libuipc/tools/activate.py'),'--python',(Join-Path $root ('tests/'+$test)))
& (Join-Path $studio 'build-blender/bin/Release/blender.exe') @a
if ($LASTEXITCODE -ne 0) { throw "Cradle haul $Mode check failed" }
if ($Mode -eq 'gui' -and -not (Get-Content -Raw -LiteralPath (Join-Path $out 'gui/panel.json') | ConvertFrom-Json).passed) { throw 'Cradle haul UI failed' }
