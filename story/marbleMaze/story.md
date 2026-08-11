# marbleMaze — the tilt table, a playable membrane

A membrane is a SEPARATE MATRIX applied to the main Gaussian space. This one's
matrix is the whole game: a maze (walls + goal) on a table, one marble, and the
operator's tilt timeline. The tilt inputs are recorded to `tilt.json`, and the
marble's position is INTEGRATED from that record — so the record IS the matrix:
replaying the tilt timeline reproduces the marble's exact path.

**In plain words —** one marble, steered by your arrow keys through an authored
maze of baffles on a Gaussian-splat table, into the green goal; the whole table
visibly tilts when you steer, and every tilt you make is recorded, so your run
replays exactly.

STATEMENT: one marble, steered by the operator's tilt through an authored maze
on a Gaussian-splat table, reaches the goal — and the operator's inputs are
recorded, so the run replays exactly.

**The deck.** ArrowUp/ArrowDown tilt the table along y, ArrowLeft/ArrowRight
along x, KeyR resets the marble to the start (clearing the tilt record),
Space plays/pauses. The maze is a zigzag of baffles with alternating gaps —
solvable by tilting R, L, R, L.

**Theory (RULE 0).** The full statement, prediction and falsifiers live in
`physics.py`'s header and are printed by `python story/marbleMaze/physics.py`:
a tilt moves the marble, the marble follows the tilt, the walls hold, the record
is the matrix (replay error 0.0), and the maze is winnable by tilt alone — a
scripted run reaches the goal in 45 of the 240 passes, and the win holds across
a band of damp/max-tilt/bounce/cap settings (worst case 46).
