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

Hardening (dyad-template-hardening-01, advisory findings of the PR #64 review,
controller feedback dce2c813): F1 — question guidance is determinability-neutral
(QUESTION_FORM_GUIDANCE below; the template document carries the same law).
F2 — OPTIONAL blind frame ordering: a spec may carry "blind": {"seed": <int>} to
have frames listed in seeded-randomized order with sidecar state values stripped
from the prompt text; the unblinding map (original order + states) is retained
to the evidence root and sha-recorded. Without that key NOTHING changes: the
default path is byte-identical to the pre-hardening driver. Blinding happens at
this spec layer only — tools/dyad_provider.py (the reviewed contract) is not
weakened and builds every prompt, blind or not, through the unchanged
DyadReviewRequest.build_prompt().
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dyad_provider import (Capture, DyadRefusal, DyadReviewRequest,
                           SubagentDyadProvider)

REPORT_BEGIN = '===DYAD_REPORT==='
REPORT_END = '===END==='

# F1 (advisory finding 1, PR #64 review, feedback dce2c813): a question that
# presupposes non-determinability leads the reviewer ("What features prevent
# you from determining X?" assumes they cannot). The canonical, neutral form
# is pinned here and quoted as law in docs/THE_DYAD_SUBAGENT_TEMPLATE.md.
QUESTION_FORM_GUIDANCE = (
    'Can you determine X? If not, what limits you?')

# F2: runtime_metadata keys of this shape carry sidecar STATE values (which
# frame is "supposed" raised) and are redacted from prompt-visible metadata in
# blind mode; their values survive only in the retained unblinding record.
_STATE_KEY = re.compile(r'^frame_\d+_state$')


def _load_spec(path: str) -> dict:
    spec = json.loads(Path(path).read_text(encoding='utf-8'))
    for key in ('task', 'attempt', 'physical_context', 'claim_under_exam',
                'review_type', 'evidence_limits', 'questions', 'captures'):
        if key not in spec:
            raise SystemExit('spec_missing_field:%s' % key)
    return spec


def _build_request(spec: dict) -> DyadReviewRequest:
    captures = []
    for c in spec['captures']:
        computed = hashlib.sha256(Path(c['path']).read_bytes()).hexdigest()
        declared = str(c.get('sha256') or '').strip().lower() or None
        # A declared hash makes verify_captures a REAL check (tamper fails
        # closed); without one the computed hash is recorded, not "verified".
        captures.append(Capture(index=int(c['index']), path=str(c['path']),
                                sha256=declared or computed,
                                metadata=c.get('metadata', {})))
    return DyadReviewRequest(
        task=spec['task'], attempt=spec['attempt'],
        physical_context=spec['physical_context'],
        claim_under_exam=spec['claim_under_exam'],
        questions=tuple(spec['questions']), captures=tuple(captures),
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


def _apply_blind(spec: dict):
    """F2 OPTIONAL blind frame ordering. Returns (effective_spec, unblinding).

    No "blind" key -> (spec, None): the default path is returned UNTOUCHED so
    its prompt bytes stay identical to the pre-hardening driver (back-compat
    is a preregistered falsifier, not a courtesy).

    With "blind": {"seed": <int>} the captures are listed in SEEDED-randomized
    order (random.Random(seed).shuffle — reproducible: plan and assemble build
    byte-identical prompts from the same spec), renumbered to blind positions
    1..n, and every prompt-visible runtime_metadata key of the form
    frame_<i>_state (the sidecar state values) is redacted; the values survive
    only in the returned unblinding record, which the caller retains to the
    evidence root and sha-records. The reviewed provider contract is untouched:
    the blinded request is an ordinary DyadReviewRequest.
    """
    blind = spec.get('blind')
    if blind is None:
        return spec, None
    if not isinstance(blind, dict):
        raise DyadRefusal('invalid_blind_spec')
    try:
        seed = int(blind['seed'])
    except (KeyError, TypeError, ValueError):
        raise DyadRefusal('blind_requires_integer_seed')
    captures = spec.get('captures') or []
    if len(captures) < 2:
        raise DyadRefusal('blind_requires_multiple_captures')
    original = sorted((dict(c) for c in captures), key=lambda c: int(c['index']))
    order = list(range(len(original)))
    random.Random(seed).shuffle(order)  # seeded shuffle: same seed, same order
    blind_caps = []
    for pos, src in enumerate(order, 1):
        c = dict(original[src])
        c['index'] = pos  # blind position: the only numbering the prompt shows
        blind_caps.append(c)
    eff = dict(spec)
    eff['captures'] = blind_caps
    runtime = dict(spec.get('runtime_metadata', {}))
    redacted = sorted(k for k in runtime if _STATE_KEY.match(str(k)))
    states = {}
    for k in redacted:
        states[str(k)] = runtime[k]
        del runtime[k]
    for k, v in (blind.get('states') or {}).items():
        states[str(k)] = v
    eff['runtime_metadata'] = runtime
    unblinding = {
        'mode': 'blind',
        'seed': seed,
        'task': spec['task'],
        'attempt': spec['attempt'],
        'original_order': [{'index': int(c['index']), 'path': c['path'],
                            'sha256': (str(c['sha256']).strip().lower()
                                       if c.get('sha256') else None)}
                           for c in original],
        'blind_order': [{'blind_index': pos,
                         'original_index': int(original[src]['index'])}
                        for pos, src in enumerate(order, 1)],
        'states': states,
        'redacted_keys': redacted,
    }
    return eff, unblinding


def _require_no_state_leak(prompt: str, states: dict) -> None:
    """Fail-closed: a retained state value that still appears verbatim in the
    prompt text is a blinding FAILURE (named refusal), never a silent leak."""
    leaked = sorted(str(k) for k, v in states.items()
                    if isinstance(v, str) and v.strip() and v in prompt)
    if leaked:
        raise DyadRefusal('blind_state_leak:%s' % ','.join(leaked))


def _guarded_prompt(request: DyadReviewRequest, unblinding) -> str:
    prompt = request.build_prompt()
    if unblinding is not None:
        _require_no_state_leak(prompt, unblinding['states'])
    return prompt


def _unblinding_record(unblinding: dict, prompt: str):
    """Deterministic unblinding bytes (no timestamps): plan and assemble
    independently produce identical records, so assemble can VERIFY instead of
    trust. Returns (text, sha256-of-text); the sha is what plan records."""
    record = dict(unblinding)
    record['prompt_sha256'] = hashlib.sha256(prompt.encode('utf-8')).hexdigest()
    text = json.dumps(record, indent=1, sort_keys=True) + '\n'
    return text, hashlib.sha256(text.encode('utf-8')).hexdigest()


def cmd_plan(args):
    spec = _load_spec(args.spec)
    eff, unblinding = _apply_blind(spec)
    request, ordered = _validated(eff)
    root = Path(args.evidence_root)
    root.mkdir(parents=True, exist_ok=True)
    prompt = _guarded_prompt(request, unblinding)
    (root / ('exact_prompt_%s.txt' % spec['attempt'])).write_text(
        prompt, encoding='utf-8')
    spec_out = dict(eff)
    spec_out.pop('blind', None)  # the shareable spec copy stays blind too
    spec_out['captures'] = [{'index': o.index, 'path': o.path, 'sha256': o.sha256}
                            for o in ordered]
    (root / ('request_spec_%s.json' % spec['attempt'])).write_text(
        json.dumps(spec_out, indent=1, sort_keys=True), encoding='utf-8')
    out = {
        'planned': True, 'attempt': spec['attempt'], 'review_type': spec['review_type'],
        'captures': [{'index': o.index, 'path': o.path, 'sha256': o.sha256} for o in ordered],
        'prompt_file': str(root / ('exact_prompt_%s.txt' % spec['attempt'])),
        'prompt_sha256': hashlib.sha256(prompt.encode('utf-8')).hexdigest(),
    }
    if unblinding is not None:
        text, sha = _unblinding_record(unblinding, prompt)
        ub_path = root / ('unblinding_%s.json' % spec['attempt'])
        # exact bytes, not text-mode: the recorded sha must equal a plain
        # sha256 of the retained file on every platform (no newline transport)
        ub_path.write_bytes(text.encode('utf-8'))
        # blind-mode-only output keys; default stdout stays byte-identical
        out['blind'] = True
        out['unblinding_file'] = str(ub_path)
        out['unblinding_sha256'] = sha
    print(json.dumps(out, indent=1))


def _flush(sections, inline, current, buf):
    """Close a section: continuation lines after an inline header are
    APPENDED to that section's value (never silently dropped). Appended prose
    on single-value sections (CONCLUSION/FINISH) fails their strict
    validation — fail-closed, which is the correct outcome."""
    text = '\n'.join(buf).strip()
    if inline.get(current):
        if text:
            inline[current] = inline[current] + '\n' + text
    else:
        sections[current] = text


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
            if current is not None:
                _flush(sections, inline, current, buf)
            current, buf = m.group(1), []
            rest = m.group(2).strip()
            if rest:
                inline[current] = rest
        else:
            buf.append(line)
    if current is not None:
        _flush(sections, inline, current, buf)
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
    eff, unblinding = _apply_blind(spec)
    request, ordered = _validated(eff)
    report_text = Path(args.report).read_text(encoding='utf-8')
    _guarded_prompt(request, unblinding)  # fail-closed leak scan, same as plan

    def callback(prompt, capture_paths):
        raw, finish, observations, uncertainty, conclusion = _parse_report(report_text)
        served = args.served if args.served else None
        return (raw, served, finish, observations, uncertainty, conclusion)

    provider = SubagentDyadProvider(callback=callback,
                                     provider_id='subagent-dyad-glm53flash')
    response = provider.review(request)  # full contract path incl. refusals
    root = Path(args.evidence_root)
    if unblinding is not None:
        # Deterministic record: verify an existing map instead of trusting it
        # (a tampered or stale unblinding record is a named refusal). Compare
        # exact bytes — the record was written byte-exact by plan.
        text, sha = _unblinding_record(unblinding, response.exact_prompt)
        ub_path = root / ('unblinding_%s.json' % spec['attempt'])
        if ub_path.exists():
            if ub_path.read_bytes() != text.encode('utf-8'):
                raise DyadRefusal('unblinding_mismatch:%s' % ub_path.name)
        else:
            ub_path.write_bytes(text.encode('utf-8'))
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
