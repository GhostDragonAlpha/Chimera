@echo off
REM bionic.cmd ^<session-id^> "<task pointer>"  — launch a visible bionic
REM (pi + LM Studio) agent session in its own console window.
REM
REM Kimi launches it with:  cmd /c start "SPIACE bionic - <tag>" E:\PythonChimera\bionic.cmd <id> "<task pointer>"
REM The operator watches/steers the TUI; Kimi tails the session transcript at
REM   C:\Users\allen\.pi\agent\sessions\--E--PythonChimera--\<timestamp>_<session-id>.jsonl
REM and keeps process control (taskkill). See AGENT_PROTOCOL.md DELEGATION.
cd /d E:\PythonChimera
pi --session-id %~1 --provider lmstudio --model bartowski/qwen3.8-27b --tools read,bash,edit,write --append-system-prompt ChimeraEngine/AGENT_PROTOCOL.md "%~2 Work from E:/PythonChimera (all task paths are relative to it). The appended AGENT_PROTOCOL.md is binding - follow THE STANDING RULES and the task's DONE MEANS exactly. Do the work yourself with your tools. Do NOT git commit. When DONE MEANS is fully satisfied, your last message is the final report."
