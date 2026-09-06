"""Motor edge-tts: voces neuronales del servicio de lectura en voz alta de
Microsoft Edge -- gratis, sin registro ni API key, con 45 voces en español
de 22 paises. Motor principal del proyecto (ver src/tts.py).

Requiere internet -- pero LOTRO es un MMO online, asi que sin internet el
juego mismo se desconecta (no hace falta un motor de respaldo offline). Si
este motor falla por otro motivo (servicio caido, etc.), quien llama
(tts.py) cae de vuelta a una voz edge-tts fija distinta.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import edge_tts


def synthesize(text: str, voice_cfg: dict, out_path: Path, base_dir: Path) -> Path:
    voice_id = voice_cfg["voice_id"]
    rate = voice_cfg.get("rate", "+0%")
    # -20% por defecto (2026-09-02, pedido explicito del usuario: "bajar el
    # volumen un 20%"). Cualquier voz puede pisar esto con su propio
    # "volume_pct" en config.yaml.
    volume = voice_cfg.get("volume_pct", "-20%")
    # pitch: confirmado en esta sesion que es, junto con rate/volume, lo
    # UNICO que este servicio realmente respeta -- el texto que se manda se
    # escapa (xml.sax.saxutils.escape) antes de meterlo en el SSML, asi que
    # cualquier etiqueta de estilo expresivo (mstts:express-as, etc.)
    # quedaria como texto literal, no como marcado real. narration.py arma
    # este pitch dinamicamente por segmento (dialogo/exclamacion/narracion,
    # ver text_utils.segment_for_narration) para dar algo de variacion de
    # verdad dentro de lo que el motor gratis permite.
    pitch = voice_cfg.get("pitch", "+0Hz")

    async def _run() -> None:
        communicate = edge_tts.Communicate(text, voice_id, rate=rate, volume=volume, pitch=pitch)
        await communicate.save(str(out_path))

    asyncio.run(_run())
    return out_path
