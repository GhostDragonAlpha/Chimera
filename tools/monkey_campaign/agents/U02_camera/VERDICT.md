# U02 ACCEPTANCE VERDICT — M-U02, 2026-09-24

Checkout: `E:/ChimeraWork/monkey-play-20260924`, branch `monkey-play-20260924`,
final verification at HEAD `8550b634` (base = game lineage `33e7a444` after the
mid-flight rebase; original discovery base `32105f18`). Verdict: **DONE — all
six acceptance items green.**

1. **Discovery note** — `discovery_note.md`: the HTTP viewer camera machinery
   (`tools/product_viewer/server.py`), the demo fixed-camera pattern
   (`product_features_walk*.py`, `membrane_demo_client.py`), the full engine
   camera contract with line-cited facts, the animal-state analysis (no
   root-motion route; rig J envelope is the anchor), the capture path
   (`/frame` G8 freshness, ring, window mirror), and the REVISION 2 section
   recording the mid-flight rebase (discovery-revision BEFORE `32105f18` /
   AFTER `33e7a444`, addendum at `8550b634`) with every citation re-verified.

2. **Frozen prereg** — `PREREGISTRATION.md`, recorded BEFORE implementation:
   camera model (ground + trunk-approach, all constants derived with cited
   laws), the frozen obstruction cases OC1-OC8, the two-layer
   never-moves-the-animal invariant, the C12-compliant latency protocol,
   tolerances, falsifiers FA-FG, stop rule. Amendments 1-5 record five
   derivation-forced corrections (pull-in segment law, phi priority, grazing-
   ray height law, surface contact point, trunk designation law) — each
   BEFORE the affected code/tests ran; no falsifier was tuned.

3. **Implementation** — `tools/monkey_campaign/product/follow_camera.py`
   (stdlib-only): contract-exact write path (one `POST /camera`, always all 8
   fields, pan frozen 0), engine eye/framing laws replicated, derived ground
   and trunk-approach framing, EMA smooth follow with the
   never-outrun-the-animal speed clamp and declared cut policy, deadbanded
   writes, avoidance order latch -> pull-in -> steepen -> height-radius scan
   -> orbit, honest `degraded` reporting. Plus `RecordingClient` (the
   command-stream invariant evidence) and the anchor providers
   (`EngineRigProvider` over the contract; `CallableAnchorProvider` for future
   root-motion sources).

4. **Tests green incl. the no-force invariant with receipts** —
   `receipts/test_run.txt`: 24/24 OK (invariant: allowlist/forbidden/pan/
   body-shaped-field checks across scenarios; OC1-OC7 obstruction cases with
   mocked cylinders; OC4 bitwise no-op; OC3b honest degradation; FF speed
   clamp and cut; FG apply echo incl. the not-vacuous case; heading follow;
   latency budgets). Measured headless latencies (50 ticks,
   `receipts/latency_run.json`): max compute 0.081 ms, max command round trip
   0.003 ms, max state->ack chain 0.062 ms (budget 50 ms), presentation with
   the mock's DECLARED deadlines 50.06 ms (budget 200 ms, the engine's own F2
   law). No-force receipts: zero allowlist violations, zero forbidden routes,
   pan 0.0 on every one of the recorded writes; engine-code receipt at
   main.cpp:4190-4204 (camera writes cannot reach `load_membrane`).

5. **C23 coverage statement** (honest boundary) — TESTED HERE, headless:
   visibility/occlusion GEOMETRY against the declared cylinder model
   (eye + look-ray, height-aware, margins), camera-collision responses, the
   no-body-force invariant (command stream + engine branch structure), the
   Python-side timing chain against a mock with declared deadlines.
   NOT tested here, declared as follow-ups: human acceptance of the view and
   feel (C23's own field — needs a live render and a human); real-engine
   frame cost and true presentation latency (U07, during actual play); the
   real clearing/trunk geometry feed (F02/F03/F07 outputs — the module takes
   an INJECTED obstacle model and does not discover obstacles); re-derivation
   of tau against P06 limits and human runs. An unmodeled obstacle can still
   occlude — the module degrades or avoids only what it is told about.

6. **Integrity** — `git status --short`: the ONLY files of this task are
   `tools/monkey_campaign/product/follow_camera.py`,
   `tools/monkey_campaign/product/follow_camera_tests.py`, and
   `tools/monkey_campaign/agents/U02_camera/**` (brief, discovery note,
   prereg, integration notes, this verdict, receipts/). Zero tracked files
   modified (`git diff --name-only | wc -l` = 0); no engine C++ edits; no GPU
   processes; no servers launched. Other untracked paths in the worktree
   belong to parallel agents (F02/F03/U03/X02) and were not touched.
   The campaign's own suite (`python -m unittest discover -s
   tools/monkey_campaign -p "test_*.py"`) passes: 23 tests OK (1 skip) —
   no collateral damage.
