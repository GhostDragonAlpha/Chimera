@echo off
rem Wrap any video_to_splat.py invocation that may trigger a gsplat CUDA JIT
rem build (first run on this machine) with the VS2022 toolchain gsplat needs.
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
set CUDA_HOME=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8
set CUDA_PATH=%CUDA_HOME%
set TORCH_CUDA_ARCH_LIST=8.9
set DISTUTILS_USE_SDK=1
E:\PythonChimera\.venv\Scripts\python.exe E:\PythonChimera\tools\video_to_splat.py %*
