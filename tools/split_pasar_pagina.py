"""Separa Pasar Pagina.mp3 (voces/, 3 sonidos de pasar hoja reales grabados
en un solo archivo, pedido explicito del usuario 2026-09-02) en 3 clips
independientes -- deteccion por energia RMS con umbral + fusion de huecos
cortos (los "clicks" internos de un mismo riffle de papel quedan pegados,
solo el silencio real >0.5s entre sonidos distintos separa grupos).

Uso: .venv/Scripts/python.exe tools/split_pasar_pagina.py
Escribe voices/sfx/_preview/pasar_pagina_1.wav / _2.wav / _3.wav
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_sfx import _level_real_recording, _write_wav  # noqa: E402

SRC = Path(__file__).resolve().parent.parent.parent / "voces" / "Pasar Pagina.mp3"
OUT_DIR = Path(__file__).resolve().parent.parent / "voices" / "sfx" / "_preview"

# BUG DE MEZCLA CORREGIDO (pedido explicito del usuario, 2026-09-02: "se
# satura el volumen muy alto... mejora los audios por el ruido") -- estos 3
# clips son transientes muy filosos con casi todo el resto en silencio
# (crest factor 20-35, medido en esta sesion), asi que normalizar por PICO
# (como hacia antes) los dejaba con un RMS real de 0.01-0.02 -- MUY bajito
# en la practica pese a "tocar" el mismo pico nominal que los sonidos
# sintetizados. _level_real_recording nivela por RMS (volumen percibido) en
# vez de por el pico de un solo instante -- ver la nota grande en gen_sfx.py.
REAL_TARGET_RMS = 0.05
REAL_PEAK_CEILING = 0.55


def _detect_groups(mono: np.ndarray, sr: int) -> list[tuple[float, float]]:
    win = int(sr * 0.02)
    n_wins = len(mono) // win
    rms = np.array([np.sqrt(np.mean(mono[i * win : (i + 1) * win] ** 2)) for i in range(n_wins)])
    thresh = rms.max() * 0.04
    active = rms > thresh

    raw = []
    start = None
    for i, a in enumerate(active):
        if a and start is None:
            start = i
        elif not a and start is not None:
            raw.append((start, i))
            start = None
    if start is not None:
        raw.append((start, len(active)))

    merged = []
    gap_frames = int(0.5 / 0.02)
    for seg in raw:
        if merged and seg[0] - merged[-1][1] <= gap_frames:
            merged[-1] = (merged[-1][0], seg[1])
        else:
            merged.append(list(seg))

    out = []
    for s, e in merged:
        t0 = max(0.0, s * 0.02 - 0.04)
        t1 = min(len(mono) / sr, e * 0.02 + 0.12)
        out.append((t0, t1))
    return out


def _fade(samples: np.ndarray, sr: int, fade_ms: float = 8.0) -> np.ndarray:
    n = int(sr * fade_ms / 1000)
    n = min(n, len(samples) // 4)
    if n <= 0:
        return samples
    out = samples.copy()
    out[:n] *= np.linspace(0, 1, n)
    out[-n:] *= np.linspace(1, 0, n)
    return out


def main() -> None:
    data, sr = sf.read(SRC)
    mono = data.mean(axis=1) if data.ndim > 1 else data
    groups = _detect_groups(mono, sr)
    print(f"[split_pasar_pagina] {len(groups)} sonidos detectados en {SRC.name}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for i, (t0, t1) in enumerate(groups, start=1):
        clip = mono[int(t0 * sr) : int(t1 * sr)]
        clip = _fade(clip, sr)
        clip = _level_real_recording(clip, sr, REAL_TARGET_RMS, REAL_PEAK_CEILING)
        out_path = OUT_DIR / f"pasar_pagina_{i}.wav"
        _write_wav(out_path, clip)
        print(f"  [{i}] {t0:.3f}s-{t1:.3f}s ({t1 - t0:.3f}s) -> {out_path}")


if __name__ == "__main__":
    main()
