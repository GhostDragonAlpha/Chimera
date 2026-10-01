# VANHOOF INTAKE 20260920 - diagnose supplementaryFiles: known-good article vs vanhoof.
$ErrorActionPreference = 'Continue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$Stage = 'E:/ChimeraWork/vanhoof-agent/tools/science_funnel/data/vanhoof_forearm'
$UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'

foreach ($id in @('PMC13425262', 'PMC7812139', 'PMC7495296')) {
  $out = Join-Path $Stage ("probe_" + $id + ".zip")
  try {
    Invoke-WebRequest -Uri "https://www.ebi.ac.uk/europepmc/webservices/rest/$id/supplementaryFiles" -UserAgent $UA -OutFile $out -UseBasicParsing -TimeoutSec 300
    $b = [System.IO.File]::ReadAllBytes($out)
    $magic = (($b[0..3] | ForEach-Object { $_.ToString('X2') }) -join ' ')
    Write-Host ("$id bytes=" + $b.Length + " magic=" + $magic)
  } catch {
    $code = ''
    if ($_.Exception.Response) { $code = [int]$_.Exception.Response.StatusCode }
    Write-Host ("$id FAIL " + $code + " " + $_.Exception.Message)
  }
}
