# Foundry Monitor — opens visible windows showing live agent activity
# Launch this from PowerShell: .\monitor.ps1

$Host.UI.RawUI.WindowTitle = "FOUNDRY MONITOR"
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       GAUSSIAN FOUNDRY MONITOR          ║" -ForegroundColor Cyan
Write-Host "║    Watching the agents in real-time     ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$BRIDGE_URL = "http://127.0.0.1:8895"
$CHRONICLE_DIR = "E:\PythonChimera\worker_bridge\chronicle"

while($true) {
    Clear-Host
    $date = Get-Date -Format "HH:mm:ss"
    Write-Host "=== $date ===" -ForegroundColor Yellow

    # Bridge status
    try {
        $status = Invoke-RestMethod -Uri "$BRIDGE_URL/api/status" -TimeoutSec 3
        Write-Host "Bridge: $($status.status) | PID: $($status.pid) | WS: $($status.ws_clients)" -ForegroundColor Green
    } catch {
        Write-Host "Bridge: DOWN" -ForegroundColor Red
    }

    # Agent state
    try {
        $state = Invoke-RestMethod -Uri "$BRIDGE_URL/api/get_state" -TimeoutSec 3
        $streaming = if ($state.data.isStreaming) { "STREAMING" } else { "idle" }
        $color = if ($state.data.isStreaming) { "Yellow" } else { "Green" }
        Write-Host "Agent: $streaming | Messages: $($state.data.messageCount) | Model: $($state.data.model.id)" -ForegroundColor $color
    } catch {
        Write-Host "Agent: DOWN" -ForegroundColor Red
    }

    # Chronicle files
    if (Test-Path $CHRONICLE_DIR) {
        $files = Get-ChildItem $CHRONICLE_DIR -Filter "*.txt" | Sort-Object LastWriteTime -Descending
        $recent = $files | Select-Object -First 3
        Write-Host ""
        Write-Host "=== Recent Chronicle ===" -ForegroundColor Cyan
        foreach ($f in $recent) {
            $content = Get-Content $f.FullName -Raw
            $preview = $content.Substring(0, [Math]::Min(200, $content.Length))
            Write-Host ""
            Write-Host "--- $($f.Name) ($($f.Length) bytes) ---" -ForegroundColor Magenta
            Write-Host $preview
        }

        # Forge logs
        $forgeLogs = Get-ChildItem $CHRONICLE_DIR -Filter "forge_*.log" | Sort-Object LastWriteTime -Descending
        $latestLog = $forgeLogs | Select-Object -First 1
        if ($latestLog) {
            $logContent = Get-Content $latestLog.FullName -Raw
            Write-Host ""
            Write-Host "=== Forge Log ($($latestLog.Name)) ===" -ForegroundColor Cyan
            $lines = $logContent -split "`n"
            $lines | Where-Object { $_ -match "STAGE|PASSED|FAILED|COMPLETE|ERROR" } | ForEach-Object {
                Write-Host $_ -ForegroundColor Yellow
            }
        }

        # Forge results
        $results = Get-ChildItem $CHRONICLE_DIR -Filter "forge_result_*.json" | Sort-Object LastWriteTime -Descending
        $latestResult = $results | Select-Object -First 1
        if ($latestResult) {
            $resultData = Get-Content $latestResult.FullName -Raw | ConvertFrom-Json
            Write-Host ""
            Write-Host "=== Last Result ===" -ForegroundColor Cyan
            if ($resultData.success) {
                Write-Host "PASS" -ForegroundColor Green
            } else {
                Write-Host "FAIL at $($resultData.failed_at): $($resultData.failure_reason)" -ForegroundColor Red
            }
        }
    }

    # Also check if the worker is currently streaming (show recent messages)
    try {
        $msgs = Invoke-RestMethod -Uri "$BRIDGE_URL/api/get_messages" -TimeoutSec 5
        $lastMsg = $msgs.data.messages[-1]
        if ($lastMsg -and $lastMsg.role -eq "assistant") {
            $text = $lastMsg.content
            if ($text -is [array]) {
                $text = ($text | Where-Object { $_.type -eq "text" } | ForEach-Object { $_.text }) -join " "
            }
            if ($text.Length -gt 50) {
                Write-Host ""
                Write-Host "=== Last Response ===" -ForegroundColor Cyan
                Write-Host $text.Substring(0, [Math]::Min(500, $text.Length))
            }
        }
    } catch {}

    Start-Sleep 5
}
