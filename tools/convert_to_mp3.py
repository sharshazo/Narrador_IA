"""Convierte todos los .wav de narracion (intro_pool, ambient, intro
fallback) a .mp3 y borra el .wav original -- pedido explicito del usuario
2026-09-05 ("pasa los audios a mp3 para bajar los mb"): ~89% de reduccion
de tamano sin perdida audible para narracion hablada (78kbps VBR, el
default de libsndfile via soundfile -- no expone control de bitrate).

No toca voices/music/ (pista fuente para remezclar despues, mejor
conservarla en calidad completa, pesa poco de todos modos).

A partir de esta fecha los scripts build_*.py ya generan directamente en
mp3 -- este script solo hace falta si aparece algun .wav suelto (ej. una
corrida vieja, o un ajuste manual).

Uso: .venv/Scripts/python.exe tools/convert_to_mp3.py
"""
from __future__ import annotations

from pathlib import Path

import soundfile as sf

APP_DIR = Path(__file__).resolve().parent.parent

TARGET_DIRS = [
    APP_DIR / "voices" / "intro_pool",
    APP_DIR / "voices" / "ambient",
    APP_DIR / "voices" / "intro",
]


def main() -> None:
    total_before = 0
    total_after = 0
    count = 0

    for d in TARGET_DIRS:
        for wav_path in sorted(d.glob("*.wav")):
            mp3_path = wav_path.with_suffix(".mp3")
            data, sr = sf.read(wav_path)
            sf.write(mp3_path, data, sr, format="MP3")
            before = wav_path.stat().st_size
            after = mp3_path.stat().st_size
            total_before += before
            total_after += after
            count += 1
            wav_path.unlink()
            print(f"{wav_path.name} -> {mp3_path.name} ({before / 1024 / 1024:.1f}MB -> {after / 1024 / 1024:.1f}MB)")

    if count == 0:
        print("No se encontro ningun .wav para convertir.")
        return

    print(f"\n{count} archivos convertidos.")
    print(f"Total antes: {total_before / 1024 / 1024:.1f} MB")
    print(f"Total despues: {total_after / 1024 / 1024:.1f} MB")
    print(f"Ahorro: {(total_before - total_after) / 1024 / 1024:.1f} MB ({100 * (1 - total_after / total_before):.0f}%)")


if __name__ == "__main__":
    main()
