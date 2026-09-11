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

## Fresh-system re-verification (window-capture-ownership-02, 2026-09-11)

Re-verified on a fresh system (Windows 10.0.26200, Python 3.14.3, slot-03,
generation 1, base `4604de40`) by `subagent-worker-02`, after inheriting this
contract additively from `origin/astra/tasks/window-capture-ownership-01`
(`00a556b3`; that lane's local tip `b8d37f1f` carries a dyad-resident fix
that was NOT ported). Preregistration committed before any run:
`docs/evidence/agent_fleet/WINDOW_CAPTURE/PREREGISTRATION.md` (commit
`c55a8383`). Evidence of the fresh run lives next to it: `RAW_TESTS_OUTPUT.txt`,
`RAW_FLEET_SUITE_OUTPUT.txt`, `RAW_MEASUREMENT_OUTPUT.txt`, `MEASUREMENT.json`,
`RESULT.md`. Acceptance stays NOT_CLAIMED.

### What the fresh run changed in the contract module

- **Fixed a real inherited bug the fresh system exposed**: `CreateCompatibleDC`
  and `CreateDIBSection` had no declared `argtypes`, so a window DC handle
  above 2^31-1 crashed with `OverflowError` instead of returning a named
  fail-closed verdict. GDI hands out such values on this system; the prior
  attempt passed only because its session got smaller handle values. Declared
  handle prototypes keep every refusal NAMED.
- **`verify_hwnd_capture(hwnd, expected_pattern, pinned_size=None, title=None)`**:
  the hwnd-level contract entry with the same fail-closed decision order and
  verdict vocabulary. `verify_owned_capture` delegates to it. Accepting any
  hwnd is what lets a REAL foreign-process fixture be refused on pid.
- **`solid_pattern(color)`**: deterministic solid fill (paint-function
  factory) so fixture cases have DISTINCT known pixel content.
- **`window_rect(hwnd)`**: outer-rect helper proving the nonclient chrome is
  strictly larger than the pinned client rect (client 120x90 vs outer
  136x129 measured) while the captured matrix is exactly the client extent.

### What the fresh run upgraded from decision-table to REAL fixtures

- **(b2) real cross-window content mismatch**: a live owned hwnd verified
  against ANOTHER owned fixture's expected pattern yields
  `occluded_or_foreign_content` - the content gate proven with real windows,
  not a synthetic tampered matrix.
- **(e2) real foreign-process fixture**: a child process of the test's own
  Python interpreter (spawned inline by the test, `ChimeraFixture` class,
  known solid red content, terminated in cleanup) is refused
  `foreign_process` on pid alone - even though its content is known,
  matching, and readable by the same window-specific capture path. No
  third-party window is touched at any point.
- **(d2)** a raw stale hwnd refused `window_destroyed` at the hwnd-level
  entry; **(a2)** distinct solid fixtures each capture exactly, with
  distinct SHA-256s.

### Engine-render capture vs screen presentation (kept explicit)

This contract certifies the content of a window's OWN surface
(engine-render capture: `PrintWindow`/`PW_CLIENTONLY` into a DIB sized to
the client rect). It does NOT certify what the desktop compositor presents
on screen, and the module constructs no screen/desktop DC at all
(AST-verified in the tests). Screen occlusion therefore cannot enter a
record - and by the same separation, a record is not evidence of on-screen
presentation. Both directions are load-bearing.

### Commands

From the REPO ROOT (never from inside `tools/agent_fleet`):

```bash
python -m unittest tools.agent_fleet.test_capture_window -v
python -m unittest discover -s tools/agent_fleet -p 'test_*.py'
```

Fresh-run results: 17/17 task tests pass; fleet suite 183 tests, 1 expected
Windows-symlink skip, 2 failures that PRE-EXIST at base `4604de40`
(`test_master_catalogue` pins 2540 catalogue lines / 76 master_row_ids; the
canonical Master list has since grown to 2584 / 82 - bit-identical inputs at
base and head, so identical outcome; catalogue files are outside this task's
scope and nothing was weakened or tolerated). Catalogue lane should re-pin.

### Continue rules (for any future run on this contract)

1. Preregister BEFORE results: statement/prediction/falsifier plus algorithm
   bounds in `docs/evidence/agent_fleet/WINDOW_CAPTURE/PREREGISTRATION.md`,
   its own commit, citing no measured actuals.
2. Use only SELF-CREATED fixture windows (own process or own child process);
   never enumerate, move, capture, or close a third-party window.
3. Never add a screen/desktop DC path; `GetDC(NULL)`, `CreateDC*`,
   `GetWindowDC`, `GetDCEx` must stay absent (AST-checked).
4. Content proof is FULL matrix equality (plus SHA-256); never weaken to
   point sampling, region sampling, or tolerance windows.
5. Evidence writes refuse overwrites; failures are retained and reported,
   never tolerated away.
6. Pin the MEASURED client size (DPI and minimum-width enforcement skew
   requested sizes on this system); do not adjust tolerances - pinning is
   the contract's answer.
7. Run from the repo root; commit trailer `Agent: <your-id>`; acceptance
   stays NOT_CLAIMED until lead review and authorized integration.
