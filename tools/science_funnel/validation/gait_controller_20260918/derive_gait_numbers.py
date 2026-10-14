"""Derive the macaque gait-controller numbers from the admitted movement data.

Lane gait-controller-20260918. Reads ONLY the two pinned data artifacts that
carry bytes in-tree:

  1. tools/science_funnel/data/oku_bipedal/42003_2021_1831_MOESM2_ESM.xlsx
     (Oku, Ide & Ogihara 2021, Commun Biol 4:1831, PMC7940622, Supplementary
     Data 1; sha256 pinned in that dir's download_receipt.json) -- two sheets,
     Fig3ABC (GRF h/v + hip/knee/ankle/MP angles + torques, TWO column blocks:
     FIRST = before foot-morphology alteration = the digitigrade macaque,
     SECOND = after) and Fig3D (10 muscle forces, same two blocks); x =
     0..100 percent of the gait cycle, angles rad, GRF N, torques N.m.

  2. tools/science_funnel/data/janisch_kinematics/wildprimate_kin.csv
     (Janisch et al. 2024, figshare 10.6084/m9.figshare.23231366; sha256
     pinned in that dir's download_receipt.json) -- 386 stride rows, 14
     species, angles at TD/MID/LO in degrees + excursions + yields + mass.

Paper-anchored constants (quoted from the pinned fulltext
PMC7940622_fulltext.xml, not invented):
  segment table (Table 1): HAT 8.184 kg/0.482 m, thigh 0.557/0.163,
    shank 0.269/0.182, foot 0.080/0.074, phalanges 0.021/0.045 (COM % 52/41/
    40/62/50; MOI about segment COM as listed)  => nine-segment total mass.
  simulated intact gait: cycle 0.71 s, stride 0.72 m, speed 1.01 m/s, duty
    0.67; MEASURED macaque: cycle 0.75 s, stride 0.79 m, duty 0.65.
  after alteration: cycle 0.72 s, stride 0.70 m, speed 0.97 m/s.
  angle/moment sign convention: hip flexion +, knee extension +, ankle and MP
    dorsiflexion +; GRF h negative = braking, positive = propelling.

The Granatosky and Higurashi Dryad bytes are DEFERRED (admitted as digest-
pinned identity records only), so NO number in this derivation comes from
them; their metadata-level claims are used only where explicitly labelled.

Outputs: prints human-readable tables and writes derived_numbers.json next to
this script. Deterministic: no clock, no randomness, fixed float formatting.
"""
import csv
import io
import json
import math
import re
import statistics
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

SSML = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
OFFDOC = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKGREL = 'http://schemas.openxmlformats.org/package/2006/relationships'

ROOT = Path(__file__).resolve().parents[4]
OKU = ROOT / 'tools/science_funnel/data/oku_bipedal/42003_2021_1831_MOESM2_ESM.xlsx'
JANISCH = ROOT / 'tools/science_funnel/data/janisch_kinematics/wildprimate_kin.csv'
OUT = Path(__file__).resolve().parent / 'derived_numbers.json'

G = 9.80665
# Table 1 of the pinned fulltext (2D nine-segment model)
SEG = {  # name: (mass_kg, length_m, com_frac, I_com_kg_m2)
    'HAT': (8.184, 0.482, 0.52, 2.07e-2),
    'thigh': (0.557, 0.163, 0.41, 1.61e-3),
    'shank': (0.269, 0.182, 0.40, 7.01e-4),
    'foot': (0.080, 0.074, 0.62, 5.49e-5),
    'phalanges': (0.021, 0.045, 0.50, 6.26e-6),
}
T_BEFORE, T_AFTER = 0.71, 0.72        # cycle duration s (paper text)
V_BEFORE, V_AFTER = 1.01, 0.97        # m/s
L_STRIDE_BEFORE, L_STRIDE_AFTER = 0.72, 0.70  # m
DUTY_MEASURED, CYCLE_MEASURED, STRIDE_MEASURED = 0.65, 0.75, 0.79  # paper text


def col_index(ref):
    letters = re.match(r'([A-Z]+)', ref).group(1)
    out = 0
    for ch in letters:
        out = out * 26 + (ord(ch) - 64)
    return out - 1


def sheet_rows(path):
    """Sheet name -> list of rows (dict col-index -> string) for the xlsx."""
    z = zipfile.ZipFile(path)
    workbook = ET.fromstring(z.read('xl/workbook.xml'))
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    rid = {r.get('Id'): r.get('Target') for r in rels.findall(f'{{{PKGREL}}}Relationship')}
    shared = []
    if 'xl/sharedStrings.xml' in z.namelist():
        sroot = ET.fromstring(z.read('xl/sharedStrings.xml'))
        shared = [''.join(t.text or '' for t in si.iter(f'{{{SSML}}}t'))
                  for si in sroot.findall(f'{{{SSML}}}si')]
    out = {}
    for sheet in workbook.iter(f'{{{SSML}}}sheet'):
        name = sheet.get('name')
        target = rid[sheet.get(f'{{{OFFDOC}}}id')]
        if not target.startswith('xl/'):
            target = 'xl/' + target.lstrip('/')
        root = ET.fromstring(z.read(target))
        rows = []
        for row in root.iter(f'{{{SSML}}}row'):
            cells = {}
            for cell in row.findall(f'{{{SSML}}}c'):
                kind = cell.get('t')
                if kind == 'inlineStr':
                    v = ''.join(t.text or '' for t in cell.iter(f'{{{SSML}}}t'))
                else:
                    node = cell.find(f'{{{SSML}}}v')
                    if node is None:
                        continue
                    v = shared[int(node.text)] if kind == 's' else node.text
                if v is not None and str(v).strip() != '':
                    cells[col_index(cell.get('r'))] = str(v)
            if cells:
                rows.append(cells)
        out[name] = rows
    return out


def f(row, col):
    v = row.get(col)
    if v is None:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def trapz(xs, ys):
    return sum(0.5 * (ys[i] + ys[i + 1]) * (xs[i + 1] - xs[i]) for i in range(len(xs) - 1))


def derive_oku_block(rows, cols, t_cycle):
    """cols: dict signal -> column index. rows: data rows with x 0..100."""
    data = []
    for r in rows:
        x = f(r, 0)
        if x is None:
            continue
        rec = {'x': x}
        for k, c in cols.items():
            rec[k] = f(r, c)
        if all(rec[k] is not None for k in cols):
            data.append(rec)
    data.sort(key=lambda d: d['x'])
    xs = [d['x'] for d in data]
    out = {'n_samples': len(data), 'x_min': min(xs), 'x_max': max(xs)}

    # --- gait-cycle timing from the vertical GRF ---
    gv = [d['GRFv'] for d in data]
    stance = [d['x'] for d, v in zip(data, gv) if v > 0.0]
    # duty factor: fraction of the sampled cycle in contact. x=0 is touch-down
    # (contact instant) and the sample grid is uniform, so count contact rows
    # plus the x=0 boundary row.
    duty = (len(stance) + 1) / (len(xs))
    toe_off_x = int(max(stance))
    out['duty_factor'] = round(duty, 4)
    out['toe_off_pct'] = toe_off_x
    out['swing_pct'] = round(100 - toe_off_x, 1)
    out['stance_dur_s'] = round(toe_off_x / 100.0 * t_cycle, 4)
    out['swing_dur_s'] = round((100 - toe_off_x) / 100.0 * t_cycle, 4)

    # --- vertical GRF profile ---
    peak_i = max(range(len(gv)), key=lambda i: gv[i])
    out['grf_v_peak_N'] = round(gv[peak_i], 3)
    out['grf_v_peak_pct'] = xs[peak_i]
    out['grf_v_peak_xBW'] = round(gv[peak_i] / BW, 4)
    out['grf_v_impulse_Ns'] = round(trapz(xs, gv) / 100.0 * t_cycle, 4)
    out['grf_v_mean_stance_N'] = round(
        trapz(xs[:toe_off_x + 1], gv[:toe_off_x + 1]) / max(1e-9, toe_off_x), 4)
    # loading rate: max dGRFv/dt over the rising phase (forward difference)
    rates = [(gv[i + 1] - gv[i]) / ((xs[i + 1] - xs[i]) / 100.0 * t_cycle)
             for i in range(toe_off_x)]
    out['grf_v_load_rate_max_N_s'] = round(max(rates), 2)
    out['grf_v_load_rate_at_50BW_N_s'] = None
    for i in range(toe_off_x):
        if gv[i] <= 0.5 * BW <= gv[i + 1]:
            out['grf_v_load_rate_at_50BW_N_s'] = round(
                (gv[i + 1] - gv[i]) / ((xs[i + 1] - xs[i]) / 100.0 * t_cycle), 2)
            break
    out['grf_v_time_to_peak_ms'] = round(xs[peak_i] / 100.0 * t_cycle * 1000, 1)

    # --- horizontal GRF (braking < 0 < propelling) ---
    gh = [d['GRFh'] for d in data]
    out['grf_h_brake_peak_N'] = round(min(gh), 3)
    out['grf_h_prop_peak_N'] = round(max(gh), 3)
    cross = None
    for i in range(toe_off_x):
        if gh[i] < 0 <= gh[i + 1]:
            cross = xs[i] + 0.5
            break
    out['grf_h_brake_prop_cross_pct'] = cross
    out['grf_h_net_impulse_Ns'] = round(trapz(xs, gh) / 100.0 * t_cycle, 4)
    out['grf_h_brake_impulse_Ns'] = round(trapz(xs[:toe_off_x + 1],
        [min(0.0, v) for v in gh[:toe_off_x + 1]]) / 100.0 * t_cycle, 4)
    out['grf_h_prop_impulse_Ns'] = round(trapz(xs[:toe_off_x + 1],
        [max(0.0, v) for v in gh[:toe_off_x + 1]]) / 100.0 * t_cycle, 4)

    # --- joint angles ---
    angles = {}
    for joint in ('hip', 'knee', 'ankle', 'MP'):
        th = [d[joint + '_ang'] for d in data]
        lo = min(th)
        hi = max(th)
        peak = {'td_rad': th[0], 'min_rad': lo, 'x_min_pct': xs[th.index(lo)],
                'max_rad': hi, 'x_max_pct': xs[th.index(hi)],
                'excursion_rad': round(hi - lo, 4),
                'excursion_deg': round(math.degrees(hi - lo), 2)}
        angles[joint] = peak
    out['angles'] = angles

    # --- joint torques ---
    tors = {}
    for joint in ('hip', 'knee', 'ankle', 'MP'):
        tq = [d[joint + '_tor'] for d in data]
        st = tq[:toe_off_x + 1]
        tors[joint] = {'td_Nm': round(tq[0], 4),
                       'min_Nm': round(min(tq), 4), 'x_min_pct': xs[tq.index(min(tq))],
                       'max_Nm': round(max(tq), 4), 'x_max_pct': xs[tq.index(max(tq))],
                       'peak_abs_stance_Nm': round(max(abs(v) for v in st), 4),
                       'rms_stance_Nm': round(math.sqrt(sum(v * v for v in st) / len(st)), 4)}
    out['torques'] = tors

    # --- per-joint mechanical work over the cycle: W = int tau dtheta ---
    works = {}
    for joint in ('hip', 'knee', 'ankle', 'MP'):
        wp = wn = 0.0
        for i in range(len(data) - 1):
            dq = data[i + 1][joint + '_ang'] - data[i][joint + '_ang']
            dw = 0.5 * (data[i][joint + '_tor'] + data[i + 1][joint + '_tor']) * dq
            if dw > 0:
                wp += dw
            else:
                wn += dw
        works[joint] = {'positive_J': round(wp, 4), 'negative_J': round(wn, 4),
                        'net_J': round(wp + wn, 4)}
    out['work_per_cycle_J'] = works
    out['work_positive_total_J'] = round(sum(w['positive_J'] for w in works.values()), 4)
    out['work_negative_total_J'] = round(sum(w['negative_J'] for w in works.values()), 4)

    # peak positive mechanical power per joint (tau * dtheta/dt)
    pows = {}
    for joint in ('hip', 'knee', 'ankle', 'MP'):
        best = 0.0
        for i in range(len(data) - 1):
            dt = (xs[i + 1] - xs[i]) / 100.0 * t_cycle
            p = 0.5 * (data[i][joint + '_tor'] + data[i + 1][joint + '_tor']) * \
                (data[i + 1][joint + '_ang'] - data[i][joint + '_ang']) / dt
            best = max(best, p)
        pows[joint] = round(best, 3)
    out['peak_positive_power_W'] = pows

    # --- controller node table: piecewise-linear phi -> target every 10% ---
    nodes = {}
    for joint in ('hip', 'knee', 'ankle', 'MP'):
        th = [d[joint + '_ang'] for d in data]
        table = []
        for k in range(11):
            xk = k * 10.0
            # data are on integer percent grid: linear interp
            i0 = int(xk)
            frac = xk - i0
            v = th[i0] * (1 - frac) + th[min(i0 + 1, len(th) - 1)] * frac
            table.append(round(v, 4))
        nodes[joint] = table
    out['node_table_rad'] = nodes

    # max node-table reconstruction error vs samples
    errs = {}
    for joint in ('hip', 'knee', 'ankle', 'MP'):
        th = [d[joint + '_ang'] for d in data]
        tab = nodes[joint]
        e = 0.0
        for i, x in enumerate(xs):
            pos = x / 10.0
            k0 = int(pos)
            frac = pos - k0
            k1 = min(k0 + 1, 10)
            v = tab[k0] * (1 - frac) + tab[k1] * frac
            e = max(e, abs(v - th[i]))
        errs[joint] = round(e, 5)
    out['node_table_max_err_rad'] = errs
    return out


def derive_oku():
    sheets = sheet_rows(OKU)
    fig = sheets['Fig3ABC']
    header = fig[0]
    before_cols = {'GRFh': 1, 'GRFv': 2, 'hip_ang': 3, 'knee_ang': 4, 'ankle_ang': 5,
                   'MP_ang': 6, 'hip_tor': 7, 'knee_tor': 8, 'ankle_tor': 9, 'MP_tor': 10}
    after_cols = {k: v + 11 for k, v in before_cols.items()}
    data_rows = fig[1:]
    before = derive_oku_block(data_rows, before_cols, T_BEFORE)
    after = derive_oku_block(data_rows, after_cols, T_AFTER)
    # muscle forces
    d = sheets['Fig3D']
    dh = d[0]
    muscles = [dh[c].strip() for c in range(1, 11)]
    mforce = {'muscles': muscles}
    for tag, base in (('before', 0), ('after', 11)):
        peaks = {}
        for i, m in enumerate(muscles):
            col = base + 1 + i
            vals = [f(r, col) for r in d[1:]]
            vals = [v for v in vals if v is not None]
            peaks[m] = {'peak_N': round(max(vals), 2), 'mean_N': round(sum(vals) / len(vals), 2)}
        mforce[tag] = peaks
    return before, after, mforce


def leg_pendulum():
    """Swing leg as a compound pendulum about the hip (Table 1 numbers)."""
    chain = [('thigh', 0.0), ('shank', SEG['thigh'][1]), ('foot', SEG['thigh'][1] + SEG['shank'][1]),
             ('phalanges', SEG['thigh'][1] + SEG['shank'][1] + SEG['foot'][1])]
    I = m_tot = md = 0.0
    for name, base in chain:
        m, L, comp, Ic = SEG[name]
        dcom = base + comp * L
        I += Ic + m * dcom * dcom
        m_tot += m
        md += m * dcom
    dcom_leg = md / m_tot
    T = 2 * math.pi * math.sqrt(I / (m_tot * G * dcom_leg))
    return {'I_hip_kg_m2': round(I, 6), 'm_leg_kg': round(m_tot, 4),
            'd_com_m': round(dcom_leg, 4), 'T_pendulum_s': round(T, 4),
            'half_period_s': round(T / 2, 4)}


def froude(v, h_leg):
    return round(v * v / (G * h_leg), 4)


def derive_janisch():
    with open(JANISCH, newline='', encoding='utf-8-sig') as fh:
        rows = list(csv.DictReader(fh))
    cerc = ('Papio', 'Chlorocebus', 'Cercopithecus', 'Lophocebus')
    subset = [r for r in rows if r['Species'].split('_')[0] in cerc]
    out = {'n_rows_total': len(rows), 'n_species_total': len(set(r['Species'] for r in rows)),
           'n_cercopithecoid_strides': len(subset),
           'cercopithecoid_species': sorted(set(r['Species'] for r in subset)),
           'per_species': {}}
    for sp in out['cercopithecoid_species']:
        out['per_species'][sp] = sum(1 for r in subset if r['Species'] == sp)

    def stat(vals):
        vals = [float(v) for v in vals if v not in ('', 'NA')]
        if not vals:
            return None
        return {'n': len(vals), 'mean': round(statistics.mean(vals), 3),
                'sd': round(statistics.pstdev(vals), 3),
                'min': round(min(vals), 3), 'max': round(max(vals), 3)}

    fields = (['hipTD', 'kneeTD', 'ankleTD', 'shoulderTD', 'elbowTD', 'wristTD',
               'hipMID', 'kneeMID', 'ankleMID', 'shoulderMID', 'elbowMID', 'wristMID',
               'hipLO', 'kneeLO', 'ankleLO', 'shoulderLO', 'elbowLO', 'wristLO']
              + ['shoulderExcur', 'hipExcur', 'flExcur', 'hlExcur',
                 'elbowYld', 'kneeYld', 'Mass'])
    out['stats'] = {k: stat([r[k] for r in subset]) for k in fields}
    out['stats_all_species'] = {k: stat([r[k] for r in rows]) for k in
                                ('shoulderExcur', 'hipExcur', 'kneeYld', 'elbowYld', 'Mass')}
    # leg length proxy: mean thigh+shank not in this dataset; only Mass is.
    return out


def engine_scale(numbers):
    """Scale the Oku per-stride energies to the two body scales the ladder uses.

    Scaling law (dynamic + geometric similarity): torque ~ m g l, angle
    amplitude dimensionless, so per-stride joint work scales ~ m g l. With
    l ~ m^(1/3) (geometric similarity), E ~ m^(4/3) g. The proportionality is
    pinned by the Oku reference instance (m_ref = 10.038 kg), so this is a
    derivation with ONE stated assumption (similarity), not a fit.
    """
    m_ref = BODY_MASS
    ref_work = numbers['oku_before_alteration']['work_positive_total_J']
    out = {}
    for tag, m in (('coupled_arm_assembly_7p006kg', 7.006001),):
        scale = (m / m_ref) ** (4.0 / 3.0)
        out[tag] = {'mass_kg': m, 'energy_scale_factor': round(scale, 5),
                    'work_positive_total_J': round(ref_work * scale, 4)}
    return out


BW_SEG = BODY_SEGMENTS = None  # placeholder naming clarity

# --- body mass from Table 1: HAT + 2 x (thigh, shank, foot, phalanges) ---
BODY_MASS = SEG['HAT'][0] + 2 * (SEG['thigh'][0] + SEG['shank'][0] + SEG['foot'][0]
                                 + SEG['phalanges'][0])
BW = BODY_MASS * G
LEG_LEN = SEG['thigh'][1] + SEG['shank'][1] + SEG['foot'][1]  # hip->MP approx


def main():
    before, after, mforce = derive_oku()
    jan = derive_janisch()
    pend = leg_pendulum()
    result = {
        'sources': {
            'oku_xlsx': 'tools/science_funnel/data/oku_bipedal/42003_2021_1831_MOESM2_ESM.xlsx',
            'janisch_csv': 'tools/science_funnel/data/janisch_kinematics/wildprimate_kin.csv',
            'deferred': ['granatosky_gait (11 analytic tables, bytes deferred, digest-pinned)',
                         'higurashi_gait (2 xlsx, bytes deferred, digest-pinned)'],
        },
        'body_model': {
            'mass_kg': round(BODY_MASS, 4), 'weight_N': round(BW, 3),
            'leg_len_hip_to_MP_m': round(LEG_LEN, 4),
            'segments_Table1': {k: {'mass_kg': v[0], 'length_m': v[1],
                                    'com_frac': v[2], 'I_com': v[3]} for k, v in SEG.items()},
        },
        'timing_paper': {'simulated_before': {'cycle_s': T_BEFORE, 'stride_m': L_STRIDE_BEFORE,
                                              'speed_m_s': V_BEFORE, 'duty_factor': 0.67},
                         'measured_macaque': {'cycle_s': CYCLE_MEASURED,
                                              'stride_m': STRIDE_MEASURED,
                                              'duty_factor': DUTY_MEASURED},
                         'simulated_after': {'cycle_s': T_AFTER, 'stride_m': L_STRIDE_AFTER,
                                             'speed_m_s': V_AFTER}},
        'oku_before_alteration': before,
        'oku_after_alteration': after,
        'oku_muscle_forces_N': mforce,
        'leg_pendulum': pend,
        'froude_before': froude(V_BEFORE, LEG_LEN),
        'froude_measured': froude(0.79 / 0.75, LEG_LEN),
        'swing_as_pendulum': {
            'swing_dur_before_s': before['swing_dur_s'],
            'swing_dur_over_half_period': round(before['swing_dur_s'] / (pend['half_period_s']), 4)},
        'janisch_cercopithecoids': jan,
        'engine_scaling': None,  # filled below
    }
    result['engine_scaling'] = engine_scale(result)
    # per-drive budget check at macaque scale and arm scale
    budget = {}
    for joint, w in before['work_per_cycle_J'].items():
        budget[joint] = {
            'positive_J_at_10kg': w['positive_J'],
            'positive_J_at_arm_scale': round(
                w['positive_J'] * result['engine_scaling']['coupled_arm_assembly_7p006kg']
                ['energy_scale_factor'], 4),
        }
    result['per_drive_budget_check_J'] = budget
    OUT.write_text(json.dumps(result, indent=1) + '\n', encoding='utf-8')

    # ---- printed tables ----
    print('BODY: mass %.4f kg  BW %.2f N  leg(hip->MP) %.3f m' % (BODY_MASS, BW, LEG_LEN))
    print('Froude (sim before) %.3f  (measured) %.3f' % (
        froude(V_BEFORE, LEG_LEN), froude(0.79 / 0.75, LEG_LEN)))
    print('leg compound pendulum: I=%.4f  m=%.3f  d=%.4f  T=%.3f s (half %.3f)'
          % (pend['I_hip_kg_m2'], pend['m_leg_kg'], pend['d_com_m'],
             pend['T_pendulum_s'], pend['half_period_s']))
    for tag, blk, T in (('BEFORE (digitigrade)', before, T_BEFORE),
                        ('AFTER (plantigrade)', after, T_AFTER)):
        print('\n=== OKU %s (T=%.2f s) ===' % (tag, T))
        print('duty %.4f  toe-off %s%%  stance %.3f s  swing %.3f s'
              % (blk['duty_factor'], blk['toe_off_pct'], blk['stance_dur_s'], blk['swing_dur_s']))
        print('GRFv peak %.1f N = %.3f BW at %s%% (t=%.0f ms)  impulse %.3f Ns  loadrate %.0f N/s'
              % (blk['grf_v_peak_N'], blk['grf_v_peak_xBW'], blk['grf_v_peak_pct'],
                 blk['grf_v_time_to_peak_ms'], blk['grf_v_impulse_Ns'],
                 blk['grf_v_load_rate_max_N_s']))
        print('GRFh brake %.2f N  prop %.2f N  cross %s%%  net impulse %.4f Ns  brake impulse %.4f Ns'
              % (blk['grf_h_brake_peak_N'], blk['grf_h_prop_peak_N'],
                 blk['grf_h_brake_prop_cross_pct'], blk['grf_h_net_impulse_Ns'],
                 blk['grf_h_brake_impulse_Ns']))
        for j in ('hip', 'knee', 'ankle', 'MP'):
            a = blk['angles'][j]
            print(' %5s ang: TD %+.3f  min %+.3f@%s%%  max %+.3f@%s%%  exc %.1f deg'
                  % (j, a['td_rad'], a['min_rad'], a['x_min_pct'], a['max_rad'],
                     a['x_max_pct'], a['excursion_deg']))
        for j in ('hip', 'knee', 'ankle', 'MP'):
            t = blk['torques'][j]
            w = blk['work_per_cycle_J'][j]
            print(' %5s tor: TD %+.2f  min %+.2f@%s%%  max %+.2f@%s%%  |peak| %.2f  rms %.2f'
                  '  W+ %.3f J  W- %.3f J  net %+.3f J  P+max %.1f W'
                  % (j, t['td_Nm'], t['min_Nm'], t['x_min_pct'], t['max_Nm'],
                     t['x_max_pct'], t['peak_abs_stance_Nm'], t['rms_stance_Nm'],
                     w['positive_J'], w['negative_J'], w['net_J'],
                     blk['peak_positive_power_W'][j]))
        print(' node table max err (rad):', blk['node_table_max_err_rad'])
        print(' total W+ %.3f J  W- %.3f J  |net| %.3f J'
              % (blk['work_positive_total_J'], blk['work_negative_total_J'],
                 blk['work_positive_total_J'] + blk['work_negative_total_J']))
    print('\nMUSCLE peaks before:', {m: v['peak_N'] for m, v in mforce['before'].items()})
    print('\nJANISCH: %d rows, %d species; cercopithecoid strides %d across %s'
          % (jan['n_rows_total'], jan['n_species_total'], jan['n_cercopithecoid_strides'],
             jan['per_species']))
    for k in ('Mass', 'shoulderExcur', 'hipExcur', 'kneeYld', 'elbowYld',
              'hipTD', 'kneeTD', 'ankleTD', 'shoulderTD', 'elbowTD', 'wristTD'):
        s = jan['stats'][k]
        print(' %14s n=%3d mean %8.2f sd %7.2f range [%7.2f, %7.2f]'
              % (k, s['n'], s['mean'], s['sd'], s['min'], s['max']))
    print('\nSCALING arm 7.006 kg: factor %.4f  W+ %.3f J'
          % (result['engine_scaling']['coupled_arm_assembly_7p006kg']['energy_scale_factor'],
             result['engine_scaling']['coupled_arm_assembly_7p006kg']['work_positive_total_J']))
    print('wrote', OUT)


if __name__ == '__main__':
    main()
