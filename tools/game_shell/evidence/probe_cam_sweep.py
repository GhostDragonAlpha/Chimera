#!/usr/bin/env python3
# Sweep zoom (r) and pitch (phi) to find a camera config that projects the tiny
# ~2m body (centroid near origin, y~0.2) onto-screen / at center. Reports NDC of
# the centroid so we know what gesture to drive in-browser.
import json, struct, math, urllib.request

BASE = "http://127.0.0.1:8210"
NAME = "Tiel-Clean"
W, H = 1280, 900
tanF = math.tan(math.pi/8)          # fov 45 -> tan(22.5)
aspect = W / H


def get(path):
    return urllib.request.urlopen(BASE + path + "?name=" + NAME, timeout=8).read()


def norm(v):
    l = math.hypot(*v) or 1.0
    return [x / l for x in v]


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def main():
    verts = get("/api/verts")
    vbuf = verts[4:] if (len(verts) % 12 != 0 and (len(verts)-4) % 12 == 0) else verts
    nverts = len(vbuf)//12
    pos = [list(struct.unpack_from("<fff", vbuf, i*12)) for i in range(nverts)]
    cx = sum(p[0] for p in pos)/nverts; cy = sum(p[1] for p in pos)/nverts; cz = sum(p[2] for p in pos)/nverts
    centroid = [cx, cy, cz]

    def eye(r, th, ph):
        ch = math.cos(ph)
        tgt = [0, 4.5, 0]
        return [tgt[0]+r*ch*math.sin(th), tgt[1]+r*math.sin(ph), tgt[2]+r*ch*math.cos(th)]

    print("centroid=%s aspect=%.3f tanF=%.3f" % ([round(x,3) for x in centroid], aspect, tanF))
    found = []
    for r in (26, 20, 15, 11, 8, 6):
        for ph in (0.42, 0.2, 0.0, -0.3, -0.6, -1.0, -1.45):
            e = eye(r, -0.55, ph)
            tgt = [0, 4.5, 0]
            fwd = norm([tgt[0]-e[0], tgt[1]-e[1], tgt[2]-e[2]])
            right = norm(cross(fwd, [0, 1, 0]))
            upv = cross(right, fwd)
            v = [centroid[0]-e[0], centroid[1]-e[1], centroid[2]-e[2]]
            depth = v[0]*fwd[0]+v[1]*fwd[1]+v[2]*fwd[2]
            if depth <= 0:
                continue
            dr = v[0]*right[0]+v[1]*right[1]+v[2]*right[2]
            du = v[0]*upv[0]+v[1]*upv[1]+v[2]*upv[2]
            ndcx = dr/(depth*tanF*aspect)
            ndcy = du/(depth*tanF)
            onscreencx = abs(ndcx) < 1
            onscreency = abs(ndcy) < 1
            dist = math.hypot(*[c-e[i] for i, c in enumerate(centroid)])
            # body angular size ~ 2m / dist
            ang = math.degrees(math.atan2(2.0, dist))
            if onscreencx and onscreency:
                found.append((r, ph, round(ndcx,3), round(ndcy,3), round(dist,2), round(ang,1)))
    print("configs where centroid is ON-SCREEN (r,phi,ndcx,ndcy,dist_m,ang_deg):")
    for f in sorted(found, key=lambda x: abs(x[2])+abs(x[3])):
        print("   ", f)
    if not found:
        print("  -> centroid never fully on-screen; closest by |ndcx|+|ndcy|:")
        best = None
        for r in (26, 20, 15, 11, 8, 6):
            for ph in (0.42, 0.2, 0.0, -0.3, -0.6, -1.0, -1.45):
                e = eye(r, -0.55, ph)
                fwd = norm([[0-e[0], 4.5-e[1], 0-e[2]]])
                right = norm(cross(fwd, [0, 1, 0]))
                upv = cross(right, fwd)
                v = [centroid[0]-e[0], centroid[1]-e[1], centroid[2]-e[2]]
                depth = v[0]*fwd[0]+v[1]*fwd[1]+v[2]*fwd[2]
                if depth <= 0:
                    continue
                dr = v[0]*right[0]+v[1]*right[1]+v[2]*right[2]
                du = v[0]*upv[0]+v[1]*upv[1]+v[2]*upv[2]
                ndcx = dr/(depth*tanF*aspect)
                ndcy = du/(depth*tanF)
                score = abs(ndcx)+abs(ndcy)
                if best is None or score < best[0]:
                    best = (score, r, ph, round(ndcx,3), round(ndcy,3))
        print("   ", best)


main()
