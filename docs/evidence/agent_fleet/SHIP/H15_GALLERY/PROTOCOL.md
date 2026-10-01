# H15 AFTER-RUN PROTOCOL — re-prove the aliveness law on the post-guard binary

Agent H15, 2026-09-14. Execute ONCE after the build window recompiles the
engine (the degenerate-split guard landing in `membrane_tick.cpp`). Everything
is staged; the one command boots, measures, judges, and cleans up after itself.

## THE ONE COMMAND

```
cd E:\ChimeraWork\slot-01
python docs\evidence\agent_fleet\SHIP\H15_GALLERY\h15_gallery.py --port 8140
```

Runtime ~1 minute (measured 48 s + boots). Exit code 0 = PASS, 1 = FAIL.

Prerequisites (all verified at baseline):
- the freshly built binary is at `.tmp\build_tick\Release\chimera_engine.exe`
  (the build window's output; if the path moved, pass `--engine <path>`)
- port 8140 free (`netstat -ano | findstr :8140` must be empty — the driver
  never touches the live stack on 8107/8206/8210)
- `python` with numpy (repo standard)

What the command does, by itself:
1. Per shape (blob, torus, capsule, peanut, rbox — `tools/gallery/obj/*.obj`):
   boots a FRESH throwaway engine on 8140 in a private cwd under
   `.h15_scratch/` (shaders copy, `--hidden` ONLY — do NOT add `--no-restore`,
   measured 2/2 boot crash with `--hidden` on this lineage), asserts the tick
   is born EMPTY (`sealed:false`), then import → classify → vertbind →
   `/tick_seal` at mid-height → A1 conservation → A2 pose (+25 deg, G4 mid pin
   first, best-armed fallback, displacement + rest-return) → A3 10 kN touch
   (dimple + dP + relax) → framed portrait → `taskkill /F /T` in a `finally`.
2. Writes `gallery_results_<stamp>.json` + `gallery_results.json` + five
   `*_alive.png` INTO THIS EVIDENCE DIR (nothing on the desktop).
3. Scans every response for `degenerate` / `refus` / `guard` strings
   (the guard tripwire) and records them per shape per endpoint.
4. Prints the gallery table and the **ONE-COMMAND VERDICT**:
   `PASS 5/5 ALIVE` or `FAIL -- GALLERY NOT RE-PROVEN`.
   `judge()` inside the driver enforces per shape: import ok, cells == 2,
   |conserve_pct| <= 0.001, dimple within 0.198944 +/- 0.005 m, pose
   displacement > 0, touch answered, portrait present, and (torus only)
   `seal_loops == 2`. A shape alive but off those numbers prints
   `ALIVE-BUT-OFF-EXPECTED` and still fails the run.

## THE EXPECTED TABLE (baseline binary, 2026-09-14 — the after-run must re-meet it)

| creature | verts | tris | cells | loops | cuts | caps | V_whole | conserve % | pose joint → maxdisp m | 10 kN dP_upper Pa | dimple m | verdict |
|----------|------:|-----:|------:|------:|-----:|-----:|--------:|-----------:|-----------------:|------------------:|--------:|---------|
| blob     | 1,986 | 3,968 | 2 | 1 | 128 | 126 | 8.33391 | 0.000 | j1 → 0.1562 | +13,136,100 | 0.198944 | ALIVE |
| **torus**| 2,048 | 4,096 | 2 | **2** | 128 | 124 | 7.34284 | 0.000 | j2 → 0.0958 | +2,249,130 | 0.198944 | ALIVE |
| capsule  | 1,346 | 2,688 | 2 | 1 | 96 | 94 | 1.69175 | 0.000 | j0 → 0.1031 | +2,371,300 | 0.198944 | ALIVE |
| peanut   | 1,986 | 3,968 | 2 | 1 | 128 | 126 | 0.90617 | 0.000 | j1 → 0.0860 | +30,212,600 | 0.198944 | ALIVE |
| rbox     | 1,986 | 3,968 | 2 | 1 | 128 | 126 | 8.47347 | 0.000 | j0 → 0.1632 | +36,092,500 | 0.198944 | ALIVE |

Tolerances baked into `judge()`: conserve band 0.001 % (A1 read wiggles in its
6th decimal — races the tick loop), dimple +/- 0.005 m, displacement > 0 with
the SAME joint routing (blob j1, torus j2, capsule j0, peanut j1, rbox j0 —
routing was bit-identical across two baseline runs; a routing change means the
travel/bind path moved, flag it). dP is the mesh-dependent channel: same order
of magnitude, not bit-pinned. Full raw numbers: `gallery_results.json` and
`BASELINE.md`.

## PASS / FAIL verdict + guard triage

- **PASS**: `ONE-COMMAND VERDICT: PASS 5/5 ALIVE`, expected table matched,
  zero guard strings in the JSON (`python -c` one-liner below), torus row
  shows loops=2 cuts=128 caps=124. The aliveness law is re-proven on the new
  binary; commit the new `gallery_results*.json` + portraits into
  `SHIP/H15_GALLERY/` as the AFTER record (append-only, do not overwrite the
  baseline pair — the baseline stamps are `20260914_082218` and
  `20260914_082450`).
- **FAIL — guard broke a legitimate seal** (the case this protocol exists
  for): any `/tick_seal` refusal or `degenerate` string on any shape. The
  gallery never offers a junk split (every daughter is 50 % of parent —
  100x above the 0.5 % floor, see `GUARD_THRESHOLD.md`), so ANY such refusal
  is a REGRESSION. Name the shape and row to the engine owner: torus first
  (multi-loop seal), capsule second (smallest absolute volumes, C1 seams).
- **FAIL — anything else** (import refusal, dimple off, displacement zero or
  re-routed, conservation out of band): record per this protocol, attach the
  new `gallery_results.json` + the failing shape's throwaway log (copy from
  `.h15_scratch/cwd_8140_*/engine.log` before rerunning), and escalate — do
  not iterate on the engine.

Guard-string check one-liner after the run:

```
python -c "import json;rs=json.load(open(r'docs\evidence\agent_fleet\SHIP\H15_GALLERY\gallery_results.json'));print([ (r['name'],w) for r in rs for k in ('import','joints','classify','vertbind','seal') for w in (r.get(k) or {}).get('_guard_watch',[]) ] or 'CLEAN')"
```

Hygiene after the run: the driver kills each throwaway in a `finally`; confirm
`netstat -ano | findstr :8140` is empty. The live stack (8107/8206/8210) is
never connected to. `.h15_scratch/` is untracked scratch — leave or delete.

Optional extra (NOT part of the pass/fail): a correct-refusal demonstration —
on a live throwaway, `POST /tick_seal_split {"cell":0}` on an intact
single-surface cell must refuse (`comps < 2`), proving the endpoint's own
honest refusal still fires beside the new guard.
