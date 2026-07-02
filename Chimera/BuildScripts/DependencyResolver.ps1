# =============================================================================
# Chimera Plugin Dependency Resolver
# =============================================================================
# Reads .uplugin files from all plugins, builds dependency graph,
# outputs correct compilation order, and detects circular dependencies.
# =============================================================================

function Get-PluginInfo {
    param(
        [string]$ProjectRoot,
        [string]$PluginName
    )

    $pluginPath = Join-Path $ProjectRoot "Plugins" $PluginName
    $upluginPath = Join-Path $pluginPath "${PluginName}.uplugin"

    if (!(Test-Path $upluginPath)) {
        Write-BuildMessage "No .uplugin file found for plugin: $PluginName" "Warning"
        return $null
    }

    try {
        $pluginData = Get-Content $upluginPath -Raw | ConvertFrom-Json

        $info = @{
            Name           = $PluginName
            Path           = $pluginPath
            UpluginPath    = $upluginPath
            Version        = $pluginData.Version
            VersionName    = if ($pluginData.VersionName) { $pluginData.VersionName } else { "N/A" }
            Category       = if ($pluginData.Category) { $pluginData.Category } else { "Unknown" }
            EnabledByDefault = if ($pluginData.EnabledByDefault) { $pluginData.EnabledByDefault } else { false }
            Dependencies   = @()
        }

        # Extract plugin dependencies from .uplugin file
        if ($pluginData.Plugins) {
            foreach ($dep in $pluginData.Plugins) {
                if ($dep.Name) {
                    $info.Dependencies += $dep.Name
                }
            }
        }

        return $info
    } catch {
        Write-BuildMessage "Failed to parse .uplugin for $PluginName: $_" "Error"
        return $null
    }
}

function Get-AllPlugins {
    param([string]$ProjectRoot)

    $pluginsDir = Join-Path $ProjectRoot "Plugins"

    if (!(Test-Path $pluginsDir)) {
        Write-BuildMessage "No Plugins directory found at: $pluginsDir" "Warning"
        return @()
    }

    $pluginDirs = Get-ChildItem -Path $pluginsDir -Directory
    $allPlugins = @()

    foreach ($dir in $pluginDirs) {
        $info = Get-PluginInfo -ProjectRoot $ProjectRoot -PluginName $dir.Name
        if ($info) {
            $allPlugins += $info
        }
    }

    return $allPlugins
}

function Build-DependencyGraph {
    param(
        [object[]]$Plugins,
        [string]$ProjectRoot
    )

    # Build adjacency list representation of the dependency graph
    $graph = @{}
    foreach ($plugin in $Plugins) {
        $graph[$plugin.Name] = @{
            Dependencies   = $plugin.Dependencies
            Dependents     = @()  # Plugins that depend on this one
            Depth          = 0
            Compiled       = $false
        }
    }

    # Build reverse mapping (dependents)
    foreach ($plugin in $Plugins) {
        foreach ($dep in $plugin.Dependencies) {
            if ($graph.ContainsKey($dep)) {
                $graph[$dep].Dependents += $plugin.Name
            }
        }
    }

    return $graph
}

function Detect-CircularDependencies {
    param(
        [hashtable]$Graph
    )

    $circularDeps = @()
    $visited = @{}
    $recursionStack = @{}

    function DFS-CheckCircular {
        param([string]$Node, [object[]]$Path)

        $visited[$Node] = $true
        $recursionStack[$Node] = $true

        if ($Graph.ContainsKey($Node)) {
            foreach ($dep in $Graph[$Node].Dependencies) {
                if (!$visited[$dep]) {
                    $newPath = $Path + @($Node)
                    $cycleResult = DFS-CheckCircular -Node $dep -Path $newPath

                    if ($cycleResult) {
                        $circularDeps += "Cycle detected: $($newPath + @($dep))"
                        return $true
                    }
                } else if ($recursionStack[$dep]) {
                    $cyclePath = $Path + @($Node, $dep)
                    $circularDeps += "Cycle detected: $($cyclePath -join ' -> ')"
                    return $true
                }
            }
        }

        $recursionStack[$Node] = false
        return $false
    }

    foreach ($pluginName in $Graph.Keys) {
        if (!$visited[$pluginName]) {
            DFS-CheckCircular -Node $pluginName -Path @()
        }
    }

    return $circularDeps
}

function TopologicalSort {
    param(
        [hashtable]$Graph,
        [string[]]$PluginNames
    )

    # Kahn's algorithm for topological sort
    $inDegree = @{}
    foreach ($name in $PluginNames) {
        if ($Graph.ContainsKey($name)) {
            $inDegree[$name] = 0
        }
    }

    # Calculate in-degrees
    foreach ($name in $PluginNames) {
        if ($Graph.ContainsKey($name)) {
            foreach ($dep in $Graph[$name].Dependencies) {
                if ($inDegree.ContainsKey($dep)) {
                    $inDegree[$dep] = ($inDegree[$dep] - 1)
                }
            }
        }
    }

    # Start with nodes that have no dependencies (in-degree = 0)
    $queue = @()
    foreach ($name in $PluginNames) {
        if ($Graph.ContainsKey($name)) {
            $depCount = 0
            foreach ($dep in $Graph[$name].Dependencies) {
                if ($inDegree.ContainsKey($dep)) {
                    $depCount++
                }
            }
            # Count how many plugins depend on this one (reverse: actual in-degree is deps count)
        }
    }

    # Simpler approach: sort by dependency depth
    $sorted = @()
    $resolved = @{}

    function Resolve-Plugin {
        param([string]$Name, [int]$Depth)

        if ($resolved[$Name]) { return }

        if ($Graph.ContainsKey($Name)) {
            foreach ($dep in $Graph[$Name].Dependencies) {
                if ($Graph.ContainsKey($dep)) {
                    Resolve-Plugin -Name $dep -Depth ($Depth + 1)
                } else {
                    # Dependency not found in graph (external), resolve it first
                    if (!$resolved[$dep]) {
                        $sorted += @{ Name = $dep; Depth = 0; Type = "External" }
                        $resolved[$dep] = $true
                    }
                }
            }

            if (!$resolved[$Name]) {
                $sorted += @{ Name = $Name; Depth = $Depth; Type = "Internal" }
                $resolved[$Name] = $true
            }
        } else {
            # Plugin not in graph (external dependency)
            if (!$resolved[$Name]) {
                $sorted += @{ Name = $Name; Depth = 0; Type = "External" }
                $resolved[$Name] = $true
            }
        }
    }

    foreach ($name in $PluginNames) {
        Resolve-Plugin -Name $name -Depth 0
    }

    return $sorted
}

function Get-PluginDependencyOrder {
    param([string]$ProjectRoot)

    Write-BuildMessage "Resolving plugin dependencies..." "Info"

    # Get all plugins in the project
    $plugins = Get-AllPlugins -ProjectRoot $ProjectRoot

    if ($plugins.Count -eq 0) {
        Write-BuildMessage "No plugins found." "Warning"
        return @()
    }

    Write-BuildMessage "Found $($plugins.Count) plugin(s):" "Info"
    foreach ($p in $plugins) {
        $depStr = if ($p.Dependencies.Count -gt 0) { " -> depends on: $($p.Dependencies -join ', ')" } else { "" }
        Write-BuildMessage "  - $($p.Name)$depStr" "Info"
    }

    # Build dependency graph
    $graph = Build-DependencyGraph -Plugins $plugins -ProjectRoot $ProjectRoot

    # Detect circular dependencies
    $circularDeps = Detect-CircularDependencies -Graph $graph

    if ($circularDeps.Count -gt 0) {
        Write-BuildMessage "WARNING: Circular dependencies detected!" "Warning"
        foreach ($cycle in $circularDeps) {
            Write-BuildMessage "  Cycle: $cycle" "Error"
        }
        Write-BuildMessage "Build order may be incorrect. Consider restructuring plugin dependencies." "Warning"
    } else {
        Write-BuildMessage "No circular dependencies detected." "Success"
    }

    # Get plugin names for sorting
    $pluginNames = @($plugins | ForEach-Object { $_.Name })

    # Compute topological sort for correct compilation order
    $sortedPlugins = TopologicalSort -Graph $graph -PluginNames $pluginNames

    Write-BuildMessage "" "Info"
    Write-BuildMessage "Recommended compilation order:" "Info"
    for ($i = 0; $i -lt $sortedPlugins.Count; $i++) {
        $sp = $sortedPlugins[$i]
        $typeMarker = if ($sp.Type -eq "Internal") { "[Plugin]" } else { "[External]" }
        Write-BuildMessage "  $($i + 1). $typeMarker $($sp.Name) (depth: $($sp.Depth))" "Info"
    }

    return $sortedPlugins
}

function Get-DependencyTree {
    param(
        [string]$PluginName,
        [hashtable]$Graph,
        [int]$IndentLevel = 0
    )

    if (!$Graph.ContainsKey($PluginName)) {
        return "  " * $IndentLevel + "- $PluginName (external)"
    }

    $pluginInfo = $Graph[$PluginName]
    $result = "  " * $IndentLevel + "- $($PluginName) [depth: $($pluginInfo.Depth)]"

    if ($pluginInfo.Dependencies.Count -gt 0) {
        foreach ($dep in $pluginInfo.Dependencies) {
            $childResult = Get-DependencyTree -PluginName $dep -Graph $Graph -IndentLevel ($IndentLevel + 1)
            $result += "`n$childResult"
        }
    }

    return $result
}

function Export-DependencyReport {
    param(
        [string]$ProjectRoot,
        [string]$OutputPath
    )

    Write-BuildMessage "Generating dependency report..." "Info"

    $plugins = Get-AllPlugins -ProjectRoot $ProjectRoot
    if ($plugins.Count -eq 0) { return }

    $graph = Build-DependencyGraph -Plugins $plugins -ProjectRoot $ProjectRoot
    $circularDeps = Detect-CircularDependencies -Graph $graph
    $sortedPlugins = TopologicalSort -Graph $graph -PluginNames @($plugins | ForEach-Object { $_.Name })

    $report = @{
        ReportType         = "DependencyAnalysis"
        Timestamp          = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fff"
        PluginCount        = $plugins.Count
        CircularDependencies = if ($circularDeps.Count -gt 0) { $circularDeps } else { @() }
        CompilationOrder   = $sortedPlugins
        Plugins            = @($plugins | ForEach-Object {
            @{
                Name           = $_.Name
                Version        = $_.Version
                Category       = $_.Category
                Dependencies   = $_.Dependencies
                EnabledByDefault = $_.EnabledByDefault
            }
        })
    }

    try {
        ConvertTo-Json $report -Depth 10 | Out-File $OutputPath -Encoding UTF8
        Write-BuildMessage "Dependency report saved to: $OutputPath" "Success"
    } catch {
        Write-BuildMessage "Failed to save dependency report: $_" "Error"
    }

    return $report
}
