"""Raw-byte run harness for the wave-35 lane (declared instrument).

Runs a gait binary on the scene with stdout/stderr to files in BINARY
(no shell re-encoding), prints the stdout sha256 + headline numbers.
Usage: python run_and_hash.py <exe> <scene.json> <out_prefix>
"""
import hashlib, subprocess, sys

exe, scene, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
with open(prefix + "_stdout.txt", "wb") as so, open(prefix + "_stderr.txt", "wb") as se:
    p = subprocess.run([exe, scene], stdout=so, stderr=se)
b = open(prefix + "_stdout.txt", "rb").read()
print("exit:", p.returncode)
print("stdout sha256:", hashlib.sha256(b).hexdigest())
print("stdout bytes:", len(b))
txt = b.decode("utf-8", "replace")
for line in txt.splitlines():
    if any(k in line for k in ("refused_tick", "worst_moving_ledger", '"pass"', "red_falsifiers", '"checks"')):
        print(" ", line.strip())
err = open(prefix + "_stderr.txt", "rb").read()
print("stderr bytes:", len(err))
