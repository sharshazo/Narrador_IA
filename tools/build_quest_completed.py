"""Arma el quest_completed final como una MEZCLA de 3 sonidos reales
(pedido explicito del usuario, 2026-09-02): la firma (Sonido de
Lapicera.mp3) arranca primero -- "recompensa de la mision" (completar del
todo, recibir los items) -- y "sonido precio.mp3" (mas bajo de volumen, para
que no sature/opaque a la firma) + "Coin sound+Sonido de moneda.mp3" se
integran juntos un poco despues, superpuestos entre si y sobre la cola de la
firma, no en secuencia.

Cada capa se procesa con la misma cadena "audio real" que ya usan
split_pasar_pagina.py/process_lapicera.py (pasa-altos + nivelado por RMS +
limitador suave -- ver _level_real_recording en gen_sfx.py) ANTES de
mezclarse, y la mezcla final pasa por un limitador maestro aparte: sumar 3
capas ya "calientes" cada una por separado puede pasarse de escala aunque
ninguna lo haga sola.

Uso: .venv/Scripts/python.exe tools/build_quest_completed.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_sfx import SR, _level_real_recording, _soft_limit, _write_wav  # noqa: E402

VOCES = Path(__file__).resolve().parent.parent.parent / "voces"
OUT = Path(__file__).resolve().parent.parent / "voices" / "sfx" / "quest_completed.wav"

FIRMA_SRC = VOCES / "Sonido de Lapicera.mp3"
PRECIO_SRC = VOCES / "sonido precio.mp3"
COIN_SRC = VOCES / "Coin sound+Sonido de moneda.mp3"

# La firma se queda "protagonista" (mismo nivel que ya se ajusto por el
# reclamo de saturacion); precio EXPLICITAMENTE mas bajo (pedido del
# usuario: "que no sature o opaque el de la firma"); moneda a un nivel
# intermedio, audible pero sin tapar a la firma tampoco.
FIRMA_RMS, FIRMA_CEIL = 0.055, 0.60
PRECIO_RMS, PRECIO_CEIL = 0.030, 0.40
COIN_RMS, COIN_CEIL = 0.045, 0.50

# Los otros 2 sonidos "se integran" DESPUES de que arranca la firma, no
# junto con ella -- offset chico, no una secuencia completa una detras de
# la otra.
JOIN_OFFSET_S = 0.40

MASTER_CEILING = 0.80


def _fade(samples: np.ndarray, sr: int, fade_ms: float = 8.0) -> np.ndarray:
    n = min(int(sr * fade_ms / 1000), len(samples) // 4)
    if n <= 0:
        return samples
    out = samples.copy()
    out[:n] *= np.linspace(0, 1, n)
    out[-n:] *= np.linspace(1, 0, n)
    return out


def _load_mono(path: Path) -> tuple[np.ndarray, int]:
    data, sr = sf.read(path)
    mono = data.mean(axis=1) if data.ndim > 1 else data
    return mono, sr


def _trim_active(mono: np.ndarray, sr: int, pad_lead_s: float = 0.05, pad_tail_s: float = 0.15) -> np.ndarray:
    """Recorta silencio de sobra alrededor del contenido real -- 'sonido
    precio.mp3' trae ~2.9s de silencio antes del sonido de verdad, dejarlo
    tal cual arruinaria el timing de la mezcla (el "precio" sonaria casi 3s
    despues de lo esperado)."""
    win = int(sr * 0.05)
    n = len(mono) // win
    if n == 0:
        return mono
    rms = np.array([np.sqrt(np.mean(mono[i * win : (i + 1) * win] ** 2)) for i in range(n)])
    peak = rms.max()
    if peak < 1e-9:
        return mono
    active = np.where(rms > peak * 0.04)[0]
    if len(active) == 0:
        return mono
    start = max(0, int(active[0] * win - sr * pad_lead_s))
    end = min(len(mono), int((active[-1] + 1) * win + sr * pad_tail_s))
    return mono[start:end]


def main() -> None:
    # BUG DE LATENCIA CORREGIDO (pedido explicito del usuario, 2026-09-03:
    # "los sonidos se demoran en aparecer y no es instantaneo") -- medido en
    # esta sesion: Sonido de Lapicera.mp3 sin recortar tenia 329ms de
    # silencio REAL al principio (la persona que grabo esperaba un poco
    # antes de hacer el sonido) -- el archivo empezaba a reproducirse al
    # instante (confirmado, el propio MCI tarda ~20-50ms en arrancar), pero
    # esos primeros 329ms de audio eran silencio de verdad, asi que sonaba
    # "tarde" igual. _trim_active() ya se usaba para "sonido precio.mp3"
    # (que tenia ~2.9s de silencio) -- se aplica tambien aca.
    firma, sr1 = _load_mono(FIRMA_SRC)
    firma = _trim_active(firma, sr1, pad_lead_s=0.02, pad_tail_s=0.15)
    firma = _fade(firma, sr1)
    firma = _level_real_recording(firma, sr1, FIRMA_RMS, FIRMA_CEIL)

    precio, sr2 = _load_mono(PRECIO_SRC)
    precio = _trim_active(precio, sr2)
    precio = _fade(precio, sr2)
    precio = _level_real_recording(precio, sr2, PRECIO_RMS, PRECIO_CEIL)

    coin, sr3 = _load_mono(COIN_SRC)
    coin = _fade(coin, sr3)
    coin = _level_real_recording(coin, sr3, COIN_RMS, COIN_CEIL)

    assert sr1 == sr2 == sr3 == SR, f"sample rates distintos: {sr1}, {sr2}, {sr3}"

    offset = int(SR * JOIN_OFFSET_S)
    total_len = max(len(firma), offset + len(precio), offset + len(coin))
    mix = np.zeros(total_len)
    mix[: len(firma)] += firma
    mix[offset : offset + len(precio)] += precio
    mix[offset : offset + len(coin)] += coin

    mix = _soft_limit(mix, MASTER_CEILING)
    _write_wav(OUT, mix)
    print(f"[build_quest_completed] {OUT} ({len(mix) / SR:.2f}s)")
    print(f"  firma: {len(firma)/SR:.2f}s @ t=0")
    print(f"  precio: {len(precio)/SR:.2f}s @ t={JOIN_OFFSET_S:.2f}s")
    print(f"  coin: {len(coin)/SR:.2f}s @ t={JOIN_OFFSET_S:.2f}s")


if __name__ == "__main__":
    main()
