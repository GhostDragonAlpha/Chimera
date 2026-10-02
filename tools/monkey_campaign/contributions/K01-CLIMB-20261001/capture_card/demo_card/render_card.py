#!/usr/bin/env python
"""Demo card capture script: deterministic synthetic renderer fixture.

Each card owns its capture script. Per-object ID constants are declared in
the card's view-spec (demo_card/view_spec.json): every object carries a flat
``mask_code`` RGB (its object-ID constant) plus a ``beauty_palette``; the
mask buffer is a SEPARATE sidecar channel, never composited into beauty.

This card's renderer plugs the template's synthetic fixture renderer into
the sidecar contract ``render_fn(view_class, frame_id, defect)``. A real
card replaces the body of ``render`` with its own renderer (engine capture,
offscreen pass, etc.) while keeping the same contract; the template audits
whatever comes out and the gate decides.

Defect injection exists ONLY to prove the normal pipeline rejects the four
planted defect classes (same classes as the VISUAL-GATE-1 suite):

- WRONG_BODY_COLOR_SHARE: leg_left renders (mask intact) but its beauty
  pixels carry leg_right's palette color. Totals stay high; co-location
  kills it.
- SHARED_COLOR_INFLATION_ABSENT: leg_left truly absent while thorax is
  painted leg_left's exact color. Totals inflate; the mask floor kills it.
- SUBJECT_ABSENT: leg_right is not rendered at all.
- UNDECLARED_OCCLUSION: the occluder covers leg_left in a class that never
  preregistered that occlusion.
"""

import json
import os
import sys

TEMPLATE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TEMPLATE_ROOT not in sys.path:
    sys.path.insert(0, TEMPLATE_ROOT)

from capture_gate import synthetic_renderer, view_spec  # noqa: E402

CARD_ID = "CAPTURE-GATE-DEMO-CARD"
CARD_ROOT = os.path.dirname(os.path.abspath(__file__))

_SPEC_CACHE = {}


def load_card_spec():
    """Load, validate and freeze the card's view-spec (per-run deep copy)."""
    cached = _SPEC_CACHE.get("spec")
    if cached is None:
        path = os.path.join(CARD_ROOT, "view_spec.json")
        with open(path, "rb") as handle:
            cached = view_spec.load_spec(json.loads(handle.read().decode("utf-8")))
        _SPEC_CACHE["spec"] = cached
    return view_spec.load_spec(cached)


def render(view_class, frame_id, defect=None):
    """Sidecar render callback: returns (beauty, mask) uint8 (h, w, 3)."""
    spec = load_card_spec()
    rendered = synthetic_renderer.render_frame(spec, view_class, defect)
    return rendered.beauty, rendered.mask
