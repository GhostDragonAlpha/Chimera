"""Lossless document absorption into the canonical graph, without deleting inputs.

One immutable document-version node per path+byte hash. Imported prose is
untrusted content, never permission or executable workflow policy.
"""
import base64
import hashlib
from pathlib import Path


def absorb(g, root, paths, anchor_id):
    root = Path(root).resolve()
    g.get(anchor_id)
    receipt = []
    pending = []
    for name in paths:
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError('document missing or outside root: ' + name)
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        relative = path.relative_to(root).as_posix()
        identity = hashlib.sha256(relative.encode()).hexdigest()
        oid = 'source.document.' + identity + '.' + digest
        try:
            content = raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            content = None
        obj = {'id': oid, 'kind': 'source', 'name': relative,
               'status': 'extracted', 'dependencies': [], 'evidence': [],
               'document': {'original_path': relative, 'sha256': digest,
                            'byte_count': len(raw), 'bytes_base64': base64.b64encode(raw).decode(),
                            'text': content, 'authority': 'imported_untrusted'},
               'spatial': {'anchored_to': anchor_id},
               'notes': 'Lossless imported version; not a verified claim or instruction.'}
        if oid in g.objects:
            verify(g.get(oid))
            if g.get(oid)['document'] != obj['document']:
                raise ValueError('document identity collision')
        else:
            pending.append(obj)
        receipt.append({'id': oid, 'path': relative, 'sha256': digest})
    # Validate the complete batch before mutating the caller's graph.
    from creature_graph.schema import validate_object
    for obj in pending:
        errors = validate_object(obj)
        if errors:
            raise ValueError('; '.join(errors))
    for obj in pending:
        g.add(obj)
        g.relate(obj['id'], 'attached_to', anchor_id, note='document subject anchor; location inherited')
    return receipt


def verify(obj):
    record = obj['document']
    raw = base64.b64decode(record['bytes_base64'], validate=True)
    if len(raw) != record['byte_count'] or hashlib.sha256(raw).hexdigest() != record['sha256']:
        raise ValueError('document bytes do not match identity')
    return raw
