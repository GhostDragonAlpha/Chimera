"""Capture the reader CLI's verbatim behavior over every W3 input.

Invoked twice against the SAME unchanging inputs: once BEFORE the repair
(-> receipts/before/) and once AFTER (-> receipts/after/). Records exit code,
stdout sha256 + byte length, and FULL verbatim stderr for every case, plus the
sha256 of the reader file itself at capture time. Diffing before/ against
after/ is the byte-identical / changed-behavior proof.

Run: python work/capture.py receipts/before   (from impl/W3_reader_m13/)
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMPL = HERE.parent
REPO = IMPL.parents[1].parent
READER = REPO / "tools" / "material_volume_body_export_reader.py"
FIXTURES = IMPL / "tests" / "fixtures"

sys.path.insert(0, str(HERE))
from make_fixtures import READ_IN_PLACE  # noqa: E402

ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}


def run_cli(report_path: Path):
    proc = subprocess.run([sys.executable, str(READER), str(report_path)],
                          cwd=str(REPO), capture_output=True, env=ENV)
    return proc.returncode, proc.stdout, proc.stderr.decode("utf-8", "replace")


def main() -> int:
    outdir = IMPL / sys.argv[1]
    outdir.mkdir(parents=True, exist_ok=True)
    manifest = {"reader_sha256_at_capture": hashlib.sha256(
        READER.read_bytes()).hexdigest(), "cases": {}}
    inputs = {f"{p.stem}": p for p in sorted(FIXTURES.glob("*.json"))}
    inputs.update(READ_IN_PLACE)
    for name, path in sorted(inputs.items()):
        code, out, err = run_cli(path)
        manifest["cases"][name] = {
            "input": str(path.relative_to(REPO)),
            "exit": code,
            "stdout_sha256": hashlib.sha256(out).hexdigest(),
            "stdout_bytes": len(out),
            "stderr_sha256": hashlib.sha256(err.encode("utf-8")).hexdigest(),
        }
        (outdir / f"{name}.exit").write_text(f"{code}\n", encoding="utf-8", newline="\n")
        (outdir / f"{name}.stdout.sha256").write_text(
            f"{hashlib.sha256(out).hexdigest()}  {len(out)} bytes\n",
            encoding="utf-8", newline="\n")
        (outdir / f"{name}.stderr.txt").write_text(err, encoding="utf-8", newline="")
    (outdir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n")
    crashes = [n for n, c in manifest["cases"].items() if c["exit"] not in (0, 2)]
    print(f"captured {len(manifest['cases'])} cases -> {outdir}")
    print(f"reader sha256: {manifest['reader_sha256_at_capture']}")
    print(f"non-0/2 exits (uncaught crashes): {crashes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
