# generate_project_structure.ps1
# Outputs the full Chimera project structure to a text file

$ProjectRoot = "E:\PythonChimera\Chimera"
$OutputFile = "E:\PythonChimera\project_structure.txt"

function Get-RelativePath {
    param([string]$FullPath)
    return $FullPath.Substring($ProjectRoot.Length + 1)
}

function Format-Indent {
    param([int]$Depth, [string]$Prefix = "")
    $indent = ""
    for ($i = 0; $i -lt $Depth; $i++) {
        $indent += "   "
    }
    return "$indent$Prefix"
}

function Write-DirectoryTree {
    param(
        [string]$Path,
        [int]$Depth = 0,
        [System.Collections.ArrayList]$Lines,
        [bool]$ShowOnlyKeyFiles = $false
    )

    $relPath = Get-RelativePath $Path
    if ($Depth -eq 0) {
        $lines.Add("Chimera/") | Out-Null
    } else {
        $prefix = Format-Indent $Depth "├──"
        $lines.Add("$prefix$relPath/") | Out-Null
    }

    $items = Get-ChildItem -Path $Path -Force | Where-Object { $_.Name -notmatch '^\.' }

    if ($items.Count -eq 0) { return }

    $dirs = $items | Where-Object { $_.PSIsContainer }
    $files = $items | Where-Object { !($_.PSIsContainer) }

    # Sort: directories first, then files
    $sortedItems = @($dirs) + @($files)

    for ($i = 0; $i -lt $sortedItems.Count; $i++) {
        $item = $sortedItems[$i]
        $isLast = ($i -eq ($sortedItems.Count - 1))
        $connector = if ($isLast) "└──" else "├──"

        if ($item.PSIsContainer) {
            $line = "$(Format-Indent $Depth "")$connector $($item.Name)/"
            $lines.Add($line) | Out-Null
            Write-DirectoryTree -Path $item.FullName -Depth ($Depth + 1) -Lines $Lines -ShowOnlyKeyFiles $ShowOnlyKeyFiles
        } else {
            # Only show key files when flag is set, or skip hidden/generated
            if ($ShowOnlyKeyFiles) {
                $ext = $item.Extension.ToLower()
                $name = $item.Name.ToLower()
                $keyExtensions = @(".h", ".cpp", ".uplugin", ".ini", ".json", ".cs", ".sln", ".slnx")
                if ($ext -in $keyExtensions) {
                    $line = "$(Format-Indent $Depth "")$connector $($item.Name)"
                    $lines.Add($line) | Out-Null
                }
            } else {
                $line = "$(Format-Indent $Depth "")$connector $($item.Name)"
                $lines.Add($line) | Out-Null
            }
        }
    }
}

function Write-CppModuleSummary {
    param([System.Collections.ArrayList]$Lines)

    $SourceDir = "$ProjectRoot\Source\Chimera"
    if (!(Test-Path $SourceDir)) { return }

    $lines.Add("") | Out-Null
    $lines.Add("C++ Module Organization (Source/Chimera)") | Out-Null
    $lines.Add("=" * 50) | Out-Null

    # Categorize directories by type
    $categories = @{
        "Gameplay" = @()
        "AI & Behavior" = @()
        "Physics & Vehicles" = @()
        "Networking" = @()
        "UI & HUD" = @()
        "MCP & Automation" = @()
        "Combat & Combat Systems" = @()
        "Economy & Progression" = @()
        "Terrain & Landscape" = @()
        "VFX & Particles" = @()
        "Audio & Animation" = @()
        "Navigation & PCG" = @()
        "Weather & Environment" = @()
        "Inventory & Crafting" = @()
        "Social & Quests" = @()
        "Debug & Tools" = @()
        "Generated" = @()
        "Other" = @()
    }

    $dirs = Get-ChildItem -Path $SourceDir -Directory | Sort-Object Name

    foreach ($dir in $dirs) {
        $nameLower = $dir.Name.ToLower()

        if ($nameLower -match "^ai|vehicleai") { $categories["AI & Behavior"] += $dir }
        elseif ($nameLower -match "combat") { $categories["Combat & Combat Systems"] += $dir }
        elseif ($nameLower -match "physics|physenh|physaug|offroadcar|sportscar|variant_|vehicle|wheel|attitude|flightcontrol|thrust|spherical|edge|lagrange|landscape|terrain|procedural|levelgen|vehiclespawn") { $categories["Physics & Vehicles"] += $dir }
        elseif ($nameLower -match "networking|netenh") { $categories["Networking"] += $dir }
        elseif ($nameLower -match "ui|hud|d6hud|chimeraui") { $categories["UI & HUD"] += $dir }
        elseif ($nameLower -match "mcp") { $categories["MCP & Automation"] += $dir }
        elseif ($nameLower -match "econ|progression|crafting|inventory|quest|social|tutorial|sequence") { $categories["Economy & Progression"] += $dir }
        elseif ($nameLower -match "terrain|landscape|landscapecollision") { $categories["Terrain & Landscape"] += $dir }
        elseif ($nameLower -match "vfx|particle|streaming") { $categories["VFX & Particles"] += $dir }
        elseif ($nameLower -match "audio|animation|animenh") { $categories["Audio & Animation"] += $dir }
        elseif ($nameLower -match "navigation|pcg") { $categories["Navigation & PCG"] += $dir }
        elseif ($nameLower -match "weather|water") { $categories["Weather & Environment"] += $dir }
        elseif ($nameLower -match "customization") { $categories["Economy & Progression"] += $dir }
        elseif ($nameLower -match "debug") { $categories["Debug & Tools"] += $dir }
        elseif ($nameLower -match "generated") { $categories["Generated"] += $dir }
        else { $categories["Other"] += $dir }
    }

    foreach ($category in $categories.GetEnumerator()) {
        if ($category.Value.Count -eq 0) { continue }

        $lines.Add("") | Out-Null
        $lines.Add("[$($category.Key)]") | Out-Null

        foreach ($dir in $category.Value | Sort-Object Name) {
            $fileCount = (Get-ChildItem -Path $dir.FullName -File).Count
            $line = "  $($dir.Name)/ ($fileCount files)"
            $lines.Add($line) | Out-Null
        }
    }

    # Summary counts
    $totalDirs = ($dirs | Measure-Object).Count
    $totalFiles = 0
    foreach ($dir in $dirs) {
        $totalFiles += (Get-ChildItem -Path $dir.FullName -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match "\.(h|cpp)$" }).Count
    }

    $lines.Add("") | Out-Null
    $lines.Add("Summary: $($totalDirs) subsystem directories, ~$totalFiles C++ files") | Out-Null
}

# Build the output
$lines = [System.Collections.ArrayList]::new()

$lines.Add("=" * 60) | Out-Null
$lines.Add("  Chimera Project Structure") | Out-Null
$lines.Add("  Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm')") | Out-Null
$lines.Add("=" * 60) | Out-Null

# Full directory tree (key files only for depth)
Write-Host "Generating full project structure..." -NoNewline
$treeLines = [System.Collections.ArrayList]::new()
Write-DirectoryTree -Path $ProjectRoot -Depth 0 -Lines $treeLines -ShowOnlyKeyFiles $true

foreach ($line in $treeLines) {
    $lines.Add($line) | Out-Null
}

# C++ module summary
Write-CppModuleSummary -Lines $lines

# Write to file
$output = $lines.ToString()
Set-Content -Path $OutputFile -Value $output -Encoding UTF8

Write-Host "Done. Output written to: $OutputFile" -ForegroundColor Green
