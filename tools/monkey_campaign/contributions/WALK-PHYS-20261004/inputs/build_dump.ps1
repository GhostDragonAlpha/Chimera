# build_dump.ps1 v2 -- out-of-tree cl.exe build of the lane-private statedump
# variant (integ7 walk harness's exact flag pattern); the variant COPY sits
# untracked beside the tree source so its relative includes resolve.
$ErrorActionPreference = 'Stop'
$scratch = 'E:\ChimeraWork\viswalk-agent\.tmp\viswalk_dump'
$vcvars = 'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat'
if (-not (Test-Path $vcvars)) { throw 'vcvarsall.bat not found' }
$src = 'E:\ChimeraWork\viswalk-agent\ChimeraEngine\engine\tests_coupled_arm\gait_unit_viswalk_dump.cpp'
$exe = Join-Path $scratch 'gait_unit_viswalk_dump.exe'
$cmd = "`"$vcvars`" x64 && cl /nologo /std:c++17 /O2 /W4 /fp:precise /EHsc /DGAIT_EVENT_TRACE `"$src`" /Fe:`"$exe`" /Fo`"$scratch\dump.obj`" 2>&1"
cmd /c $cmd > (Join-Path $scratch 'build_log.txt')
if (-not (Test-Path $exe)) { Get-Content (Join-Path $scratch 'build_log.txt') -Tail 30; throw 'build failed' }
Write-Output 'BUILD OK'
Get-Content (Join-Path $scratch 'build_log.txt') -Tail 3
