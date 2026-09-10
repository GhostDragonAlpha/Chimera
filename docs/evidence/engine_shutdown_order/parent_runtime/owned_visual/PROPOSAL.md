# Minimal owned-backdrop visual harness proposal

Apply these helpers under the task's existing
`parent_runtime/owned_visual/` evidence scope. Use `native_visual_run.py` for
one ordinary `quiet --no-restore` follow-up. It
does not replace or rerun the already accepted pending, nested, boot, or reset
cases. It copies the already-built ordinary executable and adjacent shaders to a
new unique `.tmp/engine_runtime` directory under slot 02, then records their
hashes. Only logs, PNGs, JSON, hash manifests, and source helpers belong in the
evidence output.

The helper creates one labeled Win32/GDI window owned by the harness PID at the
existing declared `(64, 64, 1280, 720)` layout. Before starting the engine it
captures that HWND's client paint as the backdrop reference. The runner starts
the unchanged executable, identifies its visible HWND by the child PID, verifies
the loopback listener PID, positions only that verified HWND, and saves `/glass`,
the engine's own presented swapchain readback. It posts `WM_CLOSE` only after a
second ownership check. After process exit and engine-HWND destruction, it
captures only the still-owned backdrop HWND. Exact reference/post backdrop hash
equality proves which pixels the after image contains.

The image record binds both captures to runner/helper/main.cpp hashes, executable
hash, shader manifest, engine PID/HWND, and backdrop PID/HWND/class/title/paint
revision. The two images are safe observations of separately owned surfaces;
because `PrintWindow` renders the backdrop independently of desktop occlusion,
they do not prove desktop exposure. The independent process handle, HWND check,
listener identity, and ordered log markers remain the shutdown proof.

Suggested invocation after root obtains the required resource admission:

```powershell
python E:/ChimeraWork/evidence/shutdown_owned_backdrop_20260910/native_visual_run.py `
  --repo E:/ChimeraWork/slot-02 `
  --exe <existing-normal-executable> `
  --output <new-unique-evidence-run-directory> `
  --runtime-name <new-unique-runtime-name> `
  --port 8102
```

Before runtime, run the CPU-only harness tests:

```powershell
python -m unittest discover `
  -s E:/ChimeraWork/evidence/shutdown_owned_backdrop_20260910 `
  -p test_harness.py -v
```

Runtime acceptance requires `result.json` to report `passed: true`, exit code 0,
no watchdog, destroyed engine HWND, ordered markers, matching listener/engine PID,
and identical backdrop reference/post hashes. Inspect `engine_before_glass.png`
and `backdrop_after.png` through separate one-image DYAD calls. The prompts must ask
numbered, non-leading questions about visible content and uncertainty, use UTF-8,
retain served model and finish reason, and use no inference timeout. A DYAD report
that cannot recognize useful engine content in the before capture leaves the
visual gate inconclusive; it does not weaken any numeric gate.
