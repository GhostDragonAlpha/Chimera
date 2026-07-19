@echo off
echo === FOUNDRY BRIDGE SERVER ===
echo Opening bridge at http://127.0.0.1:8895
cd /d E:\PythonChimera\worker_bridge
python -m uvicorn main:app --host 127.0.0.1 --port 8895
pause
