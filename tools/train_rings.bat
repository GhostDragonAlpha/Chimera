@echo off
rem Train a sv3d_to_colmap dataset with the in-repo gsplat simple_trainer.
rem vcvars64: torch's extension loader probes `cl` even for cached JIT builds.
rem Usage: tools\train_rings.bat <abs data_dir> <abs result_dir> [max_steps] [extra simple_trainer args...]
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
set CUDA_HOME=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8
set CUDA_PATH=%CUDA_HOME%
set TORCH_CUDA_ARCH_LIST=8.9
set DISTUTILS_USE_SDK=1
set PATH=E:\PythonChimera\.venv-gs\Scripts;%PATH%
cd /d E:\PythonChimera\tools\gsplat\examples
if "%TRAIN_SUBCMD%"=="" set TRAIN_SUBCMD=default
E:\PythonChimera\.venv-gs\Scripts\python.exe simple_trainer.py %TRAIN_SUBCMD% --data_dir %1 --result_dir %2 --max_steps %3 --disable_viewer --data_factor 1 --no-normalize-world-space --save_ply %4 %5 %6 %7 %8 %9
