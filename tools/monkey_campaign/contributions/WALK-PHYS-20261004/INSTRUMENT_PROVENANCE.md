# INSTRUMENT PROVENANCE — WALK-PHYS-20261004

The instrument arm's derivation chain, hash-pinned. The prereg of record is
`PREREGISTRATION.md` (committed ALONE-FIRST as
`2b58118cae81110b8e1c69a26e83d0aadab002f4` on `origin/review/WALK-PHYS-20261004`,
blob sha256 `b4326a0971326db3d6267c9e00a9372ce33707d084b11a897417406e319de3fe`).

## The chain (every step byte-verified at run time by run_battery.py)

1. BASE SOURCE: `inputs/gait_unit_viswalk_dump_orig.cpp` — byte copy of Git
   blob `a7bfe15e34e25a34c5316d65038b072d79ac529a` from the shared object
   database, reachable at the walk-anchor training revision
   `17ba94b948ca217c1bbf8f7dee5b51b995b387bb` (the revision the sealed W03
   replay extracted; its report cites this object and content sha256
   `dea2be78762860b201a348824fd6a4a4fe9f2a1dd3f9552157187729568f1cab`,
   re-verified). This is the exact program that produced the sealed W03
   anchors (stdout `8c537cdb...`, stderr `c6f9b6c0...` recorded hash, q-dumps
   `b47b709c...` x2, 302 ticks, refusal, dx `0.9131056683968011`).
2. PATCH: `INSTRUMENT_PATCH.py` — six anchored replacements, 37 added lines,
   ZERO deleted lines. Every hook is env-gated (`GAITPHYS_*`) and default-OFF;
   telemetry goes to FILES only; no new stdout/stderr byte exists in any
   mode. Hooks: per-tick telemetry (serialized status channels only),
   `GAITPHYS_POWER_CUT_TICK` (the P6 declared drive-cut via the engine's own
   `configure({"power",false})`), `GAITPHYS_INJECT_TICK` (the P9 state-write
   probe through the public `speeds()` accessor), `GAITPHYS_MAX_TICKS`
   (bounded arms / the 1-tick smoke).
3. INSTRUMENT: `gait_unit_viswalk_dump_walkphys.cpp` sha256
   `35ae38c131818f4def9d116a335b2e66a0050c4f8b56e0b11837735b497b2086`
   (== INSTRUMENT_PATCH.py applied to the base bytes; reproduce with
   `python -B INSTRUMENT_PATCH.py inputs/gait_unit_viswalk_dump_orig.cpp out.cpp`).
4. PHYSICS HEADER: `inputs/gait_controller.hpp` — content sha256
   `f0ffea12795bd47f7c48f5ed9b8aa98869725467d94a1081b1d942f6fba129bd` = Git
   blob `5863348f2deef1f01e3cf761d0c4151a10035a6d` (present in the pin
   commit's tree at three contribution paths; byte-identical). UNMODIFIED —
   the instrument never touches the engine.
5. BUILD: `inputs/build_dump.ps1`'s exact flag pattern
   (`cl /nologo /std:c++17 /O2 /W4 /fp:precise /EHsc /DGAIT_EVENT_TRACE`,
   vcvarsall x64, out-of-tree). The pinned recipe's own note: the exe hash
   differs per machine (MSVC embeds paths); the OUTPUT byte-identity is the
   load-bearing property (the W03 precedent).
6. ANCHORS: `inputs/anchors/` — byte copies from the pin commit's tree
   (`tools/monkey_campaign/contributions/MAT2-W03/viswalk_dump/`):
   dump_stdout.txt `8c537cdb...`, states_run1/2.jsonl `b47b709c...` x2,
   dump_run_record.json (the stderr anchor hash `c6f9b6c0...` is carried in
   this record; no stderr bytes are preserved anywhere — the P1 comparison
   uses the recorded hash), walk_numbers_record.json.
7. SCENE: `inputs/scene.json` sha256
   `f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342` — the
   sealed physics bytes, UNTOUCHED on every clean arm. Control-arm scene
   deltas (declared in the prereg, built in scratch at run time, hashes in
   the receipt): mu=0 (one field) and hip cap x1.5 (one field).

## P3 instrument disclosure (declared before the run)

The serialized contact channels are DIRECTION-FREE scalars
(`friction_force_N`, `slip_speed_m_s`, `reaction_N`); the tangent direction
of a STICKING contact is not recoverable from them. The frozen P3 identity is
therefore evaluated in its rigorous closable form:
`|m * d(COM_x)/dt| <= sum(|friction_force_N|) * dt` per tick (friction is the
only horizontal force; gravity and the plane normals are vertical; push_N=0),
window 1e-9. The exact-equality subset and this instrument limitation are
recorded in the receipt — the feed-forward for the store schema is that the
contact record needs a signed tangent component.
