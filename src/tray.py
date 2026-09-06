"""Icono de bandeja del sistema para Narrador_IA: pausar/reanudar y salir."""
from __future__ import annotations

import threading

import pystray
from PIL import Image, ImageDraw


def _make_icon_image(active: bool) -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    color = (70, 170, 255, 255) if active else (140, 140, 140, 255)
    draw.ellipse((4, 4, 60, 60), fill=color)
    draw.polygon([(24, 20), (24, 44), (44, 32)], fill=(255, 255, 255, 255))
    return img


def run_tray(narrator) -> None:
    # Lee narrator.enabled en vez de llevar su propio state["enabled"]
    # local (2026-09-05): con el boton silenciar/activar del Tracker
    # (UI/QuestTrackerHUD.lua) sumandose como OTRA forma de cambiar lo
    # mismo, una copia separada en la bandeja se desincronizaba -- el menu
    # podia decir "Pausar narracion" estando ya en pausa desde el juego, y
    # el proximo click togglear para el lado equivocado. narrator.enabled es
    # ahora la unica fuente de verdad (ver Narrator.set_enabled).
    def on_toggle(icon, item):
        narrator.set_enabled(not narrator.enabled)
        icon.icon = _make_icon_image(narrator.enabled)
        icon.update_menu()

    def on_quit(icon, item):
        narrator.running = False
        icon.stop()

    def on_play_intro(icon, item):
        # Prueba manual (pedido explicito del usuario): funciona SIEMPRE,
        # sin importar intro_enabled ni si ya sono automaticamente en esta
        # sesion -- corre en su propio hilo para no trabar el menu de
        # bandeja mientras dura la narracion.
        threading.Thread(target=narrator.play_intro, daemon=True).start()

    icon = pystray.Icon(
        "narrador_ia",
        # narrator.start() ya corrio (ver main()) y pudo haber arrancado en
        # off si el jugador dejo el boton del Tracker asi en la sesion
        # anterior (ver Narrator.start()) -- el icono de bandeja arranca
        # reflejando eso, no siempre "activo" a ciegas.
        _make_icon_image(narrator.enabled),
        "Narrador IA - LOTRO",
        menu=pystray.Menu(
            pystray.MenuItem(
                lambda item: "Pausar narracion" if narrator.enabled else "Reanudar narracion",
                on_toggle,
            ),
            pystray.MenuItem("Reproducir introduccion", on_play_intro),
            pystray.MenuItem("Salir", on_quit),
        ),
    )

    worker = threading.Thread(target=narrator.run_loop, daemon=True)
    worker.start()
    icon.run()
