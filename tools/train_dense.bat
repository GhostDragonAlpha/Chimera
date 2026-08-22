@echo off
rem gsplat training with the MSVC toolchain on PATH (JIT build or cache LOAD
rem both want ninja/cl visible). Args = simple_trainer.py default args.
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
set CUDA_HOME=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8
set CUDA_PATH=%CUDA_HOME%
set TORCH_CUDA_ARCH_LIST=8.9
set DISTUTILS_USE_SDK=1
set PATH=E:\PythonChimera\.venv-gs\Scripts;%PATH%
E:\PythonChimera\.venv-gs\Scripts\python.exe E:\PythonChimera\tools\gsplat\examples\simple_trainer.py default --save_ply --disable_viewer %*
