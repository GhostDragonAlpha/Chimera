param(
 [ValidateRange(1024,65535)][int]$EnginePort=8110,
 [ValidateRange(1024,65535)][int]$GamePort=8210,
 [string]$Python='python',
 [switch]$SkipBuild
)
$ErrorActionPreference='Stop'
$projectRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
if($EnginePort -eq $GamePort){throw 'Engine and game ports must differ.'}
foreach($port in @($EnginePort,$GamePort)){
 if(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue){throw "Port $port is occupied; choose private free ports."}
}
Push-Location $projectRoot
$engineProcess=$null; $gameProcess=$null
try {
 $buildDir=Join-Path $projectRoot '.tmp\body-engine'
 if(-not $SkipBuild){
  & cmake -S ChimeraEngine/engine -B $buildDir
  if($LASTEXITCODE -ne 0){throw 'Configure failed.'}
  & cmake --build $buildDir --config Release --parallel 2
  if($LASTEXITCODE -ne 0){throw 'Build failed.'}
 }
 $exe=Join-Path $buildDir 'Release\chimera_engine.exe'
 if(-not(Test-Path -LiteralPath $exe)){throw 'Engine binary missing.'}
 $output=Join-Path $projectRoot '.tmp\creature-assembly'
 New-Item -ItemType Directory -Path $output -Force | Out-Null
 $stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
 $engineProcess=Start-Process -FilePath $exe -ArgumentList @("$EnginePort",'--hidden','1600','900','--no-restore') -WorkingDirectory (Split-Path $exe) -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $output "engine_$stamp.stdout.log") -RedirectStandardError (Join-Path $output "engine_$stamp.stderr.log")
 $deadline=[DateTime]::UtcNow.AddSeconds(30);$ready=$false
 do {
  if($engineProcess.HasExited){throw 'Engine exited during startup.'}
  try {$state=Invoke-RestMethod "http://127.0.0.1:$EnginePort/tick_state" -TimeoutSec 1;$ready=$true} catch {}
  if(-not $ready){Start-Sleep -Milliseconds 200}
 }while(-not $ready -and [DateTime]::UtcNow -lt $deadline)
 if(-not $ready){throw 'Engine did not become ready.'}
 & $Python -B -m tools.science_funnel.creature_scene --engine "http://127.0.0.1:$EnginePort"
 if($LASTEXITCODE -ne 0){throw 'Graph scene admission refused.'}
 $gameProcess=Start-Process -FilePath $Python -ArgumentList @('-B','tools/game_shell/server.py',"$GamePort",'--engine',"http://127.0.0.1:$EnginePort") -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $output "game_$stamp.stdout.log") -RedirectStandardError (Join-Path $output "game_$stamp.stderr.log")
 $scene=Get-Content -LiteralPath (Join-Path $output 'scene.json') -Raw | ConvertFrom-Json
 [ordered]@{engine_pid=$engineProcess.Id;game_pid=$gameProcess.Id;engine_port=$EnginePort;game_port=$GamePort;exe=$exe;exe_sha256=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash;graph_hash=$scene.graph_hash;scene=(Join-Path $output 'scene.json');launched_utc=[DateTime]::UtcNow.ToString('o');scope='Shared geometry reference; kinematic actuation; CPU membrane solver; not locomotion qualification.'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $output 'runtime.json') -Encoding utf8
 Write-Output "Creature: http://127.0.0.1:$GamePort (engine $EnginePort). Existing worlds were left running."
} catch {
 # Only processes created by this invocation can be stopped here.
 if($gameProcess -and -not $gameProcess.HasExited){Stop-Process -Id $gameProcess.Id}
 if($engineProcess -and -not $engineProcess.HasExited){Stop-Process -Id $engineProcess.Id}
 throw
} finally {Pop-Location}
