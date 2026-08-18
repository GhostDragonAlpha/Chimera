#!/usr/bin/env python3
"""
chimera_engine shim — talks to the C++ Vulkan engine over HTTP.

Usage:
    python shim.py                          # poll /state every 100 ms, print n
    python shim.py --control G=2.0 dt=0.01  # hot-reload physics params
    python shim.py --demo                   # run a short interactive demo
"""
import argparse
import json
import sys
import time
from urllib.request import urlopen, Request


ENGINE_URL = "http://localhost:8080"


def get_state() -> dict:
    """Poll /state and return the parsed JSON."""
    resp = urlopen(f"{ENGINE_URL}/state", timeout=2)
    return json.loads(resp.read().decode())


def set_params(**kwargs) -> bool:
    """POST /control with physics parameters; returns True on success."""
    body = json.dumps(kwargs).encode()
    req = Request(
        f"{ENGINE_URL}/control",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = urlopen(req, timeout=2)
        return resp.status == 200
    except Exception as e:
        print(f"  [shim] control failed: {e}", file=sys.stderr)
        return False


def poll_loop(interval_s: float = 0.1, limit: int | None = None):
    """Continuously poll /state and print particle count + first few positions."""
    n = 0
    while limit is None or n < limit:
        try:
            state = get_state()
            count = state.get("n", "?")
            particles = state.get("particles", [])
            preview = particles[:3] if particles else []
            print(
                f"[{n}] n={count}  "
                + ", ".join(f"p{i}=({p[0]:.2f},{p[1]:.2f},{p[2]:.2f})" for i, p in enumerate(preview))
            )
        except Exception as e:
            print(f"[{n}] poll error: {e}", file=sys.stderr)
        n += 1
        time.sleep(interval_s)


def demo():
    """Short interactive demo: print state, change params, show effect."""
    print("[shim] polling engine ...")
    state = get_state()
    count = state.get("n", 0)
    particles = state.get("particles", [])
    print(f"[shim] n={count}  first particle: {particles[0] if particles else 'none'}")

    # Hot-reload: double gravity
    print("[shim] setting G=2.0 ...")
    ok = set_params(G=2.0)
    print(f"[shim] control response: {'ok' if ok else 'fail'}")
    time.sleep(0.5)

    state2 = get_state()
    p2 = state2.get("particles", [])
    print(f"[shim] after G=2.0  first particle: {p2[0] if p2 else 'none'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chimera engine HTTP shim")
    parser.add_argument("--control", nargs="*", metavar="KEY=VAL",
                        help="Hot-reload physics params (e.g. G=2.0 dt=0.01)")
    parser.add_argument("--demo", action="store_true", help="Run a short interactive demo")
    parser.add_argument("--poll", action="store_true", help="Poll /state in a loop")
    parser.add_argument("--interval", type=float, default=0.1, help="Poll interval in seconds")
    parser.add_argument("--limit", type=int, default=None, help="Max polls (None = infinite)")
    args = parser.parse_args()

    if args.control:
        kwargs = {}
        for kv in args.control:
            k, v = kv.split("=", 1)
            try:
                kwargs[k.strip()] = float(v.strip())
            except ValueError:
                kwargs[k.strip()] = v.strip()
        ok = set_params(**kwargs)
        print(f"control {'ok' if ok else 'failed'}")
        sys.exit(0 if ok else 1)

    if args.demo:
        demo()
    elif args.poll:
        poll_loop(args.interval, args.limit)
    else:
        # default: one-shot state query
        try:
            state = get_state()
            print(json.dumps(state, indent=2))
        except Exception as e:
            print(f"error: {e}", file=sys.stderr)
            sys.exit(1)
