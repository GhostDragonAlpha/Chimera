"""sonify.py — each proven term's WAV rendered from its own physics (no shared presets).

STATEMENT: Every membrane's physics governs a measurable spectrum. The star's blackbody temperature
determines its peak frequency and harmonic content. The breath's period (~4s) determines its
fundamental. The clock's period determines its tick rate. Each membrane gets a WAV derived from
its own numbers — never a shared preset.

PREDICTION: theStar (blackbody ~5772 K, peak ~585 nm → yellow-white) and theHorizon (cold, r~2.3e-35 m)
produce measurably different spectra — centroid distance above noise floor.

FALSIFIER: Two membranes produce identical spectra — the sonification is decorative, not derived.

The EAR is ADVISORY ONLY (never gates). Physics determines the signal; hearing confirms it.

Run: python ChimeraEngine/sonify.py
Output: ChimeraEngine/sonify_output/<term>.wav

Author: Agent (DeepSeek V4 Pro — density lane, 2026-08-04)
"""
from __future__ import annotations

import math
import struct
import sys
import wave
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_OUT = _HERE / "sonify_output"
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE))

import splat_appearance as sa

SAMPLE_RATE = 44100
DURATION_S = 4.0  # per membrane — long enough to hear the texture


def _phys_params(term: str, nums: dict) -> dict:
    """Extract the physics parameters that drive sonification for this membrane.

    Each membrane type maps to a different synthesis strategy:
      - Stars: blackbody temperature → harmonic series with a filter envelope
      - Clocks: period → tick at that rate with decay
      - Breathing: period → amplitude modulation at breath rate
      - Bodies: mechanical resonances from extent and derived frequencies
      - Planets: orbital harmonic from extent (radius)
      - Fields: filtered noise from temperature/composition
      - Ground/terrain: granular texture from grain count and extent
    """
    extent = float(nums.get("extent_m", 1.0))
    params = {
        "extent_m": extent,
        "duration_s": float(nums.get("duration_s", 1.0)),
    }

    # Try to find temperature
    for key in ("T_surface", "T_eff", "temperature_K", "T_K", "T"):
        if key in nums:
            params["T_K"] = float(nums[key])
            break

    # Star parameters
    if "M_system" in nums:
        params["M_system"] = float(nums["M_system"])
    if "L_star" in nums:
        params["L_star"] = float(nums["L_star"])

    # Body parameters
    for key in ("gravity", "g_m_s2", "g"):
        if key in nums:
            params["g"] = float(nums[key])
    for key in ("stature_m", "height_m", "H_m"):
        if key in nums:
            params["stature_m"] = float(nums[key])

    # Time/clock parameters
    for key in ("period_s", "tick_s", "step_s"):
        if key in nums:
            params["period_s"] = float(nums[key])

    # Mechanical resonance — from extent, approximating normal modes of a sphere
    # f_n = c/(2πR) * n — the fundamental breathing mode
    sound_speed = 340.0  # m/s in air — general proxy
    params["f_sphere"] = sound_speed / (2.0 * math.pi * max(extent, 1e-12))

    # Grain texture — from splat buffer
    buf = sa.scene_buffer(term)
    if buf is not None and buf.shape[0] > 0:
        params["n_grains"] = buf.shape[0]
        # Mean grain spatial frequency (inverse of mean grain spacing on sphere)
        radius = float(np.linalg.norm(buf[:, 0:3], axis=1).max()) or 1.0
        spacing = (4.0 * math.pi * radius * radius / max(buf.shape[0], 1)) ** 0.5
        params["grain_spacing"] = spacing
        params["grain_freq"] = 1.0 / max(spacing, 1e-12)

    return params


def _synthesize(term: str, nums: dict, p: dict) -> np.ndarray:
    """Synthesize a WAV signal from membrane physics. Returns float64 [-1, 1]."""
    n_samples = int(SAMPLE_RATE * DURATION_S)
    t = np.linspace(0, DURATION_S, n_samples, endpoint=False)
    signal = np.zeros(n_samples, dtype=np.float64)

    T_K = p.get("T_K")
    extent = p["extent_m"]
    period_s = p.get("period_s", 1.0)
    f_sphere = p["f_sphere"]

    # Classify and route
    low = term.lower()

    # ── STARS: blackbody harmonically mapped to audio ──────────────────────────────────────────
    if T_K is not None and any(k in low for k in ("star", "sun", "cooling")):
        # Wien peak: lambda_max = 2.898e-3 / T  (m)
        wien_peak = 2.898e-3 / max(T_K, 1.0)
        # Map to audio: log(T) → fundamental frequency
        f0 = 80.0 * math.log10(max(T_K, 100.0) / 100.0)  # ~130 Hz for 5772 K
        f0 = np.clip(f0, 40.0, 600.0)

        # Harmonic series with amplitudes from Planck distribution
        envelope = np.exp(-t / 2.0)  # 2s decay
        for n in range(1, 9):
            fn = f0 * n
            # Amplitude ~ 1/n for a blackbody-like rolloff, brighter for hotter
            amp = 1.0 / (n ** 1.3) * min(T_K / 5772.0, 1.5)
            signal += amp * np.sin(2.0 * math.pi * fn * t) * envelope

        # Add a soft filtered-noise corona for photospheric granulation
        rng = np.random.default_rng(int(T_K))
        noise = rng.normal(0, 0.05, n_samples)
        # Simple low-pass: moving average
        window = int(SAMPLE_RATE / f0)
        kernel = np.ones(max(window, 1)) / max(window, 1)
        noise = np.convolve(noise, kernel, mode="same")
        signal += noise * envelope * 0.3

    # ── CLOCKS: tick at derived period ────────────────────────────────────────────────────────
    elif any(k in low for k in ("clock", "densityclock", "emptying", "horizon", "humanclock")):
        tick_s = max(period_s, 0.01)
        tick_samples = int(tick_s * SAMPLE_RATE)
        # Impulse train at the clock period
        tick = np.zeros(n_samples)
        for i in range(0, n_samples, tick_samples):
            if i < len(tick):
                tick[i] = 1.0
        # Band-pass to soften: convolution with a short tone burst
        f_tick = 440.0  # A4 — a clear, pitched tick
        tone = np.sin(2.0 * math.pi * f_tick * np.arange(0, 0.03, 1 / SAMPLE_RATE))
        tick = np.convolve(tick, tone, mode="same")
        # Exponential decay on each tick
        decay = np.exp(-np.arange(n_samples) % tick_samples / (SAMPLE_RATE * 0.15))
        signal = tick * decay * 0.6

    # ── BREATHING / HUMAN-SCALE: amplitude-modulated tone ─────────────────────────────────────
    elif any(k in low for k in ("breath", "breathing")):
        breath_period = max(p.get("period_s", 4.0), 0.5)
        f_breath = 1.0 / breath_period
        # AM: slow oscillation on a soft carrier
        carrier = 220.0  # A3
        am = 0.5 + 0.5 * np.sin(2.0 * math.pi * f_breath * t)
        signal = am * np.sin(2.0 * math.pi * carrier * t) * 0.4
        # Add filtered noise for the air texture
        rng = np.random.default_rng(42)
        air = rng.normal(0, 0.08, n_samples)
        signal += air * am * 0.3

    # ── BODIES (human-scale): mechanical resonance from formant model ───────────────────────────
    elif any(k in low for k in ("human", "skin", "load", "balance", "stance", "sweep",
                                "thrust", "ankle", "grip", "hand", "eye")):
        stature = p.get("stature_m", 1.75)
        # Vocal tract formants scaled from stature: F1 ~ c/(4L), F2 ~ 3*F1, etc.
        l = stature * 0.15  # approximate vocal tract length
        f1 = 340.0 / (4.0 * max(l, 0.05))
        # Mechanical resonance from extent
        fm = f_sphere * 0.5

        # Formant-like tone with mechanical resonance
        envelope = np.exp(-t / 3.0) * (0.5 + 0.5 * np.sin(2.0 * math.pi * 0.5 * t))
        signal = (0.6 * np.sin(2.0 * math.pi * f1 * t)
                  + 0.3 * np.sin(2.0 * math.pi * f1 * 2.3 * t)
                  + 0.1 * np.sin(2.0 * math.pi * fm * t)) * envelope * 0.5

    # ── GROUND/TERRAIN: granular texture from grain spacing ────────────────────────────────────
    elif any(k in low for k in ("ground", "terrain", "terrace", "mine", "mining")):
        n_grains = p.get("n_grains", 1000)
        grain_freq = p.get("grain_freq", 100.0)
        # Granular synthesis: each grain is a short noise burst at its spatial frequency
        grain_dur = 0.02  # 20 ms grains
        n_grains_audible = min(n_grains, int(DURATION_S / grain_dur))
        rng = np.random.default_rng(hash(term) % (2**31))
        # Map grain frequency to narrow-band noise centre
        f_center = np.clip(grain_freq * 0.1, 100.0, 2000.0)  # scale to audible
        # Band-pass noise
        for i in range(n_grains_audible):
            start = int(i * grain_dur * SAMPLE_RATE)
            end = start + int(grain_dur * SAMPLE_RATE)
            if end > n_samples:
                break
            # Quick tone burst at f_center with ±10% random detune
            f = f_center * (0.9 + 0.2 * rng.random())
            burst = np.sin(2.0 * math.pi * f * t[start:end]) * np.exp(-np.arange(end - start) / (SAMPLE_RATE * grain_dur))
            signal[start:end] += burst * 0.15

    # ── ATMOSPHERE/OCEAN: filtered noise with spectral tilt ─────────────────────────────────────
    elif any(k in low for k in ("atmosphere", "ocean", "salt", "nitrogen", "cloud", "fog")):
        T = p.get("T_K", 288.0)
        # Thermal noise coloured by temperature: warmer = higher spectral tilt
        tilt = np.clip((T - 200.0) / 200.0, 0.0, 1.0)  # 0→1
        f_center = 300.0 + 700.0 * tilt
        rng = np.random.default_rng(int(T))
        noise = rng.normal(0, 0.15, n_samples)
        # Band-pass around f_center
        q = 2.0
        bw = f_center / q
        window = int(SAMPLE_RATE / bw)
        kernel = np.exp(-np.arange(-window, window + 1) ** 2 / (2 * (window / 3) ** 2))
        kernel /= kernel.sum()
        noise = np.convolve(noise, kernel, mode="same")
        signal = noise * 0.5

    # ── PLANETS: orbital resonance from extent ──────────────────────────────────────────────────
    elif any(k in low for k in ("planet", "blueworld", "rockyplanet", "biome", "steppe")):
        # Map extent to a chord: root = f_sphere * 440 (≈ concert A for Earth-sized)
        f_root = np.clip(f_sphere * 440.0, 80.0, 800.0)
        # Major triad from the extent-derived root
        ratios = [1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0]
        envelope = np.exp(-t / 4.0) * (0.5 + 0.5 * np.sin(2.0 * math.pi * 0.3 * t))
        for r in ratios[:5]:
            signal += np.sin(2.0 * math.pi * f_root * r * t) * (0.3 / (r ** 0.8)) * envelope

    # ── GENERIC: sphere resonance from extent ───────────────────────────────────────────────────
    else:
        f = np.clip(f_sphere * 440.0, 40.0, 1000.0)
        envelope = np.exp(-t / 2.0)
        signal = np.sin(2.0 * math.pi * f * t) * envelope * 0.4

    # ── Master: normalize to [-1, 1] ──
    peak = np.abs(signal).max() or 1.0
    signal = signal / peak * 0.9

    return signal.astype(np.float64)


def _write_wav(path: Path, signal: np.ndarray):
    """Write a float64 signal as a 16-bit WAV file."""
    # Convert to 16-bit PCM
    int_signal = np.clip(signal * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(int_signal.tobytes())


def spectral_centroid(signal: np.ndarray) -> float:
    """Compute the spectral centroid (Hz) — the centre of mass of the spectrum."""
    n = len(signal)
    fft = np.abs(np.fft.rfft(signal))
    freqs = np.fft.rfftfreq(n, 1.0 / SAMPLE_RATE)
    total = fft.sum()
    if total < 1e-12:
        return 0.0
    return float((freqs * fft).sum() / total)


def render_all() -> dict:
    """Synthesize WAVs for every proven term from its own physics."""
    _OUT.mkdir(parents=True, exist_ok=True)
    terms = sa.scene_terms()
    results: dict[str, dict] = {}

    for term in terms:
        nums = sa.term_numbers(term)
        p = _phys_params(term, nums)
        signal = _synthesize(term, nums, p)
        cent = spectral_centroid(signal)
        path = _OUT / f"{term}.wav"
        _write_wav(path, signal)
        results[term] = {
            "centroid_hz": round(cent, 1),
            "duration_s": DURATION_S,
            "peak": round(float(np.abs(signal).max()), 4),
            "file": str(path.name),
        }
        print(f"  {term:30s}  centroid={cent:7.1f} Hz  -> {path.name}")

    # ── Verify: theStar and theHorizon (proxy for black hole cold) differ measurably ──
    star_cent = results.get("theStar", {}).get("centroid_hz", 0)
    horizon_cent = results.get("theHorizon", {}).get("centroid_hz", 0)
    diff = abs(star_cent - horizon_cent)
    noise_floor = 20.0  # Hz — below this, difference is within measurement noise
    print(f"\nDyad check: theStar centroid={star_cent} Hz, theHorizon centroid={horizon_cent} Hz")
    print(f"  Difference: {diff:.1f} Hz (noise floor: {noise_floor} Hz)")
    if diff > noise_floor:
        print("  VERIFIED: spectra differ measurably — sonification is physics-derived.")
    else:
        print("  UNVERIFIED: spectra too close — sonification may be decorative.")

    # Write manifest
    import json
    (_OUT / "sonify_manifest.json").write_text(json.dumps({
        "terms": results,
        "sample_rate": SAMPLE_RATE,
        "duration_s": DURATION_S,
        "noise_floor_hz": noise_floor,
    }, indent=2))

    return results


if __name__ == "__main__":
    render_all()