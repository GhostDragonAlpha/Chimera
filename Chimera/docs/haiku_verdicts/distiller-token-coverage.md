# Phantom-Pain Verdict — Distiller Token-Coverage Saturation

**Pain id:** `phase_da55128aec6d109a:P1` (aged ~6 days)

**Pain (quoted):**
> "Distiller token-coverage will false-suppress genuinely new lessons once coverage saturates."

**Context:** `core/heuristic_distiller.py` clusters failures/surprises into candidate
heuristics nightly and uses a token-coverage test to decide whether a new lesson is
already covered by the constitution (dedup). The fear: once enough heuristics exist,
the overlap test matches almost anything, so genuinely NEW lessons get wrongly
suppressed as "already covered."

---

## VERDICT: confirmed

The suppression logic is a whole-document bag-of-words membership test with a
threshold proportional only to the *candidate's own* token count, run against
coverage sources that **grow monotonically**. There is **no novelty guard**. As the
constitution saturates, the probability of false-suppression rises monotonically —
exactly the predicted failure. Two independent amplifiers make it worse than the pain
assumed.

---

## EVIDENCE

### 1. The suppressor is a whole-document token-membership test (not per-heuristic)
`coverage_check` — `core/heuristic_distiller.py:129-146`:

```python
sig_tokens = _tokens(signature)                       # 133
...
text = src.read_text(encoding="utf-8", ...).lower()   # 138  ENTIRE file
...
# token coverage: >=3 distinctive tokens present in one source
if sig_tokens and len(sig_tokens) >= 3:               # 142
    hits = sum(1 for t in sig_tokens if t in text)    # 143  substring vs WHOLE doc
    if hits >= max(3, int(len(sig_tokens) * 0.8)):    # 144
        return src.name                               # 145 -> SUPPRESSED
```

`text` is the *full* lowercased source file (line 138), so a candidate is judged
"covered" when ≥80% of its tokens each appear **somewhere** in the document — not
when any single existing heuristic actually covers the lesson. This is even more
permissive than the pain's assumed "pairwise vs each heuristic": a pairwise check
would require the matching tokens to co-occur inside *one* heuristic; the implemented
token-*union* lets them be scattered across dozens of unrelated entries.

### 2. Coverage sources grow monotonically — the saturation driver
`COVERAGE_SOURCES` — `core/heuristic_distiller.py:33-38`:

```python
COVERAGE_SOURCES = [
    CHIMERA_ROOT / "docs" / "PENDING_HEURISTICS.md",   # 34
    CHIMERA_ROOT / "docs" / "MCP_PATHWAYS.md",         # 35
    CHIMERA_ROOT / "core" / "gates.py",                # 36
    CHIMERA_ROOT / "CLAUDE.md",                         # 37
]
```

- `CLAUDE.md` currently carries **20** auto-promoted heuristics (H-1…H-35) *plus the
  entire project manual* — thousands of tokens, and it only grows as heuristics
  promote.
- `PENDING_HEURISTICS.md` currently holds **35** candidate entries (`## H-N`) — and
  is `COVERAGE_SOURCES[0]`, i.e. it is *both* a coverage source *and* the file this
  same script **appends to** at `core/heuristic_distiller.py:311`
  (`PENDING_PATH.write_text(pending_text, ...)`, `PENDING_PATH` == `COVERAGE_SOURCES[0]`).
  Every night's staged candidates enlarge the very corpus that suppresses tomorrow's.

As these files grow, the union of tokens present *somewhere* in each file grows
monotonically, so the chance that ≥80% of a new candidate's tokens are each present
rises with every accumulated heuristic. That is the saturation mechanism, verbatim.

### 3. The threshold does not account for corpus size — and candidate signatures are tiny
`max(3, int(len(sig_tokens) * 0.8))` (line 144) scales with the *candidate's* token
count, never the source's. Surprise signatures are capped at 4 tokens
(`core/heuristic_distiller.py:105-106`: `sorted(_tokens(...))[:4]`), so a typical
signature yields ~4-5 distinctive tokens and the bar is just **3-4 common words
present anywhere**. In a saturated `CLAUDE.md`, generic game-dev vocabulary
(`verify`, `component`, `spawn`, `telemetry`, `beat`, `pawn`, `input`, `actor`,
`asset`, `log`) is guaranteed present — so a genuinely new *combination* of those
words is falsely marked covered.

### 4. Substring matching (not word-boundary) is a second amplifier
Line 143 uses `t in text` — Python substring containment, not whole-word matching.
`_tokens` admits tokens ≥3 chars (`core/heuristic_distiller.py:46-47`,
`[a-z0-9_]{3,}`). So `log` matches "back**log**", "cata**log**", "dia**log**",
"**log**ic"; `spawn` matches "**spawn**ed", "re**spawn**"; `act` matches
"**act**or"/"**act**ion". This inflates `hits` independently of corpus growth,
lowering the effective bar further.

### 5. No novelty guard anywhere in the path
The staging loop — `core/heuristic_distiller.py:260-269` — calls only
`coverage_check` (token test) and an exact `c["signature"] in pending_text` check.
There is **no** "minimum NEW tokens not already present," **no** novelty score,
**no** per-heuristic co-occurrence requirement, and **no** normalization for source
size. The only natural escape is a degenerate signature with <3 distinctive tokens
(the `len(sig_tokens) >= 3` guard at line 142) — which real, informative lessons
essentially never are. `conflict_check` (lines 149-163) only *annotates* staged
entries; it never rescues a candidate already suppressed by `coverage_check`.

---

## Why not "refuted"
The `needle` branch (line 139, `len(needle) > 8 and needle in text`) is a *stricter*
exact-substring path, but it is OR-ed *ahead* of the loose token test — it is an
additional way to suppress, not a guard that prevents the token test from
false-firing. No other code path caps corpus influence or measures novelty.

## Why not "still-open"
The mechanism is fully visible in-code and deterministic (zero LM). Every element the
pain predicted is present and load-bearing: (a) overlap tested against the growing
heuristic corpus, (b) a fixed proportional threshold, (c) no novelty guard. The only
correction to the pain's framing makes it *worse*, not uncertain: the check is a
token-*union* over the whole document, more saturating than a pairwise comparison.

## Suggested remedy (for the fix agent, not applied here)
Replace whole-document membership with **per-heuristic-entry** matching (tokens must
co-occur within one existing heuristic block), add a **novelty floor** (require ≥N
candidate tokens absent from every covering entry), and switch `t in text` to
**word-boundary** matching so `log` no longer matches `backlog`.

---

DISPOSITION: phase_da55128aec6d109a:P1:confirmed
