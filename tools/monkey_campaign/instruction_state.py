"""Read-only lead instruction revision check; no delivery or authorship authentication."""
import argparse
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
import stat
import sys

from integrity import unique_object, reject_constant

BEGIN = '<!-- CHIMERA_LEAD_CONTROL\n'
END = '\nCHIMERA_LEAD_CONTROL -->'
MAX_BYTES = 1024 * 1024
SCOPE = '5b07ce0c49c6a8cae42bc4f04ebce8d2835104d5591df4f1feecf7fa0dc56a00'


def require(value, reason):
    if not value:
        raise ValueError(reason)


def bounded_bytes(path):
    with Path(path).open('rb') as stream:
        data = stream.read(MAX_BYTES + 1)
    require(len(data) <= MAX_BYTES, 'instruction_file_size_limit')
    return data


def decode(raw):
    return json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)


def file_hash(raw):
    return hashlib.sha256(raw).hexdigest()


def inspect(root, acknowledgement=None):
    root = Path(root).absolute()
    entry = root/'docs'/'MONKEY_RUN.md'
    raw = bounded_bytes(entry)
    text = raw.decode('utf-8-sig').replace('\r\n','\n').replace('\r','\n')
    require(text.count(BEGIN) == 1 and text.count(END) == 1, 'lead_control_block_missing_or_duplicate')
    meta = decode(text.split(BEGIN,1)[1].split(END,1)[0])
    require(isinstance(meta,dict) and meta.get('schema') == 'chimera.lead_instructions.v1', 'unsupported_instruction_schema')
    require(meta.get('lead_id') == 'astra-codex', 'designated_lead_changed_requires_operator')
    rev = meta.get('revision')
    require(type(rev) is int and rev > 0, 'invalid_instruction_revision')
    require(meta.get('revision_id') == f'astra-{rev:04d}', 'invalid_instruction_revision_id')
    require(meta.get('scope_sha256') == SCOPE, 'scope_change_requires_separate_approval')
    names = meta.get('files')
    require(isinstance(names,list) and 1 <= len(names) <= 32 and all(isinstance(x,str) for x in names),
            'invalid_instruction_file_list')
    require(len(set(names)) == len(names) and 'docs/MONKEY_RUN.md' in names, 'duplicate_or_missing_entry')
    files = []
    for name in sorted(names):
        require(name and ':' not in name and '\\' not in name and not name.startswith('/')
                and not PureWindowsPath(name).is_absolute()
                and all(p not in ('','.','..') for p in name.split('/')), 'instruction_path_escape')
        target = root
        for part in name.split('/'):
            target = target/part
            info = target.lstat()
            require(not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0) & 0x400,
                    'instruction_link_refused')
        # Use the same entry bytes for both metadata and the fingerprint.
        data = raw if name == 'docs/MONKEY_RUN.md' else bounded_bytes(target)
        files.append({'path':name,'raw_sha256':file_hash(data)})
    payload = {'lead_id':meta['lead_id'],'revision':rev,'revision_id':meta['revision_id'],
               'scope_sha256':SCOPE,'files':files}
    bundle = file_hash(json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8'))
    state = 'READ_AND_ACK_REQUIRED'
    if acknowledgement is not None:
        a = acknowledgement
        require(isinstance(a,dict) and a.get('schema') == 'chimera.instruction_ack.v1','invalid_ack_schema')
        require(type(a.get('revision')) is int and a['revision'] > 0, 'invalid_ack_revision')
        require(a.get('scope_sha256') == SCOPE, 'ack_scope_mismatch')
        require(a.get('lead_id') == meta['lead_id'], 'ack_lead_mismatch')
        require(a.get('revision_id') == f"astra-{a['revision']:04d}", 'invalid_ack_revision_id')
        require(isinstance(a.get('bundle_sha256'),str) and re.fullmatch('[0-9a-f]{64}',a['bundle_sha256']),
                'invalid_ack_bundle')
        for key in ('coordinator_id','native_checkpoint','acknowledged_at_utc'):
            require(isinstance(a.get(key),str) and a[key].strip(), 'missing_ack_' + key)
        try:
            stamp = datetime.fromisoformat(a['acknowledged_at_utc'].replace('Z', '+00:00'))
        except ValueError as exc:
            raise ValueError('invalid_ack_timestamp') from exc
        require(stamp.tzinfo is not None and stamp.utcoffset() == timedelta(0), 'invalid_ack_timestamp')
        require(a['revision'] <= rev, 'INSTRUCTION_REVISION_ROLLBACK')
        if a['revision'] == rev:
            require(a['bundle_sha256'] == bundle, 'INSTRUCTION_CHANGED_WITHOUT_REVISION')
            state = 'ACK_RECORD_MATCHES'
        else:
            state = 'UPDATED_READ_AND_ACK_REQUIRED'
    return {**payload,'bundle_sha256':bundle,'entry_raw_sha256':file_hash(raw),
            'algorithm':'sha256-chimera-instruction-bundle-v1','state':state,
            'next_action':('Continue the current goal and check again at the next coordination event' if state == 'ACK_RECORD_MATCHES'
                           else 'Read these current files, apply the revision at a safe checkpoint, and record your own acknowledgement in the native checkpoint'),
            'limits':'Matches supplied acknowledgement fields only; does not authenticate who wrote them, deliver a notification, or prove GLM is polling.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--ack',type=Path)
    args = parser.parse_args(argv)
    try:
        ack = decode(bounded_bytes(args.ack)) if args.ack else None
        result = inspect(args.root,ack)
        print(json.dumps(result,indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError) as exc:
        print(json.dumps({'refused':str(exc)}),file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
