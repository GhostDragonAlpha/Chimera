# =============================================================================
# Chimera Build Logger - Structured Logging Utility
# =============================================================================
# Parses Unreal Build Tool output for errors/warnings, generates JSON logs,
# tracks build duration per module, and identifies slow-compiling files.
# =============================================================================

function Write-BuildLogEntry {
    param(
        [string]$EventType,
        [string]$Message,
        [string]$Module = "",
        [double]$DurationMs = 0,
        [string]$FileName = "",
        [int]$LineNumber = 0,
        [string]$ErrorCode = ""
    )

    $timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fff"

    $entry = @{
        timestamp   = $timestamp
        eventType   = $EventType
        message     = $Message
        module      = $Module
        durationMs  = $DurationMs
        fileName    = $FileName
        lineNumber  = $LineNumber
        errorCode   = $ErrorCode
    }

    return $entry
}

function Start-BuildTimer {
    param([string]$ModuleName)

    $timer = New-Object System.Diagnostics.Stopwatch
    $timer.Start()

    $global:BuildTimers[$ModuleName] = @{
        Timer     = $timer
        StartTime = Get-Date
        Files     = @{}
        Errors    = 0
        Warnings  = 0
    }

    return $timer
}

function Stop-BuildTimer {
    param([string]$ModuleName)

    if ($global:BuildTimers.ContainsKey($ModuleName)) {
        $timerData = $global:BuildTimers[$ModuleName]
        $timerData.Timer.Stop()

        $timerData.EndTime = Get-Date
        $timerData.DurationMs = $timerData.Timer.Elapsed.TotalMilliseconds

        $global:BuildTimers[$ModuleName] = $timerData
    }
}

function Add-BuildFileTiming {
    param(
        [string]$ModuleName,
        [string]$FilePath,
        [double]$CompileTimeMs
    )

    if ($global:BuildTimers.ContainsKey($ModuleName)) {
        $timerData = $global:BuildTimers[$ModuleName]
        if (!$timerData.Files.ContainsKey($FilePath)) {
            $timerData.Files[$FilePath] = @{ TotalTime = 0; CompileCount = 0 }
        }

        $timerData.Files[$FilePath].TotalTime += $CompileTimeMs
        $timerData.Files[$FilePath].CompileCount++

        $global:BuildTimers[$ModuleName] = $timerData
    }
}

function Add-BuildError {
    param(
        [string]$ModuleName,
        [string]$Message,
        [string]$FileName = "",
        [int]$LineNumber = 0,
        [string]$ErrorCode = ""
    )

    if ($global:BuildTimers.ContainsKey($ModuleName)) {
        $timerData = $global:BuildTimers[$ModuleName]
        $timerData.Errors++

        if (!$global:ErrorLog) { $global:ErrorLog = @() }
        $errorEntry = @{
            Module     = $ModuleName
            Message    = $Message
            FileName   = $FileName
            LineNumber = $LineNumber
            ErrorCode  = $ErrorCode
            Timestamp  = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fff"
        }
        $global:ErrorLog += $errorEntry

        $global:BuildTimers[$ModuleName] = $timerData
    }
}

function Add-BuildWarning {
    param(
        [string]$ModuleName,
        [string]$Message,
        [string]$FileName = "",
        [int]$LineNumber = 0,
        [string]$WarningCode = ""
    )

    if ($global:BuildTimers.ContainsKey($ModuleName)) {
        $timerData = $global:BuildTimers[$ModuleName]
        $timerData.Warnings++

        if (!$global:WarningLog) { $global:WarningLog = @() }
        $warningEntry = @{
            Module     = $ModuleName
            Message    = $Message
            FileName   = $FileName
            LineNumber = $LineNumber
            WarningCode = $WarningCode
            Timestamp  = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fff"
        }
        $global:WarningLog += $warningEntry

        $global:BuildTimers[$ModuleName] = $timerData
    }
}

function Parse-BuildOutput {
    param(
        [string]$Output,
        [string]$ModuleName
    )

    if (!$Output) { return }

    # Pattern matching for compiler errors
    $errorPatterns = @(
        "error\s+C\d+",           # MSVC error codes (C1060, C3859, etc.)
        "fatal\s+error",          # Fatal errors
        "LNK\d{4}",               # Linker errors
        "undefined\s+reference",  # Undefined references
        "cannot\s+open\s+input"   # Cannot open input files
    )

    foreach ($pattern in $errorPatterns) {
        try {
            $matches = [regex]::Matches($Output, $pattern)
            foreach ($match in $matches) {
                Add-BuildError -ModuleName $ModuleName -Message "Build error: $($match.Value)"
            }
        } catch {
            Write-Warning "Could not parse pattern '$pattern': $_"
        }
    }

    # Pattern matching for warnings
    try {
        $warningMatches = [regex]::Matches($Output, "warning\s+C\d+")
        foreach ($wm in $warningMatches) {
            Add-BuildWarning -ModuleName $ModuleName -Message "Build warning: $($wm.Value)"
        }
    } catch {
        Write-Warning "Could not parse warnings: $_"
    }

    # Extract file names from output (common patterns)
    try {
        $filePatterns = @(
            "(\w:[\\\/][\w\s\-\.]+\.cpp)",
            "(\w:[\\\/][\w\s\-\.]+\.h)",
            "(\w:[\\\/][\w\s\-\.]+\.hpp)"
        )

        foreach ($fp in $filePatterns) {
            try {
                $fileMatches = [regex]::Matches($Output, $fp)
                foreach ($fm in $fileMatches) {
                    if (!$global:ProcessedFiles) { $global:ProcessedFiles = @() }
                    $global:ProcessedFiles += $fm.Value.Trim()
                }
            } catch { /* Skip invalid patterns */ }
        }
    } catch {
        Write-Warning "Could not extract file names from output: $_"
    }
}

function Get-SlowestFiles {
    param(
        [string]$ModuleName,
        [int]$TopN = 10
    )

    if ($global:BuildTimers.ContainsKey($ModuleName)) {
        $timerData = $global:BuildTimers[$ModuleName]
        $sortedFiles = $timerData.Files.GetEnumerator() | Sort-Object Value.TotalTime -Descending | Select-Object -First $TopN

        return [PSCustomObject[]]$sortedFiles.ForEach({
            [PSCustomObject]@{
                FilePath     = $_.Key
                TotalTimeMs  = $_.Value.TotalTime
                CompileCount = $_.Value.CompileCount
                AvgTimeMs    = if ($_.Value.CompileCount -gt 0) { $_.Value.TotalTime / $_.Value.CompileCount } else { 0 }
            }
        })
    }

    return @()
}

function Generate-BuildSummaryReport {
    param(
        [string]$LogDirectory,
        [datetime]$StartTime,
        [datetime]$EndTime
    )

    $totalDurationMs = ($EndTime - $StartTime).TotalMilliseconds

    # Collect all module results from BuildTimers
    $moduleSummaries = @()
    foreach ($moduleName in $global:BuildTimers.Keys) {
        $timerData = $global:BuildTimers[$moduleName]
        $slowestFiles = Get-SlowestFiles -ModuleName $moduleName

        $summaryEntry = @{
            ModuleName      = $moduleName
            TotalDurationMs = $timerData.DurationMs
            ErrorCount      = $timerData.Errors
            WarningCount    = $timerData.Warnings
            FilesCompiled   = ($timerData.Files | Measure-Object).Count
            SlowestFiles    = $slowestFiles
        }

        $moduleSummaries += [PSCustomObject]$summaryEntry
    }

    # Determine overall status
    $totalErrors = 0
    foreach ($moduleName in $global:BuildTimers.Keys) {
        if ($global:BuildTimers[$moduleName].Errors -gt 0) {
            $totalErrors++
        }
    }

    $overallStatus = if ($totalErrors -eq 0) { "Success" } else { "Failed" }

    # Build the summary report
    $report = @{
        ReportType       = "BuildSummary"
        Timestamp        = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fff"
        StartTime        = $StartTime.ToString("yyyy-MM-ddTHH:mm:ss")
        EndTime          = $EndTime.ToString("yyyy-MM-ddTHH:mm:ss")
        TotalDurationMs  = $totalDurationMs
        OverallStatus    = $overallStatus
        ModuleCount      = ($global:BuildTimers | Measure-Object).Count
        Modules          = $moduleSummaries
        Errors           = if ($global:ErrorLog) { $global:ErrorLog } else { @() }
        Warnings         = if ($global:WarningLog) { $global:WarningLog } else { @() }
    }

    return $report
}

function Save-BuildReport {
    param(
        [hashtable]$Report,
        [string]$LogDirectory
    )

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $logPath = Join-Path $LogDirectory "$timestamp.json"

    try {
        ConvertTo-Json $Report -Depth 10 | Out-File $logPath -Encoding UTF8
        Write-BuildMessage "Build report saved to: $logPath" "Info"
        return $logPath
    } catch {
        Write-BuildMessage "Failed to save build report: $_" "Error"
        return $null
    }
}

function Get-LastBuildStatus {
    param([string]$LogDirectory)

    $lastLog = Join-Path $LogDirectory "*build.json" | Get-ChildItem -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1

    if ($lastLog) {
        try {
            $content = Get-Content $lastLog.FullName -Raw | ConvertFrom-Json
            return @{
                Timestamp = $content.timestamp
                Status    = $content.Status
                Duration  = $content.TotalDuration
                Errors    = $content.ErrorCount
            }
        } catch {
            Write-BuildMessage "Could not read last build status: $_" "Warning"
            return $null
        }
    }

    return @{ Status = "No previous builds found"; Timestamp = ""; Duration = ""; Errors = 0 }
}

# Initialize global state for the session
$global:BuildTimers = @{}
$global:ErrorLog = @()
$global:WarningLog = @()
$global:ProcessedFiles = @()
