"""eye_control.py — THE EYE'S POWER SWITCH (operator decree, 2026-09-02).

"we have to have commands to load and unload the model because you have to
just call it with a command request also the model is very very slow so you
have to wait a long long time and timeout should be disabled I will decide
if we need to start over"

Three decrees, implemented verbatim:
  1. COMMANDS to load/unload the eye — `python ChimeraEngine/eye_control.py
     load|unload|status` — the CLI the operator asked for. The load call also
     runs on-demand from inside senses.py when the eye is found dark: a read
     on a dark eye loads the decreed model (at the decree's context) instead
     of failing. "You have to just call it with a command request."
  2. TIMEOUT DISABLED — no read is ever cut off by a transport clock again.
     The wait is unbounded (urllib timeout=None = wait forever). The operator
     decides when to start over, not a socket.
  3. The operator owns restarts — unload exists precisely so THEY can order
     a fresh start; nothing here auto-unloads, ever.

CONTEXT LAW (derived, not chosen): the operator loads full context ("it likes
to be full all the time"). EYE_CONTEXT below is the floor used by the
on-demand path when NOTHING is loaded and the operator's full-context config
is unknown — 32,000 (what their last full load produced). If the operator
prefers another size they load it themselves; the on-demand path only fills
the dark-eye gap.

Usage:
  python ChimeraEngine/eye_control.py status
  python ChimeraEngine/eye_control.py load    [--context N]
  python ChimeraEngine/eye_control.py unload
"""
import json
import subprocess
import sys
import time
import urllib.request

LMSTUDIO_URL = "http://localhost:1234"
EYE_MODEL = "qwen3.8-27b-nvfp4-mtp"       # the DEFAULT eye (2026-09-02 decree);
                                          # the CLI load command accepts an explicit
                                          # model argument, and the senses on-demand
                                          # path always passes what it resolved
                                          # (pin > loaded > default) — see the
                                          # 2026-09-03 wrong-model incident: a
                                          # hardcoded load target is an eviction
                                          # gun pointed at the operator's choice.
EYE_CONTEXT_FLOOR = 60000                # the operator's 60k token budget


def _lms(*args, timeout_s: float = None) -> tuple[int, str]:
    """lms CLI, unbounded by default (decree 2: no transport clocks on the eye)."""
    cmd = ["lms", *args]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
    return p.returncode, (p.stdout + p.stderr)


def status(model: str = None) -> dict:
    try:
        req = urllib.request.Request(LMSTUDIO_URL + "/api/v0/models")
        with urllib.request.urlopen(req, timeout=15) as r:
            models = json.load(r).get("data", [])
    except Exception as e:
        return {"server": "DOWN", "error": str(e)[:120]}
    eye_id = model or EYE_MODEL
    eye = next((m for m in models if m.get("id") == eye_id), None)
    loaded = [m for m in models if m.get("state") == "loaded"]
    return {"server": "UP",
            "eye": eye_id,
            "eye_state": (eye or {}).get("state", "absent"),
            "eye_type": (eye or {}).get("type"),
            "loaded": [m.get("id") for m in loaded]}


def load(context: int = None, model: str = None) -> dict:
    """Load an eye. Waits FOREVER (decree 2). Context: operator's flag wins;
    default = the measured full-context floor. Model: explicit argument wins;
    default = EYE_MODEL. REFUSES to load over a different resident model —
    lms load can evict the operator's choice (measured 2026-09-03), so an
    eviction is the OPERATOR's unload + load, never an automatic one."""
    target = model or EYE_MODEL
    ctx = context or EYE_CONTEXT_FLOOR
    st = status()
    if st.get("eye_state") == "loaded":
        return {"ok": True, "already": True, "status": st}
    resident = st.get("loaded") or []
    if resident and target not in resident:
        return {"ok": False, "refused": True,
                "reason": f"{resident} is resident; loading {target} could evict it. "
                          f"Unload first (operator's call), or clear the pin so the "
                          f"dyad follows the loaded model.", "status": st}
    print(f"loading {target} (context {ctx}) — no timeout, this can take a while ...",
          flush=True)
    rc, out = _lms("load", target, "--gpu", "max", "--context-length", str(ctx))
    # the CLI can print a resource-guardrail warning yet succeed (measured:
    # "requires ~99.59 GB" while the load completes at 101 GB resident)
    st2 = status()
    ok = st2.get("eye_state") == "loaded" if target == EYE_MODEL else target in (st2.get("loaded") or [])
    return {"ok": ok, "rc": rc, "cli_tail": out.strip().splitlines()[-3:],
            "status": st2}


def unload() -> dict:
    """Operator-ordered restart. Nothing auto-calls this."""
    rc, out = _lms("unload", EYE_MODEL)
    time.sleep(2.0)
    return {"ok": status().get("eye_state") != "loaded", "rc": rc, "cli_tail": out.strip().splitlines()[-2:]}


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    ctx = None
    if "--context" in sys.argv:
        ctx = int(sys.argv[sys.argv.index("--context") + 1])
    mdl = None
    if "--model" in sys.argv:
        mdl = sys.argv[sys.argv.index("--model") + 1]
    if cmd == "status":
        print(json.dumps(status(mdl), indent=1))
    elif cmd == "load":
        print(json.dumps(load(ctx, mdl), indent=1))
    elif cmd == "unload":
        # unload takes an optional model; bare "unload" means the DEFAULT eye
        target = mdl or EYE_MODEL
        rc, out = _lms("unload", target)
        time.sleep(2.0)
        print(json.dumps({"ok": status(target).get("eye_state") != "loaded",
                          "rc": rc, "cli_tail": out.strip().splitlines()[-2:]}, indent=1))
    else:
        print(__doc__)
        sys.exit(1)
