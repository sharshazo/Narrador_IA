"""5 narraciones nuevas (2026-09-05, pedido explicito del usuario) con la
voz "narrador_bill" (segunda cuenta de ElevenLabs, gratis) en vez de
"narrador_intro" (Oxley) -- misma arquitectura que build_ambient_clips.py,
guion aparte porque usa otra voz/cuenta. Salen a voices/ambient/ (mismo
pool que las 41 anteriores, para que AmbientNarrator las mezcle con el
resto), sin musica, con graves realzados.

Uso: .venv/Scripts/python.exe tools/build_golodir_batch.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR / "src"))

from audio_fx import apply_narrator_fx  # noqa: E402
from config import load_config  # noqa: E402
from tts import ENGINE_FUNCS  # noqa: E402

VOICE_NAME = "narrador_bill"
OUT_DIR = APP_DIR / "voices" / "ambient"
TMP_DIR = OUT_DIR / "_fragments"

PAUSA = 0.55
PAUSA_LARGA = 1.2

CLIPS: list[tuple[str, str, dict]] = [
    (
        "golodir_y_los_hombres_que_desaparecieron_en_angmar",
        """Viajero...

¿Alguna vez has seguido un camino sabiendo que probablemente nadie regresó por él?

Existe una historia en las tierras del norte que comienza precisamente así.

Hace muchos años, un grupo de hombres se internó en Angmar.

No eran simples viajeros.

Eran guerreros.

Exploradores.

Hombres que habían escuchado historias sobre las ruinas del antiguo reino del Rey Brujo y decidieron descubrir qué quedaba allí.

Al frente de aquella expedición estaba Golodir.

Habían partido con un propósito.

Encontrar respuestas.

Descubrir qué estaba ocurriendo en aquellas tierras.

Y regresar.

Pero Angmar no era un lugar que quisiera recibir visitantes.

El tiempo pasó.

Los hombres dejaron de regresar.

Los rumores comenzaron a extenderse.

Algunos decían que habían sido capturados.

Otros...

que habían muerto.

Y otros preferían no hablar del asunto.

Porque existe una diferencia entre entrar en una tierra peligrosa...

y entrar en una tierra donde la propia historia parece estar esperando que regreses.

Golodir y sus hombres terminaron enfrentándose a fuerzas que superaban todo lo que habían imaginado.

La expedición quedó atrapada.

Y durante mucho tiempo...

nadie sabía con certeza qué había ocurrido.

Hasta que tu propio camino terminó llevándote hacia Angmar.

Y entonces descubriste que algunas historias no desaparecen.

Solo esperan a que alguien tenga el valor de buscarlas.

Mientras avanzabas por aquellas tierras, comprendiste que los hombres de Golodir no eran simplemente soldados perdidos.

Eran personas que habían dejado atrás sus hogares creyendo que regresarían.

Quizá algunos pensaban en sus familias.

Quizá otros soñaban con volver a ver el sol sobre Eriador.

Pero Angmar tenía otros planes.

Y esa es una de las cosas que debes recordar cuando atravieses sus ruinas.

No estás caminando por una tierra vacía.

Estás caminando sobre los restos de personas que vinieron antes.

Personas que tuvieron miedo.

Personas que lucharon.

Personas que esperaron.

Y algunas que nunca volvieron.

Así que cuando escuches el nombre de Golodir...

recuerda que detrás de ese nombre existió una expedición.

Un grupo de hombres que se atrevió a caminar hacia la oscuridad.

Y que necesitó que alguien llegara después...

para descubrir qué había ocurrido.

Ese alguien...

terminaste siendo tú.""",
        {"stability": 0.5, "similarity_boost": 0.8, "style": 0.45, "use_speaker_boost": True},
    ),
    (
        "moria_y_el_precio_de_recuperar_un_hogar",
        """Hola, viajero...

Hay una diferencia entre conquistar una tierra...

y recuperar un hogar.

Los enanos de la Tierra Media conocen muy bien esa diferencia.

Para ellos, Moria no es simplemente una serie de túneles.

Es Khazad-dûm.

Un reino perdido.

Un hogar que alguna vez fue uno de los mayores orgullos de su pueblo.

Durante generaciones, los enanos vivieron bajo las montañas.

Sus salones estaban llenos de voces.

Las forjas permanecían encendidas.

Los martillos golpeaban el metal.

Las familias vivían allí.

Los reyes gobernaban.

Y las grandes riquezas parecían no tener fin.

Hasta que la codicia llevó a los enanos demasiado profundo.

Encontraron mithril.

Y quisieron más.

Excavaron.

Profundizaron.

Hasta despertar algo que había permanecido oculto durante miles de años.

La criatura que sería conocida como la Perdición de Durin.

Entonces todo cambió.

Los enanos huyeron.

Khazad-dûm quedó en silencio.

Las puertas se cerraron.

Y durante años...

nadie quiso volver.

Pero los enanos no olvidan fácilmente sus hogares.

Generaciones después, comenzaron los intentos de recuperar Moria.

Y ahí está la parte que quiero que recuerdes, viajero.

Recuperar un hogar perdido significa enfrentarse a todo aquello que lo reemplazó.

Orcos.

Bestias.

Criaturas de la oscuridad.

Y recuerdos.

Porque cada salón recuperado también recuerda a alguien que ya no está.

Cada columna.

Cada puerta.

Cada antigua forja...

perteneció alguna vez a alguien.

Por eso Moria tiene una tristeza diferente.

Puedes ganar una batalla allí...

y aun así sentir que has perdido algo.

Puedes abrir una antigua puerta...

y descubrir que detrás no hay una celebración.

Solo silencio.

Pero los enanos continúan.

Porque para ellos recuperar Moria no significa solamente conquistar piedra.

Significa recuperar una parte de sí mismos.

Y quizá esa sea la verdadera fuerza de los enanos.

No olvidan.

Recuerdan a sus muertos.

Recuerdan sus reyes.

Recuerdan sus derrotas.

Y cuando llega el momento...

vuelven.

Así que cuando estés bajo aquellas montañas...

no pienses solamente en los enemigos que tienes delante.

Piensa en quienes soñaron con regresar mucho antes que tú.

Porque quizá tú no estés simplemente explorando Moria.

Quizá estés ayudando a un pueblo entero...

a volver a casa.""",
        {"stability": 0.4, "similarity_boost": 0.8, "style": 0.5, "use_speaker_boost": True},
    ),
    (
        "el_camino_de_la_compania_gris",
        """Viajero...

Presta atención.

Porque esta historia comienza cuando un grupo de hombres decide abandonar su hogar...

sin saber si volverá a verlo.

Los Rangers del Norte habían protegido Eriador durante generaciones.

Caminaban por tierras salvajes.

Vigilaban los caminos.

Combatían enemigos que pocos conocían.

Y muchas veces...

nadie sabía siquiera que estaban allí.

Pero llegó un momento en que el destino de la Tierra Media comenzó a cambiar.

Aragorn necesitaba ayuda.

La guerra se acercaba.

Y los Rangers recibieron la llamada.

Debían viajar al sur.

Muy lejos de sus tierras.

Muy lejos de los caminos que conocían.

Muy lejos de todo aquello que habían protegido durante años.

Así comenzó el viaje de la Compañía Gris.

No era un ejército.

No tenían miles de soldados.

No llevaban consigo grandes máquinas de guerra.

Eran hombres.

Guerreros.

Amigos.

Compañeros.

Cada uno con su propia historia.

Y cada uno sabía que aquel viaje podía ser el último.

Pero antes de partir...

había cosas que debían hacerse.

Preparativos.

Mensajes.

Reuniones.

Personas que debían ser encontradas.

Y ahí es donde tú entras en la historia.

Porque mientras los grandes héroes se preparan para su destino...

alguien debe ayudar a preparar el camino.

Y muchas veces...

ese alguien eres tú.

Quizá encuentres a uno de ellos en un camino.

Quizá tengas que llevar un mensaje.

Quizá debas ayudar a reunir a quienes se han separado.

Puede parecer una pequeña tarea.

Pero las grandes historias están construidas con pequeñas acciones.

Sin mensajeros...

los ejércitos no se reúnen.

Sin exploradores...

los caminos permanecen desconocidos.

Sin aquellos que preparan el camino...

los héroes no pueden llegar a su destino.

Por eso la Compañía Gris representa algo importante.

No todos los héroes aparecen en el momento de la gran batalla.

Algunos trabajan antes.

En silencio.

Sin reconocimiento.

Y cuando finalmente llega el momento...

simplemente parten.

Hacia el sur.

Hacia la guerra.

Hacia un destino incierto.

Así que cuando los veas marchar...

recuerda que estás contemplando algo más que un grupo de guerreros.

Estás viendo hombres que dejaron su hogar...

porque alguien necesitaba su ayuda.

Y esa...

también es una forma de heroísmo.""",
        {"stability": 0.35, "similarity_boost": 0.8, "style": 0.65, "use_speaker_boost": True},
    ),
    (
        "cuando_los_ents_marcharon_sobre_isengard",
        """Viajero...

Quiero que imagines algo.

Un bosque entero...

levantándose.

Durante miles de años, los Ents observaron cómo cambiaba el mundo.

Vieron pasar generaciones.

Vieron crecer reinos.

Vieron caer ciudades.

Y aprendieron algo que los hombres rara vez comprenden.

La paciencia.

Pero incluso la paciencia tiene un límite.

Saruman comenzó a talar los árboles.

Sus ejércitos necesitaban madera.

Sus máquinas necesitaban combustible.

Y poco a poco...

el bosque comenzó a desaparecer.

Para los hombres quizá eran árboles.

Para los Ents...

eran amigos.

Seres vivos.

Parte de un mundo que llevaban miles de años protegiendo.

Y entonces algo cambió.

Los Ents comenzaron a hablar.

A reunirse.

A decidir.

Y finalmente...

marcharon.

Imagínalo.

Después de miles de años de permanecer en los bosques...

criaturas enormes comienzan a caminar hacia Isengard.

No corren.

No necesitan hacerlo.

Caminan.

Paso a paso.

Como una tormenta que todavía está lejos...

pero sabes que llegará.

Saruman había construido una fortaleza pensando que podía resistir a ejércitos.

Muros.

Torres.

Máquinas.

Pero había olvidado algo.

No todo enemigo necesita atacar de la misma manera.

Los Ents no llegaron con catapultas.

Llegaron con raíces.

Con ramas.

Con fuerza.

Con la ira de un bosque entero.

Y entonces Isengard comenzó a caer.

Las máquinas fueron destruidas.

Las defensas quebradas.

Los muros atacados.

Y aquello que parecía imposible...

ocurrió.

El bosque había respondido.

Quizá por eso esta historia sea tan especial.

Porque recuerda que la naturaleza también tiene memoria.

Puedes destruir un árbol.

Después otro.

Después otro.

Y pensar que nadie responderá.

Pero llega un momento...

en que la paciencia termina.

Así que cuando atravieses un bosque, viajero...

camina con respeto.

No sabes cuántos ojos pueden estar observándote.

Quizá estés completamente solo.

O quizá...

el bosque simplemente esté esperando.""",
        {"stability": 0.3, "similarity_boost": 0.8, "style": 0.72, "use_speaker_boost": True},
    ),
    (
        "tu_camino_todavia_no_ha_terminado",
        """Viajero...

Mira cuánto has recorrido.

Cuando comenzaste...

no sabías qué te esperaba.

Quizá solo querías completar una misión.

Quizá buscabas riquezas.

Quizá simplemente querías descubrir qué había al otro lado de la siguiente colina.

Pero entonces apareció Angmar.

Después Moria.

Después Mirkwood.

Rohan.

Gondor.

Mordor.

Y cada tierra cambió un poco tu historia.

Has visto reinos caer.

Has visto pueblos resistir.

Has conocido personas que recordarás durante mucho tiempo...

y otras que quizá nunca vuelvas a encontrar.

Has ganado batallas.

También has perdido algunas.

Pero sigues aquí.

Y eso importa.

Porque la Tierra Media no recuerda solamente a quienes ganaron.

Recuerda a quienes continuaron.

A aquellos que cayeron...

y se levantaron.

A aquellos que tuvieron miedo...

y avanzaron igualmente.

Quizá hoy tu camino parezca pequeño.

Una misión.

Un viaje.

Una batalla.

Pero nunca sabes qué puede comenzar con un solo paso.

Un viajero puede convertirse en un héroe.

Una pequeña ayuda puede salvar una vida.

Una decisión puede cambiar el destino de un pueblo.

Y una persona puede terminar formando parte de una historia que comenzó mucho antes de que naciera.

Eso es lo hermoso de tu viaje.

No necesitas saber cómo terminará.

Solo necesitas continuar.

Así que cuando mañana vuelvas a entrar en este mundo...

recuerda todo lo que ya has recorrido.

Recuerda las montañas.

Los bosques.

Las ciudades.

Las ruinas.

Los amigos.

Los enemigos.

Y recuerda al viajero que comenzó este camino.

Porque ya no eres aquella persona.

Has cambiado.

Has aprendido.

Has sobrevivido.

Y todavía tienes caminos por recorrer.

Así que levanta tu arma.

Ensilla tu caballo.

Mira hacia el horizonte.

Hay una nueva historia esperando.

Quizá sea una gran batalla.

Quizá una pequeña misión.

Quizá simplemente un camino que nunca habías recorrido.

No importa.

Mientras sigas avanzando...

la Tierra Media todavía tiene algo que contarte.

Y mientras exista un camino delante de ti...

tu historia todavía no ha terminado.""",
        {"stability": 0.32, "similarity_boost": 0.8, "style": 0.68, "use_speaker_boost": True},
    ),
]


def _split_into_segments(text: str) -> list[tuple[str, float]]:
    if "[PAUSA" in text:
        parts = re.split(r"\[PAUSA LARGA\]|\[PAUSA\]", text)
        markers = re.findall(r"\[PAUSA LARGA\]|\[PAUSA\]", text)
        segments = []
        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue
            pause = 0.0
            if i < len(markers):
                pause = PAUSA_LARGA if "LARGA" in markers[i] else PAUSA
            segments.append((part, pause))
        return segments

    sentences = [s.strip() for s in re.split(r"(?<=[.!?…])\s+", text) if s.strip()]
    return [(s, PAUSA) for s in sentences[:-1]] + ([(sentences[-1], 0.0)] if sentences else [])


LEAD_IN_S = 0.4
TAIL_S = 0.8
FADE_MS = 12
TARGET_PEAK = 0.9


def _fade_edges(samples: np.ndarray, sr: int, fade_ms: float = FADE_MS) -> np.ndarray:
    n = min(int(sr * fade_ms / 1000), len(samples) // 4)
    if n <= 0:
        return samples
    out = samples.copy()
    out[:n] *= np.linspace(0.0, 1.0, n)
    out[-n:] *= np.linspace(1.0, 0.0, n)
    return out


def _peak_normalize(samples: np.ndarray, target: float = TARGET_PEAK) -> np.ndarray:
    peak = np.abs(samples).max()
    if peak < 1e-6:
        return samples
    return samples * (target / peak)


def build_clip(name: str, text: str, voice_cfg: dict, synthesize) -> None:
    segments = _split_into_segments(text)
    frag_dir = TMP_DIR / name
    frag_dir.mkdir(parents=True, exist_ok=True)

    pieces: list[np.ndarray] = []
    sr_ref: int | None = None

    print(f"[{name}] Generando {len(segments)} fragmentos...")
    for i, (seg_text, pause_after) in enumerate(segments):
        frag_path = frag_dir / f"frag_{i:02d}.mp3"
        print(f"  [{i + 1}/{len(segments)}] {seg_text[:60]}...")
        synthesize(seg_text, voice_cfg, frag_path, APP_DIR)

        data, sr = sf.read(frag_path)
        mono = data.mean(axis=1) if data.ndim > 1 else data
        if sr_ref is None:
            sr_ref = sr
        elif sr != sr_ref:
            raise SystemExit(f"Fragmento {i} de {name} vino a {sr}Hz, esperado {sr_ref}Hz.")

        mono = _peak_normalize(_fade_edges(mono.astype(np.float32), sr_ref))
        pieces.append(mono)
        if pause_after > 0:
            pieces.append(np.zeros(int(sr_ref * pause_after), dtype=np.float32))

    assert sr_ref is not None
    full = np.concatenate(
        [np.zeros(int(sr_ref * LEAD_IN_S), dtype=np.float32)]
        + pieces
        + [np.zeros(int(sr_ref * TAIL_S), dtype=np.float32)]
    )
    full = apply_narrator_fx(full, sr_ref)
    full = _peak_normalize(full)
    full = _fade_edges(full, sr_ref, fade_ms=150)

    out_path = OUT_DIR / f"{name}.mp3"
    sf.write(out_path, full, sr_ref, format="MP3")

    for frag in frag_dir.glob("frag_*.mp3"):
        frag.unlink(missing_ok=True)
    frag_dir.rmdir()

    duration = len(full) / sr_ref
    print(f"[{name}] Listo: {out_path} ({duration:.1f}s, {sr_ref}Hz)")


def main() -> None:
    config = load_config(APP_DIR / "config.yaml")
    base_voice_cfg = config["voices"].get(VOICE_NAME)
    if not base_voice_cfg:
        raise SystemExit(f"config.yaml no tiene una voz '{VOICE_NAME}'.")
    engine = base_voice_cfg.get("engine", "edge")
    synthesize = ENGINE_FUNCS[engine]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    for name, text, settings_override in CLIPS:
        out_path = OUT_DIR / f"{name}.mp3"
        if out_path.exists():
            continue
        voice_cfg = dict(base_voice_cfg)
        if settings_override:
            voice_cfg["voice_settings"] = settings_override
        try:
            build_clip(name, text, voice_cfg, synthesize)
        except Exception as exc:
            # Cuota de esta cuenta (10.000 caracteres, gratis) puede
            # agotarse a mitad del lote -- avisar con claridad y dejar
            # limpio en vez de crashear con fragmentos a medias.
            frag_dir = TMP_DIR / name
            if frag_dir.exists():
                for frag in frag_dir.glob("*.mp3"):
                    frag.unlink(missing_ok=True)
                frag_dir.rmdir()
            print(f"[Golodir] DETENIDO en '{name}': {exc}")
            return

    if TMP_DIR.exists() and not any(TMP_DIR.iterdir()):
        TMP_DIR.rmdir()


if __name__ == "__main__":
    main()
