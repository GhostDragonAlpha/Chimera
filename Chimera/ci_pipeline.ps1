# =============================================================================
# Chimera CI Pipeline — Main Continuous Integration Script
# =============================================================================
# Runs on every commit: builds project, executes tests, generates coverage,
# and uploads artifacts. Supports --dry-run for local testing.
# =============================================================================

param(
    [switch]$DryRun,
    [string]$ConfigPath = "$PSScriptRoot\ci_config.json",
    [string]$BuildTarget,
    [string]$BuildPlatform,
    [string]$BuildConfiguration,
    [string]$TestSuite,
    [string]$CoverageThreshold,
    [switch]$SkipBuild,
    [switch]$SkipTests,
    [switch]$SkipCoverage,
    [switch]$SkipUpload
)

$ErrorActionPreference = "Stop"

# =============================================================================
# CONFIGURATION LOADING
# =============================================================================

function Load-CIConfig {
    param([string]$Path)

    if (!(Test-Path $Path)) {
        Write-CIMessage "CI config not found at: $Path — using defaults" "Warning"
        return Get-DefaultCIConfig
    }

    try {
        $raw = Get-Content $Path -Raw -ErrorAction Stop
        $config = $raw | ConvertFrom-Json
        Write-CIMessage "Loaded CI configuration from: $Path" "Info"
        return $config
    } catch {
        Write-CIMessage "Failed to parse CI config: $_ — using defaults" "Warning"
        return Get-DefaultCIConfig
    }
}

function Get-DefaultCIConfig {
    [PSCustomObject]@{
        build = [PSCustomObject]@{
            targets       = @("ChimeraEditor")
            platforms     = @("Win64")
            configurations = @("Development", "Shipping")
        }
        test  = [PSCustomObject]@{
            suites   = @("mcp_full_integration_test.py")
            timeout  = 300
            parallel = $true
        }
        coverage = [PSCustomObject]@{
            enabled       = $true
            threshold     = 80
            reportFormat  = "cobertura"
            excludePatterns = @("Tests\*", "ThirdParty\*")
        }
        artifacts = [PSCustomObject]@{
            retentionDays = 30
            directories   = @("Binaries", "Intermediate", "Logs")
            maxFileSizeMB = 100
        }
        notifications = [PSCustomObject]@{
            email    = $null
            webhook  = $null
            on       = @("success", "failure")
        }
    }
}

# =============================================================================
# LOGGING UTILITIES
# =============================================================================

$CIStartTime   = Get-Date
$CILogDir      = Join-Path $PSScriptRoot ".ci_logs"
$CIReportDir   = Join-Path $PSScriptRoot ".ci_reports"

if (!(Test-Path $CILogDir)) { New-Item -ItemType Directory -Path $CILogDir -Force | Out-Null }
if (!(Test-Path $CIReportDir)) { New-Item -ItemType Directory -Path $CIReportDir -Force | Out-Null }

$CILogFile = Join-Path $CILogDir "ci_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

function Write-CIMessage {
    param(
        [string]$Message,
        [string]$Level   = "Info",
        [bool]$NoNewline  = $false
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
    $prefix    = "[{0}] [{1,-5}] {2}" -f $timestamp, $Level.ToUpper(), $Message

    switch ($Level) {
        "Error"   { Write-Host $prefix -ForegroundColor Red }
        "Warning" { Write-Host $prefix -ForegroundColor Yellow }
        "Success" { Write-Host $prefix -ForegroundColor Green }
        "Info"    { Write-Host $prefix -ForegroundColor Cyan }
        default   { Write-Host $prefix }
    }

    $prefix | Out-File $CILogFile -Append -Encoding UTF8

    if ($NoNewline) { Write-Host "" }
}

# =============================================================================
# BUILD STAGE
# =============================================================================

function Invoke-BuildStage {
    param(
        [string]$Target,
        [string]$Platform,
        [string]$Configuration
    )

    $buildScript = Join-Path $PSScriptRoot "build_pipeline.ps1"

    if (!(Test-Path $buildScript)) {
        Write-CIMessage "build_pipeline.ps1 not found. Cannot build." "Error"
        return $false
    }

    $argsList = @()
    if ($Target)      { $argsList += "-Target `"$Target`"" }
    if ($Platform)    { $argsList += "-Platform `"$Platform`"" }
    if ($Configuration) { $argsList += "-Configuration `"$Configuration`"" }

    Write-CIMessage "Starting build: Target=$Target, Platform=$Platform, Config=$Configuration" "Info"

    if ($DryRun) {
        Write-CIMessage "[DRY-RUN] Would execute:" "Info"
        Write-CIMessage "  powershell -ExecutionPolicy Bypass -File `"$buildScript`" $($argsList -join ' ')" "Info"
        return $true
    }

    try {
        $proc = Start-Process -FilePath "powershell.exe" `
            -ArgumentList "-ExecutionPolicy Bypass", "-File", "`"$buildScript`"", @($argsList) `
            -NoNewWindow -Wait -PassThru

        if ($proc.ExitCode -eq 0) {
            Write-CIMessage "Build succeeded." "Success"
            return $true
        } else {
            Write-CIMessage "Build failed (exit code: $($proc.ExitCode))." "Error"
            return $false
        }
    } catch {
        Write-CIMessage "Build exception: $_" "Error"
        return $false
    }
}

# =============================================================================
# TEST STAGE
# =============================================================================

function Invoke-TestStage {
    param(
        [string[]]$Suites,
        [int]$Timeout = 300
    )

    $testResults   = @{ Success = 0; Failed = 0 }
    $reportFiles   = @()

    foreach ($suite in $Suites) {
        Write-CIMessage "Running test suite: $suite" "Info"

        # Resolve path relative to Python directory
        $pythonDir     = Join-Path $PSScriptRoot "Python"
        $testFilePath  = Join-Path $pythonDir $suite

        if (!(Test-Path $testFilePath)) {
            Write-CIMessage "Test file not found: $testFilePath — skipping." "Warning"
            continue
        }

        try {
            $reportFile = Join-Path $CIReportDir "test_$(Get-Date -Format 'yyyyMMdd_HHmmss')_$suite.json"

            if ($DryRun) {
                Write-CIMessage "[DRY-RUN] Would execute:" "Info"
                Write-CIMessage "  python `"$testFilePath`" --report `"$reportFile`"" "Info"
                $testResults.Success++
                continue
            }

            $proc = Start-Process -FilePath "python" `
                -ArgumentList "`"$testFilePath`"", "--report", "`"$reportFile`"" `
                -NoNewWindow -Wait -PassThru

            if ($proc.ExitCode -eq 0) {
                Write-CIMessage "Test suite passed: $suite" "Success"
                $testResults.Success++
                $reportFiles += $reportFile
            } else {
                Write-CIMessage "Test suite failed: $suite (exit code: $($proc.ExitCode))" "Error"
                $testResults.Failed++
            }

            if ($Timeout -gt 0) {
                $elapsed = (Get-Date) - $CIStartTime
                if ($elapsed.TotalSeconds -gt $Timeout) {
                    Write-CIMessage "Test timeout exceeded (${Timeout}s). Stopping." "Warning"
                    break
                }
            }
        } catch {
            Write-CIMessage "Test exception for $suite: $_" "Error"
            $testResults.Failed++
        }
    }

    return @{ Results = $testResults; Reports = $reportFiles }
}

# =============================================================================
# COVERAGE STAGE
# =============================================================================

function Invoke-CoverageStage {
    param(
        [bool]$Enabled,
        [int]$Threshold,
        [string[]]$ExcludePatterns
    )

    if (!$Enabled) {
        Write-CIMessage "Coverage stage skipped (disabled)." "Info"
        return $null
    }

    Write-CIMessage "Starting coverage analysis..." "Info"

    # Coverage requires pytest-cov; attempt with available tooling
    try {
        $coverageScript = Join-Path $PSScriptRoot ".ci_scripts\run_coverage.ps1"

        if (Test-Path $coverageScript) {
            $proc = Start-Process -FilePath "powershell.exe" `
                -ArgumentList "-ExecutionPolicy Bypass", "-File", "`"$coverageScript`"" `
                -NoNewWindow -Wait -PassThru

            if ($proc.ExitCode -ne 0) {
                Write-CIMessage "Coverage generation failed." "Warning"
            }
        } else {
            # Fallback: run pytest with coverage inline
            $pythonDir = Join-Path $PSScriptRoot "Python"

            if ($DryRun) {
                Write-CIMessage "[DRY-RUN] Would generate coverage report at threshold ${Threshold}%" "Info"
                return @{ Status = "Skipped (dry-run)" }
            }

            $coverageReport = Join-Path $CIReportDir "coverage_$(Get-Date -Format 'yyyyMMdd_HHmmss').xml"

            $proc = Start-Process -FilePath "python" `
                -ArgumentList "-m", "pytest", "--cov=Python", "--cov-report=xml:`"$coverageReport`"", "--cov-branch", "--cov-target=$Threshold", "`$pythonDir" `
                -NoNewWindow -Wait -PassThru

            if ($proc.ExitCode -eq 0) {
                Write-CIMessage "Coverage report generated: $coverageReport" "Success"
                return @{ Status = "Success"; ReportPath = $coverageReport }
            } else {
                Write-CIMessage "Coverage generation failed (exit code: $($proc.ExitCode)). Threshold: ${Threshold}%" "Warning"
                return @{ Status = "Failed"; Threshold = $Threshold }
            }
        }
    } catch {
        Write-CIMessage "Coverage exception: $_" "Error"
        return @{ Status = "Exception"; Error = $_.ToString() }
    }
}

# =============================================================================
# ARTIFACT STAGE
# =============================================================================

function Invoke-ArtifactStage {
    param(
        [string[]]$Directories,
        [int]$RetentionDays,
        [bool]$SkipUpload
    )

    if ($SkipUpload) {
        Write-CIMessage "Artifact upload skipped." "Info"
        return $null
    }

    Write-CIMessage "Packaging artifacts..." "Info"

    $artifactDir = Join-Path $PSScriptRoot ".ci_artifacts"
    if (!(Test-Path $artifactDir)) { New-Item -ItemType Directory -Path $artifactDir -Force | Out-Null }

    $timestamp   = Get-Date -Format "yyyyMMdd_HHmmss"
    $archiveName = "chimera_artifacts_${timestamp}.zip"
    $archivePath = Join-Path $artifactDir $archiveName

    foreach ($dir in $Directories) {
        $fullPath = Join-Path $PSScriptRoot $dir
        if (Test-Path $fullPath) {
            Write-CIMessage "Including artifact directory: $dir" "Info"
        } else {
            Write-CIMessage "Artifact directory not found: $dir — skipping." "Warning"
        }
    }

    try {
        # Create archive of relevant directories
        $pathsToArchive = @()
        foreach ($dir in $Directories) {
            $fullPath = Join-Path $PSScriptRoot $dir
            if (Test-Path $fullPath) {
                $pathsToArchive += $fullPath
            }
        }

        # Also include CI reports and logs
        if (Test-Path $CIReportDir)  { $pathsToArchive += $CIReportDir }
        if (Test-Path $CILogDir)     { $pathsToArchive += $CILogDir }

        if ($pathsToArchive.Count -gt 0) {
            if ($DryRun) {
                Write-CIMessage "[DRY-RUN] Would create archive: $archiveName" "Info"
                return @{ Path = $archivePath; DryRun = $true }
            }

            & "7z.exe" a "$archivePath" @($pathsToArchive) -mx=6 2>&1 | Out-Null

            if (Test-Path $archivePath) {
                $sizeMB = [math]::Round((Get-Item $archivePath).Length / 1MB, 2)
                Write-CIMessage "Artifact archive created: $archiveName (${sizeMB}MB)" "Success"
                return @{ Path = $archivePath; SizeMB = $sizeMB }
            } else {
                # Fallback to built-in Compress-Archive (slower but always available)
                $fallbackDir = Join-Path $artifactDir "artifacts_${timestamp}"
                Copy-Item -Path @($pathsToArchive) -Destination $fallbackDir -Recurse -Force

                if ($DryRun) {
                    Write-CIMessage "[DRY-RUN] Would compress artifacts to: $fallbackDir" "Info"
                    return @{ Path = $fallbackDir; DryRun = $true }
                }

                Compress-Archive -Path @($pathsToArchive | Where-Object { Test-Path $_ }) `
                    -DestinationPath "$archiveName.zip" -Update -ErrorAction SilentlyContinue

                Write-CIMessage "Artifacts staged in: $fallbackDir" "Success"
                return @{ Path = $fallbackDir }
            }
        } else {
            Write-CIMessage "No artifact directories found to package." "Warning"
            return $null
        }
    } catch {
        Write-CIMessage "Artifact packaging failed: $_" "Error"
        return @{ Status = "Failed"; Error = $_.ToString() }
    }
}

# =============================================================================
# NOTIFICATION STAGE
# =============================================================================

function Send-Notification {
    param(
        [string]$Status,
        [object]$CIConfig
    )

    $notifications = $CIConfig.notifications

    if ($notifications.webhook) {
        try {
            $payload = @{
                status     = $Status
                timestamp  = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
                pipeline   = "Chimera-CI"
                dryRun     = $DryRun.IsPresent
            }

            Invoke-RestMethod -Uri $notifications.webhook `
                -Method Post `
                -ContentType "application/json" `
                -Body ($payload | ConvertTo-Json -Depth 5) `
                -TimeoutSec 10 2>&1 | Out-Null

            Write-CIMessage "Webhook notification sent." "Info"
        } catch {
            Write-CIMessage "Failed to send webhook: $_" "Warning"
        }
    }

    if ($notifications.email) {
        try {
            $emailPayload = @{
                To      = $notifications.email
                Subject = "Chimera CI Pipeline — ${Status}"
                Body    = "Pipeline status: ${Status}. Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
            }

            # Email sending requires SMTP configuration; placeholder for integration
            Write-CIMessage "Email notification would be sent to: $($notifications.email)" "Info"
        } catch {
            Write-CIMessage "Failed to send email notification: $_" "Warning"
        }
    }
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

Write-CIMessage "" "Info"
Write-CIMessage "========================================" "Info"
Write-CIMessage "  Chimera CI Pipeline v1.0" "Info"
Write-CIMessage "========================================" "Info"
Write-CIMessage "" "Info"

if ($DryRun) {
    Write-CIMessage "*** DRY-RUN MODE — no actual operations will be performed ***" "Warning"
}

# Load configuration
$ciConfig = Load-CIConfig -Path $ConfigPath

# Determine build parameters from config or CLI overrides
$configBuild  = $ciConfig.build
$configTest   = $ciConfig.test
$configCover  = $ciConfig.coverage
$configArt    = $ciConfig.artifacts
$configNotify = $ciConfig.notifications

$buildTargets      = if ($BuildTarget)     { @($BuildTarget) } else { $configBuild.targets }
$buildPlatforms    = if ($BuildPlatform)   { @($BuildPlatform) } else { $configBuild.platforms }
$buildConfigs      = if ($BuildConfiguration) { @($BuildConfiguration) } else { $configBuild.configurations }

# Use Shipping configuration for CI (production readiness)
if (!$BuildConfiguration -and $configBuild.configurations -contains "Shipping") {
    $buildConfigs = @("Shipping")
} elseif (!$BuildConfiguration) {
    $buildConfigs = @("Development")
}

$testSuites        = if ($TestSuite)       { @($TestSuite) } else { $configTest.suites }
$coverageEnabled   = $configCover.enabled
$coverageThreshold = if ($CoverageThreshold) { [int]$CoverageThreshold } else { $configCover.threshold }

# =============================================================================
# STAGE 1: BUILD
# =============================================================================

$buildSuccess = $true

if (!$SkipBuild.IsPresent) {
    Write-CIMessage "" "Info"
    Write-CIMessage "--- STAGE 1: BUILD ---" "Info"

    foreach ($target in $buildTargets) {
        foreach ($platform in $buildPlatforms) {
            foreach ($config in $buildConfigs) {
                $result = Invoke-BuildStage -Target $target -Platform $platform -Configuration $config
                if (!$result) {
                    $buildSuccess = $false
                    break
                }
            }
        }

        if (!$buildSuccess) { break }
    }

    if ($DryRun) {
        Write-CIMessage "[DRY-RUN] Build stage complete (simulated)." "Info"
    }
} else {
    Write-CIMessage "--- STAGE 1: BUILD — SKIPPED ---" "Info"
}

if (!$buildSuccess -and !$DryRun) {
    Write-CIMessage "" "Warning"
    Write-CIMessage "*** CI Pipeline halted: Build failed ***" "Error"
    Send-Notification -Status "Failed (Build)" -CIConfig $ciConfig
    exit 1
}

# =============================================================================
# STAGE 2: TEST
# =============================================================================

if (!$SkipTests.IsPresent) {
    Write-CIMessage "" "Info"
    Write-CIMessage "--- STAGE 2: TEST ---" "Info"

    $testOutput = Invoke-TestStage -Suites $testSuites -Timeout ($configTest.timeout)

    if ($DryRun) {
        Write-CIMessage "[DRY-RUN] Test stage complete (simulated)." "Info"
    } else {
        Write-CIMessage "Test results: $($testOutput.Results.Success) passed, $($testOutput.Results.Failed) failed" `
            $(if ($testOutput.Results.Failed -gt 0) { "Error" } else { "Success" })

        if ($testOutput.Reports.Count -gt 0) {
            Write-CIMessage "Test reports saved to: $CIReportDir" "Info"
        }
    }

    if ($testOutput.Results.Failed -gt 0 -and !$DryRun) {
        Write-CIMessage "" "Warning"
        Write-CIMessage "*** CI Pipeline halted: Tests failed ***" "Error"
        Send-Notification -Status "Failed (Tests)" -CIConfig $ciConfig
        exit 1
    }
} else {
    Write-CIMessage "--- STAGE 2: TEST — SKIPPED ---" "Info"
}

# =============================================================================
# STAGE 3: COVERAGE
# =============================================================================

if (!$SkipCoverage.IsPresent) {
    Write-CIMessage "" "Info"
    Write-CIMessage "--- STAGE 3: COVERAGE ---" "Info"

    $coverageOutput = Invoke-CoverageStage `
        -Enabled:$coverageEnabled `
        -Threshold $coverageThreshold `
        -ExcludePatterns $configCover.excludePatterns

    if ($DryRun) {
        Write-CIMessage "[DRY-RUN] Coverage stage complete (simulated)." "Info"
    } elseif ($coverageOutput.Status -eq "Success") {
        Write-CIMessage "Coverage analysis passed." "Success"
    } else {
        Write-CIMessage "Coverage analysis completed with warnings: $($coverageOutput.Status)" "Warning"
    }
} else {
    Write-CIMessage "--- STAGE 3: COVERAGE — SKIPPED ---" "Info"
}

# =============================================================================
# STAGE 4: ARTIFACTS
# =============================================================================

if (!$SkipUpload.IsPresent) {
    Write-CIMessage "" "Info"
    Write-CIMessage "--- STAGE 4: ARTIFACTS ---" "Info"

    $artifactOutput = Invoke-ArtifactStage `
        -Directories $configArt.directories `
        -RetentionDays $configArt.retentionDays `
        -SkipUpload:$false

    if ($DryRun) {
        Write-CIMessage "[DRY-RUN] Artifact stage complete (simulated)." "Info"
    } elseif ($artifactOutput) {
        Write-CIMessage "Artifact staging complete." "Success"
    } else {
        Write-CIMessage "No artifacts to package." "Warning"
    }

    # Retention policy: clean old artifacts
    try {
        $oldArtifacts = Get-ChildItem -Path $artifactDir -Filter "*.zip" -ErrorAction SilentlyContinue |
            Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$configArt.retentionDays) }

        if ($oldArtifacts.Count -gt 0) {
            foreach ($old in $oldArtifacts) {
                Remove-Item $old.FullName -Force
                Write-CIMessage "Removed old artifact: $($old.Name)" "Info"
            }
        } else {
            Write-CIMessage "No expired artifacts to clean." "Info"
        }
    } catch {
        Write-CIMessage "Could not enforce retention policy: $_" "Warning"
    }
} else {
    Write-CIMessage "--- STAGE 4: ARTIFACTS — SKIPPED ---" "Info"
}

# =============================================================================
# SUMMARY
# =============================================================================

$elapsed        = New-TimeSpan -Start $CIStartTime -End (Get-Date)
$status         = if ($DryRun) { "Success (dry-run)" } else { "Success" }

Write-CIMessage "" "Info"
Write-CIMessage "========================================" "Success"
Write-CIMessage "  CI Pipeline: ${status}" "Success"
Write-CIMessage "  Duration:    $($elapsed.TotalSeconds.ToString('F1'))s" "Success"
Write-CIMessage "========================================" "Success"

Send-Notification -Status $status -CIConfig $ciConfig

exit 0
