# The Taste System — and what to do when handed a completed taste file

A pure-Python subsystem (numpy only; no engine, no build). The operator authors a taste
reference — their **Will** — and the preference loop attunes to it. Files here:

- **`taste.json`** — THE LIVE WILL. Human-only-writable. The file the code reads
  (`core.taste.TASTE_PATH`). Starts blank (all weights 0 = no taste yet).
- **`taste.example.json`** — a blank, self-describing template.
- **`taste.seed.md`** — a prompt the operator plants in fresh, uncorrelated AIs to grow a
  `taste.json` draft by interview (their anti-bias method: no single AI shapes the reference).

---

## RECEIVING PROTOCOL — when the operator hands you a completed taste file

The operator grows their taste **outside** this project and hands you the result. When they do:

1. **Do NOT edit, "improve", tune, re-weight, or second-guess the taste.** It is the human's
   authored reference and the one thing an AI must never author — an LLM is never the taste
   terminal (`core/why.py`). Your job is only to **place, verify, and commit** it.
2. **Place it** at `docs/objectives/taste.json` (overwrite the blank starter). If they paste
   the contents, write them verbatim; if they give a file, copy it verbatim.
3. **Verify it loads — do not assume:**
   ```
   python -c "from core import taste; w=taste.load_will(); print(taste.will_to_prior(w)); print('composes:', taste.compose(w, []) is not None)"
   ```
   It must print the axes/weights the operator intended and compose without raising. **Show
   the operator the parsed weights and convictions so they confirm it is what they meant.**
4. **Commit it by-path and state the SHA.** It's a real project file; keep the tree clean.
5. **Changes later: you PROPOSE, they COMMIT.** `core.taste.propose_edit(...)` drafts a change
   staged to CAPCOM (`preference_select.propose_will_edit`). You never write `taste.json`
   yourself; the running system has no writer for it (enforced by `tests/test_taste.py`).

---

## What it drives once in place — and what it does NOT

- **Drives:** the taste decision in the preference loop. `preference_select.attune()` re-ranks
  the **physics-feasible** shortlist by the operator's taste and picks the preferred design.
- **Does NOT drive:** physics or feasibility (the trainer decides validity against the physics
  objectives), what gets trained, or anything else. Taste only selects among already-valid
  designs — it can't rescue an invalid one or stop a valid one from existing.
- **Does NOT run on its own yet:** `attune()` / `attune_and_surface()` are callable but nothing
  auto-invokes them after training. Auto-wiring into the circadian cycle is an unbuilt
  follow-up (say so plainly; don't imply it runs continuously).

---

## The composition (the order the reasoning places the context)

physics gates eligibility (`trainer` `top_k`, `score>0`) → the **WILL** is the prior
`N(w0, Λ0⁻¹)` → recorded `PreferenceObservation` comparisons are the likelihood → transient
chat is a weak Gaussian nudge (per-axis shift `c/(λ0+c)`, <1, shrinks with conviction so a
firm axis resists and a loose one yields) → decide by `w·φ` over eligible designs → CAPCOM
carries the frontier asks and any AI-proposed Will edits.

Every step is arithmetic on the human's numbers and measured facts. No LM judges.

---

## Module map (built 2026-07-22)

| File | Role |
|---|---|
| `core/taste.py` | the Will: load/compose (prior + comparisons + chat); `propose_edit` (draft only) |
| `core/preference.py` | `PreferenceModel` — Bayesian Bradley-Terry over the physics axes |
| `core/preference_elicit.py` | the ask-gate + active selection (BALD) |
| `core/preference_select.py` | attune-back (feasible shortlist → taste re-rank) + CAPCOM wiring |
| `core/graphify_interface.py` | `record_preference` / `PreferenceObservation` (the HUMAN taste terminal) |
| `core/trainer.py` | returns `top_k` (physics-feasible shortlist + measures) |
| `tests/test_taste.py`, `tests/test_preference_*.py` | proofs (86 checks) |
