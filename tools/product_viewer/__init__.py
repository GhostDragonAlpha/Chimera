"""product-http-viewer-01 — a thin Python viewer over the frozen engine's HTTP contract.

The C++ engine is a FROZEN SERVICE (operator directive 2026-09-11): this
package writes ZERO C++ and consumes only the engine's public HTTP routes
(/glass, /frame, /camera, /cameras, /project, /joints, /joint, /scene,
/studio_chrome). Five surfaces:

  1. live view page   GET /                     (poll /glass + /frame side by side)
  2. frame gallery    GET /api/gallery          (ring buffer: timestamps + rig/clock state)
  3. snapshot GETs    GET /api/snapshot/latest  (byte-identical pass-through PNG)
                      GET /api/snapshot/<index>
  4. camera panel     GET/POST /api/camera      (named presets incl. the Python-derived
                                                full-ROM fit preset "fit_rom")
  5. movie endpoint   GET  /api/movie           (cpp_bridge.encode_movie over the ring)

Run from the repository root:  python -m tools.product_viewer --help
"""
from .server import make_server, serve_forever

__all__ = ["make_server", "serve_forever"]
