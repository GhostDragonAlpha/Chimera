# VANHOOF INTAKE 20260920 - eutils efetch: article XML (license element + full text
# for the homology vocabulary). Plain NCBI API, no wall. Saved into the staged dir.
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$Stage = 'E:/ChimeraWork/vanhoof-agent/tools/science_funnel/data/vanhoof_forearm'
$UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'

foreach ($pair in @(@('7812139', 'PMC7812139'), @('7495296', 'PMC7495296'))) {
  $num = $pair[0]; $id = $pair[1]
  $url = "https://eutils.ncbi.nlm.nih.gov/eutils/efetch.fcgi?db=pmc&id=$num&retmode=xml"
  $out = Join-Path $Stage "$id`_fulltext.xml"
  try {
    Invoke-WebRequest -Uri $url -UserAgent $UA -OutFile $out -UseBasicParsing -TimeoutSec 300
    $head = (Get-Content $out -TotalCount 2 -Encoding UTF8) -join ' '
    Write-Host ("$id bytes=" + (Get-Item $out).Length + " head=" + $head.Substring(0, [Math]::Min(120, $head.Length)))
  } catch {
    Write-Host ("$id FAIL " + $_.Exception.Message)
  }
}
