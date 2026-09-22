@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
cd /d "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu"
echo == host_loop ==
cl /nologo /O2 /EHsc /I host_shim host_loop.cxx /Fe:host_loop.exe
if errorlevel 1 exit /b 1
echo == cpu_probe ==
cl /nologo /O2 /EHsc /std:c++17 /I engine_inc cpu_probe.cpp /Fe:cpu_probe.exe
exit /b %ERRORLEVEL%
