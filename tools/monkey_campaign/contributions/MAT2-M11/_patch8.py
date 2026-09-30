"""One-shot: repoint consumers at capture_evidence.json (split from
cameras.json)."""
import pathlib

here = pathlib.Path(__file__).resolve().parent
NL = chr(10)

# --- make_capture.py: frame hashes + tick map from the evidence bundle
p = here / 'make_capture.py'
src = p.read_text(encoding='utf-8')
old = ("    evidence = json.loads((evidence_dir / 'cameras.json').read_text(" +
       NL +
       "        encoding='utf-8'))" + NL +
       "    cams = evidence['cameras']" + NL +
       "    frame_hashes = evidence['frame_raw_sha256']")
new = ("    evidence = json.loads((evidence_dir / 'capture_evidence.json')"
       ".read_text(" + NL +
       "        encoding='utf-8'))" + NL +
       "    cams = evidence['cameras']" + NL +
       "    frame_hashes = evidence['frame_raw_sha256']")
assert src.count(old) == 1
src = src.replace(old, new)
p.write_bytes(src.encode('utf-8'))
compile(src.encode('utf-8'), 'make_capture.py', 'exec')
print('make_capture.py repointed')

# --- make_report.py
p = here / 'make_report.py'
src = p.read_text(encoding='utf-8')
old = "    cams = load(str(pathlib.Path('capture') / 'evidence' / 'cameras.json'),"
new = ("    cams = load(str(pathlib.Path('capture') / 'evidence' /"
       " 'capture_evidence.json'),")
assert src.count(old) == 1
src = src.replace(old, new)
p.write_bytes(src.encode('utf-8'))
compile(src.encode('utf-8'), 'make_report.py', 'exec')
print('make_report.py repointed')

# --- test_limb_world.py: the capture-gate loads
p = here / 'test_limb_world.py'
src = p.read_text(encoding='utf-8')
n = src.count("load(str(CAPTURE / 'evidence' / 'cameras.json'))")
assert n == 2, n
src = src.replace("load(str(CAPTURE / 'evidence' / 'cameras.json'))",
                  "load(str(CAPTURE / 'evidence' / 'capture_evidence.json'))")
p.write_bytes(src.encode('utf-8'))
compile(src.encode('utf-8'), 'test_limb_world.py', 'exec')
print('test_limb_world.py repointed')

# --- anchor script (attempt workspace)
p = pathlib.Path('E:/ChimeraWork/monkey-coordination/kanban-attempts/'
                 'MAT2-M11/8de1349ae67840fc8b8a15fb647c5e4a/'
                 'anchor_evidence.py')
src = p.read_text(encoding='utf-8')
old = "    ('cameras.json', 'capture/evidence/cameras.json',"
new = ("    ('capture_evidence.json', 'capture/evidence/capture_evidence"
       ".json',")
assert src.count(old) == 1
src = src.replace(old, new + NL +
                  "    ('cameras.json', 'capture/evidence/cameras.json',")
p.write_bytes(src.encode('utf-8'))
print('anchor script updated')
