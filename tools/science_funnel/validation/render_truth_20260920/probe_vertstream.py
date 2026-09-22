"""probe_vertstream.py -- read-only probe of the slice's live vertex stream
(render-truth lane). Prints the header vertex count and the first N vertices'
9 floats (pos3, nrm3, col3) plus aggregate normal/color statistics, so the
shading route is derived from the DATA (Rule 1), not taste.
"""
import json
import struct
import sys
import urllib.request

import numpy as np

base = sys.argv[1].rstrip("/")
with urllib.request.urlopen(base + "/api/verts", timeout=30) as r:
    raw = r.read()
n = int.from_bytes(raw[:4], "little")
arr = np.frombuffer(raw[4:4 + n * 36], dtype=np.float32).reshape(n, 9)
pos = arr[:, 0:3]
nrm = arr[:, 3:6]
col = arr[:, 6:9]
nrm_len = np.linalg.norm(nrm, axis=1)
col_len = np.linalg.norm(col, axis=1)
out = {
    "n_verts": int(n),
    "pos_min": [float(v) for v in pos.min(axis=0)],
    "pos_max": [float(v) for v in pos.max(axis=0)],
    "normal_len_min": float(nrm_len.min()),
    "normal_len_p50": float(np.median(nrm_len)),
    "normal_len_max": float(nrm_len.max()),
    "normal_nonunit_frac": float(np.mean(np.abs(nrm_len - 1.0) > 1e-3)),
    "color_min": [float(v) for v in col.min(axis=0)],
    "color_max": [float(v) for v in col.max(axis=0)],
    "color_mean": [float(v) for v in col.mean(axis=0)],
    "color_len_p50": float(np.median(col_len)),
    "distinct_colors": int(len(np.unique(col.round(4), axis=0))),
}
first = arr[:5].tolist()
mid = arr[n // 2:n // 2 + 3].tolist()
print("PROBE_RESULT " + json.dumps(
    {"stats": out, "first_verts": first, "mid_verts": mid}, indent=1))
