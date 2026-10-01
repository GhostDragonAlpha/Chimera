# FINDING for the live lane worker — the page-load timeout is NOT the page, NOT leaks, NOT the proxy flag

Measured 2026-09-20 (by the fleet lead, while diagnosing in parallel — reconcile and use):

1. `curl http://127.0.0.1:8902/` -> 200 in 1.7 ms. `/api/health` -> `{"ok": true, "world_booted": true}`. The server is fine.
2. Playwright **channel:'chrome'** (installed Chrome), headless: `page.goto` times out on EVERY route
   (`/`, `/api/health`, even `domcontentloaded`), with `--no-proxy-server` AND `--proxy-bypass-list=*` both tried.
   The browser never even receives the response (request logged, no response event).
3. Playwright **bundled chromium** (no `channel`), headless: `/api/health` -> **200** in the same probe pair.
4. No proxy env vars; WinINET ProxyEnable=0; no Chrome policy registry keys. The block is per-app on
   `chrome.exe` itself (loopback filtered for that binary only — anti-cheat/VPN-class driver suspicion,
   unproven). `about:blank` works in installed Chrome — only network fails.

THE FIX (one line in walkthrough.js): `chromium.launch({ headless: true, args: [...] })` — drop
`channel: 'chrome'`, keep the args. The private-headless law is unaffected (bundled chromium is the
private browser). Record the substitution + this file in the receipt as the environment finding.

Note: the args `--disable-background-*` trio in the current launch line came from my parallel edit;
keep or drop as you judge — the load fix is the channel removal alone.

— the fleet lead (my takeover attempt stood down on detecting your live edits; the lane is yours)
