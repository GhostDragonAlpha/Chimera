"""Restore Feature Ledger statuses lost to the junk-node quarantine.

The quarantine removed information-free nodes, but a batch of legitimate
FeatureUpdate records went with them, regressing loops 3-7 to not_started on
the Pre-Flight board. This script re-records `verified` ONLY for features that
have hard evidence in the graph: a VisualVerification node whose task_name
contains the feature name and whose status/lm response indicates verified.

Conservative rules:
- only upgrades features whose CURRENT latest status is not_started/missing
- never touches live judgments (researching/applying/blocked/needs_refinement)
- every re-record is marked backfilled=True (provenance-honest)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "core"))
from graphify_interface import load_dna_graph, record_feature

VERIFIED_TOKENS = ("verified", "pass")


def main():
    dna = load_dna_graph()
    nodes = dna.get("nodes", [])

    # Ledger features with loop numbers
    ledger = {}
    for n in nodes:
        if n.get("type") == "Feature" and str(n.get("spiral_loop", "")).startswith("Loop"):
            try:
                ledger[n["name"]] = int(n["spiral_loop"].split()[-1])
            except (ValueError, IndexError, KeyError):
                continue

    # Latest FeatureUpdate status per feature
    latest = {}
    for n in nodes:
        if n.get("type") != "FeatureUpdate":
            continue
        name, ts = n.get("feature_name"), n.get("timestamp", "")
        if name and (name not in latest or ts > latest[name][0]):
            latest[name] = (ts, n.get("status", ""))

    # Visual verification evidence
    evidence = [n for n in nodes if n.get("type") == "VisualVerification"
                and any(tok in str(n.get("status", "")).lower() for tok in VERIFIED_TOKENS)]

    restored, skipped = [], []
    for feature, loop in sorted(ledger.items()):
        current = latest.get(feature, ("", "not_started"))[1] or "not_started"
        if current not in ("not_started", ""):
            continue  # live judgment or already recorded — leave alone
        proof = [e for e in evidence if feature.lower() in str(e.get("task_name", "")).lower()]
        if not proof:
            skipped.append(feature)
            continue
        node_id = record_feature(feature, loop, "verified", parameters={
            "restored_from": proof[0].get("id"),
            "evidence_task": proof[0].get("task_name"),
            "note": "re-recorded from VisualVerification evidence after quarantine regression",
        }, backfilled=True)
        restored.append((feature, loop, node_id))
        print(f"restored: {feature} (loop {loop}) <- {proof[0].get('task_name')}")

    print(f"\nrestored {len(restored)} features; {len(skipped)} not_started features had no visual evidence (left as-is)")


if __name__ == "__main__":
    main()
