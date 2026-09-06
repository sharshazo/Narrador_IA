"""Narrador_IA: lee el chat de LOTRO (via el addon LOTRO_Chat_Narrator) y lo
narra por voz con edge-tts (neuronal, en espanol, gratis).

Uso: ejecutar con el Python del entorno virtual (.venv) o hacer doble clic en
run_narrador.bat, estando LOTRO abierto. Icono en la bandeja del sistema para
pausar/reanudar/salir (si no hay bandeja disponible, corre en consola).
"""
from __future__ import annotations

import random
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from ambient_narrator import AmbientNarrator
from config import load_config
from npc_voice import voice_for_npc
from playback import play_file_blocking
from plugindata import (
    MUTE_KEY,
    PLAY_REQUEST_KEY,
    SFX_KEY,
    STOP_KEY,
    MuteReader,
    PlayRequestReader,
    PluginDataReader,
    SfxReader,
    StopSignalReader,
    autodetect_plugindata_path,
)
from sfx import SfxPlayer
from text_utils import TextFilter
from tts import SpeechQueue

APP_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = APP_DIR / "config.yaml"
# Pool de narraciones de introduccion (2026-09-05, pedido explicito del
# usuario: "4 narraciones distintas... que se reproduzcan aleatoreamente
# cada vez que cerremos y abramos el juego") -- ver
# tools/build_motivational_clips.py. Se elige una al azar en cada apertura
# de LOTRO en vez de repetir siempre la misma.
INTRO_POOL_DIR = APP_DIR / "voices" / "intro_pool"
# Guion original largo (2-3 min) generado antes del pedido de las 4
# narraciones cortas -- se mantiene como respaldo si el pool estuviera
# vacio (ej. instalacion nueva sin correr build_motivational_clips.py).
INTRO_FALLBACK_PATH = APP_DIR / "voices" / "intro" / "intro_bienvenida.mp3"

LOTRO_PROCESS = "lotroclient64.exe"
_CREATE_NO_WINDOW = 0x08000000


def _lotro_running() -> bool:
    # Mismo chequeo que watcher.py (tasklist, sin dependencias nuevas): se
    # repite aca en vez de importar watcher.py porque ese modulo trae su
    # propio main() de "vigia" con un while True -- solo se necesita esta
    # funcion suelta.
    result = subprocess.run(
        ["tasklist", "/FI", f"IMAGENAME eq {LOTRO_PROCESS}"],
        capture_output=True,
        text=True,
        creationflags=_CREATE_NO_WINDOW,
    )
    return LOTRO_PROCESS.lower() in result.stdout.lower()


def resolve_plugindata_path(config: dict) -> Path:
    configured = config.get("plugindata_path")
    if configured:
        return Path(configured)
    detected = autodetect_plugindata_path()
    if detected:
        return detected
    raise SystemExit(
        "No se encontro LOTRO_Narrator_Feed.plugindata.\n"
        "Verifica que el addon LOTRO_Chat_Narrator este instalado en Plugins "
        "y que hayas iniciado sesion con un personaje al menos una vez, o "
        "configura 'plugindata_path' a mano en config.yaml."
    )


class Narrator:
    def __init__(self, config: dict):
        self.config = config
        self.reader: Optional[PluginDataReader] = None
        self.play_reader: Optional[PlayRequestReader] = None
        self.stop_reader: Optional[StopSignalReader] = None
        self.sfx_reader: Optional[SfxReader] = None
        self.mute_reader: Optional[MuteReader] = None
        # Estado del boton del Tracker, distinto del pausar/reanudar de la
        # bandeja (tray.py tiene su propio state["enabled"] local, ver la
        # nota grande en poll_once mas abajo) -- se sigue aca solo para
        # detectar la TRANSICION real (on->off u off->on) y no repetir
        # set_enabled/stop_now en cada sondeo mientras el jugador no toque
        # el boton de nuevo.
        self._tracker_muted = False
        # Fuente de verdad unica del on/off, leida por tray.py (2026-09-05):
        # antes tray.py llevaba su propio state["enabled"] local -- con el
        # boton del Tracker sumandose como OTRA forma de cambiar lo mismo,
        # ese duplicado se desincronizaba (el menu de bandeja podia decir
        # "Pausar narracion" estando ya en pausa desde el juego, y togglear
        # mal). set_enabled() la actualiza, tray la lee en vez de guardar su
        # propia copia.
        self.enabled = True
        self.sfx_player = SfxPlayer(
            APP_DIR / config["sfx_dir"], enabled=config["sfx_enabled"]
        )
        self.text_filter = TextFilter(
            max_chars=config["max_chars"],
            dedupe_window_seconds=config["dedupe_window_seconds"],
            ignore_patterns=config["ignore_patterns"],
        )
        self.speech_queue = SpeechQueue(
            config["voices"],
            APP_DIR,
            APP_DIR / config["cache_dir"],
            config["max_queue_depth"],
            cache_enabled=config["cache_enabled"],
            cache_max_mb=config.get("cache_max_mb", 0),
        )
        self.ambient_narrator = AmbientNarrator(
            APP_DIR / "voices" / "ambient",
            self.speech_queue,
            config.get("ambient_min_interval_seconds", 480),
            config.get("ambient_max_interval_seconds", 900),
            enabled=config.get("ambient_enabled", True),
        )
        self.running = True

    def start(self) -> None:
        path = resolve_plugindata_path(self.config)
        print(f"[Narrador_IA] Leyendo: {path}")
        self.reader = PluginDataReader(path)
        # Mismo directorio de cuenta que el feed de chat (ambos usan
        # Turbine.DataScope.Account -> carpeta "AllServers"), solo cambia el
        # nombre de archivo/clave -- ver NarratorBridge.lua.
        play_request_path = path.parent / f"{PLAY_REQUEST_KEY}.plugindata"
        self.play_reader = PlayRequestReader(play_request_path)
        stop_path = path.parent / f"{STOP_KEY}.plugindata"
        self.stop_reader = StopSignalReader(stop_path)
        sfx_path = path.parent / f"{SFX_KEY}.plugindata"
        self.sfx_reader = SfxReader(sfx_path)
        mute_path = path.parent / f"{MUTE_KEY}.plugindata"
        self.mute_reader = MuteReader(mute_path)
        # Respeta lo que el jugador ya haya dejado elegido en una sesion
        # anterior (el .plugindata sobrevive entre aperturas de LOTRO) --
        # sin esto, abrir Narrador_IA con el boton ya en "off" narraria
        # igual hasta el primer sondeo que detecte un cambio, que nunca
        # llega si el jugador no vuelve a tocar el boton.
        self._tracker_muted = self.mute_reader.poll()
        if self._tracker_muted:
            self.set_enabled(False)
        self.speech_queue.start()
        self.ambient_narrator.start()

        if self.config.get("intro_enabled", True):
            threading.Thread(target=self._auto_intro_after_delay, daemon=True).start()

    def _auto_intro_after_delay(self) -> None:
        # watcher.py lanza este proceso UNA SOLA VEZ por cada apertura de
        # LOTRO y lo mata al cerrarse (ver watcher.py) -- eso ya garantiza
        # "una sola vez por sesion, se re-habilita solo si el jugador cierra
        # y vuelve a abrir el juego" sin necesitar ningun estado propio aca.
        delay = self.config.get("intro_delay_seconds", 7)
        time.sleep(delay)
        if not _lotro_running():
            # El jugador cerro LOTRO durante la espera (ventana angosta
            # entre que este proceso arranco y el chequeo de watcher.py, que
            # sondea cada 5s) -- no narrar sobre un juego que ya se cerro.
            return
        self.play_intro()

    def _pick_intro_clip(self) -> Optional[Path]:
        # mp3 (formato actual, ver tools/convert_to_mp3 -- pedido explicito
        # del usuario "pasa los audios a mp3 para bajar los mb") + wav
        # (por si algun clip viejo/nuevo quedara sin convertir).
        pool = (
            sorted(INTRO_POOL_DIR.glob("*.mp3")) + sorted(INTRO_POOL_DIR.glob("*.wav"))
            if INTRO_POOL_DIR.exists()
            else []
        )
        if pool:
            return random.choice(pool)
        if INTRO_FALLBACK_PATH.exists():
            return INTRO_FALLBACK_PATH
        return None

    def play_intro(self) -> None:
        """Reproduce una narracion de introduccion elegida al azar del pool
        (ver tools/build_motivational_clips.py, INTRO_POOL_DIR). No pasa por
        SpeechQueue: es una sola pista de audio continua, no texto para
        sintetizar linea por linea, y no debe competir por la cola con el
        chat/Tracker."""
        clip = self._pick_intro_clip()
        if clip is None:
            print(
                f"[Narrador_IA] No hay narraciones de intro generadas -- corre "
                f"'tools/build_motivational_clips.py' primero ({INTRO_POOL_DIR})."
            )
            return
        print(f"[Narrador_IA] Reproduciendo narracion de bienvenida: {clip.stem}")
        try:
            play_file_blocking(clip)
        except Exception as exc:
            print(f"[Narrador_IA] Error reproduciendo la intro: {exc}")

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        self.speech_queue.set_enabled(enabled)
        self.ambient_narrator.set_enabled(enabled)
        print(f"[Narrador_IA] Narracion {'activada' if enabled else 'en pausa'}.")

    def poll_once(self) -> None:
        # Cambio de zona/mapa/instancia o carga del addon (login/cambio de
        # personaje/reloadui) -- pedido explicito del usuario: "que se
        # detenga la narracion". Se revisa PRIMERO: si hay que cortar, no
        # tiene sentido seguir procesando pedidos/chat de este mismo ciclo
        # que ya quedaron obsoletos por el cambio.
        if self.stop_reader.poll():
            self.speech_queue.stop_now()
            print("[Narrador_IA] Narracion detenida (cambio de zona/mapa o de personaje).")

        # Boton silenciar/activar del Tracker (UI/QuestTrackerHUD.lua,
        # verde=on / gris=off) -- se revisa junto con stop_reader, antes de
        # procesar chat/pedidos de este mismo ciclo. Solo actua en la
        # TRANSICION real (ver self._tracker_muted en __init__): sondear
        # devuelve el valor actual completo, no un pulso de cambio como
        # stop_reader, asi que sin este chequeo se llamaria a set_enabled/
        # stop_now en cada sondeo mientras el jugador no toque el boton de
        # nuevo. Al pasar a ON->OFF ademas se corta lo que este sonando en
        # ese instante (stop_now) -- un boton de silenciar que no calla el
        # audio ya en curso no se siente como un mute real.
        tracker_muted = self.mute_reader.poll()
        if tracker_muted != self._tracker_muted:
            self._tracker_muted = tracker_muted
            self.set_enabled(not tracker_muted)
            if tracker_muted:
                self.speech_queue.stop_now()
            print(f"[Narrador_IA] Narrador {'silenciado' if tracker_muted else 'activado'} desde el Tracker.")

        # Sin cola (2026-09-02, pedido explicito del usuario): si se
        # acumularon varios pedidos entre un sondeo y otro (varios clicks
        # seguidos, o la app estuvo cerrada y el addon siguio escribiendo),
        # solo importa el mas reciente -- los anteriores se descartan sin
        # narrarlos, en vez de reproducirlos todos en fila.
        # Efectos de sonido (fanfarria de mision, pergamino, click) --
        # totalmente independientes de la narracion: no pasan por
        # text_filter ni por SpeechQueue, se reproducen enseguida en su
        # propio hilo (ver SfxPlayer) y pueden sonar superpuestos a lo que
        # se este narrando.
        for sfx in self.sfx_reader.poll():
            self.sfx_player.play(sfx.name)

        requests = self.play_reader.poll()
        if requests:
            request = requests[-1]
            text = self.text_filter.clean(request.text)
            if text:
                voice_name = voice_for_npc(
                    request.npc, self.config["npc_voice_pool"], self.config.get("main_npcs")
                )
                who = request.npc or "NPC desconocido"
                print(f"[Narrar] ({who}, voz={voice_name}) {request.title}: {text}")
                self.speech_queue.say_now(text, voice_name)

        for entry in self.reader.poll():
            channel_cfg = self.config["channels"].get(entry.channel)
            if not channel_cfg or not channel_cfg.get("enabled"):
                continue
            text = self.text_filter.clean(entry.message)
            if not self.text_filter.should_speak(text):
                continue
            print(f"[{entry.channel}] {text}")
            self.speech_queue.say(text, channel_cfg["voice"])

    def run_loop(self) -> None:
        interval = self.config["poll_interval_seconds"]
        while self.running:
            try:
                self.poll_once()
            except Exception as exc:
                print(f"[Narrador_IA] Error leyendo chat: {exc}")
            time.sleep(interval)


def main() -> None:
    config = load_config(CONFIG_PATH)
    narrator = Narrator(config)
    narrator.start()

    try:
        from tray import run_tray

        run_tray(narrator)
    except Exception as exc:
        print(f"[Narrador_IA] Bandeja del sistema no disponible ({exc}); modo consola (Ctrl+C para salir).")
        narrator.run_loop()


if __name__ == "__main__":
    main()
