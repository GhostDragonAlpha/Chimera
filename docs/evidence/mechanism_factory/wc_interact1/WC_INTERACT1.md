# WC-INTERACT-1 — the workshop answers to the mouse: click-select, ghost preview, commit/cancel/remove

**Date:** 2026-10-19
**Change:** engine construction mode, 422 insertions / 1 deletion across six
clean engine files (`engine.cpp`, `main.cpp`, `b2_scene.{cpp,hpp}`,
`membrane_tick.{cpp,hpp}`). `ui.cpp` untouched (pre-existing dirt; mtime
2026-10-12 confirms).
**Runtime:** rebuilt B-suite engine `.tmp/body-engine/Release/chimera_engine.exe`,
sha256 `9cb45190428c4043a374aca9e83b4ca6dae8554a1056240be1ada6ba56e68cbb`
(baseline before edits: `fee97b375d390e070b8a8ab0e7a30a681fc35c178f4342d1fa4160e4a886e5a4`).
**Smoke:** `wc_interact_smoke.py` + `results.json` + 4 PNGs (this directory).
**Gate:** `docs/GAME_PLAN_ACTION_RPG.md` §5.1 "Close the gaps between a
walkthrough and player-directed construction" (lines 560-592), row 1.

## Player benefit

For the first time the workshop can be played **from the window itself**:
click a part and it turns white (selected); press Tab to cycle the kit
(pier → pillar → deck → crate) and a cyan ghost box appears at the last pick
point showing what will be placed; Enter commits through the real
transaction (the placed part keeps its palette color and becomes selected);
Esc cancels everything; X removes the selection. No terminal, no typed
coordinates — the §5.1 requirement that the scene be "operable without
terminal commands or an LLM advancing it" now has its input half.

## What was built (phase 1 scope, accepted design)

- **Opt-in switch:** `POST /tick_b2_interactive {"on":true}` (or
  `--interactive` at boot). **Default OFF** — with it off every input path
  (orbit, pan, console, HTTP) behaves exactly as shipped; disabling resets
  mode/selection/anchor (deterministic off).
- **Click/drag split** in `engine.cpp` WndProc: press records the point, the
  orbit move branch accumulates travel, and `WM_LBUTTONUP` fires a pick only
  under the same 4 px law as the right-click context menu — a drag orbits, a
  click selects. Panel clicks are still consumed upstream (Blender law).
- **Pick** reuses `Engine::camera_ray` + `B2Scene::pick` — the exact call
  pattern of `/tick_b2_pick`, so render/pick/contact agreement (B3) holds by
  construction. A ray miss keeps the last selection.
- **Keys** (edge-triggered, gated behind the console-captures-keyboard law —
  a typed console command can never place a part): Tab cycle mode, Enter
  commit, Esc cancel, X remove. Results and refusals land in the engine log
  (console scrollback).
- **Transactions unchanged:** commit calls the same `B2Scene::place` the HTTP
  route runs (same validation, same refusal text, same state hash); remove
  calls `b2_.remove_part`. Selection/anchor/mode are INPUT state, never
  scene state.
- **Visual language:** selected part renders white (outside the admission
  palette), the place preview renders cyan (outside palette and highlight) —
  preview, committed part and mere contact are distinguishable by color
  alone, per the plan's "Make attaching feel dependable" principle. The
  highlight member is never serialized (save doc / state hash never see it).

## Evidence

- **Baseline before any edit:** unmodified source rebuilt, full construction
  regression `python -m pytest tools/construction_packet/ -q` → **88 passed**
  (exe `fee97b37…`). The change was not built on a broken base.
- **After the edit:** same suite green (lead re-ran independently; see
  INDEX entry for the recorded output).
- **Smoke with REAL Win32 input** (`PostMessageW` mouse/key events to the
  window — no HTTP for the interactions themselves; HTTP only arms the mode
  and reads state): **15/15 asserts**, including the negative probes —
  Esc leaves the part count unchanged, disabling resets state, and a click
  with mode OFF changes nothing. Sequence: admit 2-part scene → arm → click
  selects `block_a` (renders white, `1-selected-highlight.png`) → Tab →
  `place_1` → click `block_b` sets the anchor (cyan ghost,
  `2-ghost-preview.png`) → Enter → parts 2→3, `pier_0` exists and is
  selected (`3-placed.png`) → Esc → mode off, count unchanged → re-select →
  X → parts 3→2 (`4-removed.png`).
- **Lead review (author-independent, focused):** full 422-line diff read;
  confirmed every new input path is gated on `b2i_enabled()`; lock discipline
  (b2i/b2 mutexes never nested in reverse order — no deadlock path);
  commit/remove route through the unchanged transactions; highlight is
  display-only; the ghost rides the existing overlay upload with the
  proven-outward BOX_FACES winding (a naive winding was measured to render
  as culled slivers — fixed, and the constraint is commented).

## Known limits (phase-1, stated not hidden)

- Ghost is opaque (overlay format has no alpha) and stays overlapping the
  new part after commit until mode off / next click.
- Anchor updates on click, not hover (hover-follow is phase 2).
- No weld/attach binding yet — attachments still go through the console or
  HTTP (phase 2: the plan's "attachment" verb + rotation preview).
- No on-screen mode readout (the Studio status bar would need ui.cpp —
  pre-existing dirt — so it is a lead decision, not silently done).
- Human playability unobserved: the smoke proves the input path works, not
  that it feels good. Fresh human observation remains the §5.1 "Deliver and
  observe" step.

## Process

Maya implemented under the revised brief (implement + smoke, no capture, no
commit) in one dispatch (~2.1 h): baseline-first discipline, two real bugs
found and fixed during verification (ghost winding culled; highlight not
following commit), regression green at baseline and after. The lead read the
full diff, re-ran the regression independently, and verified the smoke
artifacts before publishing.
