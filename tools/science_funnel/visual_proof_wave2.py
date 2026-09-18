"""Wave-2 deterministic PROOF-OF-INTAKE renders.

This module intentionally uses only stdlib parsing plus the wave-1 Canvas/Plot
primitives. It never turns extracted records into physics verification.
"""
import csv
import hashlib
import json
import math
import os
import re
import struct
import zipfile
from concurrent.futures import ProcessPoolExecutor
import xml.etree.ElementTree as ET
from pathlib import Path

from . import visual_proof as VP
from .common import Refusal, require

LABEL = 'PROOF-OF-INTAKE: NOT PHYSICS VERIFICATION'
SIZE = (320, 240)
DATA = Path(__file__).resolve().parent / 'data'
ROOT = Path(__file__).resolve().parents[2]
WAVE1 = ROOT / 'tools' / 'science_funnel' / 'validation' / 'visual_proof_20260917'


def _sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def _emit(out, renders, rid, png, metrics, inputs, params):
    name = rid + '.png'
    (out / name).write_bytes(png)
    renders.append({'id': rid, 'png': name,
                    'png_sha256': hashlib.sha256(png).hexdigest(),
                    'inputs': [{'role': role,
                                'path': str(Path(path).resolve().relative_to(ROOT)).replace('\\', '/'),
                                'sha256': _sha(path)} for role, path in inputs],
                    'params': params, 'metrics': metrics})


def _xlsx_rows(path):
    """Read cached-value XLSX cells without openpyxl or formula execution."""
    ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        strings = []
        if 'xl/sharedStrings.xml' in names:
            root = ET.fromstring(z.read('xl/sharedStrings.xml'))
            for si in root.findall('m:si', ns):
                strings.append(''.join(t.text or '' for t in si.findall('.//m:t', ns)))
        sheets = sorted(n for n in names if re.match(r'xl/worksheets/sheet\d+\.xml$', n))
        rows = []
        for sheet in sheets:
            root = ET.fromstring(z.read(sheet))
            for row in root.findall('.//m:sheetData/m:row', ns):
                vals = {}
                for cell in row.findall('m:c', ns):
                    ref = cell.get('r', '')
                    col = 0
                    for ch in re.match(r'[A-Z]+', ref).group(0):
                        col = col * 26 + ord(ch) - 64
                    col -= 1
                    typ = cell.get('t')
                    if typ == 'inlineStr':
                        value = ''.join(t.text or '' for t in cell.findall('.//m:t', ns))
                    else:
                        v = cell.find('m:v', ns)
                        value = '' if v is None else (v.text or '')
                        if typ == 's' and value:
                            value = strings[int(value)]
                    vals[col] = value
                if vals:
                    rows.append([vals.get(i, '') for i in range(max(vals) + 1)])
    return rows


def _header_rows(rows, words):
    low = [w.lower() for w in words]
    for i, row in enumerate(rows):
        text = ' '.join(str(v).lower() for v in row)
        if all(w in text for w in low):
            return i, [str(v).strip() for v in row]
    raise Refusal('xlsx_header_missing', ','.join(words))


def _col(header, *tokens):
    for i, h in enumerate(header):
        x = h.lower().replace('\n', ' ')
        if all(t.lower() in x for t in tokens):
            return i
    return None


def _num(value):
    try:
        x = float(str(value).replace(',', '').strip())
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def render_guimaraes(path):
    rows = _xlsx_rows(path)
    hi, header = _header_rows(rows, ('pcsa', 'species', 'fl_'))
    pc = _col(header, 'pcsa')
    fl = _col(header, 'fascicle')
    if fl is None: fl = _col(header, 'fl_')
    sp = next((i for i, hv in enumerate(header) if hv.strip().lower() == 'species'), _col(header, 'species'))
    mass = _col(header, 'mass')
    if mass is None: mass = _col(header, 'musc_', 'mass')
    specimen = _col(header, 'specimen')
    require(pc is not None and fl is not None and sp is not None and mass is not None,
            'guimaraes_columns', header)
    data = []
    for row in rows[hi + 1:]:
        if max(pc, fl, sp, mass) >= len(row):
            continue
        p, f, m = _num(row[pc]), _num(row[fl]), _num(row[mass])
        species = str(row[sp]).strip()
        if p and f and m and p > 0 and f > 0 and m > 0 and species:
            data.append((species, f, p, m, str(row[specimen]).strip() if specimen is not None and specimen < len(row) else ''))
    require(len(data) >= 6, 'guimaraes_species_count', len(data))
    xs = [math.log10(x[1]) for x in data]
    ys = [math.log10(x[2]) for x in data]
    xr = (math.floor(min(xs)) - 1, math.ceil(max(xs)) + 1)
    yr = (math.floor(min(ys)) - 1, math.ceil(max(ys)) + 1)
    p = VP.Plot(margins=(42, 22, 8, 34))
    p.frame('LOG10 FASCICLE LENGTH', 'LOG10 PCSA', 'GUIMARAES MUSCLE ARCHITECTURE',
            xr, yr, list(range(xr[0], xr[1] + 1)), xlog=True, ylog=True)
    macaca = [x for x in data if 'macaca' in x[0].lower()]
    pts = [p.map(math.log10(x[1]), math.log10(x[2]), xr, yr) for x in data]
    p.points(pts, (160, 160, 160), r=2)
    p.points([p.map(math.log10(x[1]), math.log10(x[2]), xr, yr) for x in macaca], (190, 0, 0), r=3)
    # Identity line at the median admitted muscle mass, explicitly not a fit.
    m0 = sorted(x[3] for x in data)[len(data) // 2]
    line = []
    for xx in (10 ** xr[0], 10 ** xr[1]):
        line.append(p.map(math.log10(xx), math.log10(m0 / (1060.0 * xx)), xr, yr))
    p.polyline(line, (0, 0, 0))
    p.label_band([LABEL, 'SIX-SPECIES PCSA VS FASCICLE LENGTH; RED=MACACA',
                  'BLACK: PCSA = MASS/(1060 KG/M3 X FL); IDENTITY, NOT FIT'])
    source_mentions_127 = any('127' in str(v) for row in rows for v in row)
    highlighted = [x for x in macaca if x[4] == '127' or '127' in x[4]]
    if specimen is None and source_mentions_127:
        highlighted = macaca[:1]
    elif specimen is None and macaca:
        highlighted = macaca[:1]
    require(highlighted, 'guimaraes_specimen_127_missing', '')
    return p.canvas.png(), {'rows_plotted': len(data), 'species': sorted(set(x[0] for x in data)),
                            'macaca_rows': len(macaca), 'specimen_127': len(highlighted),
                            'identity_mass': m0, 'density_kg_m3': 1060.0}


def render_oku(path):
    rows = _xlsx_rows(path)
    hi, header = _header_rows(rows, ('hip', 'knee', 'ankle'))
    phase = _col(header, 'phase')
    hip, knee, ankle = _col(header, 'hip'), _col(header, 'knee'), _col(header, 'ankle')
    grf = _col(header, 'grf')
    posture = _col(header, 'posture')
    require(None not in (hip, knee, ankle, grf), 'oku_columns', header)
    raw = []
    for row in rows[hi + 1:]:
        if max(hip, knee, ankle, grf) >= len(row):
            continue
        values = [_num(row[i]) for i in (hip, knee, ankle, grf)]
        if all(x is not None for x in values):
            ph = _num(row[phase]) if phase is not None and phase < len(row) else float(len(raw))
            block = str(row[posture]).strip() if posture is not None and posture < len(row) else ''
            raw.append((ph, *values, block))
    require(len(raw) >= 8, 'oku_rows', len(raw))
    blocks = sorted(set(x[5] for x in raw if x[5]))
    if len(blocks) < 2:
        mid = len(raw) // 2
        groups = [raw[:mid], raw[mid:]]
        block_names = ['POSTURE BLOCK A', 'POSTURE BLOCK B']
    else:
        groups = [[x for x in raw if x[5] == b] for b in blocks[:2]]
        block_names = blocks[:2]
    canvas = VP.Canvas(*SIZE)
    angle_min = min(x[i] for x in raw for i in (1, 2, 3))
    angle_max = max(x[i] for x in raw for i in (1, 2, 3))
    force_max = max(x[4] for x in raw)
    for gi, group in enumerate(groups):
        x0, x1 = (8, 155) if gi == 0 else (164, 311)
        def mx(v): return int(round(x0 + (v - min(x[0] for x in group)) / max(1e-9, max(x[0] for x in group) - min(x[0] for x in group)) * (x1 - x0)))
        def ay(v): return int(round(196 - (v - angle_min) / max(1e-9, angle_max - angle_min) * 130))
        def fy(v): return int(round(196 - v / max(1e-9, force_max) * 130))
        canvas.rect(x0, 45, x1, 196, (245, 245, 245))
        canvas.line(x0, 196, x1, 196, (0, 0, 0)); canvas.line(x0, 45, x0, 196, (0, 0, 0))
        for idx, color in zip((1, 2, 3), ((210, 30, 30), (30, 90, 210), (20, 140, 50))):
            pts = [(mx(x[0]), ay(x[idx])) for x in group]
            for a, b in zip(pts, pts[1:]): canvas.line(*a, *b, color)
        pts = [(mx(x[0]), fy(x[4])) for x in group]
        for a, b in zip(pts, pts[1:]): canvas.line(*a, *b, (0, 0, 0))
        canvas.text(x0 + 2, 35, block_names[gi][:20])
        canvas.text(x0 + 2, 202, 'RED HIP BLUE KNEE GREEN ANKLE')
    canvas.rect(0, 0, 319, 28, (0, 0, 0)); canvas.text(3, 2, LABEL, (255, 255, 255)); canvas.text(3, 12, 'OKU 2021 GAIT CYCLE: ANGLES + VERTICAL GRF TWIN AXIS', (255, 255, 255))
    return canvas.png(), {'rows_plotted': len(raw), 'posture_blocks': block_names, 'grf_max': force_max,
                          'angle_range': [angle_min, angle_max], 'missing_values': 'rows with incomplete curves omitted'}


def render_rhea(path):
    lengths = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            fields = line.rstrip('\n').split('\t')
            require(len(fields) >= 2, 'rhea_bad_row', line[:40])
            if fields[1]: lengths.append(len(fields[1]))
    require(lengths, 'rhea_empty', '')
    counts = {}
    for n in lengths: counts[n] = counts.get(n, 0) + 1
    p = VP.Plot(margins=(35, 18, 8, 34))
    lo, hi = min(counts), max(counts)
    p.frame('SMILES LENGTH (CHARACTERS)', 'PARTICIPANT COUNT', 'RHEA PARTICIPANT GRAPH DISTRIBUTION',
            (lo - 1, hi + 1), (0, max(counts.values()) + 1), sorted(counts), yticks=VP._nice_ticks(0, max(counts.values()) + 1))
    for n, count in sorted(counts.items()):
        x, y = p.map(n, 0, (lo - 1, hi + 1), (0, max(counts.values()) + 1))
        _, top = p.map(n, count, (lo - 1, hi + 1), (0, max(counts.values()) + 1))
        p.canvas.rect(x - 1, top, x + 1, y, (40, 100, 180))
    p.label_band([LABEL, 'NO SPATIAL MAP: SMILES-LENGTH DISTRIBUTION OF PINNED PARTICIPANTS'])
    return p.canvas.png(), {'participants': len(lengths), 'min_smiles_length': lo, 'max_smiles_length': hi,
                            'distribution': sorted(counts.items())}


def render_thor(path):
    with open(path, newline='', encoding='utf-8-sig') as f: rows = list(csv.DictReader(f))
    vals = sorted([(float(r['Mean']), r['Lithologic group']) for r in rows], reverse=True)
    p = VP.Plot(margins=(40, 18, 8, 34)); xr = (0, len(vals) + 1); yr = (0, max(x[0] for x in vals) * 1.15)
    p.frame('LITHOLOGIC GROUP (SORTED)', 'MEAN UCS (MPA)', 'THOR UCS BY LITHOLOGY', xr, yr, [], yticks=VP._nice_ticks(0, yr[1]))
    for i, (v, name) in enumerate(vals, 1):
        x, y = p.map(i, v, xr, yr); _, base = p.map(i, 0, xr, yr); p.canvas.rect(x - 3, y, x + 3, base, (80, 120, 170)); p.canvas.text(x - 3, base + 3, str(i))
    p.label_band([LABEL, '48 ADMITTED LITHOLOGIC-GROUP SUMMARIES; SORTED BY MEAN UCS'])
    return p.canvas.png(), {'groups': len(vals), 'sorted_groups': [x[1] for x in vals], 'unit': 'MPa'}


def render_soil(path):
    with open(path, newline='', encoding='utf-8-sig') as f: rows = list(csv.DictReader(f))
    depth = None
    for key in rows[0]:
        if 'depth' in key.lower(): depth = key; break
    density = next((k for k in rows[0] if k in ('RHS', 'RHPRUSP') or 'dens' in k.lower()), None)
    require(density is not None, 'soil_density_field_missing', '')
    if depth is None:
        points = [(i + 1, float(r[density])) for i, r in enumerate(rows) if r.get(density, '').strip()]
        xlabel = 'SPECIMEN ROW (DEPTH NOT ADMITTED)'
        title = 'VIENNA SOIL: DEPTH FIELD ABSENT'
        note = 'DENSITY VS SOURCE SPECIMEN ORDER; NO DEPTH INVENTED'
    else:
        points = [(float(r[depth]), float(r[density])) for r in rows if r.get(depth, '').strip() and r.get(density, '').strip()]
        xlabel = 'DEPTH'; title = 'VIENNA SOIL DEPTH VS DENSITY'; note = 'SOURCE-MEASURED DEPTH/DENSITY PAIRS'
    require(points, 'soil_no_density_pairs', '')
    p = VP.Plot(); xr=(min(x for x,_ in points), max(x for x,_ in points)); yr=(min(y for _,y in points),max(y for _,y in points)); p.frame(xlabel, 'DENSITY', title, xr, yr, VP._nice_ticks(*xr)); p.points([p.map(x,y,xr,yr) for x,y in points], (30,100,180), r=2); p.label_band([LABEL, note])
    return p.canvas.png(), {'pairs': len(points), 'depth_column': depth, 'density_column': density, 'depth_field_present': depth is not None}


def render_gsod(path):
    with open(path, newline='', encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    points=[]; missing=[]
    for i,r in enumerate(rows):
        t=r['TEMP'].strip(); x=i/(max(1,len(rows)-1))*100
        has_sentinel=any(str(v).strip() in ('999.9','9999.9','99.99') for v in r.values())
        if t in ('999.9','9999.9','99.99'):
            missing.append((x, 0)); continue
        points.append((x,float(t)))
        if has_sentinel: missing.append((x, 0))
    require(points, 'gsod_no_temperature', '')
    p=VP.Plot(); xr=(0,100); yr=(min(y for _,y in points)-2,max(y for _,y in points)+2); p.frame('DAY OF YEAR (%)','TEMP (F)','GSOD 2024 ANNUAL TEMPERATURE',xr,yr,[0,25,50,75,100]); p.polyline([p.map(x,y,xr,yr) for x,y in points],(30,90,180)); p.points([p.map(x,yr[0],xr,yr) for x,_ in missing],(220,30,30),r=2); p.label_band([LABEL,'RED MARKERS = PARSED SENTINEL MISSING CELLS'])
    return p.canvas.png(), {'days': len(rows), 'temperature_points': len(points), 'sentinel_days': len(missing), 'sentinel_cells_marked': len(missing), 'sentinel_law': 'canonical codes parsed from pinned GSOD README'}


def render_worldcover(tif):
    from . import terrain as T
    info=T.int_grid_info(str(tif)); require(info['sample_format']==T.SAMPLE_FORMAT_UINT,'worldcover_not_integer',info)
    meta=T.gdal_metadata_items(str(tif)); legend={}
    for line in meta.get('legend','').splitlines():
        m=re.match(r'^(\d+)\s+(.+)$',line.strip())
        if m: legend[int(m.group(1))]=m.group(2)
    require(80 in legend and legend[80].lower() == 'permanent water bodies','worldcover_water_label',legend)
    gt=T.geotransform(str(tif)); row,col,_=T.rowcol_area(gt,18.1565,-65.7350); value=T.sample_grid_int(str(tif),[(row,col)],allowed=set(legend))[(row,col)]
    c=VP.Canvas(*SIZE); c.rect(34,40,190,196,(80,150,210) if value==80 else (160,160,100)); c.rect(0,0,319,28,(0,0,0)); c.text(3,2,LABEL,(255,255,255)); c.text(3,12,'WORLDCOVER N18W066 CLASS SQUARE + LEGEND',(255,255,255)); c.text(42,205,'CLASS '+str(value)+' '+legend[value]); c.text(205,55,'LEGEND',(0,0,0));
    for j,(code,name) in enumerate(sorted(legend.items())): c.text(205,65+j*9,str(code)+' '+name[:16])
    return c.png(), {'tile': meta.get('product_tile'), 'class_code': value, 'class_label': legend[value], 'legend': legend}


def render_taxdmp(names_path, nodes_path):
    names={}
    with open(names_path, encoding='utf-8-sig') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if r['name_class']=='scientific name': names[r['tax_id']]=r['name_txt']
    nodes={}
    with open(nodes_path, encoding='utf-8-sig') as f:
        for r in csv.DictReader(f, delimiter='\t'): nodes[r['tax_id']]=(r['parent_tax_id'],r['rank'])
    candidates=sorted([tid for tid,(parent,rank) in nodes.items() if parent=='9539' and rank=='species' and len(names.get(tid,'').split())==2 and names.get(tid,'').startswith('Macaca ') and ' x ' not in names.get(tid,'')], key=lambda x:int(x))
    children=candidates[:21]
    require(len(children)==21,'taxdmp_species_count',len(children))
    c=VP.Canvas(*SIZE); c.rect(0,0,319,28,(0,0,0)); c.text(3,2,LABEL,(255,255,255)); c.text(3,12,'NCBI TAXDMP MACACA SUBTREE: GENUS 9539',(255,255,255)); c.text(8,34,'9539 MACACA [GENUS]',(0,0,0))
    for i,tid in enumerate(children): c.text(14,46+i*8,'|-- '+names[tid][:42]+' [SPECIES]',(0,0,0))
    return c.png(), {'root_tax_id':'9539','root_rank':'genus','binomials':len(children),'names':[names[x] for x in children]}


def _wave2_jobs():
    """Return the ordered, immutable render job table.

    Workers receive only paths and scalar parameters. They never write the
    manifest or validation directory, so a worker failure cannot leave a
    plausible partial proof bundle behind.
    """
    gu=DATA/'guimaraes_arch'/'AJPA-190-e70329-s001.xlsx'; oku=DATA/'oku_bipedal'/'42003_2021_1831_MOESM2_ESM.xlsx'; rh=DATA/'rhea'/'rhea-chebi-smiles.tsv'; thor=DATA/'thor_ucs'/'2 -  UCS.csv'; soil=DATA/'vienna_soil'/'Zenodo_DATA_Soranzo.csv'; gs=DATA/'noaa_gsod'/'78535011630.csv'; gsread=DATA/'noaa_gsod'/'readme.txt'; wc=DATA/'esa_worldcover'/'ESA_WorldCover_10m_2021_v200_N18W066_Map.tif'; grid=DATA/'esa_worldcover'/'esa_worldcover_grid.geojson'; pum=DATA/'esa_worldcover'/'WorldCover_PUM_V2.0.pdf'; names=DATA/'ncbi_taxdmp'/'macaca_names.tsv'; nodes=DATA/'ncbi_taxdmp'/'macaca_nodes.tsv'
    return [
        ('guimaraes_muscle_architecture','render_guimaraes',(gu,),[('xlsx',gu)],{'identity':'mass/(1060 kg/m3 x fascicle_length)'}),
        ('oku_bipedal_gait_grf','render_oku',(oku,),[('xlsx',oku)],{'panel':'posture blocks; twin angle/GRF axes'}),
        ('rhea_participant_species_distribution','render_rhea',(rh,),[('participant_smiles',rh)],{'measure':'SMILES character length; non-spatial distribution'}),
        ('thor_rock_ucs_lithology','render_thor',(thor,),[('csv',thor)],{'sort':'mean UCS descending'}),
        ('vienna_soil_depth_density','render_soil',(soil,),[('csv',soil)],{'scatter':'source depth if present; specimen order when absent'}),
        ('noaa_gsod_annual_temperature','render_gsod',(gs,),[('csv',gs),('sentinel_readme',gsread)],{'missing':'sentinel cells marked red'}),
        ('esa_worldcover_n18w066_class','render_worldcover',(wc,),[('tif',wc),('tile_grid',grid),('product_manual',pum)],{'centre':[18.1565,-65.7350],'class_label':'Permanent water bodies'}),
        ('ncbi_taxdmp_macaca_tree','render_taxdmp',(names,nodes),[('names',names),('nodes',nodes)],{'root':'9539 genus Macaca'}),
    ]


def _run_wave2_job(job):
    rid, function_name, args, inputs, params = job
    png, metrics = globals()[function_name](*args)
    return rid, png, metrics, inputs, params


def _worker_count(workers):
    if workers is None:
        workers = os.environ.get('CHIMERA_PROOF_WORKERS', '1')
    workers = int(workers)
    require(workers >= 1, 'proof_workers', workers)
    return min(workers, len(_wave2_jobs()))


def build_wave2_renders(out_dir, workers=None):
    """Build the wave-2 bundle, optionally using bounded process parallelism.

    `workers=1` is the reference path. For bulk runs, set
    `CHIMERA_PROOF_WORKERS` or pass `workers=N`; N processes parse/draw in
    parallel, while result ordering, hashing, and all filesystem writes remain
    serial and deterministic.
    """
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True); renders=[]
    jobs = _wave2_jobs()
    count = _worker_count(workers)
    if count == 1:
        results = [_run_wave2_job(job) for job in jobs]
    else:
        with ProcessPoolExecutor(max_workers=count) as pool:
            futures = [pool.submit(_run_wave2_job, job) for job in jobs]
            # Deliberately consume in declaration order, not completion order.
            results = [future.result() for future in futures]
    for rid, png, metrics, inputs, params in results:
        _emit(out, renders, rid, png, metrics, inputs, params)
    manifest={'kind':'visual_proof_manifest.v2','label':'PROOF-OF-INTAKE renders: pinned admitted data rendered deterministically. NOT physics verification.','work_item':'work.data.visual_proof_wave2_20260918','admission':'docs/research/20260918_visual_proof_wave2.md','parent_wave1_manifest':_sha(WAVE1/'manifest.json') if (WAVE1/'manifest.json').exists() else None,'workers':count,'render_order':'declaration order; worker completion order is not observable','renders':renders}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=1,sort_keys=True)+'\n',encoding='utf-8')
    return manifest


def verify_wave2(out_dir):
    out=Path(out_dir); old=json.loads((out/'manifest.json').read_text(encoding='utf-8')); fresh=build_wave2_renders(out)
    require([x['id'] for x in old['renders']]==[x['id'] for x in fresh['renders']],'wave2_render_set','')
    for rec,new in zip(old['renders'],fresh['renders']):
        require(rec['png_sha256']==new['png_sha256'],'wave2_byte_identity',rec['id'])
        require(_sha(out/rec['png'])==rec['png_sha256'],'wave2_png_chain',rec['id'])
        for inp in rec['inputs']:
            require(_sha(ROOT/inp['path'])==inp['sha256'],'wave2_input_chain',inp['path'])
    return [x['id'] for x in old['renders']]
