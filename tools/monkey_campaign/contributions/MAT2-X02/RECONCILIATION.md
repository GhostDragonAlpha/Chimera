# RECONCILIATION — MAT2-X02 (reconcile-first, written before any new implementation)

Card: MAT2-X02 — "Implement start, pause and session restart flow — Player reaches
play and can pause/restart/exit without developer commands; reset is an explicit
user action." criteria_sha256 e50bf1e89689aac419c95c1b3a8ce02bb0f5ca5b3c67cf50b575662c0bd63c20.
verification_profile id=recovery, **kind=motion** (profile demands motion-class
evidence; archived ONT-X02 precedent refused a motion-kind candidate that carried
only records evidence). checkpoint V08 is the downstream integration checkpoint
("Recover and persist the playable state"); per the card packet, integration
checkpoints are downstream milestones, never prerequisites for their constituent
tasks. Dependency MAT2-P01 is DONE (PR #192, merge 97993cbe): it froze the
completion CONTRACT only (records-kind card, "it does not implement it").

## Done_when clause -> current evidence map

| # | Clause | Current best evidence | State |
|---|--------|----------------------|-------|
| 1 | Player reaches play | Archived ONT-X02 integrated run (PR #161): page loads, real engine ticks, status live | satisfied at archived revision; re-proved here at this attempt's pins |
| 2 | start without developer commands | SessionFlow key-only `Return` (module, f30f2224 sha 30e06c04); **the shipped app has no start control and no flow at all** | UNMET in the app — implemented here |
| 3 | pause without developer commands | SessionFlow `Escape` quiesce (module-level); **archived finding M1: slice_server imports neither session_flow nor input_mapper; no /api/pause or /api/exit route; index.html binds no Escape/Q handler** | UNMET in the app — implemented here |
| 4 | restart without developer commands | App's own `[R]` -> POST /api/restart (archived A3 PASS: boot_count 1->2, byte-equal scene/state) | satisfied (legacy app path) |
| 5 | exit without developer commands | Archived M2: **no exit control or signal path exists in the app**; only a hard kill was measurable | UNMET in the app — implemented here (flow `Q` -> World.shutdown_engine) |
| 6 | reset is an explicit user action | Flow law: `R` transitions ONLY (paused)->playing; R-while-playing is a named no-op (module-level); the app has no flow to enforce it | UNMET in the app — implemented here |

First unmet clause: **the app-level session wiring (archived M1/M5-gaps above)** —
the exact piece the archived card honestly recorded as unresolved. The module
(SessionFlow) and the World lifecycle seam are existing verified work; they are
REUSED byte-exact, never redeclared.

## Reused (read-only, byte-exact; provenance in reference_manifest.json)

- f30f2224663324e9374b076938c56672febf4082 (play lineage):
  - tools/monkey_campaign/product/session_flow.py — sha256 30e06c04dc33da271bfe817d26a4adbf1251f392b224546fc795f307458455cf (matches archived ONT-X02 receipt claim)
  - tools/monkey_campaign/product/input_mapper.py — 7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44 (archived claim match)
  - tools/monkey_campaign/product/session_flow_tests.py — b6ce2bba598fcb8119de82f9a06639ee6d2744c1605ac82c8d699b8df75ef49a (archived claim match)
  - tools/science_funnel/typeb_export/command_record.py — 6771175933ad20ac… (archived claim match)
- 8550b634ebd7034bb8873eed41d8bdce4d3843d0 (pinned playable slice; extraction
  recipe per archived ONT-X02 attempt 35676f7dcb9f4ceea1c2fc41fbe45aa2):
  - tools/playable_slice/{slice_server.py, scene_boot.py, index.html, push_channel.py} — sha256s in reference_manifest.json

## Not reused / explicitly not promoted

- The archived ONT-X02 card's DONE (criteria a266d161…) is archived-scope evidence;
  it is NOT promoted to MAT2 acceptance. Everything claimed here is re-run under
  the MAT2 criteria hash e50bf1e8… at this attempt's pins.
- Archived finding M4 (mapper CommandRecords have no locomotion consumer) remains
  missing and is NOT fabricated: the wiring's record stream is session
  diagnostics, declared as such.
- MAT2-F01/forest, MAT2-P06 limits: downstream cards; not demanded by this card's
  profile subset ("Use the task-owned subset of layers/behaviors").

## Evidence-class statement (profile kind=motion)

Target of this attempt: motion-class evidence — the REAL reconstructed playable
application (pinned 8550b634 bytes), a REAL native engine process built from the
pinned source, a REAL headless-Chrome player session driving the NEW session
controls, with real video, real screenshots, real engine frames and a
chimera.visual_capture_manifest.v1 camera manifest under the recovery profile.
Anything short of that (unit probes, headless traces, CPU renderings) is labeled
records/static class and is never offered as runtime proof.
