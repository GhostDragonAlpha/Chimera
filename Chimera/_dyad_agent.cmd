@echo off
cd /d E:\PythonChimera\Chimera
echo [DYAD AGENT] Waiting for messages...
:loop
C:\Users\allen\node-portable\node-v22.23.1-win-x64\pi.CMD --provider lmstudio --model unsloth/qwen3.6-35b-a3b --no-session -p "Read docs/CHANNEL.md. If there's a message from LEAD, respond with your guidance and write it to docs/CHANNEL.md starting with 'DYAD:'. If no message, write 'DYAD: listening'."
timeout /t 10 /nobreak >nul
goto loop
