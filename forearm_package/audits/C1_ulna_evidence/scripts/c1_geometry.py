"""C1 geometry: verbatim ulna endpoints, axis direction, sites in the elbow->wrist frame.

Reads ONLY:
  - baseline_snapshot/source_xml/chimanoid.xml   (stdlib ElementTree)
  - baseline_snapshot/runs/actual_monkey_fit.json (target anchors + packet records)
Writes NOTHING outside audits/C1_ulna_evidence/. PYTHONDONTWRITEBYTECODE=1.

Geometry only: no fitting search, no moment arms, no utility numbers.
"""
import json
import xml.etree.ElementTree as ET
from math import sqrt

import numpy as np

BASE = r"E:/PythonChimera/forearm_package/baseline_snapshot"
OUT = []


def emit(*a):
    line = " ".join(str(x) for x in a)
    OUT.append(line)
    print(line)


# ---------------------------------------------------------------- XML intake
tree = ET.parse(f"{BASE}/source_xml/chimanoid.xml")
root = tree.getroot()
world = root.find("worldbody")


def find_body(elem, name):
    for b in elem.iter("body"):
        if b.get("name") == name:
            return b
    return None


def body_chain(elem, names):
    """Return {name: (pos_str, quat_str, parent, [direct site (name,pos_str)],
    [direct joint (name,type,pos,axis,range)])} with VERBATIM strings."""
    out = {}
    for nm in names:
        b = find_body(elem, nm)
        assert b is not None, nm
        sites = [(s.get("name"), s.get("pos")) for s in b.findall("site")]
        joints = [
            (j.get("name"), j.get("type"), j.get("pos"), j.get("axis"), j.get("range"))
            for j in b.findall("joint")
        ]
        out[nm] = {
            "pos": b.get("pos"),
            "quat": b.get("quat"),
            "sites": sites,
            "joints": joints,
        }
    return out


chain = body_chain(world, ["humerus", "ulna", "radius", "hand_r"])

emit("=" * 78)
emit("SECTION 1 -- VERBATIM SOURCE GEOMETRY (chimanoid.xml, sha 675e00d0...)")
emit("=" * 78)
for nm in ["humerus", "ulna", "radius", "hand_r"]:
    c = chain[nm]
    emit(f"body {nm:8s} pos = \"{c['pos']}\"  quat = \"{c['quat']}\"")
    assert c["quat"] in (None, "1.0 0.0 0.0 0.0", "1 0 0 0"), "quat not identity!"
emit("all four quats identity (bodies axis-aligned; DERIVATION sec.2 convention confirmed)")

pos = {nm: np.array([float(v) for v in chain[nm]["pos"].split()]) for nm in chain}
O_hum, O_uln, O_rad, O_hnd = pos["humerus"], pos["ulna"], pos["radius"], pos["hand_r"]
emit("")
emit("offsets (local pos, m):")
emit(f"  humerus -> ulna    (elbow offset from shoulder)  = {O_uln}  |.| = {np.linalg.norm(O_uln):.9f}")
emit(f"  ulna -> radius     (THE 2.31 cm AXIS)            = {O_rad}  |.| = {np.linalg.norm(O_rad):.9f}")
emit(f"  radius -> hand_r   (wrist offset)                = {O_hnd}  |.| = {np.linalg.norm(O_hnd):.9f}")

# world origins (axis-aligned => additive)
W_hum = O_hum
W_uln = W_hum + O_uln
W_rad = W_uln + O_rad
W_hnd = W_rad + O_hnd
emit("")
emit("accumulated world origins (m):")
for nm, w in [("humerus", W_hum), ("ulna (elbow)", W_uln), ("radius", W_rad), ("hand_r (wrist)", W_hnd)]:
    emit(f"  {nm:14s} = [{w[0]: .6f}, {w[1]: .6f}, {w[2]: .6f}]")

# joints
emit("")
emit("direct joints (verbatim):")
for nm in ["ulna", "hand_r"]:
    for jn, jt, jp, ja, jr in chain[nm]["joints"]:
        emit(f"  {nm:6s}: {jn:12s} type={jt} pos=\"{jp}\" axis=\"{ja}\" range=\"{jr}\"")

# sites
ulna_sites = chain["ulna"]["sites"]
emit("")
emit(f"ulna direct sites: {len(ulna_sites)}")
for sn, sp in ulna_sites:
    emit(f"  {sn:12s} pos = \"{sp}\"")
assert len(ulna_sites) == 10

# tendon membership from the fit packet
pkt = json.load(open(f"{BASE}/runs/actual_monkey_fit.json"))
names10 = [sn for sn, _ in ulna_sites]
refs = {}
for t in pkt["tendons"]:
    for s in t.get("sites") or []:
        refs.setdefault(s, []).append(t["name"])
emit("")
emit("tendon membership of the 10 sites (from packet tendons[].path):")
for sn in names10:
    emit(f"  {sn:12s} referenced_by={refs.get(sn, [])}")

# ------------------------------------------------------------ source frame
emit("")
emit("=" * 78)
emit("SECTION 2 -- ANATOMICAL FRAME DERIVED FROM THE CHAIN (source world)")
emit("=" * 78)
v_ur = O_rad                       # ulna->radius
v_rh = O_hnd                       # radius->hand
v_ew = W_hnd - W_uln               # elbow->wrist
u_ur = v_ur / np.linalg.norm(v_ur)
u_rh = v_rh / np.linalg.norm(v_rh)
u_ew = v_ew / np.linalg.norm(v_ew)
EW_src = np.linalg.norm(v_ew)
emit(f"elbow->wrist source vector = [{v_ew[0]: .6f}, {v_ew[1]: .6f}, {v_ew[2]: .6f}]")
emit(f"|elbow->wrist| source = {EW_src:.9f} m   (frozen evidence: ~0.306 m)")
emit(f"chain-sum |ulna->radius|+|radius->hand| = {np.linalg.norm(v_ur)+np.linalg.norm(v_rh):.9f} m "
     f"(> |EW| : the two offsets are NOT collinear)")
emit("")
emit("axis direction question:")
ax_along = float(np.dot(v_ur, u_ew))
perp_vec = v_ur - ax_along * u_ew
perp_len = np.linalg.norm(perp_vec)
third_vec = perp_vec - float(np.dot(perp_vec, np.array([0.0, 0.0, 1.0])) - 0) * np.array([0.0, 0, 0])
emit(f"  |ulna->radius|                     = {np.linalg.norm(v_ur)*1000:.3f} mm")
emit(f"  component ALONG elbow->wrist       = {ax_along*1000:+.3f} mm  ({abs(ax_along)/np.linalg.norm(v_ur)*100:.1f}% of |axis|)")
emit(f"  component PERPENDICULAR            = {perp_len*1000:.3f} mm  ({perp_len/np.linalg.norm(v_ur)*100:.1f}% of |axis|)")
emit(f"  angle(axis, forearm axis)          = {np.degrees(np.arccos(np.dot(u_ur, u_ew))):.2f} deg")

# anatomical basis: a = elbow->wrist; l = +z (source RIGHT convention) orthogonalized;
# p = a x l  (proper, det([l p a]) check below)
a_hat = u_ew
z0 = np.array([0.0, 0.0, 1.0])
l_hat = z0 - np.dot(z0, a_hat) * a_hat
l_hat = l_hat / np.linalg.norm(l_hat)
p_hat = np.cross(a_hat, l_hat)
B = np.column_stack([a_hat, l_hat, p_hat])
emit("")
emit(f"anatomical basis: a (axial, elbow->wrist) = [{a_hat[0]:.6f}, {a_hat[1]:.6f}, {a_hat[2]:.6f}]")
emit(f"                  l (lateral, +z-source-RIGHT orthogonalized) = [{l_hat[0]:.6f}, {l_hat[1]:.6f}, {l_hat[2]:.6f}]")
emit(f"                  p = a x l = [{p_hat[0]:.6f}, {p_hat[1]:.6f}, {p_hat[2]:.6f}]  (points -x = POSTERIOR, +x forward)")
emit(f"det([a l p]) = {np.linalg.det(B):.12f}")

dec = np.array([np.dot(v_ur, a_hat), np.dot(v_ur, l_hat), np.dot(v_ur, p_hat)])
emit("")
emit("  ulna->radius in the anatomical frame (axial, lateral, dorsovolar):")
emit(f"    axial   = {dec[0]*1000:+.3f} mm")
emit(f"    lateral = {dec[1]*1000:+.3f} mm   (+ = toward source +z/right = the side the RADIUS body sits on)")
emit(f"    p-axis  = {dec[2]*1000:+.3f} mm   (positive = posterior)")
emit(f"    |resid| check: {np.linalg.norm(dec)*1000:.3f} mm vs |axis| {np.linalg.norm(v_ur)*1000:.3f} mm")
emit("")
emit("  VERDICT on the open direction question: the axis is OBLIQUE, PERPENDICULAR-dominant:")
emit(f"    perpendicular-dominant: {perp_len/np.linalg.norm(v_ur)*100:.1f}% of the offset is transverse (18.1 of 23.1 mm),")
emit(f"    but {ax_along/np.linalg.norm(v_ur)*100:.1f}% runs ALONG the forearm (14.3 mm distal), so 'pure lateral' is false too;")
emit(f"    the transverse part is {(dec[1]/np.sqrt(dec[1]**2+dec[2]**2)*100):.1f}% lateral / {(abs(dec[2])/np.sqrt(dec[1]**2+dec[2]**2)*100):.1f}% dorsovolar -> the offset lies in the")
emit("    coronal plane of the forearm (radial head sits beside the ulna, slightly distal).")

# ------------------------------------------------------------- site tables
emit("")
emit("=" * 78)
emit("SECTION 3 -- THE 10 ULNA SITES IN THE ELBOW->WRIST ANATOMICAL FRAME")
emit("=" * 78)
emit("axial = p.a (distal from elbow); lateral = p.l (+ = radius side); p3 = p.p (+ = posterior)")
emit(f"fractions are of the SOURCE forearm |elbow->wrist| = {EW_src*1000:.3f} mm")
emit("")
hdr = (f"{'site':12s} {'|p| mm':>8s} {'axial mm':>9s} {'ax %EW':>7s} {'lat mm':>8s} {'p3 mm':>8s} "
       f"{'p.ur mm':>8s} {'perp_ur':>8s}")
emit(hdr)
rows = {}
for sn, sp in ulna_sites:
    p = np.array([float(v) for v in sp.split()])
    axl = float(np.dot(p, a_hat)); lat = float(np.dot(p, l_hat)); p3 = float(np.dot(p, p_hat))
    pur = float(np.dot(p, u_ur)); perp = float(np.linalg.norm(p - pur * u_ur))
    rows[sn] = dict(p=p, axl=axl, lat=lat, p3=p3, pur=pur, perp=perp, absn=float(np.linalg.norm(p)))
    emit(f"{sn:12s} {np.linalg.norm(p)*1000:8.3f} {axl*1000:9.3f} {axl/EW_src*100:7.2f} "
         f"{lat*1000:8.3f} {p3*1000:8.3f} {pur*1000:8.3f} {perp*1000:8.3f}")

pmax = max(rows.values(), key=lambda r: r["absn"])
emit("")
emit(f"max |p| = {pmax['absn']*1000:.3f} mm ({[k for k,v in rows.items() if v is pmax][0]})")
emit(f"  / |ulna->radius axis| 23.074 mm  = {pmax['absn']/np.linalg.norm(v_ur):.3f}  (the '4.4x' number)")
emit(f"  axial extent of the AXIS itself  = {ax_along*1000:.3f} mm -> max-axial/axis-axial = {pmax['axl']/abs(ax_along):.3f}")
emit(f"  ECU-P4 perp to KINEMATIC axis    = {rows['ECU-P4']['perp']*1000:.3f} mm ; perp to FOREARM axis = "
     f"{np.linalg.norm(rows['ECU-P4']['p'] - rows['ECU-P4']['axl']*a_hat)*1000:.3f} mm")

# ------------------------------------------------------------- target side
emit("")
emit("=" * 78)
emit("SECTION 4 -- TARGET ANCHORS (packet actual_monkey_fit.json) + CANDIDATE FRAMES")
emit("=" * 78)
jname = {j["name"]: j for j in pkt["joints"]}
E = np.array(jname["elbow_flexion"]["origin"])
Wt = np.array(jname["wrist_dev_r"]["origin"])
S = np.array(jname["shoulder_elv"]["origin"])
ew_t = Wt - E
ewl = np.linalg.norm(ew_t)
w_hat = ew_t / ewl
emit(f"elbow_R (packet elbow_flexion origin) = [{E[0]:.18f}, {E[1]:.18f}, {E[2]:.18f}]")
emit(f"wrist_R (packet wrist triple origin)  = [{Wt[0]:.18f}, {Wt[1]:.18f}, {Wt[2]:.18f}]")
emit(f"shoulder_R                            = [{S[0]:.9f}, {S[1]:.9f}, {S[2]:.9f}]")
emit(f"|elbow_R->wrist_R| = {ewl:.9f} m   |shoulder_R->elbow_R| = {np.linalg.norm(S-E):.9f} m")
rad_pkt = [s for s in pkt["segments"] if s.get("source_body") == "radius"][0]
emit(f"packet radius scale (known-good)      = {rad_pkt.get('scale')}")
emit(f"check 0.292029*0.221707 = {0.292029*0.221707:.9f} m  vs |EW| {ewl:.9f} m")
emit(f"source->target forearm ratio |EWt|/|EWs| = {ewl/EW_src:.6f}")

AX_U = np.linalg.norm(v_ur)          # 0.023074
ECU4 = rows["ECU-P4"]["absn"]        # 0.102764

# U-STR: P_d = elbow_R + 0.005116 along wrist direction
s_str_1 = 0.005116 / AX_U
s_str_2 = float(np.ravel(rad_pkt["scale"])[0])
emit("")
emit("U-STR: dist landmark = elbow_R + 0.005116 m along elbow->wrist (authored, no pack joint)")
emit(f"  implied s_a = 0.005116/{AX_U:.6f} = {s_str_1:.6f}   (packet body scale {s_str_2}; diff {abs(s_str_1-s_str_2):.2e} -> immaterial)")
emit(f"  target forearm partition: ulna owns {0.005116/ewl*100:.1f}% of |EW|, radius (by closure) owns {(ewl-0.005116)/ewl*100:.1f}%")
s_str = float(s_str_2) if isinstance(s_str_2, (int, float)) else s_str_1
emit(f"  using s = {s_str:.6f} for the site table below")

# U-ANA
s_ana = ewl / ECU4
emit("")
emit(f"U-ANA: dist landmark = site:ECU-P4 (|p| = {ECU4:.6f} m) mapped to wrist_R")
emit(f"  implied s_a = {ewl:.6f}/{ECU4:.6f} = {s_ana:.6f}")
emit(f"  ECU-P4 is an INTERIOR tendon waypoint (4 of 6 in ECU_tendon), not a terminal site; "
     f"terminal = ECU-P6 on hand_r: referenced_by={refs.get('ECU-P4')} / {refs.get('ECU-P6')}")

# frames' axial unit vectors
u_e4 = rows["ECU-P4"]["p"] / ECU4
emit("")
emit(f"U-ANA frame axis (unit origin->ECU-P4) = [{u_e4[0]:.6f}, {u_e4[1]:.6f}, {u_e4[2]:.6f}]")
emit(f"  angle to source forearm axis a = {np.degrees(np.arccos(np.dot(u_e4, a_hat))):.2f} deg")
emit(f"  angle to kinematic axis u_ur   = {np.degrees(np.arccos(np.dot(u_e4, u_ur))):.2f} deg")

# ------------------------------------------------- fitted placement tables
emit("")
emit("=" * 78)
emit("SECTION 5 -- GEOMETRY-ONLY PREDICTED SITE PLACEMENTS UNDER EACH AUTHORING")
emit("=" * 78)
emit("axial placement along the target forearm (roll-independent: a' = B'e . e1 = wrist direction,")
emit("so fitted_axial = s * (p . a_src_frame) exactly; transverse = s * |perp to the frame axis|).")
emit("No fitting run, no search: closed-form consequence of each single authoring.")
emit("")
emit("-- U-STR (frame axis = ulna->radius kinematic axis, s = %.6f) --" % s_str)
emit(f"{'site':12s} {'fitted_ax mm':>12s} {'%EWt':>6s} {'src %EW':>8s} {'delta pt':>9s} {'transv mm':>10s}")
str_rows = {}
for sn in names10:
    r = rows[sn]
    fa = s_str * r["pur"]
    ft = s_str * r["perp"]
    str_rows[sn] = fa
    emit(f"{sn:12s} {fa*1000:12.3f} {fa/ewl*100:6.2f} {r['axl']/EW_src*100:8.2f} "
         f"{(fa/ewl - r['axl']/EW_src)*100:9.2f} {ft*1000:10.3f}")
emit(f"  ECU-P4 lands at {str_rows['ECU-P4']*1000:.2f} mm of {ewl*1000:.2f} mm ({str_rows['ECU-P4']/ewl*100:.1f}%) "
     f"— NOT at the wrist (it is not mapped to it).")

emit("")
emit("-- U-ANA (frame axis = origin->ECU-P4, s = %.6f) --" % s_ana)
emit(f"{'site':12s} {'fitted_ax mm':>12s} {'%EWt':>6s} {'src %EW':>8s} {'delta pt':>9s} {'transv mm':>10s}")
for sn in names10:
    r = rows[sn]
    pa = float(np.dot(r["p"], u_e4))
    fa = s_ana * pa
    ft = s_ana * float(np.linalg.norm(r["p"] - pa * u_e4))
    mark = "  <= construction input" if sn == "ECU-P4" else ""
    emit(f"{sn:12s} {fa*1000:12.3f} {fa/ewl*100:6.2f} {r['axl']/EW_src*100:8.2f} "
         f"{(fa/ewl - r['axl']/EW_src)*100:9.2f} {ft*1000:10.3f}{mark}")

# ------------------------------------------------------- extrapolation math
emit("")
emit("=" * 78)
emit("SECTION 6 -- THE '4.4x EXTRAPOLATION' DECOMPOSED")
emit("=" * 78)
emit(f"(a) kinematic-frame reading:  max|p|/|axis| = {ECU4:.6f}/{AX_U:.6f} = {ECU4/AX_U:.4f}x")
emit(f"    (this is the number behind 'frame extrapolation ~4.4x the bone length')")
emit(f"(b) anatomical-frame reading: the sites are NOT 'off' the axis mostly transversely —")
emit(f"    ECU-P4 axial in the anatomical frame = {rows['ECU-P4']['axl']*1000:.3f} mm "
     f"({rows['ECU-P4']['axl']/ECU4*100:.1f}% of its |p|) vs transverse "
     f"{np.linalg.norm(rows['ECU-P4']['p'] - rows['ECU-P4']['axl']*a_hat)*1000:.3f} mm")
emit(f"    -> max-axial/|axis| = {rows['ECU-P4']['axl']/AX_U:.3f}x ; max-axial/axial-extent-of-axis = "
     f"{rows['ECU-P4']['axl']/abs(ax_along):.3f}x ; max-transverse/|axis| = "
     f"{np.linalg.norm(rows['ECU-P4']['p'] - rows['ECU-P4']['axl']*a_hat)/AX_U:.3f}x")
emit(f"(c) under U-STR the whole layout scales by s = {s_str:.6f}: the extrapolation survives the map")
emit(f"    1:1 (it is a property of the SOURCE layout, not of the target scale).")
emit(f"(d) source->target body-scale ratio (0.2217) and 1/0.2217 = {1/s_str:.3f} are a DIFFERENT number —")
emit(f"    do not conflate the cross-animal scale with the intra-source frame extrapolation.")

# ------------------------------------------------------------- mass note
m_uln = 0.729
emit("")
emit("mass closed form (uniform policy), stated WITHOUT preference:")
emit(f"  U-STR: 0.729 * {s_str:.6f}^3 = {m_uln*s_str**3:.6f} kg")
emit(f"  U-ANA: 0.729 * {s_ana:.6f}^3 = {m_uln*s_ana**3:.6f} kg   (ratio {s_ana**3/s_str**3:.2f}x)")
emit("  (m' = m*det(S); DERIVATION sec.9; physiology not carried)")

# ------------------------------------------------ envelope context numbers
emit("")
emit("envelope context (session-3 medians, quoted from B1 report sec.4.1: b 20.2 mm / c 22.9 mm;")
emit("B4 E4: hand-region cluster median perp 1.9 cm):")
emit(f"  U-STR max transverse placement = {s_str*max(r['perp'] for r in rows.values())*1000:.2f} mm")
pa = [(s_ana*np.dot(r['p'], u_e4), s_ana*float(np.linalg.norm(r['p']-np.dot(r['p'],u_e4)*u_e4))) for r in rows.values()]
emit(f"  U-ANA max transverse placement = {max(t for _, t in pa)*1000:.2f} mm")

with open(r"E:/PythonChimera/forearm_package/audits/C1_ulna_evidence/receipts/c1_geometry.txt", "w") as f:
    f.write("\n".join(OUT) + "\n")
print("\n[saved receipts/c1_geometry.txt]")
