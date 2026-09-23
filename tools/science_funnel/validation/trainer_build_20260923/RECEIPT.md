# TRAINER-BUILD RECEIPT (trainer_build_20260923) — falsifier prereg

Lane: TRAINER-BUILD (`Agent: trainer`), branch `agent/typeb-gpu-finish-20260922`,
worktree `E:/ChimeraWork/finish-agent`, base commit e3b591e1 (the lead's UCRT
work; walker_env.dll rebuilt 09:13 with the CRT math).

Frozen law consumed (bytes verified sha-identical to their pins):
- `tools/science_funnel/validation/first_skill_prestage_20260922/RUNBOOK.md`
  @ 8294053b (sha eb8d19a2... per the prestage receipt)
- `run_manifest.json` @ 8294053b (sha256 c85ba5c43aa7cf12969caf8df732dc77025bb1f50ab23ab87ed42685fe3ef39a)
- `tools/science_funnel/first_skill/{reward,baseline_controller,acceptance,__init__}.py` @ 8294053b (byte-identical copies landed in this tree)
- `tools/science_funnel/typeb_export/{observation_schema,body_velocity}.py` @ master (byte-identical copies landed in this tree)
- `tools/science_funnel/typeb_gpu/walker_env_host.py` + `walker_env.dll` (HEAD, UNTOUCHED — wrapped only)

## PREREGISTERED FALSIFIERS (declared 2026-09-23 BEFORE the build exists)

Each falsifier: STATEMENT / PREDICTION / FALSIFIER (fires when), with the
threshold fixed here before any measurement.

### F-OBS-FIELD21
- STATEMENT: the env wrapper's observation channel 21 (`com_vel_x_heading`,
  the body_velocity group's deciding scalar) is delivered LIVE from the env
  state every decision, per body_velocity.py's landed law
  (`com_vel_x(t) = (com_east(t) - com_east(t-1)) * 300.0`), not aliased.
- PREDICTION: over a 1000-tick run at tick granularity, channel 21 equals the
  independently recomputed first-difference velocity at every tick, and equals
  the engine's own velocity state `rb[:,2]` (v[3]) at every tick.
- FALSIFIER (fixed now): FIRES if, at ANY of the 1000 ticks,
  `|obs[21] - (com_east(t)-com_east(t-1))*300.0| > 1e-3` m/s
  OR `obs[21] != rb[:,2]` exactly (same array, must be exact).
  1e-3 m/s = 0.13% of v_seed: loose enough for the integrator's discretization
  order, tight enough to catch any alias (a wrong channel would miss by O(1)).

### F-REWARD-FROZEN
- STATEMENT: the trainer's ONLY reward source is the frozen
  `tools/science_funnel/first_skill/reward.py` (its `shaping()`), imported and
  called; no reward arithmetic exists outside it.
- PREDICTION: patching `reward.shaping` with a sentinel changes every non-dead
  reward the env produces; the trainer never computes reward locally.
- FALSIFIER (fixed now): FIRES if (a) any reward value the env produces over a
  5-decision probe disagrees with the sentinel-derived value, or (b) the env's
  reward path does not route through `reward.shaping`, or (c) reward arithmetic
  (`r_progress`/`r_heading`/clip/weight constants) is reimplemented in
  train_first_skill.py or the env wrapper.

### F-ACTION-MAP
- STATEMENT: the env's action-map layer is exactly
  `cmd = (a_norm + 1) / 2 * 0.7636247890` into `commanded_target_velocity_x`
  (set_command), with a_norm in [-1, 1] the post-tanh normalized action.
- PREDICTION: a_norm = +1.0 maps to exactly 0.7636247890; a_norm = 0.0 maps to
  exactly 0.3818123945; a_norm = -1.0 maps to exactly 0.0 (exact float
  equality: the halves are powers of two).
- FALSIFIER (fixed now): FIRES if any of the three exact equalities fails, or
  if the payload reaches the engine through any other channel or scaling.

### F-CLOCK
- STATEMENT: decisions are every 15 ticks (20 Hz policy over 300 Hz physics),
  command zero-order-held between decision boundaries, one command issue per
  decision.
- PREDICTION: on the live engine, after each of 20 consecutive decisions the
  per-env tick counter advanced by exactly 15 (20 x 15 = 300 = the episode
  cap), and the wrapper issued exactly one command per decision.
- FALSIFIER (fixed now): FIRES if any per-decision tick delta != 15, if 20
  decisions do not total exactly 300 ticks, or if the command-issue count per
  decision is not exactly 1.

### F-BATCH-COUPLING (manifest gpu_env_contract invariant; Astra fixture)
- STATEMENT: batch envs are isolated — an env's trajectory depends only on its
  own initial state and its own command, never on other envs' commands.
- PREDICTION: running E=4 envs with distinct held commands reproduces, per env
  and bit-exactly (float64 status), the trajectory of an E=1 run of the same
  command, over a full 300-tick episode.
- FALSIFIER (fixed now): FIRES if any env's `rb` status row at any decision
  differs bit-wise between the E=4 and the matching E=1 run.

### F-SMOKE
- STATEMENT: the full training loop (GPU env -> PPO update -> eval callback ->
  checkpoint) runs end-to-end at smoke scale: 2 iterations x 512 envs on ONE
  seed, per the runbook's smoke declaration.
- PREDICTION: 2 PPO updates complete; actor/critic/value losses finite; no NaN
  in any obs, action, reward, or loss; the eval callback fires (decision-0
  eval + the smoke's declared final eval) and a checkpoint is written.
- FALSIFIER (fixed now): FIRES on any NaN/Inf in obs/actions/rewards/losses,
  any uncaught exception, or a missing checkpoint/eval record.

## AMBIGUITIES READ, MANIFEST-FAITHFUL (named, not tuned)

1. OBS NORMALIZATION: the manifest pins obs = "80 v2 channels + 2 goal" but
   carries NO per-field norm table (that block belongs to the P3 export
   manifest, Step 4). Reading: training consumes the schema's DECLARED RAW
   units (schema per-field unit column); unavailable channels mean-fill 0.0
   with mask 0 (the schema's own convention); the export lane pins its norm
   block to match (mean 0 / std 1 pass-through) at Step 4. No norm constant is
   invented here.
2. "THE TRAINING ENV PROVIDES ALL 82 CHANNELS EVERY DECISION" vs the DLL's
   readback surface: walker_env.dll's `env_status` exposes rb(6)/rbi(6)/
   refused/refused_class/collapsed/ticks/cmd_fires/cmd_first_tick/hind_tds/
   fore_td_count. It does NOT expose the 6-slot paw census, foot forces, the
   8ch requested/applied vectors, limiter saturation, or pad gaps. The schema's
   availability law (mask 0, mean fill, never invent) and body_velocity.py's
   banked census (per-foot slots "STRUCTURAL on this body ... not delivered,
   never invented") are applied literally: fields the engine state determines
   are delivered live (gait sin/cos from phi, field 21 from the env's velocity
   state, intervention refusal flags from the engine's own refusal classes,
   clock fields from the wrapper's ZOH clock, mask aggregates); all others are
   DECLARED UNAVAILABLE. The mask is itself observed (fields 58/59). THIS IS
   THE ONE TEXT-VS-SURFACE GAP THE LEAD MUST ADJUDICATE before the real 3-seed
   run: either the runbook proceeds with the masked obs (this build), or a DLL
   v2 with a richer status readback is registered (engine lane, not this one).
3. CRITIC PRIVILEGED BLOCK: "true CoM pose, waypoint world coords" on the
   planar engine = (com_east, com_height, x_wp) -> critic input 85. No y-axis
   exists in the planar model to append.
4. POLICY NOISE STD: the manifest pins the reference to "RSL-RL LeggedRobotPPO
   published defaults"; the published default init_noise_std = 1.0 (learnable
   log std, state-independent Gaussian over the pre-map action u; the env owns
   the declared tanh bound). Cited default, not taste.
5. EVAL SEEDS ON A DETERMINISTIC ENGINE: the walk's seed entry state
   (WalkerSpec.reset_state from scene.json) is deterministic and carries no
   seed parameter, so the 5 eval episodes are 5 replays of the identical
   closed-loop (tagged by eval seed per the protocol). Zero-invention reading;
   recorded as such.
6. REFUSAL_TICK PRECISION: the engine freezes a refusing env with
   `a_ticks` = the count of completed ticks; the recorded refusal_tick is that
   frozen count (0-based first non-advanced tick). Collapse (height floor) is
   the engine's other own end-of-life class: it terminates the episode and is
   recorded in the episode record alongside refusal_tick; acceptance.py's fall
   definition (refusal classes before tick 270) is applied downstream, not here.

## MEASURED ENGINE FINDINGS (this lane's measurements on the inherited DLL; for the lead)

Both defects below live in walker_env.dll's `reset_kernel` (walker_env.cu /
walker_kernels.cuh) on this branch (e3b591e1's rebuild, committed
UNMEASURED-BY-CLOSEOUT-8). First measured here 2026-09-23; the wrapper
compensates for both (bytes of the DLL/host untouched):

1. RESET LEAVES THE rb/rbi READBACK STALE: after `env_reset`, ticks/refused/cmd
   arrays ARE re-zeroed (verified), but `rb`/`rbi` are only rewritten by the
   tick kernels -- the first status readback after a reset carries the PREVIOUS
   episode's last com/height/v3/phi/battery (probe: post-reset com 0.09536 =
   the pre-reset com; first post-reset tick then reads com 0.00250). Cost if
   uncompensated: every episode's t=0 observation is the previous episode's
   frozen state, the waypoint anchor is off by the stale com (0.095 m), and the
   first decision earns a phantom -1 progress reward. Wrapper fix:
   `_synthetic_reset_status` builds the t=0 status from the reset arrays the
   wrapper itself uploaded (phi from the spec's declared start phases).
2. THE WORK LEDGER IS NOT RE-INITIALIZED: `a_battery` persists across resets
   (probe: fresh-episode tick 1 reads rb[5] = 586.848 J = the previous
   episode's final ledger; ticks 1..16 flat at ~586.848 during settle). The
   pre-reset rb[5] IS the carry-in, so the wrapper captures it before
   env.reset and records work_J = rb_end[5] - carry_in (the honest delta).

3. THE TICK-40 REFUSAL (rc=5) IS CONFIRMED NOT COMMAND-CAUSED: with NO command
   ever issued, and with commands {0.0, 0.60 once, 0.60 re-issued, 0.7636
   once}, the trajectory is bit-identical through the tick-40 refusal
   (rb equal to 4 decimals across all five runs; phi frozen at the entry
   [0.0, 0.5] throughout -- the refusal lands mid-settle, settle_total=60).
   This is residual A (the tick-66 class, the drill lane's named open item):
   the CPU-exact probe (co8_cp_walk120.txt) walks 120 ticks refusal-free while
   this DLL build refuses at 40.

## RESULTS (filled after the runs; nothing below this line existed at prereg)

See falsifier_results.json (the runner's machine-readable output) and
smoke_seed*/run_receipt.json. Measured under GPU contention with the lead's
bars run resident (nvidia-smi ~22.7/24.5 GiB at lane start).
