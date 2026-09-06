"""Genera UNA VEZ una pista musical epica instrumental (ElevenLabs
sound-generation, misma cuenta que la voz) y la deja guardada en
voices/music/epic_bed.wav -- se reutiliza (loopeada con crossfade) para
todas las narraciones, en vez de generar musica nueva para cada una.

30s es el maximo permitido por llamada de esta API (confirmado en esta
sesion: 400 "invalid_generation_settings" para pedidos mayores) -- de sobra
para loopear sin problema, ver audio_fx.loop_to_length.

Uso: .venv/Scripts/python.exe tools/build_music_bed.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import requests
import soundfile as sf

APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR / "src"))

from secrets_env import get_env  # noqa: E402

OUT_PATH = APP_DIR / "voices" / "music" / "epic_bed.wav"
PROMPT = (
    "epic cinematic orchestral fantasy background music, slow majestic build, "
    "soft strings, distant horns and choir, no percussion hits, no vocals, ambient, loopable"
)
DURATION_S = 30.0


def main() -> None:
    api_key = get_env(APP_DIR, "ELEVENLABS_API_KEY")
    if not api_key:
        raise SystemExit("Falta ELEVENLABS_API_KEY en .env")

    print("[Musica] Generando cama musical epica (30s)...")
    r = requests.post(
        "https://api.elevenlabs.io/v1/sound-generation",
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        json={"text": PROMPT, "duration_seconds": DURATION_S, "prompt_influence": 0.4},
        timeout=120,
    )
    if r.status_code != 200:
        raise SystemExit(f"ElevenLabs fallo ({r.status_code}): {r.text[:300]}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    raw_path = OUT_PATH.with_suffix(".mp3")
    raw_path.write_bytes(r.content)

    data, sr = sf.read(raw_path)
    mono = data.mean(axis=1) if data.ndim > 1 else data
    peak = np.abs(mono).max()
    if peak > 1e-6:
        mono = mono * (0.9 / peak)

    sf.write(OUT_PATH, mono.astype(np.float32), sr, subtype="PCM_16")
    raw_path.unlink()
    print(f"[Musica] Listo: {OUT_PATH} ({len(mono) / sr:.1f}s, {sr}Hz)")


if __name__ == "__main__":
    main()
