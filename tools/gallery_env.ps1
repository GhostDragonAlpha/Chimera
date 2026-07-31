$env:CUDA_PATH = 'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8'
$env:PATH = 'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\nvvm\bin;C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin;' + $env:PATH
Stop-Process -Id 67576 -Force -ErrorAction SilentlyContinue
Start-Sleep 2
Start-Process -FilePath 'C:\Python314\python.exe' -ArgumentList 'ChimeraEngine/gallery.py 8765' -WorkingDirectory 'E:\PythonChimera' -RedirectStandardOutput 'E:\PythonChimera\ChimeraEngine\gallery_out.log' -RedirectStandardError 'E:\PythonChimera\ChimeraEngine\gallery_err.log' -WindowStyle Hidden
Start-Sleep 5
