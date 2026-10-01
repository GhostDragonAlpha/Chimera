# VANHOOF INTAKE 20260920 - europepmc mirror fallback (prereg P-DOWN named route).
# PMC direct = "Preparing to download" interstitial (kept as evidence).
# Route A: supplementaryFiles zip endpoint (guimaraes precedent; inner members sha-stable).
# Route B: PDF render endpoints; a file is accepted only if its MAGIC bytes check out.
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

# ---- Route A: supplementary zips -> members ----
foreach ($pmc in @('PMC7812139', 'PMC7495296')) {
  $zipUrl = "https://www.ebi.ac.uk/europepmc/webservices/rest/$pmc/supplementaryFiles"
  $zipPath = Join-Path $Stage "$pmc`_supplements.zip"
  $entry = @{ step = "zip $pmc"; url = $zipUrl; ok = $false }
  try {
    Invoke-WebRequest -Uri $zipUrl -UserAgent $UA -OutFile $zipPath -UseBasicParsing -TimeoutSec 300
    $entry.zip_bytes = (Get-Item $zipPath).Length
    $stageZip = Join-Path $Stage "$pmc`_supplements_extract"
    if (Test-Path $stageZip) { Remove-Item -Recurse -Force $stageZip }
    Copy-Item $zipPath "$zipPath.zip" -Force
    Expand-Archive -Path "$zipPath.zip" -DestinationPath $stageZip -Force
    Remove-Item -Force "$zipPath.zip"
    $members = Get-ChildItem $stageZip -File
    $entry.members = @()
    foreach ($m in $members) {
      $kind = 'pdf'; if ($m.Extension -match '\.(tif|tiff)$') { $kind = 'tif' }
      $good = Test-Magic $m.FullName $kind
      $entry.members += @{ name = $m.Name; bytes = $m.Length; magic_ok = $good }
      Write-Host ("MEMBER`t{0}`t{1}`t{2}`t{3}" -f $pmc, $m.Name, $m.Length, $good)
    }
    $entry.ok = $true
  } catch {
    $entry.error = $_.Exception.Message
    if ($_.Exception.InnerException) { $entry.inner = $_.Exception.InnerException.Message }
  }
  $Log += New-Object PSObject -Property $entry
}

# ---- Route B: article PDFs (magic-checked; first %PDF route wins) ----
$pdfTries = @(
  @{ Out = 'PMC7812139_article.pdf'; Urls = @('https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7812139/fullTextPDF', 'https://europepmc.org/articles/PMC7812139?pdf=render') },
  @{ Out = 'PMC7495296_article.pdf'; Urls = @('https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7495296/fullTextPDF', 'https://europepmc.org/articles/PMC7495296?pdf=render') }
)
foreach ($p in $pdfTries) {
  $dest = Join-Path $Stage $p.Out
  $entry = @{ step = "pdf $($p.Out)"; tries = @(); ok = $false }
  foreach ($u in $p.Urls) {
    if ($entry.ok) { break }
    $tmp = "$dest.try"
    $t = @{ url = $u }
    try {
      Invoke-WebRequest -Uri $u -UserAgent $UA -OutFile $tmp -UseBasicParsing -TimeoutSec 300 -MaximumRedirection 8
      $t.bytes = (Get-Item $tmp).Length
      $t.magic_ok = Test-Magic $tmp 'pdf'
      if ($t.magic_ok) {
        Move-Item -Force $tmp $dest
        $entry.ok = $true
      } else { Remove-Item -Force $tmp }
    } catch {
      $t.error = $_.Exception.Message
      if (Test-Path $tmp) { Remove-Item -Force $tmp }
    }
    $entry.tries += New-Object PSObject -Property $t
    Write-Host ("PDFTRY`t{0}`t{1}`t{2}" -f $p.Out, $u, $t.magic_ok)
  }
  $Log += New-Object PSObject -Property $entry
}
$Log | ConvertTo-Json -Depth 6 | Set-Content -Encoding Ascii (Join-Path $Stage 'download_europepmc_log.json')
Write-Host 'DONE'
