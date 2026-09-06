"""Procesa Sonido de Lapicera.mp3 (voces/, sonido real para quest_completed)
con la misma cadena "audio real" que split_pasar_pagina.py -- ver la nota
grande junto a _level_real_recording en gen_sfx.py.

BUG DE MEZCLA CORREGIDO (pedido explicito del usuario, 2026-09-02: "el de la
firma se satura el volumen muy alto"): la version anterior normalizaba por
PICO a EPIC_SFX_PEAK (0.88) -- para un click grabado con un pico muy filoso
(crest factor 9.2) eso significaba escalar TODO el clip x2.9 basandose en un
solo instante, empujando el transiente casi al maximo y volviendolo aspero
aunque la fuente en si no tenia clipping real (confirmado leyendo la forma
de onda). Nivelado por RMS + limitador suave en vez de normalizar por pico.

Uso: .venv/Scripts/python.exe tools/process_lapicera.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_sfx import _level_real_recording, _write_wav  # noqa: E402

SRC = Path(__file__).resolve().parent.parent.parent / "voces" / "Sonido de Lapicera.mp3"
OUT = Path(__file__).resolve().parent.parent / "voices" / "sfx" / "quest_completed.wav"

# Un poco mas alto que el nivel UI (es un evento raro, "completar mision"
# merece destacarse) pero lejos del 0.88 de pico que causaba la saturacion.
TARGET_RMS = 0.055
PEAK_CEILING = 0.6


def _fade(samples: np.ndarray, sr: int, fade_ms: float = 8.0) -> np.ndarray:
    n = min(int(sr * fade_ms / 1000), len(samples) // 4)
    if n <= 0:
        return samples
    out = samples.copy()
    out[:n] *= np.linspace(0, 1, n)
    out[-n:] *= np.linspace(1, 0, n)
    return out


def main() -> None:
    data, sr = sf.read(SRC)
    mono = data.mean(axis=1) if data.ndim > 1 else data
    mono = _fade(mono, sr)
    out = _level_real_recording(mono, sr, TARGET_RMS, PEAK_CEILING)
    _write_wav(OUT, out)
    print(f"[process_lapicera] {OUT} ({len(out) / sr:.2f}s)")


if __name__ == "__main__":
    main()
