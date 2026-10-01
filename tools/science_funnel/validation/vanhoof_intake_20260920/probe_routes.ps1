# VANHOOF INTAKE 20260920 - probe candidate routes for the S1 tif, cheap HEAD/GET probes.
$ErrorActionPreference = 'Continue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'

$Probes = @(
  'https://europepmc.org/articles/PMC7812139/bin/JOA-238-321-s001.tif',
  'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7812139/supplementaryFiles?format=zip',
  'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7812139/fullTextXML'
)
foreach ($u in $Probes) {
  try {
    $r = Invoke-WebRequest -Uri $u -UserAgent $UA -UseBasicParsing -Method Head -TimeoutSec 60 -MaximumRedirection 8
    $len = '?'
    if ($r.Headers['Content-Length']) { $len = $r.Headers['Content-Length'] }
    $ct = '?'
    if ($r.Headers['Content-Type']) { $ct = $r.Headers['Content-Type'] }
    Write-Host ("OK`t{0}`t{1}`t{2}" -f $r.StatusCode, $len, $ct)
    Write-Host ("  $u")
  } catch {
    $code = ''
    if ($_.Exception.Response) { $code = [int]$_.Exception.Response.StatusCode }
    Write-Host ("FAIL`t$code`t$u`t$($_.Exception.Message)")
  }
}
