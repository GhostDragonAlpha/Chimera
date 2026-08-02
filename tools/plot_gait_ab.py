import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.executable).parent.parent.parent))
import numpy as np
from daimon_runtime import setup_plot
setup_plot()
import matplotlib.pyplot as plt

tr0 = np.load('ChimeraEngine/output/policy_walk_trace.npz')
tr1 = np.load('ChimeraEngine/output/policy_walk_trace__myobody_walk_mocap.npz')
# RULE 20 -- the instrument must move with the membrane and keep no copy of it. This was
# `STRIDE_S = 1.127`, an EARTH stride typed into a plot that judges a body in 7.076 m/s^2: the
# x-axis was mislabelled by 4% and every phase read off it was wrong by the same amount.
# Read the body's own published cadence; refuse if it is absent rather than defaulting.
import sys as _sys; _sys.path.insert(0, str(Path(__file__).resolve().parent) if 'Path' in dir() else 'tools')
import json as _json, pathlib as _pl
_led = [q for q in _pl.Path(__file__).resolve().parent.parent.joinpath('story').rglob('numbers.json')
        if q.parent.name == 'theHuman']
if not _led or 'step_time_s' not in _json.loads(_led[0].read_text(encoding='utf8')):
    raise SystemExit('theHuman publishes no step_time_s -- refusing to assume an Earth stride.')
STRIDE_S = 2.0 * float(_json.loads(_led[0].read_text(encoding='utf8'))['step_time_s'])

fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.2), sharey=True)
colors = {'hip': '#c0392b', 'knee': '#2471a3', 'ankle': '#1e8449'}
x = np.linspace(0, 100, 101)

ax = axes[0]
for j in ('hip', 'knee', 'ankle'):
    m = tr0[f'ref_{j}']; s = tr0[f'ref_{j}_std']
    ax.plot(x, m, color=colors[j], lw=2.2, label=f'{j}')
    ax.fill_between(x, m - s, m + s, color=colors[j], alpha=0.15)
ax.set_title('A - REAL HUMAN (CMU mocap 35_01 walk, mean +/- std, 4 cycles)', fontsize=10)
ax.set_xlabel('gait cycle (%)  [0 = heel strike, measured by Zeni rule]')
ax.set_ylabel('sagittal angle (deg)  +flexion / +dorsiflexion')
ax.grid(alpha=0.3); ax.legend(loc='lower right', fontsize=9)
ax.set_xlim(0, 100)

ax = axes[1]
t = tr0['pol_angles_t']
xc = t / STRIDE_S * 100.0                      # same time base as the human, in cycle-%
fell = tr0['pol_rootz'] < 0.6 * 0.9802
tfall = xc[np.argmax(fell)] if fell.any() else xc[-1]
for j in ('hip', 'knee', 'ankle'):
    a = 0.5 * (tr0[f'pol_{j}_l'] + tr0[f'pol_{j}_r'])
    ax.plot(xc, a, color=colors[j], lw=2.0, label=f'{j} (shipped policy)')
    m = tr0[f'ref_{j}']
    ax.plot(x, m, color=colors[j], lw=1.0, ls='--', alpha=0.55)
if tr1['pol_angles_t'].size:
    t1 = tr1['pol_angles_t']; xc1 = t1 / STRIDE_S * 100.0
    for j in ('hip', 'knee', 'ankle'):
        a1 = 0.5 * (tr1[f'pol_{j}_l'] + tr1[f'pol_{j}_r'])
        ax.plot(xc1, a1, color=colors[j], lw=1.2, ls=':', label=f'{j} (mocap fine-tune)')
ax.axvline(tfall, color='k', lw=1.2)
if fell.any():
    ax.text(tfall + 2, 60, f'FALLS at {t[np.argmax(fell)]:.1f} s', fontsize=9, rotation=90, va='bottom')
ax.set_title('B - POLICY (myobody_walk, best of 5 seeds; dashed = human; dotted = fine-tuned)', fontsize=10)
ax.set_xlabel(f'time on the human cycle base (% of {STRIDE_S:.4f} s stride)')
ax.grid(alpha=0.3); ax.legend(loc='lower right', fontsize=8)
ax.set_xlim(0, max(160, tfall + 20))

fig.suptitle('Gait A/B: trained myobody walk vs real human mocap - same vector-angle math both sides',
             fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.94])
out = Path('ChimeraEngine/output/gait_mocap_AB.png')
fig.savefig(out, bbox_inches='tight', dpi=150)
print('wrote', out)
