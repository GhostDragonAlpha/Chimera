# VANHOOF INTAKE 20260920 - NCBI OA file list: locate the articles' oa_package paths.
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$Stage = 'E:/ChimeraWork/vanhoof-agent/tools/science_funnel/validation/vanhoof_intake_20260920'
$UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'

$listGz = Join-Path $Stage 'oa_file_list.csv.gz'
$listCsv = Join-Path $Stage 'oa_file_list.csv'
if (-not (Test-Path $listCsv)) {
  Invoke-WebRequest -Uri 'https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_file_list.csv.gz' -UserAgent $UA -OutFile $listGz -UseBasicParsing -TimeoutSec 600
  tar -xzf $listGz -C $Stage
}
Write-Host ("csv bytes: " + (Get-Item $listCsv).Length)
$hits = Select-String -Path $listCsv -Pattern ',PMC(7812139|7495296),' | ForEach-Object { $_.Line }
Write-Host ("hits: " + $hits.Count)
$hits | ForEach-Object { Write-Host $_ }
Set-Content -Encoding Ascii (Join-Path $Stage 'oa_file_list_hits.txt') ($hits -join "`r`n")
