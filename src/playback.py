"""Reproduccion de audio unificada (mp3 de edge-tts, wav de xtts) con el
mismo codigo. winsound (usado antes) no reproduce mp3, y pygame no tiene
wheel prebuilda para Python 3.14 (demasiado nuevo, forzaria compilar desde
codigo fuente) -- en vez de eso se usa MCI (winmm.dll) via ctypes, que viene
con Windows y reproduce ambos formatos sin dependencias externas.
"""
from __future__ import annotations

import ctypes
import itertools
import shutil
import tempfile
import time
from pathlib import Path

_winmm = ctypes.WinDLL("winmm")
_alias_counter = itertools.count()

# El comando "open" de mciSendString tiene un limite heredado (~127
# caracteres de linea completa, documentado en la practica aunque no en
# MSDN) que revienta con el mismo error de "nombre de archivo invalido" de
# los nombres 8.3 -- confirmado en esta sesion: falla con la ruta larga de
# este proyecto (OneDrive/Desktop/... con espacios) pero funciona igual con
# la MISMA extension/tipo desde una ruta corta. En vez de depender de que el
# volumen tenga nombres 8.3 habilitados (no siempre, sobre todo en SSD),
# cada reproduccion copia el archivo a una ruta corta y fija en %TEMP% antes
# de abrirlo con MCI. El nombre incluye el alias (no un nombre fijo) para
# que dos reproducciones seguidas nunca compitan por el mismo archivo
# mientras una todavia esta abierta en MCI.
_STAGING_DIR = Path(tempfile.gettempdir())

# Sin "type" explicito, el parser de comandos de mciSendString intenta
# adivinar el tipo por el nombre de archivo con una rutina heredada que
# rechaza nombres largos -- se declara el tipo a mano.
_MCI_TYPE = {".wav": "waveaudio", ".mp3": "mpegvideo"}


class PlaybackError(RuntimeError):
    pass


def _mci(command: str) -> str:
    buf = ctypes.create_unicode_buffer(256)
    error = _winmm.mciSendStringW(command, buf, len(buf), None)
    if error:
        err_buf = ctypes.create_unicode_buffer(256)
        _winmm.mciGetErrorStringW(error, err_buf, len(err_buf))
        raise PlaybackError(f"MCI '{command}' fallo: {err_buf.value}")
    return buf.value


def play_file_blocking(path: Path, should_stop=None) -> None:
    """Reproduce hasta que termine solo, o hasta que should_stop() (si se
    pasa) devuelva True.

    IMPORTANTE (confirmado en esta sesion): los alias de MCI son por HILO --
    un "stop alias" mandado desde un hilo distinto al que hizo "open" falla
    con "el dispositivo especificado no esta abierto", y "play alias wait"
    tampoco se deja interrumpir asi desde afuera. Por eso NO hay una funcion
    stop_current() que otro hilo pueda llamar: en cambio, se reproduce SIN
    "wait" y este mismo hilo sondea su propio estado cada 50ms, revisando
    should_stop() en cada vuelta -- el corte (si hace falta) lo pide el
    mismo hilo dueno del dispositivo, nunca otro.
    """
    path = path.resolve()
    alias = f"narrador_{next(_alias_counter)}"
    staged = _STAGING_DIR / f"narrador_ia_{alias}{path.suffix.lower()}"
    shutil.copyfile(path, staged)

    mci_type = _MCI_TYPE.get(staged.suffix.lower())
    type_clause = f" type {mci_type}" if mci_type else ""
    _mci(f'open "{staged}"{type_clause} alias {alias}')
    try:
        _mci(f"play {alias}")
        while True:
            if should_stop is not None and should_stop():
                try:
                    _mci(f"stop {alias}")
                except PlaybackError:
                    pass
                break
            status = _mci(f"status {alias} mode").strip().lower()
            if status != "playing":
                break
            time.sleep(0.05)
    finally:
        try:
            _mci(f"close {alias}")
        except PlaybackError:
            pass
        staged.unlink(missing_ok=True)
