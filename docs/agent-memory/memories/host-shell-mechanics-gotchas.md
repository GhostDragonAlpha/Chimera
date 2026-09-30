---
name: host-shell-mechanics-gotchas
description: Windows host shell mechanics gotchas for ZCode on the Chimera
  project — Git Bash mangles $ in inline powershell, PS false-fails on stderr,
  background git exit codes lie; verify state not exit codes
metadata:
  node_type: memory
  type: project
  originSessionId: sess_081be23e-8020-40ac-8e60-f794c761196d
---

Mechanics traps hit repeatedly on this Windows host (ZCode's Bash tool is Git
Bash; the operator mandates PowerShell-only mechanics):

1. **Inline `powershell -Command "…$_…"` silently breaks**: Git Bash expands
   `$_`, `$env:TEMP`, `$e`, `$z` etc. BEFORE PowerShell sees them (errors like
   `The term ':TEMP\...' is not recognized`, missing method arguments). Any
   inline PS command containing `$` must instead be a `.ps1` file written via
   the file tool and run with `-File` (forward-slash path — backslashes are
   also eaten). Plain git/status one-liners are safe inline.
1b. **Installed Chrome 153 on this machine BROKE for all real navigation
   (2026-09-20, mid-session onset)**: chrome.exe and chrome-headless-shell
   hang on every real network target (loopback AND external HTTPS) — requests
   sent, response headers never arrive — while about:blank and instant
   pre-connect rejections (ERR_UNSAFE_PORT) still work. NOT proxy (env empty,
   WinINET ProxyEnable=0, no Chrome policies) and NOT fixed by
   `--no-proxy-server`/`--proxy-bypass-list`. curl/Node reach the same servers
   in ~2 ms. THE ESCAPE: Playwright's BUNDLED chromium (`launch({headless:true})`,
   no channel), optionally canary-gated (try channel 'chrome', fall back,
   record the deviation — the stranger lane's F-ENV-CHROME pattern); for WebGL
   pages add `--enable-gpu --enable-unsafe-swiftshader` or the page's GL
   context falls to software-WebGL (rbmovie finding). Triple-evidenced
   (lead probe pair, rbmovie finding #3, stranger netlog matrix) and pinned in
   E:/ChimeraWork/lane-archive/MACHINE_FINDINGS.md — READ THAT FILE before
   diagnosing any host-level failure >10 min.
2. **PowerShell reports exit code 1 on successful commands**: PS wraps native
   stderr as `NativeCommandError`; `python -m unittest` (writes progress to
   stderr) and `git checkout` messages routinely "fail" with exit 1 while the
   output says OK. Read the output; do not trust the exit code.
3. **Background `git clone … | Select-Object -Last N` exits 1 despite a
   complete clone** (the truncating pipe kills the upstream process). Verify
   with `git rev-parse HEAD` / `git status` instead of re-running.
4. **`git show origin/master:path` mangled when run inline through Git Bash**
   (`origin/master:path` becomes `origin\master;path` → "ambiguous argument").
   Quote the rev:path string or run it inside a .ps1.
5. **Harness background-task logs can capture only the TAIL (observed a
   638-byte log for a multi-minute suite run)** — grep for gate lines may find
   nothing even though the run completed. The exit code of the background
   command is the verdict; read artifacts (receipts, store files) for numbers
   instead of trusting the log to hold them. And per the operator's repeated
   ultimatum: check background output by reading the log FILE with
   PowerShell (`Get-Content`), never by block-waiting on the task.
6. **`git merge -X ours` + `git add -A` can commit a PARTIAL merge** (2026-09-18,
   trust-tooling lane): the merge commit carried only the 2 conflicted graph
   JSONs while the lane's 13 new files never left the branch — the funnel
   suite caught it via ModuleNotFoundError on the lane's test module. After any
   conflicted merge, `git diff --stat HEAD origin/<lane>` for the lane's key
   files; missing ⇒ `git checkout origin/<lane> -- <files>` completion pass.
7. **`git add -A` also happily commits CONFLICT MARKERS** in files the -X
   strategy didn't auto-resolve (2026-09-18, wave2 lane: `<<<<<<< HEAD` blocks
   survived into build_graph.py and only py_compile caught them). After a
   conflicted merge: `grep -rn "<<<<<<< " tools/` and/or py_compile every
   touched .py BEFORE running tests; some blocks need a MANUAL merge when both
   sides rewrote the same block differently.
8. **Lane worktrees cloned from other worktrees inherit the wrong origin**

9. **Installed Chrome is LOOPBACK-BLOCKED on this machine (2026-09-20, TRIPLE-evidenced by three independent lanes):** Playwright `channel:'chrome'` headless cannot reach 127.0.0.1 at ALL — `page.goto` times out on every route even with `--no-proxy-server` and `--proxy-bypass-list=*` (the browser never receives the response; request logged, no response event), while `curl` gets the page in 1.7 ms and **playwright's BUNDLED chromium (no `channel`) returns 200 in the same probe pair**. No proxy env vars, WinINET ProxyEnable=0, no Chrome policy registry keys — a per-app block on chrome.exe itself (anti-cheat/VPN-class driver suspicion, unproven). Corroboration: the rbmovie lane measured it independently ("real Chrome lost the ability to navigate ANY http URL mid-lane; data URLs alive, network dead; bundled chromium navigates") and the stranger lane hit it too, then shipped the REPO PATTERN: a launch-time channel CANARY (probe installed Chrome; on failure fall back to bundled) recorded as its F-ENV-CHROME falsifier. FIX for any localhost page automation: `chromium.launch({headless:true, args:['--no-proxy-server', ...]})` WITHOUT channel — or copy the canary. NOTE the GPU wrinkle (rbmovie): bundled chromium needs `--enable-gpu --enable-unsafe-swiftshader` or the page's WebGL context falls to software-WebGL and dies. `about:blank` works in installed Chrome — only network fails. Evidence pair + FINDING_chrome_loopback.md in E:/ChimeraWork/buffy-stranger-20260920/.../slice_stranger_20260920/. **SHARED HOME (2026-09-20): E:/ChimeraWork/lane-archive/MACHINE_FINDINGS.md is the append-only machine-findings file (newest first) — every lane reads it BEFORE diagnosing host-level weirdness, and every host-level discovery gets pinned there with finding/evidence/escape so no lane re-pays the diagnosis cost (the chrome breakage cost three lanes before the file existed). Bake a pointer to it into any prompt whose lane touches browsers or host mechanics.**

10. **The rule-1 `$`-eating trap recurred on the LEAD itself (2026-09-20):** an inline `powershell -Command "...Get-NetTCPConnection... $c ..."` produced cascading parser errors — exactly gotcha 1, violated while diagnosing another problem. The rule is absolute even mid-diagnosis: ANY inline PS containing `$` → stop, write the .ps1, run with -File. Self-observed failure mode: the trap bites hardest when attention is on the diagnosed problem, not the mechanic.

   (Buffy wave2: origin pointed at the wave-1 worktree path, so its first
   push created the branch THERE instead of GitHub). Verify `git remote -v`
   shows the GitHub SSH alias before trusting any lane worktree's push target.
9. **MorphoSource's Anubis bot wall blocks ALL automated access** (2026-09-19,
   confirmed by direct computer-use browser session): clicking, JSON API
   (`.json` returns HTML), and CSV export all fail or redirect. The search
   DOES work visually in a real browser but download buttons don't fire from
   automated clicking. This is a permanent manual-only path — never spend
   turns trying to automate MorphoSource.
10. **`git checkout --ours` on graph stores silently discards lane-side work
    records** (2026-09-19): the merge scripts' `--ours` checkout of
    project_program.json reverts to master's version which lacks the lane's
    admission records; `git add -A` stages only the resolved conflicts,
    making the merge look clean while dropping content. Always verify work
    records exist after integration (`CreatureGraph.load()` + check record
    IDs); fix = explicit `git checkout origin/<lane> -- <file_list>` +
    re-run the lane's admission script.
11. **The engine's boot-restore thread races the first capture** (2026-09-20,
    workflow-mcp lane): `/cameras {"op":"fit"}` fires ~1.5–3.5 s after boot and
    overwrites a posted camera — the first frames come from the WRONG camera,
    reproducibly. Launch with `[exe, port, --no-restore]` (argc==3 is safe on
    master's argc-guarded window read); post-fix, probes match the projection
    model to ≤1 px. Any lane driving the engine programmatically uses
    --no-restore + its own camera posts.
12. **E: fills up under the lane fleet; worktree chains make pruning unsafe
    until mirrored** (2026-09-20/21): the 1.9T drive hit 100% mid-campaign
    (wave-25 could not make a full clone and had to `--shared` sparse-clone,
    excluding docs/ and Saved/). The lead freed 87G by deleting the
    disposable verification clones (~15G each — clone-fresh, verify, DELETE is
    the pattern; never let .verify accumulate). The lane worktrees themselves
    chain origins (lane N pushes to lane N−1's worktree), so deleting a
    finished worktree can LOSE branch refs that exist nowhere else — mirror
    all branches to the canonical origin and verify ref-hash equality BEFORE
    any pruning (the lane-mirror agent's protocol).

13. **Rapid-fire per-directory `git ls-remote` over the SSH alias THROTTLES and
    silently returns empty** (2026-09-21, fast-prune): a prune script doing one
    `ls-remote` per worktree (14 in rapid succession) had its FIRST call succeed
    and the rest fail → every later worktree was falsely spared as
    "BRANCH_NOT_ON_CANONICAL" (all 11 were in fact pushed — proven by recheck).
    The fix: ONE `git ls-remote <url> ref1 ref2 …` for all refs in a single
    connection, parse the table, compare locally; bake the verified tips into
    the deletion script so it needs no network at all.

14. **Deriving a script by `-replace` string surgery on a working script breaks
    parsing silently** (2026-09-21, batch_prune_local): swapping the source
    command from `git ls-remote` (SHA-first, TAB-separated) to
    `git for-each-ref` (REF-first, SPACE-separated) while keeping the old
    parser loaded 0 refs — the script then "verified" every worktree against
    an empty table (safe but useless; the pass deleted nothing). Write such
    scripts clean, and ASSERT the sanity count ("refs loaded: N") — abort if
    N=0 — before running any gate that consumes the table. Offline
    alternative when auth is dead: a recent clone's
    `refs/remotes/origin/*` is a valid canonical snapshot (for-each-ref
    locally, no network).

15. **Session goals live in the client SQLite store (2026-09-28)**:
    `C:/Users/allen/.zcode/cli/db/db.sqlite` → table `session_target`
    (session_id, target_id, objective, status, token_budget, tokens_used,
    time_used_seconds); the runtime's goal reminders restore from there, and
    goal text otherwise appears only in the rollout jsonl transcript. A direct
    `UPDATE session_target SET objective=? WHERE target_id=?` rewrite worked
    (goal replaced on Captain order, read-back verified) — the supported way
    to "delete and rewrite" a session goal when the Captain asks.

**Why:** these three produced several false failure reports and one aborted
command chain in the intake-muscle lane before the pattern was pinned.
**How to apply:** mechanics go through .ps1 files (matches the operator's
PowerShell-only ultimatum, see [[alan-operator-preferences]]); treat exit
codes as hints and stdout/stderr text as the verdict; verify repo state after
any clone/checkout that "failed". Related: [[chimera-fleet-lead-runbook]],
[[batch-intake-lane-2026-09-17]].
