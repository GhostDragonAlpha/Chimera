"""train_myobody_directional.py — direction-conditioned fine-tune of the mocap walk policy.

WHY: myobody_walk_mocap_policy.pt walks FORWARD only (the reward's velocity term is a dot with
the spawn heading, and its tracking envelope is the CMU 35_01 forward walk). The measured
directional gaits now exist (research_references/human/mocap_directional_reference.json:
backward + sidestep left/right from CMU 136/141/111/113/076), so the same bounded PPO fine-tune
is rerun with a movement COMMAND in the obs and per-command speed/envelope targets.

WHAT CHANGED vs train_myobody_mocap.py (only these):
  1. OBS += 4: one-hot command over [forward, backward, left, right], sampled per env per
     episode (this trainer resets every env each iteration, so the resample point is the
     iteration reset). ROUND 2: P_CMD rebalanced [0.5, 1/6 x3] -> [0.34, 0.22 x3] -- round 1
     passed the forward gate 5/5 but failed the other three directions, so mass moves to the
     weak ones while forward keeps a plurality (see P_CMD below).
  2. The velocity term projects qvel[0:2] onto the COMMANDED direction (cmd_dir, built by
     rotating the frozen spawn heading head0 by 0/180/+90/-90 deg) and scales by that
     direction's DERIVED target speed. (SUPERSEDED 2026-08-02: these used to be the raw
     Earth mocap speeds -- forward 1.285 m/s, backward 0.6, left 0.631, right 0.655 -- handed
     to a body in 7.076 m/s^2. Forward is now theHuman's own 0.9924 m/s; the other three are
     Froude-transported until the membrane derives them. See THE DERIVATION HEAD below.)
  3. The tracking term reads the matching direction's envelopes. Forward/backward use the
     same curve for both legs; a sidestep uses the LEAD envelope for the leg on the side of
     travel and the TRAIL envelope for the crossing leg (command "left" -> left leg leads).
     All four directions are pre-baked into one (4, 101, 6) table REF_ALL and gathered per
     env, so the per-step cost is unchanged.
  4. The phase clock runs at each command's own stride time, DERIVED for this world: forward
     1.1730 s (2 x theHuman's step_time_s, the leg as a compound pendulum at g=7.076); the
     other three are their Earth stride_m/speed_m_s transported by sqrt(g_E/g).
     (SUPERSEDED: forward was the Earth reference 1.127 s.)
  5. warm-start, two shapes: ROUND 2 defaults --init to the round-1 directional checkpoint
     (same 106-dim architecture -> FULL LOAD, every tensor shape-matches); the round-1 path
     (init from the 102-dim mocap policy -> PARTIAL LOAD, body.0.weight grows by the 4
     command columns seeded ~1e-3) is kept for anyone starting over.
  6. checkpoint to ChimeraEngine/output/myobody_walk_directional_policy.pt -- a NEW artifact.
     myobody_walk_mocap_policy.pt and myobody_walk_policy.pt are NEVER written (asserted).
     PRESERVED BRAINS (manual cp, never written by this script): round 1 at
     output/myobody_walk_directional_r1_policy.pt, round 2 at ..._r2_policy.pt.

ROUND 2 (after the morning gate): the gate diagnosed left as FREEZING -- the policy survives
by standing still because ALIVE_BONUS pays regardless of movement -- and right/backward as
moving-but-falling. Two levers, nothing else touched:
  a) STAGNATION PENALTY (the freeze lever): alive AND smoothed commanded-direction speed
     below STAG_FRAC * target costs STAG_W per step. The smoother is a ~0.5 s EMA seeded at
     target, so acceleration out of reset is never punished (see STAG_* below). It sits
     inside the reward bracket multiplied by `alive`, so a fallen env never accumulates it.
  b) more samples on the weak directions (the falls lever): the P_CMD rebalance above, plus
     warm-starting from the round-1 brain instead of the forward-only mocap policy.

ROUND 3 (after the round-2 gate): the freeze is dead -- all four directions translate with
real gait; the ONLY remaining failure mode is falling while moving (worst-seed survival
forward 8.9 s, backward 3.7, left 1.3, right 7.0 against the 10 s gate). Two changes:
  a) THE HORIZON BUG: episodes were 150 x 20 x 0.001 s = 3.0 s, so the policy had never
     practiced surviving as long as the gate demands -- and round 2 fell at 3.7-9.4 s,
     exactly past the practiced horizon. T=150 -> 750 (15.0 s episodes). Throughput drops
     ~5x (round 2: 511 iters/8h -> expect ~100/8h); accepted.
  b) FALL PENALTY: a fall was priced only as the end of the alive-bonus stream; now the
     terminal transition also pays FALL_PEN once (outside the alive bracket, into the GAE
     delta at the step alive goes 0 -- see the reward line). Everything else untouched.

UNCHANGED: the curriculum ramp (track term off until iter RAMP_START, then linear over
RAMP_LEN), ALIVE_BONUS, the parking-exploit guard (velocity term x2 weight so it dominates
alive+track), EFFORT, GAE/PPO hyperparameters, and the sagittal angle math -- joint angles
stay in the BODY-FACING frame (head0) for every command, because the envelopes are sagittal
hip/knee/ankle curves; only the velocity term knows about the travel direction.

Run:  C:\\Python314\\python.exe tools/train_myobody_directional.py [--envs 1024] [--seconds 840]
"""
from __future__ import annotations

import json
import sys
import os
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body   # the ONE place gravity is set (tools/world.py)

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / 'ChimeraEngine'
MYOBODY = ROOT / 'external' / 'myo_sim' / 'body' / 'myobody.xml'
REF_FWD = ROOT / 'research_references' / 'human' / 'mocap_walk_reference.json'
REF_DIR = ROOT / 'research_references' / 'human' / 'mocap_directional_reference.json'
OUT_PT = HERE / 'output' / 'myobody_walk_directional_policy.pt'
OUT_META = HERE / 'output' / 'myobody_walk_directional_meta.npy'
# HARD GUARD: this script must never clobber the forward-only policies it warm-starts from.
assert OUT_PT.name not in ('myobody_walk_mocap_policy.pt', 'myobody_walk_policy.pt')

# THE HORIZON BUG, found in round 3: T=150 x CONTROL_EVERY=20 x timestep 0.001 s = a 3.0 s
# episode, but the morning gate demands 10 s of sustained balance -- the policy had NEVER
# practiced surviving as long as it was judged on, and round 2 fell at 3.7-9.4 s, i.e.
# exactly past the practiced horizon. T=750 -> 15.0 s episodes. THROUGHPUT COST: iteration
# wall-clock scales ~linearly with T (round 2: 511 iters/8h at T=150 -> expect ~100/8h here);
# accepted, because an iter now teaches the thing the gate measures.
T = 750
CONTROL_EVERY = 20
HID = 256
GAMMA = 0.99
LAM = 0.95
CLIP = 0.2
EPOCHS = 5
MINIBATCH = 8192
LR = 3e-4
ENT = 0.004
VCOEF = 0.5
ALIVE_BONUS = 0.8        # same damping as the mocap trainer: survival must out-pay a sprint
FALL_FRAC = 0.6
# THE FALL PENALTY (round 3, THE lever for the only remaining failure mode -- falling while
# moving): until now a fall was priced only implicitly, as the end of the alive-bonus stream.
# This is an explicit one-time terminal cost applied at the step alive goes 0. Scale: ~1.5x
# a typical per-step reward (~1.3). The BIG price of a fall is still the forfeited stream
# (with the 15 s horizon, falling at 1.3 s gives up ~13.7 s x 0.8 of alive bonus); FALL_PEN
# is the sharp LOCAL signal that lands exactly on the terminal transition instead of being
# smeared across the episode by the value function.
FALL_PEN = 2.0
EFFORT = 0.01
W_TRACK = 1.0                     # weight of the mocap envelope matching term
SIGMA_DEG = 15.0                  # tolerance band, degrees
# THE CURRICULUM, inherited from the mocap trainer: W_TRACK at full weight from iter 0 pulled
# the policy off its feet. OFF for RAMP_START iters, then linear over RAMP_LEN.
RAMP_START = 8
RAMP_LEN = 16

# THE COMMAND ENCODING: one-hot over 4 directions, in this fixed order.
# ROUND 2 REBALANCE: round 1 ([0.5, 1/6 x3]) passed the forward gate 5/5 but failed the other
# three (left froze, right/backward fell), so probability mass moves to the weak directions.
# Forward keeps a plurality (0.34) so the solid skill still gets a third of the gradient
# signal; the three failing directions get 0.22 each -- more rollouts, more advantage signal.
CMDS = ('forward', 'backward', 'left', 'right')

# ══════════════════════════════════════════════════════════════════════════════════════════════
# THE DERIVATION HEAD — read the world before you look at a single weight
#
# This block exists because on 2026-08-02 this trainer was asking a body in 7.076 m/s^2 to walk at
# 1.285 m/s, a speed measured on Earth, and a four-variant parameter sweep was run to find out why
# it would not. Every variant asked the same impossible question. RULE 1, and it is a STAGE now
# rather than a warning: DERIVE IT BEFORE YOU TRAIN IT (docs/THE_LAW.md, docs/THE_WORKFLOW.md S4).
#
# The order below is not decorative. Gravity is read from the parent membrane FIRST, the targets
# are derived from it SECOND, and only what is left over is allowed anywhere near an optimiser.
# ══════════════════════════════════════════════════════════════════════════════════════════════

G_EARTH = 9.80665           # CGPM 1901 defined standard gravity (SI Brochure §5.2). Not this world's -- kept ONLY as the label
                            # on the mocap datasets, which were recorded in it.
LEDGER_MEMBRANE = 'theHuman'
LEDGER_REQUIRED = ('g', 'leg_length_m', 'comfortable_speed_ms', 'step_time_s')


class DerivationFailed(RuntimeError):
    """Raised when the world will not say what it is.

    THERE IS NO FALLBACK BRANCH IN THIS FILE, and its absence is the feature. A default is an
    assumption wearing a hat: the moment the ledger stops carrying `g`, a fallback serves 9.80665
    silently, forever, and every number downstream is an Earth number in a 0.722 g world with a
    comment claiming otherwise. Silence is better than a lie; an exception is better than silence.
    """


def read_ledger() -> dict:
    """Reach UP into the parent membrane and read what this world published about itself.

    `theHuman`'s `numbers.json` is written by `Chimera/core/grow.py` from `derive(parent, free)`, and its
    `g` arrives down an unbroken chain from `aBlueWorld`'s mass -- which is itself derived, all the
    way back to the constants that fence `theZero`. We do not compute it here and we do not choose
    it. We read it. A membrane may read only its parent, and for this trainer the body IS the parent.
    """
    hits = [p for p in (ROOT / 'story').rglob('numbers.json')
            if p.parent.name == LEDGER_MEMBRANE]
    if not hits:
        raise DerivationFailed(
            f'Derivation failed: no {LEDGER_MEMBRANE}/numbers.json anywhere under story/. '
            f'The ledger does not exist, so this world has not said what its gravity is. '
            f'Run `python Chimera/core/grow.py` and try again. Refusing to assume Earth.')
    led = json.loads(hits[0].read_text(encoding='utf8'))
    missing = [k for k in LEDGER_REQUIRED if k not in led]
    if missing:
        raise DerivationFailed(
            f'Derivation failed: {LEDGER_MEMBRANE} publishes no {missing}. '
            f'These are not optional inputs with sensible defaults -- they are the world. '
            f'The number belongs to the membrane; if it is absent the membrane must derive it. '
            f'Refusing to assume Earth.')
    return led


LEDGER = read_ledger()
GRAVITY = float(LEDGER['g'])                     # m/s^2, THIS world, read and never guessed
LEG_L = float(LEDGER['leg_length_m'])            # m, anatomy -- a fact about the body, not the world

# THE TWO INVARIANTS, both taken from the body's own published gait rather than invented.
#
# Fr_WALK -- the dimensionless Froude number a human chooses to walk at. `Fr = v^2/(gL)`, and equal
# Fr means a DYNAMICALLY SIMILAR gait, so this number is a property of walking itself and crosses
# worlds unchanged. It is what makes one law walk on every planet.
#
# K_PENDULUM -- the leg's swing constant. A leg is a compound pendulum, `T = 2*pi*sqrt(I/(m*g*d))`,
# so at fixed anatomy `T * sqrt(g)` is constant. NOTE THE SIGN, because the brief got it backwards
# and a sign error here is the whole bug wearing different clothes: a period goes as g^(-1/2), so
# WEAKER GRAVITY MAKES THE STRIDE LONGER, not shorter. Speed falls and stride time RISES.
FR_WALK = float(LEDGER['comfortable_speed_ms']) ** 2 / (GRAVITY * LEG_L)
STRIDE_S_LEDGER = 2.0 * float(LEDGER['step_time_s'])   # the membrane's own rule: a stride is 2 steps
K_PENDULUM = STRIDE_S_LEDGER * GRAVITY ** 0.5


def prove_kinematics(g: float) -> tuple[float, float]:
    """THE EXECUTABLE LAW. Gravity in; the gait's two locked numbers out.

        v(g)  = sqrt(Fr_walk * g * L)      Froude   -- speed  goes as  g^(+1/2)
        T(g)  = K_pendulum / sqrt(g)       pendulum -- stride goes as  g^(-1/2)

    This is a function and not a paragraph on purpose. Of 31 heuristics in this repo, the 18 that
    became mechanism are alive and the 13 that stayed prose degenerated into the same sentence with
    the nouns swapped. A law you can call cannot rot; a law you can only read already has.

    IT PREDICTS WHAT IT WAS NEVER FITTED TO, which is the only test that separates a derivation
    from a story: evaluated at Earth's gravity it returns a walk it has never seen, and the CMU
    mocap dataset is standing there to be compared against (see `check_kinematics`).
    """
    if not (g > 0.0):
        raise DerivationFailed(f'Derivation failed: gravity must be positive, got {g!r}.')
    return (FR_WALK * g * LEG_L) ** 0.5, K_PENDULUM / g ** 0.5


# The four commands. FORWARD is the body's own derivation, read from the ledger. The other three
# have NO derivation in the membrane -- only Earth measurements -- so they are transported by the
# same two laws, and that asymmetry is a DEBT rather than a design: `theHuman` should derive a
# backward and a sidestep gait the way it derives the forward one. Declared here so it is visible.
_FROUDE = (GRAVITY / G_EARTH) ** 0.5


def derive_targets(ref_fwd: dict, ref_dir: dict) -> tuple[list, list, dict]:
    """Every per-command speed and stride time, on this world. Nothing here is chosen."""
    v_fwd, t_fwd = prove_kinematics(GRAVITY)
    speeds, strides, earth = [v_fwd], [t_fwd], {}
    earth['forward'] = (float(ref_fwd['speed_m_s']), float(ref_fwd['stride_time_s']))
    for c in CMDS[1:]:
        v_e = float(ref_dir[c]['speed_m_s'])
        t_e = float(ref_dir[c]['stride_m']) / v_e
        earth[c] = (v_e, t_e)
        speeds.append(v_e * _FROUDE)        # v  ~ sqrt(g)
        strides.append(t_e / _FROUDE)       # T  ~ 1/sqrt(g)
    return speeds, strides, earth


def check_kinematics() -> dict:
    """Two independent checks on the law, run before the console block is printed.

    CONSISTENCY -- at the ledger's own gravity the law must return the ledger's own numbers. This
    one cannot fail by construction (the invariants were read from those numbers), so it proves
    only that nothing has been transcribed wrong. It is the cheap half.

    PREDICTION -- at EARTH's gravity the law returns a walk it was never shown, and the CMU dataset
    is right there. This is the half that can actually fail, and IT DOES: see the self-critique.
    A disagreement that is published is a finding; one that is quietly reconciled is a fudge.
    """
    v_here, t_here = prove_kinematics(GRAVITY)
    v_earth, t_earth = prove_kinematics(G_EARTH)
    ref = json.loads(REF_FWD.read_text())
    return {
        'consistency': (v_here - float(LEDGER['comfortable_speed_ms']),
                        t_here - STRIDE_S_LEDGER),
        'prediction': (v_earth, t_earth, float(ref['speed_m_s']), float(ref['stride_time_s'])),
    }


def confirm_targets(speeds, strides, earth, assume_yes: bool = False) -> None:
    """Print what was read, what was derived, and what it replaces -- then ASK THE HUMAN.

    The human is one of the two terminals and owns taste, so a derivation this load-bearing is
    shown before a single GPU-hour is spent rather than after. `--yes` exists for unattended runs
    and it is the operator's choice to pass it, not this module's choice to skip the question.
    """
    print()
    print('=' * 94)
    print('  THE DERIVATION -- READ FROM THE PARENT MEMBRANE, NOT ASSUMED')
    print('=' * 94)
    print(f'  ledger        {LEDGER_MEMBRANE}/numbers.json   (written by Chimera/core/grow.py)')
    print(f'  GRAVITY       {GRAVITY:.6f} m/s^2      ({GRAVITY / G_EARTH:.4f} of Earth,'
          f' derived from aBlueWorld mass)')
    print(f'  leg length    {LEG_L:.6f} m           (anatomy, ANSUR II proportions)')
    print(f'  Fr_walk       {FR_WALK:.6f}             dimensionless -- the gait invariant')
    print(f'  K_pendulum    {K_PENDULUM:.6f}             the leg\'s swing constant')
    print('-' * 94)
    print(f'  {"command":<10}{"speed NOW":>12}{"was (Earth)":>14}{"":4}'
          f'{"stride NOW":>12}{"was (Earth)":>14}   source')
    for i, c in enumerate(CMDS):
        ve, te = earth[c]
        src = 'DERIVED by theHuman' if i == 0 else 'Earth, Froude-transported (debt)'
        print(f'  {c:<10}{speeds[i]:>10.4f} m/s{ve:>12.4f}    {strides[i]:>10.4f} s'
              f'{te:>12.4f}     {src}')
    print('-' * 94)
    chk = check_kinematics()
    dv, dt = chk['consistency']
    ve, te, mv, mt = chk['prediction']
    print(f'  CONSISTENCY   at g={GRAVITY:.4f} the law reproduces the ledger to '
          f'{abs(dv):.2e} m/s and {abs(dt):.2e} s')
    print(f'  PREDICTION    at g={G_EARTH:.5f} (never fitted) the law says '
          f'{ve:.4f} m/s / {te:.4f} s')
    print(f'                the CMU mocap dataset says      '
          f'{mv:.4f} m/s / {mt:.4f} s'
          f'   -> {100 * (ve / mv - 1):+.1f}% / {100 * (te / mt - 1):+.1f}%')
    print(f'                THIS GAP IS PUBLISHED, NOT RECONCILED. It says theHuman\'s swing drive')
    print(f'                is ~10% fast against the only Earth walk we can check it on.')
    print('=' * 94)
    print('  These two columns are IMMUTABLE. The optimiser may move joint stiffness, friction and')
    print('  actuator response. It may never move the speed or the stride: those are the world.')
    print('=' * 94)
    if assume_yes:
        print('  --yes given: proceeding without asking.\n')
        return
    try:
        ans = input('  Do these match the law as written in the repo?  [y/N] ').strip().lower()
    except EOFError:
        raise DerivationFailed(
            'Derivation failed: no operator present to confirm the derivation, and no --yes given. '
            'Refusing to spend GPU hours on targets nobody has looked at.')
    if ans not in ('y', 'yes'):
        raise DerivationFailed(
            'Stopped at the human terminal: the operator did not confirm the derived targets. '
            'The human is the arbiter -- if these numbers contradict the law, the physics is '
            'wrong and the fix is upstream in the membrane, not in this file.')
    print()
CMD_DIM = len(CMDS)
P_CMD = (0.34, 0.22, 0.22, 0.22)

# THE STAGNATION PENALTY (round 2, the left-freeze diagnosis): the eval showed the policy
# surviving by standing still -- ALIVE_BONUS pays regardless of movement, and the parking
# guard only weights the velocity term, it does not punish immobility. Per control step, an
# env that is ALIVE and whose smoothed commanded-direction speed is below
# STAG_FRAC * target pays STAG_W. The smoother is an EMA with ~0.5 s time constant, so the
# first steps of acceleration (and normal gait speed ripple) are not punished -- a fresh
# episode starts with the EMA seeded AT target, and it has to sag below the threshold first.
# ROUND 6 -- THE PARKING EXPLOIT, MEASURED AND PRICED. Round 4's policy walked at 0.17-0.29 m/s
# against a 1.285 m/s target and would not go faster, and the render showed why: it holds a
# crouch and shuffles. The arithmetic was the whole story.
#
#   stagnation floor = STAG_FRAC * target = 0.10 * 1.285 = 0.13 m/s
#   the policy sat at 0.19 m/s -- ABOVE the floor, so the penalty never fired
#   velocity paid 1.2 * (0.19/1.285) = 0.18 per step
#   ALIVE_BONUS paid 0.8 per step, unconditionally, for not falling
#
# Standing still paid 4.4x what moving paid. The policy was not failing to learn; it found the
# optimum and sat in it. A crouched shuffle clears a 10% bar forever.
#
# So the bar moves to where walking actually begins and the penalty is priced against the alive
# bonus rather than against the track term. At 0.19 m/s the penalty now fires and costs 1.0
# against an alive bonus of 0.8 -- parking is NET NEGATIVE. At 0.7 m/s it does not fire and the
# step pays ~1.45. For the first time there is a gradient from shuffle to walk.
STAG_W = 1.0                      # priced against ALIVE_BONUS (0.8), not against the track term
STAG_FRAC = 0.45                  # below 45% of target is not walking, it is parking
STAG_TAU_S = 0.5                  # EMA time constant, seconds

BODIES = {'hip_r': 'femur_r', 'knee_r': 'tibia_r', 'ankle_r': 'talus_r', 'toe_r': 'toes_r',
          'hip_l': 'femur_l', 'knee_l': 'tibia_l', 'ankle_l': 'talus_l', 'toe_l': 'toes_l',
          'pelvis': 'pelvis', 'trunk': 'torso'}


def build_ac(OBS, ACT, torch):
    import torch.nn as nn

    class AC(nn.Module):
        def __init__(self):
            super().__init__()
            self.body = nn.Sequential(nn.Linear(OBS, HID), nn.Tanh(),
                                      nn.Linear(HID, HID), nn.Tanh())
            self.mean = nn.Linear(HID, ACT)
            self.v = nn.Linear(HID, 1)
            self.log_std = nn.Parameter(torch.full((ACT,), -0.7))

        def forward(self, o):
            h = self.body(o)
            return self.mean(h), self.log_std.exp(), self.v(h).squeeze(-1)

    return AC().to('cuda')


def close_curve(curve):
    """The forward envelopes are 101 points (closed loop); the directional ones are 100.
    Append the first sample so one (4, 101, ...) table serves all four directions."""
    return list(curve) + [curve[0]] if len(curve) == 100 else list(curve)


def build_ref_table(ref_fwd, ref_dir, dev, torch):
    """(4, 101, 6) reference envelopes, column order [hip_r, hip_l, knee_r, knee_l,
    ankle_r, ankle_l] -- matching joint_angles(). LEAD/TRAIL mapping for sidesteps: the
    lead leg is the one on the side of travel, so 'left' puts the trail curve on the
    RIGHT column and the lead curve on the LEFT column (and vice versa for 'right')."""
    np_ = np

    def both_legs(env):
        return np_.stack([env['hip'], env['hip'], env['knee'], env['knee'],
                          env['ankle'], env['ankle']], 1)          # (101, 6)

    def split_legs(env, lead_side):
        lead = {j: close_curve(env['lead'][j]) for j in ('hip', 'knee', 'ankle')}
        trail = {j: close_curve(env['trail'][j]) for j in ('hip', 'knee', 'ankle')}
        r, l = (trail, lead) if lead_side == 'l' else (lead, trail)
        return np_.stack([r['hip'], l['hip'], r['knee'], l['knee'],
                          r['ankle'], l['ankle']], 1)

    fwd = {j: close_curve(ref_fwd['envelopes_deg'][j]['mean']) for j in ('hip', 'knee', 'ankle')}
    bwd = {j: close_curve(ref_dir['backward']['envelopes_deg'][j]) for j in ('hip', 'knee', 'ankle')}
    table = np_.stack([both_legs(fwd), both_legs(bwd),
                       split_legs(ref_dir['left']['envelopes_deg'], 'l'),
                       split_legs(ref_dir['right']['envelopes_deg'], 'r')])
    return torch.tensor(table, dtype=torch.float32, device=dev)


def main() -> int:
    import torch
    import warp as wp
    import mujoco
    import mujoco_warp as mjw

    envs = int(sys.argv[sys.argv.index('--envs') + 1]) if '--envs' in sys.argv else 1024
    budget = float(sys.argv[sys.argv.index('--seconds') + 1]) if '--seconds' in sys.argv else 840.0

    # ── THE REWARD TERMS, OVERRIDABLE, SO VARIANTS CAN RUN SIDE BY SIDE ──────────────────────
    # The parking exploit was found by reading arithmetic, and the FIX was chosen by the same
    # reading -- which is a guess wearing a derivation's clothes until something measures it.
    # The box has 24.5 GiB of VRAM and a run takes ~5, so three or four variants fit at once and
    # the question stops being "is this the right price" and becomes "which price wins".
    #
    # ONE VARIABLE PER VARIANT. Three simultaneous changes have no attributable outcome: if it
    # works you cannot say why, and if it fails you know less than when you started.
    global ALIVE_BONUS, STAG_FRAC, STAG_W, EFFORT
    def _argf(flag, cur):
        return float(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else cur
    ALIVE_BONUS = _argf('--alive', ALIVE_BONUS)
    STAG_FRAC = _argf('--stag-frac', STAG_FRAC)
    STAG_W = _argf('--stag-w', STAG_W)
    EFFORT = _argf('--effort', EFFORT)
    print(f'  REWARD  alive={ALIVE_BONUS}  stag_frac={STAG_FRAC}  stag_w={STAG_W}  '
          f'effort={EFFORT}', flush=True)
    init = Path(sys.argv[sys.argv.index('--init') + 1]) if '--init' in sys.argv \
        else HERE / 'output' / 'myobody_walk_directional_policy.pt'   # round 2: own round-1 result
    out = Path(sys.argv[sys.argv.index('--out') + 1]) if '--out' in sys.argv else OUT_PT
    assert out.name not in ('myobody_walk_mocap_policy.pt', 'myobody_walk_policy.pt'), \
        f'refusing to overwrite the forward-only policy: {out}'
    dev = 'cuda'
    torch.manual_seed(0)

    ref_fwd = json.loads(REF_FWD.read_text())
    ref_dir = json.loads(REF_DIR.read_text())

    # ── THE TRACKING ENVELOPE COMES FROM THE MEMBRANE, NOT FROM AN EARTH FILE ────────────────
    # The velocity term was fixed at S4 and the tracking term was left reading CMU 35_01: a walk
    # at 1.285 m/s on Earth, Fr = 0.1830, while this body walks at Fr = 0.1513. Two terms, two
    # different gaits, 21% apart in Froude -- rule 1's contradiction one layer down.
    #
    # THE LAW THAT CONNECTS THEM EXISTS, and the claim that it does not was wrong: DYNAMIC
    # SIMILARITY. Equal Froude means geometrically similar motion, and a joint angle is
    # dimensionless, so the trajectories transfer UNCHANGED between worlds at equal Fr. What was
    # missing was not a law but a lookup -- theHuman was selecting its measured curve by matching
    # m/s against a study run on Earth, which picked the SLOW condition (Fr 0.0917) for a body
    # walking at Fr 0.1513. It now matches Froude and publishes the result.
    #
    # We READ that publication rather than importing the membrane (rule 20: an instrument may not
    # import the thing it judges). No fallback: if it is absent the membrane must publish it.
    if 'gait_envelope_deg' not in LEDGER:
        raise DerivationFailed(
            'Derivation failed: theHuman publishes no gait_envelope_deg. The tracking term would '
            'fall back to an Earth walk at a different Froude number, which is the defect this '
            'exists to remove. Run `python Chimera/core/grow.py`. Refusing to assume Earth.')
    _env = LEDGER['gait_envelope_deg']
    # keep the file's shape -- build_ref_table reads envelopes_deg[j]['mean'] -- so the swap is
    # a swap of DATA, not of structure. `close_curve` then closes 100 -> 101 as it always did.
    _was = {k: (min(ref_fwd['envelopes_deg'][k]['mean']), max(ref_fwd['envelopes_deg'][k]['mean']))
            for k in ('hip', 'knee', 'ankle')}
    ref_fwd = dict(ref_fwd)
    ref_fwd['envelopes_deg'] = {
        k: {'mean': list(_env[k])[:100], 'std': ref_fwd['envelopes_deg'][k].get('std'),
            'n_cycles': ref_fwd['envelopes_deg'][k].get('n_cycles'),
            'source': 'theHuman.gait_envelope_deg (Froude-matched)'}
        for k in ('hip', 'knee', 'ankle')}
    print('  ENVELOPE      forward tracking curves <- theHuman.gait_envelope_deg '
          f'(Fr-matched, similar Earth speed {LEDGER["v_similar_earth_ms"]:.4f} m/s)')
    for _k in ('hip', 'knee', 'ankle'):
        _lo, _hi = min(_env[_k]), max(_env[_k])
        print(f'                {_k:6} {_lo:+7.1f}..{_hi:+7.1f} deg   '
              f'(CMU 35_01 was {_was[_k][0]:+7.1f}..{_was[_k][1]:+7.1f})')

    # ── S4 DERIVE, before anything else in this routine ───────────────────────────────────────
    # These four lines used to read the two mocap files straight through: `speed_m_s` was
    # 1.285 m/s and `stride_s` was 1.127 s, both recorded on Earth, and both handed to a body
    # standing in 7.076 m/s^2. That is the defect Rule 1 exists for, and no reward-shaping
    # variant can reach past it -- the crouch was the only stable point in a contradictory
    # reward. The references are still READ, but only as the Earth column of the comparison.
    _speeds, _strides, _earth = derive_targets(ref_fwd, ref_dir)
    confirm_targets(_speeds, _strides, _earth, assume_yes=('--yes' in sys.argv))

    # --dry-run: the physics assertion block and nothing else. No optimiser is constructed, no
    # model is loaded, no checkpoint can be written. Pre-flight step 2 -- look at the numbers
    # before spending a GPU-hour on them, which is the whole of rule 1 expressed as a flag.
    if '--dry-run' in sys.argv:
        print('  --dry-run: derivation shown, optimiser NOT constructed. Exiting.\n')
        return 0

    # IMMUTABLE. Not initial values, not priors, not something a scheduler anneals -- these are
    # what this world permits, and the only honest way to change them is to change the world.
    speed_m_s = torch.tensor(_speeds, dtype=torch.float32, device=dev)
    stride_s = torch.tensor(_strides, dtype=torch.float32, device=dev)
    speed_m_s.requires_grad_(False)
    stride_s.requires_grad_(False)
    ref_all = build_ref_table(ref_fwd, ref_dir, dev, torch)
    p_cmd = torch.tensor(P_CMD, dtype=torch.float32, device=dev)

    # THE WORLD THE BODY STANDS IN -- see tools/world.py. The XML declares no gravity, so
    # MuJoCo's default -9.81 applied and every run to date simulated this walker ON EARTH.
    mjm, _g_world = load_body(MYOBODY, mujoco)
    assert abs(_g_world - GRAVITY) < 1e-12, 'the world and the derivation disagree about g'

    mjd = mujoco.MjData(mjm)
    nq, nv, nu = mjm.nq, mjm.nv, mjm.nu
    nj = nq - 7
    q_key = mjm.key_qpos[0].copy()
    quat_key = torch.tensor(q_key[3:7], dtype=torch.float32, device=dev)
    STAND_Z = float(q_key[2])
    FALL_Z = FALL_FRAC * STAND_Z
    body_id = {role: mujoco.mj_name2id(mjm, mujoco.mjtObj.mjOBJ_BODY, n) for role, n in BODIES.items()}

    W = envs
    m = mjw.put_model(mjm)
    d = mjw.put_data(mjm, mjd, nworld=W, nconmax=100, njmax=512)
    qpos = wp.to_torch(d.qpos)
    qvel = wp.to_torch(d.qvel)
    ctrl = wp.to_torch(d.ctrl)
    xpos = wp.to_torch(d.xpos)                      # (W, nbody, 3)
    q_key_t = torch.tensor(q_key, dtype=torch.float32, device=dev)

    OBS = 4 + 3 + 3 + nj * 2 + CMD_DIM              # old obs + one-hot command
    ACT = nu
    ac = build_ac(OBS, ACT, torch)

    # WARM-START, two shapes:
    #  a) FULL LOAD (round 2 default): init from a same-architecture 106-dim directional
    #     checkpoint -- every tensor shape-matches, nothing is grown.
    #  b) PARTIAL LOAD (round 1 path, kept): init from the 102-dim mocap policy -- every
    #     matching tensor is copied; body.0.weight grew by CMD_DIM, so the trained columns
    #     are kept and the 4 new command columns are seeded with ~1e-3 noise.
    sd_new = ac.state_dict()
    sd_old = torch.load(init, map_location=dev)
    loaded, grown, skipped = [], [], []
    for k, v in sd_old.items():
        if k in sd_new and sd_new[k].shape == v.shape:
            sd_new[k] = v
            loaded.append(k)
        elif k == 'body.0.weight' and v.shape[1] + CMD_DIM == sd_new[k].shape[1]:
            noise = torch.randn(sd_new[k][:, -CMD_DIM:].shape, device=dev) * 1e-3
            sd_new[k] = torch.cat([v, noise], 1)
            grown.append(f'{k} {tuple(v.shape)} -> {tuple(sd_new[k].shape)} '
                         f'(new {CMD_DIM} command cols ~N(0, 1e-3))')
        else:
            skipped.append(f'{k} {tuple(v.shape)} vs {tuple(sd_new[k].shape)}')
    ac.load_state_dict(sd_new)
    if not grown and not skipped and len(loaded) == len(sd_new):
        print(f'  FULL LOAD (round N warm start) from {init}: '
              f'all {len(loaded)} tensors shape-matched, nothing grown')
    else:
        print(f'  warm-start from {init}: {len(loaded)} tensors copied verbatim')
    for g in grown:
        print(f'    GROWN {g}')
    for s in skipped:
        print(f'    SKIPPED {s}')
    opt = torch.optim.Adam(ac.parameters(), lr=LR)

    print(f'\nPPO FINE-TUNE: mocap policy + DIRECTIONAL commands '
          f'(one-hot {CMDS}, P={P_CMD}; speeds_m_s={[round(float(s), 3) for s in speed_m_s]}, '
          f'track w={W_TRACK} ramped in after iter {RAMP_START}, sigma={SIGMA_DEG} deg, '
          f'stag w={STAG_W} below {STAG_FRAC:.0%} target, ema {STAG_TAU_S}s, '
          f'fall pen={FALL_PEN}, episode {T * mjm.opt.timestep * CONTROL_EVERY:.1f}s)\n' + '=' * 74)
    print(f'  {W} envs x {T} steps   wall-clock budget {budget:.0f}s   -> {out}')
    print(f"  {'iter':>4}{'reward':>9}{'cmdv':>7}{'track':>8}{'stag':>7}{'fall%':>7}{'surv%':>7}"
          f"{'sec':>7}{'total':>8}   per-cmd mean speed along command, m/s")

    def quat_fwd(q):
        w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
        return torch.stack([1 - 2 * (y * y + z * z), 2 * (x * y + w * z), 2 * (x * z - w * y)], 1)

    def heading_xy(q):
        f = quat_fwd(torch.nan_to_num(q))[:, :2]
        return f / (f.norm(dim=1, keepdim=True) + 1e-6)

    def observe(cmd1h):
        base = torch.nan_to_num(torch.cat([torch.nan_to_num(qpos[:, 3:7]), qvel[:, 3:6],
                                           qvel[:, 0:3], qpos[:, 7:], qvel[:, 6:]], 1)).clamp(-20, 20)
        return torch.cat([base, cmd1h], 1)          # command rides unclamped, it is already 0/1

    def seg_angle(v, head):
        """v: (W,3) segment vector; head: (W,2) travel direction. Degrees from straight-down."""
        vf = (v[:, :2] * head).sum(-1)
        vu = v[:, 2]
        return torch.rad2deg(torch.atan2(vf, -vu))

    def joint_angles(head):
        """(W,6): hip/knee/ankle x r/l, same vector math as the evaluators. Sagittal angles
        live in the BODY-FACING frame (head0) for every command -- only the velocity term
        uses the commanded travel direction."""
        p = {role: xpos[:, b, :] for role, b in body_id.items()}
        trunk = p['trunk'] - p['pelvis']
        th_trunk = seg_angle(-trunk, head)
        hips, knees, ankles = [], [], []
        for s in ('r', 'l'):
            thigh = p[f'knee_{s}'] - p[f'hip_{s}']
            shank = p[f'ankle_{s}'] - p[f'knee_{s}']
            foot = p[f'toe_{s}'] - p[f'ankle_{s}']
            th_thigh = seg_angle(thigh, head)
            th_shank = seg_angle(shank, head)
            flen = foot.norm(dim=-1).clamp_min(1e-9)
            foot_pitch = torch.rad2deg(torch.asin((foot[:, 2] / flen).clamp(-1, 1)))
            hips.append(th_thigh - th_trunk)
            knees.append(th_thigh - th_shank)
            ankles.append(foot_pitch - th_shank)
        return torch.stack(hips + knees + ankles, 1)          # [hip_r,hip_l,knee_r,knee_l,ankle_r,ankle_l]

    gen = torch.Generator(device=dev).manual_seed(1)
    t_all = time.perf_counter()
    it = 0
    while time.perf_counter() - t_all < budget:
        ti = time.perf_counter()
        qpos[:] = q_key_t.unsqueeze(0)
        qvel.zero_()
        qpos[:, 7:] += torch.randn(W, nj, device=dev, generator=gen) * 0.03
        mjw.forward(m, d)
        head0 = heading_xy(qpos[:, 3:7])
        # THE EPISODE'S COMMAND: sampled per env at reset, one-hot into the obs, and turned
        # into a world-frame travel direction by rotating the frozen spawn heading.
        # left = rotate head0 +90 deg in the xy plane -> (-y, x); right = (y, -x).
        cmd = torch.multinomial(p_cmd.expand(W, CMD_DIM), 1, generator=gen).squeeze(1)
        cmd1h = torch.nn.functional.one_hot(cmd, CMD_DIM).float()
        cand = torch.stack([head0, -head0,
                            torch.stack([-head0[:, 1], head0[:, 0]], 1),
                            torch.stack([head0[:, 1], -head0[:, 0]], 1)], 1)   # (W,4,2)
        cmd_dir = cand[torch.arange(W, device=dev), cmd]
        tgt_speed = speed_m_s[cmd]                  # (W,) per-env target, m/s
        stride_env = stride_s[cmd]                  # (W,) per-env stride clock, s
        phase0 = torch.rand(W, device=dev, generator=gen)   # desynchronized clocks across envs

        obs_b = torch.zeros(T, W, OBS, device=dev)
        act_b = torch.zeros(T, W, ACT, device=dev)
        lp_b = torch.zeros(T, W, device=dev)
        val_b = torch.zeros(T, W, device=dev)
        rew_b = torch.zeros(T, W, device=dev)
        alive_b = torch.zeros(T, W, device=dev)
        alive = torch.ones(W, device=dev)
        fwd_sum = torch.zeros(W, device=dev)        # projected speed along cmd_dir, m/s
        track_sum = torch.zeros(W, device=dev)
        stag_sum = torch.zeros(W, device=dev)       # stagnation penalty applied, reward units
        fall_sum = torch.zeros(W, device=dev)       # fall events (<=1 per env per episode)
        dt_ctrl = mjm.opt.timestep * CONTROL_EVERY
        # THE STAGNATION EMA, seeded AT the per-env target speed: a fresh episode is
        # presumed innocent, and the ~0.5 s EMA must first sag below STAG_FRAC * target
        # before the penalty bites -- so the first steps of acceleration are never punished.
        ema_alpha = 1.0 - np.exp(-dt_ctrl / STAG_TAU_S)
        speed_ema = tgt_speed.clone()

        with torch.no_grad():
            for t in range(T):
                o = observe(cmd1h)
                mean, std, v = ac(o)
                dist = torch.distributions.Normal(mean, std)
                raw = dist.sample()
                lp = dist.log_prob(raw).sum(-1)
                ctrl[:] = raw.clamp(0.0, 1.0)
                for _ in range(CONTROL_EVERY):
                    mjw.step(m, d)
                # velocity projected on the COMMANDED direction, scaled by its measured
                # target speed: backward motion pays positive under a backward command.
                fwd = (torch.nan_to_num(qvel[:, 0:2]) * cmd_dir).sum(1)
                vtrack = torch.clamp(fwd / tgt_speed, -0.5, 1.5)
                # THE PARKING EXPLOIT still applies per direction: alive+track alone pays for
                # standing still with good joint shapes, so the velocity term keeps its x2
                # weight (1.2 vs 0.5 * w_track) and must dominate the reward.
                upr = torch.clamp(torch.abs((torch.nan_to_num(qpos[:, 3:7]) * quat_key).sum(1)), 0, 1)
                was_alive = alive
                alive = alive * (torch.nan_to_num(qpos[:, 2]) > FALL_Z).float()
                # newly_fallen is 1 exactly at the transition step, 0 before and after --
                # the penalty is one-time, not per-step-dead.
                newly_fallen = was_alive * (1.0 - alive)
                effort = raw.clamp(0.0, 1.0).pow(2).mean(1)
                phase01 = (phase0 + t * dt_ctrl / stride_env) % 1.0
                ang = joint_angles(head0)
                idx = (phase01 * 100).long().clamp(0, 100)
                ra = ref_all[cmd, idx]                      # (W,6) this command's envelopes
                terr = (ang - ra) / SIGMA_DEG
                track = torch.exp(-terr.pow(2)).mean(1)
                # THE STAGNATION PENALTY: alive AND smoothed speed far below target. It is
                # multiplied by `alive` INSIDE the bracket like every other term, so a fallen
                # env stops accumulating it the moment it falls (the whole bracket zeroes).
                speed_ema = speed_ema + ema_alpha * (fwd - speed_ema)
                stag = STAG_W * (speed_ema < STAG_FRAC * tgt_speed).float()
                obs_b[t] = o; act_b[t] = raw; lp_b[t] = lp; val_b[t] = v
                w_track = W_TRACK * min(1.0, max(0.0, (it - RAMP_START) / RAMP_LEN))
                # THE FALL PENALTY sits OUTSIDE the alive-multiplied bracket: inside, it would
                # be zeroed by the very fall it prices. It enters the PPO advantage through
                # the GAE delta at the terminal step, where mask=0 also blocks the bootstrap
                # -- so the terminal return is exactly (-FALL_PEN - v), and the cost
                # propagates back with gamma*lam decay like any terminal reward.
                rew_b[t] = (1.2 * vtrack * upr + ALIVE_BONUS - EFFORT * effort
                            + 0.5 * w_track * track - stag) * alive - FALL_PEN * newly_fallen
                alive_b[t] = alive
                fwd_sum += fwd * alive
                track_sum += track * alive
                stag_sum += stag * alive
                fall_sum += newly_fallen
            _, _, last_v = ac(observe(cmd1h))

        adv = torch.zeros(T, W, device=dev); gae = torch.zeros(W, device=dev)
        for t in reversed(range(T)):
            nextv = last_v if t == T - 1 else val_b[t + 1]
            mask = alive_b[t]
            delta = rew_b[t] + GAMMA * nextv * mask - val_b[t]
            gae = delta + GAMMA * LAM * mask * gae
            adv[t] = gae
        ret = adv + val_b
        bo = obs_b.reshape(-1, OBS); ba = act_b.reshape(-1, ACT)
        blp = lp_b.reshape(-1); badv = adv.reshape(-1); bret = ret.reshape(-1)
        badv = (badv - badv.mean()) / (badv.std() + 1e-8)
        N = bo.shape[0]
        ent_coef = ENT * max(0.0, 1.0 - it / 30.0)

        # ── KL EARLY STOP, AND IT IS HERE BECAUSE A RUN DESTROYED ITSELF WITHOUT IT ──────────
        # 2026-08-01, measured: survival 41.4% -> 33.5% over five iterations, then 19.5% -> 2.0%
        # -> 0.1% over three. The policy did not decay, it was DESTROYED by a single update, and
        # then spent fifteen iterations crawling back to 2.4%.
        #
        # Gradient clipping was already here and did not prevent it, because the two guards stop
        # different things. Clipping bounds how far one STEP moves the weights; it says nothing
        # about how far FIVE EPOCHS over the same batch move the POLICY. Once the new policy is
        # far from the one that collected the data, every importance ratio is meaningless -- the
        # clip saturates, the gradient points somewhere unrelated to the objective, and the update
        # is noise applied with confidence.
        #
        # So measure the distance directly and stop when it is too far. approx_kl is Schulman's
        # low-variance estimator; 0.02 is the standard target. This does not slow learning down --
        # it declines to take the steps that were never learning in the first place.
        KL_TARGET = 0.02
        _stopped = False
        for _ep in range(EPOCHS):
            if _stopped:
                break
            idxp = torch.randperm(N, device=dev)
            for s in range(0, N, MINIBATCH):
                mb = idxp[s:s + MINIBATCH]
                mean, std, v = ac(bo[mb])
                dist = torch.distributions.Normal(mean, std)
                lp = dist.log_prob(ba[mb]).sum(-1)
                _logr = lp - blp[mb]
                with torch.no_grad():
                    _kl = ((_logr.exp() - 1.0) - _logr).mean().item()
                if _kl > 1.5 * KL_TARGET:
                    _stopped = True
                    break
                ratio = _logr.exp()
                a_mb = badv[mb]
                s1 = ratio * a_mb
                s2 = torch.clamp(ratio, 1 - CLIP, 1 + CLIP) * a_mb
                pol_loss = -torch.min(s1, s2).mean()
                val_loss = (v - bret[mb]).pow(2).mean()
                ent = dist.entropy().sum(-1).mean()
                loss = pol_loss + VCOEF * val_loss - ent_coef * ent
                opt.zero_grad(); loss.backward()
                torch.nn.utils.clip_grad_norm_(ac.parameters(), 1.0)
                opt.step()

        mean_cmdv = (fwd_sum / T).mean().item()             # m/s along the commanded direction
        mean_track = (track_sum / T).mean().item()
        mean_stag = (stag_sum / T).mean().item()            # mean penalty; should die as envs move
        fall_pct = 100.0 * fall_sum.mean().item()           # % of envs that fell this episode
        surv = 100.0 * alive_b[-1].mean().item()
        per_cmd = []
        for ci in range(CMD_DIM):
            msk = cmd == ci
            if msk.any():
                per_cmd.append(f'{CMDS[ci][:4]}={(fwd_sum[msk] / T).mean().item():.3f}(n={int(msk.sum())})')
        el = time.perf_counter() - t_all
        print(f'  {it:4d}{rew_b.mean().item():9.4f}{mean_cmdv:7.3f}{mean_track:8.3f}{mean_stag:7.3f}'
              f'{fall_pct:7.1f}{surv:7.1f}{time.perf_counter()-ti:7.1f}{el:8.0f}   '
              + ' '.join(per_cmd), flush=True)
        # ── ATOMIC CHECKPOINT WRITE ─────────────────────────────────────────────────────────
        # A power fluctuation on 2026-08-01 caught torch.save MID-WRITE and left a truncated tar:
        # the round-3 policy failed to load with KeyError('storages') and five and a half hours of
        # training were gone. Rounds 1 and 2 survived only because nothing was writing them.
        #
        # Write to a temporary file, flush it to the platter, THEN rename. os.replace is atomic on
        # every platform this runs on, so the checkpoint on disk is always a whole one -- either
        # the previous round or the new one, never half of either.
        # fsync needs a WRITABLE handle -- 'rb' raises EBADF on Windows, which killed this run
        # once already. 'rb+' opens for update without truncating what torch.save just wrote.
        _tmp = str(out) + '.tmp'
        torch.save(ac.state_dict(), _tmp)
        try:
            with open(_tmp, 'rb+') as _f:
                _f.flush()
                os.fsync(_f.fileno())
        except OSError:
            pass          # durability is a bonus; the ATOMIC RENAME below is the actual guarantee
        os.replace(_tmp, out)
        # AND THE CURVE GOES TO DISK, not only to stdout. The line printed above is the only direct
        # proof this run is LEARNING rather than coasting -- gpu_gate says so explicitly, because
        # heat and activity can both be faked. It was going to a terminal nobody was capturing, so
        # after the crash there was no way to tell whether round 3 had been improving.
        with open(str(out).replace('.pt', '.curve.tsv'), 'a', encoding='utf8') as _c:
            _row = [it, rew_b.mean().item(), mean_cmdv, mean_track, fall_pct, surv,
                    round(_kl, 5), int(_stopped)]
            _c.write("\t".join(str(x) for x in _row) + "\n")
        np.save(OUT_META, dict(OBS=OBS, HID=HID, ACT=ACT, CMD_DIM=CMD_DIM, CMDS=CMDS,
                               OBS_LAYOUT='[quat(4), angvel(3), linvel(3), qpos(nj), qvel(nj), '
                                          'cmd_onehot(4: forward,backward,left,right)]',
                               STAND_Z=STAND_Z,
                               NOTE='round 3: warm-started from the round-2 directional policy with '
                                    'fall penalty + 15 s episode horizon (T=750); '
                                    'see tools/train_myobody_directional.py'))
        it += 1

    print(f'\n  BOUND REACHED: {it} iterations in {time.perf_counter()-t_all:.0f}s')
    print(f'  saved {out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
