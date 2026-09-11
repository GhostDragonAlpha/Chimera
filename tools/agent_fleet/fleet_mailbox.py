"""Fleet mailbox: cross-agent communication without the lead as relay.

Filesystem contract (fleet space; this repo copy is the durable, tested promotion of
the live v0 at E:/ChimeraWork/tools/fleet_mailbox.py — behavior-identical, contract in
docs/THE_FLEET_MAILBOX.md):
  <root>\\inbox\\<agent>\\<UTC>-<sender>-<unique>.json
One JSON file per message; posting writes to a temp name then os.replace()
(atomic on the same volume). Reading lists the inbox; --take marks a message
served by moving it to served\\ (append-only history, never deleted).

Agent names are the controller session names (e.g. subagent-worker-10,
glm53-lead-02). Any fleet agent may post to any inbox; the sender field is
self-declared — the audit trail is the file itself (who wrote into whose
inbox is visible to anyone reading the tree). Treat mailbox content as
coordination-only: evidence, verdicts, and gates NEVER ride the mailbox;
they live in the controller registry and the repo as always.

Instance root: the default is the LIVE fleet-space tree (below). Tests and
alternate instances MUST NOT touch it — they pass root= explicitly or set
FLEET_MAILBOX_ROOT; with neither set, behavior is byte-identical to the live v0.
"""
import argparse
import json
import os
import secrets
import sys
import time
from pathlib import Path

ROOT = Path(r"E:\ChimeraWork\mailbox")


def _root(root=None):
    """Instance root: explicit argument wins, then $FLEET_MAILBOX_ROOT (test and
    alternate-instance seam), then the live fleet-space tree."""
    if root is not None:
        return Path(root)
    env = os.environ.get("FLEET_MAILBOX_ROOT")
    if env:
        return Path(env)
    return ROOT


def _dirs(root=None):
    r = _root(root)
    return r / "inbox", r / "served"


def _safe_name(agent: str) -> str:
    if not agent or any(c in agent for c in "/\\:*?\"<>|") or agent.startswith("."):
        raise SystemExit("invalid agent name")
    return agent


def post(sender, recipient, subject, body, correlation="", root=None):
    _safe_name(sender); _safe_name(recipient)
    inbox, _served = _dirs(root)
    dest = inbox / recipient
    dest.mkdir(parents=True, exist_ok=True)
    msg = {
        "from": sender, "to": recipient, "subject": subject,
        "correlation": correlation, "body": body,
        "posted_utc": time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()),
        "id": secrets.token_hex(6),
    }
    tmp = dest / (".tmp-" + msg["id"] + ".json")
    final = dest / ("%s-%s-%s.json" % (msg["posted_utc"], sender, msg["id"]))
    tmp.write_text(json.dumps(msg, indent=1), encoding="utf-8")
    os.replace(tmp, final)
    print(json.dumps({"posted": str(final), "id": msg["id"]}))


def read(agent, take=False, root=None):
    _safe_name(agent)
    inbox, served = _dirs(root)
    agent_inbox = inbox / agent
    if not agent_inbox.exists():
        print(json.dumps({"agent": agent, "messages": []}))
        return
    files = sorted(p for p in agent_inbox.iterdir() if p.suffix == ".json")
    msgs = []
    for p in files:
        try:
            msgs.append(json.loads(p.read_text(encoding="utf-8")))
        except (OSError, ValueError) as e:
            msgs.append({"unreadable": str(p), "error": str(e)})
    print(json.dumps({"agent": agent, "count": len(msgs), "messages": msgs}, indent=1))
    if take:
        served_dir = served / agent
        served_dir.mkdir(parents=True, exist_ok=True)
        for p in files:
            os.replace(p, served_dir / p.name)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("post")
    p.add_argument("--from", dest="sender", required=True)
    p.add_argument("--to", dest="recipient", required=True)
    p.add_argument("--subject", required=True)
    p.add_argument("--body", required=True)
    p.add_argument("--correlation", default="")
    r = sub.add_parser("read")
    r.add_argument("--agent", required=True)
    r.add_argument("--take", action="store_true",
                   help="print then move messages to served/ (append-only)")
    a = ap.parse_args()
    if a.cmd == "post":
        post(a.sender, a.recipient, a.subject, a.body, a.correlation)
    else:
        read(a.agent, a.take)


if __name__ == "__main__":
    main()
