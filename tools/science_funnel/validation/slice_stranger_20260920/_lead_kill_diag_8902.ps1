# kill the lead's diagnostic slice server on 8902 (own process only, verified by command line)
$c = Get-NetTCPConnection -LocalPort 8902 -State Listen -ErrorAction SilentlyContinue
if ($c) {
    foreach ($x in $c) {
        $p = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $x.OwningProcess)
        if ($p.CommandLine -like "*slice_server.py*8902*") {
            Stop-Process -Id $x.OwningProcess -Force
            Write-Output ("killed diag server pid " + $x.OwningProcess)
        } else {
            Write-Output ("8902 held by non-slice pid " + $x.OwningProcess + " - left alone")
        }
    }
} else { Write-Output "8902 free" }
