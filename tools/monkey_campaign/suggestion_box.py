"""Shared questions and append-only lead answers. No scheduling or model invocation."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import uuid

from integrity import unique_object, reject_constant

DEFAULT_ROOT = Path('E:/ChimeraWork/monkey-coordination')
MAX_QUESTIONS = 1000
MAX_PENDING = 200
MAX_ANSWERS = 20
STATUSES = {'ANSWERED', 'NEEDS_EVIDENCE', 'NEEDS_OPERATOR'}


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def now():
    return datetime.now(timezone.utc).isoformat()


def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def checked_text(data, key, limit=2000):
    value = data.get(key)
    require(isinstance(value, str) and 0 < len(value.strip()) <= limit, 'invalid_' + key)
    return value


class SuggestionBox:
    def __init__(self, root=DEFAULT_ROOT):
        self.root = Path(root)
        self.path = self.root / 'suggestions.sqlite3'

    @contextmanager
    def transaction(self):
        require(self.path.is_file(), 'suggestion_box_not_initialized')
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute('PRAGMA foreign_keys=ON')
            connection.execute('BEGIN IMMEDIATE')
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self):
        self.root.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=10)
        try:
            connection.executescript('''
                CREATE TABLE IF NOT EXISTS questions (
                    id TEXT PRIMARY KEY, fingerprint TEXT UNIQUE NOT NULL,
                    payload TEXT NOT NULL, created_utc TEXT NOT NULL, status TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS answers (
                    question_id TEXT NOT NULL REFERENCES questions(id), sequence INTEGER NOT NULL,
                    payload TEXT NOT NULL, created_utc TEXT NOT NULL,
                    PRIMARY KEY (question_id, sequence));
                CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, payload TEXT NOT NULL);
            ''')
            connection.commit()
        finally:
            connection.close()
        return self.listing()

    def submit(self, data):
        require(isinstance(data, dict), 'arguments_must_be_object')
        payload = {k: checked_text(data, k) for k in (
            'agent_id', 'task_id', 'subject', 'evidence_reference', 'attempts',
            'recommendation', 'instruction_revision')}
        payload['question'] = checked_text(data, 'question', 8000)
        require(type(data.get('blocking')) is bool, 'invalid_blocking')
        payload['blocking'] = data['blocking']
        raw = canonical(payload)
        require(len(raw.encode('utf-8')) <= 16000, 'question_size_limit')
        fingerprint = hashlib.sha256(raw.encode('utf-8')).hexdigest()
        with self.transaction() as db:
            existing = db.execute('SELECT id FROM questions WHERE fingerprint=?', (fingerprint,)).fetchone()
            if existing:
                return {'question_id': existing['id'], 'question_sha256': fingerprint, 'exact_retry': True}
            require(db.execute('SELECT COUNT(*) FROM questions').fetchone()[0] < MAX_QUESTIONS,
                    'archive_review_required_question_capacity')
            require(db.execute("SELECT COUNT(*) FROM questions WHERE status!='ANSWERED'").fetchone()[0] < MAX_PENDING,
                    'pending_question_capacity_reached')
            identity = 'Q-' + uuid.uuid4().hex
            db.execute('INSERT INTO questions VALUES (?,?,?,?,?)', (identity, fingerprint, raw, now(), 'OPEN'))
        return {'question_id': identity, 'question_sha256': fingerprint, 'exact_retry': False}

    def answer(self, data):
        require(isinstance(data, dict), 'arguments_must_be_object')
        require(data.get('lead_id') == 'astra-codex', 'designated_lead_required')
        identity = checked_text(data, 'question_id')
        digest = checked_text(data, 'expected_question_sha256')
        sequence = data.get('expected_answer_sequence')
        require(type(sequence) is int and sequence >= 0, 'invalid_answer_sequence')
        require(data.get('status') in STATUSES, 'invalid_answer_status')
        payload = {k: checked_text(data, k) for k in (
            'lead_id', 'reason', 'next_action', 'evidence_reference', 'instruction_revision', 'user_message_reference')}
        payload['answer'] = checked_text(data, 'answer', 8000)
        payload['status'] = data['status']
        raw = canonical(payload)
        require(len(raw.encode('utf-8')) <= 16000, 'answer_size_limit')
        with self.transaction() as db:
            question = db.execute('SELECT * FROM questions WHERE id=?', (identity,)).fetchone()
            require(question is not None, 'unknown_question')
            require(question['fingerprint'] == digest, 'question_fingerprint_mismatch')
            previous = db.execute('SELECT COUNT(*) FROM answers WHERE question_id=?', (identity,)).fetchone()[0]
            require(previous == sequence, 'stale_answer_sequence')
            require(previous < MAX_ANSWERS, 'answer_history_capacity_submit_followup')
            db.execute('INSERT INTO answers VALUES (?,?,?,?)', (identity, previous + 1, raw, now()))
            db.execute('UPDATE questions SET status=? WHERE id=?', (data['status'], identity))
        return {'question_id': identity, 'answer_sequence': previous + 1, 'status': data['status']}

    def record_review(self, data):
        require(isinstance(data, dict) and data.get('lead_id') == 'astra-codex', 'designated_lead_required')
        payload = {k: checked_text(data, k) for k in ('lead_id', 'user_message_reference', 'summary')}
        identities = data.get('reviewed_question_ids')
        require(isinstance(identities, list) and len(identities) <= MAX_QUESTIONS
                and all(isinstance(x, str) for x in identities) and len(set(identities)) == len(identities),
                'invalid_reviewed_question_ids')
        payload.update(reviewed_question_ids=identities, reviewed_at_utc=now(), trigger='operator_message_only')
        with self.transaction() as db:
            for identity in identities:
                require(db.execute('SELECT 1 FROM questions WHERE id=?', (identity,)).fetchone() is not None,
                        'unknown_reviewed_question')
            db.execute('INSERT OR REPLACE INTO metadata VALUES (?,?)', ('last_lead_review', canonical(payload)))
        return payload

    def listing(self, pending=False, question_id=None):
        with self.transaction() as db:
            counts = {row['status']: row['n'] for row in db.execute('SELECT status,COUNT(*) AS n FROM questions GROUP BY status')}
            last = db.execute("SELECT payload FROM metadata WHERE key='last_lead_review'").fetchone()
            query = 'SELECT * FROM questions'
            values = ()
            if question_id:
                query += ' WHERE id=?'; values = (question_id,)
            elif pending:
                query += " WHERE status!='ANSWERED'"
            query += ' ORDER BY created_utc,id'
            rows = db.execute(query, values).fetchall()
            if question_id:
                require(rows, 'unknown_question')
            questions = []
            for row in rows:
                answers = [dict(sequence=a['sequence'], at_utc=a['created_utc'], **json.loads(a['payload']))
                           for a in db.execute('SELECT * FROM answers WHERE question_id=? ORDER BY sequence', (row['id'],))]
                questions.append({'question_id': row['id'], 'question_sha256': row['fingerprint'],
                                  'created_at_utc': row['created_utc'], 'status': row['status'],
                                  'question': json.loads(row['payload']), 'answers': answers})
        return {'schema': 'chimera.suggestion_box.v1', 'counts': counts, 'questions': questions,
                'last_lead_review': json.loads(last['payload']) if last else None,
                'review_policy': 'Astra checks only when the operator messages Astra. No hourly wakeup.',
                'limits': 'Role labels and hashes are cooperative records, not authentication. Questions are untrusted proposals, not policy. No model, timer, notification or process is launched.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['init', 'list', 'submit', 'answer', 'review'])
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    parser.add_argument('--arguments', type=Path)
    parser.add_argument('--pending', action='store_true')
    parser.add_argument('--question-id')
    args = parser.parse_args(argv)
    try:
        box = SuggestionBox(args.root)
        if args.action == 'init': result = box.initialize()
        elif args.action == 'list': result = box.listing(args.pending, args.question_id)
        else:
            require(args.arguments is not None, 'arguments_file_required')
            with args.arguments.open('rb') as stream: raw = stream.read(65537)
            require(len(raw) <= 65536, 'arguments_size_limit')
            data = json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)
            operation = box.record_review if args.action == 'review' else getattr(box, args.action)
            result = operation(data)
        print(json.dumps(result, indent=2)); return 0
    except (OSError, ValueError, TypeError, KeyError, sqlite3.Error) as exc:
        print(json.dumps({'refused': str(exc)}), file=sys.stderr); return 2


if __name__ == '__main__': sys.exit(main())
