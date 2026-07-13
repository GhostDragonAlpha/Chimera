# Phantom Pain Verdict: pyautogui-forbidden

## Pain Description
**ID**: phase_ef0be888042d96ff:P1 (aged 5 days)

"The pipeline's visual stage used pyautogui desktop capture again (forbidden); the prohibition may not be enforced."

## Context
**Heuristic H-2** (CLAUDE.md):
"Never verify from desktop screenshots — capture via MCP control_editor screenshot mode=editor_viewport."

Using `pyautogui` (a desktop-screenshot library) for visual verification is forbidden because it captures the desktop, not the editor viewport (which renders regardless of window focus).

---

## Investigation Method

1. **Codebase-wide search for pyautogui usage**:
   - `grep -rn "pyautogui\|ImageGrab\|screen_capture" core/ Source/ --include="*.py"`
   - Result: Only `core/ralph_loop_harness.py:35` contains `import pyautogui`

2. **Actual pyautogui method invocations**:
   - `find /e/PythonChimera/Chimera -name "*.py" -exec grep -l "pyautogui\." {} \;`
   - Result: No files found. pyautogui is imported but never called.

3. **Visual stage implementation verification**:
   - Visual stage entry: `core/visual_verifier.py:266` — `run_visual_verification()`
   - Stage 7 is orchestrated from: `core/game_generation_orchestrator.py:36` imports `run_visual_verification`
   - No pyautogui references found in orchestrator or visual_verifier.py

4. **Screenshot capture method audit**:
   - `core/visual_verifier.py:78-129` — `capture_screenshot()` function
   - `core/ralph_loop_harness.py:683-723` — `screenshot()` method
   - Both use: `client.call("control_editor", {"action": "screenshot", "mode": "editor_viewport"})` per H-2
   - Both explicitly document: "Use MCP control_editor screenshot mode=editor_viewport (H-2 prohibition: never verify from desktop screenshots)"

---

## Findings

| Finding | Evidence |
|---------|----------|
| pyautogui imported | `core/ralph_loop_harness.py:35`: `import pyautogui` (wrapped in try/except) |
| pyautogui used | **0 matches** for `pyautogui.` method calls across entire codebase |
| Visual stage capture | `core/visual_verifier.py:97-100`: MCP `control_editor` mode=`editor_viewport` (correct) |
| Ralph loop capture | `core/ralph_loop_harness.py:696-699`: MCP `control_editor` mode=`editor_viewport` (correct) |
| PIL.ImageGrab usage | **0 matches** across codebase |
| Desktop screenshot methods | **0 matches** for screenshot-grabbing (pyautogui, PIL, etc.) |

---

## Verdict

**REFUTED**

The visual stage pipeline does **NOT** use pyautogui desktop capture. Evidence:

1. **Correct capture pathway is enforced**: Both `visual_verifier.py` and `ralph_loop_harness.py` implement screenshot capture exclusively via MCP `control_editor` with `mode=editor_viewport` (lines 97-100, 696-699 respectively).

2. **pyautogui is dead code**: Imported in `ralph_loop_harness.py:35` but never invoked (0 instances of `pyautogui.` found in the codebase).

3. **No desktop capture fallback**: No PIL.ImageGrab, no desktop screenshot methods present in the active pipeline.

4. **H-2 prohibition is enforced by design**: The visual stage is designed to use only MCP control_editor editor_viewport rendering, which is windowed and unaffected by window focus—the exact requirement H-2 mandates.

---

## Disposition

**DISPOSITION**: phase_ef0be888042d96ff:P1:refuted

The phantom pain is **refuted**. The prohibition against pyautogui desktop capture is enforced by the design of the visual stage — it uses only MCP control_editor mode=editor_viewport, which renders the editor viewport regardless of window focus. pyautogui is imported but dead (never called).
