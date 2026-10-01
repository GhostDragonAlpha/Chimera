"""THE WAVE-28B LOAD MAP (receipt_wave28b.json, the race-C bank's load-share face).

Mines the scratch probe's per-tick trace ([qpts]/[qhull]/[qjt] + the lane's own
[dv]/[dvf] lines) into the load map: per-contact reactions, per-joint demands,
the fore share, the CoM-static share line, and the unload decomposition.

The probe binary is a byte-copy of gait_unit.cpp with read-only prints; its
stdout JSON is byte-equal to the lane binaries' on both scenes (the w27 scene
and the legacy scene) -- the instrument moved no dynamics byte. The legacy run
(the two height-hold recipe keys stripped; the controller's documented
absent-key path) reproduces the wave-26 state verbatim (refusal 105, ledger
0.291120, stdout JSON byte-equal to the parent lane's recorded baseline), and
this script's share series closes to the receipted 9.4/28/10.3% there -- the
instrument validated against the receipted numbers before the w27 map is read.

Usage:
  python -B derive_load_map_wave28b.py <probe_trace.log> <out.json> [t0 t1]
"""
import json, math, re, sys, collections

QPTS = re.compile(r'\[qpts\] t=(\d+) (\S+) px=([-\d.e+]+) py=([-\d.e+]+) '
                  r'gap=(\S+) touch=(\d) rxn=([-\d.e+]+) frc=([-\d.e+]+) slip=([-\d.e+]+)')
QHULL = re.compile(r'\[qhull\] t=(\d+) n=(\d+) com=\(([-\d.e+]+),([-\d.e+]+)\) in=(\d) hull:(.*)')
HULLPT = re.compile(r'\(([-\d.e+]+),([-\d.e+]+)\)')
QJT = re.compile(r'\[qjt\] t=(\d+) (\S+) ang=([-\d.e+]+) tgt=([-\d.e+]+) tau=([-\d.e+]+) cap=([-\d.e+]+)')
DVF = re.compile(r'\[dvf\] t=(\d+) leg=(\d) mode=(\d) tgt=\(([-\d.e+]+),([-\d.e+]+)\) '
                 r'sh=\(([-\d.e+]+),([-\d.e+]+)\) D=([-\d.e+]+) off=([-\d.e+]+) hr=([-\d.e+]+) '
                 r'q1a=([-\d.e+]+) q1u=([-\d.e+]+) q2a=([-\d.e+]+) q2u=([-\d.e+]+) pins=(\d+) fol=(\d+)')


def mine(path):
    pts = collections.defaultdict(dict)      # t -> name -> dict
    hull = {}                                # t -> dict(com_x, com_y, in, pts)
    jt = collections.defaultdict(dict)       # t -> joint name -> dict
    dvf = {}                                 # t -> leg -> dict
    for line in open(path, encoding='utf-8', errors='replace'):
        m = QPTS.match(line)
        if m:
            t = int(m.group(1))
            pts[t][m.group(2)] = {'px': float(m.group(3)), 'py': float(m.group(4)),
                                  'gap': float(m.group(5)), 'touch': int(m.group(6)),
                                  'rxn': float(m.group(7)), 'frc': float(m.group(8)),
                                  'slip': float(m.group(9))}
            continue
        m = QHULL.match(line)
        if m:
            hull[int(m.group(1))] = {'com_x': float(m.group(3)), 'com_y': float(m.group(4)),
                                     'in': int(m.group(5)), 'n': int(m.group(2)),
                                     'pts': [(float(a), float(b)) for a, b in HULLPT.findall(m.group(6))]}
            continue
        m = QJT.match(line)
        if m:
            jt[int(m.group(1))][m.group(2)] = {'ang': float(m.group(3)), 'tgt': float(m.group(4)),
                                               'tau': float(m.group(5)), 'cap': float(m.group(6))}
            continue
        m = DVF.match(line)
        if m:
            dvf.setdefault(int(m.group(1)), {})[int(m.group(2))] = {
                'mode': int(m.group(3)), 'hr': float(m.group(10)),
                'tgt_x': float(m.group(4)), 'tgt_y': float(m.group(5)),
                'sh_x': float(m.group(6)), 'sh_y': float(m.group(7))}
    return pts, hull, jt, dvf


def static_share(plant_pts, com_x):
    """The 2-pair CoM-static fore share over the planted paw set (east axis).
    Returns (share, x_hind, x_fore) or (None, ...) when the line is undefined."""
    hind = [p['px'] for n, p in plant_pts.items() if not n.startswith('fore_')]
    fore = [p['px'] for n, p in plant_pts.items() if n.startswith('fore_')]
    x_h = sum(hind) / len(hind) if hind else None
    x_f = sum(fore) / len(fore) if fore else None
    if not hind or x_f is None or x_f == x_h:
        return None, x_h, x_f
    s = (com_x - x_h) / (x_f - x_h)
    return s, x_h, x_f


def classify(fore_pts, mode):
    """The unload class per the pre-registered definition."""
    worst = max(fore_pts, key=lambda p: p['rxn'])
    if mode == 1:
        return 'commanded_swing'
    if worst['gap'] > 1e-5:
        return 'stance_lifted'
    if worst['rxn'] < 0.5:
        return 'stance_geometry_unload'
    return 'stance_loaded'


def main():
    path, out_path = sys.argv[1], sys.argv[2]
    pts, hull, jt, dvf = mine(path)
    ticks = sorted(pts)
    series = []
    for t in ticks:
        d = pts[t]
        f_sum = sum(p['rxn'] for n, p in d.items() if n.startswith('fore_'))
        h_sum = sum(p['rxn'] for n, p in d.items() if not n.startswith('fore_'))
        share = 100.0 * f_sum / (f_sum + h_sum) if (f_sum + h_sum) > 1e-9 else None
        n_touch = sum(p['touch'] for p in d.values())
        hu = hull.get(t, {})
        plant = {n: p for n, p in d.items() if p['touch'] and p['gap'] <= 1e-5}
        ss, x_h, x_f = static_share(plant, hu.get('com_x', float('nan')))
        rec = {'t': t, 'fore_N': round(f_sum, 4), 'hind_N': round(h_sum, 4),
               'share_pct': None if share is None else round(share, 3),
               'n_touch': n_touch, 'in_hull': hu.get('in'), 'hull_n': hu.get('n'),
               'com_x': hu.get('com_x'), 'static_share_pct': None if ss is None else round(100.0 * min(max(ss, -1.0), 2.0), 3),
               'x_hind': None if x_h is None else round(x_h, 6),
               'x_fore': None if x_f is None else round(x_f, 6)}
        for leg, name in ((0, 'L'), (1, 'R')):
            fp = [p for n, p in d.items() if n.startswith(f'fore_{name.lower()}')]
            if fp and t in dvf and leg in dvf[t]:
                rec[f'fore{name}_class'] = classify(fp, dvf[t][leg]['mode'])
                rec[f'fore{name}_rxn'] = round(sum(p['rxn'] for p in fp), 4)
                rec[f'fore{name}_hr'] = round(dvf[t][leg]['hr'], 6)
                rec[f'fore{name}_mode'] = dvf[t][leg]['mode']
        series.append(rec)
    # per-joint demand peaks over the walk window [60, last)
    demands = {}
    for t in ticks:
        if t < 60:
            continue
        for nm, j in jt[t].items():
            a = demands.setdefault(nm, {'tau_abs_max': 0.0, 'tau_at_max': 0.0, 'cap': j['cap'], 't_at_max': t})
            if abs(j['tau']) > a['tau_abs_max']:
                a['tau_abs_max'] = abs(j['tau']); a['tau_at_max'] = j['tau']; a['t_at_max'] = t
    for nm, a in demands.items():
        a['pct_of_cap_at_max'] = round(100.0 * a['tau_abs_max'] / a['cap'], 2)
        a['tau_abs_max'] = round(a['tau_abs_max'], 5)
    out = {'source': path, 'n_ticks': len(ticks), 'series': series, 'demands_since_60': demands}
    json.dump(out, open(out_path, 'w', encoding='utf-8'), indent=1)
    print(f'wrote {out_path}: {len(ticks)} ticks')


if __name__ == '__main__':
    main()
