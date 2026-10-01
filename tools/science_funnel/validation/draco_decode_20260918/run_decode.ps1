param(
  [string]$RunTag = 'run1',
  [int]$Port = 8791
)
$ErrorActionPreference = 'Stop'

$Base     = Split-Path -Parent $MyInvocation.MyCommand.Path
$Stage    = Join-Path $Base 'staging'
$OutDir   = Join-Path $Base 'out'
$LogDir   = Join-Path $Base 'logs'
$Udd      = Join-Path $LogDir ("udd-{0}" -f $RunTag)
$RepoGlb  = 'E:\ChimeraWork\draco-decode-20260918\tools\science_funnel\data\smithsonian'
$CranGlb  = Join-Path $RepoGlb 'USNM15259_cranium_-300_dec-150k-4096-high.glb'
$MandGlb  = Join-Path $RepoGlb 'USNM15259_mandible_-300-150k-4096-high.glb'
$SelfUrl  = "http://127.0.0.1:$Port"

function Sha256File([string]$path) {
  $h = [System.Security.Cryptography.SHA256]::Create()
  $fs = [System.IO.File]::OpenRead($path)
  try { return ([System.BitConverter]::ToString($h.ComputeHash($fs))).Replace('-', '').ToLowerInvariant() }
  finally { $fs.Dispose(); $h.Dispose() }
}

New-Item -ItemType Directory -Force -Path $Stage, $OutDir, $LogDir | Out-Null
$mandSha = Sha256File $MandGlb

# --- 1. jobs.json for the harness (the corrupt probe is derived IN-PAGE from
#         the pinned bytes with a recorded flip offset, so it provably lands
#         inside the draco bufferView)
$jobs = [ordered]@{
  libs = @('three.module.js','GLTFLoader.js','DRACOLoader.js',
           'draco_wasm_wrapper.js','draco_decoder.wasm','BufferGeometryUtils.js')
  glbs = @(
    [ordered]@{ id = 'cranium'; label = 'USNM 15259 CRANIUM';
                url = '/glb/USNM15259_cranium_-300_dec-150k-4096-high.glb' },
    [ordered]@{ id = 'mandible'; label = 'USNM 15259 MANDIBLE';
                url = '/glb/USNM15259_mandible_-300-150k-4096-high.glb' }
  )
  corrupt = [ordered]@{ id = 'mandible'; of = 'mandible' }
}
$jobsPath = Join-Path $Stage 'jobs.json'
[System.IO.File]::WriteAllText($jobsPath, (ConvertTo-Json $jobs -Depth 5),
  [System.Text.UTF8Encoding]::new($false))

# --- 3. listener: start if not already answering
$ready = $false
try {
  $probe = Invoke-WebRequest -Uri "$SelfUrl/jobs.json" -UseBasicParsing -TimeoutSec 3
  if ($probe.StatusCode -eq 200) { $ready = $true }
} catch { }
if (-not $ready) {
  Remove-Item (Join-Path $LogDir 'listener.ready') -ErrorAction SilentlyContinue
  $listenerProc = Start-Process -FilePath 'powershell' -PassThru -WindowStyle Hidden `
    -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass',
                    '-File', (Join-Path $Base 'serve_draco.ps1'), '-Port', "$Port")
  Write-Output "LISTENER-PID: $($listenerProc.Id)"
  $ok = $false
  for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 500
    try {
      $probe = Invoke-WebRequest -Uri "$SelfUrl/jobs.json" -UseBasicParsing -TimeoutSec 2
      if ($probe.StatusCode -eq 200) { $ok = $true; break }
    } catch { }
  }
  if (-not $ok) { throw 'listener did not become ready' }
}
Write-Output 'LISTENER-READY'

# --- 4. headless browser (isolated profile; software WebGL allowed)
$browser = $null
foreach ($c in @('C:\Program Files\Google\Chrome\Application\chrome.exe',
                 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
                 'C:\Program Files\Microsoft\Edge\Application\msedge.exe')) {
  if (Test-Path $c) { $browser = $c; break }
}
if (-not $browser) { throw 'no chromium-family browser found' }
Remove-Item $Udd -Recurse -Force -ErrorAction SilentlyContinue
$marker = Join-Path $OutDir ("done.{0}.marker" -f $RunTag)
Remove-Item $marker -ErrorAction SilentlyContinue
$proc = Start-Process -FilePath $browser -PassThru -WindowStyle Hidden -ArgumentList @(
  '--headless=new', "--user-data-dir=$Udd", '--no-first-run',
  '--no-default-browser-check', '--disable-extensions',
  '--disable-background-networking', '--enable-unsafe-swiftshader',
  '--use-angle=swiftshader', '--window-size=420,380',
  "$SelfUrl/harness?run=$RunTag")
Write-Output ("BROWSER-PID: {0} ({1})" -f $proc.Id, $browser)

# --- 5. poll for completion (NEVER block-wait on the process itself)
$done = $false
for ($i = 0; $i -lt 100; $i++) {
  Start-Sleep -Seconds 3
  if (Test-Path $marker) { $done = $true; break }
  if ($proc.HasExited) {
    # give the page a moment in case exit raced the POST, then keep polling a bit
  }
}
Write-Output ("DONE-MARKER: {0}" -f $done)

# --- 6. kill browser tree for this isolated profile
Get-CimInstance Win32_Process -Filter "Name like 'chrome%' or Name like 'msedge%'" |
  Where-Object { $_.CommandLine -like "*$Udd*" } |
  ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch { } }
try { if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force } } catch { }

if (-not $done) {
  Write-Output '--- listener log tail ---'
  Get-Content (Join-Path $LogDir 'listener.log') -Tail 30 -ErrorAction SilentlyContinue
  throw ("harness did not signal done for tag {0}" -f $RunTag)
}

# --- 7. validate results of this run
$expect = @(
  ("{0}__cranium.json" -f $RunTag),
  ("{0}__mandible.json" -f $RunTag),
  ("{0}__corrupt.json" -f $RunTag)
)
$selftestExpected = 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
foreach ($name in $expect) {
  $p = Join-Path $OutDir $name
  if (-not (Test-Path $p)) { throw "missing result file: $name" }
  $j = Get-Content $p -Raw | ConvertFrom-Json
  if ($name.EndsWith('corrupt.json')) {
    if ($j.identical_to_pinned -eq $true) {
      throw ("corrupted GLB silently reproduced the pinned identity -- falsifier FAILED: outcome={0}" -f $j.outcome)
    }
    if ($j.outcome -eq 'REFUSED') {
      Write-Output ("CORRUPT-REFUSED at byte {0}: {1}" -f $j.flip_offset, $j.error)
    } else {
      Write-Output ("CORRUPT-DECODED-DIFFERENT at byte {0}: pinned pos {1} vs corrupt pos {2}" -f
        $j.flip_offset, $j.identical_to_pinned, $j.decoded_positions_sha256)
    }
    continue
  }
  if ($j.selftest_sha256_abc -ne $selftestExpected) {
    throw ("sha256 selftest mismatch in {0}: {1}" -f $name, $j.selftest_sha256_abc)
  }
  if ($j.redecode_identical -ne $true) {
    throw ("in-page re-decode hashes differ for {0}" -f $j.id)
  }
  if (-not $j.screenshot_png_base64 -and -not $j.screenshot_error) {
    throw ("no screenshot and no screenshot_error recorded for {0}" -f $j.id)
  }
  Write-Output ("DECODED {0}: verts {1} indices {2} pos_sha {3} shot {4}" -f
    $j.id, $j.pass1.vertex_count, $j.pass1.index_count,
    $j.pass1.positions_sha256.Substring(0, 12),
    $(if ($j.screenshot_png_base64) { 'ok' } else { "ERROR: $($j.screenshot_error)" }))
}
$fatal = Join-Path $OutDir ("{0}__fatal.json" -f $RunTag)
if (Test-Path $fatal) {
  Get-Content $fatal -Raw
  throw 'harness reported a fatal error'
}

$corruptResult = Get-Content (Join-Path $OutDir ("{0}__corrupt.json" -f $RunTag)) -Raw | ConvertFrom-Json
$summary = [ordered]@{
  kind = 'draco_decode_run.v1'
  tag = $RunTag
  utc = (Get-Date).ToUniversalTime().ToString('o')
  corrupt_probe = [ordered]@{ source_glb = $corruptResult.source_glb;
                              flip_offset = $corruptResult.flip_offset;
                              corrupted_sha256 = $corruptResult.corrupted_sha256;
                              outcome = $corruptResult.outcome;
                              error = $corruptResult.error;
                              decoded_positions_sha256 = $corruptResult.decoded_positions_sha256;
                              identical_to_pinned = $corruptResult.identical_to_pinned }
  glb = [ordered]@{ cranium_sha256 = (Sha256File $CranGlb); mandible_sha256 = $mandSha }
}
$summaryPath = Join-Path $OutDir ("{0}__summary.json" -f $RunTag)
[System.IO.File]::WriteAllText($summaryPath,
  ((ConvertTo-Json $summary -Depth 6) -replace "`n", "`r`n") + "`r`n",
  [System.Text.UTF8Encoding]::new($false))
Write-Output "RUN-OK tag=$RunTag"
