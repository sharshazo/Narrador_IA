"""Cache de audio en disco: genera cada linea (voz+texto) una sola vez.

Es la "carpeta accesoria de audio" pedida por el usuario, adaptando el
patron de la carpeta generated/sounds/ del addon AI_VoiceOver de WoW -- pero
indexada por contenido (hash de voz+texto) en vez de por tablas de lookup
NPC/quest-ID: mas simple, y se auto-invalida sola si el texto cambia (p.ej.
al mejorar una traduccion) sin necesitar un paso de regeneracion aparte.

Generacion perezosa: una linea (misma voz + mismo texto) solo se sintetiza
la primera vez que se pide; las siguientes veces se reproduce directo desde
disco, gratis y sin depender de internet.

CACHE CON TOPE (2026-09-03, pedido explicito del usuario: "que sea
instantaneo si es posible" -- version anterior de este cache, sin tope,
llego a pesar 15GB con solo 4765/14824 misiones y el usuario lo apago por
eso). `max_bytes` (si se pasa) activa un limite duro: cuando el total del
cache se pasa de ese numero, se borran los archivos usados hace MAS TIEMPO
primero (LRU real por mtime, no por orden de creacion) hasta volver a estar
por debajo del limite. `lookup()` "toca" el archivo en cada hit (actualiza
su mtime) para que una linea que se sigue usando nunca sea la candidata a
borrarse solo por haberse creado temprano.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional


class VoiceCache:
    def __init__(self, root: Path, max_bytes: Optional[int] = None):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.max_bytes = max_bytes

    def _key(self, voice_name: str, text: str) -> str:
        return hashlib.sha1(f"{voice_name}:{text}".encode("utf-8")).hexdigest()[:20]

    def path_for(self, voice_name: str, text: str, ext: str) -> Path:
        return self.root / f"{self._key(voice_name, text)}.{ext}"

    def lookup(self, voice_name: str, text: str) -> Optional[Path]:
        for ext in ("wav", "mp3"):
            candidate = self.path_for(voice_name, text, ext)
            if candidate.is_file():
                try:
                    # Refresca mtime en cada hit -- ver nota de clase: asi
                    # enforce_limit() borra lo REALMENTE viejo (sin pedirse
                    # hace tiempo), no solo lo creado primero.
                    candidate.touch()
                except OSError:
                    pass
                return candidate
        return None

    def enforce_limit(self) -> None:
        """Poda el cache si se paso de max_bytes -- se llama despues de cada
        escritura nueva (ver tts.py). Sin max_bytes configurado, no hace
        nada (mismo comportamiento sin tope de siempre)."""
        if not self.max_bytes:
            return
        try:
            files = [f for f in self.root.iterdir() if f.is_file()]
        except OSError:
            return
        try:
            sized = [(f, f.stat().st_size, f.stat().st_mtime) for f in files]
        except OSError:
            return
        total = sum(size for _, size, _ in sized)
        if total <= self.max_bytes:
            return
        # Mas viejo (mtime mas chico) primero -- se borra hasta volver a
        # estar por debajo del limite.
        sized.sort(key=lambda item: item[2])
        for f, size, _ in sized:
            if total <= self.max_bytes:
                break
            try:
                f.unlink()
                total -= size
            except OSError:
                continue
