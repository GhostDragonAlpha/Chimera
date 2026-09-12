"""visibility.py — the two-phase visibility layer (deliverable B).

Operator product laws implemented here (packet, verbatim intent):
  Law 1: all invisible elements should be able to be seen when put in motion —
         each motion-driving data-only plane from THE INVENTORY gets a drawn,
         nameable visible form composed OVER the engine's own pixels.
  Law 2: render visible but then render invisible again once proven working —
         each element carries the two-phase lifecycle:
             unverified -> verifying (VISIBLE for verification)
             verifying  -> proven    (reverts to INVISIBLE once its gate passes)
         and an on-screen toggle so a user can flip it deliberately either way
         (in the teaching product, turning the invisible visible IS the lesson).

ZERO C++: everything is composed in Python over the engine's public HTTP
contract (the classified routes from inventory.py). The base PNG is the
engine's own /glass bytes; overlays are drawn onto a COPY for the annotated
pane — the engine-authored bytes in the ring are never modified.

Lifecycle law (frozen PREREGISTRATION.txt P4):
  visible == user_override            if the user pinned it (True/False)
  visible == (state == "verifying")   otherwise
  gates set proven=True; a verifying element with proven=True reverts to
  "proven" (invisible) on its next evaluation — the auto-revert IS Law 2.

Gates are THIS LANE's own gates: measurable conditions on the element's data
plane (field moving, oscillators advancing, stream playing, surface readback
finite). A gate that cannot see its data stays open (element keeps its state);
a gate that passes once marks the element proven forever after (until reset).

PIL is used only by the composer and imported lazily: without it the lifecycle
and the API still work (tests run CPU-only); the annotated pane then reports
composer_unavailable instead of drawing.
"""
from __future__ import annotations

import json
import math
import struct
import threading
import time

UNVERIFIED = "unverified"
VERIFYING = "verifying"
PROVEN = "proven"


class Element:
    """One state plane's two-phase visibility lifecycle (CPU-testable)."""

    def __init__(self, name: str, plane: str, gate=None):
        self.name = name
        self.plane = plane              # the inventory route(s) it visualizes
        self.gate = gate                # callable(snapshot) -> bool
        self.proven = False
        self.state = UNVERIFIED
        self.user_override: bool | None = None
        self.snapshot: dict = {}        # last engine data fetch for this plane
        self.fetched_at: float = 0.0
        self.history: list = []         # small ring for sparklines / motion tests
        self.last_gate: dict = {}       # {"ok":bool,"detail":...,"ts":float}

    # -- the law -----------------------------------------------------------
    @property
    def visible(self) -> bool:
        if self.user_override is not None:
            return self.user_override
        return self.state == VERIFYING

    # -- transitions -------------------------------------------------------
    def engage(self) -> dict:
        """The on-screen toggle ON: start (or re-start) VERIFICATION.

        The lifecycle owns visibility from here — no pin — so the gate's
        auto-revert (Law 2) can fire. Re-engaging a proven element repeats
        the lesson: visible again, briefly, until the gate re-proves.
        """
        self.state = VERIFYING
        self.user_override = None
        return self.status()

    def hide(self) -> dict:
        """The on-screen toggle OFF: cancel verification / drop any pin."""
        if self.state == VERIFYING:
            self.state = UNVERIFIED
        self.user_override = None
        return self.status()

    def set_override(self, on: bool | None) -> dict:
        """Pin visibility open/closed independently of the lifecycle."""
        self.user_override = on
        if on is True and self.state == UNVERIFIED:
            self.state = VERIFYING      # a deliberate flip starts verification
        return self.status()

    def run_gate(self) -> dict:
        """Evaluate THIS LANE's gate against the latest snapshot."""
        if not self.snapshot.get("ok"):
            self.last_gate = {"ok": False, "ts": time.time(),
                              "detail": {"reason": "no fresh engine data "
                                                   "(gate stays open)"}}
            return dict(self.last_gate)
        try:
            ok = bool(self.gate(self)) if self.gate else False
        except Exception as e:                      # noqa: BLE001 — the error IS the record
            ok = False
            self.last_gate = {"ok": False, "ts": time.time(),
                              "detail": {"reason": f"gate error: {e}"}}
            return dict(self.last_gate)
        self.last_gate = {"ok": ok, "ts": time.time(),
                          "detail": {k: self.snapshot.get(k) for k in
                                     ("moving", "sum", "nc", "steps_total",
                                      "thetaL", "thetaR", "t", "active",
                                      "playing", "stretch_mean_pct")}}
        if ok:
            self.proven = True
            if self.state == VERIFYING and self.user_override is not True:
                self.state = PROVEN                 # THE AUTO-REVERT (Law 2)
            elif self.state == VERIFYING:
                self.state = PROVEN                 # pinned open still becomes proven
        return dict(self.last_gate)

    def reset(self) -> dict:
        self.proven = False
        self.state = UNVERIFIED
        self.user_override = None
        self.last_gate = {}
        self.history = []
        return self.status()

    def status(self) -> dict:
        return {"name": self.name, "visible": self.visible, "state": self.state,
                "proven": self.proven, "override": self.user_override,
                "plane": self.plane,
                "data_age_s": round(time.time() - self.fetched_at, 2)
                if self.fetched_at else None,
                "last_gate": self.last_gate}


# ---------------------------------------------------------------------------
# Engine data fetchers — every plane read through its classified route
# ---------------------------------------------------------------------------


def fetch_water(engine) -> dict:
    """GET /water_state -> octet-stream [u32 ns][u32 nc][i32 volumes]."""
    try:
        st, raw, ctype = engine.get("/water_state", timeout=20.0)
    except Exception as e:                          # noqa: BLE001
        return {"ok": False, "error": str(e)}
    if st != 200 or ctype.startswith("application/json"):
        return {"ok": False, "error": f"water_state http {st}"}
    if len(raw) < 8:
        return {"ok": False, "error": "short water_state body"}
    ns, nc = struct.unpack("<2I", raw[:8])
    vols = struct.unpack(f"<{nc}i", raw[8:8 + nc * 4]) if nc else ()
    total = int(sum(vols))
    wet = sum(1 for v in vols if v > 0)
    snap = {"ok": True, "ns": ns, "nc": nc, "vols": vols, "sum": total,
            "wet": wet, "vmax": max(vols) if vols else 0}
    return snap


def fetch_cpg(engine) -> dict:
    """GET /gait (the CPG's live state) + the phase ring head from /gait_state."""
    try:
        st, body, _ = engine.get("/gait")
        if st != 200:
            return {"ok": False, "error": f"gait http {st}"}
        doc = json.loads(body.decode("utf-8", "replace"))
    except Exception as e:                          # noqa: BLE001
        return {"ok": False, "error": str(e)}
    snap = {"ok": True, **doc}
    snap["moving"] = False
    if doc.get("loaded") and doc.get("on"):
        st2, raw2, ct2 = engine.get("/gait_state")
        if st2 == 200 and not ct2.startswith("application/json") and len(raw2) >= 16:
            total, cap = struct.unpack("<2Q", raw2[:16])
            snap["ring_total"] = total
            snap["ring_cap"] = cap
            if cap >= 1 and len(raw2) >= 16 + 8 * 8:
                # the newest sample is the ring's LAST row of 8 f64
                off = 16 + (cap - 1) * 8 * 8
                if off + 64 <= len(raw2):
                    snap["phase"] = list(struct.unpack("<8d", raw2[off:off + 64]))
    return snap


def fetch_stride(engine) -> dict:
    try:
        st, body, _ = engine.get("/stride")
        if st != 200:
            return {"ok": False, "error": f"stride http {st}"}
        doc = json.loads(body.decode("utf-8", "replace"))
    except Exception as e:                          # noqa: BLE001
        return {"ok": False, "error": str(e)}
    return {"ok": True, **doc}


def fetch_matter(engine) -> dict:
    try:
        st, body, _ = engine.get("/matter_state")
        if st != 200:
            return {"ok": False, "error": f"matter_state http {st}"}
        doc = json.loads(body.decode("utf-8", "replace"))
    except Exception as e:                          # noqa: BLE001
        return {"ok": False, "error": str(e)}
    return {"ok": bool(doc.get("ok")), **doc}


# ---------------------------------------------------------------------------
# This lane's gates: measurable, per plane (the "proven" flag's only writers)
# ---------------------------------------------------------------------------


def _motion_seen(el: Element, key: str) -> bool:
    """True when the keyed scalar CHANGED across the element's history.

    The bar is MEASURED MOTION, not a flicker: at least MOTION_MIN distinct
    markers must be on record — "put in motion" (Law 1) is what a gate can
    actually see, and it paces the visible phase long enough to be named.
    """
    vals = [h.get(key) for h in el.history if isinstance(h, dict)]
    vals = [v for v in vals if v is not None]
    return len(set(vals)) >= MOTION_MIN


MOTION_MIN = 4


def gate_water(el: Element) -> bool:
    return el.snapshot.get("nc", 0) > 0 and _motion_seen(el, "sum")


def gate_cpg(el: Element) -> bool:
    return bool(el.snapshot.get("loaded") and el.snapshot.get("on")
                and (el.snapshot.get("steps_total") or 0) > 0
                and _motion_seen(el, "thetaL"))


def gate_stride(el: Element) -> bool:
    return bool(el.snapshot.get("active") and el.snapshot.get("playing")
                and _motion_seen(el, "t"))


def gate_matter(el: Element) -> bool:
    v = el.snapshot.get("stretch_mean_pct")
    return v is not None and math.isfinite(v) and _motion_seen(el, "stretch_mean_pct")


FETCHERS = {"water": fetch_water, "cpg": fetch_cpg,
            "stride": fetch_stride, "matter": fetch_matter}


# ---------------------------------------------------------------------------
# The board: the four toggled elements of deliverable B
# ---------------------------------------------------------------------------


class VisibilityBoard:
    """All elements + the data-refresh cadence (one plane per refresh call)."""

    def __init__(self):
        self.elements = {
            "water": Element("water", "POST /water_bin · GET /water_state (field "
                                      "volumes) — the CA water field/body", gate_water),
            "cpg": Element("cpg", "POST /gait_bin · GET /gait + /gait_state (8 "
                                  "oscillators, cycle phase)", gate_cpg),
            "stride": Element("stride", "POST /stride_bin · GET /stride (the "
                                        "certified stride stream)", gate_stride),
            "matter": Element("matter", "POST /matter · GET /matter_state (surface "
                                        "stretch truth)", gate_matter),
        }
        self.auto_prove = True          # the lifecycle lives unless paced off
        self.lock = threading.Lock()
        self._rotate = 0

    def status(self) -> dict:
        with self.lock:
            return {"ok": True, "auto_prove": self.auto_prove,
                    "elements": [el.status() for el in self.elements.values()]}

    def refresh(self, engine, name: str) -> dict:
        """Fetch one plane's snapshot, advance its history, maybe run its gate."""
        el = self.elements[name]
        snap = FETCHERS[name](engine)
        with self.lock:
            el.snapshot = snap
            el.fetched_at = time.time()
            if snap.get("ok"):
                # history holds the motion markers the gates watch (compact)
                el.history.append({k: snap.get(k) for k in
                                   ("sum", "thetaL", "thetaR", "t",
                                    "stretch_mean_pct")})
                if len(el.history) > 24:
                    del el.history[:len(el.history) - 24]
            gate = None
            if (self.auto_prove and el.state == VERIFYING
                    and el.user_override is not False and snap.get("ok")):
                gate = el.run_gate()
        return {"element": name, "snapshot": _public(snap), "gate": gate}

    def refresh_one(self, engine) -> dict:
        """The annotated pane's cadence: rotate across visible elements first."""
        order = [n for n, el in self.elements.items() if el.visible] or \
                list(self.elements)
        name = order[self._rotate % len(order)]
        self._rotate += 1
        return self.refresh(engine, name)

    def handle_post(self, payload: dict, engine=None) -> dict:
        action = payload.get("action")
        if action == "run_gates":
            return {"ok": True,
                    "gates": {n: self.refresh(engine, n)["gate"]
                              if engine else self.elements[n].run_gate()
                              for n in self.elements}}
        if action == "auto_prove":
            self.auto_prove = bool(payload.get("on", True))
            return {"ok": True, "auto_prove": self.auto_prove}
        name = payload.get("element")
        if name not in self.elements:
            return {"ok": False, "error": f"unknown element: {name!r}"}
        el = self.elements[name]
        if action == "reset":
            return {"ok": True, "element": name, **el.reset()}
        if action == "run_gate":
            if engine is not None:
                self.refresh(engine, name)
            else:
                el.run_gate()
            return {"ok": True, "element": name, **el.status()}
        if "override" in payload:
            want = payload["override"]
            if want == "clear":
                return {"ok": True, "element": name, **el.set_override(None)}
            return {"ok": True, "element": name, **el.set_override(bool(want))}
        if "on" in payload:
            el = self.elements[name]
            return {"ok": True, "element": name,
                    **(el.engage() if payload["on"] else el.hide())}
        return {"ok": False, "error": "need element+on | element+override | "
                                      "action=run_gates|auto_prove|reset"}


def _public(snap: dict) -> dict:
    """Snapshot for the API: drop the bulky arrays, keep the numbers."""
    return {k: v for k, v in snap.items() if k not in ("vols",)}


# ---------------------------------------------------------------------------
# The composer: overlays drawn ONTO a copy of the engine's own pixels
# (nameable by form + motion, unlabeled — the judge names them, not the UI)
# ---------------------------------------------------------------------------

_WATER = (64, 158, 255)
_CPG = (255, 196, 64)
_STRIDE = (140, 255, 128)
_MATTER = (255, 96, 160)


def compose(board: VisibilityBoard, png_bytes: bytes) -> tuple[bytes, list[str]]:
    """Return (annotated_png_bytes, drawn_element_names).

    With nothing visible, the engine bytes are returned EXACTLY (and the drawn
    list is empty) — a proven board leaves the glass untouched.
    """
    drawn = [n for n, el in board.elements.items() if el.visible]
    if not drawn:
        return png_bytes, []
    try:
        from PIL import Image, ImageDraw          # lazy: CPU tests run without it
    except ImportError:
        return png_bytes, []
    import io
    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    W, H = img.size
    d = ImageDraw.Draw(img, "RGBA")
    scale = max(W / 2560.0, H / 1440.0)
    for name in drawn:
        el = board.elements[name]
        if name == "water":
            _draw_water(d, el, W, H, scale)
        elif name == "cpg":
            _draw_cpg(d, el, W, H, scale)
        elif name == "stride":
            _draw_stride(d, el, W, H, scale)
        elif name == "matter":
            _draw_matter(d, el, W, H, scale)
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue(), drawn


def _draw_water(d, el, W, H, scale):
    """The field: one column per cell band, height+brightness = volume.

    Blue columns filling and shifting as the CA steps — the shape a judge
    names without a word.
    """
    snap = el.snapshot
    vols = snap.get("vols") or ()
    nc = len(vols)
    if not nc:
        return
    band_w = max(2, int(24 * scale))
    x0, y1 = int(16 * scale), H - int(16 * scale)
    strip_h = int(H * 0.22)
    y0 = y1 - strip_h
    vmax = max(1, snap.get("vmax") or 1)
    cols = max(1, (W - 2 * x0) // band_w)
    per = max(1, (nc + cols - 1) // cols)
    d.rectangle([x0 - 3, y0 - 3, x0 + cols * band_w + 3, y1 + 3],
                fill=(8, 14, 22, 160))
    for c in range(cols):
        chunk = vols[c * per:(c + 1) * per]
        if not chunk:
            break
        m = max(chunk)
        if m <= 0:
            continue
        h = int(strip_h * min(1.0, m / vmax))
        a = 120 + int(120 * min(1.0, m / vmax))
        d.rectangle([x0 + c * band_w, y1 - h, x0 + (c + 1) * band_w - 2, y1],
                    fill=(*_WATER, a))


def _draw_cpg(d, el, W, H, scale):
    """The rhythm: two hip dials (thetaL/R needles) + the 8 oscillator phases."""
    snap = el.snapshot
    thL = float(snap.get("thetaL") or 0.0)
    thR = float(snap.get("thetaR") or 0.0)
    phase = snap.get("phase") or []
    r = int(46 * scale)
    cy = H - int(90 * scale)
    for i, th in enumerate((thL, thR)):
        cx = int(W * 0.5) + (-(2 * r + int(30 * scale)) if i == 0
                             else (2 * r + int(30 * scale)))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(*_CPG, 230),
                  width=max(2, int(3 * scale)))
        d.line([cx, cy, cx + int(0.8 * r * math.sin(th)),
                cy - int(0.8 * r * math.cos(th))], fill=(*_CPG, 255),
               width=max(2, int(4 * scale)))
    pr = max(3, int(7 * scale))
    row_w = int(150 * scale)
    base = W - int(40 * scale) - row_w
    for k in range(8):
        ph = phase[k] if k < len(phase) else 0.0
        px = base + int(row_w * k / 7.0)
        py = H - int(28 * scale)
        d.ellipse([px - pr, py - pr - int(2 * pr * math.sin(ph)),
                   px + pr, py + pr - int(2 * pr * math.sin(ph))],
                  fill=(*_CPG, 220))


def _draw_stride(d, el, W, H, scale):
    """The steps: a loop timeline with tick marks and a moving playhead."""
    snap = el.snapshot
    n = float(snap.get("n") or 0)
    dt = float(snap.get("dt") or 0.0)
    t = float(snap.get("t") or 0.0)
    loop = n * dt if n > 0 and dt > 0 else 0.0
    frac = (t % loop) / loop if loop > 0 else 0.0
    x0, x1 = int(W * 0.3), int(W * 0.7)
    y = H - int(48 * scale)
    d.rectangle([x0, y, x1, y + int(10 * scale)], fill=(14, 24, 16, 170))
    ticks = max(2, int(n // max(1.0, n / 12.0)) if n > 0 else 2)
    for k in range(ticks):
        tx = x0 + int((x1 - x0) * k / (ticks - 1))
        d.rectangle([tx - int(1.5 * scale), y - int(9 * scale),
                     tx + int(1.5 * scale), y], fill=(*_STRIDE, 210))
    px = x0 + int((x1 - x0) * frac)
    d.rectangle([px - int(3 * scale), y - int(16 * scale),
                 px + int(3 * scale), y + int(10 * scale)],
                fill=(*_STRIDE, 255))


def _draw_matter(d, el, W, H, scale):
    """The surface: a gauge + sparkline of the stretch readback."""
    snap = el.snapshot
    v = snap.get("stretch_mean_pct")
    if v is None:
        return
    gx = int(40 * scale)
    gy1 = H - int(40 * scale)
    gh = int(H * 0.25)
    gy0 = gy1 - gh
    d.rectangle([gx, gy0, gx + int(14 * scale), gy1], fill=(24, 12, 18, 170))
    frac = max(0.0, min(1.0, float(v) / 5.0))       # gauge law: 5% = full
    d.rectangle([gx, gy1 - int(gh * frac), gx + int(14 * scale), gy1],
                fill=(*_MATTER, 235))
    hist = [h.get("stretch_mean_pct") for h in el.history
            if isinstance(h.get("stretch_mean_pct"), (int, float))][-24:]
    if len(hist) >= 2:
        span_x = int(140 * scale)
        x0 = gx + int(24 * scale)
        ymax = max(max(hist), 0.5)
        pts = [(x0 + int(span_x * i / (len(hist) - 1)),
                gy1 - int(gh * min(1.0, v2 / ymax)))
               for i, v2 in enumerate(hist)]
        d.line(pts, fill=(*_MATTER, 220), width=max(2, int(2 * scale)))
