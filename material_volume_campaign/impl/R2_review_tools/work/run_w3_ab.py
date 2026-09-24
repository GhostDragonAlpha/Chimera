"""R2 W3 A/B driver — runs a reader copy on a report, returns (exit, stdout, stderr).

Usage: python run_w3_ab.py <reader_dir> <report.json>
Prints: exit / sha256(stdout) / sha256(stderr) / first 200 bytes of stderr.
"""
import hashlib
import io
import subprocess
import sys
from pathlib import Path

reader_dir = Path(sys.argv[1]).resolve()
report = Path(sys.argv[2]).resolve()

proc = subprocess.run(
    [sys.executable, str(reader_dir / "material_volume_body_export_reader.py"),
     str(report)],
    cwd=str(reader_dir), capture_output=True)
out_sha = hashlib.sha256(proc.stdout).hexdigest()
err_sha = hashlib.sha256(proc.stderr).hexdigest()
err_head = proc.stderr.decode("utf-8", "replace").strip().replace("\n", " // ")[:200]
has_traceback = b"Traceback (most recent call last)" in proc.stderr
print(f"reader_dir={reader_dir.parent.name}/{reader_dir.name}")
print(f"report={report.name}")
print(f"exit={proc.returncode}")
print(f"stdout_sha256={out_sha} ({len(proc.stdout)} bytes)")
print(f"stderr_sha256={err_sha}")
print(f"traceback={has_traceback}")
print(f"stderr[:200]={err_head}")
