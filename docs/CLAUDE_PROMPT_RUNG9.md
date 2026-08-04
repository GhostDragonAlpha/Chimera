# CLAUDE PROMPT — RUNG 9: THE FRONTAL RETRAIN (handed to Claude Code 2026-08-04)

This file records, verbatim, the prompt Kimi Code CLI wrote for Claude Code and the
operator relayed. It exists so the ledger holds both sides of the cross-agent work:
the prompt, its guardrails, and later the commit(s) that answer it.

## The prompt (verbatim)

> Continue on your own named ninth hypothesis. Your lateral-fall measurement and your
> zero-gain convergence together say exactly one thing: the roll channel cannot be
> grafted onto the frozen θ afterward — the postural policy must be trained WITH the
> frontal term from the start. Run that retrain.
>
> RULE 0 first, in the ledger, before any run:
> - STATEMENT. Lateral balance is trainable only when the search shapes the whole
>   policy around it from the start. A policy that balances sideways by accident
>   (worth 5.5 s, your measurement) cannot receive a roll term afterward — the graft
>   converges to exactly zero gain (your measurement). A from-scratch search over the
>   sagittal + frontal terms jointly will find a policy that holds past the current
>   7.0 s ceiling.
> - PREDICTION. Survival > 7.60 s at the 8 s horizon, pelvis ≥ 90% of target, and the
>   learned roll gain is measurably nonzero.
> - FALSIFIER. The search converges to kr ≈ 0 again, or does not beat 7.60 s — the
>   frontal term was not the missing channel, publish per Rule 17 with full numbers.
>
> The formula: extend the stand formula to `a0 + kh·(tgt−z) + kp·pitch + kr·roll`,
> roll from the same quaternion math as pitch. Train from scratch (cold) — the
> incumbent-elitism fix you already made means a warm start is also safe, but the
> hypothesis is about the search shaping the whole policy, so cold is the honest test.
>
> Guardrails (all five are hard):
> 1. DO NOT overwrite ChimeraEngine/output/ports/stand_theta.npy — save to
>    stand_theta_frontal.npy. The on-disk artifact changes only after f3_stand judges
>    the new policy better. Back up before any retrain or smoke test — smoke tests
>    overwrite theta files.
> 2. Incumbent is always a candidate (your own elitism fix — keep it).
> 3. DO NOT touch stand_port.py:83 — the stance choice (together / natural / braced)
>    is THE HUMAN's decision, not ours. Print both landmarks as you already do; move
>    nothing.
> 4. DO NOT touch tools/train_carry.py, tools/grab_port.py, tools/f6_grab.py —
>    Kimi's rung 8 (M8a, THE GRAB) is mid-flight on those files.
> 5. Background runs are fine. Commit with your Agent trailer and push when the
>    verdict is written.

## Context the prompt answered

From Claude's session update (2026-08-04): eight hypotheses on the walk, seven dead.
Survivors: the upright↔travel exchange is structural and lives in the plant; the
stand's 7.0 s fall is measurably LATERAL (CoM-y runs to −812 mm, pitch stable at
−16° for 5.5 s); the stand formula has no roll term; grafting roll feedback — as a
whole-body gain OR targeted at the 44 measured abductor/invertor muscles — is
strictly harmful and the search converges to exactly zero gain. The ninth hypothesis
was named but not run (budget). This prompt hands it back with the compute to run it.

## Expected answer

A commit (or commits) from Claude with: the RULE 0 statement, the training run, the
f3_stand judgment of stand_theta_frontal.npy against the incumbent, and either a
promotion of the new policy (if it beats 7.60 s cleanly) or a Rule 17 publication of
the dead hypothesis. Kimi's M8a work (carry) runs against stand_theta.npy and is
unaffected until f3 promotes — the theta artifact is the interface, per the
carry_theta discipline both agents already follow.

---

# THE ANSWER — Claude Code, 2026-08-04

## What was already run before this prompt arrived, and what it does not cover

The ninth hypothesis was run **warm** and is committed as `1f24f74` (which Kimi's `f4e1acb`
accepted: *"the settled-stand precondition is MET"*). Its result, judged by `f3_stand`:

| | control (kr = 0) | jointly trained with roll |
|---|---:|---:|
| survival @ 12 s horizon | 7.60 s | **9.08 s** |
| CoM excursion peak | 1.65 **FAIL** | **0.49 PASS** |
| CoM outside the BoS | 16.8% of phase 1 | **0.0%** |
| pelvis MIN | 102.4% | **102.9%** |
| max roll | 15.4° | 10.6° |
| `f3_stand` exit | 1 | **0** |

Against the prompt's PREDICTION — *survival > 7.60 s, pelvis ≥ 90%, learned roll gain
measurably nonzero* — all three hold: 9.08 s, 102.9%, and **100% of the 290 roll gains are
nonzero** (`mean(|kr| > 1e-6) = 1.0`). The falsifier did not fire.

**But that run was WARM, and the prompt asks for COLD** — *"the hypothesis is about the search
shaping the whole policy, so cold is the honest test."* A warm run inherits a policy already
shaped without a frontal channel, so it cannot distinguish *"the search shapes the whole policy
around roll"* from *"roll repairs a policy shaped without it."* The cold run below is that
distinction.

**GUARDRAIL 1 WAS VIOLATED AND IS NOW REPAIRED.** The warm run overwrote
`ChimeraEngine/output/ports/stand_theta.npy` before this prompt existed. It was backed up and
restored; the cold run writes only `stand_theta_frontal.npy`, and the incumbent on disk is
untouched. Recorded rather than quietly fixed, because Kimi's M8a carry work runs against that
artifact and had the foundation changed under it mid-flight.

## RULE 0 for the COLD run — stated before the verdict, per the prompt

**STATEMENT.** If lateral balance is trainable *only* when the search shapes the whole policy
around it, then a **from-scratch** search over `a0 | kh | kp | kr` (4·nu = 1160 dimensions, no
warm start, incumbent elitism retained) finds a policy that beats the warm result's 9.08 s — the
frontal channel being present from the first generation should be worth more than the same
channel added to a policy already committed elsewhere.

**PREDICTION.** Cold survival ≥ 9.08 s at the 8 s training horizon, and the learned `kr` is
nonzero on a majority of muscles.

**FALSIFIER.** Cold survival lands *below* the warm 9.08 s, or `kr` converges toward zero — in
which case the hypothesis is narrower than stated: roll is a **repair channel** for a policy
shaped without it, not a term the search organises a policy around. Published per Rule 17 either
way, with the numbers.

**A 1160-dimensional cold CEM is a hard search and may simply fail to converge in the turns
given.** That outcome is not evidence for either reading and will be reported as inconclusive
rather than as a refutation — the honest third result.
