@echo off
rem THE DOUBLE-CLICK LAUNCH (R1): one click starts the game in its own
rem working directory, console retired, window up, creature restored.
rem WC-PLAY-1: the workshop boots ARMED with the hazard scene already in it
rem (--interactive --scene), so Tab/hover/Enter and F9/F10 save/load work
rem without a terminal. The scene file is copied next to the exe by the
rem build (CMake POST_BUILD); the path resolves relative to the bat/exe dir.
cd /d "%~dp0"
start "" "chimera_engine.exe" 8107 --hidden --interactive --scene "%~dp0workshop1_scene.json"
