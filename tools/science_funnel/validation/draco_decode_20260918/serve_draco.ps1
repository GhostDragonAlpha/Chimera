param(
  [int]$Port = 8791
)
$ErrorActionPreference = 'Stop'

$Base    = Split-Path -Parent $MyInvocation.MyCommand.Path
$CdnDir  = Join-Path $Base 'cdn'
$Stage   = Join-Path $Base 'staging'
$OutDir  = Join-Path $Base 'out'
$LogDir  = Join-Path $Base 'logs'
$RepoGlb = 'E:\ChimeraWork\draco-decode-20260918\tools\science_funnel\data\smithsonian'
foreach ($d in @($CdnDir, $Stage, $OutDir, $LogDir)) {
  New-Item -ItemType Directory -Force -Path $d | Out-Null
}

$LibWhitelist = @('three.module.js','GLTFLoader.js','DRACOLoader.js',
                  'draco_wasm_wrapper.js','draco_decoder.wasm',
                  'BufferGeometryUtils.js')

function Write-Log([string]$msg) {
  $line = '{0} {1}' -f (Get-Date -Format o), $msg
  [System.IO.File]::AppendAllText((Join-Path $LogDir 'listener.log'),
                                 $line + "`r`n", [System.Text.Encoding]::UTF8)
}

function Send-Bytes([System.Net.Sockets.NetworkStream]$s, [string]$status,
                    [string]$ctype, [byte[]]$bytes) {
  $head = [System.Text.Encoding]::ASCII.GetBytes(
    "HTTP/1.1 $status`r`nContent-Type: $ctype`r`nContent-Length: $($bytes.Length)`r`nConnection: close`r`nCache-Control: no-store`r`n`r`n")
  $s.Write($head, 0, $head.Length)
  $s.Write($bytes, 0, $bytes.Length)
}

function Send-File([System.Net.Sockets.NetworkStream]$s, [string]$path, [string]$ctype) {
  if ((Test-Path $path) -and (Get-Item $path).PSIsContainer -eq $false) {
    $b = [System.IO.File]::ReadAllBytes($path)
    Send-Bytes $s '200 OK' $ctype $b
    Write-Log ("200 {0} ({1} bytes)" -f $path, $b.Length)
  } else {
    Send-Bytes $s '404 Not Found' 'text/plain' ([System.Text.Encoding]::ASCII.GetBytes('not found'))
    Write-Log "404 $path"
  }
}

function Read-Request([System.Net.Sockets.NetworkStream]$s) {
  $ms = New-Object System.IO.MemoryStream
  $buf = New-Object byte[] 65536
  $headerEnd = -1
  $contentLen = 0
  $head = ''
  $s.ReadTimeout = 120000
  while ($true) {
    if ($headerEnd -lt 0) {
      $scan = [Math]::Min([int]$ms.Length, 65536)
      if ($scan -gt 0) {
        $text = [System.Text.Encoding]::ASCII.GetString($ms.GetBuffer(), 0, $scan)
        $headerEnd = $text.IndexOf("`r`n`r`n")
        if ($headerEnd -ge 0) {
          $head = $text.Substring(0, $headerEnd)
          foreach ($line in ($head -split "`r`n")) {
            if ($line -match '^(?i)Content-Length:\s*(\d+)') { $contentLen = [int]$Matches[1] }
          }
        }
      }
    }
    if ($headerEnd -ge 0) {
      $bodyStart = $headerEnd + 4
      $total = $bodyStart + $contentLen
      if ([int]$ms.Length -ge $total) {
        $body = New-Object byte[] $contentLen
        [Array]::Copy($ms.GetBuffer(), $bodyStart, $body, 0, $contentLen)
        return @{ head = $head; body = $body }
      }
    }
    $n = $s.Read($buf, 0, $buf.Length)
    if ($n -le 0) { return $null }
    $ms.Write($buf, 0, $n)
    if ($ms.Length -gt 128MB) { throw 'request too large' }
  }
}

$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
$listener.Start(64)
[System.IO.File]::WriteAllText((Join-Path $LogDir 'listener.ready'),
  "listening on 127.0.0.1:$Port`r`n")
Write-Log "READY on 127.0.0.1:$Port"

while ($true) {
  try {
    $client = $listener.AcceptTcpClient()
  } catch {
    break
  }
  try {
    $stream = $client.GetStream()
    $req = Read-Request $stream
    if ($null -eq $req) { $client.Close(); continue }
    $firstLine = ($req.head -split "`r`n")[0]
    Write-Log $firstLine
    $parts = $firstLine -split ' '
    $method = $parts[0]
    $rawPath = if ($parts.Length -gt 1) { $parts[1] } else { '/' }
    $path = [Uri]::UnescapeDataString(($rawPath -split '\?')[0])

    if ($path -match '\.\.') {
      Send-Bytes $stream '400 Bad Request' 'text/plain' ([System.Text.Encoding]::ASCII.GetBytes('bad path'))
      continue
    }

    if ($method -eq 'GET') {
      switch -Regex ($path) {
        '^/harness$'            { Send-File $stream (Join-Path $Base 'harness.html') 'text/html; charset=utf-8'; continue }
        '^/jobs\.json$'         { Send-File $stream (Join-Path $Stage 'jobs.json') 'application/json'; continue }
        '^/lib/([A-Za-z0-9._-]+)$' {
          $name = $Matches[1]
          if ($LibWhitelist -contains $name) {
            $ctype = if ($name.EndsWith('.wasm')) { 'application/wasm' } else { 'text/javascript' }
            Send-File $stream (Join-Path $CdnDir $name) $ctype
          } else {
            Send-Bytes $stream '403 Forbidden' 'text/plain' ([System.Text.Encoding]::ASCII.GetBytes('forbidden'))
          }
          continue
        }
        '^/utils/([A-Za-z0-9._-]+)$' {
          $name = $Matches[1]
          if ($LibWhitelist -contains $name) {
            Send-File $stream (Join-Path $CdnDir $name) 'text/javascript'
          } else {
            Send-Bytes $stream '403 Forbidden' 'text/plain' ([System.Text.Encoding]::ASCII.GetBytes('forbidden'))
          }
          continue
        }
        '^/glb/([A-Za-z0-9._-]+\.glb)$' {
          Send-File $stream (Join-Path $RepoGlb $Matches[1]) 'model/gltf-binary'; continue
        }
        '^/corrupt/([A-Za-z0-9._-]+\.glb)$' {
          Send-File $stream (Join-Path $Stage $Matches[1]) 'model/gltf-binary'; continue
        }
        default {
          Send-Bytes $stream '404 Not Found' 'text/plain' ([System.Text.Encoding]::ASCII.GetBytes('not found'))
          continue
        }
      }
    }
    elseif ($method -eq 'POST') {
      if ($path -eq '/done') {
        $tag = [System.Text.Encoding]::UTF8.GetString($req.body).Trim()
        [System.IO.File]::WriteAllText((Join-Path $OutDir ("done.{0}.marker" -f $tag)),
          "done`r`n")
        Send-Bytes $stream '200 OK' 'text/plain' ([System.Text.Encoding]::ASCII.GetBytes('bye'))
        continue
      }
      if ($path -match '^/results/([A-Za-z0-9._-]+)$') {
        $dest = Join-Path $OutDir ($Matches[1])
        [System.IO.File]::WriteAllBytes($dest, $req.body)
        Send-Bytes $stream '200 OK' 'text/plain' ([System.Text.Encoding]::ASCII.GetBytes('saved'))
        Write-Log ("saved {0} ({1} bytes)" -f $dest, $req.body.Length)
        continue
      }
      Send-Bytes $stream '404 Not Found' 'text/plain' ([System.Text.Encoding]::ASCII.GetBytes('not found'))
    }
    else {
      Send-Bytes $stream '405 Method Not Allowed' 'text/plain' ([System.Text.Encoding]::ASCII.GetBytes('method'))
    }
  } catch {
    Write-Log ("ERROR {0}" -f $_.Exception.Message)
    try {
      Send-Bytes $stream '500 Internal Server Error' 'text/plain' ([System.Text.Encoding]::ASCII.GetBytes('error'))
    } catch { }
  } finally {
    try { $client.Close() } catch { }
  }
}
