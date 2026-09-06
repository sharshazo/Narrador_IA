"""Vigia de LOTRO: inicia/detiene Narrador_IA automaticamente segun si el
juego esta corriendo -- pedido explicito del usuario (2026-09-03):
"necesito que se abra solo cuando se abra lotro" (y antes se quejo de que
Narrador_IA no se cerraba solo al cerrar el juego).

Este script NO hace narracion en si -- solo revisa cada CHECK_INTERVAL_SECONDS
si lotroclient64.exe esta en la lista de procesos (via tasklist, sin
dependencias nuevas) y prende/apaga src/narrator.py como proceso hijo segun
corresponda. Pensado para dejarse corriendo SIEMPRE de fondo (arranca con
Windows, ver start_watcher.bat + carpeta de Inicio) -- mientras LOTRO no este
abierto, el costo es una llamada a tasklist cada 5s, practicamente gratis.

Uso manual (sin autoarranque): .venv\\Scripts\\pythonw.exe watcher.py
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

LOTRO_PROCESS = "lotroclient64.exe"
APP_DIR = Path(__file__).resolve().parent
NARRATOR_SCRIPT = APP_DIR / "src" / "narrator.py"
PYTHON_EXE = APP_DIR / ".venv" / "Scripts" / "python.exe"
CHECK_INTERVAL_SECONDS = 5

CREATE_NO_WINDOW = 0x08000000


def _is_process_running(name: str) -> bool:
    result = subprocess.run(
        ["tasklist", "/FI", f"IMAGENAME eq {name}"],
        capture_output=True,
        text=True,
        creationflags=CREATE_NO_WINDOW,
    )
    return name.lower() in result.stdout.lower()


def main() -> None:
    narrator_proc: "subprocess.Popen | None" = None
    print(f"[Vigia] Esperando a que se abra LOTRO ({LOTRO_PROCESS})...", flush=True)

    while True:
        lotro_running = _is_process_running(LOTRO_PROCESS)
        # narrator_proc.poll() devuelve None mientras el proceso sigue vivo --
        # tambien detecta correctamente si el usuario cerro la consola de
        # Narrador_IA a mano (poll() refleja el estado REAL del proceso, no
        # solo lo que este script recuerda haber lanzado).
        narrator_alive = narrator_proc is not None and narrator_proc.poll() is None

        if lotro_running and not narrator_alive:
            print("[Vigia] LOTRO detectado -- iniciando Narrador_IA...", flush=True)
            # CREATE_NO_WINDOW (no CREATE_NEW_CONSOLE): pedido explicito del
            # usuario -- no hace falta la ventana de consola, el icono de
            # bandeja (src/tray.py) ya alcanza para pausar/reanudar/salir.
            # Sigue usando python.exe (no pythonw.exe): con pythonw sys.stdout
            # es None y print() revienta en el primer log; con python.exe +
            # CREATE_NO_WINDOW el proceso tiene consola real, solo que oculta.
            narrator_proc = subprocess.Popen(
                [str(PYTHON_EXE), "-u", str(NARRATOR_SCRIPT)],
                cwd=str(APP_DIR),
                creationflags=CREATE_NO_WINDOW,
            )
        elif not lotro_running and narrator_alive:
            print("[Vigia] LOTRO se cerro -- deteniendo Narrador_IA...", flush=True)
            narrator_proc.terminate()
            try:
                narrator_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                narrator_proc.kill()
            narrator_proc = None
            print(f"[Vigia] Esperando a que se abra LOTRO de nuevo...", flush=True)

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
