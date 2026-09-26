@echo off
rem build_tie_probe.cmd -- CPU-side compile of the TIE2 boundary harness.
rem Reads the FROZEN sources under E:\ChimeraWork\finish-agent (== a62b286e);
rem writes ONLY into this run dir. Trailer: Agent: GLM 5.3
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
cl /nologo /O2 /EHsc /I "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu\host_shim" /I "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu" "%~dp0tie_boundary_probe.cxx" /Fe:"%~dp0tie_boundary_probe.exe" /Fo:"%~dp0tie_boundary_probe.obj"
echo CL_EXIT=%ERRORLEVEL%
