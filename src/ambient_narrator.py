"""Narracion ambiental aleatoria durante el juego (2026-09-05, pedido
explicito del usuario): "muchas narraciones basadas en la historia,
leyendas, consejos... que el narrador nos observe y nos motive... que se
vayan reproduciendo aleatoreamente mientras estemos jugando".

Un temporizador propio (intervalo aleatorio entre disparos) encola episodios
en SpeechQueue con la prioridad MAS BAJA (ver tts.py:play_ambient) -- si el
jugador hace click en "Narrar" para una mision mientras suena un episodio,
se corta al instante (misma señal de corte que usa todo lo demas), y este
temporizador sigue su curso aparte para el proximo episodio, sin verse
afectado por esa interrupcion.
"""
from __future__ import annotations

import random
import threading
from pathlib import Path
from typing import Optional


class AmbientNarrator:
    def __init__(
        self,
        pool_dir: Path,
        speech_queue,
        min_interval_s: float,
        max_interval_s: float,
        enabled: bool = True,
    ):
        self._pool_dir = pool_dir
        self._speech_queue = speech_queue
        self._min_interval_s = min_interval_s
        self._max_interval_s = max_interval_s
        self._enabled = enabled
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._last_clip: Optional[Path] = None

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def _pick_clip(self) -> Optional[Path]:
        # mp3 (formato actual, ver tools/convert_to_mp3 -- pedido explicito
        # del usuario "pasa los audios a mp3 para bajar los mb") + wav (por
        # si algun clip viejo/nuevo quedara sin convertir).
        pool = (
            sorted(self._pool_dir.glob("*.mp3")) + sorted(self._pool_dir.glob("*.wav"))
            if self._pool_dir.exists()
            else []
        )
        if not pool:
            return None
        # No repetir el mismo episodio 2 veces seguidas, si hay para elegir.
        if len(pool) > 1 and self._last_clip in pool:
            pool = [p for p in pool if p != self._last_clip]
        choice = random.choice(pool)
        self._last_clip = choice
        return choice

    def _run(self) -> None:
        while not self._stop.is_set():
            wait_s = random.uniform(self._min_interval_s, self._max_interval_s)
            # Event.wait() devuelve True si stop() se prendio DURANTE la
            # espera -- permite salir al instante en vez de esperar el
            # intervalo completo al cerrar LOTRO.
            if self._stop.wait(wait_s):
                break
            if not self._enabled:
                continue
            clip = self._pick_clip()
            if clip is not None:
                self._speech_queue.play_ambient(clip)
