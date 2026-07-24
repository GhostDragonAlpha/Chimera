# Local servers — what's safe to run, in plain words

> Written 2026-07-23 after three of this project's own servers were found listening on
> every network interface. None of it was a decision; all three were copied idioms.

## The one rule

**A dev server should answer only this machine.** That's `127.0.0.1` (also written
`localhost`). Anything else means other computers can reach it.

You lose nothing by doing this. The agent and the browser both run *on this machine*, so
localhost serves them exactly as well — and serves nobody else.

## The three ways to say "everyone", and what to write instead

| library | the accident | the fix |
|---|---|---|
| `socketserver` / `http.server` in code | `TCPServer(("", PORT), ...)` — an empty string means **all interfaces** | `TCPServer(("127.0.0.1", PORT), ...)` |
| `python -m http.server` on the command line | binds all interfaces **by default** | `python -m http.server 8091 --bind 127.0.0.1` |
| Flask | `app.run(host='0.0.0.0')` | `app.run(host='127.0.0.1')` |

`""`, `0.0.0.0` and `::` all mean the same thing: **every interface**. They look like
"unset" and mean "everyone".

## Wired vs Wi-Fi does not change this

An Ethernet cable is still a local network. Your router, any other computer, phones,
consoles and smart devices on it can all reach a `0.0.0.0` server exactly as easily as
over Wi-Fi. Wired changes who can *listen in* on traffic, not who can *connect*.

## Checking it yourself

```powershell
Get-NetTCPConnection -State Listen | Where-Object { $_.LocalAddress -eq '0.0.0.0' } |
  Select-Object LocalPort, OwningProcess | Sort-Object LocalPort
```

Anything in that list is reachable from your network. Ports like 135, 445, 5985 and 47001
are Windows itself and are normal. What matters is anything *you* started.

## Fixed here

- `view_renders.py` — served `Saved/SplatEmit` on all interfaces. Now localhost.
- `dashboard.py` — Flask dashboard on all interfaces. Now localhost.
- an ad-hoc `python -m http.server 8091` — same, stopped.

## Known, not changed by us

- **LM Studio's API is on `0.0.0.0:1234`** — your local models are reachable from the LAN.
  That's LM Studio's own setting, not this project's, and it is changed in its Server tab
  ("Serve on Local Network" — turn it off). Worth doing: anything on your network can
  otherwise send prompts to your models and read the replies.
- **GLM-5.2 / colibrì** correctly binds `127.0.0.1` already. It was never exposed.

## Windows Firewall

All three profiles are enabled and default to blocking unsolicited inbound, which is a
real second layer. But apps commonly add their own "allow" rule the first time they bind —
so the firewall is a backstop, not a reason to bind `0.0.0.0`.
