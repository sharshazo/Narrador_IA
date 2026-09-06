"""Motor ElevenLabs: usado UNICAMENTE por la voz "narrador_intro" (ver
config.yaml) -- el resto del addon (chat, misiones, NPCs) sigue en
edge/xtts, sin tocar. Requiere una API key en .env (ver src/secrets_env.py)
y, para voces de la Biblioteca (no las "premade" por defecto), un plan de
pago para poder usarlas via API (confirmado en esta sesion: un plan free
devuelve 402 "paid_plan_required" para cualquier voz de Biblioteca).

Elegida asi (2026-09-05, pedido explicito del usuario tras escuchar varias
rondas de candidatas): "Storyteller Oxley - Grandpa", una voz de la
Biblioteca de ElevenLabs con personalidad de abuelo narrador, la que mas se
acerco al "anciano" pedido -- por encima de gandalf_clone (XTTS, sonaba con
ruido de fondo del clip de referencia) y de las voces "premade" gratis
(Bill/Callum/George/Daniel/Arnold/Antoni, ninguna tan vieja).
"""
from __future__ import annotations

from pathlib import Path

import requests

from secrets_env import get_env

API_KEY_NAME = "ELEVENLABS_API_KEY"
TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
ADD_VOICE_URL = "https://api.elevenlabs.io/v1/voices/add/{public_owner_id}/{voice_id}"


def _ensure_voice_added(voice_id: str, public_owner_id: str, api_key: str) -> None:
    # Las voces de Biblioteca (a diferencia de las "premade") tienen que
    # agregarse a la cuenta una vez antes de poder usarse para sintesis --
    # si ya estaba agregada (caso normal, se agrego una sola vez al elegir
    # la voz), la API devuelve 400/422 "ya existe", que se ignora.
    requests.post(
        ADD_VOICE_URL.format(public_owner_id=public_owner_id, voice_id=voice_id),
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        json={"new_name": voice_id},
        timeout=30,
    )


def synthesize(text: str, voice_cfg: dict, out_path: Path, base_dir: Path) -> Path:
    # api_key_env (2026-09-05, pedido explicito del usuario: segunda cuenta
    # de ElevenLabs para otra voz) -- cada voz puede declarar en que
    # variable de .env esta su propia key; si no lo declara, usa la de
    # siempre (API_KEY_NAME) para no romper las voces ya configuradas.
    key_name = voice_cfg.get("api_key_env", API_KEY_NAME)
    api_key = get_env(base_dir, key_name)
    if not api_key:
        raise RuntimeError(f"Falta {key_name} en .env (ver src/secrets_env.py)")

    voice_id = voice_cfg["voice_id"]
    model_id = voice_cfg.get("model_id", "eleven_multilingual_v2")
    voice_settings = voice_cfg.get("voice_settings", {})

    response = requests.post(
        TTS_URL.format(voice_id=voice_id),
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        json={"text": text, "model_id": model_id, "voice_settings": voice_settings},
        timeout=60,
    )

    if response.status_code == 404 and voice_cfg.get("public_owner_id"):
        # Voz de Biblioteca todavia no agregada a esta cuenta (ej. key/cuenta
        # nueva) -- se agrega una vez y se reintenta.
        _ensure_voice_added(voice_id, voice_cfg["public_owner_id"], api_key)
        response = requests.post(
            TTS_URL.format(voice_id=voice_id),
            headers={"xi-api-key": api_key, "Content-Type": "application/json"},
            json={"text": text, "model_id": model_id, "voice_settings": voice_settings},
            timeout=60,
        )

    if response.status_code != 200:
        raise RuntimeError(f"ElevenLabs fallo ({response.status_code}): {response.text[:300]}")

    out_path.write_bytes(response.content)
    return out_path
