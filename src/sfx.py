"""Reproduce efectos de sonido cortos (fanfarria de mision, pergamino,
click de UI -- ver NarratorBridge.lua:SignalSfx) SIN pasar por sintesis de
voz: son archivos de audio ya generados (ver tools/gen_sfx.py), no texto.

Cada pedido se reproduce en un hilo daemon aparte con su propio alias MCI
(ver playback.py) -- winmm soporta varios alias de dispositivo abiertos en
simultaneo, asi que un efecto corto suena SUPERPUESTO a la narracion en
curso (SpeechQueue tiene su propio hilo/alias independiente) en vez de
esperar turno detras de ella o cortarla.
"""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Optional

from playback import play_file_blocking

_EXTENSIONS = (".wav", ".mp3")


class SfxPlayer:
    def __init__(self, sfx_dir: Path, enabled: bool = True):
        self._sfx_dir = sfx_dir
        self._enabled = enabled
        # Aviso UNA sola vez por nombre faltante -- si el archivo no existe
        # (todavia no se genero/reemplazo), no tiene sentido repetir el
        # mismo error en consola cada vez que el jugador clickea una fila.
        self._warned = set()

    def play(self, name: str) -> None:
        if not self._enabled or not name:
            return
        path = self._resolve(name)
        if path is None:
            if name not in self._warned:
                self._warned.add(name)
                print(f"[Narrador_IA] SFX '{name}' no encontrado en {self._sfx_dir} (.wav/.mp3) -- se ignora.")
            return
        threading.Thread(target=self._play_safe, args=(path,), daemon=True).start()

    @staticmethod
    def _play_safe(path: Path) -> None:
        try:
            play_file_blocking(path)
        except Exception as exc:
            print(f"[Narrador_IA] Error reproduciendo SFX '{path.name}': {exc}")

    def _resolve(self, name: str) -> Optional[Path]:
        for ext in _EXTENSIONS:
            candidate = self._sfx_dir / f"{name}{ext}"
            if candidate.is_file():
                return candidate
        return None
