"""Genera 3 narraciones motivacionales adicionales (guiones originales,
ambientados en el mundo de LOTRO, NO son texto de introduccion) con la
misma voz "narrador_intro" (Oxley) pero con voice_settings mas expresivos
(pedido explicito del usuario, 2026-09-05: "mayor expresion y motivacion").

Cada una queda guardada como archivo fijo en voices/motivational/, mismo
criterio que la intro: se generan UNA vez aca, no en vivo.

Uso: .venv/Scripts/python.exe tools/build_motivational_clips.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import soundfile as sf

APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR / "src"))

from audio_fx import apply_narrator_fx  # noqa: E402
from config import load_config  # noqa: E402
from tts import ENGINE_FUNCS  # noqa: E402

VOICE_NAME = "narrador_intro"
# "intro_pool" (2026-09-05, pedido explicito del usuario): ya no hay UNA
# sola narracion de introduccion -- narrator.py elige una al azar de esta
# carpeta cada vez que detecta que se abrio LOTRO (ver Narrator.play_intro),
# para que no suene siempre lo mismo. Duracion objetivo ~1 minuto cada una:
# el usuario midio que la demora real entre abrir LOTRO y aparecer en el
# mundo es de aproximadamente un minuto.
OUT_DIR = APP_DIR / "voices" / "intro_pool"
TMP_DIR = OUT_DIR / "_fragments"

# Mas expresivo que la intro base (style mas alto, stability mas baja) --
# pedido explicito del usuario para estas piezas motivacionales.
VOICE_SETTINGS_OVERRIDE = {
    "stability": 0.28,
    "similarity_boost": 0.8,
    "style": 0.8,
    "use_speaker_boost": True,
}

PAUSA = 0.55
PAUSA_LARGA = 1.2

CLIPS: list[tuple[str, list[tuple[str, float]]]] = [
    (
        "el_llamado_del_camino",
        [
            ("Hay un momento en la vida de todo aquel que camina esta tierra...", PAUSA),
            ("en el que el hogar deja de ser suficiente.", PAUSA),
            ("Un momento en que el corazón escucha un llamado que los oídos no pueden oír...", PAUSA),
            ("el llamado del camino.", PAUSA_LARGA),
            (
                "No importa si naciste entre las colinas verdes de la Comarca, "
                "bajo los salones de piedra de Ered Luin, o a la sombra de las Montañas Nubladas...",
                PAUSA,
            ),
            ("El mundo no espera a los que dudan.", PAUSA),
            ("Espera a los que se atreven.", PAUSA_LARGA),
            ("Así que levanta tu mirada, viajero.", PAUSA),
            ("Ajusta tu capa, empuña tu arma, y da el primer paso...", PAUSA),
            (
                "Porque más allá de esa colina, más allá de ese río, "
                "más allá de ese último rincón conocido...",
                PAUSA,
            ),
            ("te espera una leyenda con tu nombre.", PAUSA_LARGA),
            ("El camino te llama.", PAUSA),
            ("¿Vas a responder?", 0.0),
        ],
    ),
    (
        "la_hermandad_que_no_se_rinde",
        [
            ("Ningún héroe camina solo, aunque a veces lo parezca.", PAUSA),
            ("Detrás de cada gesta, de cada victoria, de cada historia que perdura...", PAUSA),
            ("hay manos que se sostuvieron cuando las piernas temblaban.", PAUSA_LARGA),
            ("Hombres y elfos, enanos y hobbits...", PAUSA),
            (
                "pueblos que la historia intentó separar, y que la amistad volvió a unir.",
                PAUSA,
            ),
            ("Porque incluso en la noche más oscura, cuando la sombra parece devorarlo todo...", PAUSA_LARGA),
            (
                "basta una sola luz para recordarnos que la esperanza nunca muere del todo.",
                PAUSA,
            ),
            ("Así que si sientes que el peso del camino es demasiado...", PAUSA),
            ("mira a tu alrededor.", PAUSA),
            ("No estás solo.", PAUSA_LARGA),
            ("Nunca lo estuviste.", 0.0),
        ],
    ),
    (
        "el_valor_frente_a_la_sombra",
        [
            ("La sombra siempre promete lo mismo: que resistir no tiene sentido.", PAUSA),
            (
                "Que las murallas caerán, que las luces se apagarán, "
                "que al final... todo será olvido.",
                PAUSA_LARGA,
            ),
            ("Pero la sombra miente.", PAUSA),
            ("Porque incluso la oscuridad más antigua ha temblado ante algo tan simple...", PAUSA),
            (
                "como la voluntad de un solo corazón que se niega a rendirse.",
                PAUSA_LARGA,
            ),
            ("No hace falta ser el más fuerte.", PAUSA),
            ("No hace falta ser el más sabio.", PAUSA),
            ("Solo hace falta dar un paso más... cuando todos esperan que retrocedas.", PAUSA_LARGA),
            ("Así que empuña tu valor como empuñarías tu espada...", PAUSA),
            ("y recuerda: incluso la noche más larga...", PAUSA),
            ("termina.", 0.0),
        ],
    ),
    (
        "toda_leyenda_tuvo_un_primer_dia",
        [
            ("Nadie nace siendo leyenda...", PAUSA),
            (
                "Ningún nombre que hoy se recuerda con asombro nació ya grabado en las piedras.",
                PAUSA_LARGA,
            ),
            ("Hubo un primer día...", PAUSA),
            (
                "un primer paso incierto, un primer camino desconocido...",
                PAUSA,
            ),
            ("para cada héroe que después el tiempo no pudo olvidar.", PAUSA_LARGA),
            ("Tal vez hoy no te sientas preparado.", PAUSA),
            ("Tal vez el mundo te parezca demasiado grande, y tú, demasiado pequeño.", PAUSA_LARGA),
            ("Pero así empezó cada leyenda.", PAUSA),
            (
                "Con alguien que decidió avanzar, sin saber aún en qué se convertiría.",
                PAUSA_LARGA,
            ),
            ("Así que respira hondo, viajero.", PAUSA),
            ("Hoy es tu primer día.", PAUSA),
            ("Y el resto de tu historia...", PAUSA),
            ("todavía está por escribirse.", 0.0),
        ],
    ),
]

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


def build_clip(name: str, segments: list[tuple[str, float]], voice_cfg: dict, synthesize) -> None:
    frag_dir = TMP_DIR / name
    frag_dir.mkdir(parents=True, exist_ok=True)

    pieces: list[np.ndarray] = []
    sr_ref: int | None = None

    print(f"[{name}] Generando {len(segments)} fragmentos...")
    for i, (text, pause_after) in enumerate(segments):
        frag_path = frag_dir / f"frag_{i:02d}.mp3"
        print(f"  [{i + 1}/{len(segments)}] {text[:60]}...")
        synthesize(text, voice_cfg, frag_path, APP_DIR)

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

    # mp3 (pedido explicito del usuario, 2026-09-05): ~89% mas chico que
    # wav sin comprimir, sin perdida audible para narracion hablada.
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

    voice_cfg = dict(base_voice_cfg)
    voice_cfg["voice_settings"] = VOICE_SETTINGS_OVERRIDE
    engine = voice_cfg.get("engine", "edge")
    synthesize = ENGINE_FUNCS[engine]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    for name, segments in CLIPS:
        build_clip(name, segments, voice_cfg, synthesize)

    if TMP_DIR.exists() and not any(TMP_DIR.iterdir()):
        TMP_DIR.rmdir()


if __name__ == "__main__":
    main()
