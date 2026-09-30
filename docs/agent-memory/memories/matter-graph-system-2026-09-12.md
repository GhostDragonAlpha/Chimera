---
name: matter-graph-system-2026-09-12
description: The organic-geometric MATTER_GRAPH system (replaces graphify — all
  old graphs deleted by operator order) — builder script, growth law, 39-node
  seed structure, plus the master-prompt-as-spec-sheet directive and the
  240fps stream target
metadata:
  node_type: memory
  type: project
  originSessionId: sess_8207b32c-37a6-443b-91a8-b9f8901a74d5
---

Operator directive 2026-09-12: **"All the graphs are obsolete and should be
deleted immediately in order to create a new system that encompasses the
matter system along with the master. We're going to do this organically
geometrically."** Executed: `E:\ChimeraWork\slot-05\graphify-out\` deleted
(graphify itself is RETIRED — the earlier "use graphify" directive is
superseded); the repo copy `docs/LEDGER_GRAPH.json` is NOT silently deleted —
it is referenced by the viewer's /graph endpoint and gets replaced through
the queued viewer lane.

**The new system:** `E:\ChimeraWork\matter_graph\build_matter_graph.py` →
`MATTER_GRAPH.json` (copy on Alan's desktop CHIMERA_PROOF/). Seed: **39 nodes
/ 33 edges** — 28 `membrane.joint` nodes at their LIVE measured rig positions
(GET /joints → J pos + rotation axis + ROM + live theta per joint), the
stride clock (live state), the Vulkan render surface, the web viewer pane,
and a shell of 8 requirement R-nodes (the master, as requirements): R.one-
feature, R.visual-proof, R.trained-walk (OPEN), R.travel (OPEN), R.240fps
(OPEN), R.one-window, R.window-maximized, R.matter (the triangle-is-the-
electron law) — PROVEN vs OPEN status each.

**Growth law (written into the file):** a NODE exists only when verified by
an artifact (live pull, file, gate); an EDGE exists only when measured
(readback, capture, gate pass); GEOMETRY is real (joint nodes at measured J
positions; requirement nodes on a shell). **The graph grows organically:
rerun `build_matter_graph.py` after every accepted feature** and the universe
extends itself. Edge relations: composes (13 limb chains), drives (10, stride
clock → limbs, measured by FEATURE_WALK gates G1-G7), renders, poses,
requires (8).

**Viewer FINAL layout (2026-09-12 late, supersedes the one-pane+labels-toggle
intermediate):** TWO panes side by side — `/frame` (the world, clean) +
`/glass` (the same moment with the instrument labels) — grabbed as ONE
lockstep cycle (frame lands, glass immediately; consecutive engine states,
never two clocks). The PrintWindow engine-window mirror was REMOVED from the
page (its clock cannot be synchronized with /frame; the /api/window/stream
endpoint stays server-side). Intermediate states superseded: one world pane +
labels toggle → Alan "I no longer see the glass view" → pair restored, mirror
dropped. **Stale-server trap (cost hours):** a viewer process started BEFORE
the page edits kept serving the OLD three-pane page — on Windows,
ThreadingHTTPServer's SO_REUSEADDR lets multiple viewers bind 8206 silently;
netstat is the only truth for who listens, kill by netstat PID, and ALWAYS
verify the SERVED page (curl + structure check), never disk state. The
native engine window is parked minimized at -32000 AND STILL SERVES FRAMES
(verified: consecutive /frame pulls differ) — but the stream goes dark if it
stays minimized (Vulkan presents only when restored), so the viewer carries
a minimized-window watchdog: `mirror.window_state()` (5s cache) → /api/health
`engine_window` field → red page banner "ENGINE WINDOW MINIMIZED — restore
it". The stream fps param caps at 30 in _window_stream; Alan's target is 240
(R.240fps) — honest ladder: GDI capture ceiling ~30-60 at reduced quality/res
(P~55%), 240 needs an engine appliance (P~95%). **ROOT CAUSE of low FPS
named by Alan (2026-09-12 session close): the GPU-resident triangles law
was violated — "load all of the triangles into the GPU, sort of like a
model that's loaded for doing AI" (weights metaphor; triangles load once,
compute in place, Python posts intents and exits — never per-frame). The
22fps stutter was the per-frame Python round-trip. Any fps fix routes
through this law, not capture tuning; see the kernel statement in
[[membrane-game-product-vision]].**

**Console-error repeatability (shipped same session):** the page
self-reports — capture-phase error beacon as the FIRST script in <head>
(JS errors, resource-load failures with URL, rejections) POSTing to
/api/client_errors → log at `tools/product_viewer/.tmp/
viewer_client_errors.log`; plus `node --check` on served inline scripts
(parse errors fire before any page hook can catch them). The embedded IAB
browser exposes no console API — instrumenting pages we serve is the only
repeatable path, and it works from his Chrome too.

**FINAL VERIFIED STATE (2026-09-12 late, after stale-viewer restart):**
served page = exactly TWO panes, `/frame` + `/glass`, BOTH loaded at
2560×1369 (DOM: `loaded:true, naturalWidth>1` for both, verified by
screenshot — side-by-side walking teddy, near-identical poses = lockstep
working). Engine window minimized at -32000 and still serving live frames.
**F1 CHROME GOTCHA:** the engine's studio chrome (panels + joint labels) is
toggled remotely via `PostMessageW(hwnd, VK_F1=0x70, keydown/keyup)` — it is
a STATEFUL TOGGLE. Always capture the window first and check whether labels
are visible BEFORE sending F1: sending blind after the operator may have
already toggled is a coin flip that "ruins it" (live incident). **The pair
only differs when studio chrome is ON:** F1-hidden chrome strips the labels
off /glass too, making it a duplicate of /frame — the operator reads that
as "both windows not working." Chrome ON is the default operating state.

**Session-final viewer state + two gotchas (2026-09-12 very late):**
served page = exactly TWO panes (/frame + /glass side by side), both loaded
at 2560×1369, mirror pane deleted from the template (verified: no
`img id="w"`, exactly 2 img tags in PAGE). Gotchas: (1) the operator
experimentally switched his Windows display language to "system default" —
Chinese UI text on his screen was partly HIS OWN OS setting (fix: Settings →
Time & Language → Language → English), not only fleet output; z.ai
navigation works in English (or Chrome right-click → translate). (2) the
IAB had TWO stale tabs at 8206 — a stale tab serves the cached old page;
after any viewer restart, hard-reload (Ctrl+F5) or close duplicate tabs.

**Why:** Alan declared the code-graph era obsolete — the graph that matters
tracks the MATTER system (membranes, joints, materials) plus the master
requirements, growing with proven reality, not parsed source code.

**THE GRAPH-MIRROR ARCHITECTURE (operator directive, the system's purpose):
"Graphify could encompass the tag system — we make graphify the same user
space as the engine — put things like the left eyebrow into a space that's
identical, searchable like a tree/database, understood both in three
dimensional and verbal terms. Measurable so we maintain physics distances.
The ultimate editor for an AI — a CAD system where you measure and draw off
coordinates found in the game system. A searchable mirror of the system
itself; eventually tie it into the system as the Python controller."**

**THE STORY LAYER (same directive cluster): "The master doc will be woven
into graphify as needed — that in a way is what I call the story. You can
look it up — there's terms that describe what that is in the
documentation."** Looked up: `docs/THE_METHOD_AS_A_STORY.md` — laws told as
a story with WHY-EDGES (each law caused by the one before; a chronicle says
"then", a story says "therefore"); terms: theSeed / theShape / theHuman /
theStance / theZero / needles / marbleMaze (story/ dirs); membranes as
boundaries supplying local frame, local unit, identity, inside-outside,
depth. Executed: `matter_graph/MASTER_STORY.md` (the master doc in story
form — every 2026-09-12 directive placed at the membrane that forced it)
and a `story` field on every membrane node, generated from measured state —
e.g. mem.knee_L: "The left knee membrane: a hinged boundary of triangles at
measured position (0.48, 1.90, -0.02), rotating about its measured axis,
bending from -131.0 to 147.0 degrees. Its story is its description; its
description is its measured state." (Operator's confirmation: "the story is
essentially how you would describe each membrane — the title/description of
the membrane itself.")

**MEMBRANE ONTOLOGY REFINEMENT (operator): "Each membrane would encompass
collections of triangles and CA triangle types."** A membrane = a triangle
set + its CA-type assignments (CA-field GPU law, THE_TRIANGLE_GUIDE);
triangles are the irreducible; movement = triangle sets going through their
calculations/ranges of motion, each set an elaborate polygonal hinge
system; representation is Gaussian-splat-like (matter by reflecting light),
never mole-by-mole. The creature is the hard proof (living, angle-dependent
strength); uniform structures come after and are easier. Graphify tool
facts if the weave returns: `update` / `affected` (works with basenames) /
`query` (BFS) work; `explain` needs node basenames not paths; known gap —
engine.cpp (one giant class) does not extract member functions.

**KERNEL_SPEC.md joined the matter_graph/ canon (2026-09-12 session close):**
alongside MASTER_STORY.md, `E:\ChimeraWork\matter_graph\KERNEL_SPEC.md` (+
desktop copy) is the matter-kernel spec awaiting operator approval — four
laws, the JSON body/bond definition format, the B1–B5 test battery, and the
build order. See [[membrane-game-product-vision]] for full contents.

Related: [[membrane-game-product-vision]] (the tiers the R-shell mirrors),
[[alan-operator-preferences]] (the spec-sheet law below).
