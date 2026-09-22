@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio‚2\BuildTools\VC\Auxiliary\Buildcvars64.bat" >nul 2>&1
cd /d "E:\ChimeraWorkinish-agent	ools\science_funnel	ypeb_gpu"
echo == host_loop ==
cl /nologo /O2 /EHsc /I host_shim host_loop.cxx /Fe:host_loop.exe
if errorlevel 1 exit /b 1
echo == substep_probe ==
cl /nologo /O2 /EHsc /I host_shim substep_probe.cxx /Fe:substep_probe.exe
exit /b %ERRORLEVEL%
