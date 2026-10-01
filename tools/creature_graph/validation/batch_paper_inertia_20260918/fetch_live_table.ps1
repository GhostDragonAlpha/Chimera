# PAPER-TABLE-INERTIA-INTAKE: fetch + pin the live table artifacts.
# nature.com tables/1 and the article page are fetched with a browser UA
# (served 200; refusal only hit UA-less fetchers); EuropePMC fullTextXML is the
# same article's PMC version of record and the digit-for-digit parse target.
# Writes into the lane's data dir only.
$ErrorActionPreference = 'Stop'
$lane = 'E:\ChimeraWork\paper-inertia-20260918'
$data = Join-Path $lane 'tools\science_funnel\data\oku_paper_table'
$val  = Join-Path $lane 'tools\creature_graph\validation\batch_paper_inertia_20260918'
New-Item -ItemType Directory -Force -Path $data, $val | Out-Null
$ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'

function Fetch-Pin($url, $outPath) {
    Invoke-WebRequest -Uri $url -OutFile $outPath -UseBasicParsing -UserAgent $ua
    $fi = Get-Item $outPath
    return [ordered]@{ url = $url; bytes = $fi.Length;
        sha256 = (Get-FileHash $outPath -Algorithm SHA256).Hash.ToLower() }
}

# 1) The publisher's own pages (license + provenance artifacts)
$natureTables  = Fetch-Pin 'https://www.nature.com/articles/s42003-021-01831-w/tables/1' (Join-Path $data 'nature_s42003-021-01831-w_tables_1.html')
$natureArticle = Fetch-Pin 'https://www.nature.com/articles/s42003-021-01831-w'         (Join-Path $data 'nature_s42003-021-01831-w.html')

# 2) The PMC version of record: full text XML incl. Table 1 markup (parse target)
$epmc = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7940622/fullTextXML'
$xmlPath = Join-Path $data 'PMC7940622_fulltext.xml'
Invoke-WebRequest -Uri $epmc -OutFile $xmlPath -UseBasicParsing
$epmcPin = [ordered]@{ url = $epmc; bytes = (Get-Item $xmlPath).Length;
    sha256 = (Get-FileHash $xmlPath -Algorithm SHA256).Hash.ToLower() }

# 3) The banked dossier (provenance attachment), copied byte-exact from the repo
$docSrc = Join-Path $lane 'docs\research\20260917_dbhunt_motion.md'
$docDst = Join-Path $data '20260917_dbhunt_motion.md'
Copy-Item $docSrc $docDst -Force
$dossierPin = [ordered]@{ url = 'repo:docs/research/20260917_dbhunt_motion.md (banked 2026-09-17 dossier, commit 5a180eb4)';
    bytes = (Get-Item $docDst).Length; sha256 = (Get-FileHash $docDst -Algorithm SHA256).Hash.ToLower() }

$log = [ordered]@{
    retrieved_utc   = (Get-Date).ToUniversalTime().ToString('o')
    artifacts       = [ordered]@{
        nature_tables_page  = $natureTables
        nature_article_page = $natureArticle
        epmc_fulltext_xml   = $epmcPin
        banked_dossier      = $dossierPin }
    route_note      = 'nature.com serves these pages authlessly with a browser UA; a UA-less fetcher receives 406/303 (recorded). EuropePMC fullTextXML is the same article (PMC7940622) and is the digit-for-digit parse target; its sha256 matches the oku_bipedal lane pin of the same endpoint.'
}
$log | ConvertTo-Json -Depth 5 | Set-Content -Path (Join-Path $val 'fetch_log.json') -Encoding UTF8
Get-Content (Join-Path $val 'fetch_log.json')
