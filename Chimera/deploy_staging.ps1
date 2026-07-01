# =============================================================================
# Chimera Staging Deployment Script
# =============================================================================
# Builds the project in Shipping configuration, packages output into a
# distributable archive, deploys to staging server path, and runs smoke tests.
# =============================================================================

param(
    [string]$StagingServerPath = "E:\PythonChimera\staging",
    [string]$ArchiveName = "chimera_staging_$(Get-Date -Format 'yyyyMMdd_HHmmss').zip",
    [switch]$SkipBuild,
    [switch]$SkipPackage,
    [switch]$SkipDeploy,
    [switch]$SkipSmokeTest,
    [string]$BackupPath = "E:\PythonChimera\staging_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
)

$ErrorActionPreference = "Stop"

# =============================================================================
# CONFIGURATION AND PATHS
# =============================================================================

$ProjectRoot   = $PSScriptRoot
$BuildScript   = Join-Path $ProjectRoot "build_pipeline.ps1"
$BinariesDir   = Join-Path $ProjectRoot "Binaries\Win64"
$StagingLogDir = Join-Path $ProjectRoot ".deploy_logs"

if (!(Test-Path $StagingLogDir)) { New-Item -ItemType Directory -Path $StagingLogDir -Force | Out-Null }

$DeployStartTime = Get-Date

function Write-DeployMessage {
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

    $prefix | Out-File (Join-Path $StagingLogDir "deploy_staging_$(Get-Date -Format 'yyyyMMdd_HHmmss').log") -Append -Encoding UTF8

    if ($NoNewline) { Write-Host "" }
}

# =============================================================================
# STAGE 1: BUILD IN SHIPPING CONFIGURATION
# =============================================================================

function Invoke-StagingBuild {
    Write-DeployMessage "=== STAGE 1: BUILD (Shipping Configuration) ===" "Info"

    if ($SkipBuild.IsPresent) {
        Write-DeployMessage "Build stage skipped." "Info"
        return $true
    }

    if (!(Test-Path $BuildScript)) {
        Write-DeployMessage "build_pipeline.ps1 not found at: $BuildScript" "Error"
        return $false
    }

    try {
        $proc = Start-Process -FilePath "powershell.exe" `
            -ArgumentList "-ExecutionPolicy Bypass", "-File", "`"$BuildScript`"", `-Configuration`, "Shipping", `-Platform`, "Win64", `-Full` `
            -NoNewWindow -Wait -PassThru

        if ($proc.ExitCode -eq 0) {
            Write-DeployMessage "Shipping build succeeded." "Success"
            return $true
        } else {
            Write-DeployMessage "Shipping build failed (exit code: $($proc.ExitCode))." "Error"
            return $false
        }
    } catch {
        Write-DeployMessage "Build exception: $_" "Error"
        return $false
    }
}

# =============================================================================
# STAGE 2: PACKAGE OUTPUT INTO DISTRIBUTABLE ARCHIVE
# =============================================================================

function Invoke-StagingPackage {
    param([bool]$Skip)

    if ($Skip) {
        Write-DeployMessage "Packaging stage skipped." "Info"
        return $null
    }

    Write-DeployMessage "=== STAGE 2: PACKAGE ===" "Info"

    if (!(Test-Path $BinariesDir)) {
        Write-DeployMessage "Binaries directory not found: $BinariesDir — build may be incomplete." "Warning"
        return $null
    }

    $archivePath = Join-Path $StagingLogDir $ArchiveName

    try {
        # Collect all distributable files from Binaries and other relevant directories
        $filesToPackage = Get-ChildItem -Path $BinariesDir -Recurse -Include "*.dll", "*.exe" -ErrorAction SilentlyContinue

        if ($filesToPackage.Count -eq 0) {
            Write-DeployMessage "No distributable files (.dll/.exe) found in Binaries\Win64." "Warning"
            return $null
        }

        # Create a staging package directory
        $packageDir = Join-Path $StagingLogDir "staging_package"
        if (Test-Path $packageDir) { Remove-Item $packageDir -Recurse -Force }
        New-Item -ItemType Directory -Path $packageDir -Force | Out-Null

        # Copy binaries to package directory
        foreach ($file in $filesToPackage) {
            $destDir = Join-Path $packageDir $file.DirectoryName.Replace($BinariesDir, "").TrimStart("\")
            if (!(Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
            Copy-Item $file.FullName (Join-Path $packageDir ($file.Name)) -Force
        }

        # Include project config files needed for staging
        $configFiles = @(
            "Chimera.uproject",
            "Config\DefaultEngine.ini",
            "Config\DefaultGame.ini"
        )

        foreach ($cfg in $configFiles) {
            $cfgPath = Join-Path $ProjectRoot $cfg
            if (Test-Path $cfgPath) {
                Copy-Item $cfgPath -Destination $packageDir -Force -ErrorAction SilentlyContinue
            }
        }

        # Compress the package
        & "7z.exe" a "$archivePath" "$packageDir\*" 2>&1 | Out-Null

        if (Test-Path $archivePath) {
            $sizeMB = [math]::Round((Get-Item $archivePath).Length / 1MB, 2)
            Write-DeployMessage "Package created: $ArchiveName (${sizeMB}MB)" "Success"
            return @{ Path = $archivePath; SizeMB = $sizeMB }
        } else {
            # Fallback to Compress-Archive
            Compress-Archive -Path $packageDir -DestinationPath "$archivePath" -Update -ErrorAction SilentlyContinue

            if (Test-Path $archivePath) {
                Write-DeployMessage "Package created (fallback): $ArchiveName" "Success"
                return @{ Path = $archivePath }
            } else {
                Write-DeployMessage "Package creation failed." "Warning"
                return $null
            }
        }
    } catch {
        Write-DeployMessage "Packaging exception: $_" "Error"
        return $null
    }
}

# =============================================================================
# STAGE 3: DEPLOY TO STAGING SERVER PATH
# =============================================================================

function Invoke-StagingDeploy {
    param([string]$ArchivePath, [string]$TargetPath)

    if ($SkipDeploy.IsPresent) {
        Write-DeployMessage "Deployment stage skipped." "Info"
        return $true
    }

    Write-DeployMessage "=== STAGE 3: DEPLOY ===" "Info"

    # Ensure target directory exists
    if (!(Test-Path $TargetPath)) {
        try {
            New-Item -ItemType Directory -Path $TargetPath -Force | Out-Null
            Write-DeployMessage "Created staging path: $TargetPath" "Success"
        } catch {
            Write-DeployMessage "Failed to create staging path: $_" "Error"
            return $false
        }
    }

    # Backup existing installation if present
    try {
        $existingFiles = Get-ChildItem -Path $TargetPath -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.PSIsContainer -eq $false }

        if ($existingFiles.Count -gt 0) {
            Write-DeployMessage "Backing up existing staging installation..." "Info"

            try {
                New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null
                Copy-Item -Path $TargetPath -Destination $BackupPath -Recurse -Force -ErrorAction Stop
                Write-DeployMessage "Backup created at: $BackupPath" "Success"
            } catch {
                Write-DeployMessage "Backup failed (proceeding anyway): $_" "Warning"
            }
        } else {
            Write-DeployMessage "No existing installation to back up." "Info"
        }
    } catch {
        Write-DeployMessage "Could not check for existing files: $_" "Warning"
    }

    # Extract and deploy the archive
    try {
        if (Test-Path $ArchivePath) {
            & "7z.exe" x "$ArchivePath" -o"$TargetPath" -y 2>&1 | Out-Null

            if ($LASTEXITCODE -eq 0) {
                Write-DeployMessage "Deployment to staging complete: $TargetPath" "Success"
                return $true
            } else {
                Write-DeployMessage "7z extraction failed (exit code: $LASTEXITCODE). Trying fallback." "Warning"

                # Fallback: use Expand-Archive if 7z fails
                try {
                    Add-Type -Assembly System.IO.Compression.FileSystem 2>&1 | Out-Null
                    [System.IO.Compression.ZipFile]::ExtractToDirectory($ArchivePath, $TargetPath)
                    Write-DeployMessage "Deployment via fallback extraction complete." "Success"
                    return $true
                } catch {
                    Write-DeployMessage "Fallback extraction failed: $_" "Error"
                    return $false
                }
            }
        } else {
            Write-DeployMessage "Archive not found at: $ArchivePath — skipping deployment." "Warning"
            return $false
        }
    } catch {
        Write-DeployMessage "Deployment exception: $_" "Error"

        # Rollback: restore from backup if available
        try {
            if (Test-Path $BackupPath) {
                Write-DeployMessage "Rolling back: restoring from backup..." "Warning"
                Remove-Item -Path $TargetPath -Recurse -Force -ErrorAction SilentlyContinue
                Copy-Item -Path $BackupPath -Destination $TargetPath -Recurse -Force
                Write-DeployMessage "Rollback complete." "Success"
            } else {
                Write-DeployMessage "No backup available for rollback." "Warning"
            }
        } catch {
            Write-DeployMessage "Rollback failed: $_" "Error"
        }

        return $false
    }
}

# =============================================================================
# STAGE 4: SMOKE TESTS AFTER DEPLOYMENT
# =============================================================================

function Invoke-StagingSmokeTests {
    param([string]$StagingPath)

    if ($SkipSmokeTest.IsPresent) {
        Write-DeployMessage "Smoke test stage skipped." "Info"
        return $true
    }

    Write-DeployMessage "=== STAGE 4: SMOKE TESTS ===" "Info"

    $smokeTests = @{ Passed = 0; Failed = 0 }

    # Smoke Test 1: Verify critical files exist
    Write-DeployMessage "[Smoke Test 1] Verifying critical files in staging..." "Info"

    $criticalFiles = @(
        Join-Path $StagingPath "*ChimeraEditor*.exe",
        Join-Path $StagingPath "*McpAutomationBridge.dll",
        Join-Path $StagingPath "*PythonScriptPlugin.dll"
    )

    foreach ($pattern in $criticalFiles) {
        $found = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue | Select-Object -First 1

        if ($found) {
            Write-DeployMessage "  Found: $($found.Name)" "Success"
            $smokeTests.Passed++
        } else {
            Write-DeployMessage "  Missing: $pattern" "Warning"
            $smokeTests.Failed++
        }
    }

    # Smoke Test 2: Verify file integrity (check non-zero sizes)
    Write-DeployMessage "[Smoke Test 2] Verifying file sizes..." "Info"

    try {
        $deployedFiles = Get-ChildItem -Path $StagingPath -Recurse -Include "*.dll", "*.exe" -ErrorAction SilentlyContinue

        foreach ($file in $deployedFiles) {
            if ($file.Length -eq 0) {
                Write-DeployMessage "  Empty file detected: $($file.Name)" "Warning"
                $smokeTests.Failed++
            } else {
                $smokeTests.Passed++
            }
        }

        if ($deployedFiles.Count -eq 0) {
            Write-DeployMessage "  No .dll/.exe files found to verify." "Warning"
        }
    } catch {
        Write-DeployMessage "Could not verify file sizes: $_" "Warning"
        $smokeTests.Failed++
    }

    # Smoke Test 3: Run integration test against staging if MCP server is available
    Write-DeployMessage "[Smoke Test 3] Running integration tests..." "Info"

    try {
        $testScript = Join-Path $ProjectRoot "Python\mcp_full_integration_test.py"

        if (Test-Path $testScript) {
            $proc = Start-Process -FilePath "python" `
                -ArgumentList "`"$testScript`"" `
                -NoNewWindow -Wait -PassThru

            if ($proc.ExitCode -eq 0) {
                Write-DeployMessage "Integration smoke tests passed." "Success"
                $smokeTests.Passed++
            } else {
                Write-DeployMessage "Integration smoke tests failed (exit code: $($proc.ExitCode))." "Warning"
                $smokeTests.Failed++
            }
        } else {
            Write-DeployMessage "Test script not found at: $testScript — skipping." "Info"
        }
    } catch {
        Write-DeployMessage "Smoke test exception: $_" "Error"
        $smokeTests.Failed++
    }

    # Report smoke test results
    Write-DeployMessage "" "Info"
    Write-DeployMessage "Smoke Test Results: $($smokeTests.Passed) passed, $($smokeTests.Failed) failed" `
        $(if ($smokeTests.Failed -gt 0) { "Warning" } else { "Success" })

    return ($smokeTests.Failed -eq 0)
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

Write-DeployMessage "" "Info"
Write-DeployMessage "========================================" "Info"
Write-DeployMessage "  Chimera Staging Deployment v1.0" "Info"
Write-DeployMessage "========================================" "Info"
Write-DeployMessage "" "Info"
Write-DeployMessage "Target: $StagingServerPath" "Info"

$deploymentSuccess = $true

# Stage 1: Build
if ($deploymentSuccess) {
    $buildResult = Invoke-StagingBuild
    if (!$buildResult) {
        $deploymentSuccess = $false
    }
}

# Stage 2: Package
$packageResult = $null
if ($deploymentSuccess) {
    $packageResult = Invoke-StagingPackage -Skip:$SkipPackage.IsPresent
    if (!$packageResult) {
        $deploymentSuccess = $false
    }
}

# Stage 3: Deploy
if ($deploymentSuccess -and $packageResult) {
    $deployResult = Invoke-StagingDeploy -ArchivePath $packageResult.Path -TargetPath $StagingServerPath
    if (!$deployResult) {
        $deploymentSuccess = $false
    }
} elseif ($SkipDeploy.IsPresent) {
    Write-DeployMessage "Deployment skipped." "Info"
}

# Stage 4: Smoke Tests
$smokeTestPassed = $true
if ($deploymentSuccess) {
    $smokeTestPassed = Invoke-StagingSmokeTests -StagingPath $StagingServerPath
    if (!$smokeTestPassed) {
        Write-DeployMessage "Some smoke tests failed. Review logs." "Warning"
    }
}

# Final status
$elapsed       = New-TimeSpan -Start $DeployStartTime -End (Get-Date)
$statusMessage = if ($deploymentSuccess -and $smokeTestPassed) { "Staging deployment successful." } else { "Staging deployment completed with issues." }

Write-DeployMessage "" "Info"
Write-DeployMessage "========================================" $(if ($deploymentSuccess) { "Success" } else { "Warning" })
Write-DeployMessage "  $statusMessage" $(if ($deploymentSuccess) { "Success" } else { "Warning" })
Write-DeployMessage "  Duration:    $($elapsed.TotalSeconds.ToString('F1'))s" "Info"
Write-DeployMessage "========================================"

exit $(if ($deploymentSuccess -and $smokeTestPassed) { 0 } else { 1 })
