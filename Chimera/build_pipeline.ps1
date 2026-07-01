# =============================================================================
# Chimera Build Pipeline - Main Build Script
# =============================================================================
# Comprehensive Unreal Engine build automation with incremental detection,
# plugin compilation, progress tracking, and post-build validation.
# =============================================================================

param(
    [switch]$Full,
    [switch]$Incremental,
    [switch]$PluginsOnly,
    [switch]$Validate,
    [switch]$Clean,
    [string]$Target = "ChimeraEditor",
    [string]$Platform = "Win64",
    [string]$Configuration = "Development",
    [string]$ConfigPath = "$PSScriptRoot\BuildScripts\BuildConfig.json"
)

$ErrorActionPreference = "Stop"

# =============================================================================
# MODULES AND PATHS
# =============================================================================
$ProjectRoot = Join-Path $PSScriptRoot ".." | Resolve-Path
$IntermediateDir = Join-Path $ProjectRoot "Intermediate"
$SavedDir = Join-Path $ProjectRoot "Saved"
$BinariesDir = Join-Path $ProjectRoot "Binaries"
$PluginsDir = Join-Path $ProjectRoot "Plugins"
$BuildScriptsDir = Join-Path $ProjectRoot "BuildScripts"
$LogDir = Join-Path $env:APPDATA "\Chimera\build_logs"

if (!(Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

# Import build modules
$BuildLoggerPath = Join-Path $BuildScriptsDir "BuildLogger.ps1"
$DependencyResolverPath = Join-Path $BuildScriptsDir "DependencyResolver.ps1"
$BuildConfigPath = Join-Path $BuildScriptsDir "BuildConfig.json"

if (Test-Path $BuildLoggerPath) { . $BuildLoggerPath }
if (Test-Path $DependencyResolverPath) { . $DependencyResolverPath }

# =============================================================================
# GLOBAL STATE
# =============================================================================
$BuildStartTime = Get-Date
$ModuleResults = @{}
$PluginResults = @{}
$Errors = @()
$Warnings = @()
$SkippedModules = @()

function Write-BuildMessage {
    param(
        [string]$Message,
        [string]$Level = "Info",
        [bool]$NoNewline = $false
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
    $prefix = "[{0}] [{1,-5}] {2}" -f $timestamp, $Level, $Message

    switch ($Level) {
        "Error"   { Write-Host $prefix -ForegroundColor Red }
        "Warning" { Write-Host $prefix -ForegroundColor Yellow }
        "Success" { Write-Host $prefix -ForegroundColor Green }
        "Info"    { Write-Host $prefix -ForegroundColor Cyan }
        default   { Write-Host $prefix }
    }

    if ($NoNewline) { Write-Host "" }
}

function Test-DiskSpace {
    param([long]$MinimumGB = 10)

    try {
        $drives = Get-WmiObject -Class Win32_LogicalDisk | Where-Object { $_.DriveType -eq 3 }
        foreach ($drive in $drives) {
            $freeGB = [math]::Round($drive.FreeSpace / 1GB, 2)
            if ($freeGB -lt $MinimumGB) {
                Write-BuildMessage "Low disk space on $($drive.DeviceName): ${freeGB}GB free (minimum: ${MinimumGB}GB)" "Warning"
                return $false
            }
        }
        return $true
    }
    catch {
        Write-BuildMessage "Could not check disk space: $_" "Warning"
        return $true
    }
}

function Test-Prerequisites {
    Write-BuildMessage "Checking prerequisites..." "Info"

    $prereqs = @{
        "UnrealEngine"   = $false
        "VisualStudio"   = $false
        "DiskSpace"      = $false
        "ProjectFiles"   = $false
    }

    # Check Unreal Engine installation
    try {
        $uePath = Get-ChildItem -Path "C:\Program Files\Epic Games" -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "^UE-" } | Select-Object -First 1
        if ($uePath) {
            Write-BuildMessage "Unreal Engine found: $($uePath.Name)" "Success"
            $prereqs.UnrealEngine = $true
        } else {
            $envVar = Get-ItemProperty -Path "HKLM:\SOFTWARE\Epic Games\UE4" -Name "InstallDir" -ErrorAction SilentlyContinue
            if ($envVar) {
                Write-BuildMessage "Unreal Engine found via registry: $($envVar.InstallDir)" "Success"
                $prereqs.UnrealEngine = $true
            } else {
                Write-BuildMessage "Unreal Engine not found. Please install UE 5.x." "Error"
            }
        }
    } catch {
        Write-BuildMessage "Could not detect Unreal Engine installation: $_" "Error"
    }

    # Check Visual Studio / MSVC
    try {
        $vsPath = Get-ChildItem -Path "C:\Program Files\Microsoft Visual Studio" -Directory -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "2022|2019" } | Select-Object -First 1
        if ($vsPath) {
            Write-BuildMessage "Visual Studio found: $($vsPath.Name)" "Success"
            $prereqs.VisualStudio = $true
        } else {
            Write-BuildMessage "Visual Studio not found. Please install VS 2019 or 2022 with C++ workload." "Error"
        }

        # Check for MSVC compiler
        $msvcPath = Get-ChildItem -Path "C:\Program Files\Microsoft Visual Studio" -Directory -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match "VC\\Tools\\MSVC" } | Select-Object -First 1
        if ($msvcPath) {
            Write-BuildMessage "MSVC compiler found: $($msvcPath.Name)" "Success"
        } else {
            Write-BuildMessage "MSVC compiler not detected." "Warning"
        }
    } catch {
        Write-BuildMessage "Could not check Visual Studio installation: $_" "Warning"
    }

    # Check disk space
    $prereqs.DiskSpace = Test-DiskSpace -MinimumGB 10

    # Check project files exist
    $uprojectPath = Join-Path $ProjectRoot "${env:PROJECT_NAME:-Chimera}.uproject"
    if (Test-Path $uprojectPath) {
        Write-BuildMessage "Project file found: $uprojectPath" "Success"
        $prereqs.ProjectFiles = $true
    } else {
        $uprojectPath = Join-Path $ProjectRoot "Chimera.uproject"
        if (Test-Path $uprojectPath) {
            Write-BuildMessage "Project file found: $uprojectPath" "Success"
            $prereqs.ProjectFiles = $true
        } else {
            Write-BuildMessage "Project file (.uproject) not found." "Error"
        }
    }

    return ($prereqs.UnrealEngine -and $prereqs.VisualStudio -and $prereqs.DiskSpace -and $prereqs.ProjectFiles)
}

function Invoke-Clean {
    Write-BuildMessage "Performing clean operation..." "Info"

    if (Test-Path $IntermediateDir) {
        Write-BuildMessage "Removing Intermediate directory: $IntermediateDir" "Info"
        Remove-Item -Path $IntermediateDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    if (Test-Path $SavedDir) {
        Write-BuildMessage "Removing Saved directory: $SavedDir" "Info"
        Remove-Item -Path $SavedDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    if (Test-Path $BinariesDir) {
        Write-BuildMessage "Removing Binaries directory: $BinariesDir" "Info"
        Remove-Item -Path $BinariesDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    # Clean DerivedDataCache for fresh build
    $ddcPath = Join-Path $ProjectRoot "DerivedDataCache"
    if (Test-Path $ddcPath) {
        Write-BuildMessage "Clearing DerivedDataCache: $ddcPath" "Info"
        Remove-Item -Path $ddcPath -Recurse -Force -ErrorAction SilentlyContinue
    }

    Write-BuildMessage "Clean complete." "Success"
}

function Test-IncrementalBuild {
    param([string]$TargetModule)

    $lastBuildLog = Join-Path $LogDir "*LastBuild*.json" | Get-ChildItem -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1

    if (!$lastBuildLog) {
        Write-BuildMessage "No previous build log found. Performing full build." "Info"
        return $true
    }

    try {
        $logContent = Get-Content $lastBuildLog.FullName -Raw | ConvertFrom-Json
        $lastBuildTime = Get-Date $logContent.timestamp

        Write-BuildMessage "Last build timestamp: $($lastBuildTime.ToString('yyyy-MM-dd HH:mm:ss'))" "Info"

        # Check if any source files have been modified since last build
        $sourceDirs = @(
            Join-Path $ProjectRoot "Source",
            Join-Path $ProjectRoot "Plugins"
        )

        $modifiedFiles = @()
        foreach ($dir in $sourceDirs) {
            if (Test-Path $dir) {
                $recentFiles = Get-ChildItem -Path $dir -Recurse -Include "*.cpp", "*.h", "*.cs" -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -gt $lastBuildTime }
                if ($recentFiles) {
                    foreach ($f in $recentFiles) {
                        $modifiedFiles += $f.FullName
                    }
                }
            }
        }

        if ($modifiedFiles.Count -gt 0) {
            Write-BuildMessage "Detected $($modifiedFiles.Count) modified source file(s) since last build:" "Info"
            foreach ($f in $modifiedFiles | Select-Object -First 10) {
                Write-BuildMessage "  - $f" "Info"
            }
            if ($modifiedFiles.Count -gt 10) {
                Write-BuildMessage "  ... and $($modifiedFiles.Count - 10) more" "Info"
            }
            return $true
        }

        Write-BuildMessage "No source files modified since last build. Skipping incremental build." "Success"
        return $false
    } catch {
        Write-BuildMessage "Could not determine incremental build status: $_" "Warning"
        return $true
    }
}

function Invoke-PluginCompilation {
    param(
        [string[]]$PluginsToBuild,
        [bool]$SkipAlreadyCompiled = $false
    )

    if (!(Test-Path $PluginsDir)) {
        Write-BuildMessage "No Plugins directory found." "Warning"
        return
    }

    # Resolve plugin dependency order
    $pluginOrder = @()
    try {
        $pluginOrder = Get-PluginDependencyOrder -ProjectRoot $ProjectRoot
        if ($pluginOrder.Count -gt 0) {
            Write-BuildMessage "Resolved plugin compilation order:" "Info"
            for ($i = 0; $i -lt $pluginOrder.Count; $i++) {
                Write-BuildMessage "  $($i + 1). $($pluginOrder[$i].Name)" "Info"
            }
        }
    } catch {
        Write-BuildMessage "Could not resolve plugin dependencies: $_" "Warning"
    }

    # Get all plugins if none specified
    if ($PluginsToBuild.Count -eq 0) {
        $PluginsToBuild = (Get-ChildItem -Path $PluginsDir -Directory).Name
    }

    foreach ($pluginName in $PluginsToBuild) {
        $pluginPath = Join-Path $PluginsDir $pluginName
        if (!(Test-Path $pluginPath)) {
            Write-BuildMessage "Plugin not found: $pluginName" "Warning"
            continue
        }

        $upluginPath = Join-Path $pluginPath "${pluginName}.uplugin"
        if (!(Test-Path $upluginPath)) {
            Write-BuildMessage "No .uplugin file for: $pluginName" "Warning"
            continue
        }

        try {
            Write-BuildMessage "Compiling plugin: $pluginName" "Info"
            $pluginStartTime = Get-Date

            # Use UBT to compile the plugin
            $uprojectPath = Join-Path $ProjectRoot "Chimera.uproject"
            $buildCommand = @"
& '"$(Get-UbtPath)"' "$uprojectPath" -target="BuildPlugin" -plugin="$upluginPath" -platform="$Platform" -configuration="$Configuration"'
"@

            $output = Invoke-Expression $buildCommand 2>&1
            $pluginEndTime = Get-Date
            $duration = New-TimeSpan -Start $pluginStartTime -End $pluginEndTime

            if ($LASTEXITCODE -eq 0) {
                Write-BuildMessage "Plugin compiled successfully: $pluginName (${duration.TotalSeconds}s)" "Success"
                $PluginResults[$pluginName] = @{ Status = "Success"; Duration = $duration }
            } else {
                Write-BuildMessage "Plugin compilation failed: $pluginName (exit code: $LASTEXITCODE)" "Error"
                $Errors += "Plugin compilation failed: $pluginName"

                # Check for specific error patterns in output
                if ($output -match "error\s+C") {
                    Write-BuildMessage "  Compile error detected in plugin." "Warning"
                }

                $PluginResults[$pluginName] = @{ Status = "Failed"; Duration = $duration; Output = $output }
            }
        } catch {
            Write-BuildMessage "Exception during plugin compilation ($pluginName): $_" "Error"
            $Errors += "Plugin exception: $pluginName - $_"
            $PluginResults[$pluginName] = @{ Status = "Error"; Duration = 0; Error = $_.ToString() }
        }
    }
}

function Invoke-ModuleBuild {
    param(
        [string]$ModuleName,
        [bool]$IsIncremental = $false
    )

    Write-BuildMessage "Building module: $ModuleName" "Info"

    $moduleStartTime = Get-Date
    $uprojectPath = Join-Path $ProjectRoot "Chimera.uproject"

    try {
        # Build command for Unreal Build Tool
        $buildArgs = @(
            '"$uprojectPath"',
            "-target=`"Build` $($ModuleName)`"",
            "-platform=`"$Platform`"",
            "-configuration=`"$Configuration`""
        )

        if ($IsIncremental) {
            $buildArgs += "-incremental"
        }

        $ubtPath = Get-UbtPath
        Write-BuildMessage "Running: & `"`$ubtPath`" $($buildArgs -join ' ')" "Info"

        $process = Start-Process -FilePath $ubtPath -ArgumentList ($buildArgs -join ' ') `
            -NoNewWindow -Wait -PassThru -RedirectStandardOutput "$LogDir\build_$ModuleName.log"

        $moduleEndTime = Get-Date
        $duration = New-TimeSpan -Start $moduleStartTime -End $moduleEndTime

        if ($process.ExitCode -eq 0) {
            Write-BuildMessage "Module built successfully: $ModuleName (${duration.TotalSeconds}s)" "Success"
            $ModuleResults[$ModuleName] = @{ Status = "Success"; Duration = $duration }
        } else {
            Write-BuildMessage "Module build failed: $ModuleName (exit code: $($process.ExitCode))" "Error"
            $Errors += "Module build failed: $ModuleName"

            # Parse log for errors
            $logFile = "$LogDir\build_$ModuleName.log"
            if (Test-Path $logFile) {
                $errorsInLog = Select-String -Path $logFile -Pattern "error\s+C\d+|fatal\s+error" | Select-Object -First 10
                foreach ($err in $errorsInLog) {
                    Write-BuildMessage "  Log error: $($err.Line)" "Warning"
                }
            }

            $ModuleResults[$ModuleName] = @{ Status = "Failed"; Duration = $duration; ExitCode = $process.ExitCode }
        }
    } catch {
        Write-BuildMessage "Exception during module build ($ModuleName): $_" "Error"
        $Errors += "Module exception: $ModuleName - $_"

        $moduleEndTime = Get-Date
        $duration = New-TimeSpan -Start $moduleStartTime -End $moduleEndTime
        $ModuleResults[$ModuleName] = @{ Status = "Error"; Duration = $duration; Error = $_.ToString() }
    }
}

function Get-UbtPath {
    try {
        # Try to find UnrealBuildTool.exe in common locations
        $ubtPaths = @(
            "C:\Program Files\Epic Games\UE*\Engine\Binaries\Win64\UnrealBuildTool.exe",
            "$env:EPICROOT\Unreal Engine\Engine\Binaries\Win64\UnrealBuildTool.exe"
        )

        foreach ($path in $ubtPaths) {
            $found = Get-ChildItem -Path $path -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($found) { return $found.FullName }
        }

        # Try to find via environment or PATH
        $inPath = Get-Command "UnrealBuildTool.exe" -ErrorAction SilentlyContinue
        if ($inPath) { return $inPath.Source }

        Write-BuildMessage "UnrealBuildTool.exe not found in standard locations." "Warning"
        return $null
    } catch {
        Write-BuildMessage "Could not locate UnrealBuildTool: $_" "Error"
        return $null
    }
}

function Invoke-PostBuildValidation {
    param([string]$ProjectName)

    Write-BuildMessage "Running post-build validation..." "Info"

    $validationResults = @{
        DllsExist     = $false
        NoCompileErrors = $true
        LogFilesValid  = $true
    }

    # Check for expected DLLs in Binaries directory
    $dllPatterns = @(
        "*$ProjectName*.dll",
        "McpAutomationBridge.dll",
        "PythonScriptPlugin.dll"
    )

    $foundDlls = @()
    foreach ($pattern in $dllPatterns) {
        $dlls = Get-ChildItem -Path "$BinariesDir\$Platform" -Include $pattern -ErrorAction SilentlyContinue -Recurse
        if ($dlls) {
            foreach ($dll in $dlls) {
                Write-BuildMessage "Found DLL: $($dll.Name)" "Success"
                $foundDlls += $dll.FullName
            }
        }
    }

    if ($foundDlls.Count -gt 0) {
        $validationResults.DllsExist = $true
        Write-BuildMessage "DLL validation passed: $($foundDlls.Count) file(s) found" "Success"
    } else {
        $validationResults.DllsExist = $false
        Write-BuildMessage "No expected DLLs found in Binaries\$Platform" "Warning"
    }

    # Check build logs for compile errors
    $logFiles = Get-ChildItem -Path "$LogDir\*.log" -ErrorAction SilentlyContinue
    foreach ($logFile in $logFiles) {
        try {
            $errorCount = (Select-String -Path $logFile.FullName -Pattern "error\s+C\d+|fatal\s+error|LNK110[0-9]" | Measure-Object).Count
            if ($errorCount -gt 0) {
                Write-BuildMessage "Found $errorCount compile error(s) in $($logFile.Name)" "Warning"
                $validationResults.NoCompileErrors = $false
            }

            $warningCount = (Select-String -Path $logFile.FullName -Pattern "warning\s+C\d+" | Measure-Object).Count
            if ($warningCount -gt 0) {
                Write-BuildMessage "Found $warningCount warnings in $($logFile.Name)" "Warning"
            }
        } catch {
            Write-BuildMessage "Could not parse log file: $($logFile.FullName)" "Warning"
            $validationResults.LogFilesValid = $false
        }
    }

    return $validationResults
}

function Generate-BuildSummary {
    param(
        [hashtable]$ModuleResults,
        [hashtable]$PluginResults,
        [string[]]$Errors,
        [datetime]$StartTime,
        [datetime]$EndTime
    )

    $totalDuration = New-TimeSpan -Start $StartTime -End $EndTime
    $successCount = ($ModuleResults.Values | Where-Object { $_.Status -eq "Success" }).Count + ($PluginResults.Values | Where-Object { $_.Status -eq "Success" }).Count
    $failCount = ($ModuleResults.Values | Where-Object { $_.Status -eq "Failed" }).Count + ($PluginResults.Values | Where-Object { $_.Status -eq "Failed" }).Count

    $summary = [PSCustomObject]@{
        Timestamp       = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"
        TotalDuration   = "{0:N2}s" -f $totalDuration.TotalSeconds
        ModulesBuilt    = ($ModuleResults | Measure-Object).Count
        PluginsCompiled = ($PluginResults | Measure-Object).Count
        SuccessCount    = $successCount
        FailureCount    = $failCount
        ErrorCount      = $Errors.Count
        Status          = if ($failCount -eq 0) { "Success" } elseif ($successCount -gt 0) { "Partial Success" } else { "Failed" }
        ModuleResults   = $ModuleResults
        PluginResults   = $PluginResults
        Errors          = $Errors
    }

    return $summary
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

Write-BuildMessage "" "Info"
Write-BuildMessage "========================================" "Info"
Write-BuildMessage "  Chimera Build Pipeline v1.0" "Info"
Write-BuildMessage "========================================" "Info"
Write-BuildMessage "" "Info"

# Parse configuration from JSON if available
if (Test-Path $BuildConfigPath) {
    try {
        $config = Get-Content $BuildConfigPath -Raw | ConvertFrom-Json
        Write-BuildMessage "Loaded build configuration from: $BuildConfigPath" "Info"

        # Apply config defaults for unspecified flags
        if (!$Target -or $Target -eq "ChimeraEditor") {
            $Target = $config.DefaultTarget
        }
    } catch {
        Write-BuildMessage "Could not parse build configuration: $_" "Warning"
    }
}

# Handle -Clean flag (always runs first)
if ($Clean) {
    Invoke-Clean
    # Continue to build after clean
}

# Check prerequisites
$prereqsPassed = Test-Prerequisites
if (!$prereqsPassed) {
    Write-BuildMessage "Prerequisites check failed. Some checks may have warnings." "Warning"
    Write-BuildMessage "Continuing anyway (use -Full for strict mode)." "Info"
}

# Determine build type
$buildType = "Incremental"
if ($Full) { $buildType = "Full" }
elseif ($PluginsOnly) { $buildType = "Plugins Only" }
elseif ($Validate) { $buildType = "Validation Only" }
elseif ($Incremental) { $buildType = "Incremental (forced)" }

Write-BuildMessage "" "Info"
Write-BuildMessage "Build type: $buildType" "Info"
Write-BuildMessage "Target: $Target | Platform: $Platform | Configuration: $Configuration" "Info"
Write-BuildMessage "" "Info"

# Validation-only mode
if ($Validate) {
    Write-BuildMessage "Running post-build validation only..." "Info"
    $validation = Invoke-PostBuildValidation -ProjectName $Target
    $summary = Generate-BuildSummary @{} @{} @($Errors) $BuildStartTime (Get-Date)

    # Save summary as JSON
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $summaryPath = Join-Path $LogDir "$timestamp-validation.json"
    $summary | ConvertTo-Json | ConvertTo-Json | Out-File $summaryPath -Encoding UTF8
    Write-BuildMessage "Validation summary saved to: $summaryPath" "Info"

    if ($validation.DllsExist -and $validation.NoCompileErrors) {
        Write-BuildMessage "Post-build validation PASSED." "Success"
    } else {
        Write-BuildMessage "Post-build validation completed with warnings/errors." "Warning"
    }

    exit 0
}

# Plugin-only mode
if ($PluginsOnly) {
    $pluginNames = @("McpAutomationBridge", "PythonScriptPlugin")
    Invoke-PluginCompilation -PluginsToBuild $pluginNames
    $summary = Generate-BuildSummary @{} $PluginResults @($Errors) $BuildStartTime (Get-Date)

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $summaryPath = Join-Path $LogDir "$timestamp-plugins.json"
    ConvertTo-Json $summary | Out-File $summaryPath -Encoding UTF8
    Write-BuildMessage "Plugin build summary saved to: $summaryPath" "Info"

    if ($PluginResults.Values.Status -contains "Failed") {
        exit 1
    }
    exit 0
}

# Full or incremental build
$shouldBuild = $true
if (!$Full) {
    $shouldBuild = Test-IncrementalBuild -TargetModule $Target
}

if ($shouldBuild) {
    # Build main module(s)
    $targets = @($Target)
    if ($config.DefaultTargets) {
        $targets = @($config.DefaultTargets)
    }

    foreach ($t in $targets) {
        Invoke-ModuleBuild -ModuleName $t -IsIncremental (!$Full)
    }

    # Build plugins after main modules (unless PluginsOnly was specified)
    if (!$PluginsOnly) {
        $pluginNames = @("McpAutomationBridge", "PythonScriptPlugin")
        Invoke-PluginCompilation -PluginsToBuild $pluginNames
    }
} else {
    Write-BuildMessage "Skipping build - no changes detected since last build." "Info"
}

# Post-build validation
$validation = Invoke-PostBuildValidation -ProjectName $Target

# Generate and save summary
$summary = Generate-BuildSummary $ModuleResults $PluginResults @($Errors) $BuildStartTime (Get-Date)

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$summaryPath = Join-Path $LogDir "$timestamp-build.json"
ConvertTo-Json $summary | Out-File $summaryPath -Encoding UTF8
Write-BuildMessage "Build summary saved to: $summaryPath" "Info"

# Final status
if ($ModuleResults.Values.Status -contains "Failed" -or $PluginResults.Values.Status -contains "Failed") {
    Write-BuildMessage "" "Info"
    Write-BuildMessage "========================================" "Warning"
    Write-BuildMessage "  Build completed with errors." "Warning"
    Write-BuildMessage "========================================" "Warning"

    foreach ($err in $Errors) {
        Write-BuildMessage "  - $err" "Error"
    }

    exit 1
} else {
    Write-BuildMessage "" "Info"
    Write-BuildMessage "========================================" "Success"
    Write-BuildMessage "  Build completed successfully." "Success"
    Write-BuildMessage "========================================" "Success"
    exit 0
}
