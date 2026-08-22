@echo off
rem Run tools/anysplat_refine.py under the VS2022 toolchain so gsplat's CUDA JIT
rem check finds cl/ninja (mirrors train_capture.bat). Args are passed through.
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
set CUDA_HOME=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8
set CUDA_PATH=%CUDA_HOME%
set TORCH_CUDA_ARCH_LIST=8.9
set DISTUTILS_USE_SDK=1
set PATH=E:\PythonChimera\.venv-gs\Scripts;%PATH%
E:\PythonChimera\.venv-gs\Scripts\python.exe E:\PythonChimera\tools\anysplat_refine.py %*
