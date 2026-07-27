# verify_setup.ps1
# PowerShell verification script for Chimera project configuration

$ErrorActionPreference = "Stop"
$ProjectRoot = "E:\PythonChimera\Chimera"
$UprojectFile = "$ProjectRoot\Chimera.uproject"
$DefaultPluginsIni = "$ProjectRoot\Config\DefaultPlugins.ini"
$DefaultGameIni = "$ProjectRoot\Config\DefaultGame.ini"

$Results = @{
    PluginsInUproject = @()
    PluginsInIni = @()
    Issues = @()
}

function Test-FileExists {
    param([string]$Path, [string]$Name)
    if (Test-Path $Path) {
        Write-Host "[OK]   $Name" -ForegroundColor Green
        return $true
    } else {
        Write-Host "[MISSING] $Name ($Path)" -ForegroundColor Red
        $Results.Issues += "Missing: $Name at $Path"
        return $false
    }
}

function Test-PluginInUproject {
    param([string]$PluginName)
    $content = Get-Content $UprojectFile -Raw
    if ($content -match "`"$PluginName`"\s*:\s*true") {
        Write-Host "[OK]   $PluginName (in Chimera.uproject)" -ForegroundColor Green
        return $true
    } else {
        Write-Host "[MISSING] $PluginName not enabled in Chimera.uproject" -ForegroundColor Red
        $Results.Issues += "$PluginName not enabled in Chimera.uproject"
        return $false
    }
}

function Test-PluginInDefaultPluginsIni {
    param([string]$PluginName)
    if (!(Test-Path $DefaultPluginsIni)) {
        Write-Host "[MISSING] DefaultPlugins.ini not found" -ForegroundColor Red
        $Results.Issues += "DefaultPlugins.ini missing"
        return $false
    }
    $content = Get-Content $DefaultPluginsIni -Raw
    if ($content -match "\[$PluginName\]" -and $content -match "bEnabled\s*=\s*True") {
        Write-Host "[OK]   $PluginName (in DefaultPlugins.ini)" -ForegroundColor Green
        return $true
    } else {
        Write-Host "[MISSING] $PluginName not enabled in DefaultPlugins.ini" -ForegroundColor Red
        $Results.Issues += "$PluginName not enabled in DefaultPlugins.ini"
        return $false
    }
}

function Test-McpSettingsInGameIni {
    param([string]$Setting, [string]$ExpectedValue)
    if (!(Test-Path $DefaultGameIni)) {
        Write-Host "[MISSING] DefaultGame.ini not found" -ForegroundColor Red
        $Results.Issues += "DefaultGame.ini missing"
        return $false
    }
    $content = Get-Content $DefaultGameIni -Raw
    if ($content -match "$Setting\s*=\s*$ExpectedValue") {
        Write-Host "[OK]   $Setting=$ExpectedValue (in DefaultGame.ini)" -ForegroundColor Green
        return $true
    } else {
        Write-Host "[MISMATCH] $Setting expected=$ExpectedValue not found in DefaultGame.ini" -ForegroundColor Red
        $Results.Issues += "Mcp setting mismatch: $Setting expected=$ExpectedValue"
        return $false
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Chimera Project Setup Verification" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check project file
Test-FileExists $UprojectFile "Chimera.uproject" | Out-Null

# Verify required plugins in .uproject
Write-Host "`n--- Plugins in Chimera.uproject ---" -ForegroundColor Yellow
$RequiredPlugins = @("McpAutomationBridge", "PythonScriptPlugin")
foreach ($plugin in $RequiredPlugins) {
    Test-PluginInUproject $plugin | Out-Null
}

# Verify plugins in DefaultPlugins.ini
Write-Host "`n--- Plugins in DefaultPlugins.ini ---" -ForegroundColor Yellow
$IniPlugins = @("McpAutomationBridge", "PythonScriptPlugin")
foreach ($plugin in $IniPlugins) {
    Test-PluginInDefaultPluginsIni $plugin | Out-Null
}

# Verify MCP settings in DefaultGame.ini
Write-Host "`n--- Native MCP Settings ---" -ForegroundColor Yellow
Test-McpSettingsInGameIni "bEnableNativeMCP" "True" | Out-Null
Test-McpSettingsInGameIni "NativeMCPPort" "3000" | Out-Null

# Verify DLL exists
Write-Host "`n--- Plugin Binary ---" -ForegroundColor Yellow
$DllPath = "$ProjectRoot\Plugins\McpAutomationBridge\Binaries\Win64\UnrealEditor-McpAutomationBridge-Win64-DebugGame.dll"
Test-FileExists $DllPath "MCP Bridge DLL" | Out-Null

# Report issues
Write-Host ""
if ($Results.Issues.Count -gt 0) {
    Write-Host "--- Configuration Issues Found ---" -ForegroundColor Red
    foreach ($issue in $Results.Issues) {
        Write-Host "  * $issue" -ForegroundColor Red
    }
} else {
    Write-Host "--- All checks passed. Setup is correct. ---" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Verification Complete" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
