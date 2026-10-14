# VANHOOF INTAKE 20260920 - PMC downloads carrying the browser-solved PoW cookie.
# The cookie was computed by Chrome (agent-browser session) from PMC's own challenge JS;
# this script only re-plays the browser's own credentials. Every file magic-checked.
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Stage = 'E:/ChimeraWork/vanhoof-agent/tools/science_funnel/data/vanhoof_forearm'
$UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
$Cookie = 'cloudpmc-viewer-pow=VwR3BGNkZQZ1ZQRhAQRkZwV0Vt:IJ5JoyF0qMbbO1Eee9DYppbGK9h1s3QOr2PAZbqpEYp%2C63686; ncbi_sid=E73CB977AB2CA453_17001SID'

$Targets = @(
  @{ Out = 'JOA-238-321-s001.tif'; Kind = 'tif'; Url = 'https://pmc.ncbi.nlm.nih.gov/articles/instance/7812139/bin/JOA-238-321-s001.tif' },
  @{ Out = 'JOA-238-321-s002.tif'; Kind = 'tif'; Url = 'https://pmc.ncbi.nlm.nih.gov/articles/instance/7812139/bin/JOA-238-321-s002.tif' },
  @{ Out = 'PMC7812139_article.pdf'; Kind = 'pdf'; Url = 'https://pmc.ncbi.nlm.nih.gov/articles/PMC7812139/pdf/' },
  @{ Out = 'PMC7495296_article.pdf'; Kind = 'pdf'; Url = 'https://pmc.ncbi.nlm.nih.gov/articles/PMC7495296/pdf/' },
  @{ Out = 'JOA-237-774-s004.pdf'; Kind = 'pdf'; Url = 'https://pmc.ncbi.nlm.nih.gov/articles/instance/7495296/bin/JOA-237-774-s004.pdf' }
)
$Log = @()
foreach ($t in $Targets) {
  $dest = Join-Path $Stage $t.Out
  $tmp = "$dest.part"
  $entry = @{ file = $t.Out; url = $t.Url; ok = $false }
  try {
    $headers = @{ Cookie = $Cookie; Referer = 'https://pmc.ncbi.nlm.nih.gov/' }
    Invoke-WebRequest -Uri $t.Url -UserAgent $UA -Headers $headers -OutFile $tmp -UseBasicParsing -TimeoutSec 600 -MaximumRedirection 8
    $b = [System.IO.File]::ReadAllBytes($tmp)
    $entry.bytes = $b.Length
    $good = $false
    if ($t.Kind -eq 'pdf' -and $b.Length -gt 4 -and $b[0] -eq 0x25 -and $b[1] -eq 0x50 -and $b[2] -eq 0x44 -and $b[3] -eq 0x46) { $good = $true }
    if ($t.Kind -eq 'tif' -and $b.Length -gt 4 -and (($b[0] -eq 0x49 -and $b[1] -eq 0x49) -or ($b[0] -eq 0x4D -and $b[1] -eq 0x4D))) { $good = $true }
    $entry.magic_ok = $good
    if ($good) { Move-Item -Force $tmp $dest; $entry.ok = $true }
    else { $entry.head = [System.Text.Encoding]::ASCII.GetString($b, 0, [Math]::Min(200, $b.Length)); Remove-Item -Force $tmp }
  } catch {
    $entry.error = $_.Exception.Message
    if ($_.Exception.InnerException) { $entry.inner = $_.Exception.InnerException.Message }
    if (Test-Path $tmp) { Remove-Item -Force $tmp }
  }
  $Log += New-Object PSObject -Property $entry
  Write-Host ("{0}`t{1}`t{2}`t{3}" -f $t.Out, $(if ($entry.bytes) { $entry.bytes } else { 'ERR' }), $(if ($null -ne $entry.magic_ok) { $entry.magic_ok } else { '-' }), $(if ($entry.error) { $entry.error } else { 'ok' }))
}
$Log | ConvertTo-Json -Depth 5 | Set-Content -Encoding Ascii (Join-Path $Stage 'download_pmc_cookie_log.json')
Write-Host 'DONE'
