# copies.ps1 -- THE DELIVERY (lane render-truth-20260920). The judged movie
# lands in three places, exactly the realbody-movie lane's delivery shape:
# the repo's CHIMERA_PROOF/REAL_BODY_SLICE/, beside the receipt in the lane
# dir, and the operator's desktop CHIMERA_PROOF/REAL_BODY_SLICE/ (that
# folder only -- nothing else on the desktop is touched). Prints sha256 for
# every copy.
$ErrorActionPreference = "Stop"
$Root = "E:\ChimeraWork\rendertruth-agent"
$Lane = Join-Path $Root "tools\science_funnel\validation\render_truth_20260920"
$Src = Join-Path $Lane "real_body_slice_v2.mp4"
if (-not (Test-Path $Src)) { Write-Output "movie missing: $Src"; exit 1 }

$Targets = @(
    (Join-Path $Root "CHIMERA_PROOF\REAL_BODY_SLICE"),
    $Lane,
    (Join-Path ([Environment]::GetFolderPath("Desktop")) "CHIMERA_PROOF\REAL_BODY_SLICE")
)
foreach ($t in $Targets) {
    New-Item -ItemType Directory -Force -Path $t | Out-Null
    $dst = Join-Path $t "real_body_slice_v2.mp4"
    if ((Resolve-Path $t).Path -ne (Resolve-Path (Split-Path $Src)).Path) {
        Copy-Item -Force $Src $dst
    }
    $h = (Get-FileHash -Algorithm SHA256 $dst).Hash.ToLower()
    Write-Output ("copy {0} sha256 {1}" -f $dst, $h)
}
