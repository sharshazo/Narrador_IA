"""Dispatcher de motores de voz + cola de sintesis/reproduccion.

Cada voz en config.yaml declara su `engine`. Piper (offline) se elimino a
proposito (2026-09-02, pedido explicito del usuario): LOTRO es un MMO
online -- si no hay internet, el juego mismo se desconecta, asi que un
motor de respaldo "sin internet" no tiene caso de uso real. Si "edge" o
"xtts" fallan por cualquier otro motivo (servicio caido, clip de referencia
faltante, etc.), se cae a una voz edge-tts fija de respaldo (ver
FALLBACK_VOICE_NAME) en vez de fallar en silencio.
"""
from __future__ import annotations

import collections
import queue
import tempfile
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from engines import edge_engine, elevenlabs_engine, xtts_engine
from playback import play_file_blocking
from text_utils import segment_for_narration
from voicecache import VoiceCache

ENGINE_FUNCS = {
    "edge": edge_engine.synthesize,
    "xtts": xtts_engine.synthesize,
    # Solo usado por la voz "narrador_intro" (ver config.yaml) -- el resto
    # del addon sigue en edge/xtts, sin tocar.
    "elevenlabs": elevenlabs_engine.synthesize,
}

FALLBACK_VOICE_NAME = "edge_alvaro"

# 2026-09-02 (pedido explicito del usuario: narracion "con expresiones,
# cambios de tono" -- ver text_utils.segment_for_narration para el porque de
# solo pitch/rate y no estilos expresivos reales, que edge-tts no permite).
#
# 2026-09-02 (pedido explicito del usuario: "ponelo un poco mas rapido... a
# una velocidad que estimes profesional"): el "+0%" por defecto de estas
# voces es un ritmo neutro/pausado, mas lento que un narrador profesional
# tipico (~150-160 palabras/min de audiolibro). +12% de base en vez de +0%,
# subido a +17% (2026-09-02, pedido explicito del usuario: "aumentar un 5%").
#
# BUG DE CALIDAD (encontrado en vivo, 2026-09-02: "existe un cambio de
# velocidad no bien escuchada"): cada oracion es una sintesis SEPARADA (no
# una sola grabacion continua, ver _speak_now), asi que variar "rate" entre
# oraciones se escucha como un salto brusco de ritmo al pegar los clips uno
# tras otro -- un narrador real varia el TONO, no la velocidad, entre frase
# y frase. Fix: "rate" queda FIJO igual en las 3, la variacion de estilo
# ahora es SOLO de pitch (mas sutil que antes: 3Hz/6Hz en vez de 4Hz/9Hz).
_EDGE_STYLE_PARAMS = {
    "narration": {"rate": "+17%"},
    "dialogue": {"pitch": "+3Hz", "rate": "+17%"},
    "exclaim": {"pitch": "+6Hz", "rate": "+17%"},
}


class SpeechQueue:
    """Serializa la narracion: toma de cache (o sintetiza) y reproduce una
    linea a la vez en un hilo aparte.

    cache_enabled=False (default, pedido explicito del usuario 2026-09-02:
    "sin cache, nada se guarda" -- el cache de audio real llego a pesar 15GB
    con solo 4765 de 14824 misiones): cada linea se sintetiza a un archivo de
    SCRATCH en %TEMP% (no en la carpeta del proyecto) y se borra apenas
    termina de reproducirse -- cero acumulacion en disco, a cambio de volver
    a sintetizar (y, para voces edge, volver a pedir internet) cada vez,
    incluso repitiendo la misma linea.
    """

    def __init__(
        self,
        voices_config: dict,
        base_dir: Path,
        cache_dir: Path,
        max_depth: int,
        cache_enabled: bool = False,
        cache_max_mb: int = 0,
    ):
        self._voices_config = voices_config
        self._base_dir = base_dir
        self._cache_enabled = cache_enabled
        max_bytes = int(cache_max_mb * 1024 * 1024) if cache_enabled and cache_max_mb else None
        self._cache = VoiceCache(
            cache_dir if cache_enabled else Path(tempfile.gettempdir()) / "narrador_ia_scratch",
            max_bytes=max_bytes,
        )
        if not cache_enabled:
            # Verificacion de errores (2026-09-02): un cierre forzado de la
            # app a mitad de reproduccion (crash, o el usuario matando el
            # proceso) salta el "finally: path.unlink()" de _speak_now y deja
            # el archivo temporal huerfano -- confirmado en esta sesion, 29
            # archivos / 13MB acumulados tras varios reinicios. Como el modo
            # sin cache promete "nada se guarda", se limpia el scratch entero
            # al arrancar, no solo despues de cada reproduccion.
            for stale in self._cache.root.glob("*"):
                if stale.is_file():
                    stale.unlink(missing_ok=True)
        self._queue: "queue.Queue[tuple[str, str]]" = queue.Queue()
        # Cola aparte para pedidos explicitos/automaticos del Tracker (ver
        # NarratorBridge.lua): siempre se atiende antes que el chat ambiental.
        self._priority_queue: "queue.Queue[tuple[str, str]]" = queue.Queue()
        # Narracion ambiental aleatoria (2026-09-05, pedido explicito del
        # usuario: historias/leyendas/consejos que suenan solos mientras se
        # juega) -- PRIORIDAD MAS BAJA de las 3: si el jugador hace click en
        # "Narrar" mientras suena un episodio, se corta igual que cualquier
        # otra cosa de baja prioridad (misma señal _interrupt). Ver
        # AmbientNarrator (src/ambient_narrator.py), que la alimenta con un
        # temporizador aleatorio propio, independiente de esta cola.
        self._ambient_queue: "queue.Queue[Path]" = queue.Queue()
        self._max_depth = max_depth
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._stop = threading.Event()
        # Señal para el propio hilo worker: los alias de MCI son por hilo
        # (confirmado en esta sesion -- un "stop" desde OTRO hilo falla con
        # "dispositivo no reconocido"), asi que say_now() no puede cortar la
        # reproduccion en curso directamente. En cambio, prende esta señal;
        # _speak_now()/play_file_blocking() la revisan desde DENTRO del
        # propio worker y se cortan solas.
        self._interrupt = threading.Event()
        # CARRERA (encontrada en verificacion, 2026-09-02): say_now() corre en
        # el hilo principal (narrator.py) mientras _worker corre en su propio
        # hilo. Sin este lock existia una ventana de microsegundos entre que
        # _worker sacaba un pedido de _priority_queue y llamaba a
        # _speak_now() (que limpiaba self._interrupt como primer paso): un
        # say_now() nuevo que llegara justo en esa ventana prendia la señal
        # de corte, pero _speak_now() la apagaba enseguida sin haber cortado
        # nada -- el pedido viejo terminaba de sonar completo antes del
        # nuevo, justo el caso (aceptar + primer progreso casi seguidos, o
        # doble click rapido) que say_now() existe para resolver. Fix: sacar
        # el pedido de la cola y limpiar la señal son ahora una sola
        # operacion atomica (mismo lock que usan say_now()/stop_now() al
        # vaciar/prender la señal), asi ninguna de las dos puede "colarse" a
        # mitad de la otra.
        self._lock = threading.Lock()
        self._enabled = True

        # CACHE EN RAM de repeticiones EXACTAS (2026-09-02, pedido explicito
        # del usuario: "que sea instantaneo si es posible"). Medido en esta
        # sesion con el motor edge-tts real: el "piso" de una sintesis nueva
        # es ~0.7s SOLO de conexion (TLS+WebSocket a los servidores de
        # Microsoft) antes de recibir el primer byte de audio -- ese numero
        # no cambia sea cual sea el largo del texto, y no hay forma de
        # bajarlo desde este lado sin evitar la llamada de red por completo
        # para ese texto puntual (confirmado leyendo edge_tts/communicate.py:
        # abre una ClientSession+WebSocket nueva en cada llamada, no expone
        # un mecanismo real de reutilizar la conexion entre llamadas).
        # Esto es DISTINTO del cache en disco (cache_enabled, sigue apagado
        # por decision explicita del usuario: crecio a 15GB sin limite antes)
        # -- vive solo en memoria, se pierde al cerrar la app, y tiene un
        # tope chico de entradas para no crecer sin control tampoco. Cubre
        # el caso real de "la MISMA linea se repite" (reabrir el libro de
        # una mision ya narrada, un progreso que se re-anuncia, doble click
        # en Narrar) con audio verdaderamente instantaneo -- no ayuda la
        # PRIMERA vez que se narra una linea nueva, ese primer segundo de
        # conexion es un piso fisico de red, no un bug de codigo.
        self._mem_cache: "collections.OrderedDict[tuple, bytes]" = collections.OrderedDict()
        self._mem_cache_max = 60

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        if not enabled:
            self._drain()

    def _drain(self) -> None:
        try:
            while True:
                self._queue.get_nowait()
        except queue.Empty:
            pass

    def say(self, text: str, voice_name: str) -> None:
        if not self._enabled:
            return
        if self._queue.qsize() >= self._max_depth:
            # Se acumulo texto de sobra (jugador AFK, pico de chat, etc.): se
            # prioriza ponerse al dia antes que leer todo el historial.
            self._drain()
        self._queue.put((text, voice_name))

    def _drain_priority(self) -> None:
        try:
            while True:
                self._priority_queue.get_nowait()
        except queue.Empty:
            pass

    def say_now(self, text: str, voice_name: str) -> None:
        """Pedido explicito/automatico del Tracker: SIN cola (2026-09-02,
        pedido explicito del usuario -- antes se acumulaban todos los clicks/
        misiones pendientes y se reproducian uno tras otro, incluso viejos).
        Cada pedido nuevo reemplaza a cualquiera pendiente y corta lo que
        este sonando ahora mismo -- solo importa el mas reciente."""
        if not self._enabled:
            return
        with self._lock:
            self._drain_priority()
            self._interrupt.set()
            self._priority_queue.put((text, voice_name))

    def play_ambient(self, path: Path) -> None:
        """Encola un episodio de narracion ambiental pre-generado (archivo
        .wav ya listo, ver tools/build_ambient_clips.py) -- NO reemplaza ni
        corta lo que ya este sonando (a diferencia de say_now): si hay algo
        en curso, este episodio simplemente espera su turno detras, con la
        prioridad mas baja de las 3 colas."""
        if not self._enabled:
            return
        self._ambient_queue.put(path)

    def stop_now(self) -> None:
        """Corta lo que este sonando y vacia ambas colas SIN reemplazar por
        nada nuevo -- pedido por NarratorBridge.lua al detectar cambio de
        zona/mapa/instancia o al cargar el addon (login/cambio de personaje/
        reloadui), ver src/plugindata.py:StopSignalReader. A diferencia de
        say_now(), esto no encola una narracion nueva: la idea es silencio,
        no continuar con otra cosa."""
        with self._lock:
            self._drain()
            self._drain_priority()
            self._interrupt.set()

    def _worker(self) -> None:
        while not self._stop.is_set():
            kind = None
            with self._lock:
                try:
                    text, voice_name = self._priority_queue.get_nowait()
                    kind = "speak"
                except queue.Empty:
                    try:
                        # BUG DE LATENCIA (encontrado en vivo, 2026-09-02: "se
                        # demora mucho" desde el click hasta el audio): este
                        # timeout era 0.2s -- si say_now() ponia un pedido
                        # prioritario justo cuando este hilo ya estaba
                        # bloqueado aca (caso comun: la cola ambiental esta
                        # vacia casi siempre con los canales apagados), no se
                        # notaba hasta que expiraba el timeout completo.
                        # Bajado a 0.02s: el costo es revisar la cola vacia
                        # mas seguido (insignificante para CPU), la ganancia
                        # es hasta 180ms menos de demora.
                        text, voice_name = self._queue.get(timeout=0.02)
                        kind = "speak"
                    except queue.Empty:
                        # Tercer nivel, el mas bajo de los 3 (2026-09-05):
                        # episodios ambientales pre-generados. get_nowait()
                        # aca (no timeout) porque ya se esperaron los 0.02s
                        # de la cola de chat arriba -- esperar de nuevo solo
                        # demoraria detectar un pedido prioritario nuevo.
                        try:
                            ambient_path = self._ambient_queue.get_nowait()
                            kind = "ambient"
                        except queue.Empty:
                            continue
                # Sacar el pedido y limpiar la señal de corte es una sola
                # operacion atomica junto con say_now()/stop_now() (mismo
                # lock) -- ver comentario en __init__ sobre la carrera que
                # esto evita. Vale igual para los 3 niveles: un say_now()
                # que llegue justo aca encuentra la señal ya limpia, nunca a
                # mitad de sacar un pedido de cualquiera de las 3 colas.
                self._interrupt.clear()
            if not self._enabled:
                continue
            try:
                if kind == "ambient":
                    play_file_blocking(ambient_path, should_stop=self._interrupt.is_set)
                else:
                    self._speak_now(text, voice_name)
            except Exception as exc:
                print(f"[Narrador_IA] Error al sintetizar/reproducir: {exc}")

    def _synthesize(self, text: str, voice_name: str, style: str = "narration") -> Path:
        # El estilo forma parte de la clave de cache: la MISMA oracion podria
        # sonar distinta segun el estilo con el que se pida (pitch/rate
        # distintos), asi que no pueden compartir archivo.
        cache_key_voice = voice_name if style == "narration" else f"{voice_name}__{style}"
        cached = self._cache.lookup(cache_key_voice, text) if self._cache_enabled else None
        if cached:
            return cached

        voice_cfg = dict(self._voices_config[voice_name])
        engine = voice_cfg.get("engine", "edge")
        if engine == "edge":
            voice_cfg.update(_EDGE_STYLE_PARAMS.get(style, {}))

        ext = "mp3" if engine == "edge" else "wav"
        if self._cache_enabled:
            out_path = self._cache.path_for(cache_key_voice, text, ext)
        else:
            # Sin cache: cada sintesis usa un nombre UNICO (2026-09-02, bug
            # real encontrado en esta sesion) -- path_for() por contenido
            # colisiona si el mismo texto/voz/estilo se repite dentro de una
            # misma narracion (ej. una oracion identica dos veces), y en modo
            # sin cache el archivo se borra apenas se reproduce una vez
            # (ver _speak_now): la segunda reproduccion encontraba el
            # archivo ya borrado por la primera.
            out_path = self._cache.root / f"{uuid.uuid4().hex}.{ext}"

        mem_key = (cache_key_voice, text)
        mem_hit = self._mem_cache.get(mem_key)
        if mem_hit is not None:
            # Repeticion exacta dentro de esta sesion (ver nota en __init__)
            # -- se escribe el archivo desde los bytes ya guardados en RAM,
            # SIN llamar al motor/red: esto es lo que de verdad puede ser
            # instantaneo, a diferencia de una sintesis nueva.
            self._mem_cache.move_to_end(mem_key)
            out_path.write_bytes(mem_hit)
            return out_path

        try:
            ENGINE_FUNCS[engine](text, voice_cfg, out_path, self._base_dir)
            if self._cache_enabled:
                # Poda por tope DESPUES de escribir el archivo nuevo -- ver
                # VoiceCache.enforce_limit(). No hace nada si no hay
                # cache_max_mb configurado (cache sin tope, comportamiento
                # de siempre).
                self._cache.enforce_limit()
            self._mem_cache[mem_key] = out_path.read_bytes()
            self._mem_cache.move_to_end(mem_key)
            while len(self._mem_cache) > self._mem_cache_max:
                self._mem_cache.popitem(last=False)
            return out_path
        except Exception as exc:
            if voice_name == FALLBACK_VOICE_NAME:
                # Si hasta la propia voz de respaldo fallo, no hay a donde
                # mas caer -- que se propague y lo maneje _worker (loguea y
                # sigue con lo siguiente, no deja el hilo muerto).
                raise
            print(f"[Narrador_IA] Motor '{engine}' fallo ({exc}); usando '{FALLBACK_VOICE_NAME}' de respaldo.")
            # El respaldo tambien es una voz "edge": debe llevar el mismo
            # pitch/rate de estilo (narracion/dialogo/exclamacion) que
            # llevaba el pedido original -- si no, la frase de respaldo suena
            # sin variacion de tono en medio de una narracion que si la tiene
            # (encontrado en verificacion, 2026-09-02: faltaba aca).
            fallback_cfg = dict(self._voices_config[FALLBACK_VOICE_NAME])
            fallback_cfg.update(_EDGE_STYLE_PARAMS.get(style, {}))
            fallback_cache_key = (
                FALLBACK_VOICE_NAME if style == "narration" else f"{FALLBACK_VOICE_NAME}__{style}"
            )
            fallback_path = (
                self._cache.path_for(fallback_cache_key, text, "mp3")
                if self._cache_enabled
                else self._cache.root / f"{uuid.uuid4().hex}.mp3"
            )
            edge_engine.synthesize(text, fallback_cfg, fallback_path, self._base_dir)
            return fallback_path

    def _speak_now(self, text: str, voice_name: str) -> None:
        # La señal de corte ya se limpio en _worker(), atomicamente junto con
        # sacar este pedido de su cola (ver comentario en __init__) -- no se
        # repite aca para no reabrir la misma ventana de carrera.
        # Se narra oracion por oracion (no todo el texto en una sola llamada
        # al motor) para poder variar pitch/rate segun si es dialogo,
        # exclamacion o narracion plana -- ver text_utils.segment_for_narration.
        segments = segment_for_narration(text) or [{"text": text, "style": "narration"}]

        if len(segments) == 1:
            path = self._synthesize(segments[0]["text"], voice_name, segments[0]["style"])
            try:
                play_file_blocking(path, should_stop=self._interrupt.is_set)
            finally:
                if not self._cache_enabled:
                    path.unlink(missing_ok=True)
            return

        # BUG DE LATENCIA (encontrado en vivo, 2026-09-02: "podemos mejorar
        # el tiempo de reaccion entre el click y que narre"): esto sintetiza
        # las oraciones en paralelo, pero antes esperaba a que TODAS
        # terminaran (list(pool.map(...)) bloquea hasta el ultimo resultado)
        # antes de reproducir la primera -- si una oracion tardaba mas, el
        # tiempo hasta el primer sonido era el de la MAS LENTA, no el de la
        # primera. Fix: se somete todo el trabajo de una (pool.submit, no
        # bloquea), y se reproduce cada oracion apenas SU PROPIO future esta
        # listo, mientras las siguientes se siguen sintetizando de fondo --
        # el tiempo hasta el primer sonido pasa a ser el de la primera
        # oracion sola, no el de todo el lote.
        pool = ThreadPoolExecutor(max_workers=min(len(segments), 6))
        try:
            futures = [
                pool.submit(self._synthesize, seg["text"], voice_name, seg["style"]) for seg in segments
            ]
            for future in futures:
                if self._interrupt.is_set():
                    break
                path = future.result()
                try:
                    play_file_blocking(path, should_stop=self._interrupt.is_set)
                finally:
                    if not self._cache_enabled:
                        path.unlink(missing_ok=True)
        finally:
            # wait=False + cancel_futures=True: si se corto por interrupcion,
            # no hace falta esperar a que terminen de sintetizarse oraciones
            # que ya no se van a reproducir.
            pool.shutdown(wait=False, cancel_futures=True)
