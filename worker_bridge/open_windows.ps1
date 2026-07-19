Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd E:\PythonChimera\worker_bridge; python -m uvicorn main:app --host 127.0.0.1 --port 8895"
Start-Sleep 3
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd E:\PythonChimera\worker_bridge; while(1){cls; Write-Host (Get-Date -Format HH:mm:ss) -ForegroundColor Yellow; ls chronicle\*.txt -ea 0 | %{Write-Host ($_.Name + ' (' + $_.Length + ' bytes)') -ForegroundColor Cyan}; Start-Sleep 5}"
