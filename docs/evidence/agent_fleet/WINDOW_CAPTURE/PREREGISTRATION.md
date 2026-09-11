# PREREGISTRATION — window-capture-ownership-02 (fresh-system re-verification)

Recorded BEFORE any new run or measurement of this task. Task: `window-capture-ownership-02`,
worker `subagent-worker-02`, slot-03, generation 1, base `4604de40bd6cdd02d3cc277019f8bac5030c2dbe`,
branch `astra/tasks/window-capture-ownership-02`. This run inherits the preserved contract of
`window-capture-ownership-01` (branch `origin/astra/tasks/window-capture-ownership-01`, head
`00a556b3`, merged additively; commit `b8d37f1f` on that lane's local tip is explicitly NOT
ported — it belongs to the dyad-resident-identity-01 lane). This document states what will be
tested on THIS system and what result would falsify the claim. It cites no measured actual of
this run.

## STATEMENT

Capture output intended for public engine evidence contains only verified owned client
pixels; occlusion or stale ownership fails closed before publication. Ownership = the window
was created by the capturing process's own code (pid equality), its window class carries the
`ChimeraFixture` prefix, and it is a live, visible window. Content = the captured client-area
pixel matrix is FULLY equal (complete matrix equality, not point sampling) to a deterministic
computed pattern with distinct known pixel content.

## PREDICTION (fresh-system, this machine, this run)

Deterministic, self-created Win32 fixture windows with distinct known pixel content exercise
the following cases:

- **(a) unobscured** — an owned fixture at its pinned client size yields verdict
  `unobscured`, `publishable=True`, and the captured full pixel matrix (and its SHA-256)
  is exactly equal to the expected deterministic pattern.
- **(b) overlapped** — a second owned fixture overlaps the first (Z-order changed with
  `SetWindowPos`, no move/resize). The window-specific capture path (`PrintWindow` with
  `PW_CLIENTONLY` into a DIB sized to the client rect) reads the window's OWN surface, so
  the capture remains exactly the expected matrix — the inherited contract's recorded
  amendment of the original screen-region prediction. Any content deviation still fails
  closed as `occluded_or_foreign_content` with `publishable=False`.
- **(b2) real cross-window content mismatch** — verifying one live owned fixture's hwnd
  against ANOTHER owned fixture's expected pattern (different known content, same class and
  pid) yields `occluded_or_foreign_content`, `publishable=False`. This exercises the
  content gate with real windows (the prior attempt reached this verdict only through a
  synthetic tampered matrix).
- **(c) resized** — moving the real client area away from the size pinned at creation
  yields `window_resized`, `publishable=False`, with both sizes named in the record.
- **(d) destroyed / stale handle** — destroying the fixture yields `window_destroyed`;
  any capture attempt through the stale hwnd is refused `stale_or_invalid_handle` — never
  a fallback capture.
- **(e) owner mismatch (REAL foreign-process fixture)** — a fixture window created by a
  CHILD PROCESS of this test's own Python interpreter (spawned inline by the test, class
  `ChimeraFixture*`, distinct known content, terminated in cleanup) is checked at hwnd
  level: verdict `foreign_process`, `publishable=False`, no evidence written. The packet's
  prohibition is on THIRD-PARTY windows; this child is my own code and my own process tree.
  The pid gate must refuse publication even when the window's content is known and its
  class prefix matches — fail-closed on ownership, not only on content deviation.
- **(f) client rect excludes nonclient** — the captured matrix dimensions equal the
  MEASURED `GetClientRect` dimensions pinned at creation; on this system's DWM chrome the
  outer `GetWindowRect` bounds are strictly larger than the client bounds, and no shadow,
  rounded-corner or caption pixel can enter a record (capture is sized to the client rect
  and uses `PW_CLIENTONLY`).
- **(g) no desktop/screen fallback; evidence never overwritten** — AST scan of the module:
  no `CreateDCW`/`CreateDCA`/`GetWindowDC`/`GetDCEx` call, no `GetDC(NULL)` (the desktop
  DC), `PrintWindow` present. `write_evidence` refuses to overwrite an existing path
  (`FileExistsError`), leaving the original bytes intact.

## FALSIFIER (named before the run)

This run is FALSIFIED if any of the following is observed on this system:

1. Foreign fixture pixels (child-process window, or another fixture's pattern) classified
   as publishable / verdict `unobscured`.
2. A stale HWND or a non-owned PID accepted as publishable.
3. A full-desktop or screen-region capture produced by any fallback path (any screen DC
   construction, `GetDC(NULL)`).
4. Evidence bytes overwritten (an existing evidence path silently replaced).
5. Any window not created by this run's own process tree moved, resized or closed.
6. Point sampling substituted for full-matrix equality as the content proof.

## ALGORITHM CHOICES AND BOUNDS (fixed before the run)

- Capture path: `PrintWindow(hwnd, mem_dc, PW_CLIENTONLY)` into a `CreateDIBSection`
  32-bpp top-down DIB sized to the pinned client rect. No `GetDC(NULL)`, no
  `CreateDC*`, no `GetWindowDC`/`GetDCEx` anywhere in the module.
- Content proof: complete RGB matrix equality (`rows == expected`), plus SHA-256 over the
  full matrix recorded in the evidence. Point sampling is NOT a completeness proof and is
  not used.
- Ownership checks, in fail-closed order: `IsWindow` → pid equality → class prefix
  `ChimeraFixture` → `WS_VISIBLE` → pinned client size → capture → content equality. Any
  failure stops before publication with a named verdict.
- Fixture content: deterministic functions of geometry only (no time, no OS state), with
  distinct known pixel content per case (solid color fills per region; the coordinate
  pattern of the inherited contract remains the default).
- Child-process fixture bounds: `subprocess.Popen([sys.executable, '-c', inline_code])`,
  a unique `ChimeraFixture*` class name, small pinned client size, terminated with
  `terminate()` + `wait()` in cleanup; parent identifies it by the hwnd the child prints
  to stdout (no window enumeration of the desktop).
- Environment: CPU/GDI only. No GPU work, no model loads, no engine build writes, no
  third-party window manipulation, no operator desktop screenshots in public tests.
- Tests run from the repo root: `python -m unittest tools.agent_fleet.test_capture_window -v`,
  then the full fleet suite `python -m unittest discover -s tools/agent_fleet -p 'test_*.py'`.
  Expected baseline: 0 failures, 1 Windows-symlink skip. Nothing is weakened to go green;
  a failure is retained and reported, not tolerated away.

## SCOPE AND ACCEPTANCE

Write scope: `tools/agent_fleet/capture_window.py`, `tools/agent_fleet/test_capture_window.py`,
`docs/THE_WINDOW_CAPTURE_OWNERSHIP.md`, `docs/evidence/agent_fleet/WINDOW_CAPTURE`.
Acceptance remains **NOT_CLAIMED** by this worker: lead review and authorized integration
are separate gates. The distinction between engine-render capture (this contract: a
window's own surface content) and screen presentation (what the desktop compositor shows)
is kept explicit in the contract doc and RESULT.
