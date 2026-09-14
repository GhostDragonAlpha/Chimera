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
