# build_host_loop.ps1 -- rebuild the CPU-replay harness from the current
# walker_kernels.cuh + host_loop.cxx under the MSVC environment.
$here = "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu"
Set-Location -LiteralPath $here
cmd /v /c "call ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat >nul 2>&1 && cl /nologo /O2 /EHsc /I host_shim host_loop.cxx /Fe:host_loop.exe"""
$code = $LASTEXITCODE
Get-Content build_host_loop.log -ErrorAction SilentlyContinue | Out-Null
"EXIT=$code"
