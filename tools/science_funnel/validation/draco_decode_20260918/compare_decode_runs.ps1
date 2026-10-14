param(
  [string]$RunA = 'run1',
  [string]$RunB = 'run2'
)
$ErrorActionPreference = 'Stop'

$Base    = Split-Path -Parent $MyInvocation.MyCommand.Path
$OutDir  = Join-Path $Base 'out'
$RepoGlb = 'E:\ChimeraWork\draco-decode-20260918\tools\science_funnel\data\smithsonian'

function Sha256Bytes([byte[]]$bytes) {
  $h = [System.Security.Cryptography.SHA256]::Create()
  try { return ([System.BitConverter]::ToString($h.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant() }
  finally { $h.Dispose() }
}
function Sha256File([string]$path) {
  Sha256Bytes ([System.IO.File]::ReadAllBytes($path))
}

$receipt = [ordered]@{
  kind = 'draco_decode_receipt.v1'
  utc = (Get-Date).ToUniversalTime().ToString('o')
  falsifier = 're-decode (fresh decoder instances, separate page runs) must reproduce ' +
              'identical position/normal/index buffer sha256; a one-byte-corrupted GLB ' +
              'inside the draco bufferView must refuse loudly or change the identity -- ' +
              'never reproduce it'
  selftest_expected = 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
  specimens = [ordered]@{ }
}

foreach ($id in @('cranium', 'mandible')) {
  $fa = Get-Content (Join-Path $OutDir ("{0}__{1}.json" -f $RunA, $id)) -Raw | ConvertFrom-Json
  $fb = Get-Content (Join-Path $OutDir ("{0}__{1}.json" -f $RunB, $id)) -Raw | ConvertFrom-Json

  if ($fa.selftest_sha256_abc -ne $receipt.selftest_expected) { throw "$id runA selftest bad" }
  if ($fb.selftest_sha256_abc -ne $receipt.selftest_expected) { throw "$id runB selftest bad" }

  # glb sha recorded by the page must match the pinned file on disk
  $glbName = [System.IO.Path]::GetFileName($fa.glb.url)
  $diskSha = Sha256File (Join-Path $RepoGlb $glbName)
  if ($fa.glb.sha256 -ne $diskSha) { throw "$id glb sha mismatch vs disk" }
  if ($fb.glb.sha256 -ne $diskSha) { throw "$id glb sha mismatch vs disk (runB)" }

  # in-page pass1 == pass2 (fresh decoder instances)
  $inRunIdentical = ($fa.pass1.positions_sha256 -eq $fa.pass2.positions_sha256) -and
                    ($fa.pass1.normals_sha256 -eq $fa.pass2.normals_sha256) -and
                    ($fa.pass1.indices_sha256 -eq $fa.pass2.indices_sha256)
  if (-not $inRunIdentical) { throw "$id in-run re-decode differs" }

  # cross-run: separate page load, separate WASM instantiations
  $crossRunIdentical = ($fa.pass1.positions_sha256 -eq $fb.pass1.positions_sha256) -and
                       ($fa.pass1.normals_sha256 -eq $fb.pass1.normals_sha256) -and
                       ($fa.pass1.indices_sha256 -eq $fb.pass1.indices_sha256) -and
                       ($fa.pass1.vertex_count -eq $fb.pass1.vertex_count) -and
                       ($fa.pass1.index_count -eq $fb.pass1.index_count)
  if (-not $crossRunIdentical) { throw "$id cross-run re-decode differs" }

  # the POSTed buffer bytes must hash to exactly the recorded identity
  $posBytes = [Convert]::FromBase64String($fa.buffers.positions_b64)
  $posSha = Sha256Bytes $posBytes
  if ($posSha -ne $fa.pass1.positions_sha256) { throw "$id posted position bytes do not match recorded hash" }
  $idxBytes = [Convert]::FromBase64String($fa.buffers.indices_b64)
  $idxSha = Sha256Bytes $idxBytes
  if ($idxSha -ne $fa.pass1.indices_sha256) { throw "$id posted index bytes do not match recorded hash" }
  $norSha = $null
  if ($fa.buffers.normals_b64) {
    $norBytes = [Convert]::FromBase64String($fa.buffers.normals_b64)
    $norSha = Sha256Bytes $norBytes
    if ($norSha -ne $fa.pass1.normals_sha256) { throw "$id posted normal bytes do not match recorded hash" }
  }

  # screenshot sha (perceptual evidence identity)
  $shotSha = $null
  if ($fa.screenshot_png_base64) {
    $shotSha = Sha256Bytes ([Convert]::FromBase64String($fa.screenshot_png_base64))
  }

  Write-Output ("RECEIPT {0}: cross-run identical; verts {1}; pos {2}" -f
    $id, $fa.pass1.vertex_count, $fa.pass1.positions_sha256.Substring(0, 16))

  $receipt.specimens[$id] = [ordered]@{
    glb_file = $glbName
    glb_sha256 = $diskSha
    three_revision = $fa.decoder.three_revision
    draco_header = $fa.gltf_facts.draco
    accessor_declared = $fa.gltf_facts.accessors
    decoded = [ordered]@{
      positions_sha256 = $fa.pass1.positions_sha256
      normals_sha256 = $fa.pass1.normals_sha256
      indices_sha256 = $fa.pass1.indices_sha256
      index_type = $fa.pass1.index_type
      vertex_count = $fa.pass1.vertex_count
      index_count = $fa.pass1.index_count
      meshes = $fa.pass1.meshes
    }
    redecode_identical_in_run = $inRunIdentical
    redecode_identical_cross_run = $crossRunIdentical
    posted_buffer_bytes = [ordered]@{ positions = $posBytes.Length; indices = $idxBytes.Length }
    screenshot_sha256 = $shotSha
    screenshot_error = $fa.screenshot_error
    user_agent = $fa.user_agent
  }
}

$ca = Get-Content (Join-Path $OutDir ("{0}__corrupt.json" -f $RunA)) -Raw | ConvertFrom-Json
$cb = Get-Content (Join-Path $OutDir ("{0}__corrupt.json" -f $RunB)) -Raw | ConvertFrom-Json
if ($ca.identical_to_pinned -eq $true) { throw 'runA corrupt probe reproduced pinned identity' }
if ($cb.identical_to_pinned -eq $true) { throw 'runB corrupt probe reproduced pinned identity' }
$receipt.corrupt_probe = [ordered]@{
  source_glb = $ca.source_glb
  flip_offset = $ca.flip_offset
  corrupted_sha256 = $ca.corrupted_sha256
  outcome_runA = $ca.outcome
  outcome_runB = $cb.outcome
  error_runA = $ca.error
  error_runB = $cb.error
}
Write-Output ("RECEIPT corrupt: {0} / {1}" -f $ca.outcome, $cb.outcome)

$receiptPath = Join-Path $Base 'decode_receipt.json'
[System.IO.File]::WriteAllText($receiptPath,
  ((ConvertTo-Json $receipt -Depth 8) -replace "`n", "`r`n") + "`r`n",
  [System.Text.UTF8Encoding]::new($false))
Write-Output "RECEIPT-WRITTEN: $receiptPath"
