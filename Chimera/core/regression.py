"""Regression Curator — converts rejection observations into permanent regression beat scripts.

Every rejection observation (feature verdict=rejected), chaos crash, or solver fix
in the DNA graph becomes a permanent regression beat that guards against backsliding.
The curator mines these failures and converts them into beat scripts that can be
replayed via the Sleepwalker.

Usage (CLI):
    python -m core.regression mine              # scan graph for rejections; print candidates
    python -m core.regression propose <obs_id>  # generate beat JSON for one observation
    python -m core.regression prune --days 180  # freshen stale beats
    python -m core.regression --help

Usage (module):
    from core.regression import RegressionCurator
    curator = RegressionCurator()
    candidates = curator.mine()  # returns list of rejection Observation nodes
    beat = curator.propose(candidates[0])  # returns beat dict (JSON-serializable)
"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from core.graphify_interface import load_dna_graph, record_heuristic
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from core.graphify_interface import load_dna_graph, record_heuristic

ROOT = Path(__file__).resolve().parent.parent          # E:/PythonChimera/Chimera
BEATS_DIR = ROOT / "docs" / "beats"


class RegressionCurator:
    """Curator that mines and converts rejection observations into regression beats."""

    def __init__(self):
        self.graph = load_dna_graph()
        self.nodes = self.graph.get("nodes", [])
        self.beat_count = 0

    def mine(self) -> list:
        """Scan DNA graph for rejection observations and chaos crashes.

        Returns:
            List of dicts with Observation node data (type, id, feature, verdict, context).
        """
        rejections = []

        # Find all Observation nodes with verdict=rejected or verdict=chaos
        for node in self.nodes:
            if node.get("type") != "Observation":
                continue

            verdict = node.get("verdict", "").lower()
            if verdict in ("rejected", "chaos", "crash"):
                rejections.append({
                    "id": node.get("id"),
                    "feature": node.get("feature", "unknown"),
                    "verdict": verdict,
                    "status": node.get("status", "unknown"),
                    "timestamp": node.get("timestamp", ""),
                    "notes": node.get("notes", ""),
                    "error_signature": node.get("error_signature", ""),
                    "context": node.get("context", ""),
                })

        return sorted(rejections, key=lambda x: x["timestamp"], reverse=True)

    def propose(self, rejection_record: dict) -> dict:
        """Convert a single rejection observation into a regression beat.

        Args:
            rejection_record: Dict with 'id', 'feature', 'verdict', 'notes', etc.

        Returns:
            Dict representing a beat (JSON-serializable, Sleepwalker format).
        """
        feature_name = rejection_record.get("feature", "unknown_feature")
        obs_id = rejection_record.get("id", "unknown_obs")
        timestamp = rejection_record.get("timestamp", datetime.now(timezone.utc).isoformat())
        error_sig = rejection_record.get("error_signature", "unknown")
        notes = rejection_record.get("notes", "")
        context = rejection_record.get("context", "")

        # Construct a beat that exercises the failure condition
        # The beat structure follows Sleepwalker schema
        beat = {
            "id": f"regression_{obs_id}",
            "name": f"Regression Guard: {feature_name}",
            "description": f"Regression beat for {feature_name} (observation {obs_id}). "
                          f"Guards against failure: {error_sig}",
            "origin_observation": obs_id,
            "created_at": timestamp,
            "actions": [
                {
                    "action": "setup",
                    "description": f"Initialize {feature_name} test harness",
                },
                {
                    "action": "exercise",
                    "description": f"Execute {feature_name} in the condition that caused rejection",
                    "context": context,
                },
            ],
            "expects": [
                {
                    "expect": "not_crash",
                    "description": "The feature must not crash during exercise",
                },
                {
                    "expect": "state_change",
                    "description": f"The feature must exhibit a measurable state change",
                    "context": f"Failure was: {error_sig}",
                },
            ],
            "tags": [feature_name, "regression", f"orig:{error_sig}"],
            "metadata": {
                "curator_version": 1,
                "feature_name": feature_name,
                "rejection_notes": notes,
                "derived_from_observation": obs_id,
            },
        }

        return beat

    def save_beat(self, beat: dict, filename: str = None) -> Path:
        """Save a beat dict to a file under docs/beats/.

        Args:
            beat: Dict (from propose())
            filename: Optional filename (default: beat['id'].beats.json)

        Returns:
            Path to saved file.
        """
        if filename is None:
            filename = f"{beat.get('id', 'beat')}.beats.json"

        beat_file = BEATS_DIR / filename
        beat_file.parent.mkdir(parents=True, exist_ok=True)

        with open(beat_file, "w", encoding="utf-8") as f:
            json.dump(beat, f, indent=2)

        self.beat_count += 1
        return beat_file

    def prune(self, max_age_days: int = 180) -> dict:
        """Freshen stale regression beats.

        Args:
            max_age_days: Remove or flag beats older than this.

        Returns:
            Dict with pruning stats: {'archived': N, 'flagged': N, 'total_checked': N}.
        """
        if not BEATS_DIR.exists():
            return {"archived": 0, "flagged": 0, "total_checked": 0}

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        stats = {"archived": 0, "flagged": 0, "total_checked": 0}

        for beat_file in BEATS_DIR.glob("regression_*.beats.json"):
            stats["total_checked"] += 1

            try:
                with open(beat_file, "r", encoding="utf-8") as f:
                    beat = json.load(f)

                created_at_str = beat.get("created_at", "")
                if created_at_str:
                    # Parse ISO format timestamp
                    try:
                        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                        if created_at < cutoff_date:
                            # Mark for archive (don't delete; archive-never-delete principle)
                            beat["status"] = "archived"
                            with open(beat_file, "w", encoding="utf-8") as f:
                                json.dump(beat, f, indent=2)
                            stats["archived"] += 1
                    except ValueError:
                        pass  # Skip unparseable timestamps
            except Exception:
                pass  # Skip malformed files

        return stats


def main():
    parser = argparse.ArgumentParser(description="Regression Curator: mine rejections into regression beats")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # mine subcommand
    subparsers.add_parser("mine", help="Scan graph for rejection observations")

    # propose subcommand
    propose_parser = subparsers.add_parser("propose", help="Generate beat JSON for an observation")
    propose_parser.add_argument("obs_id", help="Observation node ID")
    propose_parser.add_argument("--save", action="store_true", help="Save beat to file")

    # prune subcommand
    prune_parser = subparsers.add_parser("prune", help="Freshen stale regression beats")
    prune_parser.add_argument("--days", type=int, default=180, help="Max age in days (default: 180)")

    args = parser.parse_args()

    curator = RegressionCurator()

    if args.command == "mine":
        candidates = curator.mine()
        print(f"Found {len(candidates)} rejection observations:")
        for i, cand in enumerate(candidates[:10], 1):
            print(f"  {i}. {cand['id']:30s} {cand['feature']:40s} [{cand['verdict']}]")
        if len(candidates) > 10:
            print(f"  ... and {len(candidates) - 10} more")
        return 0

    elif args.command == "propose":
        candidates = curator.mine()
        matching = [c for c in candidates if c["id"] == args.obs_id]
        if not matching:
            print(f"ERROR: Observation {args.obs_id} not found", file=sys.stderr)
            return 1

        beat = curator.propose(matching[0])
        print(json.dumps(beat, indent=2))

        if args.save:
            beat_file = curator.save_beat(beat)
            print(f"Saved to: {beat_file}", file=sys.stderr)

        return 0

    elif args.command == "prune":
        stats = curator.prune(max_age_days=args.days)
        print(f"Pruning complete (max_age={args.days}d): "
              f"{stats['archived']} archived, {stats['flagged']} flagged, "
              f"{stats['total_checked']} checked")
        return 0

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
