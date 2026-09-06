"""Mezcla la cama musical epica (voices/music/epic_bed.wav) por debajo de
cada narracion del pool de intro (voices/intro_pool/), con swell de
entrada/salida y ducking mientras habla el narrador -- pedido explicito del
usuario, 2026-09-05: "agregale banda sonora epica".

Idempotente respecto de la VOZ: siempre parte de la copia sin musica en
_dry/ (se crea la primera vez que corre este script) para poder volver a
mezclar sin ir acumulando musica sobre musica si se corre mas de una vez.

Uso: .venv/Scripts/python.exe tools/apply_music_bed.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import soundfile as sf

APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR / "src"))

from audio_fx import mix_with_ducked_music  # noqa: E402

POOL_DIR = APP_DIR / "voices" / "intro_pool"
DRY_DIR = POOL_DIR / "_dry"
MUSIC_PATH = APP_DIR / "voices" / "music" / "epic_bed.wav"


def main() -> None:
    if not MUSIC_PATH.exists():
        raise SystemExit(f"Falta {MUSIC_PATH} -- corre tools/build_music_bed.py primero.")

    music, music_sr = sf.read(MUSIC_PATH)
    music = music.astype(np.float32)

    DRY_DIR.mkdir(parents=True, exist_ok=True)

    # mp3 (pedido explicito del usuario, 2026-09-05: "pasa los audios a mp3
    # para bajar los mb") -- ver tools/convert_to_mp3.py.
    clips = sorted(POOL_DIR.glob("*.mp3"))
    if not clips:
        raise SystemExit(f"No hay clips en {POOL_DIR}.")

    for clip_path in clips:
        dry_path = DRY_DIR / clip_path.name
        if not dry_path.exists():
            # Primera vez: esta version de clip_path todavia es "seca" (sin
            # musica) -- se guarda como referencia limpia antes de mezclar.
            dry_path.write_bytes(clip_path.read_bytes())

        voice, voice_sr = sf.read(dry_path)
        voice = voice.astype(np.float32)
        if voice_sr != music_sr:
            raise SystemExit(
                f"{clip_path.name}: sample rate de voz ({voice_sr}) distinto al de la musica ({music_sr})."
            )

        mixed = mix_with_ducked_music(voice, music, voice_sr)
        sf.write(clip_path, mixed, voice_sr, format="MP3")
        print(f"[{clip_path.name}] mezclado con musica ({len(mixed) / voice_sr:.1f}s)")


if __name__ == "__main__":
    main()
