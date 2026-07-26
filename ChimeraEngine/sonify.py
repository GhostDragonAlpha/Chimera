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


def _lowpass(x, cutoff_hz, sr: int = SR):
    """Brick-wall low-pass (FFT): keep only energy below cutoff -- e.g. a star is a PURE low rumble, no hiss."""
    import numpy as np
    X = np.fft.rfft(x)
    X[np.fft.rfftfreq(len(x), 1.0 / sr) > cutoff_hz] = 0.0
    return np.fft.irfft(X, n=len(x))


def _bandpass(x, lo_hz, hi_hz, sr: int = SR):
    """Keep energy between lo and hi -- e.g. wind lives in the mid/high band, not the sub-bass."""
    import numpy as np
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1.0 / sr)
    X[(f < lo_hz) | (f > hi_hz)] = 0.0
    return np.fft.irfft(X, n=len(x))


def _write_wav(path, sig, sr: int = SR):
    import numpy as np
    s = (np.clip(sig, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(s.tobytes())


# ── the synthesis LAWS: a term's physics -> its sound ───────────────────────────────────────────
def _theStar(dur, seed):
    """A warm G-star: granulation (turbulence) as a low RUMBLE + a convective HUM, slowly churning.
    LOW-PASSED to a pure deep rumble -- a warm star is not shrill (the ear caught a hiss; this removes it)."""
    import numpy as np
    rng = np.random.default_rng(seed); n = int(SR * dur); t = np.arange(n) / SR
    brown = np.cumsum(rng.standard_normal(n)); brown = _norm(brown - brown.mean())   # integrated white = low rumble
    hum = 0.45 * np.sin(2 * np.pi * 55 * t) + 0.25 * np.sin(2 * np.pi * 82 * t)       # convective furnace tone
    churn = 0.7 + 0.3 * np.sin(2 * np.pi * 0.3 * t + rng.uniform(0, 6))               # slow convection swell
    return _norm(_lowpass((0.85 * brown + 0.5 * hum) * churn, 170.0)) * 0.9           # <170 Hz only -> warm, not shrill


def _aPlanet(dur, seed):
    """A habitable world: WIND (airy BAND-limited hiss, gusting) + OCEAN (low swell) + a faint rotational sub-bass."""
    import numpy as np
    rng = np.random.default_rng(seed); n = int(SR * dur); t = np.arange(n) / SR
    white = rng.standard_normal(n)
    wind = _norm(_bandpass(white, 300.0, 3000.0))                                    # airy breath -- not shrill, not sub-bass
    gust = 0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 0.18 * t + rng.uniform(0, 6)))       # slow gusts
    swell = _norm(_lowpass(np.cumsum(white), 120.0))                                 # low ocean swell
    subbass = 0.12 * np.sin(2 * np.pi * 30 * t)                                       # slow rotation
    return _norm(0.55 * wind * gust + 0.45 * swell + subbass) * 0.85


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
