# sweep_leaked_headless.ps1 -- automation hygiene, the realbody lane's own
# lesson (a wedged automation run leaked 31 Chrome processes and starved the
# machine). Kills ONLY chrome processes whose command line names 'headless':
# the user's desktop browser is never touched. Safe to run anytime.
$procs = Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" |
    Where-Object { $_.CommandLine -match 'headless' }
foreach ($p in $procs) {
    Write-Output ("sweep: killing leaked headless chrome pid {0}" -f $p.ProcessId)
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Milliseconds 800
$left = (Get-Process chrome -ErrorAction SilentlyContinue).Count
Write-Output ("sweep: {0} chrome process(es) remaining (desktop browser untouched)" -f $left)
