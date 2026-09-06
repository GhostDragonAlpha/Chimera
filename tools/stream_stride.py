"""stream_stride.py — push the certified stride into the live engine.

Reads Saved/gait/stride.json (chimera-stride-1, produced by gait_capture.py's
export hook), packs the theta rows into the /stride_bin binary protocol, then
starts playback. Verifies the stream landed before playing.

Protocol (must match main.cpp /stride_bin):
  [u32 magic=0x47415431 ('GAT1')][u32 n_samples][u32 n_joints]
  [f32 dt][u32 loop0][f32*n*nj thetas, radians, pack order]
"""
import json
import struct
import sys
import urllib.request

BASE = "http://127.0.0.1:" + (sys.argv[1] if len(sys.argv) > 1 else "8090")
STRIDE = "Saved/gait/stride.json"
MAGIC = 0x47415431  # 'GAT1'


def post(path, body: bytes, timeout=30):
    req = urllib.request.Request(BASE + path, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def get(path, timeout=10):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def main() -> int:
    doc = json.load(open(STRIDE, encoding="utf-8"))
    if doc.get("format") != "chimera-stride-1":
        print(f"unknown stride format: {doc.get('format')!r}")
        return 2
    names = doc["names"]
    rows = doc["theta"]
    n, nj = doc["n_samples"], doc["n_joints"]
    if len(rows) != n or any(len(r) != nj for r in rows) or len(names) != nj:
        print(f"shape mismatch: rows={len(rows)} n={n} nj={nj} names={len(names)}")
        return 2

    loop0 = int(round(doc["loop_t0"] / doc["dt"]))
    payload = struct.pack("<IIIfI", MAGIC, n, nj, doc["dt"], loop0)
    payload += struct.pack(f"<{n * nj}f", *[v for row in rows for v in row])
    print(f"uploading {n} samples x {nj} joints ({len(payload) / 1e6:.2f} MB)...")
    resp = post("/stride_bin", payload, timeout=120)
    print("stride_bin -> ", resp)
    if '"ok":true' not in resp:
        return 3

    # verify the stream landed before playing
    st = get("/stride")
    print("status  ->", st)
    if st.get("n") != n or st.get("j") != nj:
        print("engine state does not match the uploaded stream")
        return 4

    # start: play from t=0 (startup plays once, then the stride loops)
    print(post("/stride", json.dumps({"on": True, "playing": True, "t": 0.0}).encode()))
    print(f"PLAYING: startup {doc['loop_t0']:.2f}s then {doc['stride_t']:.2f}s stride, "
          f"clock T_stance={doc['clock']['T_stance']:.4f}s, "
          f"gates: foot_max={doc['gates']['foot_max']:.2e} jump_max={doc['gates']['jump_max']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
