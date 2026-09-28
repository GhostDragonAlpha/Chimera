#!/usr/bin/env python -B
"""MAT2-W02 pinned-input extraction (provenance tool, CPU-only, read-only git access).

Extracts every frozen input byte-for-byte from the merged lane in the source repository
using `git -c core.autocrlf=false show`, at BOTH the historical ONT-W02 winner head and the
publication base, requires the two extractions to be identical, writes them into this
attempt's frozen_sites/ directory, and verifies each against the sha256+size table frozen in
PREREGISTRATION.md section 2. No file content is typed or regenerated here.

Usage: python -B extract_pins.py
Exit 0 iff every extracted byte stream matches its frozen identity.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FS = HERE / "frozen_sites"
SOURCE_REPO = Path("E:/PythonChimera")

ONT_HEAD = "531b99354ef241ced711abbaa137105afb28ca5b"
PUBLICATION_BASE = "8ec90f13e76954596af3711c241c08b843ff78bf"
ONT_CONTRIB = "tools/monkey_campaign/contributions/ONT-W02/frozen_sites"

FROZEN_PINS = {
    "trig_inputs.txt": ("a21467e5e5aeb09f23a6de39c16902c34d2a34ebaa83cbccaab01ba1a0ea8b01", 349),
    "ucrt_math.c": ("cde32a8d36c0fbf481d67fa0005ace7dab08f066971085e543f7909740900b97", 28375),
    "ucrt_math_tables.h": ("cdae6a920bb38d517c11683e11fda0c2f15b6069ab5c1ee4d5bbdd9a62d437ed", 12970),
    "ucrt_math_consts.h": ("106b7cc7cc9823d58092a0eddc4987df5a31f0e02d0705e905292b2759aec938", 13101),
    "preserved/trig_host.txt": ("ed48cf12865115dc8223c0e4ab03ca331144a7c6267ad5e25dda327a9b0a24f2", 5463),
    "preserved/trig_gpu.txt": ("bb896746b5883a3cfd73acccd6b4373496da589aa61361fe58be83237fa9e733", 5458),
    "preserved/trig_fdlibm_out.txt": ("41e484b2bf5be5eba7d7607d029d3221880e1af236ea424d938570dd158c34ed", 5469),
    "preserved/co7_gate_out2.txt": ("54e72577920b1fb0a1cfe068ac482198929bfc208779738c2ddf9c7ab1c740a4", 155),
    "preserved/co7_dense_full2.txt": ("2bc8d9bc9631d58f81cf5c1e1d5774455b40e4c30e50661d62351f49ce909f67", 203),
    "preserved/co6_trig_dense.txt": ("c51cda41db828723bdfa3c9360709f2733927164be05cc21db92727c5d5db8d2", 2419),
    "parity_gate_host.cxx": ("9cdc67df81b7fd358d7eef83634ba294a4f9ac310500f5d452fe74b51b17c683", 8766),
    "host_qual_shim.h": ("39ebeeb939d85345c28dcea41f4ab4e4443f168b4c2a4b3a0e0ac33772c1250a", 1010),
}


def show(ref, path):
    proc = subprocess.run(["git", "-C", str(SOURCE_REPO), "-c", "core.autocrlf=false",
                           "show", f"{ref}:{path}"], capture_output=True, shell=False)
    if proc.returncode != 0:
        raise ValueError(f"blob_missing {ref}:{path}: {proc.stderr.decode('utf-8','replace')[:200]}")
    return proc.stdout


def main():
    manifest = {"schema": "chimera.mat2-w02.pin-extraction.v1",
                "task": "MAT2-W02",
                "attempt_id": "296a4a34840e4c81a3a65f95ec491d11",
                "source_repository": "GhostDragonAlpha/Chimera",
                "extracted_from_refs": {"ont_w02_winner_head": ONT_HEAD,
                                        "publication_base_astra_gait_capture": PUBLICATION_BASE},
                "files": {}}
    ok = True
    for rel, (want_sha, want_size) in FROZEN_PINS.items():
        a = show(ONT_HEAD, f"{ONT_CONTRIB}/{rel}")
        b = show(PUBLICATION_BASE, f"{ONT_CONTRIB}/{rel}")
        identical = a == b
        sha = hashlib.sha256(a).hexdigest()
        matches = identical and sha == want_sha and len(a) == want_size
        ok &= matches
        out = FS / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(a)
        manifest["files"][rel] = {"sha256": sha, "bytes": len(a),
                                  "identical_at_both_refs": identical,
                                  "expected_sha256": want_sha,
                                  "expected_bytes": want_size,
                                  "ok": matches}
        print(f"{'OK ' if matches else 'BAD'} {rel:34s} {sha[:16]}… {len(a)} bytes")
    manifest["verdict"] = "PINS_OK" if ok else "PINS_FAIL"
    (HERE / "pin_manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print("VERDICT:", manifest["verdict"])
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print("EXTRACT ERROR:", exc)
        sys.exit(1)
