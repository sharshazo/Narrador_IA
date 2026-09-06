"""Localiza y lee los archivos PluginData que escriben los addons
LOTRO_Chat_Narrator (feed de chat pasivo) y NarratorBridge.lua (pedidos de
"Narrar", manuales o automaticos -- ver Core/NarratorBridge.lua).

Formato en disco: el addon guarda con Turbine.PluginData.Save(Account, ...),
que LOTRO serializa como una tabla Lua literal ("return { ... }"). Esta
libreria la interpreta con `luadata`, la misma sintaxis que usan los
SavedVariables de WoW.

Ambos addons escriben el mismo formato de ring buffer ({entries = {...}}),
asi que la logica de "detectar cambio de archivo + reintentar parseo si se
lee a mitad de una escritura" vive una sola vez en _RingBufferReader.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import luadata

NARRATOR_KEY = "LOTRO_Narrator_Feed"
PLAY_REQUEST_KEY = "LOTRO_Narrator_PlayRequest"
STOP_KEY = "LOTRO_Narrator_Stop"
SFX_KEY = "LOTRO_Narrator_Sfx"
MUTE_KEY = "LOTRO_Narrator_Mute"

# El addon guarda en Turbine.DataScope.Account -> carpeta "AllServers", una
# unica ruta fija sin importar servidor/personaje activo. Se prueban las
# variantes de carpeta Documentos que usa Windows segun idioma/OneDrive.
CANDIDATE_ROOTS = [
    Path.home() / "Documents" / "The Lord of the Rings Online" / "PluginData",
    Path.home() / "OneDrive" / "Documents" / "The Lord of the Rings Online" / "PluginData",
    Path.home() / "OneDrive" / "Documentos" / "The Lord of the Rings Online" / "PluginData",
    Path.home() / "Documentos" / "The Lord of the Rings Online" / "PluginData",
]


def autodetect_plugindata_path() -> Optional[Path]:
    for root in CANDIDATE_ROOTS:
        if not root.is_dir():
            continue
        for account_dir in root.iterdir():
            candidate = account_dir / "AllServers" / f"{NARRATOR_KEY}.plugindata"
            if candidate.is_file():
                return candidate
    return None


class _RingBufferReader:
    """Sondea un archivo .plugindata de ring buffer y entrega solo las
    entradas (dict crudos) con id mayor al ultimo visto."""

    def __init__(self, path: Path):
        self.path = path
        self._last_id = 0
        self._last_mtime: Optional[float] = None
        self._last_size: Optional[int] = None
        self._seed_baseline()

    def _seed_baseline(self) -> None:
        # Al arrancar (cada vez que se abre LOTRO, watcher.py lanza un
        # proceso nuevo) no hay que narrar de una todo lo que ya estaba en
        # el ring buffer de la sesion anterior -- pedido explicito del
        # usuario: "abre LOTRO y empieza a narrar solo, sin que yo haga
        # nada". Se registra el id mas alto ya presente como punto de
        # partida silencioso; recien lo que se agregue DESPUES de esto
        # cuenta como "nuevo" en _read_new_entries().
        if not self.path.is_file():
            return
        try:
            stat = self.path.stat()
            text = self.path.read_text(encoding="utf-8")
            data = luadata.unserialize(text, encoding="utf-8")
        except Exception:
            return
        self._last_mtime = stat.st_mtime
        self._last_size = stat.st_size
        if not isinstance(data, dict):
            return
        raw_entries = data.get("entries") or []
        if raw_entries:
            self._last_id = max(int(e.get("id", 0)) for e in raw_entries)

    def _changed_since_last_read(self) -> bool:
        try:
            stat = self.path.stat()
        except FileNotFoundError:
            return False
        changed = stat.st_mtime != self._last_mtime or stat.st_size != self._last_size
        self._last_mtime = stat.st_mtime
        self._last_size = stat.st_size
        return changed

    def _read_new_entries(self) -> list[dict]:
        if not self.path.is_file():
            return []
        if not self._changed_since_last_read():
            return []

        # El addon reescribe el archivo entero en cada guardado. Si se llega a
        # leer a mitad de esa escritura el Lua queda invalido; la ventana es
        # minuscula (el archivo pesa pocos KB) asi que unos pocos reintentos
        # cortos alcanzan, sin necesitar bloqueos de archivo que Turbine/LOTRO
        # no exponen de todas formas.
        data = None
        for _ in range(5):
            try:
                text = self.path.read_text(encoding="utf-8")
                data = luadata.unserialize(text, encoding="utf-8")
                break
            except Exception:
                time.sleep(0.05)
        if not isinstance(data, dict):
            return []

        raw_entries = data.get("entries") or []
        if not raw_entries:
            return []

        max_id = max(int(e.get("id", 0)) for e in raw_entries)
        if max_id < self._last_id:
            # El addon se reinicio (relog / recarga de UI): sus ids volvieron
            # a empezar desde 1. Se trata todo el buffer actual como nuevo.
            self._last_id = 0

        new_entries = [e for e in raw_entries if int(e.get("id", 0)) > self._last_id]
        if new_entries:
            self._last_id = max(int(e.get("id", 0)) for e in new_entries)
        return new_entries


@dataclass
class ChatEntry:
    id: int
    channel: str
    message: str
    game_time: float


class PluginDataReader(_RingBufferReader):
    """Sondea el feed de chat pasivo (LOTRO_Chat_Narrator)."""

    def poll(self) -> list[ChatEntry]:
        return [
            ChatEntry(
                id=int(e.get("id", 0)),
                channel=str(e.get("ch", "")),
                message=str(e.get("msg", "")),
                game_time=float(e.get("t", 0.0)),
            )
            for e in self._read_new_entries()
        ]


@dataclass
class PlayRequest:
    id: int
    title: str
    text: str
    npc: str = ""


class PlayRequestReader(_RingBufferReader):
    """Sondea pedidos de 'Narrar' (boton manual en el Tracker/ventana
    principal de QuestSync, o narracion automatica al aceptar/avanzar/
    completar una mision -- ver Core/NarratorBridge.lua). A diferencia de
    PluginDataReader, no lleva filtro de canal/duplicado/largo: son acciones
    que el jugador pidio o que el Tracker detecto a proposito, se reproducen
    con prioridad. Devuelve una lista (no un solo pedido) porque dos eventos
    pueden dispararse casi seguidos -- p.ej. aceptar una mision y su primer
    progreso -- antes de que este lado alcance a sondear el archivo.
    """

    def poll(self) -> list[PlayRequest]:
        return [
            PlayRequest(
                id=int(e.get("id", 0)),
                title=str(e.get("title", "")),
                text=str(e.get("text", "")),
                npc=str(e.get("npc", "")),
            )
            for e in self._read_new_entries()
        ]


@dataclass
class SfxRequest:
    id: int
    name: str


class SfxReader(_RingBufferReader):
    """Sondea pedidos de efecto de sonido (fanfarria de mision, pergamino,
    click de UI -- ver NarratorBridge.lua:SignalSfx). Mismo ring buffer que
    PlayRequestReader: son eventos discretos (un click, un accept), no texto
    a narrar, asi que no llevan filtro de canal/duplicado/largo tampoco."""

    def poll(self) -> list[SfxRequest]:
        return [
            SfxRequest(id=int(e.get("id", 0)), name=str(e.get("name", "")))
            for e in self._read_new_entries()
        ]


class StopSignalReader:
    """Sondea un contador simple que NarratorBridge.lua sube cada vez que
    hay que cortar la narracion en curso: al cargar el addon (login/cambio
    de personaje/reloadui -- no hay evento real para detectar esto, "al
    cargar" es el proxy mas cercano) y al detectar, via el chat de sistema,
    que el jugador entro/salio de una zona o instancia (ver
    Core/NarratorBridge.lua para el porque de este mecanismo). No lleva
    logica de "entradas nuevas" como _RingBufferReader -- solo importa si
    el numero subio desde la ultima vez que se sondeo."""

    def __init__(self, path: Path):
        self.path = path
        self._last_count = 0

    def poll(self) -> bool:
        if not self.path.is_file():
            return False
        try:
            data = luadata.unserialize(self.path.read_text(encoding="utf-8"), encoding="utf-8")
        except Exception:
            return False
        if not isinstance(data, dict):
            return False
        count = int(data.get("count", 0))
        if count != self._last_count:
            self._last_count = count
            return True
        return False


class MuteReader:
    """Sondea el boton silenciar/activar del Tracker (Core/NarratorMute.lua,
    UI/QuestTrackerHUD.lua). A diferencia de StopSignalReader (un pulso que
    solo importa cuando CAMBIA), aca el propio VALOR es lo que le hace falta
    a Narrador_IA en cada sondeo -- por ejemplo si la app se abre despues de
    que el jugador ya haya dejado el boton en off desde una sesion anterior,
    tiene que arrancar respetando eso, no esperar a un cambio futuro."""

    def __init__(self, path: Path):
        self.path = path

    def poll(self) -> bool:
        """True si el jugador dejo el narrador en OFF ahora mismo. Si el
        archivo no existe todavia (instalacion nueva, el boton nunca se
        toco) o no se puede leer, se asume no-silenciado -- mismo criterio
        de "todo prendido por defecto" que ya usa el resto del addon."""
        if not self.path.is_file():
            return False
        try:
            data = luadata.unserialize(self.path.read_text(encoding="utf-8"), encoding="utf-8")
        except Exception:
            return False
        if not isinstance(data, dict):
            return False
        return bool(data.get("muted", False))
