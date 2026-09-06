"""Carga config.yaml y la completa con valores por defecto si faltan claves."""
from __future__ import annotations

import copy
from pathlib import Path

import yaml

DEFAULT_CONFIG = {
    "plugindata_path": None,
    "poll_interval_seconds": 0.04,
    "max_chars": 400,
    "dedupe_window_seconds": 6,
    "max_queue_depth": 8,
    # Carpeta accesoria de audio (relativa a Narrador_IA/), usada solo si
    # cache_enabled es true. Ver src/voicecache.py.
    "cache_dir": "VoiceOverData/cache",
    # 2026-09-02 (pedido explicito del usuario: "sin cache, nada se guarda"
    # -- el cache real llego a pesar 15GB con solo 4765/14824 misiones):
    # false por defecto AQUI (el config.yaml real de esta instalacion lo
    # pisa a true, ver ese archivo). Cada narracion se sintetiza a un
    # scratch temporal (%TEMP%, no la carpeta del proyecto) y se borra
    # apenas termina de reproducirse.
    "cache_enabled": False,
    # 2026-09-03 (pedido explicito del usuario: "que sea instantaneo si es
    # posible", cache reactivado CON TOPE esta vez): limite duro en MB para
    # cache_dir -- 0/False = sin tope (comportamiento viejo que crecio a
    # 15GB). Ver VoiceCache.enforce_limit(): borra lo usado hace mas tiempo
    # primero (LRU real) cuando se pasa del limite, nunca crece sin control.
    "cache_max_mb": 300,
    "channels": {
        "Quest": {"enabled": True, "voice": "edge_alvaro"},
        "Say": {"enabled": True, "voice": "edge_elvira"},
        "Emote": {"enabled": True, "voice": "edge_elvira"},
        "Tell": {"enabled": True, "voice": "edge_elvira"},
        "Fellowship": {"enabled": False, "voice": "edge_elvira"},
        "Kinship": {"enabled": False, "voice": "edge_elvira"},
        "Raid": {"enabled": False, "voice": "edge_elvira"},
        "Death": {"enabled": True, "voice": "edge_alvaro"},
        "Loot": {"enabled": True, "voice": "edge_alvaro"},
        "Advancement": {"enabled": True, "voice": "edge_alvaro"},
    },
    # Piper (offline) se elimino a proposito (2026-09-02, pedido explicito
    # del usuario): LOTRO es un MMO online, sin internet el juego mismo se
    # desconecta, asi que un motor de respaldo "sin internet" no tenia caso
    # de uso real. Solo queda "edge" (gratis, requiere internet) y "xtts"
    # (clonacion local, opcional).
    "voices": {
        "edge_alvaro": {"engine": "edge", "voice_id": "es-ES-AlvaroNeural"},
        "edge_elvira": {"engine": "edge", "voice_id": "es-ES-ElviraNeural"},
        "edge_jorge": {"engine": "edge", "voice_id": "es-MX-JorgeNeural"},
        "edge_dalia": {"engine": "edge", "voice_id": "es-MX-DaliaNeural"},
        "edge_tomas": {"engine": "edge", "voice_id": "es-AR-TomasNeural"},
        "edge_elena": {"engine": "edge", "voice_id": "es-AR-ElenaNeural"},
    },
    "npc_voice_pool": [
        "edge_alvaro",
        "edge_elvira",
        "edge_jorge",
        "edge_dalia",
        "edge_tomas",
        "edge_elena",
    ],
    # Override para personajes principales: nombre de NPC (en minusculas) ->
    # nombre de voz declarado arriba en "voices". Ejemplo (comentado en el
    # config.yaml de verdad) para clonar con XTTS a partir de un clip real:
    #   main_npcs: {"gandalf": "gandalf_clone"}
    #   voices: {gandalf_clone: {engine: xtts, clone_ref: "voices/reference/gandalf.wav"}}
    "main_npcs": {},
    "ignore_patterns": ["^/"],
    # Efectos de sonido cortos (fanfarria de mision, pergamino, click de UI
    # -- ver NarratorBridge.lua:SignalSfx, src/sfx.py). Independiente de
    # cache_enabled/voices: no son texto sintetizado, son archivos ya
    # generados (ver tools/gen_sfx.py) que se reproducen tal cual.
    "sfx_enabled": True,
    "sfx_dir": "voices/sfx",
    # 2026-09-05 (pedido explicito del usuario): narracion de bienvenida
    # automatica, una vez por apertura de LOTRO -- ver Narrator.play_intro.
    "intro_enabled": True,
    "intro_delay_seconds": 7,
    # 2026-09-05 (pedido explicito del usuario): narracion ambiental
    # aleatoria durante el juego (historias/leyendas/consejos), prioridad
    # mas baja -- ver src/ambient_narrator.py, tts.py:play_ambient.
    "ambient_enabled": True,
    "ambient_min_interval_seconds": 480,
    "ambient_max_interval_seconds": 900,
}


def _deep_merge(base: dict, override: dict) -> dict:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(path: Path) -> dict:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f) or {}
    else:
        user_config = {}
    return _deep_merge(DEFAULT_CONFIG, user_config)
