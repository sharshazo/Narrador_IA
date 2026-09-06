"""Precalienta VoiceOverData/cache/ con un lote de misiones reales.

Herramienta de desarrollo (no forma parte de la app en ejecucion, narrator.py
no la importa): lee un export generado por
LOTRO_Quest_Assistant/extract_for_narration.lua (mismo texto exacto que
produciria Core/NarratorBridge.lua en el juego, con el fix de plantillas de
genero ya aplicado) y sintetiza+cachea cada mision con la MISMA voz que le
tocaria en produccion (src/npc_voice.py, incluyendo el override de
personajes principales) -- asi cuando el jugador la active de verdad en el
Tracker, ya sale instantaneo de la cache.

Resumible: como la cache es por contenido (voz+texto), volver a correr este
script sobre el mismo export salta todo lo ya generado -- interrumpir con
Ctrl+C o que se caiga a mitad de un lote nocturno no pierde el progreso.

Uso: .venv\\Scripts\\python.exe warm_cache.py [ruta_export.lua] [workers]
"""
from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import luadata

sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import load_config
from npc_voice import voice_for_npc
from tts import SpeechQueue

APP_DIR = Path(__file__).parent
MAX_RETRIES = 3


def synth_one(sq: SpeechQueue, q: dict, voice_name: str) -> Path:
    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return sq._synthesize(q["text"], voice_name)
        except Exception as exc:  # motor externo (edge/xtts) caido momentaneamente
            last_exc = exc
            if attempt < MAX_RETRIES:
                time.sleep(1.5 * attempt)
    raise last_exc  # type: ignore[misc]


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.isdigit()]
    workers = next((int(a) for a in sys.argv[1:] if a.isdigit()), 6)
    export_path = Path(args[0]) if args else APP_DIR / "narration_export.lua"

    quests = luadata.unserialize(export_path.read_text(encoding="utf-8"), encoding="utf-8")
    cfg = load_config(APP_DIR / "config.yaml")
    # cache_enabled=True siempre aca, sin importar config.yaml: el trabajo de
    # esta herramienta ES precalentar el cache persistente -- si el usuario
    # desactivo el cache para el uso normal (ver src/tts.py), este script
    # solo tiene sentido si de verdad se quiere reconstruir ese cache.
    sq = SpeechQueue(cfg["voices"], APP_DIR, APP_DIR / cfg["cache_dir"], cfg["max_queue_depth"], cache_enabled=True)

    total = len(quests)
    print(f"Lote: {total} misiones, {workers} workers en paralelo, export={export_path.name}", flush=True)

    ok = 0
    failed = 0
    started = time.monotonic()

    def process(q: dict) -> tuple[dict, str, Path | None, Exception | None]:
        voice_name = voice_for_npc(q.get("bestower", ""), cfg["npc_voice_pool"], cfg.get("main_npcs"))
        try:
            path = synth_one(sq, q, voice_name)
            return q, voice_name, path, None
        except Exception as exc:
            return q, voice_name, None, exc

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(process, q) for q in quests]
        for i, fut in enumerate(as_completed(futures), start=1):
            q, voice_name, path, exc = fut.result()
            if exc is not None:
                failed += 1
                print(f"[{i}/{total}] FAIL ndx={q['ndx']:<6} voz={voice_name:<12} {q['title']}: {exc}", flush=True)
            else:
                ok += 1
                if i % 25 == 0 or i == total:
                    elapsed = time.monotonic() - started
                    rate = i / elapsed if elapsed > 0 else 0
                    eta_min = (total - i) / rate / 60 if rate > 0 else float("inf")
                    print(
                        f"[{i}/{total}] progreso: {ok} ok, {failed} fallidas -- "
                        f"{rate:.2f} misiones/seg, ETA {eta_min:.1f} min",
                        flush=True,
                    )

    elapsed = time.monotonic() - started
    print(f"\nListo: {ok} generadas/cacheadas, {failed} fallidas, {elapsed / 60:.1f} min total.", flush=True)


if __name__ == "__main__":
    main()
