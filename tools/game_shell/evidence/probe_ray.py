#!/usr/bin/env python3
# Fetch REAL streamed verts + topology; raycast in Python against the exact page
# camera (r=26, theta=-0.55, phi=0.42, target=[0,4.5,0]) to see whether any body
# triangle lies under a screen-center / look-down ray.
import json, struct, math, urllib.request

BASE = "http://127.0.0.1:8210"
NAME = "Tiel-Clean"


def get(path):
    return urllib.request.urlopen(BASE + path + "?name=" + NAME, timeout=8).read()


def camEye(r, th, ph, tgt):
    ch = math.cos(ph)
    return [tgt[0] + r * ch * math.sin(th), tgt[1] + r * math.sin(ph), tgt[2] + r * ch * math.cos(th)]


def norm(v):
    l = math.hypot(*v) or 1.0
    return [x / l for x in v]


def ray_tri(ox, oy, oz, dx, dy, dz, p0, p1, p2):
    e1 = [p1[0]-p0[0], p1[1]-p0[1], p1[2]-p0[2]]
    e2 = [p2[0]-p0[0], p2[1]-p0[1], p2[2]-p0[2]]
    h = [dy*e2[2]-dz*e2[1], dz*e2[0]-dx*e2[2], dx*e2[1]-dy*e2[0]]
    det = e1[0]*h[0] + e1[1]*h[1] + e1[2]*h[2]
    if abs(det) < 1e-9:
        return None
    inv = 1.0 / det
    t = [ox-p0[0], oy-p0[1], oz-p0[2]]
    u = (t[0]*h[0]+t[1]*h[1]+t[2]*h[2]) * inv
    if u < 0 or u > 1:
        return None
    q = [e1[1]*e2[2]-e1[2]*e2[1], e1[2]*e2[0]-e1[0]*e2[2], e1[0]*e2[1]-e1[1]*e2[0]]
    s = [dx*q[0]+dy*q[1]+dz*q[2], dx*q[1]+dy*q[2]+dz*q[0], dx*q[2]+dy*q[0]+dz*q[1]]
    v = (t[0]*s[0]+t[1]*s[1]+t[2]*s[2]) * inv
    if v < 0 or u+v > 1:
        return None
    tt = (e1[0]*s[0]+e1[1]*s[1]+e1[2]*s[2]) * inv
    return tt if tt > 1e-4 else None


def main():
    verts = get("/api/verts")
    topo = get("/api/topology")
    # verts: positions-only Float32 (12 bytes/vert) + 4-byte header if not divisible
    vbuf = verts
    if len(vbuf) % 12 != 0 and (len(vbuf)-4) % 12 == 0:
        vbuf = vbuf[4:]
    nverts = len(vbuf)//12
    pos = []
    for i in range(nverts):
        off = i*12
        px, py, pz = struct.unpack_from("<fff", vbuf, off)
        pos.append([px, py, pz])
    xs = [p[0] for p in pos]; ys = [p[1] for p in pos]; zs = [p[2] for p in pos]
    print("verts=%d  x[%g,%g] y[%g,%g] z[%g,%g]" % (nverts, min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
    centroid = [sum(xs)/nverts, sum(ys)/nverts, sum(zs)/nverts]
    print("centroid:", [round(x,3) for x in centroid])

    ibuf = topo
    if len(ibuf) % 4 != 0 and (len(ibuf)-4) % 4 == 0:
        ibuf = ibuf[4:]
    allidx = list(struct.unpack("<%dI" % (len(ibuf)//4), ibuf))
    tris = len(allidx)//3
    print("tris=%d" % tris)
    idx = allidx

    eye = camEye(26, -0.55, 0.42, [0, 4.5, 0])
    print("eye:", [round(x,2) for x in eye])

    rays = {
        "toward_target": [0, 4.5, 0],
        "toward_origin": [0, 0, 0],
        "straight_down": [eye[0], -100, eye[2]],
        "toward_centroid": centroid,
    }
    for name, d in rays.items():
        dd = norm([d[0]-eye[0], d[1]-eye[1], d[2]-eye[2]])
        hits = 0; first = None
        for i in range(tris):
            i0 = idx[i*3]; i1 = idx[i*3+1]; i2 = idx[i*3+2]
            t = ray_tri(eye[0], eye[1], eye[2], dd[0], dd[1], dd[2], pos[i0], pos[i1], pos[i2])
            if t is not None:
                hits += 1
                if first is None:
                    first = [round(eye[j]+dd[j]*t, 3) for j in range(3)]
        print("ray %-16s hits=%d  first_hit=%s" % (name, hits, first))


main()
