# MAT2-W03 sergeant attempt G2: rebuild walker_env_v2.dll and host_loop.exe
# from the extracted a62b286e blobs, following the pinned build_dll_v2.ps1 /
# build_host_loop.ps1 recipes verbatim (paths redirected to this attempt
# workspace). Agent: arrival-db26712d6a264e4899c951f55b074d80
$ErrorActionPreference = 'Stop'
$here = 'E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-W03\sergeant-arrival-db26712d\typeb_build'
$nvcc = 'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin\nvcc.exe'
$cl = 'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\cl.exe'
Set-Location -LiteralPath $here

# --- walker_env_v2.dll (pinned recipe: build_dll_v2.ps1) ---
& $nvcc -shared -arch=sm_89 -lineinfo -fmad=false -ccbin $cl -I. -std=c++17 -DUCRT_MATH_DEVICE --expt-relaxed-constexpr walker_env.cu -o walker_env_v2.dll -Xcompiler "/EHsc" 2>&1 | Out-File -Encoding utf8 build_dll_v2.log
$rc1 = $LASTEXITCODE
"NVCC_EXIT=$rc1"

# --- host_loop.exe (pinned recipe: build_host_loop.ps1) ---
$vcvars = 'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat'
cmd /v /c "call ""$vcvars"" >nul 2>&1 && cl /nologo /O2 /EHsc /I host_shim host_loop.cxx /Fe:host_loop.exe" 2>&1 | Out-File -Encoding utf8 build_host_loop.log
$rc2 = $LASTEXITCODE
"CL_EXIT=$rc2"

foreach ($f in @('walker_env_v2.dll','host_loop.exe')) {
  if (Test-Path $f) {
    $h = (Get-FileHash -Algorithm SHA256 $f).Hash
    $n = (Get-Item $f).Length
    "ARTIFACT $f sha256=$h bytes=$n"
  } else {
    "ARTIFACT $f MISSING"
    Get-Content ("build_" + ($f -replace '\.(dll|exe)$','') + ".log") -Tail 15
  }
}
