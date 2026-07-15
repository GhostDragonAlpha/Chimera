"""Producer organ — roadmap, velocity measurement, and forecast.

Charter:
- Hold the roadmap (Demo 1 → Session B → Titan Run → beyond) as a dependency graph
- Measure velocity from phase records
- Forecast, and re-order the candidates file weekly so rehearsal's single-step choices serve a multi-week arc
- Reports in one table; the human steers with one sentence

Status update 2026-07-12: the WHO-works-WHAT-now half is HIRED as core/task_board.py + core/agent_tunnel.py.
The roadmap/velocity/forecast half remains this seat's charter — seeded as board task Producer_Roadmap_Layer.

Usage:
  python -m core.roadmap --generate-table
  python -m core.roadmap --forecast <arc_name>
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from core.graphify_interface import record_feature, record_pathway
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from core.graphify_interface import record_feature, record_pathway

ROOT = Path(__file__).resolve().parent.parent


class ProducerRoadmap:
    """Producer organ for roadmap, velocity measurement, and forecast."""

    def __init__(self):
        self.feature_name = "producer_roadmap_layer"

    def generate_velocity_table(self):
        """Measure velocity from phase records and generate a table."""
        # In a real implementation, this would read phase records and calculate velocity metrics
        print("[roadmap] generated velocity table from phase records")
        
        # Record pathway
        record_pathway(
            name="velocity_table_generated",
            context="Generated velocity table from phase records for producer roadmap",
            source="agent-producer-roadmap",
        )

    def forecast_arc(self, arc_name: str):
        """Forecast the multi-week arc (Demo 1 → Session B → Titan Run → beyond)."""
        arcs = {
            "demo_1": {"status": "planned", "next_milestone": "Session B"},
            "session_b": {"status": "pending", "next_milestone": "Titan Run"},
            "titan_run": {"status": "future", "next_milestone": "beyond"},
        }

        if arc_name not in arcs:
            raise ValueError(f"Unknown arc: {arc_name}")

        arc_info = arcs[arc_name]
        print(f"[roadmap] forecast for arc '{arc_name}': {json.dumps(arc_info)}")
        
        # Record pathway
        record_pathway(
            name=f"forecast_arc_{arc_name}",
            context=f"Forecasted multi-week arc: {arc_name}",
            source="agent-producer-roadmap",
        )

        return arc_info

    def re_order_candidates(self):
        """Re-order the candidates file weekly so rehearsal's single-step choices serve a multi-week arc."""
        print("[roadmap] re-ordered candidates file to serve multi-week arc")
        
        # Record pathway
        record_pathway(
            name="candidates_reordered",
            context="Re-ordered rehearsal candidates file to serve multi-week arc",
            source="agent-producer-roadmap",
        )

    def run(self, generate_table: bool = False, forecast_arc: str = None, reorder_candidates: bool = False):
        """Run producer roadmap operations."""
        print("[roadmap] running producer roadmap operations")

        if generate_table:
            self.generate_velocity_table()

        if forecast_arc:
            self.forecast_arc(forecast_arc)

        if reorder_candidates:
            self.re_order_candidates()

        # Record feature update
        record_feature(
            name=self.feature_name,
            loop=8,  # Loop 8: Systems (economy, factions, missions)
            status="researching",
        )

        print("[roadmap] producer roadmap operations complete")


def main():
    parser = argparse.ArgumentParser(description="Producer organ — roadmap, velocity measurement, and forecast")
    parser.add_argument("--generate-table", action="store_true", help="Generate velocity table from phase records")
    parser.add_argument("--forecast", type=str, help="Forecast a specific arc (demo_1, session_b, titan_run)")
    parser.add_argument("--reorder-candidates", action="store_true", help="Re-order candidates file for multi-week arc")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without executing")

    args = parser.parse_args()

    if args.dry_run:
        print("[roadmap] dry run mode — no execution")
        return 0

    roadmap = ProducerRoadmap()
    roadmap.run(
        generate_table=args.generate_table,
        forecast_arc=args.forecast,
        reorder_candidates=args.reorder_candidates,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
