# MAT2-W03 sergeant attempt: rebuild the pinned statedump variant from the
# extracted 17ba94b9 blobs with the P02-pinned cl recipe. Builds INSIDE this
# attempt workspace only. Agent: arrival-db26712d6a264e4899c951f55b074d80
$ErrorActionPreference = 'Stop'
$vcvars = 'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat'
if (-not (Test-Path $vcvars)) { throw 'vcvarsall.bat not found' }
$here = 'E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-W03\sergeant-arrival-db26712d'
# Same layout as the pinned P02 build: the statedump source sits in
# ChimeraEngine\engine\tests_coupled_arm\ so ../gait_controller.hpp resolves
# to the pinned engine header.
$layout = Join-Path $here 'engine_tree17\ChimeraEngine\engine\tests_coupled_arm'
New-Item -ItemType Directory -Force -Path $layout | Out-Null
Copy-Item (Join-Path $here 'engine_tree17\tools\science_funnel\validation\visible_walk_20260923\native\gait_unit_viswalk_dump.cpp') (Join-Path $layout 'gait_unit_viswalk_dump.cpp') -Force
$src = Join-Path $layout 'gait_unit_viswalk_dump.cpp'
$outdir = Join-Path $here 'viswalk_dump'
New-Item -ItemType Directory -Force -Path $outdir | Out-Null
$exe = Join-Path $outdir 'gait_unit_viswalk_dump.exe'
$cmd = "`"$vcvars`" x64 && cl /nologo /std:c++17 /O2 /W4 /fp:precise /EHsc /DGAIT_EVENT_TRACE `"$src`" /Fe:`"$exe`" /Fo`"$outdir\dump.obj`" 2>&1"
cmd /c $cmd > (Join-Path $outdir 'build_log.txt')
if (-not (Test-Path $exe)) { Get-Content (Join-Path $outdir 'build_log.txt') -Tail 30; throw 'build failed' }
Write-Output 'BUILD OK'
$hash = (Get-FileHash -Algorithm SHA256 $exe).Hash
Write-Output "EXE_SHA256=$hash"
$tail = Get-Content (Join-Path $outdir 'build_log.txt') -Tail 5
$tail | ForEach-Object { $_ }
