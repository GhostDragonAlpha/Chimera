"""sonify.py -- THE SOUND: a term's matter projected into PRESSURE (the twin of splat_appearance.py).

Render = matter -> light; sonify = matter -> pressure. The sound DERIVES from the term's physics via
programmed synthesis laws (numpy, CPU -- no GPU, so it never competes with the vision/ear model), it is
deterministic (seeded from the term name), and it runs on the SAME movie timeline (loopable). See
ChimeraEngine/SOUND_DESIGN.md. Judged by the operator's ear (and, advisory, an Omni audio model).

16 kHz mono -- the rate the audio encoder (Whisper feature extractor) expects.
"""
from __future__ import annotations
import wave
import zlib
from pathlib import Path

SR = 16000


def _seed(term: str) -> int:
    return zlib.crc32(term.encode("utf-8")) & 0x7FFFFFFF


def _norm(x):
    import numpy as np
    m = float(np.max(np.abs(x)))
    return x / m if m > 1e-9 else x


def _write_wav(path, sig, sr: int = SR):
    import numpy as np
    s = (np.clip(sig, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(s.tobytes())


# ── the synthesis LAWS: a term's physics -> its sound ───────────────────────────────────────────
def _theStar(dur, seed):
    """A warm G-star: granulation (turbulence) as a low RUMBLE + a convective HUM, slowly churning."""
    import numpy as np
    rng = np.random.default_rng(seed); n = int(SR * dur); t = np.arange(n) / SR
    brown = np.cumsum(rng.standard_normal(n)); brown = _norm(brown - brown.mean())   # integrated white = low rumble
    hum = 0.45 * np.sin(2 * np.pi * 55 * t) + 0.25 * np.sin(2 * np.pi * 82 * t)       # convective furnace tone
    churn = 0.7 + 0.3 * np.sin(2 * np.pi * 0.3 * t + rng.uniform(0, 6))               # slow convection swell
    return _norm((0.85 * brown + 0.5 * hum) * churn) * 0.9


def _aPlanet(dur, seed):
    """A habitable world: WIND (gusting high noise) + OCEAN (low swell) + a faint rotational sub-bass."""
    import numpy as np
    rng = np.random.default_rng(seed); n = int(SR * dur); t = np.arange(n) / SR
    white = rng.standard_normal(n)
    wind = _norm(white - np.convolve(white, np.ones(80) / 80, mode="same"))          # high-pass = airy hiss
    gust = 0.45 + 0.55 * np.abs(np.sin(2 * np.pi * 0.2 * t + rng.uniform(0, 6)))      # gusts
    swell = _norm(np.cumsum(white) - np.cumsum(white).mean())                        # low ocean swell
    subbass = 0.15 * np.sin(2 * np.pi * 30 * t)                                       # slow rotation
    return _norm(0.5 * wind * gust + 0.5 * swell + subbass) * 0.85


_LAWS = {"theStar": _theStar, "aPlanet": _aPlanet}
PHYSICS_HEARING = {
    "theStar": "a deep, warm, continuous rumble or roar -- a furnace/plasma hum; low-pitched, not shrill, not silent",
    "aPlanet": "wind and water -- a breathy, airy hiss with a low swelling undertone; a living, weather-y world",
}


def sonify(term: str, out_dir, dur: float = 4.0):
    """Write `term`'s sonification to a WAV. Returns the path, or None if the term has no soundscape."""
    law = _LAWS.get(term)
    if not law:
        return None
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    path = out / f"sound_{term}.wav"
    _write_wav(path, law(dur, _seed(term)))
    return str(path)


def sound_terms():
    return list(_LAWS)


if __name__ == "__main__":
    import sys
    term = sys.argv[1] if len(sys.argv) > 1 else "theStar"
    p = sonify(term, Path(__file__).parent / "output")
    print(f"{term}: {p}")
