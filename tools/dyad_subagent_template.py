"""DYAD subagent template driver: easy, contract-bound creation of a DYAD
reviewer subagent (operator direction 2026-09-11, HUMAN feedback d015187c).

Two steps, no inference in this file:

  plan     validate a request spec, hash-verify captures, and emit the EXACT
           prompt the spawned subagent will be given (evidence root copy).
  assemble parse the spawned subagent's structured report and run it through
           SubagentDyadProvider so the reviewed refusals, verdict building and
           numeric-mention tagging execute on the real path; retain the
           DyadResponse JSON and append the dyad log.

Served identity for this provider class is the HARNESS declaration passed via
--served (e.g. the operator-asserted vision model of the subagent fleet), or
None (recorded as a named uncertainty). The model's self-report is never used
as served identity. The spawn itself is the lead's Agent call using the
template in docs/THE_DYAD_SUBAGENT_TEMPLATE.md; nothing here bypasses the
controller, loads a model, or claims GPU resources.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dyad_provider import (Capture, DyadRefusal, DyadReviewRequest,
                           SubagentDyadProvider)

REPORT_BEGIN = '===DYAD_REPORT==='
REPORT_END = '===END==='


def _load_spec(path: str) -> dict:
    spec = json.loads(Path(path).read_text(encoding='utf-8'))
    for key in ('task', 'attempt', 'physical_context', 'claim_under_exam',
                'review_type', 'evidence_limits', 'questions', 'captures'):
        if key not in spec:
            raise SystemExit('spec_missing_field:%s' % key)
    return spec


def _build_request(spec: dict) -> DyadReviewRequest:
    captures = tuple(
        Capture(index=int(c['index']), path=str(c['path']),
                sha256=hashlib.sha256(Path(c['path']).read_bytes()).hexdigest(),
                metadata=c.get('metadata', {}))
        for c in spec['captures'])
    return DyadReviewRequest(
        task=spec['task'], attempt=spec['attempt'],
        physical_context=spec['physical_context'],
        claim_under_exam=spec['claim_under_exam'],
        questions=tuple(spec['questions']), captures=captures,
        runtime_metadata=spec.get('runtime_metadata', {}),
        review_type=spec['review_type'],
        evidence_limits=spec['evidence_limits'])


def _validated(spec: dict):
    request = _build_request(spec)
    ordered = request.validate()
    provider = SubagentDyadProvider(callback=lambda *a: None)  # validation only
    provider.check_request(request)
    provider.verify_captures(ordered)
    return request, ordered


def cmd_plan(args):
    spec = _load_spec(args.spec)
    request, ordered = _validated(spec)
    root = Path(args.evidence_root)
    root.mkdir(parents=True, exist_ok=True)
    prompt = request.build_prompt()
    (root / ('exact_prompt_%s.txt' % spec['attempt'])).write_text(
        prompt, encoding='utf-8')
    spec_out = dict(spec)
    spec_out['captures'] = [{'index': o.index, 'path': o.path, 'sha256': o.sha256}
                            for o in ordered]
    (root / ('request_spec_%s.json' % spec['attempt'])).write_text(
        json.dumps(spec_out, indent=1, sort_keys=True), encoding='utf-8')
    print(json.dumps({
        'planned': True, 'attempt': spec['attempt'], 'review_type': spec['review_type'],
        'captures': [{'index': o.index, 'path': o.path, 'sha256': o.sha256} for o in ordered],
        'prompt_file': str(root / ('exact_prompt_%s.txt' % spec['attempt'])),
        'prompt_sha256': hashlib.sha256(prompt.encode('utf-8')).hexdigest(),
    }, indent=1))


_SECTION = re.compile(r'^(RAW_RESPONSE|OBSERVATIONS|UNCERTAINTY|CONCLUSION|FINISH):[ \t]*(.*)$')


def _parse_report(text: str):
    """Parse the template's structured report block into the callback tuple."""
    if REPORT_BEGIN not in text or REPORT_END not in text:
        raise DyadRefusal('subagent_callback_malformed:report_block_missing')
    block = text.split(REPORT_BEGIN, 1)[1].split(REPORT_END, 1)[0]
    sections, current, buf, inline = {}, None, [], {}
    for line in block.splitlines():
        m = _SECTION.match(line.strip())
        if m:
            if current is not None and not inline.get(current):
                sections[current] = '\n'.join(buf).strip()
            current, buf = m.group(1), []
            rest = m.group(2).strip()
            if rest:
                inline[current] = rest
        else:
            buf.append(line)
    if current is not None and not inline.get(current):
        sections[current] = '\n'.join(buf).strip()
    sections.update(inline)
    missing = [k for k in ('RAW_RESPONSE', 'OBSERVATIONS', 'UNCERTAINTY',
                           'CONCLUSION', 'FINISH') if not sections.get(k)]
    if missing:
        raise DyadRefusal('subagent_callback_malformed:missing_sections:%s'
                          % ','.join(missing))
    observations = [re.sub(r'^[-*\d.)\s]+', '', l).strip()
                    for l in sections['OBSERVATIONS'].splitlines()
                    if l.strip()]
    conclusion = sections['CONCLUSION'].strip().lower()
    if conclusion not in ('supports', 'contradicts', 'unclear'):
        raise DyadRefusal('subagent_callback_malformed:invalid_conclusion:%s'
                          % conclusion)
    finish = sections['FINISH'].strip().lower()
    return (sections['RAW_RESPONSE'], finish, observations,
            sections['UNCERTAINTY'], conclusion)


def cmd_assemble(args):
    spec = _load_spec(args.spec)
    request, ordered = _validated(spec)
    report_text = Path(args.report).read_text(encoding='utf-8')

    def callback(prompt, capture_paths):
        raw, finish, observations, uncertainty, conclusion = _parse_report(report_text)
        served = args.served if args.served else None
        return (raw, served, finish, observations, uncertainty, conclusion)

    provider = SubagentDyadProvider(callback=callback,
                                     provider_id='subagent-dyad-glm53flash')
    response = provider.review(request)  # full contract path incl. refusals
    root = Path(args.evidence_root)
    out = root / ('dyad_response_%s.json' % spec['attempt'])
    out.write_text(response.to_json(), encoding='utf-8')
    log = root / 'dyad_log.jsonl'
    entry = {'ts_utc': _dt.datetime.now(_dt.timezone.utc).isoformat(),
             'task': spec['task'], 'attempt': spec['attempt'],
             'provider': response.provider_id,
             'served_model': response.served_model,
             'served_identity_note': response.served_identity_note,
             'review_type': response.review_type,
             'verdict': response.verdict.status,
             'evidence_file': out.name,
             'report_file': Path(args.report).name}
    with log.open('a', encoding='utf-8') as fh:
        fh.write(json.dumps(entry, sort_keys=True) + '\n')
    print(json.dumps({'assembled': True, 'verdict': response.verdict.status,
                      'supports_claim': response.verdict.supports_claim,
                      'numeric_mentions': len(response.verdict.numeric_mentions),
                      'evidence': str(out)}, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('plan', help='validate spec + hashes, emit exact prompt')
    p.add_argument('--spec', required=True)
    p.add_argument('--evidence-root', required=True)
    p.set_defaults(fn=cmd_plan)
    a = sub.add_parser('assemble', help='parse report, run provider, retain evidence')
    a.add_argument('--spec', required=True)
    a.add_argument('--report', required=True,
                   help='file containing the subagent final message verbatim')
    a.add_argument('--evidence-root', required=True)
    a.add_argument('--served', default=None,
                   help='harness-declared served identity (never the model self-report)')
    a.set_defaults(fn=cmd_assemble)
    args = ap.parse_args()
    try:
        args.fn(args)
    except DyadRefusal as exc:
        print(json.dumps({'refused': str(exc)}))
        sys.exit(2)


if __name__ == '__main__':
    main()
