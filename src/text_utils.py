"""Limpieza y filtrado de texto antes de mandarlo a sintesis de voz."""
from __future__ import annotations

import re
import time

# 2026-09-02 (pedido explicito del usuario: "a veces narra codigos o barras,
# o guion" -- la sintesis lee literal cosas que el texto fuente nunca
# penso para narrarse en voz alta):
#
# - Contadores de progreso SIN RELLENAR, ej. "derrotados (/)" -- QuestLocES
#   viene extraido de forma estatica (LotRO Companion), no del estado real
#   del juego, asi que estos contadores nunca tienen numeros de verdad
#   (el progreso real ya se narra aparte, con numeros reales, via
#   NarratorBridge.AnnounceProgress). Se descartan enteros, con o sin
#   digitos a los lados.
#
# 2026-09-02 (auditoria completa de las 14824 misiones reales, pedido
# explicito del usuario: "verifica que no narre codigos o errores"): se
# encontraron 4 patrones mas que no estaban cubiertos:
# - Etiquetas de escena/formato en <...> mas alla de rgb/u (ej.
#   "<Armund sighs>", "<b>"), generalizado a cualquier <...>. Tambien un
#   fragmento malformado sin el "<" de apertura, ej. "rgb=#FF0000>" (el dato
#   fuente ya vino roto asi en algunas misiones -- no es algo que nuestro
#   pipeline rompio, se limpia igual).
# - "\q" literal (2 caracteres) donde el dato fuente queria una comilla.
# - ". ," (punto seguido de coma) -- resto de un nombre/titulo de jugador ya
#   vacio en el dato original, nunca gramatical en español.
# - Plantilla de genero SIN el prefijo "$", ej. "{un amigo[m]|una amiga[f]}"
#   -- mismo concepto que ${PLAYERNAME:...} pero un formato de dato distinto
#   que el filtro anterior no cubria. Se resuelve igual, a la variante [m].
_MARKUP_RE = re.compile(r"<[^<>]*>|\b\w+=#[0-9A-Fa-f]{6}>")
_LITERAL_Q_RE = re.compile(r"\\q")
_PERIOD_COMMA_RE = re.compile(r"\.\s*,")
# Segunda vuelta de auditoria: el dato fuente trae el orden [m]/[f] en
# CUALQUIERA de los dos sentidos (ej. "{hermana[f]|hermano[m]}") -- se
# resuelven ambos ordenes, siempre a la variante [m].
_BARE_GENDER_TEMPLATE_RE = re.compile(r"\{([^{}|]*)\[m\]\s*\|[^{}]*\[f\]\s*\}")
_BARE_GENDER_TEMPLATE_REV_RE = re.compile(r"\{[^{}|]*\[f\]\s*\|([^{}]*)\[m\]\s*\}")
# "${...}" con "[f]" primero: la limpieza generica de abajo (_TEMPLATE_RE)
# ya los borra enteros como red de seguridad, pero resolverlos a la
# variante [m] (igual que Core/NarratorBridge.lua) da mejor narracion que
# perder la palabra por completo.
_DOLLAR_GENDER_TEMPLATE_RE = re.compile(r"\$\{(?:PLAYERNAME|PLAYER):([^|{}]*)\[m\]\s*\|[^{}]*\[f\]\s*\}")
_DOLLAR_GENDER_TEMPLATE_REV_RE = re.compile(r"\$\{(?:PLAYERNAME|PLAYER):[^|{}]*\[f\]\s*\|([^{}]*)\[m\]\s*\}")
_TEMPLATE_RE = re.compile(r"\$\{[^}]*\}")
# Restos de "\n"/"\ n" (con espacio) que no fueron un salto de linea real
# (ver _LITERAL_NEWLINE_RE) y cualquier backslash suelto que sobreviva --
# confirmado en la auditoria: algunas misiones traen un "\" extra pegado
# antes de una oracion, error de tipeo en el dato fuente original.
_LITERAL_SPACED_N_RE = re.compile(r"\\\s+n\b")
_STRAY_BACKSLASH_RE = re.compile(r"\\")

# Red de seguridad final (auditoria completa, casos raros pero reales: 1 en
# 14824 misiones tenia llaves ANIDADAS rotas en el dato fuente -- imposible
# de resolver de forma limpia con regex normal -- y varias tenian "</rgb>>"
# con un ">" de mas, typo del dato original). Todo lo que llegue hasta aca
# ya paso por los resolvers especificos de arriba; si sobrevive algun "<",
# ">" huerfano o resto de plantilla de genero, mejor borrarlo que leerlo.
_ORPHAN_ANGLE_RE = re.compile(r"[<>]")
_ORPHAN_GENDER_FRAGMENT_RE = re.compile(r"[{}|]|\[[mf]\]")
_EMPTY_COUNTER_RE = re.compile(r"\(\s*\d*\s*/\s*\d*\s*\)")
# " - " (guion con espacios a los dos lados, usado como separador/aclaracion)
# se lee literal como "guion" -- se reemplaza por una coma. Un guion PEGADO
# a las palabras (ej. "Fushaum-doram", un nombre compuesto real) no matchea
# esto (no tiene espacios alrededor) y se deja intacto.
_ISOLATED_DASH_RE = re.compile(r"\s+-\s+")

# 2026-09-02 (pedido explicito del usuario: narracion "extremadamente
# profesional... con expresiones, cambios de tono, dramas"). Investigado
# antes de implementar: edge-tts (motor gratis usado, ver engines/
# edge_engine.py) escapa el texto antes de armar el SSML, asi que estilos
# expresivos tipo mstts:express-as (alegre, dramatico, etc.) NO se pueden
# inyectar -- confirmado leyendo su codigo fuente (mkssml() en
# edge_tts/communicate.py). Lo UNICO real que el motor gratis respeta es
# pitch/rate/volume. Esto separa el texto en oraciones y las clasifica para
# que tts.py sintetice cada una con un pitch/rate distinto -- no es
# "actuacion" real, pero es variacion genuina dentro de lo que existe gratis.
# Python exige lookbehind de ancho fijo -- no se puede usar "[.!?]['\"]?"
# (0 o 1 caracteres) en un solo lookbehind, asi que se alternan dos de ancho
# fijo: termina en .!? solo, o en .!? seguido de una comilla de cierre
# (comun en dialogo, ej. "viajero!'").
_SENTENCE_SPLIT_RE = re.compile(r"(?:(?<=[.!?])|(?<=[.!?][\"']))\s+")


def segment_for_narration(text: str) -> list[dict]:
    sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]
    segments = []
    for s in sentences:
        if "!" in s or s.startswith("¡"):
            style = "exclaim"
        elif s.startswith("'") or s.startswith('"'):
            style = "dialogue"
        else:
            style = "narration"
        segments.append({"text": s, "style": style})
    return segments

# 2026-09-02 (reporte en vivo del usuario: "lectura de codigos como barra
# inversa n barra inversa ene"): Turbine.PluginData.Save guarda los saltos
# de parrafo del texto de origen como la secuencia LITERAL de 2 caracteres
# "\n" (backslash + letra ene), no como un salto de linea real -- y
# luadata.unserialize() del lado Python no la reinterpreta de vuelta a un
# salto real al leer el archivo. El resultado: la voz recibe los caracteres
# "\" y "n" tal cual y los deletrea. Se reemplaza por un punto (pausa
# natural, como un cambio de parrafo) antes de cualquier otra limpieza.
_LITERAL_NEWLINE_RE = re.compile(r"\\n")
_LITERAL_CR_RE = re.compile(r"\\r")


class TextFilter:
    def __init__(self, max_chars: int, dedupe_window_seconds: float, ignore_patterns: list[str]):
        self.max_chars = max_chars
        self.dedupe_window_seconds = dedupe_window_seconds
        self._ignore_regexes = [re.compile(p) for p in ignore_patterns]
        self._recent: dict[str, float] = {}

    def clean(self, message: str) -> str:
        message = _LITERAL_NEWLINE_RE.sub(". ", message)
        message = _LITERAL_SPACED_N_RE.sub(". ", message)
        message = _LITERAL_CR_RE.sub("", message)
        message = _LITERAL_Q_RE.sub('"', message)
        message = _MARKUP_RE.sub("", message)
        message = _BARE_GENDER_TEMPLATE_RE.sub(r"\1", message)
        message = _BARE_GENDER_TEMPLATE_REV_RE.sub(r"\1", message)
        message = _DOLLAR_GENDER_TEMPLATE_RE.sub(r"\1", message)
        message = _DOLLAR_GENDER_TEMPLATE_REV_RE.sub(r"\1", message)
        message = _TEMPLATE_RE.sub("", message)
        message = _EMPTY_COUNTER_RE.sub("", message)
        message = _PERIOD_COMMA_RE.sub(".", message)
        message = _STRAY_BACKSLASH_RE.sub("", message)
        message = _ORPHAN_ANGLE_RE.sub("", message)
        message = _ORPHAN_GENDER_FRAGMENT_RE.sub("", message)
        # Al final, no antes: quitar "->"/"<-" (flechas de instrucciones de UI,
        # ej. "'j' -> Selecciona...") y cualquier " - " que haya quedado
        # expuesto recien al borrar el "<"/">" de arriba -- si corriera antes,
        # no alcanzaria a los guiones que la limpieza de angulos deja sueltos.
        message = _ISOLATED_DASH_RE.sub(", ", message)
        message = _PERIOD_COMMA_RE.sub(".", message)  # de nuevo: un fragmento borrado puede dejar ". ," otra vez
        message = re.sub(r"\s+([.,!?;:])", r"\1", message)  # "texto ." -> "texto."
        message = re.sub(r"([.,!?;:])\1+", r"\1", message)  # ".." -> "."
        message = re.sub(r"\s+", " ", message).strip()
        return message

    def should_speak(self, message: str) -> bool:
        if not message:
            return False
        if len(message) > self.max_chars:
            return False
        if any(rx.search(message) for rx in self._ignore_regexes):
            return False

        now = time.monotonic()
        last_seen = self._recent.get(message)
        self._recent[message] = now
        if last_seen is not None and (now - last_seen) < self.dedupe_window_seconds:
            return False

        if len(self._recent) > 200:
            cutoff = now - self.dedupe_window_seconds
            self._recent = {m: t for m, t in self._recent.items() if t >= cutoff}

        return True
