"""Pose-vs-frame consistency audit for the SV3D rings.

For each adjacent frame pair in a ring, triangulate SIFT matches under the
COMMANDED relative pose (from poses.json) with the calibrated focal, and
report the median reprojection error. A consistent (image, pose) pair gives
~1-2px; a drifted/wrong pose gives tens of px.

Also does a FREE essential-matrix estimate per pair (cv2.findEssentialMat +
recoverPose) and reports the angular gap between the recovered relative
rotation and the commanded one. This catches elevation/roll drift that the
commanded-pose residual alone attributes to noise.
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RING_DIR = ROOT / "capture" / "sv3d_bear"
FOCAL = 900.0
RES = 576


def cam_center(r, elev_deg, az_deg):
    el = np.deg2rad(elev_deg)
    az = np.deg2rad(az_deg)
    return r * np.array([np.cos(el) * np.sin(az), np.sin(el), np.cos(el) * np.cos(az)])


def world2cam(C):
    z = -C / np.linalg.norm(C)            # forward: toward origin
    up = np.array([0.0, 1.0, 0.0])
    x = np.cross(up, z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return np.stack([x, y, z], axis=0)    # rows: cam axes in world


def pair_stats(im1, im2, R1, R2, C1, C2, sift, bf):
    g1 = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(im2, cv2.COLOR_BGR2GRAY)
    k1, d1 = sift.detectAndCompute(g1, None)
    k2, d2 = sift.detectAndCompute(g2, None)
    if d1 is None or d2 is None:
        return None
    matches = bf.knnMatch(d1, d2, k=2)
    good = [m for m, n in matches if m.distance < 0.75 * n.distance]
    if len(good) < 12:
        return None
    p1 = np.float64([k1[m.queryIdx].pt for m in good])
    p2 = np.float64([k2[m.trainIdx].pt for m in good])

    # commanded-pose reprojection via midpoint triangulation
    x1 = np.stack([(p1[:, 0] - RES / 2) / FOCAL, (p1[:, 1] - RES / 2) / FOCAL,
                   np.ones(len(p1))], axis=1)
    x2 = np.stack([(p2[:, 0] - RES / 2) / FOCAL, (p2[:, 1] - RES / 2) / FOCAL,
                   np.ones(len(p2))], axis=1)
    u = x1 @ R1  # world rays (row form of R1.T @ x)
    v = x2 @ R2
    b = C2 - C1
    errs = []
    for ui, vi, q1px, q2px in zip(u, v, p1, p2):
        A = np.stack([ui, -vi], axis=1)
        try:
            d, *_ = np.linalg.lstsq(A, b, rcond=None)
        except np.linalg.LinAlgError:
            continue
        X = 0.5 * (C1 + d[0] * ui + C2 + d[1] * vi)  # midpoint of closest approach
        r1 = R1 @ (X - C1)
        r2 = R2 @ (X - C2)
        if r1[2] <= 0 or r2[2] <= 0:
            continue
        q1 = np.array([r1[0] / r1[2] * FOCAL + RES / 2, r1[1] / r1[2] * FOCAL + RES / 2])
        q2 = np.array([r2[0] / r2[2] * FOCAL + RES / 2, r2[1] / r2[2] * FOCAL + RES / 2])
        errs.append(0.5 * (np.linalg.norm(q1 - q1px) + np.linalg.norm(q2 - q2px)))
    med = float(np.median(errs)) if errs else float("nan")

    # free essential-matrix relative rotation
    E, mask = cv2.findEssentialMat(p1, p2, focal=FOCAL, pp=(RES / 2, RES / 2),
                                   method=cv2.RANSAC, prob=0.999, threshold=1.5)
    ang_gap = float("nan")
    inliers = 0
    if E is not None:
        n, Rf, tf, maskp = cv2.recoverPose(E, p1, p2, focal=FOCAL, pp=(RES / 2, RES / 2))
        inliers = int(maskp.sum() / 255) if maskp is not None else 0
        # commanded relative rotation (cam2 wrt cam1): Rrel = R2 @ R1.T
        Rrel_cmd = R2 @ R1.T
        # recoverPose gives R from cam1->cam2 in cam1 coords (x2 ~ R x1 + t): Rf ≈ R2 @ R1.T
        dR = Rf @ Rrel_cmd.T
        cosang = min(1.0, max(-1.0, (np.trace(dR) - 1) / 2))
        ang_gap = float(np.rad2deg(np.arccos(cosang)))
    return {"pairs_matches": len(good), "cmd_reproj_px": med,
            "free_rot_gap_deg": ang_gap, "free_inliers": inliers}


def main():
    poses = json.loads((RING_DIR / "poses.json").read_text())["poses"]
    by_ring = {}
    for p in poses:
        by_ring.setdefault(p["ring"], []).append(p)
    sift = cv2.SIFT_create(nfeatures=4000)
    bf = cv2.BFMatcher()
    r = 1.899  # calibrated gauge
    for ring, plist in by_ring.items():
        plist.sort(key=lambda p: p["frame_index"])
        print(f"\n=== ring {ring} ({len(plist)} frames) ===")
        rows = []
        for a, b in zip(plist[:-1], plist[1:]):
            im1 = cv2.imread(str(RING_DIR / a["frame_filename"]))
            im2 = cv2.imread(str(RING_DIR / b["frame_filename"]))
            C1 = cam_center(r, a["elevation_deg"], a["azimuth_deg"])
            C2 = cam_center(r, b["elevation_deg"], b["azimuth_deg"])
            st = pair_stats(im1, im2, world2cam(C1), world2cam(C2), C1, C2, sift, bf)
            if st is None:
                print(f"  {a['frame_index']:02d}->{b['frame_index']:02d}: insufficient matches")
                continue
            rows.append(st)
            print(f"  {a['frame_index']:02d}->{b['frame_index']:02d}: "
                  f"cmd_reproj={st['cmd_reproj_px']:.2f}px  "
                  f"free_rot_gap={st['free_rot_gap_deg']:.2f}deg  "
                  f"matches={st['pairs_matches']} inliers={st['free_inliers']}")
        if rows:
            meds = [x["cmd_reproj_px"] for x in rows]
            gaps = [x["free_rot_gap_deg"] for x in rows if not np.isnan(x["free_rot_gap_deg"])]
            print(f"  RING MEDIAN: cmd_reproj={np.median(meds):.2f}px  "
                  f"free_rot_gap={np.median(gaps):.2f}deg" if gaps else "")


if __name__ == "__main__":
    sys.exit(main())
