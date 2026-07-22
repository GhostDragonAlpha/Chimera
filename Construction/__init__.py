"""The Construction Layer — 2D authoring, deterministic 3D, direct control.

See DESIGN.md.  A renderer-agnostic scene model (scene.py) is projected by two
backends: the ParticleEngine GPU splat renderer (backend_3d.py, the product
surface) and an HTML canvas (backend_html.py, the development surface).  The
'tree' construction operator (tree.py) is the first worked example.
"""
