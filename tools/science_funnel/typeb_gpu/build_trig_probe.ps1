# build_trig_probe.ps1 -- build the pair-3 libdevice-vs-CRT transcendental
# probe pair: trig_probe.exe (nvcc device, sm_89) and trig_probe_host.exe
# (cl host). Both consume trig_inputs.txt.
# Trailer Agent: GLM 5.3.
$nvcc = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin\nvcc.exe"
$cl = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\cl.exe"
$here = "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu"
Set-Location -LiteralPath $here
& $nvcc -arch=sm_89 -ccbin $cl -std=c++17 trig_probe.cu -o trig_probe.exe 2>&1 | Out-File -Encoding utf8 build_trig_probe.log
"NVCC_EXIT=$LASTEXITCODE"
& cmd /v /c "call ""C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"" >nul 2>&1 && cl /nologo /O2 /EHsc trig_probe_host.cxx /Fe:trig_probe_host.exe" 2>&1 | Out-File -Encoding utf8 -Append build_trig_probe.log
"CL_EXIT=$LASTEXITCODE"
