# H12 DEPLOY AUDIT — the deploy kit vs today's three-process stack (fleet agent H12 "deploy-doctor")

2026-09-14 · workspace `E:\ChimeraWork\slot-01` · branch `astra/tasks/matter-kernel-format-01` · HEAD `569083bb`
Scope owned/touched: `tools/deploy/`, `tools/supervisor/`, `docs/DEPLOY_RUNBOOK.md`, this evidence dir.
Never touched (as ordered): `tools/game_shell/`, `tools/website/`, `ChimeraEngine/`, the live stack (read-only curls + netstat only).

## VERDICT: SHIP-READY on the machine side — every gap an agent could close is closed; the residuals below are operator-only.

---

## 1. Drift list (found -> fixed)

| # | drift found | fixed how |
|---|---|---|
| D1 | **Runbook "Known gap" was stale**: PLAY THE DEMO no longer hardcodes `127.0.0.1:8206` — `demoUrl()` in `tools/website/index.html` derives the door from the serving hostname (H6 already walked it). | Runbook bullet replaced: door is hostname-derived; step 13 now includes the click that proves `https://play.chimera.game`. |
| D2 | **Runbook claimed "a real player never sees a 429"** — refuted by H6's storm: two players behind one NAT share the 600/min stream bucket. | Security-notes bullet corrected; new runbook section "The shared-NAT rate question" (posture, limits table, starved-player signature, monitoring line, production numbers). |
| D3 | **Runbook's Option A sample config lacked the apex hostname** (`chimera.game` -> 8210) that the in-repo master `cloudflared_config.yml` has. | Sample now matches the master (3 hostnames + 404). |
| D4 | **The watchdog could never stop the engine it started**: pieces spawned `launch_chimera.bat`, whose `start ""` DETACHES the engine — the watchdog's child handle was a cmd wrapper that exits instantly, so "Ctrl+C terminates the pieces this watchdog started" was false for the engine. | `pieces_public.json` + `start_chimera.py` DEFAULT_CONFIG spawn `chimera_engine.exe 8107 --hidden` DIRECTLY; `spawn()` now resolves a bare exe name against the piece cwd (Popen does NOT: WinError 2, tested). Shutdown contract re-validated on scratch (children_terminated includes the engine; port closed). |
| D5 | **Boot-time numbers in the sequence were guesses** ("engine ~40 s"): measured cold boot is ~1 s for the exe (with `shaders/` present), whole stack ~8 s. | Sequence updated with measured timings [bracketed]. The 40 s stays only as the health-check boot BUDGET. |
| D6 | **PII gate missing**: the guard is in server CODE, but a live process started from an older checkout still served `signups.jsonl` raw (this actually happened: dev website 9/13 21:56 -> 9/14 08:19, loopback-only so never public; timeline in `rehearsal_timings.json`). The watchdog would have kept such a process alive into a public launch. | Step 11 now has the **PII GATE**: `GET /signups.jsonl` must 404 before the tunnel opens, with the exact recovery (close dev stack, re-run step 3). Live instance re-verified 404 after another agent's 08:19 restart. |
| D7 | **og:image capsule**: H6's D3 (404 until deploy copies it) is now CLOSED on disk+live (`tools/website/store_art/` serves 200) — but nothing in the sequence checked it. | Step 11 og:image probe added (200 expected; 404 names the missing copy). Note for the website owner: `tools/website/store_art/` is untracked in git. |
| D8 | **H6 D4 (IPv4-only bind) undocumented.** | Security note added: servers bind IPv4; `localhost` works via browser fallback; never route an IPv6 literal. |
| D9 | **No failure call-tree / reboot story.** | New runbook sections: FAILURE CALL-TREE (engine/shell/site/tunnel deaths, player-visible symptoms, supervisor action, measured restore times) + the reboot caveat (`start_all.bat` is a window, not a service; Task Scheduler + `cloudflared service install`). |

## 2. Supervisor verdict

**COVERS ALL THREE, PROVEN.** Config checks engine (`/tick_state` has "ticks"), shell (`/api/health` ok:true), website (`GET /` 200) every 5 s; any dead piece restarts through the same starters. Scratch tests (dummy pieces on 8245–8247 + real pieces on 8137/8246/8245 — log: `supervisor_test_log.txt`, numbers: `rehearsal_timings.json`):

- single kill -> healthy: 2.6–8 s (detection ≤ one 5 s poll + 1–2 s boot)
- simultaneous double kill -> both healthy in 4–7 s
- real engine kill -> healthy: 5 s (creature restored from saved world state)
- stack from zero: ~8 s total; clean shutdown terminates exactly the children it spawned

One upgrade shipped: the direct-exe spawn (D4 above) — without it the engine was un-killable by the supervisor and outlived every Ctrl+C.

## 3. Rehearsal result (what CAN be rehearsed on localhost)

Full start-from-zero on scratch ports PASSED (attempt 2; attempt 1 found a real deploy bug — exe without `shaders/` boots nothing, now a named call-tree signature with the log fingerprint `start_failed attempt=1/2` pairs). Shell proxy verified with one read-only `/api/state`. Teardown verified: zero scratch listeners remained, live stack healthy throughout.

## 4. Residual list — what actually blocks R9 go-live (operator-only; no agent can close these)

1. **Buy the domain + Cloudflare account** (sequence steps 1, 5): `chimera.game` (~$10/yr), nameservers to Cloudflare, `cloudflared tunnel login` (browser + human credentials). Nothing in the repo can proceed without this.
2. **Own the go-live windows** (steps 3, 10): double-click `tools\deploy\start_all.bat` (public 0.0.0.0 bindings — the current dev stack is loopback and must be closed first, per step 2) and own the `cloudflared tunnel run` window (the kill-switch), or install both as services.
3. **The phone check** (step 13): human with a phone on cellular, pass a lesson, submit the test signup, back up `signups.jsonl`.
4. **The shared-NAT starvation itself** — the server-side fix (session keying or raised budget) is assigned to another agent; until it lands, demo-day posture is "one active camera per shared IP" (runbook section documents the numbers, the player-visible signature, and the monitoring line).
5. (Housekeeping, not blocking) `tools/website/store_art/` is untracked — the website owner should commit it so a fresh checkout serves the social card; and H6 left four clearly-marked test rows in `signups.jsonl` the operator may prune before launch.

## Evidence index

- `supervisor_test_log.txt` — the watchdog's own log lines for every scratch test (dummies, real stack, bare-exe resolution)
- `rehearsal_timings.json` — every measured number, the shaders/ failure, the PII timeline
- `docs/DEPLOY_RUNBOOK.md` — updated runbook (drift fixes, shared-NAT posture, refreshed 15-step sequence, rollback + failure call-tree)
- `tools/deploy/pieces_public.json`, `tools/supervisor/start_chimera.py`, `tools/deploy/start_all.bat`, `tools/supervisor/README.md` — the supervisor fixes
