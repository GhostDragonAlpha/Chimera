# copies: repo CHIMERA_PROOF (committed), lane validation dir (sane size),
# desktop CHIMERA_PROOF. The movie itself is copied by this script only after
# the encode exists; run AFTER encode.
$src = "E:\ChimeraWork\rbmovie-agent\CHIMERA_PROOF\REAL_BODY_SLICE\real_body_slice.mp4"
if (-not (Test-Path $src)) { Write-Output "missing $src"; exit 1 }
New-Item -ItemType Directory -Force -Path "E:\ChimeraWork\rbmovie-agent\tools\science_funnel\validation\realbody_movie_20260920\movie" | Out-Null
New-Item -ItemType Directory -Force -Path "C:\Users\allen\Desktop\CHIMERA_PROOF\REAL_BODY_SLICE" | Out-Null
Copy-Item $src "E:\ChimeraWork\rbmovie-agent\tools\science_funnel\validation\realbody_movie_20260920\movie\real_body_slice.mp4" -Force
Copy-Item $src "C:\Users\allen\Desktop\CHIMERA_PROOF\REAL_BODY_SLICE\real_body_slice.mp4" -Force
Get-Item $src, "E:\ChimeraWork\rbmovie-agent\tools\science_funnel\validation\realbody_movie_20260920\movie\real_body_slice.mp4", "C:\Users\allen\Desktop\CHIMERA_PROOF\REAL_BODY_SLICE\real_body_slice.mp4" | Select-Object FullName, Length | Format-List
