# MAT2-M09 report — loose bones assembled by physical connective matter

Candidate revision: see git log (prereg 6319a4fd -> Amendment A1 954de43f -> implementation 727dae9f on base b3490ecd = merge of PR #267, the MAT2-M08 winner). Criteria sha256 803ca2d1cd6e410217fb9e3a2bdb8e29fbe291ae2fe685fcfb83f66b442dacc4. House standards cited at the candidate commit: IMPLEMENTER_CHECKLIST.md (G1-G9), TOOLKIT.md (P1-P9).

## X1 full-trajectory run (CPU, all gates armed)

- done_when clause demonstrated in ONE continuous 90-tick run: the two bone shapes fall separately (first bone-ground contact ticks 21 and 30; the frozen windows require bone_b in [17, 24] and bone_a in [24, 31]), are assembled by authored connective material (bind tick 45: ligament check-rein + capsule strut on the sealed M05 bond interface; joint contact material first loads tick 66), held under the declared pull (ligament tension 1.7311434100896435 N at tick 84 with the joint contact OPEN — no adhesion), and become independent again at the tick-85 release.
- bitwise post-release zero on ticks 85..89: True; E_diss_release 0.05542663563142605 J equals the held element energy 0.05542663563142605 J within 1e-18.
- derived restraint: count 3 (minimum over bound ticks, elements only) -> BITWISE zero matrix and count 0 after release: True. The restraint record is measurement-only (P-AST-restraint probe True); no joint/hinge/pose-writer element exists (P-AST-no-joint True).
- ledger: worst per-substep momentum identity 3.469446951953614e-18 N*s (bound 1e-12); worst energy residual/bound ratio 0.9926921125409394; max bone speed 2.07 m/s (bound 4.0, T7).
- determinism (X2): fresh-run trace sha256 273dbc4f8c73a6f562c0260050f7d23012288af29426f4d7b8a191b35efeb744 == rerun sha256 (byte-identical).

## Falsifier bank (P1 form: clean control FIRST, named guards)

- FB1 hidden hinge survives removal: clean control bitwise zero with release displacement 0.0222781141437259 m; tampered stale edge keeps 'refused' N of force (bit True).
- FB2 unbound media: render_unbound_to_state refused on the offset geometry (bit True); the committed render binds every frame by bitwise state_hash equality with the trace.
- FB3 hidden support / clipped load path: the dropped ground reaction refuses ledger_imbalance ('ledger_imbalance'; bit True).
- FB4 area-independent triangle forces: clean patch load ratio 0.3997925690123838 equals the area ratio 10/7; the equal-load tamper measures 1.0 (bit True).
- FB5 overlay-driven motion: frame-source identity refuses overlay_motion_detected (bit True).
- FB6 unaccounted energy: dropping E_diss_release trips the release-tick residual bound (bit True).

## Capture and regression

- capture: single-artifact video binding fa86c9823826fd82... (FFV1 +bitexact, ffmpeg 8.1.1-full_build-www.gyan.dev); validate_manifest CAMERA_METADATA_STRUCTURE_ONLY, structurally_valid True, 6 views; frames 12; every frame bound bitwise to the trace.
- X4 regression: M05 suite exit 0, M06 suite exit 0 (both UNMODIFIED, this revision).

## Applicability and disclosure

- CPU bank authoritative AND X3 GPU confirmation MEASURED (window 3, head 103afa35, jobs m09-gmain-003/grerun-001/gcompare-001): X3_pass=True, worst position diff 6.477457459297398e-15 m (window 1e-12), worst comparable scalar 4.583847270645864e-12 relative (window 1e-9), telemetry 40 B/tick up / 1920 B/tick down (960 B/comp vs 1024 budget), digest chain green every tick; gcompare trace+receipt byte-identical across runs (trace 0c1b464c5f95506c58a7e89bed4603421e9000b671385318ec822b9a56274fec). CPU-first discipline held: the full 90-tick numba CUDA-simulator run was green before any mailbox job.
- Visual acceptance of the capture remains with the independent reviewer; validate_manifest is camera-metadata structure only.
- The X1 agreement fixture runs on THIS card's scenario; the GPU arm must confirm the same fixture (frozen windows 1e-12 m positions, 1e-9 relative scalars, byte-identical reruns).
