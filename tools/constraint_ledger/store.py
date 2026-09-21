"""The record store: an append-only DIRECTORY of per-lane JSONL inboxes plus
a canonical merged snapshot.

No worktrees, no locks on the shared directory: each lane appends to its OWN
inbox file (O_APPEND); the merge is a pure function of the inbox SET —
records sorted by (name, digest), duplicates by content deduplicated,
DISTINCT records sharing a label are a diagnostic, never a silent overwrite
(F-DROP). Order-independence: merge(append(A),append(B)) == merge(append(B),
append(A)) == merge(A then B sequentially) — byte-for-byte (F-ORDER).

Acceptance of a concurrent merge is INVARIANT-CONFLUENCE (Bailis), not
Knaster-Tarski: each family must independently satisfy the store's declared
invariants, and the merged extension must satisfy them too:
  I1 one-defining-writer per quantity-version across accepted definitions
  I2 record labels unique per distinct content (distinct content + same
     label = diagnostic, blocks the snapshot)
  I3 every record's content digest recomputes (immutability)
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .schema import Record, RecordError, content_digest, effects, expand, load


class StoreError(ValueError):
    pass


def append_records(inbox: Path, specs: list[dict]) -> list[str]:
    """Append records (canonical JSON lines) to a lane's inbox. Returns the
    appended content digests. Append-only: existing bytes are never touched."""
    inbox = Path(inbox)
    digests = []
    inbox.parent.mkdir(parents=True, exist_ok=True)
    with open(inbox, 'a', encoding='utf-8', newline='\n') as f:
        for spec in specs:
            rec = load(spec)
            line = json.dumps(rec.content(), sort_keys=True,
                              separators=(',', ':'), ensure_ascii=True)
            f.write(line + '\n')
            digests.append(rec.digest)
    return digests


def read_inbox(inbox: Path) -> list[Record]:
    inbox = Path(inbox)
    out = []
    if not inbox.exists():
        return out
    for line in inbox.read_text(encoding='utf-8').splitlines():
        if line.strip():
            out.append(load(json.loads(line)))
    return out


def store_invariants(records: list[Record], externals: dict[str, dict] | None = None
                     ) -> list[str]:
    """The declared store invariants; returns violation strings (empty = OK)."""
    problems: list[str] = []
    by_label: dict[str, Record] = {}
    writer: dict[str, str] = {}
    for rec in records:
        # I3 immutability: the digest recomputes from content
        if content_digest(rec) != rec.digest:
            problems.append(f'I3 digest mismatch on {rec.name!r}')
        # I2 label uniqueness per distinct content
        if rec.name in by_label:
            if by_label[rec.name].digest != rec.digest:
                problems.append(f'I2 label collision on {rec.name!r} '
                                f'({by_label[rec.name].digest[:8]} vs {rec.digest[:8]})')
        else:
            by_label[rec.name] = rec
        # I1 one defining writer per quantity-version (definitions only)
        if rec.kind == 'definition':
            for inst in expand(rec):
                wx, _, _ = effects(inst)
                for q in wx:
                    if q in writer and writer[q] != inst.name:
                        problems.append(f'I1 second writer for {q!r}: '
                                        f'{writer[q]!r} and {inst.name!r}')
                    writer[q] = inst.name
    return problems


def merge(store_dir: Path) -> tuple[bytes, list[str]]:
    """Merge ALL inbox files into the canonical snapshot bytes (sorted,
    deduplicated by content). Pure: a function of the inbox SET only."""
    records: dict[str, Record] = {}       # digest -> record
    labels: dict[str, str] = {}           # label -> digest
    diagnostics: list[str] = []
    for inbox in sorted(store_dir.glob('incoming/*.jsonl')):
        for rec in read_inbox(inbox):
            records.setdefault(rec.digest, rec)
    ordered = sorted(records.values(), key=lambda r: (r.name, r.digest))
    for rec in ordered:
        if rec.name in labels and labels[rec.name] != rec.digest:
            diagnostics.append(f'label collision: {rec.name!r} '
                               f'({labels[rec.name][:8]} vs {rec.digest[:8]})')
        labels[rec.name] = rec.digest
    body = ''.join(
        json.dumps(rec.content(), sort_keys=True, separators=(',', ':'),
                   ensure_ascii=True) + '\n'
        for rec in ordered)
    problems = store_invariants(list(records.values()))
    header = json.dumps({
        'protocol': 'chimera-record-pilot-v1',
        'records': len(ordered),
        'diagnostics': diagnostics,
        'invariant_violations': problems,
        'digest': hashlib.sha256(body.encode()).hexdigest(),
    }, sort_keys=True, separators=(',', ':')) + '\n'
    return header.encode() + body.encode(), problems + diagnostics


def write_snapshot(store_dir: Path) -> Path:
    data, problems = merge(store_dir)
    if problems:
        raise StoreError('snapshot refused: ' + '; '.join(problems))
    out = store_dir / 'snapshot.json'
    out.write_bytes(data)
    return out
