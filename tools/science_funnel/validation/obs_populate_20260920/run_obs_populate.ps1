# THE OBS-POPULATE RUN HARNESS (lane/obs-populate-20260920; preregistered in
# record.md BEFORE this run -- the declared instrument). Fresh scene, fresh
# scratch GAIT_EVENT_TRACE + no-trace builds of the IDENTICAL HEAD source
# OUT OF TREE (nothing tracked is built or modified), ONE live walk run, the
# FENCE (fence_audit_stdout.py, the interface-freeze instrument REUSED
# unmodified), then the CONTROL mine (the interface-freeze mine verbatim) and
# the TREATMENT mine (the delivered re-run), then the F3/F4 pins and the F5
# 3-run determinism legs.
#
# Raw bytes via cmd /c redirection (binary; no shell re-encoding).
$ErrorActionPreference = "Stop"

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Resolve-Path (Join-Path $here "..\..\..\..")
$ifreeze = Join-Path $repo "tools\science_funnel\validation\policy_interface_freeze_20260920"
$audit = Join-Path $repo ".tmp\obspop\audit"
New-Item -ItemType Directory -Force -Path $audit | Out-Null

# ---- 1. the scene (current gait_scene.py); the FILE sha must equal the
#         wave-38/interface-freeze anchor f6844ee... (the prereg's F2 clause;
#         the generator's printed digest is a pre-canonicalization value, the
#         interface-freeze receipt's correction -- the FILE sha is the anchor)
Write-Host "=== scene generation ==="
$sceneDir = Join-Path $repo ".tmp\obspop\scene"
New-Item -ItemType Directory -Force -Path $sceneDir | Out-Null
$gen = & python (Join-Path $repo "tools\science_funnel\gait_scene.py") --output $sceneDir 2>&1
$gen | Select-Object -Last 1
$scene = Join-Path $sceneDir "scene.json"
if (-not (Test-Path $scene)) { throw "scene not generated" }
$sceneSha = & python -c "import sys,hashlib;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" $scene
Write-Host "scene FILE sha256: $sceneSha"
if ($sceneSha -ne "f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342") {
  throw "F2 FIRED: scene FILE sha $sceneSha != the anchor f6844ee..."
}

# ---- 2. the scratch trace + no-trace builds (cl.exe, out of tree; the
#         gait_unit_trace target's exact flags) --
Write-Host "=== scratch trace + no-trace builds (cl.exe, out-of-tree) ==="
$vcvars = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"
if (-not (Test-Path $vcvars)) { throw "vcvarsall.bat not found" }
$src = Join-Path $repo "ChimeraEngine\engine\tests_coupled_arm\gait_unit.cpp"
$exe = Join-Path $audit "gait_unit_obspop_trace.exe"
$exeNT = Join-Path $audit "gait_unit_obspop_notrace.exe"
$buildLog = Join-Path $audit "build_log.txt"
$cmdTrace = "`"$vcvars`" x64 && cl /nologo /std:c++17 /O2 /W4 /fp:precise /EHsc /DGAIT_EVENT_TRACE `"$src`" /Fe:`"$exe`" /Fo`"$audit\trace.obj`" 2>&1"
$cmdNoTrace = "`"$vcvars`" x64 && cl /nologo /std:c++17 /O2 /W4 /fp:precise /EHsc `"$src`" /Fe:`"$exeNT`" /Fo`"$audit\notrace.obj`" 2>&1"
cmd /c $cmdTrace > $buildLog
cmd /c $cmdNoTrace >> $buildLog
if (-not (Test-Path $exe)) { Get-Content $buildLog -Tail 30; throw "trace build failed (see $buildLog)" }
if (-not (Test-Path $exeNT)) { Get-Content $buildLog -Tail 30; throw "no-trace build failed (see $buildLog)" }
Write-Host "built: $exe"
Write-Host "built: $exeNT"

# ---- 3. ONE live walk run (the trace build), raw stdout/stderr to files
Write-Host "=== live walk run (trace build) ==="
$outBin = Join-Path $audit "audit_stdout.txt"
$errBin = Join-Path $audit "audit_stderr.txt"
cmd /c "`"$exe`" `"$scene`" > `"$outBin`" 2> `"$errBin`""
Write-Host "exit: $LASTEXITCODE"

Write-Host "=== no-trace walk run (LEG A comparison) ==="
$outNT = Join-Path $audit "notrace_stdout.txt"
$errNT = Join-Path $audit "notrace_stderr.txt"
cmd /c "`"$exeNT`" `"$scene`" > `"$outNT`" 2> `"$errNT`""
Write-Host "exit: $LASTEXITCODE"

Write-Host "=== ref-exe walk run (LEG B ship anchor) ==="
$refExe = Join-Path $repo "ChimeraEngine\engine\tests_coupled_arm\gait_unit_ref.exe"
$outRef = Join-Path $audit "ship_stdout.txt"
$errRef = Join-Path $audit "ship_stderr.txt"
cmd /c "`"$refExe`" `"$scene`" > `"$outRef`" 2> `"$errRef`""
Write-Host "exit: $LASTEXITCODE"

# ---- 4. THE FENCE (the interface-freeze fence_audit_stdout.py, reused
#         unmodified: LEG A instrument inertness + LEG B ship anchor)
Write-Host "=== fence (LEG A: trace==notrace bytes; LEG B: ship anchors) ==="
$fence = & python (Join-Path $ifreeze "fence_audit_stdout.py") $outBin $outNT $outRef $errBin 2>&1
$fence
if ($LASTEXITCODE -ne 0) { throw "FENCE FAILED -- audit VOID (exit $LASTEXITCODE)" }

# ---- 5. the stderr trace anchor (F2's strongest leg: the walk bytes are the
#         interface-freeze audit's bytes, so the CONTROL census must reproduce)
$traceSha = & python -c "import sys,hashlib;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" $errBin
Write-Host "walk trace sha256: $traceSha"
if ($traceSha -ne "c6f9b6c00a1d549a4bc709724d2f62f8f28b37823696de4689e1950651c37481") {
  throw "F2 FIRED: walk trace sha $traceSha != the anchor c6f9b6c0..."
}
Write-Host "=== F2 GREEN: scene f6844ee / fence LEG A+B / trace c6f9b6c0 ==="

# ---- 6. the CONTROL mine (the interface-freeze instrument, verbatim)
Write-Host "=== control mine (interface-freeze mine verbatim on the fresh trace) ==="
$ctlDir = Join-Path $audit "control_out"
& python (Join-Path $ifreeze "mine_aliasing_audit.py") $errBin $ctlDir 2>&1 | Select-Object -Last 6
if ($LASTEXITCODE -ne 0) { throw "control mine failed (exit $LASTEXITCODE)" }

# ---- 7. the TREATMENT mine (the delivered re-run), 3 runs (F5 legs 1..3)
Write-Host "=== treatment mine (delivered re-run), runs 1..3 ==="
$runDirs = @()
foreach ($i in 1..3) {
  $rd = Join-Path $audit ("populate_run" + $i)
  $runDirs += $rd
  & python (Join-Path $here "mine_obs_populate.py") $errBin $rd 2>&1 | Select-Object -Last 10
  Write-Host ("run " + $i + " exit: " + $LASTEXITCODE)
}

# ---- 8. the pins fence (F3 table-invariance + F4 corpus re-freeze) and the
#         determinism comparator (F5)
Write-Host "=== fences: F3 table-invariance + F4 corpus re-freeze ==="
& python (Join-Path $here "fences_corpus.py") pins (Join-Path $ctlDir "aliased_pairs.json")
if ($LASTEXITCODE -ne 0) { throw "F3/F4 FIRED (exit $LASTEXITCODE)" }
Write-Host "=== fences: F5 determinism (3-run byte-identity) ==="
& python (Join-Path $here "fences_corpus.py") determinism $runDirs[0] $runDirs[1] $runDirs[2]
if ($LASTEXITCODE -ne 0) { throw "F5 FIRED (exit $LASTEXITCODE)" }

Write-Host "=== HARNESS COMPLETE (F1 verdict is the treatment mine's own printed verdict) ==="
