"""C2 step 2a — SOURCE hand skeleton geometry from the 27 authored geom positions.

Read-only. Parses baseline_snapshot/source_xml/chimanoid.xml; measures in the
hand_r body frame (quat identity, so authored geom pos IS body-frame):
  - per-geom |p| (wrist-origin distance), distalmost geom
  - hand length (wrist -> distalmost phalanx geom anchor)
  - metacarpal spread / palm width candidates (the H-ASP denominators)
  - thumb vs finger axis divergence
  - palm-plane fit quality of the 27 points (SVD best-fit plane residuals)
  - per-digit ray lengths along the mc->prox->mid->dist chain
  - source forearm: elbow->hand origin (straight line) and chain-sum
  - the 5 hand sites: |p|, coplanarity
Writes receipt to audits/C2_hand_evidence/receipts/source_hand_measures.txt.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from itertools import combinations

import numpy as np

XML = Path(r"E:\PythonChimera\forearm_package\baseline_snapshot\source_xml\chimanoid.xml")
OUT = Path(r"E:\PythonChimera\forearm_package\audits\C2_hand_evidence\receipts\source_hand_measures.txt")

L: list[str] = []


def say(s: str = "") -> None:
    L.append(s)
    print(s)


def vec(s):
    if s is None:
        return np.zeros(3)  # MJ default: missing pos = origin
    return np.array([float(t) for t in s.split()])


def best_fit_plane(P: np.ndarray):
    """Return (normal, centroid, signed residuals)."""
    c = P.mean(axis=0)
    Q = P - c
    _, _, vt = np.linalg.svd(Q, full_matrices=False)
    n = vt[-1]
    res = Q @ n
    return n, c, res


tree = ET.parse(XML)
root = tree.getroot()

hand = None
for b in root.iter("body"):
    if b.get("name") == "hand_r":
        hand = b
        break
assert hand is not None

# parent bodies for chain distances
pos_of = {}
parent_of = {}
for b in root.iter("body"):
    nm = b.get("name")
    pos_of[nm] = vec(b.get("pos"))
    parent_of[nm] = None
# second pass to record parenting via containment
def walk(e, parent_name):
    for c in e.findall("body"):
        parent_of[c.get("name")] = parent_name
        walk(c, c.get("name"))
world = root.find("worldbody")
walk(world, None)

CARPALS = ["pisiform", "lunate", "scaphoid", "triquetrum", "hamate", "capitate", "trapezoid", "trapezium"]
MCS = ["1mc", "2mc", "3mc", "4mc", "5mc"]
PHALANGES = ["thumbprox", "thumbdist",
             "2proxph", "2midph", "2distph",
             "3proxph", "3midph", "3distph",
             "4proxph", "4midph", "4distph",
             "5proxph", "5midph", "5distph"]

geoms = {}
n_capsule = 0
for g in hand.findall("geom"):
    nm = g.get("name")
    if g.get("type") == "capsule":
        n_capsule += 1
        continue
    geoms[nm] = vec(g.get("pos"))

say("=== C2 SOURCE HAND MEASURES (hand_r, body frame; geom pos anchors, identity quat) ===")
say(f"mesh geoms parsed: {len(geoms)} (capsules skipped: {n_capsule})")
assert len(geoms) == 27, "expected 27 skeleton mesh geoms"

say("")
say("--- per-geom |p| from wrist origin (mm) ---")
allp = np.array([geoms[n] for n in CARPALS + MCS + PHALANGES])
order = sorted(geoms, key=lambda n: -np.linalg.norm(geoms[n]))
for n in order:
    p = geoms[n]
    say(f"  {n:10s} |p| = {np.linalg.norm(p)*1000:7.2f} mm   pos = {np.round(p, 6)}")

distalmost = order[0]
hand_len = np.linalg.norm(geoms[distalmost])
say("")
say(f"hand length (wrist -> distalmost geom anchor) = {hand_len*1000:.2f} mm  ({distalmost})")

# palmar/dorsal: y is long axis (distal = -y). Confirm distal-most by |p| and by -y extent.
say(f"max -y extent = {-allp[:,1].min()*1000:.2f} mm ({ [n for n in CARPALS+MCS+PHALANGES if geoms[n][1] == allp[:,1].min() ] })")

say("")
say("--- palm width/thickness candidates (the H-ASP denominators) ---")
mc = np.array([geoms[n] for n in MCS])
say(f"5mc x-range: [{mc[:,0].min()*1000:.2f}, {mc[:,0].max()*1000:.2f}] mm  extent {((mc[:,0].max()-mc[:,0].min()))*1000:.2f} mm")
say(f"5mc z-range: [{mc[:,1*0].min()*1000:.2f}, {mc[:,2].max()*1000:.2f}] mm  extent {(mc[:,2].max()-mc[:,2].min())*1000:.2f} mm")
say(f"5mc y-range: [{mc[:,1].min()*1000:.2f}, {mc[:,1].max()*1000:.2f}] mm")
# 1mc..5mc max pairwise
dmax = 0; pair = None
for a, b in combinations(MCS, 2):
    d = np.linalg.norm(geoms[a] - geoms[b])
    if d > dmax:
        dmax, pair = d, (a, b)
say(f"max pairwise distance within mc row: {dmax*1000:.2f} mm ({pair[0]}-{pair[1]})")
# x-range including thumb column (1mc..5mc + trapezium + thumbprox)
thumb_col = MCS + ["trapezium", "thumbprox"]
tc = np.array([geoms[n] for n in thumb_col])
say(f"mc+thumb-column x-range: [{tc[:,0].min()*1000:.2f}, {tc[:,0].max()*1000:.2f}] mm  extent {(tc[:,0].max()-tc[:,0].min())*1000:.2f} mm")
allx = allp[:, 0]
say(f"ALL-27 x-range: [{allx.min()*1000:.2f}, {allx.max()*1000:.2f}] mm  extent {(allx.max()-allx.min())*1000:.2f} mm")
allz = allp[:, 2]
say(f"ALL-27 z-range: [{allz.min()*1000:.2f}, {allz.max()*1000:.2f}] mm  extent {(allz.max()-allz.min())*1000:.2f} mm")
ally = allp[:, 1]
say(f"ALL-27 y-range: [{ally.min()*1000:.2f}, {ally.max()*1000:.2f}] mm")

say("")
say("--- thumb vs finger axis divergence ---")
fingers = ["2", "3", "4", "5"]
# finger axis: mean direction from wrist to distal phalanx anchors
fd = np.mean([geoms[f + "distph"] for f in fingers], axis=0)
fd /= np.linalg.norm(fd)
td = geoms["thumbdist"] / np.linalg.norm(geoms["thumbdist"])
ang = np.degrees(np.arccos(np.clip(fd @ td, -1, 1)))
say(f"direction wrist->thumbdist  : {np.round(td,4)}")
say(f"mean direction wrist->2-5distph: {np.round(fd,4)}")
say(f"angle between = {ang:.1f} deg")
# per-digit ray axes prox->dist
say("per-ray prox->dist direction and angle vs 3rd ray:")
r3 = geoms["3distph"] - geoms["3proxph"]; r3 /= np.linalg.norm(r3)
for f in ["thumb", "2", "4", "5"]:
    a_, b_ = ("thumbprox", "thumbdist") if f == "thumb" else (f + "proxph", f + "distph")
    r = geoms[b_] - geoms[a_]
    Lr = np.linalg.norm(r); r /= Lr
    say(f"  ray {f}: axis {np.round(r,4)}  angle vs ray3 = {np.degrees(np.arccos(np.clip(r@r3,-1,1))):.1f} deg  (prox->dist anchor span {Lr*1000:.1f} mm)")

say("")
say("--- palm-plane fit of the 27 points (SVD) ---")
n_, c_, res = best_fit_plane(allp)
say(f"best-fit plane normal = {np.round(n_,4)}")
say(f"RMS residual = {np.sqrt((res**2).mean())*1000:.2f} mm   max |res| = {np.abs(res).max()*1000:.2f} mm")
say(f"residual percentiles |r| mm: 50% {np.percentile(np.abs(res),50)*1000:.2f}, 90% {np.percentile(np.abs(res),90)*1000:.2f}, 100% {np.abs(res).max()*1000:.2f}")
# carpals+mc only (the palm proper)
palmset = CARPALS + MCS
Pp = np.array([geoms[n] for n in palmset])
np_, cp, resp = best_fit_plane(Pp)
say(f"carpals+mc (13 pts) plane: RMS {np.sqrt((resp**2).mean())*1000:.2f} mm, max {np.abs(resp).max()*1000:.2f} mm")
# phalanges only
Php = np.array([geoms[n] for n in PHALANGES])
nh_, ch, resh = best_fit_plane(Php)
say(f"14 phalanges plane: RMS {np.sqrt((resh**2).mean())*1000:.2f} mm, max {np.abs(resh).max()*1000:.2f} mm")
# sites coplanarity (map: 'the 5 hand sites are near-coplanar')
sites = {}
for s in hand.findall("site"):
    sites[s.get("name")] = vec(s.get("pos"))
Ps = np.array([sites[k] for k in sorted(sites)])
ns_, cs, ress = best_fit_plane(Ps)
say(f"5 sites: plane RMS {np.sqrt((ress**2).mean())*1000:.2f} mm, max {np.abs(ress).max()*1000:.2f} mm; |p| mm: "
    + ", ".join(f"{k}={np.linalg.norm(v)*1000:.1f}" for k, v in sorted(sites.items(), key=lambda kv: np.linalg.norm(kv[1]))))

say("")
say("--- per-digit ray lengths (sum of consecutive anchor distances) ---")
for f, chain in [("thumb", ["1mc", "thumbprox", "thumbdist"]),
                 ("2", ["2mc", "2proxph", "2midph", "2distph"]),
                 ("3", ["3mc", "3proxph", "3midph", "3distph"]),
                 ("4", ["4mc", "4proxph", "4midph", "4distph"]),
                 ("5", ["5mc", "5proxph", "5midph", "5distph"])]:
    pts = [geoms[k] for k in chain]
    seg = [np.linalg.norm(pts[i + 1] - pts[i]) for i in range(len(pts) - 1)]
    say(f"  ray {f}: segments mm {[round(s*1000,1) for s in seg]}  total {sum(seg)*1000:.1f} mm")

say("")
say("--- source forearm / chain (right) ---")
p_ulna = pos_of["ulna"]; p_rad = pos_of["radius"]; p_hand = pos_of["hand_r"]
say(f"ulna pos rel humerus  = {p_ulna}  |.| = {np.linalg.norm(p_ulna):.5f} m (shoulder->elbow)")
say(f"radius pos rel ulna   = {p_rad}  |.| = {np.linalg.norm(p_rad):.5f} m (ulna->radius)")
say(f"hand pos rel radius   = {p_hand}  |.| = {np.linalg.norm(p_hand):.5f} m (radius->hand)")
elbow_to_hand = np.linalg.norm(p_rad + p_hand)
say(f"elbow->hand origin straight-line |radius_pos + hand_pos| = {elbow_to_hand:.5f} m")
say(f"chain-sum ulna->radius + radius->hand = {np.linalg.norm(p_rad)+np.linalg.norm(p_hand):.5f} m")
say("")
say("--- ratios ---")
say(f"source hand:forearm (hand_len/elbow->hand straight) = {hand_len/elbow_to_hand:.4f}")
say(f"source hand:forearm (hand_len/chain-sum)            = {hand_len/(np.linalg.norm(p_rad)+np.linalg.norm(p_hand)):.4f}")
say(f"source hand:forearm (hand_len/radius->hand only)    = {hand_len/np.linalg.norm(p_hand):.4f}")

say("")
say("--- inertial (authored) ---")
inert = hand.find("inertial")
say(f"hand_r inertial: pos {inert.get('pos')} mass {inert.get('mass')} kg fullinertia {inert.get('fullinertia')}")

OUT.write_text("\n".join(L), encoding="utf-8")
print(f"\n[receipt written: {OUT}]")
