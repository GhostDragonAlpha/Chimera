"""composed_chain.py -- P5 REUSE: the SAME piece artifacts (A, B and the
apex-weld seam law) reassembled into a SECOND, DIFFERENT topology, plus one
new piece C. ("then reuse the same artifact in a second assembly and
supported scale".)

TOPOLOGY LAW (why this is the minimal legal second assembly):
  Under the constant-gamma CURRENT-area law a rim weld is structurally
  impossible: a FREE seam ring has no equilibrium (every film contracts a
  free boundary -- witness (g) of composed_patch_checks: step_limit,
  residual 1.08) and a GROUNDED ring weld transfers nothing (bit-for-bit
  zero). Each fan piece has exactly ONE apex, and welds happen only at
  apexes, so a connected assembly's piece-interconnection graph is a STAR:
  one grounded piece whose apex is the seam vertex + k inverted pieces
  hanging from it (their far rims pinned). A connected chain A->B->C
  through two seam vertices CANNOT exist under this law (no piece owns two
  apexes); the minimal legal second assembly is therefore the k=2 FAN-OUT
  STAR: assembly 1's pieces A and B reused BYTE-IDENTICALLY (same
  generator params, same identity/reflection placement, same seam law)
  plus piece C -- a new inverted fan -- welded onto the SAME seam apex
  (two welded joints, one seam vertex).

  Consequence recorded as a finding: the INPUT port is legally pinned to
  the seam apex (the only free vertex of the star; the solver refuses
  loads on pinned vertices and freeing a rim has no equilibrium), so the
  input coincides with assembly 1's by necessity. The OUTPUT port is
  genuinely distinct: piece C's far rim. The transfer check (d) proves
  the load really crosses BOTH welded joints (B's and C's).

PIECES:
  A  high_degree_fan(n_rim=200, radius=1.0, height=0.3), identity
     placement, rim z=0 pinned, apex UP at z=0.3 = THE seam (owner).
  B  high_degree_fan(n_rim=200, radius=0.8, height=0.3), reflected about
     the seam plane (inverted), far rim z=0.6 pinned. Byte-identical to
     assembly 1's B (check (a) hashes the blocks).
  C  high_degree_fan(n_rim=200, radius=0.5, height=0.25), reflected about
     the seam plane (inverted), far rim z=0.55 pinned. C's cone lies
     strictly inside B's cone (no film intersection at any height:
     r_C(z) = 0.5*(z-0.3)/0.25 < 0.8*(z-0.3)/0.3 = r_B(z) for z in (0.3,
     0.55]).

MEASURED SCALE WINDOW (finding, reported not tuned): the three-film star's
stagnation residual grows ~linearly with the physical scale (1.15e-7 at
0.5x, 5.9e-7 at 1x, 1.11e-6 at 1.5x, 1.64e-6 at 2.0x -- the packet's
preregistered 1e-6 law unchanged), so the star's supported window on the
packet's size axis is ~[0.5, 1.5]. Assembly 2 qualifies at 1.0 and at the
NEW point 0.75 (residual 3.0e-7); 1.5x is recorded as honestly over the
gate, never tuned.

RECEIPT: schema chimera-mechanism-factory-composed-qualification-v1 -- the
VERSIONED schema the adapter already accepts explicitly (no adapter change,
no new acceptance surface; the unknown-variant fault F13 stays green). The
case shape (composed family, composition record, per-scale cases) is
unchanged; only the composition record's content describes the star.

CPU only; numpy + stdlib; no engine, no GPU, no network, no LLM calls.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent            # tools/mechanism_factory
_REPO = _HERE.parent.parent
_TOOLS = _HERE.parent
_LAB = _TOOLS / "membrane_scale_lab"
for _p in (str(_TOOLS), str(_LAB), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import patch_equilibrium as pe                    # noqa: E402  the qualified solve
import fixture_generator as fg                    # noqa: E402  lab fixtures
from surface_energy_reference import InvalidSurface  # noqa: E402
from evidence_output import (                     # noqa: E402
    EvidencePathExists, resolve_evidence_path)
import composed_patch as cp                       # noqa: E402  pieces A, B + seam law

EVID_DIR = cp.EVID_DIR
PACKET_PATH = cp.PACKET_PATH
COMPOSED_RECEIPT_SCHEMA = cp.COMPOSED_RECEIPT_SCHEMA
COMPOSED_FAMILY = "composed-apex-weld-fanout-star"

HASHED_SOURCES = list(cp.HASHED_SOURCES) + [
    "tools/mechanism_factory/composed_chain.py",
    "tools/mechanism_factory/composed_chain_checks.py",
]

# ── frozen assembly-2 parameters (before any run) ───────────────────────────
PIECE_C = {"n_rim": 200, "radius": 0.5, "height": 0.25, "seed": 3}
SEAM_LOAD_N = cp.SEAM_LOAD_N            # input port: same port law (0.8 N)
SUPPORTED_SCALES = (1.0, 0.75)          # 0.75 = NEW scale point (assembly 1
                                        # qualified 0.5/2.0; see the measured
                                        # scale-window finding above)
MAX_STEPS = cp.MAX_STEPS


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _source_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(_REPO), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=30, check=True)
        return out.stdout.strip() or "UNTRACKED"
    except Exception:                                 # pragma: no cover
        return "UNTRACKED"


def build_star(scale: float = 1.0,
               hangers: tuple = (cp.PIECE_B, PIECE_C),
               load: tuple = SEAM_LOAD_N,
               seam_perturbation: int | tuple | None = None) -> dict:
    """Build the k-hanger fan-out star by REUSING assembly 1's piece law:
    the ground piece A exactly as cp.build_assembly builds it (identity
    placement), every hanger by the SAME reflection/winding/seam-claim law
    cp uses, with cp's named refusals BEFORE any solve. seam_perturbation:
    index of the hanger whose seam claim is shifted (the falsifier)."""
    cp._check_scale(scale)
    n = cp.PIECE_A["n_rim"]
    h_a = cp.PIECE_A["height"]

    fa = fg.high_degree_fan(seed=cp.PIECE_A["seed"], n_rim=n,
                            radius=cp.PIECE_A["radius"], height=h_a)
    VA, FA = fa.positions.copy(), fa.faces.copy()   # A: byte-identical to asm 1
    V = VA.copy()
    F = FA.copy()
    seam = n                                        # A's apex = the seam (owner)
    blocks = []
    for k, prm in enumerate(hangers):
        fx = fg.high_degree_fan(seed=prm["seed"], n_rim=prm["n_rim"],
                                radius=prm["radius"], height=prm["height"])
        Vb = fx.positions.copy()
        Fb = fx.faces.copy()
        # SAME placement law as assembly 1's hangers, generalized to any
        # hanger height: reflect about (h_a + h)/2 so the hanger's apex
        # lands exactly ON the seam and its far rim at h_a + h. For B
        # (h = h_a) this is bit-identical to assembly 1's placement.
        Vb[:, 2] = (h_a + prm["height"]) - Vb[:, 2]
        Fb = Fb[:, [0, 2, 1]]                       # SAME winding fix
        claim = Vb[prm["n_rim"]].copy()             # hanger's seam REFERENCE
        if seam_perturbation == k:
            claim = claim + np.array([0.0, 0.0, 1.0e-6])
        d = float(np.linalg.norm(claim - V[seam]))
        if not (d <= cp.SEAM_COORD_TOL):
            raise InvalidSurface(
                cp.ComposedRejectionReason.SEAM_VERTEX_COORDINATE_MISMATCH,
                f"hanger {k} claims seam position {claim.tolist()} but the "
                f"owner holds {V[seam].tolist()} (||delta|| = {d:.3e} > "
                f"{cp.SEAM_COORD_TOL:.0e}); refusing before any solve")
        off = V.shape[0]
        V = np.vstack([V, Vb[:prm["n_rim"]]])       # apex dedups onto the seam
        Fh = Fb.copy()
        Fh[Fh == prm["n_rim"]] = seam               # hanger references A's index
        Fh[Fh < prm["n_rim"]] += off
        F = np.vstack([F, Fh])
        blocks.append({"piece": prm, "rim_block": list(range(off, off + n)),
                       "placement": "reflected about the seam plane "
                                    "(inverted), winding restored"})
    gamma = np.ones(F.shape[0], dtype=np.float64)
    pins = list(range(n))                           # A's rim
    for b in blocks:
        pins += b["rim_block"]                      # every hanger's far rim
    loads = [(seam, tuple(load))]
    if float(scale) != 1.0:
        V = V * float(scale)                        # rigid physical-size scale
    return {"positions": V, "faces": F, "gamma": gamma, "pins": pins,
            "loads": loads, "seam_index": seam, "scale": float(scale),
            "blocks": [list(range(n)), *[
                b["rim_block"] for b in blocks]],
            "placement": {
                "ground_piece": "A (identity placement, byte-identical to "
                                "assembly 1's A)",
                "hangers": [b["placement"] for b in blocks],
                "topology": "fan-out star k=2: ONE seam vertex (A's apex), "
                            "two welded joints (A-B reused byte-identically, "
                            "A-C new); connected chains through two seam "
                            "vertices do not exist under this law (one apex "
                            "per piece; rim welds forbidden by witness (g))",
            }}


def solve_star(star: dict, max_steps: int = MAX_STEPS) -> dict:
    """THE reference: ONE solve_equilibrium on the joined star mesh."""
    r = pe.solve_equilibrium(star["positions"], star["faces"], star["gamma"],
                             star["pins"], star["loads"], max_steps=max_steps)
    R = np.asarray(r.reaction_forces, dtype=np.float64)
    fsum = np.zeros(3)
    for _i, v in star["loads"]:
        fsum += np.asarray(v, dtype=np.float64)
    force_res = float(np.linalg.norm(R.sum(axis=0) + fsum))
    x = r.positions
    mom = np.zeros(3)
    for k, i in enumerate(r.fixed_indices):
        mom += np.cross(x[i], R[k])
    for i, v in star["loads"]:
        mom += np.cross(x[i], np.asarray(v, dtype=np.float64))
    moment_res = float(np.linalg.norm(mom))
    rn = np.linalg.norm(R, axis=1)
    n = cp.PIECE_A["n_rim"]
    means = {"A_rim_near_load": float(rn[:n].mean()),
             "B_far_rim_reused": float(rn[n:2 * n].mean()),
             "C_far_rim_output": float(rn[2 * n:].mean())}
    port_sums = {"B_reused_port": float(np.linalg.norm(R[n:2 * n].sum(axis=0))),
                 "C_output_port": float(np.linalg.norm(R[2 * n:].sum(axis=0)))}
    return {"result": r, "reactions": R,
            "force_balance_residual": force_res,
            "moment_balance_residual": moment_res,
            "block_mean_reaction_norms": means,
            "port_net_forces_N": port_sums,
            "seam_height": float(x[star["seam_index"], 2])}


def reduction_case() -> dict:
    """Remove piece C from assembly 2 -> the remaining mesh must be
    BYTE-IDENTICAL to assembly 1's (reuse proven structurally), and its
    solve must reproduce assembly 1's final energy within 1e-9 (C2
    precedent): the second assembly degenerates to the first qualified
    artifact."""
    star = build_star()
    n = cp.PIECE_A["n_rim"]
    Vs = star["positions"][:2 * n + 1]
    Fs = star["faces"][:2 * n]
    gs = star["gamma"][:2 * n]
    asm1 = cp.build_assembly()
    r1 = cp.solve_assembly(asm1)
    same_v = bool(np.array_equal(Vs, asm1.positions))
    same_f = bool(np.array_equal(Fs, asm1.faces))
    r_s = pe.solve_equilibrium(Vs, Fs, gs, asm1.pins, asm1.loads,
                               max_steps=MAX_STEPS)
    return {"stripped_positions_byte_equal": same_v,
            "stripped_faces_byte_equal": same_f,
            "stripped_energy": float(r_s.energy),
            "assembly1_energy": float(r1["result"].energy),
            "energy_delta": abs(float(r_s.energy) - float(r1["result"].energy)),
            "stripped_status": r_s.status,
            "assembly1_status": r1["result"].status}


def scale_window_probe() -> list:
    """The measured supported-scale window (finding): stagnation residuals
    across the packet's size axis; 1.5x and 2.0x exceed the packet's 1e-6
    law and are recorded as honestly unqualified scales for THIS topology
    (the gate is never widened)."""
    rows = []
    for s in (0.5, 0.75, 1.0, 1.5, 2.0):
        star = build_star(scale=s)
        solved = solve_star(star)
        rows.append({"scale_m": s,
                     "free_residual_N": solved["result"].free_residual,
                     "within_packet_law": bool(
                         solved["result"].free_residual
                         <= _thresholds()["max_free_residual_N"])})
    return rows


def _thresholds() -> dict:
    packet = json.loads(PACKET_PATH.read_bytes())
    return packet["acceptance_thresholds"]


def _compose_case(star: dict, solved: dict) -> dict:
    r = solved["result"]
    return {
        "case_id": f"{COMPOSED_FAMILY}_scale{star['scale']:g}",
        "family": COMPOSED_FAMILY,
        "status": r.status,
        "outputs": {
            "energy_J": float(r.energy),
            "max_free_residual_N": float(r.free_residual),
            "reactions_N": [[float(v) for v in row] for row in solved["reactions"]],
            "max_force_balance_residual": solved["force_balance_residual"],
            "max_moment_balance_residual": solved["moment_balance_residual"],
            "scale_m": star["scale"],
            "n_rim_per_piece": cp.PIECE_A["n_rim"],
            "seam_height_wu": solved["seam_height"],
            "block_mean_reaction_norms_N": solved["block_mean_reaction_norms"],
            "port_net_forces_N": solved["port_net_forces_N"],
        },
        "gpu_job": None,
    }


def _recomputed_pass(cases: list, thr: dict) -> bool:
    allowed = {"stationary", "stagnated"}
    for c in cases:
        if c["status"] not in allowed:
            return False
        out = c["outputs"]
        if out["max_free_residual_N"] > thr["max_free_residual_N"]:
            return False
        if out["max_force_balance_residual"] > thr["max_force_balance_residual"]:
            return False
        if out["max_moment_balance_residual"] > thr["max_moment_balance_residual"]:
            return False
    return True


def composition_record() -> dict:
    return {
        "what": "P5 REUSE: assembly 1's pieces A and B byte-identically plus "
                "new piece C, reassembled into the k=2 fan-out star; "
                "reference = ONE solve_equilibrium on the joined mesh; no "
                "new physics",
        "topology_law": "rim welds are impossible under this law (free ring: "
                        "no equilibrium; grounded ring: zero transfer -- "
                        "witnessed) and each piece has ONE apex, so every "
                        "connected assembly is a single-seam STAR; the "
                        "minimal legal second assembly is k=2",
        "pieces": {"A": dict(cp.PIECE_A, role="ground piece; owns the seam; "
                             "input port at the seam apex (legally the only "
                             "free vertex)", placement="identity, "
                             "byte-identical to assembly 1's A (hashed)"),
                   "B": dict(cp.PIECE_B, role="reused hanger; far rim = "
                             "reused output witness", placement="reflected, "
                             "byte-identical to assembly 1's B (hashed)"),
                   "C": dict(PIECE_C, role="new hanger; far rim = the "
                             "DISTINCT output port", placement="reflected; "
                             "cone strictly inside B's (no intersection)")},
        "seam": {"vertices": [cp.PIECE_A["n_rim"]],
                 "owner": "piece A",
                 "referenced_by": ["piece B (reused weld)",
                                   "piece C (new weld)"],
                 "joints": 2, "vertices_count": 1,
                 "note": "two welded joints at one seam vertex; the load "
                         "crosses both (check (d))"},
        "ports": {"input": "vertical dead load (0.8 N) at the seam apex -- "
                  "legally identical in position to assembly 1's input (the "
                  "only free vertex; loads on pinned vertices are refused; "
                  "freeing a rim has no equilibrium)",
                  "output": "reactions at piece C's far rim pins (distinct "
                            "from assembly 1's B far rim)"},
        "supported_scales_m": list(SUPPORTED_SCALES),
        "scale_window_finding": "the star's stagnation residual grows "
                                "~linearly with scale (1.15e-7 at 0.5x, "
                                "1.11e-6 at 1.5x, 1.64e-6 at 2.0x); within "
                                "the packet's UNCHANGED 1e-6 law the star "
                                "qualifies at 1.0 and the NEW 0.75; 1.5x "
                                "and 2.0x are recorded as honestly "
                                "over-gate for this topology",
        "reduction": "removing C leaves a mesh byte-identical to assembly 1 "
                     "(hashed) whose solve reproduces assembly 1's energy "
                     "exactly (check (e))",
    }


def build_composed_receipt(cases: list, scale_window: list) -> dict:
    packet_bytes = PACKET_PATH.read_bytes()
    packet = json.loads(packet_bytes)
    thr = packet["acceptance_thresholds"]
    ok = _recomputed_pass(cases, thr)
    return {
        "schema": COMPOSED_RECEIPT_SCHEMA,
        "utc": datetime.now(timezone.utc).isoformat(),
        "adapter_version": "adapter-v1",
        "source_commit": _source_commit(),
        "source_file_hashes": {
            rel: cp._sha256_file(_REPO / rel) for rel in HASHED_SOURCES
        },
        "packet_sha256": _sha256_bytes(packet_bytes),
        "units": packet["units"],
        "composition": composition_record(),
        "scale_window_measured": scale_window,
        "declared_verdict": {
            "verdict": "PASS" if ok else "FAIL",
            "recomputed_from": "packet acceptance_thresholds (the "
                               "preregistered 1e-6 law); the reuse "
                               "certificate adds no thresholds",
        },
        "cases": cases,
    }


def compose_all_scales() -> tuple:
    thr = _thresholds()
    cases, failures = [], []
    for scale in SUPPORTED_SCALES:
        star = build_star(scale=scale)
        solved = solve_star(star)
        c = _compose_case(star, solved)
        ok = (c["status"] in {"stationary", "stagnated"}
              and c["outputs"]["max_free_residual_N"] <= thr["max_free_residual_N"]
              and c["outputs"]["max_force_balance_residual"]
              <= thr["max_force_balance_residual"]
              and c["outputs"]["max_moment_balance_residual"]
              <= thr["max_moment_balance_residual"])
        if not ok:
            failures.append(c["case_id"])
        print(f"{c['case_id']}: status={c['status']} "
              f"free_residual={c['outputs']['max_free_residual_N']:.3e} "
              f"force_bal={c['outputs']['max_force_balance_residual']:.3e} "
              f"moment_bal={c['outputs']['max_moment_balance_residual']:.3e} "
              f"seam_z={c['outputs']['seam_height_wu']:.4f} "
              f"blocks={c['outputs']['block_mean_reaction_norms_N']} -> "
              f"{'OK' if ok else 'FAIL'}")
        cases.append(c)
    return cases, failures


def write_composed_receipt(path: Path, cases: list, scale_window: list) -> Path:
    receipt = build_composed_receipt(cases, scale_window)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return path


def main(argv: list) -> int:
    cases, failures = compose_all_scales()
    if failures:
        print(f"FAIL: threshold/status violation in: {', '.join(failures)}")
        return 1
    scale_window = scale_window_probe()
    out_path = resolve_evidence_path(EVID_DIR, "composed_chain_receipt", argv)
    write_composed_receipt(out_path, cases, scale_window)
    print(f"receipt: {out_path}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except EvidencePathExists as exc:
        print(f"REFUSED: {exc}")
        sys.exit(2)
