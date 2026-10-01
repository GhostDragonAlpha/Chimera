# PREREGISTRATION ADDENDUM 1 — MAT2-W05 pin correction (before any experiment)

Dated: before the first executor run; nothing has been measured yet. The
preregistration (`PREREGISTRATION.md`, sha
`260c6d53e66c79689e95b5f880c1f6828f5316d4d7d6e172132296137d3f1c2a`) stands
except where corrected here. Every receipt binds BOTH the preregistration
sha256 and this addendum's sha256; `verify_inputs.py` refuses on any drift
from either document's declared pins.

## Correction: W04 freeze-manifest pin (prereg section 1, entry 18)

- WRITTEN: `w04_freeze_manifest.json` expected
  `07f05bfa982e066ae67413b04e3367c5ad7570830e99fc32edcb86cbe8d87598`.
- VERIFIED ON DISK (sha256sum, this attempt start):
  `be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29`.
- CAUSE (honest): the written value is the W04 CERTIFICATE's sha256 — the
  freeze manifest itself records it as its `certificate_sha256` field. The
  two store artifacts were transposed in the prereg pin table. The same
  verification pass then caught the paired error: the prereg's
  `w04_certificate.json` entry carried the certificate's INTERNAL `cert_hash`
  (`4b306f4f66f100335276fdc79f1e201aaccacc65ce7303f65183ea46d283f76b`)
  instead of the file's sha256; the corrected pair above is authoritative
  for both artifacts.
- CORRECTED PINS (both verified byte-exact on disk, this attempt):
  - `E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-W04/numerical/w04_freeze_manifest.json`
    = `be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29`
  - `E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-W04/numerical/w04_certificate.json`
    = `07f05bfa982e066ae67413b04e3367c5ad7570830e99fc32edcb86cbe8d87598`
- No runbook value, seed, trainer constant, prediction, falsifier arm,
  termination law or resource bound changes. This addendum corrects one
  transcription in the pin table only.

All other section-1 pins verified byte-exact as written (the executor's pin
verifier ran and refused on exactly this one entry — the falsifier worked).
