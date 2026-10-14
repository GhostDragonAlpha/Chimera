# THE OBS-SPLIT-CHANNELS RUN HARNESS (raw stdout via cmd /c; the mine's
# stdout is captured verbatim to mine_pad_channels_out.txt by the mine itself;
# this harness records the raw console echo + exit code for the receipt).
# EPHEMERAL scratch: none (the mine is read-only over the pinned trace).
$ErrorActionPreference = "Continue"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Resolve-Path (Join-Path $here "..\..\..\..")
Set-Location $repo
cmd /c python "tools\science_funnel\validation\obs_split_channels_20260921\mine_pad_channels.py"
$code = $LASTEXITCODE
Write-Host "=== mine exit code: $code ==="
exit $code
