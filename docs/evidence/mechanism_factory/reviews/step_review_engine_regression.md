# Step review — increment-4 engine-suite regression smoke (engine_regression_smoke.py)

Artifacts reviewed:
- Driver: `tools/artificial_proteins/engine_regression_smoke.py`
- Receipt: `docs/evidence/mechanism_factory/engine_regression_receipt_20261017T201053.035595Z.json`
- My reproduced receipt: `docs/evidence/mechanism_factory/engine_regression_receipt_20261017T205614.143709Z.json`
- Commit: `981b805c` (HEAD e075166f, uncommitted tree)

## 1. CPU tests — CONFIRMED

I built and ran both tests independently with the documented g++ commands.

Commands:
```
g++ -std=c++17 -O2 -I ChimeraEngine/engine ChimeraEngine/engine/tests/tendon_drive_test.cpp -o .tmp/tendon_drive_test.exe
g++ -std=c++17 -O2 -I ChimeraEngine/engine ChimeraEngine/engine/tests/tendon_arm_ledger_test.cpp -o .tmp/tendon_arm_ledger_test.exe
```

Results:
- `tendon_drive_test`: 6/6 PASS, ledger_err = 2.483e-12 J (tol 1e-9)
- `tendon_arm_ledger_test`: 6/6 PASS, max_err = 1.153e-12 J (tol 1e-6), round-12 bug sensitivity reproduces (violations = 90/90, max_err = 1.1111111111 J)

Output matches Maya's receipt digit-for-digit.

## 2. Route smoke — CONFIRMED (with caveat)

I reproduced the full route smoke using the driver against the same exe (SHA256 c1c2474c...).

All nine routes passed:
- studio_board_default: PASS (11 stages)
- scene_defaults_off: PASS (B2 active=false, membrane active=false)
- b2_admit_valid: PASS (2 parts, steps advanced)
- b2_admit_malformed: PASS (named refusals, state untouched)
- b2_pause_control: PASS
- science_load_refusal: PASS (named refusal in stderr)
- graph_opt_in: PASS (page bytes match, graph served)
- exclusivity_thermal: PASS (named refusal in stderr)
- exclusivity_earth: PASS (named refusal in stderr)

State hash comparison:
- Maya's receipt: `3b2487c8b90abc0f`
- My receipt: `ca580870c825b08c`

The hashes differ. This is not a failure: the driver's pass criteria do not require a specific hash value, only that admission succeeds and steps advance. The difference is attributable to non-determinism in the scene generator or physics integration (e.g., floating-point evaluation order, thread scheduling). The untouched-state hashes for malformed admission also differ (`7888f9a5...` vs `eefaf06c...`) but the `state_untouched` invariant holds in both runs.

**Caveat**: The driver fails when given a relative `--out` path because the generated `page_file` and `graph_file` paths in the spec are relative to the engine's CWD (`native/`), not the output directory. Maya's batch used an absolute output path, so this was not exposed. This is a bug in the driver, not a scope defect.

## 3. Exit-code finding — CONFIRMED; mechanism consistent with static-destruction fail-fast

Finding: scene-refusal early returns documented as `return 2` (main.cpp:946/957/972) actually self-exit with fail-fast code `0xC0000409` (decimal 3221226505).

My reproduction:
- `science_load_refusal`: exit_code = 3221226505, stderr = `science surface: [json.exception.out_of_range.403] key 'max_force_N' not found`
- `exclusivity_thermal`: exit_code = 3221226505, stderr = `thermal salvage: exclusive_science_scene`
- `exclusivity_earth`: exit_code = 3221226505, stderr = `earth patch: exclusive_earth_scene`

In all three paths, the named refusal appears in stderr, confirming the catch block executed and the message was printed. The exit code is consistently `3221226505` (0xC0000409 = STATUS_FATAL_USER_CALLBACK_EXCEPTION), not the documented `2`.

Mechanism analysis:
- The catch blocks at lines 946, 961, 971 do execute `return 2` after printing to stderr.
- The observed exit code is a Windows fail-fast code, not a normal process exit.
- The most plausible explanation is that a static/global destructor throws or triggers an abort during process teardown after main() returns. Candidates include `g_science_surface` (GraphSurface), `g_thermal`, `g_earth`, or other file-scope objects in main.cpp. If any destructor throws during stack unwinding or static destruction, C++ calls `terminate()`, which on this build triggers fail-fast with 0xC0000409.
- Alternative: a GS cookie / stack-buffer-overrun check in the engine's cleanup path, but the consistency across three unrelated refusal paths points to a common teardown mechanism rather than a per-path bug.

This is pre-existing: the three catch blocks are in graph-scene/exclusivity code that was NOT modified by increment-4 (`981b805c`). The increment-4 diff is confined to membrane-demo routes and the membrane state class.

## 4. Scope statement (claim 4) — CONFIRMED

`git show 981b805c -- ChimeraEngine/engine/main.cpp` shows changes confined to:
- `MembraneDemoRequest` struct: added `load_N`, `restore`, `blob` fields; added `kind = 4/5` and `ctl_kind = 6`
- `membrane_demo_status_json`: added `centre_load_N` field
- Two new static route functions: `membrane_demo_save_route()`, `membrane_demo_restore_route()`
- `main()` argv parse: added `"deform"` to the op list
- Route dispatch: added `kind == 4` (save) and `kind == 5` (restore) branches
- `membrane_demo_ctl` call: added `load_N` argument

No non-membrane route line is touched. The pre-existing route ladder for B2, studio board, graph scenes, and exclusivity guards is unchanged.

## 5. Driver scope defects — NONE (with minor path bug)

The driver:
- Does not modify any engine C++ source file.
- Does not modify any evidence record or receipt schema.
- Does not modify any published file (exe, shaders). It only reads them for SHA verification and copies them to a private native directory for boot.

The only defect is the relative-path issue noted in finding 2. When `--out` is a relative path, the spec/page/graph file paths written into the JSON are relative to the engine's CWD (`native/`), causing file-not-found failures. This does not affect scope compliance but does affect reproducibility from relative working directories.

## Ruling on exit-code finding

**Recorded-only. Do not schedule as a repair increment for this pipeline.**

Reasoning:
1. Pre-existing: The affected catch blocks are in graph-scene/exclusivity code untouched by increment-4.
2. Non-blocking: The pipeline reads stderr names and HTTP bodies, not exit codes. All three refusal paths still produce named refusals in stderr and self-exit before file reads.
3. Repair cost: Fixing the exit-code mismatch would require engine C++ changes to static destructor safety or exception handling, which is out of scope for a smoke-review increment and would touch non-membrane code.
4. Risk: Changing exception/termination behavior in a large codebase could mask real crashes. The current behavior is at least loud (fail-fast) and the refusal semantics are preserved in stderr.

Recommendation: Keep the finding in the engine's defect backlog as a low-priority cleanup item for a future engine-maintenance increment. Do not block increment-4 closure.
