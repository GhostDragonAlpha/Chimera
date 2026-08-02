# tb-0019 — Pain verdict: distiller token-coverage false-suppression

<!-- CHIMERA-LAW -->
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
> **[docs/THE_LAW.md](../../../docs/THE_LAW.md)** · full method: `Chimera/docs/EXPERIMENTAL_METHOD.md`
> · enforced by `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

**Pain** (`phase_da55128aec6d109a:P1`, aged 6d): *"Distiller token-coverage will
false-suppress genuinely new lessons once PENDING_HEURISTICS.md grows large —
watch for repeat failures that never re-stage."*

**Verdict: REFUTED** (2026-07-13, agent opus-cycle). The predicted mechanism was
the OLD behavior and has been eliminated by a targeted per-entry "saturation fix"
in `core/heuristic_distiller.py::coverage_check`.

## Why the pain WAS real (old behavior)
The old coverage test summed token presence over the ENTIRE source text. Since
`PENDING_HEURISTICS.md` is both a coverage source AND the distiller's own append
target, the token union grew monotonically as the corpus grew, so eventually any
3-4 common game-dev words were "present" anywhere and a genuinely-new lesson was
false-suppressed.

## Why it is refuted now (current code)
`coverage_check` (heuristic_distiller.py:140-174) judges coverage PER-ENTRY: a
lesson counts as covered only when ≥80% of its distinctive whole-word tokens
CO-OCCUR within a SINGLE line/entry (`for line in text.splitlines(): if
len(sig_tokens & _tokens(line)) >= threshold`). Adding unrelated entries can
never raise a candidate's apparent coverage — coverage is independent of corpus
size.

## Evidence (empirical, run against the LIVE 160,347-char corpus, 4 sources)
Novel signature: `surprise: telemetry footstep material shovel economy faction
docking beacon` (9 distinctive tokens).

| Metric | Result |
|---|---|
| Tokens present SOMEWHERE in corpus (old whole-doc metric) | **8/9** |
| OLD logic verdict (threshold 80% = 7) | **COVERED — false-suppress!** |
| NEW `coverage_check(novel)` | **`''` — NOT covered (correct)** |
| Control: real duplicate `surprise: beat discovered expected gap` | **`'PENDING_HEURISTICS.md'` — covered (correct)** |

The exact failure the pain predicted (8/9 tokens scattered across a large corpus)
does NOT suppress under current code, while a genuine duplicate is still caught —
so the fix eliminated the false-suppression without weakening real coverage.

## Frame audit
- **Target, not proxy**: ran the actual `coverage_check` against the actual live
  corpus — not a stand-in.
- **Who judged**: deterministic function + the empirical contrast above (re-runnable).
- **Generator vs artifact**: N/A — a verdict task; the fix already lives in the code.

## Residual note (not the pain, but adjacent)
The whole-document path survives only as a long-exact-phrase check (needle >8
chars, line 164) — that matches genuine duplication, not token saturation, so it
does not reintroduce the failure.
