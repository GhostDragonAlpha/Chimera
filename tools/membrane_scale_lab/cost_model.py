"""cost_model.py — memory and algorithmic cost model for membrane evaluation.

Derives from fixture statistics and measured timings to predict:
- buffer sizes scaling with vertices, faces, corners
- algorithmic cost scaling with topology
- per-operation counts

STATEMENT  The cost model decomposes membrane evaluation into named
           operations whose counts are derived directly from mesh topology,
           not fitted to timing data.

PREDICTION  Buffer memory scales linearly with vertices and faces;
            face evaluation cost scales with face count; CSR assembly
            cost scales with corner count (3 * face count).

FALSIFIER  Any derived formula whose predicted buffer size disagrees
           with the actual allocation by more than 10%.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(_TOOLS))
from fixture_generator import generate_suite, Fixture

# ---------------------------------------------------------------------------
# Cost model
# ---------------------------------------------------------------------------

@dataclass
class CostModel:
    fixture_name: str
    n_vertices: int
    n_faces: int
    n_corners: int
    degree_max: int
    degree_mean: float
    coord_scale: float

    @property
    def buffer_sizes(self) -> dict:
        return {
            "positions_f32_bytes": self.n_vertices * 3 * 4,
            "indices_u32_bytes": self.n_faces * 3 * 4,
            "gamma_f32_bytes": self.n_faces * 4,
            "csr_offsets_bytes": (self.n_vertices + 1) * 4,
            "csr_corner_idx_bytes": self.n_corners * 4,
            "face_records_bytes": self.n_faces * 64,   # FaceRecord = 64 bytes
            "vertex_forces_bytes": self.n_vertices * 4 * 4,
            "energy_bytes": 4,
            "validity_bytes": self.n_faces * 4,
            "total_storage_bytes": (
                self.n_vertices * 3 * 4
                + self.n_faces * 3 * 4
                + self.n_faces * 4
                + (self.n_vertices + 1) * 4
                + self.n_corners * 4
                + self.n_faces * 64
                + self.n_vertices * 4 * 4
                + 4
                + self.n_faces * 4
            ),
        }

    @property
    def op_counts(self) -> dict:
        return {
            "face_eval_flops_per_face": 30,
            "face_eval_total": self.n_faces * 30,
            "csr_gather_ops_per_corner": 3,
            "csr_gather_total": self.n_corners * 3,
            "energy_reduction_adds": self.n_faces,
            "total_flops": self.n_faces * 30 + self.n_corners * 3 + self.n_faces,
        }

    @property
    def scaling(self) -> dict:
        return {
            "vertices": "O(V)",
            "faces": "O(F)",
            "corners": "O(3F)",
            "assembly": "O(corners) = O(3F)",
            "energy": "O(F)",
            "memory": f"O(V + F) = {self.n_vertices + self.n_faces} elements",
        }

# ---------------------------------------------------------------------------
# Suite cost model
# ---------------------------------------------------------------------------

def model_suite(suite: dict) -> dict:
    models = {}
    for name, fx in suite.items():
        if fx is None:
            continue
        s = fx.stats
        cm = CostModel(
            fixture_name=s.name,
            n_vertices=s.n_vertices,
            n_faces=s.n_faces,
            n_corners=3 * s.n_faces,
            degree_max=s.degree_max,
            degree_mean=s.degree_mean,
            coord_scale=s.coord_scale,
        )
        models[name] = {
            "buffer_sizes": cm.buffer_sizes,
            "op_counts": cm.op_counts,
            "scaling": cm.scaling,
            "n_vertices": cm.n_vertices,
            "n_faces": cm.n_faces,
            "n_corners": cm.n_corners,
        }
    return models

# ---------------------------------------------------------------------------
# Manifest writer
# ---------------------------------------------------------------------------

def write_cost_model(models: dict, out_dir: Path, source_commit: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    manifest = {
        "schema": "chimera-membrane-scale-lab-cost-model-v1",
        "utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": source_commit,
        "models": models,
    }
    mp = out_dir / f"cost_model_{stamp}.json"
    mp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return mp

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Generate cost model for fixture suite")
    ap.add_argument("--fixtures", type=Path, default=Path("docs/evidence/membrane_scale_lab/fixtures"))
    ap.add_argument("--out", type=Path, default=Path("docs/evidence/membrane_scale_lab/cost_model"))
    ap.add_argument("--seed-base", type=int, default=0)
    ap.add_argument("--sizes", type=int, nargs="+", default=[4, 8, 16, 32, 64])
    args = ap.parse_args()
    head = __import__("subprocess").run(
        ["git", "-C", str(_TOOLS.parent), "rev-parse", "HEAD"],
        capture_output=True, text=True).stdout.strip()
    print(f"source_commit={head}")
    suite = generate_suite(sizes=tuple(args.sizes), seed_base=args.seed_base)
    models = model_suite(suite)
    mp = write_cost_model(models, args.out, head)
    for name, m in models.items():
        print(f"  {name}: nV={m['n_vertices']} nF={m['n_faces']}  "
              f"total_storage={m['buffer_sizes']['total_storage_bytes']} bytes")
    print(f"cost model: {len(models)} entries -> {mp}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
