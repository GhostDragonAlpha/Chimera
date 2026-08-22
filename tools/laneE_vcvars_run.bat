@echo off
rem Generic runner for gsplat JIT scripts under the VS2022 + CUDA 12.8 toolchain.
rem Mirrors tools/anysplat_refine.bat so any python script that imports gsplat compiles.
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
set CUDA_HOME=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8
set CUDA_PATH=%CUDA_HOME%
set TORCH_CUDA_ARCH_LIST=8.9
set DISTUTILS_USE_SDK=1
set PATH=E:\PythonChimera\.venv-gs\Scripts;%PATH%
E:\PythonChimera\.venv-gs\Scripts\python.exe %*
