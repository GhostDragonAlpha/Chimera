# VANHOOF INTAKE 20260920 - PMC downloads to the staged path (runbook step 1).
# No inline -Command; every status logged; failures named, never silently retried here.
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Stage = 'E:/ChimeraWork/vanhoof-agent/tools/science_funnel/data/vanhoof_forearm'
New-Item -ItemType Directory -Force -Path $Stage | Out-Null
$UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'

$Targets = @(
  @{ Out = 'JOA-238-321-s001.tif'; Url = 'https://pmc.ncbi.nlm.nih.gov/articles/instance/7812139/bin/JOA-238-321-s001.tif' },
  @{ Out = 'JOA-238-321-s002.tif'; Url = 'https://pmc.ncbi.nlm.nih.gov/articles/instance/7812139/bin/JOA-238-321-s002.tif' },
  @{ Out = 'PMC7812139_article.pdf'; Url = 'https://pmc.ncbi.nlm.nih.gov/articles/PMC7812139/pdf/' },
  @{ Out = 'PMC7495296_article.pdf'; Url = 'https://pmc.ncbi.nlm.nih.gov/articles/PMC7495296/pdf/' },
  @{ Out = 'JOA-237-774-s004.pdf'; Url = 'https://pmc.ncbi.nlm.nih.gov/articles/instance/7495296/bin/JOA-237-774-s004.pdf' }
)

$Log = @()
foreach ($t in $Targets) {
  $dest = Join-Path $Stage $t.Out
  $tmp = Join-Path $Stage ($t.Out + '.part')
  $entry = @{ file = $t.Out; url = $t.Url; ok = $false }
  try {
    $resp = Invoke-WebRequest -Uri $t.Url -UserAgent $UA -OutFile $tmp -UseBasicParsing -PassThru -TimeoutSec 300 -MaximumRedirection 8
    $len = (Get-Item $tmp).Length
    $entry.status = [int]$resp.StatusCode
    $entry.bytes = $len
    if ($len -gt 0) {
      Move-Item -Force -Path $tmp -Destination $dest
      $entry.ok = $true
    }
  } catch {
    $entry.status = 'ERROR'
    $entry.error = $_.Exception.Message
    if ($_.Exception.InnerException) { $entry.inner = $_.Exception.InnerException.Message }
    $entry.at = $_.InvocationInfo.PositionMessage
    if (Test-Path $tmp) { Remove-Item -Force $tmp }
  }
  $Log += New-Object PSObject -Property $entry
  Write-Host ("{0}`t{1}`t{2}" -f $t.Out, $entry.status, $(if ($entry.bytes) { $entry.bytes } else { $entry.error }))
}
$Log | ConvertTo-Json -Depth 4 | Set-Content -Encoding Ascii (Join-Path $Stage 'download_status_log.json')
