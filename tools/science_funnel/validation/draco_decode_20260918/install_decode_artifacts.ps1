$ErrorActionPreference = 'Stop'

$Base     = Split-Path -Parent $MyInvocation.MyCommand.Path
$OutDir   = Join-Path $Base 'out'
$RepoRoot = 'E:\ChimeraWork\draco-decode-20260918'
$DecDir   = Join-Path $RepoRoot 'tools\science_funnel\data\smithsonian\draco_decode'
$ValDir   = Join-Path $RepoRoot 'tools\science_funnel\validation\visual_proof_20260917'
New-Item -ItemType Directory -Force -Path $DecDir | Out-Null

function Sha256Bytes([byte[]]$bytes) {
  $h = [System.Security.Cryptography.SHA256]::Create()
  try { return ([System.BitConverter]::ToString($h.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant() }
  finally { $h.Dispose() }
}

function Sha256File([string]$path) {
  Sha256Bytes ([System.IO.File]::ReadAllBytes($path))
}

$lock = Get-Content (Join-Path $Base 'cdn.lock.json') -Raw | ConvertFrom-Json
$receipt = Get-Content (Join-Path $Base 'decode_receipt.json') -Raw | ConvertFrom-Json

$indexExt = @{ 'Uint32Array' = '.indices.u32'; 'Uint16Array' = '.indices.u16' }
$specimens = [ordered]@{ }
foreach ($id in @('cranium', 'mandible')) {
  $j = Get-Content (Join-Path $OutDir ("run1__{0}.json" -f $id)) -Raw | ConvertFrom-Json

  $posBytes = [Convert]::FromBase64String($j.buffers.positions_b64)
  $norBytes = if ($j.buffers.normals_b64) { [Convert]::FromBase64String($j.buffers.normals_b64) } else { $null }
  $idxBytes = if ($j.buffers.indices_b64) { [Convert]::FromBase64String($j.buffers.indices_b64) } else { $null }

  # trust, but verify: bytes -> sha256 must equal what the page recorded
  if ((Sha256Bytes $posBytes) -ne $j.pass1.positions_sha256) { throw "$id positions hash mismatch" }
  if ($norBytes -and ((Sha256Bytes $norBytes) -ne $j.pass1.normals_sha256)) { throw "$id normals hash mismatch" }
  if ($idxBytes -and ((Sha256Bytes $idxBytes) -ne $j.pass1.indices_sha256)) { throw "$id indices hash mismatch" }

  $stem = "USNM15259_{0}" -f $id
  $posName = "$stem.positions.f32"
  $norName = "$stem.normals.f32"
  $idxName = "$stem$($indexExt[$j.pass1.index_type])"
  [System.IO.File]::WriteAllBytes((Join-Path $DecDir $posName), $posBytes)
  if ($norBytes) { [System.IO.File]::WriteAllBytes((Join-Path $DecDir $norName), $norBytes) }
  if ($idxBytes) { [System.IO.File]::WriteAllBytes((Join-Path $DecDir $idxName), $idxBytes) }

  # perceptual-evidence screenshot -> next to the renders it evidences
  $shotName = "smithsonian_usnm15259_{0}.decode_screenshot.png" -f $id
  $shotSha = $null
  if ($j.screenshot_png_base64) {
    $shotBytes = [Convert]::FromBase64String($j.screenshot_png_base64)
    $shotSha = Sha256Bytes $shotBytes
    [System.IO.File]::WriteAllBytes((Join-Path $ValDir $shotName), $shotBytes)
  }

  $specimens[$id] = [ordered]@{
    glb = [ordered]@{ name = [System.IO.Path]::GetFileName($j.glb.url); sha256 = $j.glb.sha256 }
    draco_header = $j.gltf_facts.draco
    accessor_declared = $j.gltf_facts.accessors
    decoded = [ordered]@{
      positions_sha256 = $j.pass1.positions_sha256
      normals_sha256 = $j.pass1.normals_sha256
      indices_sha256 = $j.pass1.indices_sha256
      index_type = $j.pass1.index_type
      vertex_count = $j.pass1.vertex_count
      index_count = $j.pass1.index_count
      meshes = $j.pass1.meshes
    }
    buffers = [ordered]@{
      positions = $posName
      normals = $norName
      indices = $idxName
    }
    screenshot = [ordered]@{
      file = $shotName
      sha256 = $shotSha
      label = 'PERCEPTUAL EVIDENCE: the decode hash is the proof; the picture is for the human'
    }
  }
  Write-Output ("INSTALLED {0}: {1} verts, pos {2}" -f $id, $j.pass1.vertex_count,
    $j.pass1.positions_sha256.Substring(0, 16))
}

$libs = [ordered]@{ }
foreach ($f in $lock.files) { $libs[$f.file] = [ordered]@{ url = $f.url; sha256 = $f.sha256; bytes = $f.bytes } }

$run1 = Get-Content (Join-Path $OutDir 'run1__summary.json') -Raw | ConvertFrom-Json
$manifest = [ordered]@{
  kind = 'draco_decode_manifest.v1'
  label = 'Pinned decode identity for the draco-compressed Smithsonian USNM 15259 GLBs: ' +
          'produced by the OFFICIAL Google Draco WASM decoder (trusted reference decoder, ' +
          'no port) running in a browser page via three.js GLTFLoader + DRACOLoader. ' +
          'Decoding is pure: re-decode reproduces every hash (see receipt). The decoded ' +
          'buffer sha256s are the geometry machine identity; the screenshots are ' +
          'PERCEPTUAL EVIDENCE, never the proof.'
  work_item = 'work.data.visual_proof_20260917'
  channel = [ordered]@{
    decoder = 'official Google Draco WASM decoder (gstatic versioned 1.5.7), draco_wasm_wrapper.js + draco_decoder.wasm'
    page = 'three.js r160 GLTFLoader + DRACOLoader, decoder_config wasm'
    three_revision = $receipt.specimens.cranium.three_revision
    browser_user_agent = $receipt.specimens.cranium.user_agent
    libs = $libs
    receipt = 'tools/science_funnel/validation/draco_decode_20260918/decode_receipt.json'
  }
  falsifiers = [ordered]@{
    redecode_in_run = 'pass1 == pass2, fresh DRACOLoader/WASM instances (identical=true for both specimens)'
    redecode_cross_run = 'two separate page loads reproduce every buffer sha256 (identical=true for both specimens)'
    corrupt_probe = ('one flipped byte inside the draco bufferView: {0} / {1}' -f
      $receipt.corrupt_probe.outcome_runA, $receipt.corrupt_probe.outcome_runB)
  }
  corrupt_probe = $receipt.corrupt_probe
  run_summary = [ordered]@{ tag = $run1.tag; utc = $run1.utc }
  notes = @(
    'The trusted decoder emits 133172 vertices for the cranium where the glTF accessor ' +
    'declares 133171 -- the same producer divergence from reference draco layouts the ' +
    'pure-python lane measured; the decode identity is pinned to what the trusted ' +
    'decoder actually produced, and both counts are recorded.',
    'Normals are present in both decoded meshes; indices decode as Uint32Array.'
  )
  specimens = $specimens
}
$manifestPath = Join-Path $DecDir 'draco_decode_manifest.json'
[System.IO.File]::WriteAllText($manifestPath,
  ((ConvertTo-Json $manifest -Depth 10) -replace "`n", "`r`n") + "`r`n",
  [System.Text.UTF8Encoding]::new($false))
Write-Output "MANIFEST-WRITTEN: $manifestPath"

# final chain check: files on disk hash back to the recorded identities
$check = Get-Content $manifestPath -Raw | ConvertFrom-Json
foreach ($id in @('cranium', 'mandible')) {
  $s = $check.specimens.$id
  foreach ($pair in @(@('positions', 'positions_sha256'),
                      @('normals', 'normals_sha256'),
                      @('indices', 'indices_sha256'))) {
    $fname = $s.buffers.($pair[0])
    $want = $s.decoded.($pair[1])
    if ($fname -and $want) {
      $got = Sha256File (Join-Path $DecDir $fname)
      if ($got -ne $want) { throw "chain broken: $id $pair file $fname" }
    }
  }
}
Write-Output 'CHAIN-VERIFIED: buffer files on disk match the recorded decode identities'
