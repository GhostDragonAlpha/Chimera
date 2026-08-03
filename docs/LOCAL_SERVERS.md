# Local servers — what's safe to run, in plain words

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY MEMBRANE IS A THEORY. STATE IT BEFORE YOU BUILD IT.** Three parts, all three
> required: a **STATEMENT** someone could disagree with · a **PREDICTION** you have not measured
> yet · a **FALSIFIER** named *before* the run. **A description survives any result; a theory can
> lose.** No falsifier, no build.
>
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
>
> **RULE 0 IS ENFORCED AT S-1 VALIDATE** — every port tested alone, and `port_test()` REFUSES to
> register a test that names no falsifier. The model it feeds: `docs/THE_COMPILER.md` — ports →
> primitives → programs → parser → runtime → calibration.
>
> **[docs/THE_LAW.md](../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

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
- **GLM-5.2 / colibrì** was removed entirely on 2026-07-23 (operator's call). It is gone.

## Windows Firewall

All three profiles are enabled and default to blocking unsolicited inbound, which is a
real second layer. But apps commonly add their own "allow" rule the first time they bind —
so the firewall is a backstop, not a reason to bind `0.0.0.0`.

---

## It is now enforced, not just documented

A doc nobody re-reads stops working the day it is written. Two gates run on every commit:

```
git config core.hooksPath .githooks    # already set here
```

**`.githooks/pre-commit`** runs `python -m core.bind_guard --staged` and then hands off to
shazam's own hook. A staged file that binds the whole network is **refused**, with the file,
the line, and what to write instead.

**Why it lives in `.githooks/` and not `.git/hooks/`:** `.git/hooks/pre-commit` is owned and
rewritten by shazam, so a check added there vanishes on the next reinstall. `.githooks/` is
tracked in git, survives that, travels to any clone, and *delegates* to shazam so nothing is
lost.

**The escape hatch.** Exposure is allowed — it just has to be a sentence somebody wrote:

```python
app.run(host='0.0.0.0')   # bind-public: staging box, firewalled, ticket CH-402
```

The marker covers **one statement**, on its own line or in the comment block above it. It
does not silence a file.

Run it yourself any time:

```bash
python -m core.bind_guard
```

## And every commit now says who wrote it

**`.githooks/commit-msg`** requires one trailer:

```
Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
    or
Agent: pi-haiku-fleet
```

**Why:** when two exposed servers turned up, the obvious question — *"which AI did that, so
I can avoid it?"* — was **unanswerable**. Every agent commits under the same git identity and
only Claude Code was adding a trailer, so the history could say what changed and never who
changed it.

Genuinely automated commits (`Merge`, `Revert`, `fixup!`, `chore: auto-flush`) are exempt —
but the hook **announces** the exemption rather than passing silently, because a quiet
exemption is how the gap comes back.

## What the guard found that four manual sweeps did not

`core/ds4_brain.py:36` — a DS4 server launched with `--host 0.0.0.0` inside an f-string.
Greps missed it; the guard caught it on its first run. It is a legitimate case (the server
runs inside WSL2, which has its own network namespace) so it now carries a `bind-public`
marker **with the reason** — which is the whole point: the exposure is now something someone
decided, not something nobody saw.
