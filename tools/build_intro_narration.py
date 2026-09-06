"""Pre-genera UNA VEZ la narracion de introduccion ("Bienvenido, viajero...")
y la deja guardada como archivo fijo en voices/intro/intro_bienvenida.wav.

Por que pre-generar en vez de sintetizar en vivo cada vez (pedido explicito
del usuario, 2026-09-05: "que quede guardada en nuestro addons"): el texto de
la intro NUNCA cambia, asi que no tiene sentido pagar el costo de sintesis ni
el riesgo de que falle el motor cada vez que el jugador abre LOTRO. Se genera
una sola vez aca, offline, y narrator.py solo la REPRODUCE (ver
Narrator.play_intro en src/narrator.py).

Motor: edge-tts con la voz "narrador_intro" (ver config.yaml), NO xtts/clon.
Primer intento fue con gandalf_clone (XTTS): el usuario lo escucho y lo
rechazo ("esta demasiado malo, tiene mucho ruido... prefiero que NO sea una
voz clonada") -- clonar desde un clip corto (~10s) arrastra ruido/artefactos
de fondo en cada fragmento nuevo, notorio en una pieza continua de 2-3
minutos. edge-tts (mismo motor confiable que usa el resto del addon, sin
clonacion, sin ruido) con pitch/rate bajados para sonar mas grave y pausado
da el mismo "sabor" de narrador anciano sin ese problema.

El guion trae marcas [PAUSA]/[PAUSA LARGA] (ver el pedido original del
usuario) que el motor no entiende como SSML -- se resuelven generando cada
fragmento por separado y empalmandolos con silencio real de por medio, en
vez de mandar el texto completo con las marcas literales al motor.

Uso: .venv/Scripts/python.exe tools/build_intro_narration.py
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
OUT_PATH = APP_DIR / "voices" / "intro" / "intro_bienvenida.mp3"
TMP_DIR = APP_DIR / "voices" / "intro" / "_fragments"

PAUSA = 0.55
PAUSA_LARGA = 1.2
GAP_CORTO = 0.35  # entre frases del mismo parrafo, sin marca explicita

# (texto, pausa en segundos DESPUES de este fragmento)
SEGMENTS: list[tuple[str, float]] = [
    ("En una tierra donde los caminos se pierden entre montañas...", PAUSA),
    ("Donde los antiguos bosques guardan secretos...", PAUSA),
    ("Y donde la sombra aún se extiende sobre la Tierra Media...", PAUSA_LARGA),
    ("Hubo un tiempo en que el destino de muchos quedó ligado a las decisiones de unos pocos.", PAUSA),
    ("Hombres... Elfos... Enanos... Hobbits...", PAUSA),
    ("Pueblos distintos, unidos por una misma tierra... y por una historia que aún está siendo escrita.", PAUSA_LARGA),
    ("Ahora... esa historia también puede ser la tuya.", PAUSA),
    ("Bienvenido, viajero.", PAUSA),
    ("Ante ti se extiende un mundo vasto y antiguo.", GAP_CORTO),
    (
        "Un mundo de reinos olvidados, ciudades legendarias, criaturas de las sombras, "
        "y héroes cuyos nombres perdurarán mucho después de que sus pasos desaparezcan de los caminos.",
        PAUSA,
    ),
    ("Aquí, cada sendero puede conducir hacia una nueva aventura.", GAP_CORTO),
    ("Cada encuentro puede cambiar el rumbo de tu viaje.", GAP_CORTO),
    ("Y cada decisión...", PAUSA),
    ("Puede convertirse en parte de tu propia leyenda.", PAUSA_LARGA),
    ("Pero ninguna gran historia comienza sin un primer paso.", PAUSA),
    ("Así que prepara tus armas.", GAP_CORTO),
    ("Afirma tu voluntad.", GAP_CORTO),
    ("Y mira hacia el horizonte...", PAUSA_LARGA),
    ("Porque las tierras de la Tierra Media te esperan.", PAUSA),
    ("Tu aventura está a punto de comenzar.", PAUSA_LARGA),
    ("Selecciona tu personaje...", PAUSA),
    ("Y emprendamos juntos este viaje.", PAUSA_LARGA),
    ("Que tu camino sea largo...", PAUSA),
    ("Y que la luz te acompañe.", 0.0),
]

LEAD_IN_S = 0.5
TAIL_S = 1.0
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


def main() -> None:
    config = load_config(APP_DIR / "config.yaml")
    voice_cfg = config["voices"].get(VOICE_NAME)
    if not voice_cfg:
        raise SystemExit(f"config.yaml no tiene una voz '{VOICE_NAME}'.")
    engine = voice_cfg.get("engine", "edge")
    synthesize = ENGINE_FUNCS[engine]

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    pieces: list[np.ndarray] = []
    sr_ref: int | None = None

    print(f"[Intro] Generando {len(SEGMENTS)} fragmentos con '{VOICE_NAME}' (engine={engine})...")
    for i, (text, pause_after) in enumerate(SEGMENTS):
        frag_path = TMP_DIR / f"frag_{i:02d}.mp3"
        print(f"  [{i + 1}/{len(SEGMENTS)}] {text[:60]}...")
        synthesize(text, voice_cfg, frag_path, APP_DIR)

        data, sr = sf.read(frag_path)
        mono = data.mean(axis=1) if data.ndim > 1 else data
        if sr_ref is None:
            sr_ref = sr
        elif sr != sr_ref:
            # Distinto sample rate entre fragmentos (no deberia pasar con el
            # mismo motor, pero si pasara, remuestrear rompe la
            # concatenacion por silencio simple) -- avisar fuerte en vez de
            # generar un wav con velocidad/tono incorrectos.
            raise SystemExit(f"Fragmento {i} vino a {sr}Hz, esperado {sr_ref}Hz.")

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
    full = _fade_edges(full, sr_ref, fade_ms=200)

    # mp3 (pedido explicito del usuario, 2026-09-05): ~89% mas chico que
    # wav sin comprimir, sin perdida audible para narracion hablada.
    sf.write(OUT_PATH, full, sr_ref, format="MP3")

    for frag in TMP_DIR.glob("frag_*.mp3"):
        frag.unlink(missing_ok=True)
    TMP_DIR.rmdir()

    duration = len(full) / sr_ref
    print(f"[Intro] Listo: {OUT_PATH} ({duration:.1f}s, {sr_ref}Hz)")


if __name__ == "__main__":
    main()
