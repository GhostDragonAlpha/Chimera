#!/usr/bin/env python3
"""retained-evidence-integrity-sweep-01 -- deterministic AUDIT of recorded sha256 references.

Recomputes every sha256 recorded in docs/evidence/** sidecars and MEASUREMENT
files against the file it references, when that file is still present in the
tree. Read-only outside its own scope dir. Classifies every 64-hex token it
meets into exactly one status; no hash class is silently skipped.

Extraction classes (fixed, declared in PREREGISTRATION.txt P3):
  C1 sha256sum_line : "<hex64> [marker]<path>" -- path token immediately after
  C2 line_path_token: line with exactly one hex64 and exactly one other
                      path-like token (either order)
  C3 json_key_path  : JSON object key is path-like, value is 64-hex
  C4 json_sibling   : 64-hex value bound to a sibling path/file key
  C5 named_sidecar  : "X.sha256" whose whole content is one bare hex64 -> sibling X
  C6 labeled_nearby : labeled hex64 bound to file:/path: on a nearby line
Unbound tokens are UNASSOCIATED (enumerated, never dropped).

Usage:
  python evidence_integrity_sweep.py --selftest     # fixture run, asserts prereg P5 counts
  python evidence_integrity_sweep.py --sweep OUT    # full sweep, writes raw table to OUT
"""
import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))                                # .../EVIDENCE_INTEGRITY_SWEEP
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))  # repo root
EVIDENCE = os.path.join(ROOT, 'docs', 'evidence')
FIXTURE = os.path.join(HERE, 'fixture')

TEXT_EXTS = {'.json', '.txt', '.md', '.log', '.py', '.sha256', '.jsonl', '.html',
             '.diff', '.patch', '.source', '.ps1', '.csv', '.yml', '.yaml'}

HEX64_RE = re.compile(r'(?<![0-9a-fA-F])([0-9a-fA-F]{64})(?![0-9a-fA-F])')
PATHY_RE = re.compile(r'.+\.[A-Za-z][A-Za-z0-9_.\-]{0,15}$')

STATUS_ORDER = ('MATCH', 'MISMATCH', 'MISSING', 'OUT_OF_TREE', 'UNRESOLVABLE', 'UNASSOCIATED')
SIBLING_EXACT = ('path', 'file', 'filename', 'filepath', 'location', 'artifact')
SUFFIXES = ('_path', '_file', '_filename')
TRUNC = ('...', '\u2026')


def norm_path(p):
    # Fixpoint strip (amendment A1): markdown backticks wrap tokens like
    # `path`: and sha256sum binary mode prefixes markers like *path; a single
    # ordered strip pass leaves the inner wrapper when the outer one strips
    # first, so strip until stable.
    p = p.strip()
    prev = None
    while prev != p:
        prev = p
        p = p.strip('"\'`*').strip('<>()[]{}').rstrip('.,;:')
    return p.replace('\\', '/')


def is_pathlike(tok):
    t = norm_path(tok)
    if len(t) < 4 or HEX64_RE.fullmatch(t):
        return False
    if re.match(r'(?i)^[a-z]+://', t):
        return False
    return ('/' in t) or bool(PATHY_RE.match(t)) or bool(re.match(r'^[A-Za-z]:', t))


def is_truncated(t):
    return t.endswith(TRUNC)


def classify_absolute(p):
    ap = os.path.normcase(os.path.normpath(p))
    rp = os.path.normcase(os.path.normpath(ROOT))
    if ap == rp or ap.startswith(rp + os.sep):
        return 'in', os.path.relpath(os.path.normpath(p), ROOT).replace('\\', '/')
    return 'out', None


def sha256_file(path, normalized):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b.replace(b'\r\n', b'\n') if normalized else b)
    return h.hexdigest()


def resolve_and_check(recorded_path, sidecar_dir, recorded_hash, normalized):
    """Deterministic resolution. Returns (status, target_desc, computed|None)."""
    p = norm_path(recorded_path)
    if is_truncated(p):
        return 'UNRESOLVABLE', p + ' (truncated by capture tool)', None
    if re.match(r'^[A-Za-z]:', p) or p.startswith('//'):
        where, rel = classify_absolute(p)
        if where == 'out':
            return 'OUT_OF_TREE', p + ' (outside repo root)', None
        candidates = [('abs', rel)]
    else:
        candidates = [('rel_sidecar', os.path.relpath(os.path.join(sidecar_dir, p), ROOT).replace('\\', '/')),
                      ('rel_root', p)]
    tried = []
    for _kind, c in candidates:
        tried.append(c)
        fp = os.path.join(ROOT, c)
        if os.path.isfile(fp):
            got = sha256_file(fp, normalized)
            if got == recorded_hash.lower():
                return 'MATCH', c, got
            return 'MISMATCH', c, got
    if len(tried) == 2:
        return 'MISSING', tried[0] + ' | also tried ' + tried[1], None
    return 'MISSING', tried[0], None


def json_key_pathlike(k):
    if HEX64_RE.fullmatch(k):
        return False
    t = k.replace('\\', '/')
    return ('/' in t) or bool(PATHY_RE.match(t)) or bool(re.match(r'^[A-Za-z]:', t))


def bind_json(key, obj):
    """C3/C4 sibling binding. Returns (class, raw_path_value, via_key) or (None, None, None)."""
    if json_key_pathlike(key):
        return 'C3', key, ''
    low = key.lower()
    prefix = low[:-len('_sha256')] if low.endswith('_sha256') else ''
    cands = list(SIBLING_EXACT) if (low == 'sha256' or low.endswith('_sha256')) else []
    cands.extend(prefix + s for s in SUFFIXES)
    for c in dict.fromkeys(cands):
        v = obj.get(c)
        if isinstance(v, str) and v.strip():
            return 'C4', v, c
    for k2 in sorted(obj.keys()):
        if isinstance(obj[k2], str) and k2.lower().endswith(SUFFIXES):
            return 'C4', obj[k2], k2
    return None, None, None


def walk_json(node, out):
    """Append (status|None, class, hash, path_value|None, label) per 64-hex value."""
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, str) and HEX64_RE.fullmatch(v):
                cls, pv, via = bind_json(k, node)
                label = 'key:' + k + (' via:' + via if via else '')
                out.append((None if cls else 'UNASSOCIATED', cls or 'C4', v, pv, label))
            else:
                walk_json(v, out)
    elif isinstance(node, list):
        for item in node:
            walk_json(item, out)


def scan_line(line, lines, idx, out):
    """C1 per hex occurrence; C2/C6 only when the line carries exactly one hex."""
    hexes = list(HEX64_RE.finditer(line))
    if not hexes:
        return
    toks = line.split()
    tokset = {}
    for pos, t in enumerate(toks):
        tokset.setdefault(pos, t)
    bound = []
    for hi, hm in enumerate(hexes):
        # C1: token immediately after this hex is a path
        htok_idx = [i for i, t in enumerate(toks) if hm.group(1) in t][0]
        if htok_idx + 1 < len(toks):
            nxt = toks[htok_idx + 1].strip('.,;:')
            if is_pathlike(nxt):
                out.append((None, 'C1', hm.group(1), nxt, 'line:%d#%d' % (idx + 1, hi + 1)))
                bound.append(hi)
                continue
    if len(hexes) == 1 and not bound:
        hm = hexes[0]
        others = sorted({t for t in toks if is_pathlike(t) and not HEX64_RE.fullmatch(norm_path(t))})
        if len(others) == 1:  # C2
            out.append((None, 'C2', hm.group(1), others[0], 'line:%d' % (idx + 1)))
            return
        low = line.lower()
        if 'sha' in low or 'digest' in low or 'hash' in low:  # C6
            for j in list(range(idx - 1, max(-1, idx - 4), -1)) + list(range(idx + 1, min(len(lines), idx + 3))):
                if j < 0 or j >= len(lines):
                    continue
                m = re.match(r'(?i)^(?:file|path|filename)\s*[:=]\s*(\S.*)$', lines[j].strip())
                if m:
                    tok = m.group(1).strip().strip('.,;:')
                    if is_pathlike(tok):
                        out.append((None, 'C6', hm.group(1), tok, 'line:%d' % (idx + 1)))
                        return
        out.append(('UNASSOCIATED', 'C2', hm.group(1), None, 'line:%d' % (idx + 1)))
        return
    for hi, hm in enumerate(hexes):
        if hi not in bound:
            out.append(('UNASSOCIATED', 'C1', hm.group(1), None, 'line:%d#%d' % (idx + 1, hi + 1)))


def scan_source(rel, fullpath):
    """Returns list of raw rows for one source file."""
    out = []
    ext = os.path.splitext(rel)[1].lower()
    with open(fullpath, 'rb') as f:
        data = f.read()
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        text = data.decode('utf-8', errors='replace')
    lines = text.splitlines()
    if ext == '.sha256':  # C5: bare-hash sidecar
        m = HEX64_RE.fullmatch(text.strip())
        if m:
            stem = os.path.basename(rel)[:-len('.sha256')]
            out.append((None, 'C5', m.group(1), stem, 'whole-file'))
            return out
    if ext == '.json':
        try:
            doc = json.loads(text)
        except Exception:
            doc = None
        if doc is not None:
            walk_json(doc, out)
            return out
    for i in range(len(lines)):
        if HEX64_RE.search(lines[i]):
            scan_line(lines[i], lines, i, out)
    return out


def gather_sources(source_root, exclude_dirs):
    files = []
    for dirpath, dirnames, filenames in os.walk(source_root):
        dirnames[:] = sorted(d for d in dirnames
                             if os.path.normpath(os.path.join(dirpath, d)) not in exclude_dirs)
        for fn in sorted(filenames):
            fp = os.path.join(dirpath, fn)
            files.append((os.path.relpath(fp, ROOT).replace('\\', '/'), fp))
    return files


def run(source_root, exclude_dirs, header):
    rows = []
    cov = {}
    hexlen_hist = {}
    for rel, fp in gather_sources(source_root, exclude_dirs):
        ext = os.path.splitext(rel)[1].lower()
        cov['source_ext:' + ext] = cov.get('source_ext:' + ext, 0) + 1
        if ext not in TEXT_EXTS:
            cov['nontext_skipped_as_source:' + ext] = cov.get('nontext_skipped_as_source:' + ext, 0) + 1
            continue
        if ext == '.json':
            try:
                json.loads(open(fp, 'rb').read().decode('utf-8'))
            except Exception:
                cov['json_parse_fail_fallback_to_lines'] = cov.get('json_parse_fail_fallback_to_lines', 0) + 1
        for st, cls, h, pv, anchor in scan_source(rel, fp):
            if st is None:
                nz = 'crlf_normalized_to_lf' in pv.lower() or 'crlf_normalized_to_lf' in anchor.lower()
                st, tgt, got = resolve_and_check(pv, os.path.dirname(fp), h, nz)
                rows.append((st, cls, h, rel + ':' + anchor, tgt, ('computed=' + got) if got else ''))
            else:
                rows.append((st, cls, h, rel + ':' + anchor, '-', ''))
        # hex-length histogram over the raw text (non-64 token visibility)
        txt = open(fp, 'rb').read().decode('utf-8', errors='replace')
        for tok in re.findall(r'(?<![0-9a-fA-F])[0-9a-fA-F]{6,}(?![0-9a-fA-F])', txt):
            if len(tok) != 64:
                key = 'hexlen_%d' % len(tok)
                hexlen_hist[key] = hexlen_hist.get(key, 0) + 1
    counts = {s: 0 for s in STATUS_ORDER}
    for r in rows:
        counts[r[0]] += 1
    cov.update(hexlen_hist)
    return header, counts, rows, cov


def raw_table(header, rows):
    out = [header, 'status\tclass\trecorded\tsrc\ttarget\tnote']
    for st, cls, h, src, tgt, note in rows:
        out.append('\t'.join((st, cls, h, src, tgt, note)))
    return '\n'.join(out) + '\n'


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--selftest', action='store_true')
    g.add_argument('--sweep', metavar='OUT_TXT')
    a = ap.parse_args()

    if a.selftest:
        header, counts, rows, cov = run(FIXTURE, set(), 'FIXTURE RUN (self-test) source_root=fixture/')
        print(raw_table(header, rows), end='')
        print('COUNTS ' + json.dumps(counts, sort_keys=True))
        # amendment A1 (2026-09-11): +1 MATCH (backtick+comma token),
        # +1 MISMATCH (backtick token); see PREREGISTRATION.txt amendment.
        expect = {'MATCH': 8, 'MISMATCH': 3, 'MISSING': 3, 'OUT_OF_TREE': 0,
                  'UNRESOLVABLE': 0, 'UNASSOCIATED': 0}
        print('EXPECTED ' + json.dumps(expect, sort_keys=True))
        ok = counts == expect
        print('SELFTEST ' + ('PASS' if ok else 'FAIL'))
        sys.exit(0 if ok else 1)

    header, counts, rows, cov = run(
        EVIDENCE, {os.path.normpath(HERE)},
        'SWEEP source_root=docs/evidence excluded=' +
        os.path.relpath(HERE, ROOT).replace('\\', '/') +
        ' (self-exclusion per PREREGISTRATION.txt P1)')
    with open(a.sweep, 'w', encoding='utf-8', newline='\n') as f:
        f.write(raw_table(header, rows))
    print(header)
    print('COUNTS ' + json.dumps(counts, sort_keys=True))
    print('COVERAGE ' + json.dumps(sorted(cov.items())))
    print('RAW_TABLE ' + a.sweep)


if __name__ == '__main__':
    main()
