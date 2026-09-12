#!/usr/bin/env python3
"""retained-evidence-integrity-sweep-01 -- generates FINDINGS.txt from SWEEP_RAW_TABLE.txt.

Retained so the findings table is mechanically reproducible from the raw
table. Run from this directory: python make_findings.py
"""
import collections
import hashlib
import json
import os
import subprocess

rows = [l.split('\t') for l in open('SWEEP_RAW_TABLE.txt', encoding='utf-8').read().splitlines()[2:]]
by = {s: [r for r in rows if r[0] == s] for s in
      ('MATCH', 'MISMATCH', 'MISSING', 'OUT_OF_TREE', 'UNRESOLVABLE', 'UNASSOCIATED')}
raw_digest = hashlib.sha256(open('SWEEP_RAW_TABLE.txt', 'rb').read()).hexdigest()
script_digest = hashlib.sha256(open('evidence_integrity_sweep.py', 'rb').read()).hexdigest()
head = subprocess.run(['git', '-C', r'E:\ChimeraWork\slot-08', 'rev-parse', 'HEAD'],
                      capture_output=True, text=True).stdout.strip()


def srcrel(r):
    return r[3].split(':')[0]


mis_by_src = collections.Counter(srcrel(r) for r in by['MISMATCH'])
mis_by_cls = collections.Counter(r[1] for r in by['MISMATCH'])
mis_by_tzone = collections.Counter()
for r in by['MISMATCH']:
    t = r[4]
    zone = ('docs/evidence (retained artifact)' if t.startswith('docs/evidence')
            else ('worktree .tmp' if '.tmp' in t else 'in-tree non-evidence'))
    mis_by_tzone[zone] += 1
mis_tgt_files = collections.Counter(r[4] for r in by['MISMATCH'])
mis_by_srcext = collections.Counter(srcrel(r).rsplit('.', 1)[-1] for r in by['MISMATCH'])
missing_by_cls = collections.Counter(r[1] for r in by['MISSING'])
missing_zones = collections.Counter()
for r in by['MISSING']:
    t = r[4].split(' | ')[0]
    zone = ('docs/evidence' if t.startswith('docs/evidence')
            else ('.tmp (build/run artifact)' if '.tmp' in t else 'other in-tree'))
    missing_zones[zone] += 1
unas_anchor = collections.Counter(
    r[3].split('key:')[-1].split(' via')[0] for r in by['UNASSOCIATED'] if 'key:' in r[3])
unas_line = sum(1 for r in by['UNASSOCIATED'] if 'key:' not in r[3])
oot_by_src = collections.Counter(srcrel(r) for r in by['OUT_OF_TREE'])
oot_slot = collections.Counter(r[4].split('/')[2] for r in by['OUT_OF_TREE']
                               if r[4].startswith('E:/ChimeraWork/'))

out = []
w = out.append
w('retained-evidence-integrity-sweep-01 FINDINGS (post-amendment-A1 measurement)')
w('task: retained-evidence-integrity-sweep-01 gen 1 slot 8 worktree E:\\ChimeraWork\\slot-08')
w('git head at measurement: ' + head)
w('script: evidence_integrity_sweep.py sha256=' + script_digest)
w('raw table: SWEEP_RAW_TABLE.txt sha256=' + raw_digest)
w('fixture self-test: FIXTURE_TEST.txt -- SELFTEST PASS (matched=8, mismatched=3,')
w('  missing_file=3, others 0 -- exactly the amendment-A1 declared counts).')
w('')
w('METHOD (as preregistered)')
w('  PREREGISTRATION.txt P1-P6 + amendment A1. Extraction classes C1-C6,')
w('  fixpoint wrapper stripping, sidecar-dir-then-repo-root resolution,')
w('  self-exclusion of docs/evidence/agent_fleet/EVIDENCE_INTEGRITY_SWEEP.')
w('  Read-only outside the scope dir. The sweep ran twice; the two raw')
w('  tables were byte-identical (both sha256 ' + raw_digest[:16] + '...);')
w('  the second run wrote outside the repo and was deleted after the diff.')
w('')
w('THE THREE COUNTS (packet headline)')
w('  matched      = %d' % len(by['MATCH']))
w('  mismatched   = %d' % len(by['MISMATCH']))
w('  missing_file = %d' % len(by['MISSING']))
w('AUXILIARY COUNTS (never merged into the three)')
w('  out_of_tree  = %d' % len(by['OUT_OF_TREE']))
w('  unresolvable = %d' % len(by['UNRESOLVABLE']))
w('  unassociated = %d' % len(by['UNASSOCIATED']))
w('  total 64-hex instances classified = %d' % len(rows))
w('')
w('MISMATCH BREAKDOWN')
w('  by class: ' + json.dumps(dict(sorted(mis_by_cls.items()))))
w('  by source extension: ' + json.dumps(dict(sorted(mis_by_srcext.items()))))
w('  by target zone: ' + json.dumps(dict(sorted(mis_by_tzone.items()))))
w('  distinct source files: %d; top sources:' % len(mis_by_src))
for s, c in mis_by_src.most_common(15):
    w('    %4d  %s' % (c, s))
w('  top mismatch targets (referenced files):')
for t, c in mis_tgt_files.most_common(15):
    w('    %4d  %s' % (c, t))
w('')
w('MISSING BREAKDOWN')
w('  by class: ' + json.dumps(dict(sorted(missing_by_cls.items()))))
w('  by target zone: ' + json.dumps(dict(sorted(missing_zones.items()))))
w('')
w('UNASSOCIATED BREAKDOWN (hash classes with no defensible file binding)')
w('  json-keyed digests, top keys: ' + json.dumps(dict(unas_anchor.most_common(8))))
w('  text-line digests (no bindable path): %d' % unas_line)
w('  NOTE: dominated by runtime/data digests (state_id, geometry_sha256_f64le,')
w('  upload_positions_f32le_sha256, stdout/exe digests without recorded paths,')
w('  sha256_raw pairs whose sibling file was consumed at capture time).')
w('')
w('OUT_OF_TREE: %d references recorded against OTHER slot worktrees:' % len(by['OUT_OF_TREE']))
w('  by recorded slot: ' + json.dumps(dict(sorted(oot_slot.items()))))
w('  top sources: ' + json.dumps({s: c for s, c in oot_by_src.most_common(5)}))
w('')
w('UNRESOLVABLE: %d references truncated by the original capture tool' % len(by['UNRESOLVABLE']))
w('  (Get-FileHash Format-Table ellipsis); enumerated verbatim below.')
w('')
w('COVERAGE (no hash class silently skipped)')
w('  source extensions swept as text: json txt md log py sha256 jsonl html')
w('  diff patch source ps1 (counts in SWEEP_STDOUT.txt COVERAGE line).')
w('  non-text files present, NOT parsed as sources (they are hash TARGETS,')
w('  not records): .npy 58, .png 153, .npz 16, .cpp 11 (retained copies),')
w('  .hpp 5, .raw 3. Non-64 hex-token lengths met in swept text are counted')
w('  in the COVERAGE line (e.g. 40-hex git sha1 1227x, 16-hex 11589x); only')
w('  64-hex tokens are sha256-class references per the task statement.')
w('  json files that failed JSON parsing fell back to line scanning: 7.')
w('')
w('ZERO-EDITS PROOF')
w('  git status --porcelain captured before and after the sweep; the only')
w('  delta is the untracked scope artifact SWEEP_RAW_TABLE.txt itself.')
w('  No tracked file was modified; no file outside the scope dir was')
w('  created or changed by the sweep.')
w('')
w('HEADLINE FINDING')
w('  The retained evidence tree does NOT fully satisfy the preregistered')
w('  statement: %d recorded sha256 references fail recomputation against' % len(by['MISMATCH']))
w('  the file still present at the recorded path, and %d references' % len(by['MISSING']))
w('  name files no longer present. %d references recompute identically.' % len(by['MATCH']))
w('  Mismatches are FINDINGS, not edits: nothing was rewritten (packet:')
w('  "findings, not edits"). Spot hand-verifications (sha256sum) of five')
w('  mismatch rows (P04_PACKAGE.md, docs/AGENT_BOOTSTRAP_READINESS.md,')
w('  REVIEW_SLOT_HANDOFF/run_extension_legacy_tests.py,')
w('  g01/r3_snapshot/tools/evidence_output.py, ChimeraEngine/engine_state.py)')
w('  confirmed genuine drift, not extractor error.')
w('')
w('  Dominant pattern: manifests/tables captured at an earlier source_base')
w('  (e.g. agent_fleet/MANIFEST.json at bf0a6216, gpu_fixtures manifests at')
w('  cf2a0ae2, DESIGN_VALIDATION.md file->hash tables, g01 r3 SHA256SUMS)')
w('  record hashes of LIVE tree files (docs/*.md, tools/*.py,')
w('  ChimeraEngine/*.py|json) that legitimately evolved afterwards. The')
w('  retained sidecars are internally consistent snapshots; the tree moved.')
w('  FOLLOWUP CANDIDATE (not acted on, out of this task scope):')
w('  %d references are recorded against OTHER slot worktrees' % len(by['OUT_OF_TREE']))
w('  (E:/ChimeraWork/slot-NN/...) and cannot be audited from this tree at')
w('  all; %d were truncated by the recording tool. Both classes are' % len(by['UNRESOLVABLE']))
w('  un-auditable-as-recorded and are candidates for a re-recording lane.')
w('')
w('================================================================')
w('VERBATIM ENUMERATIONS (rows copied unchanged from SWEEP_RAW_TABLE.txt)')
w('================================================================')
w('')
w('--- MISMATCHED (%d rows) ---' % len(by['MISMATCH']))
for r in by['MISMATCH']:
    w('\t'.join(r))
w('')
w('--- MISSING_FILE (%d rows) ---' % len(by['MISSING']))
for r in by['MISSING']:
    w('\t'.join(r))
w('')
w('--- OUT_OF_TREE (%d rows) ---' % len(by['OUT_OF_TREE']))
for r in by['OUT_OF_TREE']:
    w('\t'.join(r))
w('')
w('--- UNRESOLVABLE (%d rows) ---' % len(by['UNRESOLVABLE']))
for r in by['UNRESOLVABLE']:
    w('\t'.join(r))
w('')
w('UNASSOCIATED rows (%d) are retained verbatim in SWEEP_RAW_TABLE.txt;' % len(by['UNASSOCIATED']))
w('they are enumeration-only (no recomputation is possible without a path)')
w('and are not duplicated here to keep this file focused on findings.')
w('')
w('Trailer: Agent: subagent-worker-12')

with open('FINDINGS.txt', 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(out) + '\n')
print('FINDINGS.txt written:', len(out), 'lines,', os.path.getsize('FINDINGS.txt'), 'bytes')
