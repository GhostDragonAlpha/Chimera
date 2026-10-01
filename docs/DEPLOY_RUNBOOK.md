# DEPLOY_RUNBOOK.md — putting R9 on the public internet

The whole stack is one operator decision away. Everything on the machine side
is already built and tested. **Currency: audited against the live three-process
stack 2026-09-14 by fleet agent H12 (drift list + supervisor kill/restart tests
+ a full start-from-zero rehearsal on scratch ports:
`docs/evidence/agent_fleet/SHIP/H12_DEPLOY/`).** The stack today:

- **engine** — `chimera_engine.exe 8107 --hidden`, HTTP, bound `127.0.0.1`,
  from `.tmp/build_tick/Release` (needs `shaders/` next to the exe).
- **game shell** — `tools/game_shell/server.py`, stateless Python, proxies the
  engine, rate-limits per visitor IP, keeps player progress.
- **website** — `tools/website/server.py`, Python, landing page +
  `signups.jsonl` (append-only PII, never web-readable).

- `tools/deploy/start_all.bat` — ONE double-click: starts the engine, the game
  shell (**0.0.0.0:8206**), the website (**0.0.0.0:8210**), and the watchdog
  (`tools/supervisor/watchdog.py` with `tools/deploy/pieces_public.json`).
  The watchdog is starter AND keeper: it boots any dead piece and restarts
  dead ones every 5 s, logging to `tools/supervisor/watchdog.log`. Measured on
  scratch instances 2026-09-14: a killed piece is detected within one 5 s poll
  and healthy again 2–8 s after death; the full stack comes up from zero in
  ~8 s. The watchdog covers **all three** services (config + kill/restart
  test in the evidence dir).
- Hardened stdlib servers (`tools/website/server.py`, `tools/game_shell/server.py`):
  per-IP rate limits (429), request-body caps (413), traversal-refusing static
  paths, no directory listing, `signups.jsonl` never web-readable. Verified by
  curl probe matrices on throwaway ports 2026-09-13 (agent D4, this repo), and
  re-verified against the live instance 2026-09-14: `/signups.jsonl` → 404
  (H12). **The guard lives in the code, not in a running process** — the live
  website that ran on 9/13 21:56→9/14 08:19 predated the hardening and still
  served the file (loopback-only, so never public). Step 12's PII gate exists
  so a stale process can never be carried public.

## THE ONE RULE

**The engine has no auth.** It listens on `127.0.0.1:8107` and must NEVER be
routed, forwarded, or port-opened. The game shell on 8206 is the world's only
door to it. Whatever you deploy below, route **only 8206 and 8210**.

---

## What ONLY the operator does

1. Create the account(s) and pay (Option A needs a Cloudflare account + a
   domain; Option B needs a VPS account + payment; Option C needs a free ngrok
   account). No fleet agent can or should do this.
2. Run `cloudflared tunnel login` / `ngrok` auth once (browser + your
   credentials).
3. Double-click `tools\deploy\start_all.bat` and keep the window open (that
   window IS the watchdog; Ctrl+C stops it cleanly).
4. Own the backups of `tools/website/signups.jsonl` (see Security notes).

## What the fleet does

Everything else — the launcher, the watchdog config, the hardening, the health
checks, the runbook itself. Ask a fleet agent for anything not listed above.

---

## Option A — Cloudflare Tunnel (RECOMMENDED)

Free. No router ports opened, no home IP exposed, TLS and DDoS shielding come
with it, and Cloudflare writes the real visitor IP into `CF-Connecting-IP`
which the servers' rate limiter reads. Only costs: a Cloudflare account and a
domain (~$10/yr from any registrar, or free with a `trycloudflare.com` quick
tunnel for a first look).

One-time setup (operator):

```bat
winget install --id Cloudflare.cloudflared
cloudflared tunnel login
cloudflared tunnel create chimera
cloudflared tunnel route dns chimera play.YOURDOMAIN.com
cloudflared tunnel route dns chimera www.YOURDOMAIN.com
```

Then create `%USERPROFILE%\.cloudflared\config.yml`:

```yaml
tunnel: <the tunnel UUID printed by "tunnel create">
credentials-file: C:\Users\<you>\.cloudflared\<the tunnel UUID>.json
ingress:
  - hostname: play.YOURDOMAIN.com
    service: http://localhost:8206
  - hostname: YOURDOMAIN.com
    service: http://localhost:8210
  - hostname: www.YOURDOMAIN.com
    service: http://localhost:8210
  - service: http_status:404
```

This matches the in-repo master `tools/deploy/cloudflared_config.yml`
(three hostnames + 404 catch-all; the apex CNAME is flattened by Cloudflare,
this is supported).

Every boot: double-click `tools\deploy\start_all.bat`, then run
`cloudflared tunnel run chimera` (or `cloudflared service install` once to
make it a Windows service that survives reboots).

Trade-offs: needs the account + domain; Cloudflare terminates TLS in front of
you (their network sees the traffic — normal for any public site).

## Option B — a $5–6/mo VPS

Full control, a static public IP, no third party in the request path — but
the most setup, and you own the box's security (updates, firewall, TLS
renewal). The engine is a Windows exe, so the practical shape is: the stack
stays on this machine, the VPS is the public front, and an SSH reverse tunnel
carries 8206/8210 to it.

Operator + setup (once, on the VPS): `sshd_config` gets `GatewayPorts yes`,
then from this machine:

```bat
ssh -N -R 0.0.0.0:8206:127.0.0.1:8206 -R 0.0.0.0:8210:127.0.0.1:8210 root@YOUR.VPS.IP
```

On the VPS put nginx (or Caddy, which auto-TLS) in front on 80/443 proxying to
localhost:8206/8210, open 80/443 in the VPS firewall, and point DNS at the VPS
IP. Trade-offs: you maintain the box (unattended upgrades, fail2ban, cert
renewal); if the SSH tunnel drops, the site drops. A plain router
port-forward is the naive version of this and is NOT recommended: it exposes
your home IP and router to the internet with no shielding.

## Option C — ngrok quick test (5 minutes)

For showing the site to someone today. Free ngrok account; free tier gives
random URLs that change each run and (currently) one simultaneous endpoint —
if the second tunnel is refused, test the game on its own or upgrade.

```bat
winget install ngrok.ngrok
ngrok config add-authtoken <token from your ngrok dashboard>
ngrok http 8206      REM window 1 -> prints a https://xxxx.ngrok-free.app URL
ngrok http 8210      REM window 2 -> prints the website URL
```

Trade-offs: URL changes every run, ngrok shows an interstitial page to
visitors on the free tier, not a production door.

---

## Security notes (read before going live)

- **Engine: no auth, never public.** `start_all.bat` binds it 127.0.0.1:8107.
  Only ever route 8206 + 8210. Anyone who can reach 8107 can drive the world.
- **signups.jsonl is append-only PII** (name + email + timestamp, one JSON
  line per signup, duplicates stay). The hardened website returns 404 for it —
  before the hardening it was downloadable by anyone at `/signups.jsonl`.
  Back it up: `copy tools\website\signups.jsonl E:\backups\signups-backup.jsonl`
  (the server only ever appends, so a copy-aside is always safe and complete).
- **Rate limits are per visitor IP.** Behind cloudflared/ngrok all sockets
  arrive from 127.0.0.1, so the servers read the tunnel-written forwarded
  header (`CF-Connecting-IP`, else `X-Forwarded-For`) — but ONLY for loopback
  peers; a direct remote client cannot spoof it. Gameplay polling
  (`/api/verts` 3 Hz + `/api/state` ~1.4 Hz = 264 req/min per player) is
  bucketed generously (600/min): a SOLO player never sees a 429, but two
  active players behind ONE shared NAT do — see the shared-NAT section below.
- **Bodies are capped** (5 MB anywhere, 4 KB for a signup) and refused with
  413 before the body is read. Static paths refuse `..`, backslashes, and
  drive letters after percent-decoding. No directory listing anywhere.
- **Player progress** (`tools/game_shell/progress/<name>.json`) is public by
  design — sanitized names, lesson progress only, no secrets.
- **The demo door is hostname-derived** (`demoUrl()` in
  `tools/website/index.html`): a loopback visitor gets `http://127.0.0.1:8206`,
  a visitor on `www.<domain>` gets `https://play.<domain>` (the page derives
  `play.` + the serving domain). The older hardcoded-`127.0.0.1` gap is fixed.
  Step 13's phone check includes the click that proves the public door works.
- **IPv4 only** (H6 finding D4): both servers bind IPv4, so
  `http://[::1]:8206` is refused; browsers fall back to IPv4 for `localhost`,
  and the door derivation sends loopback hosts to the IPv4 door. Never route
  an IPv6 literal at the stack.

## The shared-NAT rate question (deployment posture, read before go-live)

H6's funnel audit (`docs/evidence/agent_fleet/SHIP/R9_FUNNEL/`) measured a real
starvation: two active game sessions behind ONE public IP drain the shell's
shared stream bucket and 429-starve each other. This section is the
deployment-side posture: what the tunnel passes, what the limits are, how to
SEE a starved player, and what "production numbers" means. The server-side fix
(session keying / raised budget) is a separate fleet task — **no numbers here
change code**.

**What the tunnel passes.** cloudflared connects from loopback, so every
visitor's socket peer is `127.0.0.1`. Both servers key their token buckets on
`CF-Connecting-IP` (else `X-Forwarded-For`) — but ONLY for loopback peers.
Cloudflare overwrites `CF-Connecting-IP` with the real visitor IP at the edge,
so through the tunnel every distinct public IP gets its own bucket; a direct
(non-loopback) client cannot spoof the header because it is never read for
remote peers. Consequence: the buckets that can collide are exactly the
players behind one shared egress IP (home/office NAT, school, carrier NAT) —
and co-tenant fleet tooling on this machine (everything loops back).

**The limits, per class of route** (`RATE_LIMITS` in each server):

| server | class | routes | refill | burst | measured demand |
|---|---|---|---|---|---|
| shell | stream | `/api/verts` `/api/state` `/api/frame` `/api/topology` `/api/touch*` `/api/pose` `/api/gravity` | 600/min | 240 | 264 req/min per playing camera (verts 3 Hz + state ~1.4 Hz) |
| shell | api | `/api/health` `/api/progress` `/api/cam` | 30/min | 15 | a handful per session |
| shell | static | `/`, `/sound.js`, `/lessons.json` | 120/min | 60 | ~3 per page load |
| website | api | `/api/signups/count`, `/api/health`, POST `/api/signup` | 30/min | 15 | 2 per page load + one per signup |
| website | static | page + assets | 120/min | 60 | ~5 per page load |

**The math that bites.** One player needs ~264 stream req/min against 600/min
— a SOLO player cannot trip the bucket (confirmed empirically, zero 429s in
clean runs). Two simultaneous players behind one NAT demand ~528–1000+ req/min
against ONE shared 600/min bucket: the second active camera starts eating
429s. Worse, the page's poll path doubles its own pressure under 429s (a
failed `?delta=1` costs an immediate `?delta=key` pull — measured 6.7 Hz vs
the intended 3 Hz), so a starving session accelerates the starvation.

**What the player sees** (H6's measured failure, so the operator can
recognize it): starved `/api/state` polls mean the lesson judge never sees the
body heal — the verdict line freezes on "the goal is met — now LET GO, and let
the body heal" while the player has done everything right (`goalMet=true` in
the physics). Only the small link line may show "the world is silent —
retrying…". The verdict line never names the starvation.

**The monitoring line — how we'd SEE a starved player.** Both servers are
quiet by design (`log_message` suppressed; the game page polls fast), so
today there is NO server-side per-request log and a 429 leaves no trace on
this machine. A starved player is seen from THEIR side:

- browser console floods `429` on `/api/verts?delta=1`, `?delta=key` and
  `/api/state` (H6 measured 494×429 in a 122 s session), while
- `curl http://play.chimera.game/api/health` from the same machine still
  returns 200 — health is api-class, the starved routes are stream-class;
  health-200 + stream-429 IS the starvation signature;
- the shell-side confirmation, from this machine's co-tenants or a probe:
  count 429s in the tunnel window — the servers don't log them, so the
  counting has to happen client-side or in cloudflared's metrics
  (`cloudflared tunnel run` prints per-request errors at debug level).

Once the server-side fix lands (session keying), ITS log line becomes the
monitoring point; until then the posture is honest: solo players are safe,
two-plus behind one NAT are not, and the workaround for demo-day is
"one active camera per shared IP".

**Recommended production numbers** (for the server-side fix task, restated
from deployment math): key the stream bucket per session, not per IP — a
session id issued with the page; per-IP remains the fallback cap. If the
budget is raised instead of re-keyed: N simultaneous NAT co-tenants need
~264·N req/min plus headroom for the 429-retry doubling, so 2 players ⇒ ≥
1320/min refill and ≥ 500 burst; every expected extra co-tenant adds 264/min.
Anything raised this far stops shedding hammering clients (a hammer stays
under 2 players' worth), which argues for session keying over a bigger bucket.

## The 10-line go-live checklist

1. Close any dev (127.0.0.1) stack on 8206/8210 first — the watchdog keeps
   whatever is already alive, so the public bindings need the ports free.
2. Double-click `tools\deploy\start_all.bat`; wait for `stack up` in the window.
3. Local check: `http://127.0.0.1:8210` loads; PLAY THE DEMO works locally.
4. `netstat -an | findstr "8107 8206 8210"` → 8206/8210 on 0.0.0.0, 8107 on
   127.0.0.1 only.
5. Back up `tools\website\signups.jsonl`.
6. Bring up your door (Option A tunnel / B VPS tunnel / C ngrok) — routes for
   8206 and 8210 ONLY; never 8107.
7. Open the public URL from your PHONE (not this machine): page loads, demo
   plays, a test signup lands in `signups.jsonl`.
8. Watch `tools\supervisor\watchdog.log` for 5 minutes — no restart flapping.
9. Optional abuse check: `for /l %i in (1,1,30) do @curl -s -o NUL -w "%{http_code} " http://127.0.0.1:8210/api/health` → 200s then 429s.
10. Write the public URL into this file's header and the handoff doc; the
    launch is real when a stranger signs up.

---

## GO-LIVE SEQUENCE — Option A, concrete (`chimera.game` via Cloudflare Tunnel)

The detailed, no-assumptions version of the checklist above for the
recommended door. Fifteen steps, in order — **the supervisor comes up first
(step 3) and the tunnel last (step 10)**, so the world is being kept alive
before the first stranger can reach it. Steps marked **[OPERATOR]** need a
human with a browser and payment; every other step a fleet agent can drive.
The config this sequence places is `tools/deploy/cloudflared_config.yml`
(in-repo master; its two placeholders are filled in step 8). Rehearsal
timings from the 2026-09-14 scratch rehearsal are in brackets.

1. **[OPERATOR]** Buy the domain `chimera.game` (~$10/yr at any registrar)
   and create a Cloudflare account. Add the domain to Cloudflare and follow
   its prompts to point the registrar's nameservers at Cloudflare's
   (propagation: minutes to a few hours). No fleet agent can or should do
   this part.
2. Close any dev (127.0.0.1) stack on 8206/8210 — the watchdog keeps whatever
   is already alive, so the public bindings need the ports free. Check:
   `netstat -ano | findstr "8206 8210"` must return nothing (or kill the
   listed PIDs).
3. Double-click `tools\deploy\start_all.bat` and leave the window open (the
   window IS the watchdog). Wait out the boots (engine ~1 s to first health
   once shaders/ is in place; shell/site ~1–2 s; the whole stack from zero
   measured ~8 s [rehearsal]), then confirm the bindings: `netstat -an |
   findstr "8107 8206 8210"` → 8206/8210 on 0.0.0.0, and **8107 on 127.0.0.1
   ONLY**.
   SMOKE: the window shows `stack up`; `curl -s
   http://127.0.0.1:8107/tick_state` contains `ticks`;
   `curl -s http://127.0.0.1:8206/api/health` → `{"ok": true...}`;
   `curl -s -o NUL -w "%{http_code}" http://127.0.0.1:8210/` → 200.
4. Install the tunnel client: `winget install --id Cloudflare.cloudflared`.
   Open a NEW terminal afterwards so PATH picks it up.
5. **[OPERATOR]** `cloudflared tunnel login` — opens a browser; pick the
   `chimera.game` zone and approve. Writes `%USERPROFILE%\.cloudflared\cert.pem`.
   One time per machine.
6. `cloudflared tunnel create chimera` — prints the tunnel UUID and writes
   `%USERPROFILE%\.cloudflared\<UUID>.json`. **Copy the UUID**; step 8 needs
   it twice.
7. Route the three hostnames (each creates a CNAME at the Cloudflare edge;
   the apex CNAME is flattened by Cloudflare, this is supported):
   - `cloudflared tunnel route dns chimera play.chimera.game`
   - `cloudflared tunnel route dns chimera www.chimera.game`
   - `cloudflared tunnel route dns chimera chimera.game`
8. Place the config: `copy tools\deploy\cloudflared_config.yml
   %USERPROFILE%\.cloudflared\config.yml`, then edit THE COPY: replace both
   `<TUNNEL-UUID>` placeholders (the `tunnel:` line and the `credentials-file`
   line) with the UUID from step 6 and `<YOU>` with your Windows username.
   Verify: `cloudflared tunnel ingress validate` → OK.
9. Dry-check the rule table without sending traffic:
   - `cloudflared tunnel ingress rule https://play.chimera.game` → 8206
   - `cloudflared tunnel ingress rule https://chimera.game` → 8210 (same for www)
   - `cloudflared tunnel ingress rule https://probe.chimera.game` → 404 catch-all
10. Start the door — `cloudflared tunnel run chimera` — and keep that window
    open: closing it IS taking the site down (that is the rollback). This is
    the operator's kill-switch; the human should own this window. To make it
    survive reboots instead: run `cloudflared service install chimera` once
    (as admin) — it auto-runs the tunnel with the same config.
11. Loopback verification, on this machine, before trusting the door:
    - `curl -s -o NUL -w "%{http_code}\n" http://127.0.0.1:8206/api/health` → 200
    - `curl -s -o NUL -w "%{http_code}\n" http://127.0.0.1:8210/` → 200
    - **PII GATE (must be 404 — do not open the tunnel if not):**
      `curl -s -o NUL -w "%{http_code}\n" http://127.0.0.1:8210/signups.jsonl`
      → **404**. The 404 comes from the hardened server CODE — a running
      process started from an older checkout still serves the file (this
      happened on the dev stack 9/13–9/14, loopback-only). If you see 200:
      close the dev stack, re-run step 3, re-test.
    - og:image check: `curl -s -o NUL -w "%{http_code}\n"
      http://127.0.0.1:8210/store_art/capsule_616x353.png` → 200 (the page's
      social card; 404 means `tools\store_art` was never copied to
      `tools\website\store_art`).
12. Public verification:
    - `curl -s -o NUL -w "%{http_code}\n" https://play.chimera.game/api/health` → 200
    - `curl -s -o NUL -w "%{http_code}\n" https://www.chimera.game/` → 200
    - `curl -s -o NUL -w "%{http_code}\n" https://chimera.game/` → 200
    - catch-all (hosts with no DNS record never resolve, so force it):
      `nslookup play.chimera.game` for an edge IP, then
      `curl -s -o NUL -w "%{http_code}\n" --resolve probe.chimera.game:443:<THAT-IP> https://probe.chimera.game/api/health` → 404
13. **[OPERATOR]** The human check: open `https://chimera.game` on your PHONE
    (not this machine), PLAY THE DEMO — it must open
    `https://play.chimera.game` (the derived door; if it tries plain-http or
    127.0.0.1, stop and fix before launch) — pass one lesson, submit a test
    signup, confirm the line landed in `tools\website\signups.jsonl`, and
    back the file up:
    `copy tools\website\signups.jsonl E:\backups\signups-backup.jsonl`.
14. Watch `tools\supervisor\watchdog.log` for 5 minutes — no restart flapping
    (healthy log shows only `watchdog_started`; any `action=down`/`restarted`
    pairs more than once or twice is flapping: fix the piece, don't launch),
    and the cloudflared window stays quiet.
15. Write the public URL into this file's header and the handoff doc. The
    launch is real when a stranger signs up.

**ROLLBACK (any time, seconds):** Ctrl+C in the `cloudflared tunnel run`
window takes the public door down immediately — Cloudflare's edge then
returns errors for the hostnames, but nothing on this machine becomes
reachable (the DNS records stay, pointing at a tunnel that is simply not
running). Ctrl+C in the `start_all.bat` window stops the stack cleanly in
seconds — it terminates the shell, the site, and (since the supervisor spawns
the exe directly) the ENGINE too, hard (TerminateProcess: the world keeps its
last saved state; session logs up to that moment stay on disk). To unpublish
fully, delete the three CNAME records in the Cloudflare dashboard
(DNS → Records). To re-open, resume at step 10.

### FAILURE CALL-TREE — what each death looks like to a player

The watchdog health-checks every 5 s; a killed piece is detected within one
poll and healthy 2–8 s after death (measured on scratch instances,
`docs/evidence/agent_fleet/SHIP/H12_DEPLOY/`). Deaths mid-session:

- **The engine dies mid-session** (crash, OOM, someone closes a stray window):
  players see the world FREEZE — the page keeps polling, but the shell's
  proxy gets connection-refused and answers `502 {"error": "world
  unreachable..."}` for every world route; verts stop changing; the small
  link line shows "the world is silent — retrying…". The watchdog detects the
  dead /tick_state within ≤5 s and the fresh exe answers health in ~1 s
  (measured kill→healthy 5 s): the creature is restored from its saved world
  state. Players' pages re-attach on their next poll — no refresh needed;
  the current lesson judge resumes. Total player-visible freeze: well under
  15 s. A player mid-LOSES-nothing-but-ticks: progress is saved explicitly
  ("save progress" button) and lesson passes latch server-side.
- **The game shell dies mid-session** (8206): the door itself is gone — the
  page's polls fail outright (connection refused through the tunnel;
  cloudflared answers 502 at the edge), so the page can't even say
  "retrying". Watchdog restart: ~1–2 s boot, kill→healthy ≤8 s (measured).
  The world never died, so after the page's poll reconnects, the creature
  state is exactly where it was; a lesson in progress continues.
- **The website dies mid-session** (8210): the GAME KEEPS PLAYING (separate
  service — players already in the shell are untouched). New visitors get
  edge errors for ~8 s; the count endpoint and signups are unreachable, so a
  signup attempted in the gap fails client-side and must be retried
  (nothing is half-written: the signup store is one append per POST).
- **cloudflared dies / window closed**: loopback is fine; the public doors
  all return edge errors (1033) until it runs again. This IS the designed
  kill-switch. To make the tunnel survive reboots and crashes:
  `cloudflared service install chimera` (once, as admin).
- **The machine reboots**: nothing auto-starts the stack — `start_all.bat`
  is a window, not a service. Either re-double-click it (and the tunnel
  window), or once, as admin, put a Task Scheduler entry on
  `tools\deploy\start_all.bat` plus `cloudflared service install chimera`.
  The watchdog is the auto-restarter WITHIN a boot session, not across one.
- **A piece that cannot boot** (e.g. the exe missing its `shaders/` dir —
  this exact failure was caught in the 2026-09-14 rehearsal): the watchdog
  retries it forever (~2 attempts ≈ every 85 s for the engine's 40 s boot
  budget), and its front doors stay up. `tools\supervisor\watchdog.log` fills
  with `start_failed attempt=1/2` pairs for the dead piece — read the log
  from the top, the first `start_failed` names the piece that never came
  back.

### Security posture (state it plainly)

- **The engine never leaves the machine.** 8107 is bound to 127.0.0.1 by
  `pieces_public.json`, has NO ingress rule in `cloudflared_config.yml`, and
  must never get one — it has no auth; anyone who reaches it can drive the
  world. Step 3's netstat is the standing proof of the binding.
- **Exactly two doors.** Only 8206 (game) and 8210 (website) are routed; the
  404 catch-all answers every other hostname that somehow reaches the tunnel.
  No router ports are opened and the home IP is never visible to visitors.
- **The rate limits in the servers are the ONLY abuse defense.** The free
  tunnel provides TLS and home-IP shielding, but no WAF, no bot rules, no
  allowlist is configured. A determined abuser's requests flow straight to
  the stdlib servers, where the per-real-visitor-IP buckets (600/min gameplay
  polling, 30–120/min everything else, 5 MB / 4 KB body caps) are all that
  stands — with the one honest caveat that buckets key on IP, so co-tenants
  of one NAT share a bucket (the shared-NAT section above; the server-side
  session-keying fix is a separate fleet task). If that ever stops being
  enough, the operator's next lever is Cloudflare dashboard security rules —
  not this repo.
