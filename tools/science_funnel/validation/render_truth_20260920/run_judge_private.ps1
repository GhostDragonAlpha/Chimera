# run_judge_private.ps1 -- THE JUDGE ON A LANE-PRIVATE OLLAMA (lane
# render-truth-20260920). The SHARED ollama (11434) timed out three times at
# its own fixed 5-minute llama-server start budget (named in the server log:
# "Load failed ... timed out waiting for llama-server to start"; the model +
# 61k KV needs a few minutes more while sibling lanes' engines hold the
# GPU). This runner starts a LANE-PRIVATE ollama serve on 127.0.0.1:11435
# with a 30-minute load budget, SAME model bytes (OLLAMA_MODELS inherited
# explicitly), and runs the UNCHANGED judge protocol against it. The lane
# server is killed when the judge returns. Nothing shared is touched.
$ErrorActionPreference = "Stop"
$Lane = "E:\ChimeraWork\rendertruth-agent\tools\science_funnel\validation\render_truth_20260920"
$Port = 11435

# the port must be free (never touch another process's server)
$held = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($held) { Write-Output "port $Port is held -- refusing"; exit 1 }

$env:OLLAMA_HOST = "127.0.0.1:$Port"
$env:OLLAMA_LOAD_TIMEOUT = "30m"
$env:OLLAMA_MODELS = "D:\ollama\models"
$env:OLLAMA_NOPRUNE = "1"
$server = Start-Process -FilePath "ollama" -ArgumentList "serve" `
    -WindowStyle Hidden -PassThru
Write-Output ("lane ollama pid " + $server.Id + " on " + $env:OLLAMA_HOST)

$up = $false
for ($i = 1; $i -le 30; $i++) {
    Start-Sleep -Seconds 1
    try {
        $null = Invoke-RestMethod -Uri ("http://127.0.0.1:" + $Port + "/api/tags") -TimeoutSec 2
        $up = $true; break
    } catch { }
}
if (-not $up) { Write-Output "lane ollama never answered"; try { Stop-Process -Id $server.Id -Force } catch {}; exit 1 }
Write-Output "lane ollama answers"

python -u (Join-Path $Lane "render_truth_judge.py") `
    --frames (Join-Path $Lane "frames") `
    --capture-record (Join-Path $Lane "capture_record.json") `
    --n 12 --url ("http://127.0.0.1:" + $Port)
$rc = $LASTEXITCODE

try { Stop-Process -Id $server.Id -Force } catch { }
Start-Sleep -Milliseconds 800
Write-Output ("judge rc=" + $rc + "; lane ollama stopped")
exit $rc
