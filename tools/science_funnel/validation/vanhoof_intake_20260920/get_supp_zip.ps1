# VANHOOF INTAKE 20260920 - GET the supplementaryFiles?format=zip and inspect bytes.
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$Stage = 'E:/ChimeraWork/vanhoof-agent/tools/science_funnel/data/vanhoof_forearm'
$UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'

$u = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7812139/supplementaryFiles?format=zip'
$out = Join-Path $Stage 'PMC7812139_suppfmt.zip'
Invoke-WebRequest -Uri $u -UserAgent $UA -OutFile $out -UseBasicParsing -TimeoutSec 300
$b = [System.IO.File]::ReadAllBytes($out)
Write-Host ("bytes: " + $b.Length)
Write-Host ("magic: " + (($b[0..15] | ForEach-Object { $_.ToString('X2') }) -join ' '))
if ($b.Length -lt 400) { Write-Host ([System.Text.Encoding]::ASCII.GetString($b)) }
