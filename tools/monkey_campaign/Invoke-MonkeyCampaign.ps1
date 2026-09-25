param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('validate','plan','packet','storage','checkpoint')]
    [string]$Action,
    [string]$ApprovedSha256 = $env:CHIMERA_MONKEY_APPROVED_SHA256,
    [string]$SessionPath,
    [string]$SnapshotPath,
    [string]$BindingsPath,
    [int]$HarnessLimit = 0,
    [int]$ActiveSubagents = 0,
    [string]$VolumePath = 'E:\',
    [string]$TaskId,
    [string]$ScanPath,
    [string]$ReceiptPath,
    [string]$ContextPath,
    [string]$ContextSha256,
    [string]$EvidenceRoot,
    [switch]$IncludeConditional
)
$ErrorActionPreference = 'Stop'
$campaignArgs = @((Join-Path $PSScriptRoot 'campaign.py'))
if ($ApprovedSha256) { $campaignArgs += @('--approved-sha256', $ApprovedSha256) }
$campaignArgs += $Action
switch ($Action) {
    'checkpoint' {
        if (-not $ReceiptPath -or -not $ContextPath -or -not $ContextSha256 -or -not $EvidenceRoot) {
            throw 'ReceiptPath, ContextPath, ContextSha256 and EvidenceRoot are required.'
        }
        $campaignArgs += @($ReceiptPath, '--context', $ContextPath,
                          '--context-sha256', $ContextSha256, '--evidence-root', $EvidenceRoot)
    }
    'plan' {
        if ((-not $SessionPath -and -not $SnapshotPath) -or ($SessionPath -and $SnapshotPath)) {
            throw 'Supply exactly one provisioned SessionPath or timestamped SnapshotPath.'
        }
        if (-not $BindingsPath -or $HarnessLimit -lt 1) { throw 'BindingsPath and actual HarnessLimit are required.' }
        if ($SessionPath) { $campaignArgs += @('--session', $SessionPath) }
        else { $campaignArgs += @('--snapshot', $SnapshotPath) }
        $campaignArgs += @('--bindings', $BindingsPath, '--harness-limit', "$HarnessLimit",
                          '--active-subagents', "$ActiveSubagents", '--volume-path', $VolumePath)
        if ($IncludeConditional) { $campaignArgs += '--include-conditional' }
    }
    'packet' {
        if (-not $TaskId) { throw 'TaskId is required.' }
        $campaignArgs += $TaskId
    }
    'storage' {
        if (-not $ScanPath) { throw 'ScanPath is required.' }
        $campaignArgs += $ScanPath
    }
}
& python @campaignArgs
exit $LASTEXITCODE
