# DEPLOY_RUNBOOK.md — putting R9 on the public internet

The whole stack is one operator decision away. Everything on the machine side
is already built and tested:

- `tools/deploy/start_all.bat` — ONE double-click: starts the engine, the game
  shell (**0.0.0.0:8206**), the website (**0.0.0.0:8210**), and the watchdog
  (`tools/supervisor/watchdog.py` with `tools/deploy/pieces_public.json`).
  The watchdog is starter AND keeper: it boots any dead piece and restarts
  dead ones every 5 s, logging to `tools/supervisor/watchdog.log`.
- Hardened stdlib servers (`tools/website/server.py`, `tools/game_shell/server.py`):
  per-IP rate limits (429), request-body caps (413), traversal-refusing static
  paths, no directory listing, `signups.jsonl` never web-readable. Verified by
  curl probe matrices on throwaway ports 2026-09-13 (agent D4, this repo).

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
  - hostname: www.YOURDOMAIN.com
    service: http://localhost:8210
  - service: http_status:404
```

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
  bucketed generously (600/min) so a real player never sees a 429; everything
  else gets 30–120 req/min.
- **Bodies are capped** (5 MB anywhere, 4 KB for a signup) and refused with
  413 before the body is read. Static paths refuse `..`, backslashes, and
  drive letters after percent-decoding. No directory listing anywhere.
- **Player progress** (`tools/game_shell/progress/<name>.json`) is public by
  design — sanitized names, lesson progress only, no secrets.
- **Known gap (fleet task):** the website's PLAY THE DEMO button
  (`tools/website/index.html` line 193) opens a hardcoded
  `http://127.0.0.1:8206`, which works on this machine but not for a public
  visitor. Before public launch it should read the game's public URL (e.g.
  `play.YOURDOMAIN.com` under Option A). Not fixed here — outside this task's
  file list.

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
recommended door. Fifteen steps, in order. Steps marked **[OPERATOR]** need a
human with a browser and payment; every other step a fleet agent can drive.
The config this sequence places is `tools/deploy/cloudflared_config.yml`
(in-repo master; its two placeholders are filled in step 8).

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
   window IS the watchdog). Wait out the boots (engine ~40 s, shells ~10 s),
   then confirm the bindings: `netstat -an | findstr "8107 8206 8210"` →
   8206/8210 on 0.0.0.0, and **8107 on 127.0.0.1 ONLY**.
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
12. Public verification:
    - `curl -s -o NUL -w "%{http_code}\n" https://play.chimera.game/api/health` → 200
    - `curl -s -o NUL -w "%{http_code}\n" https://www.chimera.game/` → 200
    - `curl -s -o NUL -w "%{http_code}\n" https://chimera.game/` → 200
    - catch-all (hosts with no DNS record never resolve, so force it):
      `nslookup play.chimera.game` for an edge IP, then
      `curl -s -o NUL -w "%{http_code}\n" --resolve probe.chimera.game:443:<THAT-IP> https://probe.chimera.game/api/health` → 404
13. **[OPERATOR]** The human check: open `https://chimera.game` on your PHONE
    (not this machine), play the demo, submit a test signup, confirm the line
    landed in `tools\website\signups.jsonl`, and back the file up:
    `copy tools\website\signups.jsonl E:\backups\signups-backup.jsonl`.
14. Watch `tools\supervisor\watchdog.log` for 5 minutes — no restart flapping,
    and the cloudflared window stays quiet.
15. Write the public URL into this file's header and the handoff doc. The
    launch is real when a stranger signs up.

**ROLLBACK (any time, seconds):** Ctrl+C in the `cloudflared tunnel run`
window takes the public door down immediately — Cloudflare's edge then
returns errors for the hostnames, but nothing on this machine becomes
reachable (the DNS records stay, pointing at a tunnel that is simply not
running). Ctrl+C in the `start_all.bat` window stops the stack cleanly. To
unpublish fully, delete the three CNAME records in the Cloudflare dashboard
(DNS → Records). To re-open, resume at step 10.

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
  stands. If that ever stops being enough, the operator's next lever is
  Cloudflare dashboard security rules — not this repo.
