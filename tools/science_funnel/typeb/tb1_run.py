"""TypeB-P1 raw-byte run harness (declared instrument).

Runs a gait binary on a scene with stdout/stderr to files in BINARY
(no shell re-encoding), times the process wall clock, prints the stdout
sha256 + headline numbers + wall time. Extends the wave-38 run_and_hash
pattern with timing. Usage:
  python tb1_run.py <exe> <scene.json> <out_prefix> [stdout_sha_expect]
"""
import hashlib, json, subprocess, sys, time

exe, scene, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
expect = sys.argv[4] if len(sys.argv) > 4 else None
t0 = time.perf_counter()
with open(prefix + "_stdout.txt", "wb") as so, open(prefix + "_stderr.txt", "wb") as se:
    p = subprocess.run([exe, scene], stdout=so, stderr=se)
wall = time.perf_counter() - t0
b = open(prefix + "_stdout.txt", "rb").read()
sha = hashlib.sha256(b).hexdigest()
print("exit:", p.returncode)
print("wall_s: %.3f" % wall)
print("stdout sha256:", sha)
print("stdout bytes:", len(b))
if expect:
    print("stdout sha match:", sha == expect)
txt = b.decode("utf-8", "replace")
for line in txt.splitlines():
    if any(k in line for k in ("refused_tick", "worst_moving_ledger", '"pass"', "red_falsifiers", '"checks"')):
        print(" ", line.strip()[:400])
err = open(prefix + "_stderr.txt", "rb").read()
print("stderr bytes:", len(err))
er = err.decode("utf-8", "replace")
for line in er.splitlines():
    if line.startswith("WALK REFUSED") or "[tb1-timing]" in line or "[tb1]" in line:
        print(" ", line.strip()[:400])
