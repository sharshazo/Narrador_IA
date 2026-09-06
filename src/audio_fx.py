"""Procesamiento de audio para la voz del narrador -- separado de tts.py
(que solo orquesta sintesis/cola) para que build_intro_narration.py y
build_motivational_clips.py compartan el mismo efecto sin duplicar codigo.
"""
from __future__ import annotations

import numpy as np


def low_shelf_boost(samples: np.ndarray, sr: int, freq: float = 150.0, gain_db: float = 6.0, slope: float = 1.0) -> np.ndarray:
    """Realce de graves tipo shelf (formula RBJ Audio EQ Cookbook): sube
    parejo todo lo que esta POR DEBAJO de `freq` en `gain_db`, sin tocar
    agudos -- pedido explicito del usuario 2026-09-05: "agregale bajos,
    dandole efecto a la narracion" (mas cuerpo/presencia grave, look de
    trailer cinematico, sin ensuciar la inteligibilidad de la voz)."""
    A = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * freq / sr
    cos_w0 = np.cos(w0)
    sin_w0 = np.sin(w0)
    alpha = sin_w0 / 2 * np.sqrt((A + 1 / A) * (1 / slope - 1) + 2)
    sqrt_a = np.sqrt(A)

    b0 = A * ((A + 1) - (A - 1) * cos_w0 + 2 * sqrt_a * alpha)
    b1 = 2 * A * ((A - 1) - (A + 1) * cos_w0)
    b2 = A * ((A + 1) - (A - 1) * cos_w0 - 2 * sqrt_a * alpha)
    a0 = (A + 1) + (A - 1) * cos_w0 + 2 * sqrt_a * alpha
    a1 = -2 * ((A - 1) + (A + 1) * cos_w0)
    a2 = (A + 1) + (A - 1) * cos_w0 - 2 * sqrt_a * alpha

    from scipy.signal import lfilter

    b = np.array([b0, b1, b2]) / a0
    a = np.array([1.0, a1 / a0, a2 / a0])
    return lfilter(b, a, samples).astype(np.float32)


def apply_narrator_fx(samples: np.ndarray, sr: int) -> np.ndarray:
    """Cadena de efectos aplicada a toda narracion pre-generada del
    narrador (intro y clips motivacionales). Un solo lugar para ajustar el
    "sonido" del narrador sin tocar cada script de generacion."""
    return low_shelf_boost(samples, sr, freq=150.0, gain_db=6.0, slope=1.0)


def loop_to_length(samples: np.ndarray, sr: int, target_len: int, crossfade_s: float = 1.5) -> np.ndarray:
    """Repite `samples` (loopeandolo con crossfade, sin corte audible en la
    union) hasta cubrir `target_len` muestras -- para estirar una pista
    musical corta (ej. 30s, el maximo de una sola llamada a la API) hasta
    la duracion real de cada narracion (~55-65s)."""
    if len(samples) >= target_len:
        return samples[:target_len]

    crossfade_n = min(int(sr * crossfade_s), len(samples) // 4)
    fade_out = np.linspace(1.0, 0.0, crossfade_n)
    fade_in = np.linspace(0.0, 1.0, crossfade_n)

    out = samples.copy()
    while len(out) < target_len:
        tail = out[-crossfade_n:] * fade_out
        head = samples[:crossfade_n] * fade_in
        blended = tail + head
        out = np.concatenate([out[:-crossfade_n], blended, samples[crossfade_n:]])
    return out[:target_len]


def _smoothstep(n: int) -> np.ndarray:
    """Curva 0->1 sin quiebres en las puntas (derivada cero en ambos
    extremos) -- a diferencia de una rampa lineal, no se percibe un
    arranque/corte brusco de volumen."""
    t = np.linspace(0.0, 1.0, n, dtype=np.float32)
    return 3 * t**2 - 2 * t**3


def _music_envelope(n: int, sr: int, music_level: float, swell_level: float, rise_s: float, duck_s: float) -> np.ndarray:
    """Construye el sobre de volumen de la musica en 2 etapas simetricas al
    principio y al final -- pedido explicito del usuario ("que la musica no
    suene de golpe... que inicie suave... y lo mismo al final"):
      1) rise_s: desde silencio absoluto hasta el pico "swell" (entrada de
         apertura cinematica), con curva suave, no lineal.
      2) duck_s: desde el pico hasta el nivel bajo ("ducking") con el que
         la musica queda de fondo mientras habla el narrador.
    Simetrico en la cola: del nivel bajo sube al pico y de ahi baja a
    silencio absoluto, nunca corta de golpe."""
    rise_n = min(int(sr * rise_s), n // 6) if n > 0 else 0
    duck_n = min(int(sr * duck_s), n // 6) if n > 0 else 0

    envelope = np.full(n, music_level, dtype=np.float32)
    if rise_n > 0:
        envelope[:rise_n] = swell_level * _smoothstep(rise_n)
        envelope[-rise_n:] = swell_level * _smoothstep(rise_n)[::-1]
    if duck_n > 0:
        start = rise_n
        envelope[start:start + duck_n] = swell_level - (swell_level - music_level) * _smoothstep(duck_n)
        end = n - rise_n
        envelope[end - duck_n:end] = music_level + (swell_level - music_level) * _smoothstep(duck_n)
    return envelope


def mix_with_ducked_music(
    voice: np.ndarray,
    music: np.ndarray,
    sr: int,
    music_level: float = 0.14,
    swell_level: float = 0.45,
    rise_s: float = 3.0,
    duck_s: float = 2.5,
) -> np.ndarray:
    """Mezcla la voz (nivel completo) con una cama musical de fondo: la
    musica aparece desde silencio con una entrada suave ("swell" cinematico
    de apertura), baja ("ducking") mientras habla el narrador para no
    competir con la voz, y al final vuelve a subir y se apaga hacia
    silencio con la misma suavidad -- nunca arranca ni corta de golpe."""
    music = loop_to_length(music, sr, len(voice))
    envelope = _music_envelope(len(voice), sr, music_level, swell_level, rise_s, duck_s)

    mixed = voice + music * envelope
    peak = np.abs(mixed).max()
    if peak > 0.98:
        mixed = mixed * (0.98 / peak)
    return mixed.astype(np.float32)
