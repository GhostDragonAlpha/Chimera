# VANHOOF INTAKE 20260920 - F2 byte-stability, byte-safe method:
#   (a) git ls-tree blob id == git hash-object(worktree file)  => committed == checkout
#   (b) Get-FileHash(worktree) == recorded sha256              => pin matches bytes
#   (c) git check-attr text                                    => -text in force
$ErrorActionPreference = 'Stop'
$Repo = 'E:/ChimeraWork/vanhoof-agent'
Set-Location $Repo

$Files = @(
  @{ P = 'tools/science_funnel/data/vanhoof_forearm/JOA-238-321-s001.tif';              Sha = '3b799371f646fff77eb2f5806249ea8361820c9817aa57225e5b0128d7f1a041' },
  @{ P = 'tools/science_funnel/data/vanhoof_forearm/JOA-238-321-s002.tif';              Sha = 'cb9e91be3d2345182b6d2b956245b76905243d4bbf37fff79c3d96a802e5debe' },
  @{ P = 'tools/science_funnel/data/vanhoof_forearm/PMC7495296_fulltext.xml';           Sha = '7e2b1247c97a805759dd50a16d8ebab3eac4e63ffff3903fb64ee7260be8bcbd' },
  @{ P = 'tools/science_funnel/data/vanhoof_forearm/PMC7812139_fulltext.xml';           Sha = '47cc6b836d0a9b44d8a1ab35dba1c91114291f63721c2db44175de001c1ce8f8' },
  @{ P = 'tools/science_funnel/data/vanhoof_forearm/pmc_cli_interstitial_evidence.html'; Sha = 'e1f44ab8a484fce2c97643d736f661407e883c57dc0476fef26d3cc949e3ed3c' },
  @{ P = 'tools/science_funnel/data/vanhoof_forearm/download_attempts_evidence.json';   Sha = 'c890b4d20b7ff52256629b7a489d3cd5c93c242fc8e32cf202050251a6c4c3ee' }
)
$fail = 0
foreach ($f in $Files) {
  $blobSha = (git ls-tree HEAD -- $f.P).Split()[2]
  $workSha = (git hash-object -- $f.P).Trim()
  $sha256 = (Get-FileHash -Path $f.P -Algorithm SHA256).Hash.ToLower()
  $checkoutOk = ($blobSha -eq $workSha)
  $pinOk = ($sha256 -eq $f.Sha)
  if (-not ($checkoutOk -and $pinOk)) { $fail++ }
  Write-Host ("{0}`tblob={1}`tpin={2}`t{3}" -f $(if ($checkoutOk -and $pinOk) { 'OK' } else { 'FAIL' }), $checkoutOk, $pinOk, $f.P)
}
$attr = git check-attr text -- 'tools/science_funnel/data/vanhoof_forearm/JOA-238-321-s001.tif'
Write-Host ("attr: " + $attr)
Write-Host ("failures: " + $fail)
