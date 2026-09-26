"""implementation.py -- R5-forest-review-FOLLOWUP: scene-readiness smoke-test
runner.

Mechanizes the accepted R5 corrected verdict's readiness gate over ONLY the
documented slice runtime endpoints (slice_server.py: /api/health, /api/status,
/tick_state, /tick_touch, /tick_gravity -- cited in PREREGISTRATION.md). The
transport is INJECTED (an urllib transport class is provided for live use;
CPU tests use fakes; this card starts no engine).

LAWS:
  - documented endpoints only: every probe goes through the configured
    endpoint set; the request log is part of the verdict;
  - bounded: every request carries the configured timeout;
  - named failures: engine_unavailable, health_unhealthy, scene_identity_
    mismatch, native_collision_route_missing, walking_open;
  - the collision capability check consumes the accepted negative finding
    (the documented HTTP contract has NO collision query route); a configured
    non-empty route list probes it -- nothing is invented;
  - a fixture transport is labeled in every output and can NEVER yield a
    native-acceptance claim: fixture READY still requires a controlled native
    run + visual capture (stated in the verdict itself).

Verdict: READY | NOT_READY with findings[].
"""
from __future__ import annotations

import argparse
import json
import pathlib
import time
import urllib.error
import urllib.request

DOCUMENTED_ENDPOINTS = ("/api/health", "/api/status", "/tick_state",
                       "/tick_touch", "/tick_gravity")   # slice_server.py cites

SCHEMA = "r5-followup.scene_readiness.v1"


class UrllibTransport:
    """Live transport (GET/POST JSON with a bounded timeout). Not exercised
    by this card's tests -- a live engine is out of scope here."""

    def __init__(self, base_url, timeout_s=5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_s = float(timeout_s)

    def request(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            self.base_url + path, data=data, method=method,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))


class ReadinessRunner:
    def __init__(self, config, transport, transport_label="injected-fixture"):
        self.config = config
        self.transport = transport
        self.transport_label = transport_label
        self.requests = []
        # documented set = the five cited routes plus any EXPLICITLY declared
        # future contract additions; probing anything else is refused
        self.documented = DOCUMENTED_ENDPOINTS + tuple(
            config.get("extra_documented_endpoints", ()))

    def _request(self, method, path, body=None):
        if path not in self.documented:
            raise ValueError("endpoint_not_documented %r (invention refused)" % path)
        self.requests.append((method, path))
        return self.transport.request(method, path, body)

    def run(self) -> dict:
        cfg = self.config
        findings = []
        started = time.monotonic()

        def finding(code, **detail):
            findings.append({"code": code, **detail})

        # 1. engine availability (documented health route)
        health = None
        try:
            status, health = self._request("GET", cfg.get("health_path",
                                                          "/api/health"))
        except Exception as exc:                          # noqa: BLE001
            finding("engine_unavailable", error=type(exc).__name__,
                    detail=str(exc)[:200])
            health = None
        if health is not None:
            for field, expected in (cfg.get("expected_health") or {}).items():
                if health.get(field) != expected:
                    finding("health_unhealthy", field=field,
                            expected=expected, served=health.get(field))

        # 2. scene/build identity (documented status route; configurable field)
        if health is not None and cfg.get("scene_identity"):
            ident = cfg["scene_identity"]
            try:
                _, served_status = self._request("GET", "/api/status")
                served = served_status.get(ident["field"])
                if served != ident["expected"]:
                    finding("scene_identity_mismatch", field=ident["field"],
                            expected=ident["expected"], served=served)
                else:
                    self.scene_served = served
            except Exception as exc:                      # noqa: BLE001
                finding("engine_unavailable", error=type(exc).__name__,
                        detail="status route: " + str(exc)[:160])

        # 3. native collision capability: the accepted negative finding, or a
        #    probe of a DOCUMENTED route if the contract ever gains one
        routes = cfg.get("collision_routes", [])
        if not routes:
            finding("native_collision_route_missing",
                    detail="the documented HTTP contract has no collision "
                           "query route (accepted R5/D-FOREST negative "
                           "finding); native heightfield/trunk contact is "
                           "absent on the current engine")
        else:
            probed = False
            for path in routes:
                try:
                    status, payload = self._request("GET", path)
                    if status == 200 and payload:
                        probed = True
                except Exception:                          # noqa: BLE001
                    continue
            if not probed:
                finding("native_collision_route_missing",
                        detail="configured collision routes did not answer",
                        routes=list(routes))

        # 4. walking prerequisite (process fact, not a transport probe)
        if cfg.get("walking_prerequisites_open", True):
            finding("walking_open",
                    detail="trained walking W05-W09 and in-scene walking/"
                           "camera acceptance remain open (accepted R5 "
                           "verdict); scene readiness cannot precede them")

        ready = not findings
        verdict = {
            "schema": SCHEMA,
            "verdict": "READY" if ready else "NOT_READY",
            "transport": self.transport_label,
            "native_acceptance": False,
            "note": ("A READY verdict under transport=%s is NOT native "
                     "acceptance: a controlled native run plus visual capture "
                     "remains required (card falsifier)." %
                     self.transport_label),
            "findings": findings,
            "requests": list(self.requests),
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "pinned_scene_identities": self.config.get("pinned_scene_identities"),
        }
        return verdict


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--base-url", default=None,
                    help="live transport base URL (omit for dry self-check)")
    args = ap.parse_args(argv)
    config = json.loads(pathlib.Path(args.config).read_text(encoding="utf-8"))
    if args.base_url:
        transport = UrllibTransport(args.base_url, config.get("timeout_s", 5.0))
        label = "live-urllib"
    else:
        raise SystemExit("no transport injected: pass --base-url for a live run "
                         "(CPU regression uses the injected fakes in tests)")
    verdict = ReadinessRunner(config, transport, label).run()
    print(json.dumps(verdict, indent=1))
    return 0 if verdict["verdict"] == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
