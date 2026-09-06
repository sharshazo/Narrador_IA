"""Genera VARIANTES de 2 sonidos nuevos pedidos por el usuario (2026-09-02):
1. "window_open" con sonido de pagina de libro cambiando (reemplaza el
   swoosh+tono generico que tenia antes).
2. Un sonido nuevo de "escribiendo/pluma sobre el libro" para cuando se abre
   la ventana de mision nueva / se activa una mision (reemplaza el rol que
   hoy cumple parchment_open en ese momento especifico).

Esto es un script de PREVIEW/eleccion, no toca voices/sfx/ (los archivos
"oficiales" que ya usa el addon) -- escribe a una carpeta aparte para que el
usuario escuche opciones antes de decidir cual queda. Reusa los helpers de
gen_sfx.py (misma tecnica de sintesis, mismo nivel de volumen UI_SFX_PEAK)
en vez de duplicarlos.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_sfx import SR, UI_SFX_PEAK, _bandpassed_noise, _envelope, _noise_hit, _normalize_peak, _write_wav  # noqa: E402

PREVIEW_DIR = Path(__file__).resolve().parent.parent / "voices" / "sfx" / "_preview"


# ===== Opciones para "window_open" (cambiar hoja de libro) =====

def flip_A_single() -> np.ndarray:
    """Un solo flip: golpe de ruido agudo, corto y seco -- la version mas
    "minimalista", un unico papel pasando rapido."""
    dur = 0.15
    n = int(SR * dur)
    noise = _bandpassed_noise(dur, 2000, 7000)
    env = _envelope(n, attack=int(SR * 0.008), decay_rate=16.0)
    return _normalize_peak(noise * env, UI_SFX_PEAK)


def flip_B_double() -> np.ndarray:
    """Dos flips superpuestos (como pasar 2 hojas rapido) -- version ya
    usada en page_turn, ofrecida aca tambien como candidata a window_open."""
    dur1, dur2 = 0.12, 0.10
    n1, n2 = int(SR * dur1), int(SR * dur2)
    noise1 = _bandpassed_noise(dur1, 1500, 6000)
    noise2 = _bandpassed_noise(dur2, 2000, 7000)
    env1 = _envelope(n1, attack=int(SR * 0.01), decay_rate=14.0)
    env2 = _envelope(n2, attack=1, decay_rate=20.0)
    offset = int(SR * 0.06)
    out = np.zeros(offset + n2)
    out[:n1] += noise1 * env1
    out[offset : offset + n2] += noise2 * env2 * 0.8
    return _normalize_peak(out, UI_SFX_PEAK)


def flip_C_settle() -> np.ndarray:
    """Un flip + un "asentamiento" grave muy suave al final (la hoja cae
    plana contra el libro) -- mas "fisico"/completo que un flip solo."""
    dur1 = 0.13
    n1 = int(SR * dur1)
    noise = _bandpassed_noise(dur1, 2200, 7000)
    env1 = _envelope(n1, attack=int(SR * 0.008), decay_rate=18.0)
    flip = noise * env1

    settle_dur = 0.08
    n2 = int(SR * settle_dur)
    settle = _bandpassed_noise(settle_dur, 300, 1200) * _envelope(n2, attack=int(SR * 0.01), decay_rate=20.0) * 0.35
    settle_start = int(SR * 0.10)

    out = np.zeros(max(len(flip), settle_start + len(settle)))
    out[: len(flip)] += flip
    out[settle_start : settle_start + len(settle)] += settle
    return _normalize_peak(out, UI_SFX_PEAK)


# ===== Opciones para "escribiendo sobre el libro" (mision nueva/activada) =====

def _quill_stroke(duration: float, low_hz: float = 2500, high_hz: float = 7000,
                   mod_hz: float = 35.0, amp: float = 1.0, seed: int = 0) -> np.ndarray:
    """Un trazo de pluma: ruido agudo filtrado con un tremolo IRREGULAR (seno
    + jitter aleatorio, no un temblor limpio/musical) -- esa irregularidad es
    lo que hace que suene a "rasguño de nib sobre papel" en vez de un synth."""
    n = int(SR * duration)
    noise = _bandpassed_noise(duration, low_hz, high_hz)
    rng = np.random.default_rng(seed)
    t = np.arange(n) / SR
    jitter = rng.normal(0, 0.15, n)
    tremolo = 0.5 + 0.5 * np.abs(np.sin(2 * np.pi * mod_hz * t) + jitter)
    env = _envelope(n, attack=int(SR * 0.01), decay_rate=3.0)
    return amp * noise * tremolo * env


def write_A_scribble() -> np.ndarray:
    """4 trazos cortos e irregulares + un "punto" final seco -- una anotacion
    rapida, tipo "se escribio algo corto en el libro"."""
    rng = np.random.default_rng(1)
    out = np.zeros(int(SR * 0.9))
    t_cursor = 0.0
    for i in range(4):
        dur = rng.uniform(0.06, 0.11)
        stroke = _quill_stroke(dur, amp=0.9, seed=i)
        start = int(SR * t_cursor)
        out[start : start + len(stroke)] += stroke
        t_cursor += dur + rng.uniform(0.02, 0.05)
    tap_start = int(SR * t_cursor)
    tap = _noise_hit(0.02, amp=0.5, low_hz=2000, high_hz=8000)
    end = tap_start + len(tap)
    out[tap_start:end] += tap
    return _normalize_peak(out[: end + 200], UI_SFX_PEAK)


def write_B_flourish() -> np.ndarray:
    """Trazo continuo con ondulacion lenta (como una firma/rubrica, no
    golpes discretos) + punto final -- version mas "elegante"/larga."""
    dur = 0.85
    n = int(SR * dur)
    noise = _bandpassed_noise(dur, 2500, 7000)
    t = np.arange(n) / SR
    tremolo = 0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 4 * t + 0.5 * np.sin(2 * np.pi * 1.3 * t)))
    env = _envelope(n, attack=int(SR * 0.02), decay_rate=1.8)
    body = noise * tremolo * env

    tap = _noise_hit(0.025, amp=0.5, low_hz=2000, high_hz=8000)
    tap_start = len(body) - int(SR * 0.01)
    out = np.zeros(max(len(body), tap_start + len(tap)))
    out[: len(body)] += body
    out[tap_start : tap_start + len(tap)] += tap
    return _normalize_peak(out, UI_SFX_PEAK)


def write_C_stroke_dip() -> np.ndarray:
    """Trazo, pausa breve (mojar la pluma en el tintero), segundo trazo mas
    largo + punto -- transmite "escribiendo una frase", no solo un garabato."""
    out = np.zeros(int(SR * 1.0))
    s1 = _quill_stroke(0.22, amp=0.9, seed=5)
    out[: len(s1)] += s1
    gap = int(SR * 0.15)
    start2 = len(s1) + gap
    s2 = _quill_stroke(0.28, amp=0.9, seed=6)
    out[start2 : start2 + len(s2)] += s2
    tap_start = start2 + len(s2)
    tap = _noise_hit(0.02, amp=0.5, low_hz=2000, high_hz=8000)
    end = tap_start + len(tap)
    out[tap_start:end] += tap
    return _normalize_peak(out[: end + 200], UI_SFX_PEAK)


OPTIONS = {
    "window_open_A_flip_unico": flip_A_single,
    "window_open_B_flip_doble": flip_B_double,
    "window_open_C_flip_asentado": flip_C_settle,
    "escribiendo_A_garabato": write_A_scribble,
    "escribiendo_B_florido": write_B_flourish,
    "escribiendo_C_trazo_tintero": write_C_stroke_dip,
}


def main() -> None:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    for name, gen in OPTIONS.items():
        samples = gen()
        out_path = PREVIEW_DIR / f"{name}.wav"
        _write_wav(out_path, samples)
        print(f"[preview_sfx_options] {out_path} ({len(samples) / SR:.2f}s)")


if __name__ == "__main__":
    main()
