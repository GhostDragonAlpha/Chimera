# Rule 0 record — THE REAL BODY'S MOVIE, lane realbody-movie-20260920

Lane: `lane/realbody-movie-20260920` @ `7d7868d3` (the landed mesh-parse tip;
verified `git log -1` == `7d7868d3` "RECEIPT: the parse cost measured dead,
per-falsifier verdicts banked (lane mesh-parse-20260920): ALL GREEN." before
the worktree add). Git trailer on this lane's commits: `Agent: rbmovie`.
Worktree: `E:/ChimeraWork/rbmovie-agent`. Only this lane branch is pushed.

## THE THEORY (Rule 0)

**STATEMENT** (someone could disagree): the playable slice's REAL CT-derived
macaque body — the sha-pinned 499,976-triangle payload riding the engine's own
gravity/contact/fall law — moving through the slice's own scripted sequences
(settle -> the named carry mock -> THE FALL TEST -> restart), captured live
through the REAL slice page in a private headless browser, becomes a watchable
movie in which the skeleton reads as ONE CONNECTED PHYSICAL ANIMAL moved by
physics — the day's capstone visual the dyad can judge.

**PREDICTION** (not yet measured by anyone):
- P-CAP: the capture sustains **>= 15 frames per second** through the real
  page (the encoded movie is cut at the measured mean cadence — the frames'
  true timebase — so movie duration == capture wall time).
- P-JUDGE: the blind judge, shown ordered frames from the movie with a prompt
  that names neither the body's origin nor the expected answer, names the body
  parts as moving TOGETHER — one connected creature — as it did for prior
  movie-lane watches (its prior form: it named parts and arrangement, not
  fragments). The carry segment is the discriminating one: the whole body
  translating rigidly through the slide is the physics-carried read.

**FALSIFIERS** (named before the run; any one failing = the theory loses; the
RED is recorded verbatim and reported, never tuned away):

| id | class | pass condition |
|----|-------|----------------|
| F1-NO-MOVIE | capture/encode production | the movie EXISTS: capture completes through the real page, the encode completes, the sustained capture cadence >= 15 fps (movie cut at the measured cadence); a failure or a lower cadence is RED and the bottleneck is NAMED and measured, not guessed |
| F2-PAGE-ERROR | the page's own honesty | ZERO console-class errors (`console` type=error, uncaught `pageerror`, failed page requests to its own API) during the whole capture; Chrome's own software-WebGL INFO notice (measured class, prior lane) is not a page error |
| F3-DISCONNECTED-BODY | the visual truth itself | the blind judge's verbatim read describes body parts moving together / one connected animal; if the judge reads separated or floating parts, that verdict is recorded VERBATIM — it is a FINDING about the slice's visual truth, not a rendering bug to hide or a movie to re-cut |
| F4-PROVENANCE | the frames are the page's | every frame is a raw screenshot of the live page (Playwright `page.screenshot` on the canvas viewport); no composited, edited, re-encoded-then-captured, or synthesized frame anywhere; the receipt carries frame count, measured cadence, duration, the MP4 sha256, and individual frame sha256s; the choreography drives ONLY the slice's own API endpoints (`/api/send`, `/api/stop`, `/api/drop_test`, `/api/restart`) — no desktop input injection, no engine or slice edits |

## DERIVED, NOT TUNED (Rule 1)

- The choreography is the slice's OWN: the sequences this movie runs are the
  endpoints the slice page's buttons already ship — settle (the boot's own
  background physics), `/api/send` (MOCK[mock_carry], the slide to the marker),
  `/api/drop_test` (THE FALL TEST, real engine law), `/api/restart` (the
  byte-clean re-boot). Nothing is invented; no physics or page file is edited.
- The movie's fps is the MEASURED capture cadence, not a chosen number: the
  frames' true timebase is the only honest playback speed. No fps is picked
  for smoothness; a low cadence is a measured F1 RED, not a knob.
- The judge's prompt is blind: it names neither "CT", "skeleton origin",
  "macaque", "mock", nor the expected verdict; it asks what the body is doing
  and whether it reads as one connected physical animal or separate floating
  parts. The judge lane is the established ollama lane (qwen3.8, think:false,
  num_ctx sized to the frames — senses.py's own ollama branch math).
- Frame budget ~30 s total is the slice's own sequence lengths (carry 1.2 m
  at its 0.4 m/s constant; the fall test's own transient-then-settle shape;
  a restart's cached ~2 s boot + settle), not a runtime picked for a target.

## RUN PLAN

Prereg (this file + receipt.json, committed) -> engine binary copied to THIS
worktree's `.tmp/slice_build/Release/` (built from the base tip by the landed
mesh-parse lane; this lane edits no engine code) -> boot timing measured
through the cached path (the lane's own ~2.1 s claim re-measured here) ->
private headless Playwright chrome (fresh profile, channel `chrome`, never the
shared desktop) loads the real page; HUD panels hidden by an injected capture
style (a capture-side view choice; the page files untouched); frames captured
on a steady loop with wall-clock timestamps while the slice's own sequences
run -> encode at the measured cadence (the established `encode_movie` ffmpeg
shape) -> copies (repo `CHIMERA_PROOF/REAL_BODY_SLICE/`, this validation dir
at a sane size, `C:/Users/allen/Desktop/CHIMERA_PROOF/REAL_BODY_SLICE/`) ->
dyad judge (verbatim verdict recorded) -> receipt.json per-falsifier ->
commit + push ONLY this lane branch.

Receipt: `tools/science_funnel/validation/realbody_movie_20260920/receipt.json`.

Agent: rbmovie
