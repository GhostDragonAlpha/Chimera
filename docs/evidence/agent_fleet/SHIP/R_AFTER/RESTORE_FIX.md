# R_AFTER — RESTORE_FIX (agent R2-restore "restore-doctor", 2026-09-14)

Fixes the two boot-restore defects R-after's run 1 named as the gait falsifier
blocker. Commit carries: `ChimeraEngine/engine/membrane_tick.cpp`,
`membrane_tick.hpp` (the seal-idempotency + seal-tree-state code, landed here
from this lane's cancelled prior dispatch and audited/fixed), `main.cpp` (the
restore replay path + two new fixes), and this note.

Provenance honesty: the working tree already held this lane's uncommitted
fix-1 code when this dispatch started (the "cancelled before starting" note
was wrong — a prior dispatch wrote it AND got a build through: the build-dir
exe sha256 `e6418d9b…`, 2026-09-14 11:28, contains it). G8-round-3's sweep
(4dcc082d) separately committed the lane's main.cpp half mid-session. This
dispatch audited every line as untrusted, found the loader dead on arrival,
fixed it, and re-verified the whole path on scratch. R-after's binary
(`a62c6b46…`) no longer exists anywhere on disk — it was overwritten by the
11:28 build — which bounds what can still be reproduced (below).

---

## MECHANISM 1 — restore was not idempotent (the amplifier + the refusal wall)

The session snapshot journals seal INTENTS: every successful `POST /tick_seal`
body was appended verbatim to `tick_seal_history.log`, and boot restore
replayed the file through the engine's own handler. The live world's history
held ~60 entries for 3 distinct cuts (3 foundation cuts + repeats the
pre-guard binary had re-applied silently and re-journaled), so on the
post-H8-guard binary every boot re-refused the repeats BY NAME
(`degenerate_split`), answered `ok:false, replayed:7, failed:60-66`, and —
because the snapshot write-through at the bottom of the api lambda fired for
the replay's own nested successful posts — re-appended +3 history lines per
retry cycle (R-after measured 60→63→66 inside one boot). Per-seal the guard
was right; as a restore it was wrong three ways: the boot retry loop then
re-initialized the body three times (mesh re-post → `init()`), the history
grew forever, and the restore verdict poisoned everything downstream.

FIX SHAPE (three layers, all measured on scratch):
1. **Already-satisfied skip** — `seal(y, cell, &outcome)` now answers
   `SEAL_ALREADY` (HTTP: `{"ok":true,"seal":"already"}`) when the requested
   plane sits on a stored cell bound within 1e-4 m (test a: the named cell's
   own ylo/yhi; test b: the plane crosses nothing but some sealed cell
   carries the plane — a repeat of an ancestor cut). Derivation for 1e-4 m:
   stored bounds are exact (seal() forces new cap slots to py == y), the
   re-evaluation drift H8 measured is ~1 ulp (~1e-7 m), authored cut planes
   on this creature are >= 0.3 m apart — 1e-4 is 1000x above the drift and
   3000x below authored separation. Genuine degenerate/invalid cuts still
   refuse by name.
2. **Seal-tree STATE blob** — the mitosis tree is fully determined by the
   mesh + cut blends + per-cell piece lists, so it round-trips as bytes
   (`tick_seal_state.blob`, magic 'SEL1', self-validating: vertex count must
   match, every cell's rest volume is recomputed from its own pieces and
   compared with the stored v0 at 1e-4 relative; anything stale refuses with
   nothing mutated and the caller falls back to the intent history). It sits
   LAST in the replay order; an executed cut re-snapshots it; already-only
   boots leave it byte-stable.
3. **Replay journal gate** — a thread-local flag suppresses the snapshot
   write-through for exactly the replay's nested posts (the replay is one
   thread), so replayed seals never re-journal themselves; live operator
   POSTs still journal.

**+ THE BUG THIS DISPATCH FOUND IN THAT CODE:** `load_seal_state`'s cell walk
started at `12 + n_cuts*68`, missing the `+4` for the `n_cells` u32 the cut
block had just consumed — so `pn` read `n_cells` itself (4), `4 % 3 != 0`,
and EVERY blob — the loader's own exports included — refused in
microseconds ("stale or absent tree"). The fallback masked it: boots still
restored correctly via history (3 executed + 57 already), so nothing looked
broken except that the state path never once engaged. Diagnosed on the live
exe by bisecting hand-crafted blobs (a 2-cell truncation and a minimal
no-cut blob both refused; the full 512,292-B blob refused in 0.77 ms —
before the witness could possibly run), then by walking the blob in Python
with the reader's exact logic: everything passes once the +4 is applied
(worst witness error 1.06e-06 vs the 1e-4 tolerance). Fixed:
`off = 12 + n_cuts*(4+32+32) + 4`.
Two smaller main.cpp corrections ride along: the restore body's `ok` rule
now counts already-skips as satisfaction (a fully state-restored boot used
to answer `ok:false, replayed:0` — a full restore reported as a failure),
and the boot loop reads the body's `"ok":true` as authoritative (the old
replayed-count heuristic misread the state-blob boot as a failure and
retried it).

## MECHANISM 2 — the inert restored body (contact exactly 0 N vs m·g 135,618 N)

What R-after measured was real, binary-specific, and — as far as every
surviving artifact can show — a DOWNSTREAM FACE of mechanism 1's refused
replay, not an independent defect. The tick's gravity law
(`step()`, membrane_tick.cpp:713) integrates `root_vy` unconditionally
whenever `gravity_on_`; a frozen `root_vy ≡ 0` with gravity armed and a
300 fps render loop is not reachable through the current source (the
block has no gates; the freeze would require the tick to never step, but
`/tick_state` answered — same mutex — and ticks were advancing). The frozen
state was observed exactly once, on `a62c6b46` (guard + round-1 readback
build), in exactly one configuration: the refused-replay restore
(`ok:false, failed:60-66, seal_refusal:"degenerate_split"`, 3x boot retry
re-initializing the body). That binary is gone and that configuration is
unreachable on the current line: the idempotent restore turns the refused
wall into already-skips (`failed:0`), the state blob removes replay entirely,
and the retry loop no longer re-initializes the body. Measured on scratch,
the restored body now engages gravity EXACTLY like R-after's fresh-body
control in every configuration I could construct (table below) — rise to the
derived +9.507 mm equilibrium, settle, `g_contact_n = 135,618 N = m·g`
exactly, `root_vy` settling micro-oscillation ~4e-8 m/s. Per Rule 0 I name
what would falsify this classification: if the lead's build-window-#3
scratch probe (procedure below) still shows `g_contact_n = 0` with
`gravity_on:true` after this fix's build, the freeze is an independent
defect on the a62c line and reopens — the probe is the discriminator.

## SCRATCH VERIFICATION (private ports, isolated cwds, killed BY PID only)

Harness: `.tmp/restore_doctor/` (watch_boot.py, ab_boot.py, reboot_in_place.py;
raw logs + watch.jsonl per run dir). Live 8107 untouched (GET-only probes not
even needed). All ports confirmed freed after each run.

| run | build | snapshot | restore answer | gravity arm result |
|---|---|---|---|---|
| R-after run1 (cited) | a62c6b46 (gone) | 63-line poisoned history | ok:false, replayed:7, failed:60→63→66, +3 history/cycle, seal_refusal set | **contact 0 N, root_vy 0, INERT** |
| 8142 first boot | e6418d9b (has fix-1 + loader bug) | 60-line history + stale blob | ok:true, replayed:8, failed:0, executed:3, already:57, history 60→60, blob rewritten | **ALIVE**: root_y +0.00950712 m (the derived +9.5 mm rise), settles, g_contact_n 135,618 N (0.000% dev), root_vy ~-4e-8 |
| 8142 second boot | e6418d9b | same dir | blob refused (the +4 bug), fallback ok:true, failed:0, history 60→60, blob byte-identical (sha d435a7bc…) | **ALIVE**: identical settle numbers |
| 8143 A/B | 3854de55 (pre-guard class) | 60-line history, no blob | ok:false, replayed:8, failed:60→64→68, +4 history/cycle, n_cells=5 (a repeat re-cut published) | **ALIVE**: same settle numbers |
| 8144 falsifier arm | e6418d9b | 3 foundation + 57 x {"y":99} (genuine refusals) | ok:false, failed:57/cycle, retry x3 ran | **ALIVE**: same settle numbers — the failure/retry path itself is exonerated on the current build |

The 8142 pair also shows the amplifier dead (history 60→60 across boots) and
the snapshot byte-stable. The 8144 run is the mission's BEFORE-arm reproduced
as closely as any surviving binary allows: 60 genuine refusals, 3x retry —
and the body still falls, which is why the freeze is classified as a62c-line
specific with the reopened-falsifier named above.

## FOR THE LEAD — BUILD WINDOW #3 PROCEDURE

1. **Rebuild** `.tmp/build_tick/Release/chimera_engine.exe` from this commit
   (plain incremental is fine — `membrane_tick.obj` is NOT stale this time:
   the fix is in-source; if any compile fails, STOP and surface the error,
   do not link past it — a stale-obj link is how the 11:28 build shipped a
   loader that never loaded).
2. **Scratch verify BEFORE touching live** (the falsifier, 2 minutes): copy
   `session_snapshot/` next to the new exe into an isolated cwd, boot on a
   private port (e.g. 8142) with `--hidden`, wait ~30 s, then:
   - Expected boot log line: `session: boot restore -> {"ok":true,…,
     "failed":0,…}` with EITHER `"seal_executed":0,"seal_already":60` plus
     `snapshot: seal-tree loaded (512292 B, zero cuts executed)` (blob path)
     OR `seal_executed:3, seal_already:57` plus
     `snapshot: seal-tree blob refused… falling back` + `tick_seal_state
     written` (history path — also fine). NO `seal:FAIL` wall, NO retry
     cycles, NO `tick_seal_history +1` lines. Second boot over the same dir
     must print `seal-tree loaded` and leave the blob and the 60-line
     history byte-identical.
   - Gravity probe: `POST /tick_gravity {"on":true}` → poll /tick_state ~4 s:
     `root_y` rises to **+0.00950712 m**, `g_contact_n` settles at
     **135,618 N** (m·g, dev < 0.5%), `root_vy` ~1e-7. If contact reads 0
     with gravity_on:true — the freeze reopened; do not trust the live fall.
3. **Relaunch live 8107** by the standard procedure (kill by PID only).
   Expected restore output: same as the scratch boot line above; /tick_state
   should show `seal_refusal:""` (the state restore clears it), n_cells=4,
   conserve ~-0.0001%. Then the operator may arm gravity on live — the
   scratch probe above is the evidence it will actually fall.
4. Then re-run the R4 gait falsifier (`tools/gait_verify.py --scratch` or on
   a private port): V1b's contact bar and V3a's gravity rung are the two bars
   this fix unblocks; V4-V10 remain unexercised and unjudged.

## NOTES FOR THE NEXT AUDITOR

- `seal_cuts` semantics changed with the state path: live-replayed trees
  report the LAST seal's cut count (130), state-loaded trees report the
  tree's TOTAL cut blends (630). Cosmetic, but it will look like a jump.
- The prior dispatch's gait-enable refusals are now named
  (`gait_enable_block` in /tick_state: gravity_off / stance_off /
  unclassified / no_leg_pins / unsealed / no_feet_cell / patch_degenerate_L
  / no_channel_knee_L …) — a set_gait refusal is now readable, not a bare
  ok:false.
- Raw scratch artifacts (engine logs, watch.jsonl, probe scripts):
  `.tmp/restore_doctor/` (run_p8142, ab_p8143, ab_p8144, snap_prefix,
  snap_poison). Not committed, per the targeted-add rule.
