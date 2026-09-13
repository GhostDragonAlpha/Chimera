# tools/website — the public front door (R9)

What this is: the landing page for Chimera. A stranger lands here, plays the
free demo, and signs up afterwards — our page, our player list, no store gate.

How to run: `python tools/website/server.py` (serves http://127.0.0.1:8210).

Sign-ups land in `tools/website/signups.jsonl`, one JSON line each
(`{"name", "email", "at"}`), appended honestly — duplicates stay.

The PLAY THE DEMO button expects the game shell running on
http://127.0.0.1:8206 (`python tools/game_shell/server.py`).

Plain Python stdlib and vanilla JS only — no frameworks, no external fonts.
