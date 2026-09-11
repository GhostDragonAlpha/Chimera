# F4 documented finding: the fixture watchdog is FAIL-OPEN on a malformed spawner pid

- Source: PR #62 review finding F4 (INFO), recorded in the
  fleet-followups-batch-02 packet (2026-09-11).
- Status: DOCUMENTED ONLY in this task. `tools/agent_fleet/capture_window.py`
  is NOT in this task's write scopes, so no code edit was made; the exact
  patch and the regression test sketch below are delivered for the lead's
  disposition (a followup scoped to capture_window.py +
  test_capture_window.py can land this in minutes).
- File referenced: `tools/agent_fleet/capture_window.py`,
  `install_parent_watchdog` (the fixture-child orphan watchdog,
  fleet-evidence-hygiene-01 F2). Lines quoted from base `4c319997`:
  identical in the slot-09 worktree at the prereg head.

## The fail-open edge

```python
    if parent_pid is None:
        raw = os.environ.get(WATCHDOG_ENV_VAR, '')
        try:
            parent_pid = int(raw) if raw else os.getppid()
        except (TypeError, ValueError):
            parent_pid = 0              # <-- FAIL-OPEN
    parent_pid = int(parent_pid or 0)
    if parent_pid <= 0:
        return None                     # <-- guard silently DISABLED
```

`WATCHDOG_ENV_VAR` (`CHIMERA_FIXTURE_PARENT_PID`) is set by the SPAWNER to
point the child's watchdog at the parent. If that env value is malformed
(non-integer, corrupted, truncated), `int(raw)` raises ValueError, the
handler sets `parent_pid = 0`, and the function returns None: the orphan
guard is silently DISABLED exactly in the scenario where the spawner-side
contract is already broken. Every other failure in this function is
fail-closed toward hygiene ("cannot observe the parent -> exit"; "cannot
open -> orphaned") - this is the one input that turns the whole guard OFF.
The module docstring's own principle ("Fail-closed toward hygiene") is
violated by this path.

## The exact fail-closed fix

Malformed env -> watchdog ACTIVE with `os.getppid()` (the REAL parent), so
a corrupt spawner pid degrades to the DEFAULT correct target instead of
degrading to "no guard":

```python
    if parent_pid is None:
        raw = os.environ.get(WATCHDOG_ENV_VAR, '')
        try:
            parent_pid = int(raw)
        except (TypeError, ValueError):
            # fail-closed (PR #62 review F4): a malformed spawner pid must
            # never disable the guard; watch the real parent instead.
            parent_pid = os.getppid()
    parent_pid = int(parent_pid or 0)
    if parent_pid <= 0:
        return None
```

Behavior change is confined to NON-EMPTY malformed values:

- empty/unset env: `int('')` now falls into the except -> `os.getppid()`,
  which is exactly the old `int(raw) if raw else os.getppid()` behavior for
  empty -- UNCHANGED.
- well-formed env: `int(raw)` succeeds -- UNCHANGED.
- non-integer env: OLD = watchdog disabled (None, fail-open); NEW = watchdog
  active on the real parent (fail-closed). This is the fix.
- explicit `parent_pid=0` argument (the tested opt-out,
  `test_watchdog_disabled_without_resolvable_parent`): still returns None --
  UNCHANGED, because the fix only touches the `parent_pid is None` branch.

The docstring line "Disabled (returns None) when no parent pid resolves"
should be amended to "when the caller passes no resolvable parent_pid"
(env now falls back to os.getppid(), never disables).

## Regression test sketch (for test_capture_window.py)

Add to `FixtureChildWatchdogTests` (Windows-only class; keep the
`skipUnless(IS_WINDOWS, ...)` boundary by asserting the platform-natural
result):

```python
    def test_watchdog_fails_closed_on_malformed_env_pid(self):
        # PR #62 review F4: a malformed CHIMERA_FIXTURE_PARENT_PID must NOT
        # disable the orphan guard (the old fail-open returned None); the
        # watchdog stays ACTIVE, pointed at the real parent (os.getppid()).
        old = os.environ.pop(WATCHDOG_ENV_VAR, None)
        os.environ[WATCHDOG_ENV_VAR] = 'not-a-pid'
        try:
            thread = install_parent_watchdog()
            if not IS_WINDOWS:
                self.assertIsNone(thread)   # non-Windows contract unchanged
                return
            self.assertIsNotNone(thread,    # <-- fails on the OLD code
                'malformed env pid disabled the orphan watchdog')
            self.assertTrue(thread.daemon)
            # Watching THIS (live) process: the guard must observe a live
            # parent and keep polling, not fire.
            self.assertTrue(thread.is_alive())
            time.sleep(max(2.0, 6 * DEFAULT_WATCHDOG_CADENCE_S))
            self.assertTrue(thread.is_alive(),
                'watchdog fired on a live parent')
        finally:
            os.environ.pop(WATCHDOG_ENV_VAR, None)
            if old is not None:
                os.environ[WATCHDOG_ENV_VAR] = old
```

The new assertion `assertIsNotNone(thread, ...)` is the regression tripwire:
on the current fail-open code the call returns None and the test fails; on
the fixed code the thread exists and is alive. No new process is spawned
(the watchdog watches the test process itself, which stays alive), so the
test is as cheap as the existing `test_watchdog_disabled_without_resolvable_parent`.

## Disposition note for the lead

The fix is two lines plus a comment inside `install_parent_watchdog`, plus
the test above; both target files are outside this task's recorded scopes.
Landing it here would have violated the scope falsifier ("a followup fixed
outside its scope" / out-of-scope edit), so it is delivered as this finding
per the packet instruction. Recommended followup task:
`watchdog-fail-closed-01` scoped to
`tools/agent_fleet/capture_window.py` + `tools/agent_fleet/test_capture_window.py`.
