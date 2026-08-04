# Task 7 — Single-Rollout Judgment Audit (read-only)

## Method

Searched `tools/*.py` and `docs/*.md` for: single-rollout verdicts,
default seed counts, the `--seeds 1` backward-compat flag, and any place
a PASS/FAIL or score rests on one rollout rather than a multi-seed median.

## Where a verdict RESTS on one rollout (by default)

### Trainers that default to seeds=1 (single rollout)

Found via grep for the `seeds = ... else 1` pattern across tools/:

| File | Line | Default | Pattern |
|------|------|---------|---------|
| tools/train_stand.py | 316 | seeds=1 | `seeds = int(a[a.index("--seeds") + 1]) if "--seeds" in a else 1` |
| tools/train_walk.py | 292 | seeds=1 | `seeds = int(a[a.index("--seeds") + 1]) if "--seeds" in a else 1` |
| tools/walk_dyad.py | 304 | seeds=1 | `seeds = int(a[a.index("--seeds") + 1]) if "--seeds" in a else 1` |

### The single-rollout code path

In both trainers, when seeds <= 1, a SINGLE rollout with seed=0
(unperturbed initial condition) is used:

**train_stand.py:257-258:**
```
if seeds <= 1:
    s, tr, pics = evaluate(..., seed=0, ...)
```
Docstring (line 251): "seeds=1 REPRODUCES THE OLD BEHAVIOUR EXACTLY
-- seed 0, unperturbed, one rollout"

**train_walk.py:94-97:**
```
if seeds <= 1:
    s, tr, pics = evaluate(..., seed=0)
```
Docstring (line 90): "seeds=1 REPRODUCES THE OLD BEHAVIOUR EXACTLY
-- seed 0, unperturbed, one rollout"

### The verdict that depends on it

**train_stand.py:391 + :432:**
```
score_theta(m, d, mujoco, c, P, secs, seeds, joints=joints)
...
print(f"...  PROVEN" if ok else "not yet")
```
When seeds=1 (default), the "PROVEN/not yet" verdict rests on a single
seed-0 rollout. The verbose output at line 374 confirms:
```
+ ("  (seeds=1 -- the old single-rollout behaviour, reproduced exactly)"
   if seeds <= 1
```

**train_walk.py:366-368:**
```
score_theta(m, d, mujoco, theta_stand, c, groups, P, secs, seeds=seeds, ...)
```
Same pattern — passes seeds=1 to score_theta, which runs single rollout.
Line 349:
```
+ ("  (seeds=1 -- the old single-rollout behaviour, reproduced exactly)"
   if seeds <= 1
```

### Explicit --seeds 1 flag (opt-in single rollout)

| File | Line | Quote |
|------|------|-------|
| tools/f3_stand.py | 48 | `python tools/f3_stand.py --seeds 1  # the retired single-rollout behaviour, exactly` |
| tools/f4_walk.py | 40 | `python tools/f4_walk.py --seeds 1  # the retired single-rollout behaviour, exactly` |

Both default to SEEDS=10 (multi-seed), but `--seeds 1` reverts to single.

### Warning behavior when single-rollout is detected

| File | Line | Quote |
|------|------|-------|
| tools/f3_stand.py | 328 | `the min and the spread are printed with it, because one rollout is a coin toss.` |
| tools/f4_walk.py | 350 | `f"single-rollout is {(-dev):+6.1f}%"` — measures seed-0 deviation from median, only when nseeds > 1 |

When nseeds == 1, the deviation block is skipped (f4_walk.py:339:
`if nseeds > 1:`) — no warning emitted.

## Where the code CORRECTLY uses multi-seed (no finding)

| File | Line | Default | Pattern |
|------|------|---------|---------|
| tools/f3_stand.py | 79, 231 | SEEDS=10 | `nseeds = ... else SEEDS` |
| tools/f4_walk.py | 72, 223 | SEEDS=10 | `nseeds = ... else SEEDS` |
| tools/stand_survival.py | 106 | nseeds=10 | `nseeds = ... else 10` |
| tools/port_trainer.py | 105 | n_seeds=4 | WORST of 4, with robustness ratio |
| tools/grab_load_path.py | 180 | nseeds=10 | `nseeds = ... else 10` |
| tools/fall_exit.py | 169 | nseeds=10 | `nseeds = ... else 10` |
| tools/stance_choice.py | 130 | nseeds=10 | `nseeds = ... else 10` |

## Documented single-rollout risk in docs/

| Source | Line | Quote |
|--------|------|-------|
| docs/THE_LOCOMOTION_LANE.md | 95 | "Single-rollout numbers overstate by ~30%, so F3/F4 must headline median-of-10." |
| docs/CLAUDE_PROMPT_RUNG9.md | 91, 109-112 | "seed 0 (what this table reports) vs median of 10 vs min vs spread" |
| docs/CLAUDE_PROMPT_RUNG9.md | 112 | "And the cold A/B reverses under the median. Judged at ten seeds, the cold roll arm holds 4.95 s median ... single-rollout numbers had it ahead." |
| docs/THE_SLICE.md | 285-289 | "one rollout from one initial condition is a coin toss" |

## Verdict

| # | Location | Single-rollout verdict? | Mitigation |
|---|----------|------------------------|------------|
| 1 | train_stand.py:251,316,391,432 | YES — seeds=1 default | Docstring warns; caller can override |
| 2 | train_walk.py:80,292,349,366 | YES — seeds=1 default | Docstring warns; caller can override |
| 3 | train_walk.py:240 | YES — score_theta seeds=1 default | Function-level default |
| 4 | walk_dyad.py:304 | YES — seeds=1 default | Same pattern |
| 5 | f3_stand.py:48 | Only with --seeds 1 flag | Default is 10; warning printed when multi-seed |
| 6 | f4_walk.py:40,339-350 | Only with --seeds 1 flag | Default is 10; silent when single |
| 7 | docs/THE_LOCOMOTION_LANE.md:95 | Documents the risk | — |
| 8 | docs/CLAUDE_PROMPT_RUNG9.md:112 | Documents the reversal | — |
| 9 | docs/THE_SLICE.md:289 | Documents the risk | — |

**Three TRAINER functions default to seeds=1** (the actual training
loop verdicts). The JUDGE scripts (f3/f4) default to 10 seeds.
