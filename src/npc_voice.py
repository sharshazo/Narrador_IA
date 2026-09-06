"""Asigna una voz a cada NPC (bestower de la mision, ver NarratorBridge.lua).

Dos niveles:
1. `main_npcs` (config.yaml): override explicito para personajes principales
   -- nombre de NPC -> nombre de voz ya declarado en `voices:` (puede ser
   una voz xtts clonada de un clip real, o una voz edge-tts elegida a oido
   como "la mas parecida"). Pedido explicito del usuario (2026-09-02): NPCs
   principales deben sonar lo mas identico posible a LOTRO, no solo variado.
2. Si no hay override, hash estable (md5, no el hash() nativo de Python --
   ese cambia de proceso a proceso por seguridad) sobre `npc_voice_pool`: el
   mismo NPC generico siempre saca la MISMA voz, y NPCs distintos tienden a
   sonar distinto porque el pool tiene varias voces. No hace falta guardar
   ningun mapeo NPC->voz en disco.

No hay datos reales de genero por NPC en QuestSync (se reviso: QuestDB no
tiene ese campo, y adivinarlo por nombre en un mundo de fantasia no seria
confiable) -- por eso el nivel 2 no intenta "acertar" el genero real de cada
NPC, solo darle variedad y consistencia.
"""
from __future__ import annotations

import hashlib


def voice_for_npc(npc_name: str, pool: list[str], main_npcs: dict[str, str] | None = None) -> str:
    if not npc_name:
        if not pool:
            raise ValueError("npc_voice_pool esta vacio en config.yaml")
        return pool[0]

    key = npc_name.strip().lower()

    if main_npcs and key in main_npcs:
        return main_npcs[key]

    if not pool:
        raise ValueError("npc_voice_pool esta vacio en config.yaml")
    digest = hashlib.md5(key.encode("utf-8")).hexdigest()
    index = int(digest, 16) % len(pool)
    return pool[index]
