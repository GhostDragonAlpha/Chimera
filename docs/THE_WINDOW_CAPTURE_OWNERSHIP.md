# The Window Capture Ownership Contract

**STATEMENT:** A Windows-owned client capture reports only windows it actually holds; inference without an owned handle is a silent failure.
**PREDICTION:** `capture_window.owned_client()` returns a non-empty result only when a handle is acquired and verified through Win32 `IsWindow`.
**FALSIFIER (preregistered):** A synthetic fixture with no loaded window reports `None` / empty — not a fabricated window id. If the synthetic fixture reports a non-empty result, the contract fails.
