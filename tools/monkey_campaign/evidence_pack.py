"""Generate raw artifact identities from explicit files; never invent verdicts."""
import argparse
import hashlib
import json
from pathlib import Path


def collect(root, files):
    root = Path(root).resolve(); rows = []; seen = set()
    for name in files:
        p = (root/name).resolve()
        if not p.is_relative_to(root) or not p.is_file():
            raise ValueError('artifact_outside_root_or_missing')
        if p in seen: raise ValueError('duplicate_artifact')
        seen.add(p); before = p.stat(); h = hashlib.sha256(); size = 0
        with p.open('rb') as f:
            for chunk in iter(lambda: f.read(1024*1024), b''):
                h.update(chunk); size += len(chunk)
        after = p.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns) or size != after.st_size:
            raise ValueError('artifact_changed_during_hash')
        rows.append(dict(path=str(p), sha256=h.hexdigest(), bytes=size))
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True); p.add_argument('--file', action='append', required=True)
    p.add_argument('--task', required=True); p.add_argument('--source-commit', required=True)
    args = p.parse_args()
    print(json.dumps(dict(schema='chimera.artifact_pack.v1', task_id=args.task,
                          declared_source_commit=args.source_commit, artifacts=collect(args.root, args.file),
                          verdict='NOT_ASSESSED',
                          limits='Source commit is caller-declared. Hashes identify bytes, not correctness. '
                                 'Attach actual test logs and existing camera/runtime receipts explicitly.'), indent=2))


if __name__ == '__main__': main()
