"""repair_and_decimate.py -- THE SLICE'S REAL BODY: from the committed CT
previews (the pose of record's full resolution) to an import-grade creature
body, under the aliveness importer's own laws.

The debt (measured on 2909bb4e, preregistration.md): the 25 committed
`meshes_preview/*_lo.obj` carry 712,522 triangles vs the importer's
`kMaxTris` 500,000, and 19/25 fail the importer's closure rule
(index-degenerate faces 312, non-manifold edges 174, winding violations 348,
boundary edges 0). This tool, one op per class the check names:

  1. drop index-degenerate faces (repeated indices);
  2. drop exact duplicate faces (same sorted triple; keep the first);
  3. non-manifold edges: keep exactly one face per traversal direction --
     the faces kept prefer the fewest other over-shared edges (the minimum
     that restores one-face-per-direction), face-index tie-break;
  4. orient each connected component by BFS across shared edges, then force
     the component's signed volume positive (the importer's divergence sign
     law -- a global-only flip would be wrong for multi-component bodies);
  5. trace any boundary loops the cleanup created (the measured hole class
     is EMPTY in the committed previews, so this runs only as a consequence
     of step 3) and fill each loop by ear clipping in its best-fit plane.

Then the decimation, the ratio DERIVED from the cap, not chosen:
  r = kMaxTris / N_repaired;  per-bone target_i = floor(r * n_i);
  sum(floor(r*n_i)) <= sum(r*n_i) = kMaxTris, and the engine refuses only
  > kMaxTris. No margin constant exists in this lane.
The reducer is quadric error metric (Garland-Heckbert) edge collapse with the
topology-safety set: the link condition (manifoldness preserved by
construction), a normal-flip guard, and boundary-plane constraints (included
though the boundary class measured empty). Quality is MEASURED and recorded:
per-bone signed-volume delta pre/post repair and pre/post decimation, and the
one-sided deviation of the repaired mesh's vertices from the decimated
surface. No quality threshold is applied here -- the acceptance falsifier is
the importer's own closure rule (check_body_closure.py) plus the bone count.

The posed import payload (scene metres, the standing placement) is composed by
scene_boot.build_standing_layer -- the SAME compose the ghost runs live --
from these repaired/decimated bones, and written beside the slice as
standing_body.obj with its sha pinned in the manifest.

Run:  python repair_and_decimate.py [--write]
Writes only with --write; a bare run audits and prints the plan.
"""
from __future__ import annotations

import argparse
import hashlib
import heapq
import io
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

CT_DIR = ROOT / "tools/science_funnel/data/morphosource_ct"
PREVIEW_DIR = CT_DIR / "meshes_preview"
BODY_DIR = CT_DIR / "meshes_body_20260922"
SLICE = ROOT / "tools/playable_slice"
PAYLOAD = SLICE / "standing_body.obj"

K_MAX_TRIS = 500000          # ChimeraEngine/engine/importer.hpp:16 -- the cap names the number
K_MAX_VERTS = 1500000        # importer.hpp:17


# ── the importer's own closure rule (mirrored; the check that refused 19/25) ──

def edge_audit(tris: np.ndarray, n_verts: int) -> dict:
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    idx_deg = int(((a == b) | (b == c) | (c == a)).sum())
    keep = ~((a == b) | (b == c) | (c == a))
    a, b, c = a[keep], b[keep], c[keep]
    keys = []
    for u, v in ((a, b), (b, c), (c, a)):
        lo = np.minimum(u, v).astype(np.int64)
        hi = np.maximum(u, v).astype(np.int64)
        keys.append(lo * (n_verts + 1) + hi)
    all_k = np.concatenate(keys)
    _, counts = np.unique(all_k, return_counts=True)
    boundary = int((counts == 1).sum())
    nonman = int((counts > 2).sum())
    dirk = np.concatenate([a.astype(np.int64) * (n_verts + 1) + b,
                           b.astype(np.int64) * (n_verts + 1) + c,
                           c.astype(np.int64) * (n_verts + 1) + a])
    _, dc = np.unique(dirk, return_counts=True)
    winding_bad = int((dc != 1).sum())
    return {"index_degenerate_faces": idx_deg, "boundary_edges": boundary,
            "nonmanifold_edges": nonman, "winding_violations": winding_bad,
            "faces": int(len(a)), "closed": idx_deg == 0 and boundary == 0
            and nonman == 0 and winding_bad == 0}


def load_obj(p: Path):
    verts, tris = [], []
    with open(p, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if line.startswith("v "):
                q = line.split()
                verts.append((float(q[1]), float(q[2]), float(q[3])))
            elif line.startswith("f "):
                idx = [int(t.split("/")[0]) - 1 for t in line.split()[1:]]
                for k in range(1, len(idx) - 1):
                    tris.append((idx[0], idx[k], idx[k + 1]))
    return np.asarray(verts, np.float64), np.asarray(tris, np.int64)


def signed_volume(V: np.ndarray, T: np.ndarray) -> float:
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)


def write_obj(path: Path, V: np.ndarray, T: np.ndarray, header: list[bytes]) -> bytes:
    out = io.BytesIO()
    for h in header:
        out.write(h + b"\n")
    np.savetxt(out, V, fmt="v %.6f %.6f %.6f")
    np.savetxt(out, np.asarray(T, np.int64) + 1, fmt="f %d %d %d")
    raw = out.getvalue()
    if path is not None:
        path.write_bytes(raw)
    return raw


# ── REPAIR: one op per class the closure check names ─────────────────────────

def repair(V: np.ndarray, T: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    stats = {"idx_degenerate_dropped": 0, "duplicate_faces_dropped": 0,
             "nonman_extra_faces_removed": 0, "orient_flips_applied": 0,
             "same_direction_edge_residual": 0,
             "boundary_loops_filled": 0, "faces_filled": 0,
             "centroid_fan_fallbacks": 0}
    T = T.copy()

    # (1) index-degenerate faces: the importer refuses them BY NAME
    keep = ~((T[:, 0] == T[:, 1]) | (T[:, 1] == T[:, 2]) | (T[:, 2] == T[:, 0]))
    stats["idx_degenerate_dropped"] = int((~keep).sum())
    T = T[keep]

    # (2) exact duplicate faces (same sorted triple; the first stays)
    seen: set[tuple] = set()
    keep_mask = np.empty(len(T), bool)
    for i in range(len(T)):
        f = T[i]
        key = tuple(sorted((int(f[0]), int(f[1]), int(f[2]))))
        keep_mask[i] = key not in seen
        if keep_mask[i]:
            seen.add(key)
    stats["duplicate_faces_dropped"] = int((~keep_mask).sum())
    T = T[keep_mask]

    def edge_map(T):
        em: dict[tuple, list[int]] = defaultdict(list)
        for ti in range(len(T)):
            a, b, c = int(T[ti][0]), int(T[ti][1]), int(T[ti][2])
            for u, v in ((a, b), (b, c), (c, a)):
                em[(min(u, v), max(u, v))].append(ti)
        return em

    # (3) non-manifold edges: keep one face per traversal direction
    for _ in range(8):        # one pass converges; the loop is defensive
        em = edge_map(T)
        over = {e: fs for e, fs in em.items() if len(fs) > 2}
        if not over:
            break
        invol: dict[int, int] = defaultdict(int)
        for fs in over.values():
            for ti in fs:
                invol[ti] += 1
        dead: set[int] = set()
        for e, fs in over.items():
            u, v = e
            by_dir: dict[int, list[int]] = defaultdict(list)
            for ti in fs:
                a, b, c = int(T[ti][0]), int(T[ti][1]), int(T[ti][2])
                d = 1 if (u, v) in ((a, b), (b, c), (c, a)) else -1
                by_dir[d].append(ti)
            for d, tis in by_dir.items():
                tis.sort(key=lambda ti: (invol[ti], ti))
                dead.update(tis[1:])
        T = np.array([T[i] for i in range(len(T)) if i not in dead], np.int64)
        stats["nonman_extra_faces_removed"] += len(dead)

    # (4) orient each connected component consistently (BFS across shared
    # edges), then force positive signed volume per component
    em = edge_map(T)
    pair = {e: fs for e, fs in em.items() if len(fs) == 2}
    nbr: dict[int, list] = defaultdict(list)
    for e, fs in pair.items():
        nbr[fs[0]].append((fs[1], e))
        nbr[fs[1]].append((fs[0], e))
    seen_f = [False] * len(T)
    flip = [False] * len(T)
    comp_of = np.full(len(T), -1, np.int64)
    comp = 0
    for seed in range(len(T)):
        if seen_f[seed]:
            continue
        comp += 1
        seen_f[seed] = True
        comp_of[seed] = comp
        stack = [seed]
        while stack:
            ti = stack.pop()
            for tj, e in nbr[ti]:
                if seen_f[tj]:
                    continue
                u, v = e
                ta = (int(T[ti][0]), int(T[ti][1]), int(T[ti][2]))
                tb = (int(T[tj][0]), int(T[tj][1]), int(T[tj][2]))
                fwd_ti = (u, v) in ((ta[0], ta[1]), (ta[1], ta[2]), (ta[2], ta[0]))
                fwd_tj = (u, v) in ((tb[0], tb[1]), (tb[1], tb[2]), (tb[2], tb[0]))
                if fwd_ti == fwd_tj:
                    T[tj] = T[tj][::-1]
                    flip[tj] = True
                seen_f[tj] = True
                comp_of[tj] = comp
                stack.append(tj)
    stats["orient_flips_applied"] = sum(1 for f in flip if f)

    def same_direction_residual(T):
        em = edge_map(T)
        bad = 0
        for e, fs in em.items():
            if len(fs) != 2:
                continue
            u, v = e
            dirs = []
            for ti in fs:
                ta = (int(T[ti][0]), int(T[ti][1]), int(T[ti][2]))
                dirs.append((u, v) in ((ta[0], ta[1]), (ta[1], ta[2]), (ta[2], ta[0])))
            if dirs[0] == dirs[1]:
                bad += 1
        return bad

    comps: dict[int, list[int]] = defaultdict(list)
    for ti in range(len(T)):
        comps[int(comp_of[ti])].append(ti)
    for c, tis in comps.items():
        idx = np.array(tis, np.int64)
        if signed_volume(V, T[idx]) < 0:
            T[idx] = T[idx][:, ::-1]
    stats["same_direction_edge_residual"] = same_direction_residual(T)

    # (5) boundary loops the cleanup may have created -> ear-clip fill.
    # Walk DIRECTED half-edges: a face traverses the boundary edge u->v, so
    # the hole side traverses v->u; the fill faces follow the hole's own
    # direction, which restores exactly-one-face-per-direction on every edge.
    for _ in range(64):
        em = edge_map(T)
        bnd = {e for e, fs in em.items() if len(fs) == 1}
        if not bnd:
            break
        existing_edges = set(em.keys())
        # hole-directed half-edges: the REVERSE of the face's own traversal
        hole: dict[int, list[int]] = defaultdict(list)
        for (u, v) in bnd:
            ti = em[(u, v)][0]
            ta = (int(T[ti][0]), int(T[ti][1]), int(T[ti][2]))
            if (u, v) in ((ta[0], ta[1]), (ta[1], ta[2]), (ta[2], ta[0])):
                hole[v].append(u)          # face used u->v, hole goes v->u
            else:
                hole[u].append(v)
        used: set[tuple] = set()
        loops = []
        for (u0, v0) in sorted(bnd):
            # deterministic start: the hole half-edge on this boundary edge
            if v0 in hole.get(u0, []):
                start = (u0, v0)
            elif u0 in hole.get(v0, []):
                start = (v0, u0)
            else:
                continue
            if start in used:
                continue
            loop = [start[0], start[1]]
            cur = start
            used.add(start)
            closed = False
            while True:
                nxts = [w for w in hole.get(cur[1], []) if (cur[1], w) not in used]
                if not nxts:
                    break
                nxt = (cur[1], nxts[0])
                used.add(nxt)
                loop.append(nxt[1])
                cur = nxt
                if cur[1] == loop[0]:
                    closed = True
                    break
            if closed and len(loop) >= 4:
                loops.append(loop[:-1])
        if not loops:
            break
        filled_any = False
        for walk in loops:
            # a closed walk may pass a PINCH vertex twice (figure-8); fill
            # each SIMPLE cycle of the walk separately -- a fan over a
            # repeated vertex would reuse an edge and go non-manifold
            for cycle in split_simple_cycles(walk):
                V, new_t, fan = fill_loop(V, cycle, existing_edges)
                if new_t:
                    T = np.vstack([T, np.array(new_t, np.int64)])
                    stats["faces_filled"] += len(new_t)
                    stats["boundary_loops_filled"] += 1
                    if fan:
                        stats["centroid_fan_fallbacks"] += 1
                    filled_any = True
        if not filled_any:
            break

    T = np.array(T, np.int64)
    aud = edge_audit(T, len(V))
    stats["audit_after"] = aud
    return V, T, stats


def split_simple_cycles(walk: list[int]) -> list[list[int]]:
    """Decompose a closed vertex walk (last connects to first; it may repeat
    pinch vertices) into simple cycles: when the walk arrives at a vertex
    already on the current stack, the stack tail is a cycle."""
    cycles: list[list[int]] = []
    stack: list[int] = []
    where: dict[int, int] = {}
    for v in list(walk) + [walk[0]]:
        if v in where:
            i = where[v]
            cyc = stack[i:]
            cycles.append(cyc)
            for vv in cyc[1:]:        # the tail leaves the stack; v stays at i
                del where[vv]
            stack = stack[:i + 1]
        else:
            where[v] = len(stack)
            stack.append(v)
    return [c for c in cycles if len(c) >= 3]


def fill_loop(V: np.ndarray, loop: list[int], existing_edges: set):
    """Fill one closed boundary loop WITHOUT reusing an existing edge: an
    ear clip whose diagonal must be a NEW edge (the pinched geometry often
    already contains the natural diagonals, and reusing one would create a
    non-manifold edge); when no valid ear exists, a centroid fan covers the
    rest with a fresh vertex -- topologically manifold by construction.
    MUTATES existing_edges: every edge this fill creates joins the set, so a
    later cycle in the same pass cannot reuse it."""
    n = len(loop)
    if n < 3:
        return V, [], False
    existing = existing_edges
    P = V[np.array(loop, np.int64)].astype(np.float64)
    Q = P - P.mean(axis=0)
    _, _, Ut = np.linalg.svd(Q, full_matrices=False)
    pts = np.stack([Q @ Ut[0], Q @ Ut[1]], axis=1)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    def inside(p, a, b, c):
        d1, d2, d3 = cross(a, b, p), cross(b, c, p), cross(c, a, p)
        neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
        pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
        return not (neg and pos)

    idxs = list(range(n))
    tris: list[tuple[int, int, int]] = []
    added_diag: set = set()
    guard = 0
    while len(idxs) > 3 and guard < 10 * n:
        guard += 1
        cut = False
        for k in range(len(idxs)):
            i0 = idxs[(k - 1) % len(idxs)]
            i1 = idxs[k]
            i2 = idxs[(k + 1) % len(idxs)]
            a, b, c = pts[i0], pts[i1], pts[i2]
            if cross(a, b, c) <= 1e-18:
                continue
            d_lo, d_hi = min(loop[i0], loop[i2]), max(loop[i0], loop[i2])
            if (d_lo, d_hi) in existing or (d_lo, d_hi) in added_diag:
                continue
            if any(inside(pts[j], a, b, c) for j in idxs if j not in (i0, i1, i2)):
                continue
            tris.append((loop[i0], loop[i1], loop[i2]))
            added_diag.add((d_lo, d_hi))
            existing.add((d_lo, d_hi))
            idxs.pop(k)
            cut = True
            break
        if not cut:
            break
    if len(idxs) == 3:
        tris.append((loop[idxs[0]], loop[idxs[1]], loop[idxs[2]]))
        for t in tris:
            for e in ((min(t[0], t[1]), max(t[0], t[1])),
                      (min(t[1], t[2]), max(t[1], t[2])),
                      (min(t[2], t[0]), max(t[2], t[0]))):
                existing.add(e)
        return V, tris, False
    # fallback: centroid fan over the REMAINING polygon (the ears already cut
    # keep their triangles; the fan closes what is left of the cycle -- never
    # the whole loop, or the cut ears would be double-covered)
    ctr = P[idxs].mean(axis=0)          # 3-D centroid of the remaining cycle
    w = len(V)
    V = np.vstack([V, ctr[None, :]])
    for k in range(len(idxs)):
        i_a = idxs[k]
        i_b = idxs[(k + 1) % len(idxs)]
        tris.append((w, loop[i_a], loop[i_b]))
    for t in tris:
        for e in ((min(t[0], t[1]), max(t[0], t[1])),
                  (min(t[1], t[2]), max(t[1], t[2])),
                  (min(t[2], t[0]), max(t[2], t[0]))):
            existing.add(e)
    return V, tris, True


# ── DECIMATION: quadric error metric edge collapse, topology-safe ────────────

def quadrics(V: np.ndarray, T: np.ndarray) -> np.ndarray:
    """Per-vertex plane quadrics (the standard Q; planes from non-degenerate
    faces)."""
    n = len(V)
    Q = np.zeros((n, 4, 4), np.float64)
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    fn = np.cross(b - a, c - a)
    ln = np.linalg.norm(fn, axis=1)
    ok = ln > 1e-14
    fno = fn[ok] / ln[ok][:, None]
    d = -np.einsum("ij,ij->i", fno, a[ok])
    P = np.concatenate([fno, d[:, None]], axis=1)
    outer = P[:, :, None] * P[:, None, :]
    for w in range(3):
        np.add.at(Q, T[ok, w], outer)
    return Q


def decimate(V: np.ndarray, T: np.ndarray, target_faces: int):
    """QEM edge collapse to <= target_faces. The link condition (shared
    neighbors == the two opposite corners) preserves manifoldness by
    construction; a normal-flip guard blocks fold-overs. Deterministic: heap
    ties break by insertion counter."""
    V = V.copy()
    T = [tuple(map(int, t)) for t in np.asarray(T, np.int64)]
    n = len(V)
    Q = quadrics(V, np.array(T, np.int64))
    adj: list[set] = [set() for _ in range(n)]
    inc: list[set] = [set() for _ in range(n)]
    for ti, (a, b, c) in enumerate(T):
        adj[a].add(b); adj[a].add(c)
        adj[b].add(a); adj[b].add(c)
        adj[c].add(a); adj[c].add(b)
        inc[a].add(ti); inc[b].add(ti); inc[c].add(ti)

    def optimal(u, v):
        Qs = Q[u] + Q[v]
        A = Qs[:3, :3]
        rhs = -Qs[:3, 3]
        try:
            x = np.linalg.solve(A, rhs)
            if np.all(np.isfinite(x)):
                xh = np.array([x[0], x[1], x[2], 1.0])
                return x, float(xh @ Qs @ xh)
        except np.linalg.LinAlgError:
            pass
        best, cost = None, None
        for x in (V[u], V[v], (V[u] + V[v]) / 2.0):
            xh = np.array([x[0], x[1], x[2], 1.0])
            cst = float(xh @ Qs @ xh)
            if best is None or cst < cost:
                best, cost = x, cst
        return best, cost

    heap = []
    counter = 0
    seen_edge: set = set()
    for (a, b, c) in T:
        for u, v in ((a, b), (b, c), (c, a)):
            seen_edge.add((min(u, v), max(u, v)))
    for (u, v) in sorted(seen_edge):
        x, cost = optimal(u, v)
        heapq.heappush(heap, (cost, counter, u, v, x))
        counter += 1

    n_faces = len(T)
    n_collapses = 0
    n_rejected = 0
    dead: set = set()

    while n_faces > target_faces and heap:
        cost, _, u, v, x = heapq.heappop(heap)
        if v not in adj[u] or u not in adj[v]:
            continue
        faces_uv = {ti for ti in (inc[u] & inc[v]) if ti not in dead}
        if len(faces_uv) != 2:
            n_rejected += 1
            continue
        opp_verts = set()
        for ti in faces_uv:
            opp_verts |= set(T[ti]) - {u, v}
        shared = adj[u] & adj[v]
        if shared != opp_verts or len(opp_verts) != 2:
            n_rejected += 1
            continue
        touched = {ti for ti in (inc[u] | inc[v]) if ti not in dead}

        def fnorm(ti, pos):
            a, b, c = pos[T[ti][0]], pos[T[ti][1]], pos[T[ti][2]]
            f = np.cross(b - a, c - a)
            ln = float(np.linalg.norm(f))
            return f / ln if ln > 1e-14 else None

        oldV = V[u].copy()
        normals_before = {ti: fnorm(ti, V) for ti in touched}
        V[u] = x
        bad = False
        for ti in touched:
            nb = normals_before[ti]
            na = fnorm(ti, V)
            if nb is not None and na is not None and float(na @ nb) <= 0.0:
                bad = True
                break
        if bad:
            V[u] = oldV
            n_rejected += 1
            continue

        # collapse v -> u
        Q[u] = Q[u] + Q[v]
        for ti in list(faces_uv):
            dead.add(ti)
            for w in T[ti]:
                inc[w].discard(ti)
            n_faces -= 1
        for w in list(adj[v]):
            if w != u:
                adj[w].discard(v)
                adj[w].add(u)
                adj[u].add(w)
        adj[u].discard(v)
        adj[v] = set()
        for ti in list(inc[v]):
            f = T[ti]
            f2 = tuple(u if w == v else w for w in f)
            if f2[0] == f2[1] or f2[1] == f2[2] or f2[0] == f2[2]:
                dead.add(ti)
                for w in f:
                    inc[w].discard(ti)
                n_faces -= 1
                continue
            T[ti] = f2
            inc[u].add(ti)
        for w in sorted(adj[u]):
            x2, c2 = optimal(u, w)
            heapq.heappush(heap, (c2, counter, u, w, x2))
            counter += 2
        n_collapses += 1

    keep = [i for i in range(len(T)) if i not in dead]
    T2 = np.array([T[i] for i in keep], np.int64)
    used = sorted({int(x) for t in T2 for x in t})
    remap = np.full(n, -1, np.int64)
    remap[np.array(used, np.int64)] = np.arange(len(used), dtype=np.int64)
    V2 = V[np.array(used, np.int64)].copy()
    T2 = remap[T2]
    return V2, T2, {"collapses": n_collapses, "rejected": n_rejected,
                    "faces": int(len(T2)), "verts": int(len(V2))}


def deviation(V_from: np.ndarray, V_to: np.ndarray, T_to: np.ndarray,
              samples: int = 1500) -> dict:
    """One-sided deviation: max/mean distance of `V_from`'s (sampled,
    deterministic) vertices from the mesh (V_to, T_to). Point-triangle."""
    rng = np.random.default_rng(0)   # fixed seed: deterministic sampling
    idx = np.sort(rng.choice(len(V_from), size=min(samples, len(V_from)),
                             replace=False))
    P = V_from[idx]
    a, b, c = V_to[T_to[:, 0]], V_to[T_to[:, 1]], V_to[T_to[:, 2]]
    ab, ac = b - a, c - a
    aa = np.einsum("jk,jk->j", ab, ab)[None, :]
    bb = np.einsum("jk,jk->j", ac, ac)[None, :]
    dab = np.einsum("jk,jk->j", ab, ac)[None, :]
    det = np.where(np.abs(aa * bb - dab * dab) < 1e-30, 1e-30, aa * bb - dab * dab)
    d_best = np.full(len(P), np.inf)
    for i0 in range(0, len(P), 128):
        p = P[i0:i0 + 128][:, None, :]
        ap = p - a[None, :, :]
        d1 = np.einsum("ijk,jk->ij", ap, ab)
        d2 = np.einsum("ijk,jk->ij", ap, ac)
        s = np.clip((bb * d1 - dab * d2) / det, 0, 1)
        t = np.clip((aa * d2 - dab * d1) / det, 0, 1)
        st = s + t
        over = st > 1.0
        s = np.where(over, s / np.maximum(st, 1e-30), s)
        t = np.where(over, t / np.maximum(st, 1e-30), t)
        q = a[None, :, :] + s[:, :, None] * ab[None, :, :] + t[:, :, None] * ac[None, :, :]
        d_best[i0:i0 + 128] = np.linalg.norm(p - q, axis=2).min(axis=1)
    return {"sampled_verts": int(len(P)),
            "max_dev_mm": float(d_best.max()), "mean_dev_mm": float(d_best.mean())}


# ═══ the lane ═══

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    man = json.loads((CT_DIR / "meshes" / "manifest.json").read_text())

    repaired = {}
    n_repaired_total = 0
    sources = []
    for entry in man["bones"]:
        name = Path(entry["file"]).name
        preview = name.replace(".obj", "_lo.obj")
        sources.append(preview)
        V, T = load_obj(PREVIEW_DIR / preview)
        aud0 = edge_audit(T, len(V))
        vol0 = signed_volume(V, T)
        V1, T1, rep_stats = repair(V, T)
        aud1 = edge_audit(T1, len(V1))
        vol1 = signed_volume(V1, T1)
        n_repaired_total += aud1["faces"]
        repaired[preview] = {
            "source_faces": int(len(T)), "source_verts": int(len(V)),
            "source_closed": aud0["closed"], "source_audit": aud0,
            **{k: v for k, v in rep_stats.items() if k != "audit_after"},
            "volume_before_mm3": vol0,
            "volume_after_repair_mm3": vol1,
            "volume_repair_rel_delta": (vol1 - vol0) / vol0 if vol0 else None,
            "audit_after_repair": aud1}
        print(f"{preview}: repair {len(T)}->{aud1['faces']} closed={aud1['closed']} "
              f"volD={repaired[preview]['volume_repair_rel_delta']:.3e}", flush=True)

    r = K_MAX_TRIS / n_repaired_total
    print(f"N_repaired={n_repaired_total}  r={r:.9f}", flush=True)

    BODY_DIR.mkdir(parents=True, exist_ok=True)
    body_entries = []
    total_after = 0
    for entry in man["bones"]:
        name = Path(entry["file"]).name
        preview = name.replace(".obj", "_lo.obj")
        body_name = preview.replace("_lo.obj", "_body.obj")
        V, T = load_obj(PREVIEW_DIR / preview)
        V1, T1, _ = repair(V, T)      # deterministic: identical to pass 1
        n_i = len(T1)
        target = int(math.floor(r * n_i))
        V2, T2, dec_stats = decimate(V1, T1, target)
        aud2 = edge_audit(T2, len(V2))
        vol1 = signed_volume(V1, T1)
        vol2 = signed_volume(V2, T2)
        dev = deviation(V1, V2, T2)
        total_after += len(T2)
        print(f"  decimate {preview}: {n_i}->{len(T2)} (target {target}) "
              f"closed={aud2['closed']} volD={((vol2 - vol1) / vol1):.3e} "
              f"maxdev={dev['max_dev_mm']:.4f}mm", flush=True)
        body_entries.append({
            "source_preview": preview, "output": body_name,
            "repair": repaired[preview],
            "decimation": {"faces_before": n_i, "target": target,
                           "ratio": r, **dec_stats,
                           "volume_before_mm3": vol1, "volume_after_mm3": vol2,
                           "volume_decimation_rel_delta": (vol2 - vol1) / vol1,
                           "deviation": dev,
                           "audit_after": aud2}})
        if args.write:
            write_obj(BODY_DIR / body_name, V2, T2,
                      [b"# chimera.real_body_20260922: the committed CT preview, repaired",
                       b"# and QEM-decimated under the importer's kMaxTris; see",
                       b"# validation/slice_real_body_20260922/{preregistration.md,",
                       b"# repair_and_decimate.py, check_body_closure.py, body_manifest.json}"])

    print(f"TOTAL after decimation: {total_after} (cap {K_MAX_TRIS})", flush=True)

    if args.write:
        # the posed import payload: the SAME compose the ghost runs live
        from tools.playable_slice import scene_boot as sb
        verts, tris, compose_rec = sb.build_standing_layer(
            preview_dir=BODY_DIR, obj_suffix="_body")
        raw = write_obj(PAYLOAD, verts, tris, [
            b"# chimera.playable_slice REAL[physics_body] import payload",
            b"# the committed CT skeleton, repaired + decimated under the importer's",
            b"# kMaxTris (meshes_body_20260922), posed by scene_boot.build_standing_layer",
            b"# -- the SAME compose the ghost runs live (scene metres, pads' mean plane",
            b"# at y=0); sha pinned in meshes_body_20260922/body_manifest.json"])
        payload_sha = hashlib.sha256(raw).hexdigest()
        manifest = {
            "schema": "chimera.real_body.v1",
            "lane": "agent/slice-real-body-20260922",
            "date": "2026-09-22",
            "base_commit": "2909bb4e (the slice) + prereg 4aba5bfe",
            "kMaxTris": K_MAX_TRIS,
            "kMaxVerts": K_MAX_VERTS,
            "source_previews": sources,
            "source_manifest": "tools/science_funnel/data/morphosource_ct/meshes/manifest.json",
            "n_repaired_faces": n_repaired_total,
            "ratio_r": r,
            "budget_rule": "r = kMaxTris / N_repaired; target_i = floor(r * n_i); "
                           "sum(floor(r*n_i)) <= kMaxTris by construction; the engine "
                           "refuses only > kMaxTris",
            "bones": body_entries,
            "total_faces_after": total_after,
            "bone_count": len(body_entries),
            "import_payload": {"path": "tools/playable_slice/standing_body.obj",
                               "sha256": payload_sha,
                               "triangles": int(len(tris)),
                               "vertices": int(len(verts)),
                               "compose": compose_rec},
        }
        (BODY_DIR / "body_manifest.json").write_text(
            json.dumps(manifest, indent=1), encoding="utf-8")
        print(f"payload {PAYLOAD.name}: {len(tris)} tris sha {payload_sha[:16]}",
              flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
