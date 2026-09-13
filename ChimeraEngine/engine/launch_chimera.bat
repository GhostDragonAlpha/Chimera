@echo off
rem THE DOUBLE-CLICK LAUNCH (R1): one click starts the game in its own
rem working directory, console retired, window up, creature restored.
cd /d "%~dp0"
start "" "chimera_engine.exe" 8107 --hidden
