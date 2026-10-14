"""CLI: python -m tools.policy_compat <mode> [args]

Worker modes (fresh subprocesses, raw-byte files -- the frozen-ref pattern):
  run-full <out_prefix> <seed> <N|N+1> <horizon>
  checkpoint <out_snapshot.json> <seed> <tick> <horizon>
  resume <snapshot.json> <out_prefix> <seed> <horizon> <start_tick>
  resume-forced <snapshot.json> <out_prefix> <seed> <horizon> <start_tick> <rng|warm>

Gate modes:
  validate <certificate.json>            exit 0 valid / 1 invalid / 2 unreadable
  schema                                 print the draft-2020-12 JSON schema
  check-deploy <request.json> <certificate.json|NONE>   exit 0 ALLOW / 1 BLOCK
"""
from __future__ import annotations

import json
import sys


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    mode, args = argv[0], argv[1:]

    if mode == "run-full":
        from .runner import worker_run
        worker_run(args[0], int(args[1]), args[2], int(args[3]))
        return 0
    if mode == "checkpoint":
        from .runner import worker_checkpoint
        worker_checkpoint(args[0], int(args[1]), int(args[2]), int(args[3]))
        return 0
    if mode == "resume":
        from .runner import worker_resume
        worker_resume(args[0], args[1], int(args[2]), int(args[3]), int(args[4]))
        return 0
    if mode == "resume-forced":
        from .runner import worker_resume
        worker_resume(args[0], args[1], int(args[2]), int(args[3]), int(args[4]),
                      forced_drop=args[5])
        return 0
    if mode == "validate":
        from .certificate import validate_certificate
        try:
            with open(args[0], "r", encoding="utf-8") as f:
                cert = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"INVALID/UNREADABLE: {exc}")
            return 2
        errs = validate_certificate(cert)
        if errs:
            print("INVALID -- deployment BLOCKED:")
            for e in errs:
                print("  -", e)
            return 1
        print("VALID -- certificate verifies "
              f"(compat_key {cert['compat_key'][:16]}..., cert_hash "
              f"{cert['cert_hash'][:16]}...)")
        return 0
    if mode == "schema":
        from .certificate import json_schema
        print(json.dumps(json_schema(), indent=2))
        return 0
    if mode == "check-deploy":
        from .certificate import check_deploy
        with open(args[0], "r", encoding="utf-8") as f:
            request = json.load(f)
        cert = None
        if len(args) > 1 and args[1] != "NONE":
            with open(args[1], "r", encoding="utf-8") as f:
                cert = json.load(f)
        verdict = check_deploy(request, cert)
        print(json.dumps(verdict, indent=2, sort_keys=True))
        return 0 if verdict["decision"] == "ALLOW" else 1
    print(f"unknown mode: {mode}\n{__doc__}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
