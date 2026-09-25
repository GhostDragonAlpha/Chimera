# Ontology inspector verification — 2026-09-24

Scope: authored composition, structural/source inspection and read-only browser
navigation. No native runtime, GPU, training, physics qualification, anatomy
supersession or material export was executed.

The live source inspection found 22 authored membranes, 8 ports and 4 planned
connection membranes. All 18 referenced source files were present. Eighteen
declared binding gaps remain visible. Presence and structural validity are not
acceptance of those source files' physical claims.

`python -B tools/membrane_ontology/test_model.py`: 19/19 passed, covering O1–O7,
including malformed containment/endpoints/exposure, matter ownership, unsafe
paths, deterministic hashing, preserved input bytes, source changes/missing
files, read-only HTTP routes and named refusal responses.

`python -B -m unittest discover -s tools/monkey_campaign -p 'test_*.py' -q`:
96 tests run, 95 passed, one platform-dependent symlink case skipped. The sealed
83-task/default-76 scope remains unchanged. This is workflow regression evidence,
not game completion or a live end-to-end GitHub merge exercise.

Browser checks against the real API passed: tree search/ancestor retention,
selection, nested contents, ports/endpoints, deep links, history and refresh
preserving selection. Missing-source and HTTP 422 UI paths were tested with
browser-only fixtures and restored afterward. No production data was mutated.
Mobile overflow was found and fixed; the refreshed mobile view has no horizontal
page overflow. Desktop and mobile screenshots were captured and inspected.

An independent design agent returned PASS after that fix. The available evaluator
was a separate session from the same provider; cross-provider review was not
available. O8 holds for the inspected tree/port/detail cases. O9's tested paths
hold, with one explicit limitation: the JSON download Blob matched all 29,364
bytes of the API response, but the browser harness canceled actual disk saves
for both Blob and ordinary same-origin controls. Disk saving through that button
is therefore unverified; the CLI snapshot export works and was exercised.

Local screenshots: `E:/Chimera/ontology-qa/ontology-desktop-creature.png`,
`ontology-desktop-connection.png`, `ontology-mobile-creature.png`. These are UI
evidence, not geometry/physics visual qualification. The task's headless browser
sessions were closed. The loopback inspector server exits after idle timeout.

Policy revision astra-0014 binds the ontology document and definition in the
existing raw-file instruction fingerprint. It starts no fleet workers and leaves
active task cards and their acceptance criteria intact.
