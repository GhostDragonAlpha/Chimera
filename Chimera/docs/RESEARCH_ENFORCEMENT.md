> **DEPRECATED** — This document describes the old approach.
> Read `AGENT_ONBOARDING.md`, `DECISION_METHOD.md`, and `EMERGENT_WORKFLOW.md` instead.
> The thought chain is at `docs/THOUGHT_CHAIN.md`.

# Research Enforcement — Proof-of-Use

> Enforced at the Pi harness, not requested in prose. An agent may not write an
> engine API call it has not read, may not write a call that does not exist, and
> may not leave a file on disk that will not compile.

## The problem this exists to solve

The agents were not refusing to research. **Their research tools were broken and
failed silently, and nothing downstream could tell the difference between
"researched and found nothing" and "the tool is dead."**

Measured 2026-07-10, not assumed:

- `.pi/extensions/web-browsing.ts` → `web_browse` closed over `params` inside
  `page.evaluate()`. That callback is serialized into the browser, where `params`
  does not exist. **Every call threw `ReferenceError` before reading a byte**, and
  the `catch` turned it into a calm sentence the model read and shrugged at.
- `web_search_real` scraped Google's `div.g`. Headless, realistic UA: HTTP 200,
  zero matches, page title is the raw URL — a bot wall. It returned an empty list
  with `status: "success"`.

So an agent could "research" all day and receive nothing, worded as success. Then
it would write from memory — and memory produced things like a comment reading
`// Measure current capsule half-height for verified crouch mechanics` sitting
above a line that measured the capsule *radius* on the wrong component. Every
mechanical gate passed it. (See the still-live bug in
`Source/Chimera/ProceduralGenerated/Demo/DemoPlayerController.cpp`.)

This is the failure named in **"Proof-of-Use: Mitigating Tool-Call Hacking in Deep
Research Agents"** (arXiv:2510.10931): rewarding the tool *call* rather than its
*use* produces hallucinated tool use — the call is made, but the reasoning chain
has no causal dependence on what came back. And it is the failure named in the
self-critique literature: an actor and a critic that share a model family agree on
wrong answers, which is why a system that grades its own output (this project's
`result_grader`, `collapse_proxy`, sleepwalker) can report a 2.02 GPA over
features that don't work.

## The fix: three external gates, none of which ask the agent how it did

Every check is performed by something the agent did not write — ripgrep, the
filesystem, the engine source on disk, ultimately the build. None consults the
model's own judgment.

```
  1. SYMBOL GATE    (tool_call, before write)   you may not WRITE a foreign API you did not READ
  2. INCLUDE GATE   (tool_result, reverts)      what you wrote must RESOLVE
  3. THE BUILD      (existing gate_build_succeeded)   what resolves must COMPILE
```

Each gate catches what the one above it cannot. The symbol gate cannot tell
`SetCrouchedHalfHeight` from a plausible-looking wrong call — but the include
gate catches the fabricated header the wrong call dragged in, and the build
catches the rest.

### Gate 1 — the symbol gate (`.pi/extensions/proof-of-use.ts`)

Before any `write`/`edit` into `Source/**/*.{h,cpp,inl}`:

1. Extract the API symbols the change **introduces** — methods invoked (`->m(`,
   `.m(`), scope calls (`Super::BeginPlay`), and Unreal-conventioned type names
   (`UCapsuleComponent`). Comments and string literals are stripped first: **a
   comment claiming "verified" proves nothing.**
2. Keep only the **foreign** ones — not defined in the incoming text, not defined
   anywhere in this project's own `Source/`. Everything foreign needs evidence.
   A hallucinated name is foreign, exists nowhere, and so can never obtain a
   citation — which is how invented API calls are caught rather than exempted.
3. Each foreign symbol must appear in a **citation that re-verifies right now**, by
   re-reading the engine source. No citation → **the tool call is blocked** and the
   unproven symbols are named.

A citation is a reproducible read, not a URL:

| kind | locator | verified by |
|---|---|---|
| `engine` / `repo` | absolute path + line | re-read the file; the quote must still be there (drift is reported, not tolerated) |
| `web` | url + sha256 | re-read the on-disk snapshot; its bytes must hash to the stored sha256 and contain the quote |

Citations accrue in `docs/research/ledger.json` from three sources: the
`research_engine` tool (greps engine source, auto-cites every hit), the
`research_cite` tool (records a web quote you actually retrieved, snapshotting the
page), and passive harvest of the builtin `grep` tool when it runs over the engine
tree.

**A blocked write hands over the evidence.** Refusing while only saying "go read the
source" is a hang — the agent reissues the same write forever (observed live). So
on block the gate performs the engine read itself, returns the actual source lines
in the refusal, records them as citations, and lets the informed retry through. A
strike counter halts anything that repeats 3× on the same symbols.

### Gate 2 — the include gate (`tool_result`, reverts)

Proof-of-use guarantees *retrieval*, not *comprehension*. Measured live: given the
crouch task, the model read `SetCrouchedHalfHeight(40.0f)` out of the engine, took
the `40.0f`, ignored the method, hand-resized the capsule anyway, and wrote
`#include "Bend.h"` for a header that did not exist. Every citation verified. The
file would not compile.

Nothing that reads the diff catches that — the diff looks reasonable. So after a
guarded write lands, an external oracle speaks: **does every `#include "..."`
resolve to a real file** under the project or engine source? (A `.cpp` may include
its own not-yet-written `.h`; `.generated.h` is UHT's.) If not:

- The write is **reverted** — a new file is deleted, an overwrite is restored to
  its prior bytes (snapshotted in the `tool_call` handler before the write landed).
- The agent is told, in the preprocessor's voice, which include failed.

A gate that only *reports* the bad file and leaves it on disk is a smoke alarm —
the same self-report failure in new clothes. This one removes the artifact.

### Gate 3 — the build

Already exists as `gate_build_succeeded` in the pipeline. Gates 1–2 exist so the
build is not the *first* thing to notice a problem the agent already had the
evidence to avoid.

## Fail closed

If the verifier cannot verify — ripgrep missing, or no engine-source root exists —
guarded writes are **blocked**, not waved through. Found by test: one nonexistent
subtree in the search path made ripgrep exit 2 on every call, silently disabling
the entire gate. A gate that fails open is worse than no gate: it reports a safety
it is not providing. Escape hatch, to be set consciously:

```
CHIMERA_PROOF_OF_USE=0   # gate becomes advisory (still records, never blocks)
```

## What it does NOT do (stated, not hidden)

- **It does not verify correctness.** Gate 1 proves a symbol was read; it cannot
  prove the *right* symbol was chosen. Only a running build and a behavioural test
  prove `SetCrouchedHalfHeight` was called on the right object with the right value.
- **Scope-call under-blocking is possible** for exotic qualifier forms; the common
  `Super::` / `UClass::` cases are handled.
- **Cross-file ping-pong is not strike-counted.** The counter resets per file, so a
  weak model oscillating `.cpp ↔ .h` can spin until the session's wall-clock cap.
  Observed live. "Produces nothing" still beats "produces a broken file it reports
  as done."
- **It is a Pi-side harness.** It gates the Pi agent's `write`/`edit`. It is not
  wired into `core/gates.py`.

## Verification status

- **28 harness cases pass** (`.pi` extension loaded via jiti, fresh ledger per case
  so auto-cited symbols cannot leak between tests). Cases include: uncited call
  blocked by name; allowed after `research_engine` retrieves it; comment cannot
  launder an uncited call; `Super::BeginPlay()` caught while its own definition is
  not; invented symbol never unblocks and halts the loop; missing include reverts a
  new file / restores an overwritten one; fail-closed on missing engine root.
- **Verified live** against a local LM Studio model (Pi headless, hard-capped,
  structured event stream): a forced write with a missing header was reverted on
  every attempt; the `Source/` tree ended **empty**, confirmed by reading the disk
  rather than a status line. Contrast the first live run, before Gate 2, which left
  a non-compiling file with a fabricated class on disk.

## Files

| File | Role |
|---|---|
| `.pi/extensions/proof-of-use.ts` | Gates 1 & 2, the ledger, `research_engine` / `research_cite` tools, `/proof` command |
| `.pi/extensions/web-browsing.ts` | Repaired `web_browse` / `web_search_real` (startpage primary, bing fallback; zero results is an error) |
| `core/research.py` | Standalone Python equivalent — engine/repo/web citations + `gate_research_grounded`, usable by the pipeline with no agent present |
| `docs/research/ledger.json` | The citation ledger (accrues at runtime) |
| `docs/research/snapshots/*.txt` | Web-page snapshots, named by sha256, for offline re-verification |
