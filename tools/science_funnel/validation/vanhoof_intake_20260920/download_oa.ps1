# VANHOOF INTAKE 20260920 - NCBI OA API route (programmatic access, license reported).
# oa.fcgi -> tgz link -> download -> tar extract -> magic-check members.
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Stage = 'E:/ChimeraWork/vanhoof-agent/tools/science_funnel/data/vanhoof_forearm'
$UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
$Log = @()

function Test-Magic([string]$Path, [string]$Kind) {
  $b = [System.IO.File]::ReadAllBytes($Path)
  if ($Kind -eq 'pdf') { return ($b.Length -gt 4 -and $b[0] -eq 0x25 -and $b[1] -eq 0x50 -and $b[2] -eq 0x44 -and $b[3] -eq 0x46) }
  if ($Kind -eq 'tif') { return ($b.Length -gt 4 -and (($b[0] -eq 0x49 -and $b[1] -eq 0x49) -or ($b[0] -eq 0x4D -and $b[1] -eq 0x4D))) }
  return $false
}

foreach ($pmc in @('PMC7812139', 'PMC7495296')) {
  $entry = @{ pmc = $pmc; ok = $false }
  try {
    $oaUrl = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=$pmc"
    $entry.oa_url = $oaUrl
    $xmlText = (Invoke-WebRequest -Uri $oaUrl -UserAgent $UA -UseBasicParsing -TimeoutSec 120).Content
    Set-Content -Encoding Ascii (Join-Path $Stage "$pmc`_oa.xml") $xmlText
    $xml = [xml]$xmlText
    $rec = $xml.OA.records.record
    $entry.license = $rec.license
    $entry.oa_citation = $rec.citation
    $link = ($rec.link | Where-Object { $_.format -eq 'tgz' } | Select-Object -First 1).link
    $entry.link = $link
    if (-not $link) { throw "no tgz link in oa.fcgi response" }
    $https = $link -replace '^ftp://', 'https://'
    $tgz = Join-Path $Stage "$pmc`_oa_package.tar.gz"
    Invoke-WebRequest -Uri $https -UserAgent $UA -OutFile $tgz -UseBasicParsing -TimeoutSec 600
    $entry.tgz_bytes = (Get-Item $tgz).Length
    $pkgDir = Join-Path $Stage "$pmc`_pkg"
    if (Test-Path $pkgDir) { Remove-Item -Recurse -Force $pkgDir }
    New-Item -ItemType Directory -Force -Path $pkgDir | Out-Null
    tar -xzf $tgz -C $pkgDir
    if ($LASTEXITCODE -ne 0) { throw "tar exit $LASTEXITCODE" }
    $entry.members = @()
    Get-ChildItem $pkgDir -File -Recurse | ForEach-Object {
      $kind = 'other'
      if ($_.Name -match '\.(tif|tiff)$') { $kind = 'tif' }
      elseif ($_.Name -match '\.pdf$') { $kind = 'pdf' }
      $good = '?'
      if ($kind -ne 'other') { $good = Test-Magic $_.FullName $kind }
      $entry.members += @{ name = $_.Name; bytes = $_.Length; kind = $kind; magic_ok = $good }
      Write-Host ("MEMBER`t{0}`t{1}`t{2}`t{3}" -f $pmc, $_.Name, $_.Length, $good)
    }
    $entry.ok = $true
  } catch {
    $entry.error = $_.Exception.Message
    if ($_.Exception.InnerException) { $entry.inner = $_.Exception.InnerException.Message }
  }
  $Log += New-Object PSObject -Property $entry
}
$Log | ConvertTo-Json -Depth 6 | Set-Content -Encoding Ascii (Join-Path $Stage 'download_oa_log.json')
Write-Host 'DONE'
