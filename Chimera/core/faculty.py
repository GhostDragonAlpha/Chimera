"""
The Faculty — the curriculum writes its own exams from the studio's own scars.

The idea worth building (2026-07-12, from the entropy/aliveness discussion)
--------------------------------------------------------------------------
A school where the teacher writes every exam is inheriting objectives. A
lineage writes its own — what killed the last generation becomes the test the
next must pass. That is the one place the "life as problem-solving matter"
frame touches real code: the boundary isn't feeling, it's whether a system's
acceptance criteria are GIVEN to it or GROWN by it.

Chimera already distills failures into heuristics (heuristic_distiller ->
PENDING_HEURISTICS -> promoted H-rules) and records SurpriseMoments live. But
those scars never became EXAMS: as of first light, 18 promoted H-rules exist
and zero are a specific curriculum checkpoint. The Faculty closes that loop —
it reads the constitution's H-rules and the graph's surprises and PROPOSES
checkpoints that pin each scar to a question every future feature must answer.

The safety boundary (why this is authorship, not runaway self-modification)
---------------------------------------------------------------------------
The Faculty only ever PROPOSES, into docs/curriculum/pending_checkpoints.json.
Promotion into the live curriculum.json is a separate, gated act (promote),
exactly like the Gardener's human-approved heuristic queue. The system may
author its own objectives; a gate still decides which ones become real. Every
proposed checkpoint carries PROVENANCE (the scar it came from) and a verify
spec the curriculum engine can actually grade — the Faculty cannot invent an
exam that cannot be marked.

CLI
---
    python -m core.faculty propose [--from-surprises] [--limit N]
    python -m core.faculty list [--all]
    python -m core.faculty promote --id fac.h31 [--force]
    python -m core.faculty lint          # every pending spec is engine-gradable
    python -m core.faculty stats
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent

CONSTITUTION = Path(os.environ.get("CHIMERA_CONSTITUTION", ROOT.parent / "CLAUDE.md"))
PENDING_PATH = Path(os.environ.get("CHIMERA_FACULTY_PENDING",
                                   ROOT / "docs" / "curriculum" / "pending_checkpoints.json"))

try:
    from core import curriculum as cu
except ImportError:
    sys.path.insert(0, str(HERE))
    import curriculum as cu

FACULTY_DISCIPLINE = "faculty"
FACULTY_COURSE_TITLE = "Faculty electives (grown from the studio's own scars)"


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_pending():
    try:
        return json.loads(PENDING_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"proposed": []}


def _write_pending(data):
    PENDING_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = PENDING_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(PENDING_PATH)


# ---------------------------------------------------------------------------
# What already exists — so the Faculty proposes only genuine GAPS.
# ---------------------------------------------------------------------------
def _curriculum_text():
    try:
        return cu.CURRICULUM_PATH.read_text(encoding="utf-8")
    except Exception:
        return ""


def _existing_checkpoint_ids():
    ids = set()
    try:
        for band in cu.load_curriculum():
            for course in band["courses"]:
                for cp in course["checkpoints"]:
                    ids.add(cp["id"])
    except Exception:
        pass
    for p in _read_pending()["proposed"]:
        ids.add(p["checkpoint"]["id"])
    return ids


def _h_rules_already_pinned():
    """H-rules cited LITERALLY (by id) anywhere an exam can see them — the
    curriculum plus already-pending proposals. Word-boundary matched so H-1
    does not read as covered by H-13 (a lesson this session paid for)."""
    text = _curriculum_text() + "\n" + json.dumps(_read_pending())
    return set(re.findall(r"\bH-\d+\b", text))


# ---------------------------------------------------------------------------
# Scar readers
# ---------------------------------------------------------------------------
def _h_rules_from_constitution():
    """[(id, gloss_line)] for every promoted H-rule in CLAUDE.md."""
    out, seen = [], set()
    try:
        text = CONSTITUTION.read_text(encoding="utf-8")
    except OSError:
        return out
    for line in text.splitlines():
        m = re.search(r"\[(H-\d+)[,\]]", line)
        if not m:
            continue
        rid = m.group(1)
        if rid in seen:
            continue
        seen.add(rid)
        gloss = re.sub(r"^\s*[-*]?\s*", "", line).strip()
        gloss = re.sub(r"\*\*\[H-\d+[^\]]*\]\*\*\s*", "", gloss)  # strip the badge
        out.append((rid, gloss))
    return out


_STOP = {"never", "always", "before", "means", "a", "an", "the", "with", "when",
         "that", "this", "from", "into", "must", "same", "then", "than", "only",
         "each", "your", "their", "which", "while", "after"}


def _distinctive_token(text):
    """A concrete identifier from a rule the exam can require a student to name:
    CamelCase, UPPER/underscored, error codes, gate_names. Falls back to a
    salient domain noun, else None."""
    for pat in (r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b",   # CamelCase
                r"\b[a-z]+_[a-z_]+\b",                  # snake_case (reset_position)
                r"\bC\d{4}\b", r"\bLNK\d+\b",           # compiler/linker codes
                r"\bgate_[a-z_]+\b",
                r"\b[A-Z]{2,}(?:_[A-Z0-9]+)+\b"):        # UPPER_SNAKE
        m = re.search(pat, text)
        if m and m.group(0).lower() not in _STOP:
            return m.group(0)
    for noun in ("telemetry", "screenshot", "viewport", "beat", "build",
                 "movement", "component", "economy", "template", "schema"):
        if re.search(rf"\b{noun}\b", text, re.IGNORECASE):
            return noun
    return None


def _band_for(text):
    low = text.lower()
    if any(k in low for k in ("screenshot", "viewport", "desktop", "palette",
                              "dark", "vision")):
        return "master"
    if any(k in low for k in ("economy", "grade c/f", "criteria coverage", " fps")):
        return "high"
    return "bachelor"


# ---------------------------------------------------------------------------
# Proposal builders — each returns a checkpoint dict + provenance, or None.
# ---------------------------------------------------------------------------
def _proposal_from_h_rule(rid, gloss, existing_ids):
    cid = f"fac.{rid.lower()}"          # fac.h-31
    if cid in existing_ids:
        return None
    token = _distinctive_token(gloss)
    must = [rf"\b{re.escape(rid)}\b"]
    hint = ""
    if token:
        must.append(re.escape(token))
        hint = f" Name the concrete mechanism (the artifact must mention '{token}')."
    prompt = (
        f"SCAR {rid} — \"{gloss[:150]}\" — was distilled from a real failure the "
        f"studio already paid for. In <feature>'s own terms, show how <feature> is "
        f"structurally immune to this failure mode, or confess exactly where it is "
        f"exposed and the specific change that would close it. Cite {rid} by id.{hint}")
    checkpoint = {
        "id": cid,
        "prompt": prompt,
        "artifact": f"{cid.replace('.', '_').replace('-', '_')}.md",
        "verify": [{"type": "artifact", "min_chars": 180, "must_match": must},
                   {"type": "h_rule"}],
    }
    provenance = {"source_type": "h_rule", "source_id": rid, "quote": gloss[:180]}
    return {"band": _band_for(gloss), "discipline": FACULTY_DISCIPLINE,
            "checkpoint": checkpoint, "provenance": provenance,
            "status": "pending", "proposed_at": _now_iso()}


def _proposals_from_surprises(existing_ids, limit=5):
    """Weaker, flagged: recent SurpriseMoments -> hazard checkpoints. The verify
    is artifact + a keyword from the surprise (no live cross-check exists for an
    arbitrary surprise), so these are marked lower-confidence."""
    try:
        nodes = cu._graph_nodes()
    except Exception:
        return []
    surp = [n for n in nodes if n.get("type") == "SurpriseMoment"]
    surp.sort(key=lambda n: n.get("timestamp", ""), reverse=True)
    out, seen_tokens = [], set()
    for n in surp:
        blob = " ".join(str(n.get(k, "")) for k in ("context", "reality", "surprise"))
        token = _distinctive_token(blob)
        if not token or token.lower() in seen_tokens:
            continue
        sig = re.sub(r"[^a-z0-9]", "", token.lower())[:16]
        cid = f"fac.s.{sig}"
        if cid in existing_ids or cid in {p['checkpoint']['id'] for p in out}:
            continue
        seen_tokens.add(token.lower())
        prompt = (
            f"HAZARD (from a recorded surprise): \"{blob[:150]}\". Show that "
            f"<feature> cannot be bitten by this class of surprise — name where "
            f"'{token}' would appear in <feature> and how it is handled — or flag "
            f"the exposure. This checkpoint is Faculty-proposed and lower-confidence "
            f"until an engineer tightens its verify spec.")
        out.append({
            "band": "bachelor", "discipline": FACULTY_DISCIPLINE,
            "checkpoint": {"id": cid, "prompt": prompt,
                           "artifact": f"{cid.replace('.', '_')}.md",
                           "verify": [{"type": "artifact", "min_chars": 180,
                                       "must_match": [re.escape(token)]}]},
            "provenance": {"source_type": "surprise", "source_id": n.get("id"),
                           "quote": blob[:180], "confidence": "low"},
            "status": "pending", "proposed_at": _now_iso()})
        if len(out) >= limit:
            break
    return out


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def propose(from_surprises=False, limit=50):
    """Read the studio's scars; stage checkpoints for the ones with no exam.
    Idempotent: never re-proposes an id already live or pending."""
    existing = _existing_checkpoint_ids()
    pinned = _h_rules_already_pinned()
    pending = _read_pending()
    added = []
    for rid, gloss in _h_rules_from_constitution():
        if rid in pinned:
            continue
        p = _proposal_from_h_rule(rid, gloss, existing)
        if p:
            added.append(p)
            existing.add(p["checkpoint"]["id"])
    if from_surprises:
        added.extend(_proposals_from_surprises(existing, limit=5))
    # Validate every proposal is engine-gradable before staging (the Faculty
    # cannot invent an exam that cannot be marked).
    added = [p for p in added if _spec_is_gradable(p["checkpoint"])]
    added = added[:limit]
    pending["proposed"].extend(added)
    _write_pending(pending)
    return added


def _spec_is_gradable(checkpoint):
    if not checkpoint.get("artifact") or "<feature>" not in checkpoint["prompt"] \
            and "feature" not in checkpoint["prompt"].lower():
        return False
    for spec in checkpoint.get("verify", []):
        if spec.get("type") not in cu.VERIFIERS:
            return False
    return True


def lint():
    """Every pending proposal must be engine-gradable and unique. Returns
    list[(id, ok, reason)]."""
    live = _existing_live_ids()
    seen, out = set(), []
    for p in _read_pending()["proposed"]:
        cid = p["checkpoint"]["id"]
        if cid in seen:
            out.append((cid, False, "duplicate id in pending"))
        elif cid in live:
            out.append((cid, False, "id already live in curriculum"))
        elif not _spec_is_gradable(p["checkpoint"]):
            out.append((cid, False, "verify spec not engine-gradable"))
        else:
            out.append((cid, True, "ok"))
        seen.add(cid)
    return out


def _existing_live_ids():
    ids = set()
    for band in cu.load_curriculum():
        for course in band["courses"]:
            for cp in course["checkpoints"]:
                ids.add(cp["id"])
    return ids


def promote(cid, force=False):
    """THE GATE. Move one approved pending checkpoint into the live curriculum.
    Refuses a duplicate id. Records the promotion to the graph (non-fatal)."""
    pending = _read_pending()
    entry = next((p for p in pending["proposed"] if p["checkpoint"]["id"] == cid), None)
    if entry is None:
        raise KeyError(f"no pending proposal {cid!r}")
    if entry.get("status") == "promoted":
        raise ValueError(f"{cid} already promoted")
    if not force and entry.get("status") == "vetoed":
        raise ValueError(f"{cid} is vetoed — pass --force to override the gate")
    if cid in _existing_live_ids():
        raise ValueError(f"{cid} already exists in the live curriculum")

    curriculum = json.loads(cu.CURRICULUM_PATH.read_text(encoding="utf-8"))
    band = next((b for b in curriculum["bands"] if b["band"] == entry["band"]), None)
    if band is None:
        raise ValueError(f"target band {entry['band']!r} not in curriculum")
    course = next((c for c in band["courses"]
                   if c.get("discipline") == FACULTY_DISCIPLINE), None)
    if course is None:
        course = {"discipline": FACULTY_DISCIPLINE, "title": FACULTY_COURSE_TITLE,
                  "checkpoints": []}
        band["courses"].append(course)
    cp = dict(entry["checkpoint"])
    cp["provenance"] = entry["provenance"]          # the exam remembers its scar
    course["checkpoints"].append(cp)
    tmp = cu.CURRICULUM_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(curriculum, indent=2), encoding="utf-8")
    tmp.replace(cu.CURRICULUM_PATH)

    entry["status"] = "promoted"
    entry["promoted_at"] = _now_iso()
    _write_pending(pending)
    try:
        from core.graphify_interface import record_phase
        record_phase(f"Faculty promoted checkpoint {cid}",
                     f"from {entry['provenance']['source_type']} "
                     f"{entry['provenance'].get('source_id')} into band {entry['band']}", "")
    except Exception:
        pass
    return cp


def veto(cid, note=""):
    pending = _read_pending()
    entry = next((p for p in pending["proposed"] if p["checkpoint"]["id"] == cid), None)
    if entry is None:
        raise KeyError(f"no pending proposal {cid!r}")
    entry["status"] = "vetoed"
    entry["veto_note"] = note
    _write_pending(pending)
    return entry


def stats():
    pending = _read_pending()["proposed"]
    by_status = {}
    for p in pending:
        by_status[p["status"]] = by_status.get(p["status"], 0) + 1
    scars = _h_rules_from_constitution()
    pinned = _h_rules_already_pinned()
    uncovered = [rid for rid, _ in scars if rid not in pinned]
    return {"pending": len(pending), "by_status": by_status,
            "h_rules_total": len(scars), "h_rules_uncovered": len(uncovered),
            "uncovered_ids": uncovered}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description="The Faculty — curriculum writes its own exams")
    sub = p.add_subparsers(dest="cmd", required=True)
    pp = sub.add_parser("propose", help="Stage checkpoints for scars with no exam")
    pp.add_argument("--from-surprises", action="store_true",
                    help="also mine recent SurpriseMoments (lower-confidence)")
    pp.add_argument("--limit", type=int, default=50)
    pl = sub.add_parser("list", help="Show pending proposals")
    pl.add_argument("--all", action="store_true", help="include promoted/vetoed")
    pr = sub.add_parser("promote", help="THE GATE — move a proposal into the live curriculum")
    pr.add_argument("--id", required=True)
    pr.add_argument("--force", action="store_true")
    pv = sub.add_parser("veto", help="Reject a proposal")
    pv.add_argument("--id", required=True)
    pv.add_argument("--note", default="")
    sub.add_parser("lint", help="Every pending spec is engine-gradable + unique")
    sub.add_parser("stats", help="Coverage: scars with no exam yet")

    args = p.parse_args(argv)
    if args.cmd == "propose":
        added = propose(from_surprises=args.from_surprises, limit=args.limit)
        print(f"proposed {len(added)} checkpoint(s) -> {PENDING_PATH.name} "
              f"(pending approval; promote is the gate)")
        for a in added:
            c = a["checkpoint"]
            print(f"  {c['id']:<12} [{a['band']}] <- {a['provenance']['source_type']} "
                  f"{a['provenance'].get('source_id')}")
    elif args.cmd == "list":
        for pnd in _read_pending()["proposed"]:
            if not args.all and pnd["status"] != "pending":
                continue
            c = pnd["checkpoint"]
            conf = pnd["provenance"].get("confidence", "")
            print(f"  [{pnd['status']:>8}] {c['id']:<12} [{pnd['band']}] "
                  f"{c['prompt'][:70]}{' ('+conf+')' if conf else ''}")
    elif args.cmd == "promote":
        try:
            cp = promote(args.id, force=args.force)
        except (KeyError, ValueError) as e:
            print(f"REFUSED: {e}")
            sys.exit(1)
        print(f"PROMOTED {cp['id']} into the live curriculum "
              f"(course: {FACULTY_COURSE_TITLE})")
    elif args.cmd == "veto":
        veto(args.id, note=args.note)
        print(f"vetoed {args.id}")
    elif args.cmd == "lint":
        rows = lint()
        bad = [r for r in rows if not r[1]]
        for cid, ok, reason in rows:
            print(f"  [{'OK' if ok else 'BAD'}] {cid}: {reason}")
        print(f"{len(rows) - len(bad)}/{len(rows)} pending proposals gradable")
        sys.exit(1 if bad else 0)
    elif args.cmd == "stats":
        s = stats()
        print(f"Faculty: {s['pending']} pending {s['by_status']}")
        print(f"Scars: {s['h_rules_uncovered']}/{s['h_rules_total']} H-rules still "
              f"have NO exam: {', '.join(s['uncovered_ids']) or 'none — all covered'}")


if __name__ == "__main__":
    main()
