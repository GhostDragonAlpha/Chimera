@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
cd /d "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu"
cl /nologo /O2 /EHsc /I host_shim host_loop.cxx /Fe:host_loop.exe
exit /b %ERRORLEVEL%
