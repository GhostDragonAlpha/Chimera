# FIRST-SKILL TRIGGER RUNBOOK (skill-1: FLAT-GROUND GOAL TRACKING)

Prestaged 2026-09-22 by `agent/first-skill-prestage-20260922` @ 73f3a860.
Execute the hour the GPU environment's first tick lands. ZERO decisions remain:
everything below is frozen in `run_manifest.json` (same directory). Any change
to a frozen field is a NEW registration, never an amendment.

## Inputs (all frozen, all at 73f3a860 or later pins)

| Piece | Where | Status |
|---|---|---|
| Run manifest (prereg) | `tools/science_funnel/validation/first_skill_prestage_20260922/run_manifest.json` | FROZEN |
| Reward (shaping only) | `tools/science_funnel/first_skill/reward.py` | FROZEN, tested 19/19 |
| Scripted baseline | `tools/science_funnel/first_skill/baseline_controller.py` | FROZEN, tested |
| Acceptance + ranking | `tools/science_funnel/first_skill/acceptance.py` | FROZEN, tested |
| Obs schema v2 (80ch) | `tools/science_funnel/typeb_export/observation_schema.py` | SHIPPED 73f3a860 |
| Export harness | `tools/science_funnel/typeb_export/` (1b6d7749) | SHIPPED |
| Command adapter | `commanded_target_velocity_x` via `GaitWalker::configure` (9808dc94) | SHIPPED |

## Step 1 -- GPU env (`FirstSkillGoalEnv`)

Build the batched env exactly per `run_manifest.json` § `gpu_env_contract`:
gait_unit bodies at 300 Hz + the adapter channel, decisions every 15 ticks,
obs = 80 v2 channels + 2 goal channels (`goal_dist_norm`, `goal_closing_speed_norm`),
action dim 1 mapped `(tanh(u)+1)/2 * 0.7636247890` into `commanded_target_velocity_x`.
Episode: one waypoint dead ahead at `d_wp = 0.5 m`, cap 300 ticks, the engine's
own refusal classes terminate (never env-invented failures). Batch-isolation
fixtures per Astra F-BATCH-COUPLING. Invariants are falsifier-gated
(F-REFLEX-REGRESSION, F-CREDIT-BLOCKED via the F-G42 census).

## Step 2 -- Train (PPO, 3 seeds)

RSL-RL-style config, frozen in the manifest: 4096 envs x 24 steps, 10
iterations = 983,040 decisions/seed (the 1M pilot budget, floored to the
iteration grid), gamma 0.99, lam 0.95, clip 0.2, entropy 0.01, adaptive lr
1e-3 (KL 0.01), 4 minibatches, 5 epochs, seeds {20260922, 20260923, 20260924}.
Curriculum: NONE. Eval every 25,000 decisions on eval seeds
{20260922..20260926} with deterministic mean actions; return = the frozen
shaping sum. Wire the eval callback at the 25k decision grid -- framework
defaults do NOT set this cadence.

```
python tools/train_first_skill.py --manifest tools/science_funnel/validation/first_skill_prestage_20260922/run_manifest.json \
    --seed 20260922   # then 20260923, 20260924
```
(The trainer is the GPU-env lane's one new file; it reads the manifest and the
frozen modules above -- it invents no number.)

## Step 3 -- Select checkpoint (rule frozen in the manifest)

Best mean eval return among the LAST 10% of evals (evals 37..40 = decision
counts 900000/925000/950000/975000); ties to the EARLIEST. Selection is not
acceptance.

## Step 4 -- Export through P3's harness (F-EXPORT-VALID)

Build a `typeb_policy_manifest` with observation.dim 82, architecture
[82,128,128,1], action.dim 1 (clock 20/15/300, bounds [0, 0.7636247890]) --
validator-compatible with zero amendments (proven in the prestage tests).
Fixture set: the first 4096 observations of the selected checkpoint's eval
rollouts, digest-pinned. The export must replay those actions BIT-EXACTLY
(float32 bytes) from two fresh processes through
`tools/science_funnel/typeb_export/run_f_cpu_policy_bytes.py` machinery.
Any mismatch: F-EXPORT-VALID fires, carry it, do not tune.

## Step 5 -- Baseline first, then acceptance (F-ACCEPTANCE-EXACT, F-FIRST-SKILL)

On the CPU-exact engine (gait_unit + adapter): run
`baseline_controller.BaselineController()` (constant 0.60 m/s hold, the banked
R2 schedule) on the eval seed set FIRST; record reach rate, no-fall rate,
median time-to-waypoint, and the per-episode CoT band
(`acceptance.run_bars`) into the acceptance ledger. THEN evaluate the exported
policy on the identical set and apply `acceptance.first_skill_ranking`:
reach strictly greater, paired median time strictly less, no-fall == 1.0,
CoT within the measured band (`acceptance.cot_band_ok`). Hard conditions are
independent; there is no blended score anywhere. CoT = E_ledger/(13824.5 kg x
d_reached). If the scripted baseline matches the policy on every bar,
F-FIRST-SKILL FIRES and the record says so: passing the pipeline does not
establish learning was necessary.

## Report

All three seeds' curves, training cost, exported actors, CPU results,
requested-vs-applied command traces (never best-seed-only), receipt under
`tools/science_funnel/validation/` with the manifest hash restated verbatim.
