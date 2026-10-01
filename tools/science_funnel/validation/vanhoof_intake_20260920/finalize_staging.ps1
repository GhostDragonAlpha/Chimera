# VANHOOF INTAKE 20260920 - consolidate download-attempt evidence, clean probe junk,
# compute sha256 pins for every staged file (runbook step 2).
$ErrorActionPreference = 'Stop'
$Stage = 'E:/ChimeraWork/vanhoof-agent/tools/science_funnel/data/vanhoof_forearm'

# consolidate the three small attempt logs into one evidence file (delete bulk junk first)
$junk = @('probe_PMC13425262.zip', 'probe_PMC7495296.zip', 'probe_PMC7812139.zip')
foreach ($j in $junk) {
  $p = Join-Path $Stage $j
  if (Test-Path $p) { Remove-Item -Force $p }
}
$logs = @('download_oa_log.json', 'download_europepmc_log.json', 'download_pmc_cookie_log.json')
$merged = @()
foreach ($l in $logs) {
  $p = Join-Path $Stage $l
  if (Test-Path $p) {
    $merged += @{ log = $l; content = (Get-Content $p -Raw | ConvertFrom-Json) }
    Remove-Item -Force $p
  }
}
$evidence = @{
  attempts = $merged
  routes_tried = @(
    'PMC direct bin/pdf URLs (Invoke-WebRequest, browser UA) -> 200 with ~1.8 KB PoW interstitial "Preparing to download" (evidence: pmc_cli_interstitial_evidence.html)',
    'europepmc REST supplementaryFiles -> errCode 0 errorBean for PMC7812139/PMC7495296 specifically (control PMC13425262 returned a real 3.2 MB zip; endpoint healthy, article absent)',
    'NCBI oa.fcgi -> 404; ftp.ncbi.nlm.nih.gov/pub/pmc/oa_file_list.csv.gz -> 404 (bulk-OA index retired at this path)',
    'Browser (agent-browser Chrome) navigation -> solved PMC PoW (cloudpmc-viewer-pow cookie), TIFFs downloaded; PDF renders inline, no file lands',
    'Browser cookie replay via Invoke-WebRequest -> fresh per-request interstitials (cookie does not validate on new URLs)',
    'agent-browser download command (viewer Download button + article PDF link) -> local CDP stream failure (os error 10060) on this host, reproducible',
    'europepmc ?pdf=render in browser -> Cloudflare "Just a moment" held indefinitely',
    'in-page fetch of PDF from viewer/article context -> 403 (PMC keys on request mode)',
    'eutils efetch db=pmc -> full text XML withheld by publisher ("does not allow downloading of the full text in XML form"); front matter only (kept: PMC*_fulltext.xml)'
  )
}
$merged | ConvertTo-Json -Depth 8 | Set-Content -Encoding Ascii (Join-Path $Stage 'download_attempts_evidence.json')

# sha256 for every remaining file
$files = Get-ChildItem $Stage -File
foreach ($f in $files) {
  $h = (Get-FileHash -Path $f.FullName -Algorithm SHA256).Hash.ToLower()
  Write-Host ("{0}`t{1}`t{2}" -f $f.Name, $f.Length, $h)
}
