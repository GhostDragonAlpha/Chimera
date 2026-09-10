# The window capture ownership contract

Preregistered contract for `window-capture-ownership-01` (worker buffy-02,
slot-02, generation 1, base `0e878758`). Derived from the shutdown
verification lesson: a correct PID/HWND did not imply an unobscured desktop
region, and window borders included unrelated background.

## Preregistration

**STATEMENT.** Capture output intended for public engine evidence contains
only verified owned client pixels. *Ownership* means the window is
self-created by the capturing process (pid equality), its class carries the
`ChimeraFixture` prefix, it is a live visible top-level window. *Content*
means the captured client-area pixel matrix is FULLY equal to a deterministic
computed pattern. Any ownership, size, visibility, or content deviation fails
closed with a named verdict before publication; the module contains no
desktop/screen-DC construction at all.

**PREDICTION.** (a) an unobscured owned fixture yields `unobscured` with the
capture hash exactly equal to the expected-pattern hash; (b) see the
amendment below - the window-specific path is not contaminated by screen
occlusion; (c) moving the real client area away from the pinned size yields
`window_resized`; (d) a destroyed window yields `window_destroyed` and the
stale handle is refused (`stale_or_invalid_handle`), never fallen back;
(e) a non-owned pid on the decision path yields `foreign_process`; (f) a
foreign class on the decision path yields `foreign_window_class`;
(g) the module source contains no `CreateDC`, no `GetDC(NULL)`, no
`GetWindowDC`/`GetDCEx` (AST-verified) and uses the window-specific
`PrintWindow` path.

**FALSIFIER.** Foreign, occluded, stale, resized, or destroyed pixels
classified as publishable; a full-desktop capture by fallback; evidence
overwritten; unknown/foreign windows moved or closed; or point sampling
substituted for full-matrix proof.

**AMENDMENT (recorded at controller rev 384, before submission).**
Prediction (b) as originally stated ("overlap by a second owned fixture
yields `occluded_or_foreign_content`") described a SCREEN-REGION capture and
is falsified for the implemented path: `PrintWindow`/`PW_CLIENTONLY` reads
the window's OWN surface, so desktop occlusion cannot enter the record -
validated by fixture test (overlap present, capture bytes still exactly
equal to the expected full matrix). This is exactly the separation of
engine-render capture from screen presentation the packet asked to
establish. The `occluded_or_foreign_content` verdict remains reachable
through CONTENT deviation (captured matrix != expected matrix), which is the
generalized form of the original shutdown counterexample.

## Interface

```python
from capture_window import FixtureWindow, verify_owned_capture, write_evidence

with FixtureWindow('chimera-fixture') as win:      # self-created window
    record = verify_owned_capture(win)             # fail-closed verdicts
    if record['publishable']:                      # only verdict 'unobscured'
        write_evidence(path, record)               # refuses to overwrite
```

Verdict vocabulary: `unobscured` (only publishable verdict),
`window_destroyed`, `foreign_process`, `foreign_window_class`,
`window_not_visible`, `window_resized`, `occluded_or_foreign_content`,
`stale_or_invalid_handle`, `capture_refused:<reason>`.

Capture path: `PrintWindow` with `PW_CLIENTONLY` into a DIB section sized to
the client rect; rows are compared as complete RGB matrices against the
deterministic coordinate-derived pattern (no time, no OS state). Client size
is pinned at creation (measured after DPI-aware adjustment) and any later
deviation is `window_resized`.

## Scope and limits

CPU/GDI only. No model loads, no GPU/DYAD reservation, no engine comparison,
no third-party window manipulation: foreign windows are only ever inspected
through the decision table in tests, never enumerated, moved, captured, or
closed. Evidence writes refuse to overwrite existing paths. The contract
certifies owned-window pixel correspondence; it does not claim GPU
submission linkage - that remains separately admitted work.
