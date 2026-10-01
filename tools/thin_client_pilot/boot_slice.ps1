# thincli lane: boot the declared playable slice (no desktop browser pop) as a
# background process with redirected logs, then wait for /api/health.
param(
  [int]$Port = 0,
  [string]$OutDir = "E:/ChimeraWork/thincli-agent/.tmp/thincli_run"
)
$ErrorActionPreference = "Stop"
if ($Port -eq 0) {
  # bind-tested free port, 8127 refused (the port law)
  $l = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
  $l.Start(); $Port = ([System.Net.IPEndPoint]$l.LocalEndpoint).Port; $l.Stop()
  if ($Port -eq 8127) { $Port = $Port + 1 }
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$py = (Get-Command python.exe).Source
$p = Start-Process -FilePath $py `
  -ArgumentList @("-u", "E:/ChimeraWork/thincli-agent/tools/thin_client_pilot/boot_slice.py", "--port", "$Port") `
  -WorkingDirectory "E:/ChimeraWork/thincli-agent" `
  -RedirectStandardOutput (Join-Path $OutDir "slice_stdout.log") `
  -RedirectStandardError (Join-Path $OutDir "slice_stderr.log") `
  -WindowStyle Hidden -PassThru
Write-Output "SLICE_PID=$($p.Id)"
Write-Output "SLICE_PORT=$Port"
