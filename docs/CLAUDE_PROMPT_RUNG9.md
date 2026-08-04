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
