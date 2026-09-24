"""C2 step 4 — mass spread arithmetic: m' = m·|det S| under each candidate's S.

Zero-residual demonstration against the BODY_RESOLUTION_MAP §2.2 mass row
(0.0050 / 0.168-0.169 / 0.227 kg), using only baseline numbers:
  m          = 0.4575 kg           (hand_r <inertial>, chimanoid.xml)
  L_hand     = 0.15529 m           (wrist->3distph geom anchor, C2 source receipt)
  L_paddle   = 0.1113 / 0.1114 m   (C2 target receipt; B1 v3)
  W_source   = 0.06089 m           (mc+thumb-column x-extent, C2 source receipt)
  T_source   = 0.02019 m           (mc-row z-extent, C2 source receipt)
  W_paddle   = 0.0471 m, T_paddle = 0.0181 m  (far-end transverse extents, B1 v3 + C2)
  s_body     = 0.2217 / 0.221707   (body scale, frozen evidence / A4)

Also verifies the packet's own hand_r record carries NO mass (unresolved), and
reproduces the map's site-placement row for H-LEN and H-BODY.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

FIT = Path(r"E:\PythonChimera\forearm_package\baseline_snapshot\runs\actual_monkey_fit.json")
ADMIT = Path(r"E:\PythonChimera\forearm_package\baseline_snapshot\runs\admission_actual_monkey.json")
OUT = Path(r"E:\PythonChimera\forearm_package\audits\C2_hand_evidence\receipts\mass_arithmetic.txt")

L: list[str] = []


def say(s: str = "") -> None:
    L.append(s)
    print(s)


M = 0.4575                       # kg, authored hand mass
L_HAND = 0.15529                 # m, wrist->3distph anchor (measured this audit)
L_HAND_MAP = 0.1554              # m, map's frozen value
L_PAD_V3 = 0.1114                # m, B1 v3 skin extent
L_PAD_C2 = 0.1113                # m, C2 r<25mm max axial
W_SRC = 0.06089                  # m, palm width (5mc..thumbprox x-extent)
W_SRC_MAP = 0.061
T_SRC = 0.02019                  # m, palm thickness (mc-row z-extent)
T_SRC_MAP = 0.020
W_PAD = 0.0471                   # m, paddle far-end width
T_PAD = 0.0181                   # m, paddle far-end thickness
S_BODY = 0.221707                # body scale (A4 exact)
S_BODY_MAP = 0.2217

say("=== C2 MASS-SPREAD ARITHMETIC (uniform-constant-density closed form, DERIVATION §9) ===")
say("closed form (DERIVATION §9 verbatim): m' = m · |det L| = m · det S   (proper rotations det +1)")
say(f"authored hand mass m = {M} kg (chimanoid.xml hand_r <inertial>)")
say("")

say("--- H-LEN: uniform s from paddle/phalanx length match ---")
for lpad, lhand, tag in ((L_PAD_C2, L_HAND, "paddle 0.1113 / hand 0.15529 (this audit)"),
                         (L_PAD_V3, L_HAND_MAP, "paddle 0.1114 / hand 0.1554 (B1 v3 / map)")):
    s = lpad / lhand
    m_ = M * s**3
    say(f"  s = {lpad}/{lhand} = {s:.6f}   [{tag}]")
    say(f"      det S = s^3 = {s**3:.6f}   m' = 0.4575 x {s**3:.6f} = {m_:.6f} kg  -> {m_:.3f} kg")
say(f"  map's rounded s=0.716:  m' = 0.4575 x 0.716^3 = {M*0.716**3:.6f} kg -> {M*0.716**3:.3f} kg")
say(f"  s / body scale = {(L_PAD_C2/L_HAND)/S_BODY:.2f}x (map: '3.2x body scale - flagged')")
say("")

say("--- H-ASP: length + aspect (diagonal S = diag(s_a, s_b, s_c)) ---")
sa = L_PAD_C2 / L_HAND
sb = W_PAD / W_SRC
sc = T_PAD / T_SRC
det = sa * sb * sc
say(f"  s_a = {L_PAD_C2}/{L_HAND} = {sa:.6f}")
say(f"  s_b = {W_PAD}/{W_SRC} = {sb:.6f}   (map: 0.0471/0.061 = {W_PAD/W_SRC_MAP:.4f})")
say(f"  s_c = {T_PAD}/{T_SRC} = {sc:.6f}   (map: 0.0181/0.020 = {T_PAD/T_SRC_MAP:.4f})")
say(f"  det S = s_a.s_b.s_c = {det:.6f}   m' = 0.4575 x {det:.6f} = {M*det:.6f} kg -> {M*det:.3f} kg")
det_map = 0.716 * 0.77 * 0.90
say(f"  map's rounded s = 0.716x0.77x0.90: det = {det_map:.6f}, m' = {M*det_map:.6f} kg -> {M*det_map:.3f} kg")
say("")

say("--- H-BODY: uniform body scale ---")
for s, tag in ((S_BODY, "A4 exact 0.221707"), (S_BODY_MAP, "map rounded 0.2217")):
    say(f"  s = {s} [{tag}]: det S = s^3 = {s**3:.8f}  m' = {M*s**3:.6f} kg -> {M*s**3:.4f} kg")
say(f"  fingertip image under body scale: {L_HAND*S_BODY:.5f} m = {L_HAND*S_BODY*1000:.1f} mm (map: '0.0344 m distal')")
say("")

say("--- spread structure ---")
m_len = M * (L_PAD_V3 / L_HAND_MAP) ** 3
m_asp = M * det_map
m_body = M * S_BODY_MAP ** 3
say(f"  candidates' masses: H-BODY {m_body:.4f} / H-LEN {m_len:.4f} / H-ASP {m_asp:.4f} kg")
say(f"  spread max/min = {m_asp/m_body:.1f}x ; det ratio = {det_map/(S_BODY_MAP**3):.1f}x  (identical: pure det(S))")
say(f"  H-ASP/H-LEN = {m_asp/m_len:.3f} = s_b.s_c/s^2 = {(0.77*0.90)/0.716**2:.3f}")
say("")

say("--- site-placement row cross-check (map §2.2) ---")
sites = (0.0299, 0.0428)
s_len = L_PAD_V3 / L_HAND_MAP
say(f"  source sites |p| {sites[0]}..{sites[1]} m (frozen evidence)")
say(f"  H-LEN  axial x s = x {s_len:.3f} -> {sites[0]*s_len:.4f}..{sites[1]*s_len:.4f} m (map: '2.1-3.1 cm')")
say(f"  H-BODY axial x s = x {S_BODY_MAP:.4f} -> {sites[0]*S_BODY_MAP:.4f}..{sites[1]*S_BODY_MAP:.4f} m (map: '0.7-0.9 cm')")
say("")

say("--- the shipped packet's own hand record ---")
d = json.load(open(FIT))
segs = d.get("segments", {})
if isinstance(segs, dict):
    hr = segs.get("hand_r")
else:
    hr = next((s for s in segs if isinstance(s, dict) and s.get("name") == "hand_r"), None)
if hr is None:
    say("  hand_r not in 'segments' (expected: it is UNRESOLVED)")
    key = [k for k in d.keys()]
    us = d.get("unresolved_segments", [])
    hru = None
    if isinstance(us, dict):
        hru = us.get("hand_r")
    elif isinstance(us, list):
        hru = next((u for u in us if isinstance(u, dict) and u.get("name", "").startswith("hand_r")), None)
    if hru is not None:
        say(f"  unresolved_segments hand_r keys: {sorted(hru.keys())}")
        say(f"  reason: {hru.get('reason')}")
        say(f"  axial: {hru.get('axial')}; mass field present: {'mass' in hru}")
say(f"  top-level packet keys: {list(d.keys())}")
say("")

say("--- admission (shipped) ---")
adm = json.load(open(ADMIT))
ma = adm["admission"]["mass_admission"]
for k, v in ma.items():
    say(f"  {k}: {json.dumps(v)}")
say(f"  counts: {adm['admission']['counts']}")
say(f"  hand in unresolved: {'hand_r' in adm['admission']['bodies']['unresolved']}")
say(f"  physically_admitted mass total: {adm['admission']['totals_mass_kg']['physically_admitted']} kg")

OUT.write_text("\n".join(L), encoding="utf-8")
print(f"\n[receipt written: {OUT}]")
