# Private design validation

No engine, GPU, model, or window was launched. No production or slot-02 file was
changed.

Final CPU-only command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s E:/ChimeraWork/evidence/shutdown_owned_backdrop_20260910 -p test_harness.py -v
```

Result: 7 tests ran in 0.025 seconds; all passed. The tests cover inherited
layout/watchdog constants, complete marker ordering, image identity binding,
foreign-HWND close refusal, absence of desktop capture APIs, absence of build or
DYAD side effects, and Rule-0 preregistration structure. AST parsing and the
runner's `--help` path also passed without creating a window.

An earlier structural run had one failed test because the test searched for a
quoted literal `/glass` while the runner constructs the URL with an f-string.
The assertion was corrected to test the intended property; no runtime behavior
was changed in response to that failure.

Candidate hashes before this validation record was added:

```text
d89fee8fd6ab160360f5fefbe716ce2e3fcf629d23b6d20ac1ba0a9da90a01b9  native_visual_run.py
22828017da247edbada56c4e0ccf593a5de0841e723b8821e8783bcdd692a5f6  owned_backdrop.py
4b43bc6290282de545abd16ace97a2201388b165a89ed511cda7c69865a67b1e  PREREGISTRATION_CORRECTION.md
427e6386007e497c446520bbea6d07fae0365b1d8544c71bf67e579e2f913846  PROPOSAL.md
d272e555c53534403f7201c598a3603d32eec3be4a232fad066f83155ec5e9c2  test_harness.py
```

Runtime and DYAD execution remain for the root under resource admission.
