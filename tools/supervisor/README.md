Chimera stack supervisor: the game never stays dead.
Run it:  python tools/supervisor/watchdog.py  (every 5s, forever; Ctrl+C stops cleanly)
Watches three pieces: engine (chimera_engine.exe 8107 --hidden spawned DIRECTLY from
.tmp/build_tick/Release -- needs shaders/ next to the exe; NOT launch_chimera.bat, whose
`start ""` detaches the engine so shutdown could never stop it),
game shell (tools/game_shell/server.py 8206, /api/health ok:true), website
(tools/website/server.py 8210, GET / -> 200). Any dead piece is restarted through the
same starters as tools/supervisor/start_chimera.py, which brings the whole stack up
once ("stack already up" and exit 0 if all three are already healthy -- no duplicates).
One line per event (timestamp, piece, action) goes to stdout AND tools/supervisor/watchdog.log.
On shutdown it terminates only children it spawned itself; a stack it found running is left alone.
--config pieces.json points both scripts at alternate ports for throwaway tests.
