# needles — one million needles, each on its own groove

A membrane is a SEPARATE MATRIX applied to the main Gaussian space. This one's
matrix is tiny: 1M groove specs + a switch timeline — not 1M x T recorded
frames. Positions are a closed-form law of the pass clock
(`ChimeraEngine/needle_law.py`), so replay is free: the record IS the matrix.

**In plain words —** a million needles fall from a single point, each one on its
own smooth curved rail, and pack into one shared Gaussian frame; press Q and the
deck throws a switch that reroutes a whole block onto new rails through where
they already are — a railroad join, not a teleport.

STATEMENT: 1,000,000 needles, each born on its own closed-form rail, share ONE
Gaussian frame inside the wallet; an operator key throws a switch that reroutes
a block onto a new rail through the needles' current positions — no teleport, no
lookup table.

**The deck.** KeyQ throws the next mood onto the next block (you join the
matrix), KeyR returns to the recorded seed timeline. Live throws are written
back to `switches.json` — the deck is part of the record.

**Chain.** The same code the standalone experiment used, run live:
`ChimeraEngine/million_needles.py` wrote `matrix_out/needles`; this membrane
owns a copy in its own folder and lives in the viewer's scene list like any
other term.
