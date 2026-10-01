@echo off
REM ============================================================
REM start_all.bat -- ONE double-click brings up the PUBLIC stack.
REM
REM What it starts (the watchdog is BOTH the starter and the keeper):
REM   engine       127.0.0.1:8107   the exe spawned DIRECTLY
REM                                 (.tmp\build_tick\Release\chimera_engine.exe,
REM                                 needs shaders/ next to it -- both live there)
REM   game shell   0.0.0.0:8206     public: the free demo
REM   website      0.0.0.0:8210     public: the front door + sign-ups
REM
REM The 0.0.0.0 bindings live in tools\deploy\pieces_public.json --
REM the watchdog reads that config, so any piece it has to RESTART
REM comes back public too, not just the ones it started first.
REM
REM THE ENGINE HAS NO AUTH. It is deliberately bound to 127.0.0.1 and
REM must NEVER be routed, forwarded, or port-opened. The game shell on
REM 8206 is the world's only door to it. See docs\DEPLOY_RUNBOOK.md
REM for the three ways to put 8206 + 8210 on the internet.
REM
REM Keep this window open: it IS the watchdog. It health-checks all
REM three pieces every 5 seconds and restarts any dead one. Ctrl+C
REM stops cleanly and terminates the pieces THIS watchdog started --
REM including the engine now that it is spawned directly (a Ctrl+C is
REM a hard stop for the engine; the world keeps its last saved state).
REM
REM NOTE: if a dev (127.0.0.1) stack is already running on 8206/8210,
REM the watchdog will see those ports healthy and leave them alone.
REM Close the dev stack first (or reboot) so the public bindings win.
REM ============================================================
title Chimera Public Stack (watchdog)
cd /d "%~dp0..\.."
echo Starting the public stack -- engine, game shell, website...
echo The watchdog log also lands in tools\supervisor\watchdog.log
python "tools\supervisor\watchdog.py" --config "tools\deploy\pieces_public.json"
pause
