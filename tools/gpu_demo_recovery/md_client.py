#!/usr/bin/env python
"""md_client.py -- GPU-DEMO-RECOVERY-01 control/upload harness.

Builds byte-exact MD01 /membrane_demo_bin payloads from the B2 fixture
(main.cpp:62-65 contract), drives the documented op sequence with
per-request logging (order, payload bytes/hash, timing, response,
process liveness), and records JSONL evidence. stdlib + numpy only.

Usage:
  python tools/gpu_demo_recovery/md_client.py --port 8093 --seq upload,status,step
  python tools/gpu_demo_recovery/md_client.py --port 8093 --seq full --out DIR
Ops: upload,status,step,run,pause,gamma-N,reset,reject,frame,invalid-*
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(TOOLS / "gpu_fixtures_recovered"))

from membrane_fixture_b2 import b2_mesh  # noqa: E402
from surface_energy_reference import build_vertex_corner_adjacency  # noqa: E402

GAMMA = 1.0
LIFT = 0.5


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def pack_upload(pos_f32: np.ndarray, faces: np.ndarray, gamma: float,
                centre: int, lift: float) -> bytes:
    nv, nf = int(pos_f32.shape[0]), int(faces.shape[0])
    idx = np.ascontiguousarray(faces, dtype="<u4")
    off, corners = build_vertex_corner_adjacency(idx, nv)
    off = np.ascontiguousarray(off, dtype="<u4")
    corners = np.ascontiguousarray(corners, dtype="<u4")
    gam = np.ascontiguousarray(np.full(nf, gamma, dtype="<f4"))
    pos = np.ascontiguousarray(pos_f32, dtype="<f4")
    header = struct.pack("<4sIII", b"MD01", nv, nf, centre)
    header += struct.pack("<d", float(gamma))
    header += struct.pack("<f", float(lift))
    header += struct.pack("<I", 0)
    assert len(header) == 32
    return (header + pos.tobytes() + idx.tobytes() + off.tobytes()
            + corners.tobytes() + gam.tobytes())


def b2_payload(gamma: float = GAMMA, lift: float = LIFT):
    _, V_up, F = b2_mesh()
    pos32 = V_up.astype(np.float32)
    blob = pack_upload(pos32, F, gamma, int(np.argmax(V_up[:, 2])), lift)
    return blob, pos32, F


def http_post(url: str, body: bytes, ctype: str, timeout: float = 70.0):
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": ctype},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(), dict(r.headers)
    except Exception as e:
        return -1, repr(e).encode(), {}


def http_get(url: str, timeout: float = 30.0):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, r.read(), dict(r.headers)
    except Exception as e:
        return -1, repr(e).encode(), {}


def alive(port: int) -> bool:
    s, _, _ = http_get(f"http://localhost:{port}/state", timeout=5.0)
    return s == 200


class Session:
    def __init__(self, port: int, outdir: Path):
        self.port = port
        self.base = f"http://localhost:{port}"
        self.outdir = outdir
        self.outdir.mkdir(parents=True, exist_ok=True)
        self.log = open(outdir / "requests.jsonl", "a", encoding="utf-8")
        self.n = 0

    def rec(self, **kw):
        kw["seq"] = self.n
        kw["utc"] = datetime.now(timezone.utc).isoformat()
        self.n += 1
        self.log.write(json.dumps(kw) + "\n")
        self.log.flush()
        return kw

    def post_bin(self, blob: bytes, label: str):
        t0 = time.time()
        s, body, _ = http_post(f"{self.base}/membrane_demo_bin", blob,
                               "application/octet-stream", timeout=70.0)
        dt = time.time() - t0
        r = self.rec(op=label, endpoint="/membrane_demo_bin",
                     payload_bytes=len(blob), payload_sha=sha(blob),
                     http=s, ms=round(dt * 1000, 1),
                     body=body[:2000].decode("utf-8", "replace"),
                     alive_after=alive(self.port))
        print(f"[{r['seq']}] {label}: http={s} {dt*1000:.0f}ms alive={r['alive_after']}")
        print(f"   {r['body'][:300]}")
        return r

    def ctl(self, op: str, extra: dict | None = None):
        payload = {"op": op}
        if extra:
            payload.update(extra)
        raw = json.dumps(payload).encode()
        t0 = time.time()
        s, body, _ = http_post(f"{self.base}/membrane_demo", raw,
                               "application/json", timeout=90.0)
        dt = time.time() - t0
        r = self.rec(op=f"ctl:{op}", endpoint="/membrane_demo",
                     payload_bytes=len(raw), payload_sha=sha(raw),
                     payload=payload, http=s, ms=round(dt * 1000, 1),
                     body=body[:2000].decode("utf-8", "replace"),
                     alive_after=alive(self.port))
        print(f"[{r['seq']}] ctl:{op}: http={s} {dt*1000:.0f}ms alive={r['alive_after']}")
        print(f"   {r['body'][:300]}")
        return r

    def status(self, label="status"):
        t0 = time.time()
        s, body, _ = http_get(f"{self.base}/membrane_demo", timeout=15.0)
        dt = time.time() - t0
        r = self.rec(op=label, endpoint="GET /membrane_demo", http=s,
                     ms=round(dt * 1000, 1),
                     body=body[:2000].decode("utf-8", "replace"),
                     alive_after=alive(self.port))
        print(f"[{r['seq']}] {label}: http={s} alive={r['alive_after']}")
        print(f"   {r['body'][:300]}")
        return r

    def frame(self, label="frame"):
        t0 = time.time()
        s, body, h = http_get(f"{self.base}/frame", timeout=30.0)
        dt = time.time() - t0
        p = None
        if s == 200 and body[:4] == b"\x89PNG":
            p = self.outdir / f"{label}.png"
            p.write_bytes(body)
        r = self.rec(op=label, endpoint="/frame", http=s,
                     ms=round(dt * 1000, 1), png_bytes=len(body),
                     png_sha=sha(body), png_path=str(p) if p else None,
                     alive_after=alive(self.port))
        print(f"[{r['seq']}] {label}: http={s} bytes={len(body)} alive={r['alive_after']}")
        return r

    def close(self):
        self.log.close()


def run_seq(port: int, seq: list[str], outdir: Path):
    ses = Session(port, outdir)
    blob, _, _ = b2_payload()
    try:
        for op in seq:
            if op == "upload":
                ses.post_bin(blob, "upload-B2")
            elif op == "status":
                ses.status()
            elif op == "frame":
                ses.frame()
            elif op.startswith("gamma-"):
                ses.ctl("gamma", {"gamma": float(op.split("-", 1)[1])})
            elif op.startswith("run-"):
                ses.ctl("run", {"n_steps": int(op.split("-", 1)[1])})
            elif op in ("reset", "step", "run", "pause", "reject"):
                ses.ctl(op)
            elif op == "reupload":
                ses.post_bin(blob, "reupload-B2-same-bytes")
            elif op == "upload-short":
                ses.post_bin(b"MD01" + b"\x00" * 10, "upload-short")
            elif op == "upload-badmagic":
                bad = b"BAD!" + blob[4:]
                ses.post_bin(bad, "upload-badmagic")
            elif op == "ctl-badop":
                ses.ctl("explode")
            else:
                print(f"unknown op {op}")
            if not alive(port):
                print("ENGINE DEAD -- stopping sequence")
                ses.rec(op="engine-dead", alive_after=False)
                break
    finally:
        ses.close()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8093)
    ap.add_argument("--seq", default="upload,status,step")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    seq = args.seq.split(",")
    if seq == ["full"]:
        seq = ["upload", "status", "step", "status", "gamma-0", "status",
               "gamma-2", "status", "reset", "status", "reject", "status",
               "run-126", "status", "reupload", "status", "frame"]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    outdir = Path(args.out) if args.out else Path(
        f"docs/evidence/gpu_demo_recovery/seq_{stamp}")
    run_seq(args.port, seq, outdir)
    print(f"evidence: {outdir}")


if __name__ == "__main__":
    main()
