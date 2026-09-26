"""Bind the existing capture validator to actual evidence files at acceptance."""
import hashlib
import json
from pathlib import Path
from visual_capture import validate_manifest, require
from integrity import unique_object, reject_constant

def checked_file(item, limit, keep=False):
    path=Path(item['reference'])
    require(path.is_absolute() and path.is_file(), 'visual_evidence_file_missing')
    require(0 < path.stat().st_size <= limit, 'visual_evidence_size_limit')
    digest=hashlib.sha256();size=0;parts=[]
    with path.open('rb') as stream:
        while chunk:=stream.read(1024*1024):
            size+=len(chunk)
            require(size<=limit, 'visual_evidence_size_limit')
            digest.update(chunk)
            if keep:parts.append(chunk)
    require(digest.hexdigest()==item['raw_sha256'], 'visual_evidence_hash_mismatch')
    return b''.join(parts) if keep else digest.hexdigest()

def verify(receipt,contract):
    evidence=receipt['evidence']
    raw=checked_file(evidence['camera'],2*1024*1024,True)
    manifest=json.loads(raw,object_pairs_hook=unique_object,parse_constant=reject_constant)
    capture_hash=checked_file(evidence['visual'],4*1024**3)
    context=receipt.get('capture_context')
    require(isinstance(context,dict), 'capture_context_required')
    require(context.get('task_id')==contract['task_id'], 'capture_task_mismatch')
    require(context.get('capture_sha256')==capture_hash, 'capture_file_binding_mismatch')
    return validate_manifest(manifest,context,contract['task']['verification_profile'])
