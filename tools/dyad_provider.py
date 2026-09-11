"""DYAD provider interface: the review contract separated from the vision provider.

A dedicated visual reviewer can run through a lead-delegated subagent callback,
a remote service, or the existing local senses/LM Studio eye, without changing
the protocol. Fail-closed by named refusals; evidence (exact prompt, raw
response, served identity, capture identities) is retained on every response.
Numeric mentions in visual prose are tagged, never manufactured into facts.

This module performs no inference itself and never removes the local adapter.
Actual visual acceptance still requires a live provider run with retained
evidence (acceptance is NOT_CLAIMED here).
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

REVIEW_TYPES = ('still', 'ordered_frames', 'movie')
CAPTURE_HASH_ALGO = 'sha256'
_NUMERIC_MENTION = re.compile(r'[-+]?\d+(?:\.\d+)?(?:\s*%|\s*px|\s*x)?', re.IGNORECASE)


class DyadRefusal(ValueError):
    """Named fail-closed refusal; the reason string is machine-readable."""


@dataclass(frozen=True)
class Capture:
    index: int
    path: str
    sha256: str
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class DyadReviewRequest:
    task: str
    attempt: str
    physical_context: str
    claim_under_exam: str
    questions: tuple
    captures: tuple
    runtime_metadata: dict
    review_type: str
    evidence_limits: str

    def validate(self):
        if self.review_type not in REVIEW_TYPES:
            raise DyadRefusal('invalid_review_type')
        if not self.questions:
            raise DyadRefusal('questions_required')
        for q in self.questions:
            if not isinstance(q, str) or not q.strip():
                raise DyadRefusal('invalid_question')
        if not self.captures:
            raise DyadRefusal('captures_required')
        seen = set()
        for c in self.captures:
            if not isinstance(c, Capture):
                raise DyadRefusal('invalid_capture')
            if c.index < 1 or c.path in seen:
                raise DyadRefusal('invalid_capture_order_or_duplicate')
            seen.add(c.path)
            if not re.fullmatch('[0-9a-f]{64}', c.sha256 or ''):
                raise DyadRefusal('invalid_capture_hash')
        ordered = sorted(self.captures, key=lambda c: c.index)
        n = len(ordered)
        if self.review_type == 'still' and n != 1:
            raise DyadRefusal('still_requires_exactly_one_capture')
        if self.review_type in ('ordered_frames', 'movie') and n < 2:
            raise DyadRefusal('temporal_review_requires_multiple_captures')
        if self.review_type == 'movie' and not self.runtime_metadata.get('movie_artifact'):
            raise DyadRefusal('movie_requires_artifact_reference')
        for required in ('task', 'attempt', 'physical_context', 'claim_under_exam', 'evidence_limits'):
            if not getattr(self, required).strip():
                raise DyadRefusal('missing_' + required)
        return ordered

    def build_prompt(self) -> str:
        """Deterministic, retained verbatim. Non-leading questions only; the
        request carries no expected-defect strings (protocol r7 lesson)."""
        ordered = self.validate()
        lines = [
            'DYAD visual review request',
            'task: %s' % self.task,
            'attempt: %s' % self.attempt,
            'physical/programming context: %s' % self.physical_context,
            'claim under examination: %s' % self.claim_under_exam,
            'review type: %s' % self.review_type,
            'ordered captures: %s' % ', '.join(
                '#%d %s (sha256 %s...)' % (c.index, Path(c.path).name, c.sha256[:12])
                for c in ordered),
            'camera/runtime metadata: %s' % json.dumps(self.runtime_metadata, sort_keys=True),
            'evidence limits: %s' % self.evidence_limits,
            '',
            'Answer EVERY question with its number. Report only what you can observe in the '
            'supplied images; state uncertainty explicitly. Do not guess. Numbers you mention '
            'are observations to verify, not measurements.',
        ]
        for i, q in enumerate(self.questions, 1):
            lines.append('%d. %s' % (i, q))
        return '\n'.join(lines)


@dataclass
class DyadVerdict:
    status: str = 'NOT_CLAIMED'          # PASS | FAIL | INCONCLUSIVE | NOT_CLAIMED
    supports_claim: Optional[bool] = None
    numeric_mentions: list = field(default_factory=list)


@dataclass
class DyadResponse:
    task: str
    attempt: str
    review_type: str
    provider_id: str
    served_model: Optional[str]
    served_identity_note: str
    capture_identities: list
    exact_prompt: str
    raw_response: str
    finish_status: str
    observations: list
    uncertainty: str
    verdict: DyadVerdict

    def to_json(self) -> str:
        d = dict(self.__dict__)
        d['verdict'] = self.verdict.__dict__
        return json.dumps(d, indent=1, sort_keys=True)


def parse_numeric_mentions(text: str) -> list:
    """Numeric mentions in visual prose are retained but tagged; they are
    NEVER converted into asserted facts."""
    return [{'text': m.group(0), 'tag': 'unverified_numeric_mention'}
            for m in _NUMERIC_MENTION.finditer(text or '')]


def build_verdict(conclusion: str, observations, raw_response: str) -> DyadVerdict:
    c = (conclusion or '').strip().lower()
    supports = {'supports': True, 'contradicts': False, 'unclear': None}.get(c)
    status = 'NOT_CLAIMED'
    if supports is True:
        status = 'INCONCLUSIVE'  # model agreement is never acceptance/proof
    elif supports is False:
        status = 'FAIL'
    return DyadVerdict(status=status, supports_claim=supports,
                       numeric_mentions=parse_numeric_mentions(' '.join(observations) + ' ' + raw_response))


class DyadProvider:
    """Base class. Capability declaration is explicit and never inferred."""
    id = 'abstract'
    vision = False
    temporal = 'none'   # 'none' | 'frames' | 'movie'

    def check_request(self, request: DyadReviewRequest):
        if not self.vision:
            raise DyadRefusal('no_vision')
        need = {'still': 'none', 'ordered_frames': 'frames', 'movie': 'movie'}[request.review_type]
        ladder = {'none': 0, 'frames': 1, 'movie': 2}
        if ladder[self.temporal] < ladder[need]:
            raise DyadRefusal('provider_cannot_verify_temporal_claim')

    def verify_captures(self, ordered):
        for c in ordered:
            p = Path(c.path)
            if not p.is_file():
                raise DyadRefusal('capture_missing:%s' % c.path)
            h = hashlib.sha256(p.read_bytes()).hexdigest()
            if h != c.sha256:
                raise DyadRefusal('capture_hash_mismatch:%s' % c.path)

    def review(self, request: DyadReviewRequest) -> DyadResponse:
        request.validate()
        self.check_request(request)
        ordered = request.validate()
        self.verify_captures(ordered)
        return self._review(request, ordered)

    def _review(self, request, ordered):  # pragma: no cover - abstract
        raise NotImplementedError


class SubagentDyadProvider(DyadProvider):
    """Lead-delegated reviewer subagent: a callback receiving the exact prompt
    and capture paths, returning (raw_response, served_model_or_None,
    finish_status, observations, uncertainty, conclusion)."""
    def __init__(self, callback: Callable, provider_id='subagent-dyad'):
        if not callable(callback):
            raise DyadRefusal('subagent_callback_required')
        self.callback = callback
        self.id = provider_id
        self.vision = True
        self.temporal = 'frames'  # a subagent may inspect ordered captures; movie needs declared support

    def _review(self, request, ordered):
        raw, served, finish, observations, uncertainty, conclusion = self.callback(
            request.build_prompt(), [c.path for c in ordered])
        return DyadResponse(
            task=request.task, attempt=request.attempt, review_type=request.review_type,
            provider_id=self.id, served_model=served,
            served_identity_note=('reported: %s' % served) if served else
            'served identity unavailable from provider; recorded as named uncertainty, no substitution',
            capture_identities=[{'index': c.index, 'path': c.path, 'sha256': c.sha256} for c in ordered],
            exact_prompt=request.build_prompt(), raw_response=raw,
            finish_status=finish or 'unknown', observations=list(observations or []),
            uncertainty=uncertainty or '', verdict=build_verdict(conclusion, observations or [], raw))


class RemoteDyadProvider(DyadProvider):
    """Remote vision service. Endpoint and auth come from configuration; the
    auth token is read from an environment variable NAME (never stored here)."""
    def __init__(self, endpoint: str, auth_env_var: str, temporal='none', provider_id='remote-dyad'):
        if not endpoint.startswith('https://'):
            raise DyadRefusal('remote_endpoint_must_be_https')
        if not auth_env_var:
            raise DyadRefusal('auth_env_var_required')
        self.endpoint, self.auth_env_var = endpoint, auth_env_var
        self.id, self.vision, self.temporal = provider_id, True, temporal

    def _review(self, request, ordered):  # pragma: no cover - network path
        raise NotImplementedError(
            'transport wiring is deployment configuration; the contract, refusals and '
            'evidence retention are defined and tested; HTTP execution is added by the '
            'deploying lane with its own evidence')


class LocalSensesDyadProvider(DyadProvider):
    """The existing local eye (ChimeraEngine senses / LM Studio), retained.
    Lazily imported so CPU contract tests need no engine or loaded model.
    One image per call remains the law: ordered frames are a call sequence."""
    def __init__(self, temporal='none', provider_id='local-senses'):
        if temporal not in ('none', 'frames'):
            raise DyadRefusal('local_eye_temporal_capability_is_stills_or_looped_frames')
        self.id, self.vision, self.temporal = provider_id, True, temporal

    def _review(self, request, ordered):  # pragma: no cover - engine path
        raise NotImplementedError(
            'live eye execution stays in ChimeraEngine/senses.py under THE_DYAD_PROTOCOL; '
            'this adapter binds it to the contract when the deploying lane wires it')


def select_provider(config: dict) -> DyadProvider:
    kind = (config or {}).get('kind')
    if kind == 'subagent':
        return SubagentDyadProvider(config['callback'], provider_id=config.get('id', 'subagent-dyad'))
    if kind == 'remote':
        return RemoteDyadProvider(config['endpoint'], config.get('auth_env_var', ''),
                                  temporal=config.get('temporal', 'none'),
                                  provider_id=config.get('id', 'remote-dyad'))
    if kind == 'local':
        return LocalSensesDyadProvider(temporal=config.get('temporal', 'none'),
                                       provider_id=config.get('id', 'local-senses'))
    raise DyadRefusal('unknown_provider_kind:%s' % kind)
