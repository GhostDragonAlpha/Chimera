# THE ALIASING-AUDIT RUN HARNESS (lane/policy-interface-freeze-20260920;
# preregistered in PREREGISTRATION.md BEFORE this build -- the declared
# instrument). Scratch GAIT_EVENT_TRACE build of gait_unit.cpp OUT OF TREE
# (nothing tracked is built or modified), then ONE live walk run on the current
# scene, then the FENCE: the trace build's unexercised stdout must equal the
# ship stdout sha 71065ac5... byte-for-byte or the audit is VOID (the
# instrument perturbed the walk it claims to observe).
#
# Raw bytes via cmd /c redirection (binary; no shell re-encoding). The mine
# (mine_aliasing_audit.py) parses the preserved trace separately.
$ErrorActionPreference = "Stop"

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Resolve-Path (Join-Path $here "..\..\..\..")
$audit = Join-Path $repo ".tmp\ifreeze\audit"
New-Item -ItemType Directory -Force -Path $audit | Out-Null

# ---- 1. the scene (current gait_scene.py; its derived-table inputs were
#         refined by waves 39-47, so the scene digest differs from the wave-38
#         pin f6844ee... -- declared in the prereg) ----
Write-Host "=== scene generation ==="
$sceneDir = Join-Path $repo ".tmp\ifreeze\scene"
New-Item -ItemType Directory -Force -Path $sceneDir | Out-Null
$gen = & python (Join-Path $repo "tools\science_funnel\gait_scene.py") --output $sceneDir 2>&1
$gen | Select-Object -Last 1
$scene = Join-Path $sceneDir "scene.json"
if (-not (Test-Path $scene)) { throw "scene not generated" }

# ---- 2. the scratch trace build (GAIT_EVENT_TRACE; the CMake target
#         gait_unit_trace's exact flags: /W4 /fp:precise + the define), PLUS a
#         no-trace build of the IDENTICAL source -- LEG A of the fence
#         (instrument inertness: trace stdout == no-trace stdout, byte-for-byte) ----
Write-Host "=== scratch trace + no-trace builds (cl.exe, out-of-tree) ==="
$vcvars = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"
if (-not (Test-Path $vcvars)) { throw "vcvarsall.bat not found" }
$src = Join-Path $repo "ChimeraEngine\engine\tests_coupled_arm\gait_unit.cpp"
$exe = Join-Path $audit "gait_unit_ifreeze_trace.exe"
$exeNT = Join-Path $audit "gait_unit_ifreeze_notrace.exe"
$buildLog = Join-Path $audit "build_log.txt"
$cmdTrace = "`"$vcvars`" x64 && cl /nologo /std:c++17 /O2 /W4 /fp:precise /EHsc /DGAIT_EVENT_TRACE `"$src`" /Fe:`"$exe`" /Fo`"$audit\trace.obj`" 2>&1"
$cmdNoTrace = "`"$vcvars`" x64 && cl /nologo /std:c++17 /O2 /W4 /fp:precise /EHsc `"$src`" /Fe:`"$exeNT`" /Fo`"$audit\notrace.obj`" 2>&1"
cmd /c $cmdTrace > $buildLog
cmd /c $cmdNoTrace >> $buildLog
if (-not (Test-Path $exe)) { Get-Content $buildLog -Tail 30; throw "trace build failed (see $buildLog)" }
if (-not (Test-Path $exeNT)) { Get-Content $buildLog -Tail 30; throw "no-trace build failed (see $buildLog)" }
Write-Host "built: $exe"
Write-Host "built: $exeNT"

# ---- 3. ONE live walk run (the trace build), raw stdout/stderr to files ----
Write-Host "=== live walk run (trace build) ==="
$outBin = Join-Path $audit "audit_stdout.txt"
$errBin = Join-Path $audit "audit_stderr.txt"
cmd /c "`"$exe`" `"$scene`" > `"$outBin`" 2> `"$errBin`""
Write-Host "exit: $LASTEXITCODE"

# the no-trace build, same scene (LEG A comparison bytes)
Write-Host "=== no-trace walk run (LEG A comparison) ==="
$outNT = Join-Path $audit "notrace_stdout.txt"
$errNT = Join-Path $audit "notrace_stderr.txt"
cmd /c "`"$exeNT`" `"$scene`" > `"$outNT`" 2> `"$errNT`""
Write-Host "exit: $LASTEXITCODE"

# the ship-anchor bytes: the shipped ref exe (the wave-38/command-adapter
# vintage, stdout 71065ac5...), same scene
Write-Host "=== ref-exe walk run (LEG B ship anchor) ==="
$refExe = Join-Path $repo "ChimeraEngine\engine\tests_coupled_arm\gait_unit_ref.exe"
$outRef = Join-Path $audit "ship_stdout.txt"
$errRef = Join-Path $audit "ship_stderr.txt"
cmd /c "`"$refExe`" `"$scene`" > `"$outRef`" 2> `"$errRef`""
Write-Host "exit: $LASTEXITCODE"

# ---- 4. THE FENCE v2 (LEG A instrument inertness + LEG B ship anchor;
#         the v1 clause fired on committed reporting growth -- diagnosed and
#         carried in the receipt; this fence measures the invariants directly) ----
Write-Host "=== fence v2 (LEG A: trace==notrace bytes; LEG B: ship anchors) ==="
$fence = & python (Join-Path $here "fence_audit_stdout.py") $outBin $outNT $outRef $errBin 2>&1
$fence
if ($LASTEXITCODE -ne 0) { throw "FENCE FAILED -- audit VOID (exit $LASTEXITCODE)" }
Write-Host "=== FENCE GREEN: the instrument did not perturb the walk ==="
