"""Genera los efectos de sonido cortos del addon (fanfarrias de mision,
pergamino, click de UI) por SINTESIS -- pedido explicito del usuario
(2026-09-02): "generar tonos sinteticos por ahora" en vez de audio real
extraido del cliente o de una libreria externa (no hay forma de conseguir
eso desde esta sesion). Reemplazables mas adelante sin tocar codigo: alcanza
con pisar estos mismos nombres de archivo en voices/sfx/ por audio real.

Uso: .venv/Scripts/python.exe tools/gen_sfx.py
Escribe en voices/sfx/*.wav (44100Hz, 16-bit PCM mono).
"""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

SR = 44100
OUT_DIR = Path(__file__).resolve().parent.parent / "voices" / "sfx"

# BUG DE MEZCLA CORREGIDO (pedido explicito del usuario, 2026-09-02: "que
# sea un volumen promedio que se usa en todos los otros [sonidos]") -- antes
# cada generador multiplicaba por un numero elegido a mano (0.5, 0.35, 0.85,
# etc.) sin relacion entre si, asi que el volumen PERCIBIDO saltaba de un
# sonido a otro sin ningun criterio (un click podia sonar mas fuerte que el
# swoosh del pergamino solo por casualidad de a que numero se multiplico).
# Dos niveles con normalizacion real (por pico, no por "a ojo"):
#   UI_SFX_PEAK -- click, cambio de pagina, abrir/cerrar ventana, pergamino,
#     ding de progreso: sonidos FRECUENTES (varios por minuto), tienen que
#     ser todos parejos entre si y discretos.
#   EPIC_SFX_PEAK -- aceptar/completar mision: son RAROS (una vez por
#     mision) y el pedido explicito fue que suenen "epicos" -- se quedan en
#     un nivel mas alto a proposito, no es un descuido de mezcla.
UI_SFX_PEAK = 0.42
EPIC_SFX_PEAK = 0.88


def _normalize_peak(samples: np.ndarray, target_peak: float) -> np.ndarray:
    """Escala samples para que su pico (no su "volumen a ojo") llegue
    exactamente a target_peak -- asi dos sonidos con tecnicas de sintesis
    distintas (ruido filtrado vs. suma de senos) terminan con el MISMO
    volumen percibido en vez de uno al azar segun cuantas capas se sumaron.

    Sirve bien para audio SINTETIZADO por este mismo script (formas de onda
    limpias, sin ruido de fondo real). Para audio REAL grabado (ver
    _level_real_recording mas abajo) normalizar por PICO es la fuente de un
    bug real encontrado en esta sesion: un click grabado (ej. una lapicera)
    tiene un pico muy filoso rodeado de silencio casi total -- normalizar
    por ese pico solo escala TODO el clip segun un solo instante, empujando
    el transiente casi al maximo mientras el resto queda igual de bajito, y
    a ese volumen el transiente se escucha "saturado"/aspero aunque nunca
    hubo clipping digital real (confirmado leyendo la forma de onda: no hay
    muestras planas en el pico de la fuente)."""
    peak = np.max(np.abs(samples))
    if peak < 1e-9:
        return samples
    return samples * (target_peak / peak)


def _highpass(samples: np.ndarray, sr: int, cutoff_hz: float = 80.0) -> np.ndarray:
    """Pasa-altos simple via FFT -- saca ruido grave/zumbido de grabacion
    real (nunca hace falta en audio sintetizado, que no tiene ese piso de
    ruido) sin necesitar una libreria de audio aparte."""
    n = len(samples)
    spectrum = np.fft.rfft(samples)
    freqs = np.fft.rfftfreq(n, 1 / sr)
    spectrum[freqs < cutoff_hz] = 0
    return np.fft.irfft(spectrum, n)


def _soft_limit(samples: np.ndarray, ceiling: float) -> np.ndarray:
    """Limitador suave (tanh): a diferencia de un corte duro (np.clip, que
    aplana la punta de la onda y SI sueca a distorsion real), tanh redondea
    los picos que se pasan de "ceiling" de forma continua -- se nota mucho
    menos incluso cuando el pico original era bastante mas alto."""
    return np.tanh(samples / ceiling) * ceiling


def _level_real_recording(samples: np.ndarray, sr: int, target_rms: float, peak_ceiling: float) -> np.ndarray:
    """Cadena completa para procesar un CLIP REAL grabado (no sintetizado):
    pasa-altos (saca zumbido/ruido grave) -> nivelado por RMS (volumen
    PERCIBIDO promedio, no el pico de un solo instante -- esto es lo que
    evita el problema de arriba) -> limitador suave (por si el nivelado por
    RMS empuja el pico mas alla de un techo seguro)."""
    samples = _highpass(samples, sr, 80.0)
    rms = np.sqrt(np.mean(samples**2))
    if rms > 1e-9:
        samples = samples * (target_rms / rms)
    return _soft_limit(samples, peak_ceiling)


def _write_wav(path: Path, samples: np.ndarray) -> None:
    # Clip antes de convertir -- una suma de armonicos/ecos puede pasarse de
    # +-1.0, y sin este clip el int16 da vuelta (wrap-around) en vez de
    # saturar, lo que suena como un "crack" digital feo.
    samples = np.clip(samples, -1.0, 1.0)
    pcm = (samples * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(pcm.tobytes())


def _envelope(n: int, attack: int, decay_rate: float) -> np.ndarray:
    """Ataque lineal rapido + caida exponencial -- forma basica de
    "campana"/"pulso" en vez de un tono plano que empieza y corta seco."""
    t = np.arange(n)
    env = np.ones(n)
    if attack > 0:
        env[:attack] = np.linspace(0, 1, attack)
    env *= np.exp(-decay_rate * t / SR)
    return env


def _note(freq: float, duration: float, amp: float = 1.0, decay_rate: float = 3.5) -> np.ndarray:
    """Un tono tipo "campana": fundamental + 2 armonicos mas debiles (sin
    armonicos un seno puro suena a pitido de microondas, no a instrumento) --
    cada uno con su propia caida, el armonico agudo se apaga primero (igual
    que una campana real)."""
    n = int(SR * duration)
    t = np.arange(n) / SR
    attack = max(1, int(SR * 0.004))
    wave1 = np.sin(2 * np.pi * freq * t) * _envelope(n, attack, decay_rate)
    wave2 = 0.35 * np.sin(2 * np.pi * freq * 2 * t) * _envelope(n, attack, decay_rate * 1.8)
    wave3 = 0.15 * np.sin(2 * np.pi * freq * 3 * t) * _envelope(n, attack, decay_rate * 2.6)
    return amp * (wave1 + wave2 + wave3)


def _reverb_tail(samples: np.ndarray, taps: int = 5, delay_s: float = 0.09, decay: float = 0.45) -> np.ndarray:
    """Eco simple (varias copias retrasadas y cada vez mas debiles) --
    aproxima una cola de reverberacion de sala sin necesitar una libreria de
    audio real, para que la fanfarria de mision no corte seco."""
    delay = int(SR * delay_s)
    out = np.zeros(len(samples) + delay * taps)
    out[: len(samples)] += samples
    level = decay
    for i in range(1, taps + 1):
        start = delay * i
        out[start : start + len(samples)] += samples * level
        level *= decay
    return out


def _sub_thump(duration: float, start_freq: float, end_freq: float, amp: float = 1.0, decay_rate: float = 8.0) -> np.ndarray:
    """"Boom" grave de trailer -- un seno que BAJA de frecuencia muy rapido
    (150Hz a 45Hz tipico) con caida exponencial. Es la pieza que le da peso
    "de impacto" a un golpe -- sin esto, un acorde solo suena a instrumento
    de juguete, nunca a "golpe orquestal"."""
    n = int(SR * duration)
    t = np.arange(n) / SR
    freq = np.linspace(start_freq, end_freq, n)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    env = _envelope(n, attack=int(SR * 0.004), decay_rate=decay_rate)
    return amp * np.sin(phase) * env


def _noise_hit(duration: float, amp: float = 1.0, low_hz: float = 1500, high_hz: float = 9000) -> np.ndarray:
    """El "crack" percusivo del golpe (como un platillo/orchestral hit
    corto) -- ruido filtrado en agudos con ataque instantaneo y caida muy
    rapida. Se suma AL MISMO TIEMPO que el sub-thump, no en secuencia."""
    n = int(SR * duration)
    noise = _bandpassed_noise(duration, low_hz, high_hz)
    env = _envelope(n, attack=1, decay_rate=25.0)
    return amp * noise * env


def _power_chord(freqs: list[float], duration: float, amp: float = 1.0, decay_rate: float = 2.0,
                  detune_cents: float = 7.0, layers: int = 4, seed: int = 7) -> np.ndarray:
    """Acorde "grande" tipo metales/coro de trailer: cada nota se toca con
    VARIAS copias ligeramente desafinadas entre si (unison detune, la misma
    tecnica que usan los synths de pelicula para sonar "ancho" en vez de un
    seno solo y fino) en vez de una sola sinusoide limpia por nota."""
    n = int(SR * duration)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    out = np.zeros(n)
    for f in freqs:
        for _ in range(layers):
            detuned = f * (2 ** (rng.uniform(-detune_cents, detune_cents) / 1200))
            out += np.sin(2 * np.pi * detuned * t)
    out /= (len(freqs) * layers)
    env = _envelope(n, attack=int(SR * 0.008), decay_rate=decay_rate)
    return amp * out * env


def _riser(duration: float, start_freq: float, end_freq: float, amp: float = 1.0) -> np.ndarray:
    """"Riser" de tension antes del golpe -- tono + ruido subiendo de
    frecuencia con volumen creciente, cortado justo al llegar el impacto.
    Formula estandar de trailer/sting de juego ("build up" -> "hit"), lo que
    mas le faltaba a la version anterior (empezaba directo en la nota, sin
    ninguna anticipacion)."""
    n = int(SR * duration)
    t = np.arange(n) / SR
    freq = np.linspace(start_freq, end_freq, n)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    tone = np.sin(phase)
    noise = _bandpassed_noise(duration, start_freq, end_freq * 1.2)
    env = np.linspace(0, 1, n) ** 1.6
    return amp * env * (0.45 * tone + 0.7 * noise)


def _shimmer(base_freq: float, duration: float, amp: float = 0.25, decay_rate: float = 1.4) -> np.ndarray:
    """Brillo agudo tipo platillo/coro sostenido detras del acorde --
    parciales INarmonicos (no multiplos enteros de la fundamental, a
    proposito: los multiplos enteros suenan a organo, los inarmonicos suenan
    a metal/campana grande) con caida lenta para la cola larga."""
    n = int(SR * duration)
    t = np.arange(n) / SR
    ratios = [2.0, 3.4, 5.2, 6.7]
    out = np.zeros(n)
    for i, r in enumerate(ratios):
        out += (1.0 / (i + 1)) * np.sin(2 * np.pi * base_freq * r * t)
    env = _envelope(n, attack=int(SR * 0.02), decay_rate=decay_rate)
    return amp * out * env


def _bandpassed_noise(duration: float, low_hz: float, high_hz: float) -> np.ndarray:
    """Ruido blanco filtrado en banda via FFT (recorta todo lo que no este
    entre low_hz/high_hz) -- sin esto, ruido blanco puro suena a "estatica de
    radio", no a papel/tela. Con el filtro se acerca mas a un "swoosh"."""
    n = int(SR * duration)
    noise = np.random.default_rng(42).normal(0, 1, n)
    spectrum = np.fft.rfft(noise)
    freqs = np.fft.rfftfreq(n, 1 / SR)
    mask = (freqs >= low_hz) & (freqs <= high_hz)
    spectrum[~mask] = 0
    filtered = np.fft.irfft(spectrum, n)
    return filtered / (np.max(np.abs(filtered)) + 1e-9)


def gen_quest_accepted() -> np.ndarray:
    # BUG DE DISEÑO CORREGIDO (pedido explicito del usuario tras escuchar la
    # v1: "que sean sonidos epicos y no sonidos de un instrumento y ya...
    # como de otros juegos parecidos") -- un arpegio de seno+armonicos suena
    # a caja de musica, no a sting de videojuego. La formula real de un
    # "sting" epico de juego/trailer es RISER (tension subiendo) + IMPACTO
    # (sub-bajo + crack percusivo + acorde ancho desafinado + brillo), todo
    # el impacto sonando A LA VEZ, no en secuencia como notas de melodia.
    riser = _riser(0.32, 300, 1600, amp=0.55)
    hit_at = len(riser) - int(SR * 0.02)  # el golpe entra un poco ANTES de que el riser termine de bajar, se siente mas conectado que un corte seco

    thump = _sub_thump(0.4, 140, 45, amp=0.9)
    crack = _noise_hit(0.1, amp=0.55)
    chord = _power_chord([261.63, 392.00, 523.25], 1.0, amp=0.55, decay_rate=1.9)  # Do-Sol-Do (quinta abierta), sonido "heroico" clasico de fanfarria de juego
    shimmer = _shimmer(523.25, 0.9, amp=0.18, decay_rate=1.3)

    total = hit_at + max(len(thump), len(crack), len(chord), len(shimmer))
    out = np.zeros(total)
    out[: len(riser)] += riser
    out[hit_at : hit_at + len(thump)] += thump
    out[hit_at : hit_at + len(crack)] += crack
    out[hit_at : hit_at + len(chord)] += chord
    out[hit_at : hit_at + len(shimmer)] += shimmer
    return _normalize_peak(_reverb_tail(out, taps=4, delay_s=0.1, decay=0.32), EPIC_SFX_PEAK)


def gen_quest_completed() -> np.ndarray:
    # Version mas GRANDE/resuelta de accepted: riser mas largo, golpe mas
    # profundo, acorde mayor completo de 4 notas (no solo quinta abierta) y
    # mas capas de shimmer -- la "victoria" tiene que sentirse mas grande
    # que el "algo nuevo empieza" de accepted, no solo distinta.
    riser = _riser(0.45, 250, 2000, amp=0.6)
    hit_at = len(riser) - int(SR * 0.02)

    thump = _sub_thump(0.5, 160, 38, amp=1.0, decay_rate=6.0)
    crack = _noise_hit(0.14, amp=0.65, low_hz=1200, high_hz=10000)
    chord = _power_chord([261.63, 329.63, 392.00, 523.25], 1.3, amp=0.6, decay_rate=1.4)  # Do mayor completo (Do-Mi-Sol-Do), resuelto, no solo quinta abierta
    shimmer1 = _shimmer(523.25, 1.2, amp=0.22, decay_rate=1.0)
    shimmer2 = _shimmer(659.25, 1.1, amp=0.16, decay_rate=1.1)

    total = hit_at + max(len(thump), len(crack), len(chord), len(shimmer1), len(shimmer2))
    out = np.zeros(total)
    out[: len(riser)] += riser
    out[hit_at : hit_at + len(thump)] += thump
    out[hit_at : hit_at + len(crack)] += crack
    out[hit_at : hit_at + len(chord)] += chord
    out[hit_at : hit_at + len(shimmer1)] += shimmer1
    out[hit_at : hit_at + len(shimmer2)] += shimmer2
    return _normalize_peak(_reverb_tail(out, taps=6, delay_s=0.12, decay=0.42), EPIC_SFX_PEAK)


def gen_quest_progress() -> np.ndarray:
    # Un solo "ding" corto y suave -- se dispara seguido (cada avance real
    # de objetivo), tiene que ser discreto, no competir con la narracion.
    return _normalize_peak(_note(880.0, 0.35, 1.0, decay_rate=6.0), UI_SFX_PEAK)


def gen_parchment_open() -> np.ndarray:
    # "Swoosh" de papel: ruido filtrado con un sobre que SUBE rapido y baja
    # -- sensacion de algo desenrollandose. Sin componente tonal (no es
    # musical, es textura).
    dur = 0.55
    n = int(SR * dur)
    noise = _bandpassed_noise(dur, 800, 4500)
    t = np.linspace(0, 1, n)
    env = np.sin(np.pi * t) ** 0.6  # sube y baja suave, pico cerca del medio
    return _normalize_peak(noise * env, UI_SFX_PEAK)


def gen_parchment_close() -> np.ndarray:
    # Misma textura que abrir pero mas corta, MAS UN golpe grave al final
    # (el "thud" del libro cerrandose) -- swoosh + thump, no solo swoosh.
    dur = 0.35
    n = int(SR * dur)
    noise = _bandpassed_noise(dur, 700, 3500)
    t = np.linspace(0, 1, n)
    env = np.sin(np.pi * t) ** 0.8
    swoosh = 0.45 * noise * env
    thump = _note(90.0, 0.3, 0.6, decay_rate=9.0)
    out = np.zeros(max(len(swoosh), len(thump)))
    out[: len(swoosh)] += swoosh
    out[: len(thump)] += thump
    return _normalize_peak(out, UI_SFX_PEAK)


def gen_ui_click() -> np.ndarray:
    # Tick muy corto (30ms): un pulso agudo con caida casi instantanea --
    # se dispara en cada click de fila, tiene que ser practicamente
    # imperceptible salvo como confirmacion tactil.
    dur = 0.03
    n = int(SR * dur)
    t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * 2200 * t) * _envelope(n, attack=2, decay_rate=60)
    return _normalize_peak(tone, UI_SFX_PEAK)


def gen_page_turn() -> np.ndarray:
    # Pedido explicito del usuario (2026-09-02: "sonido de cambio de hoja,
    # al cambiar de pestaña") -- 2 "riffles" de papel cortos y superpuestos
    # (como una hoja que se desliza y cae contra la otra), mas agudo/corto
    # que parchment_open/close (esos son "desenrollar un pergamino grande",
    # esto es "pasar una sola hoja").
    dur1, dur2 = 0.12, 0.10
    n1, n2 = int(SR * dur1), int(SR * dur2)
    noise1 = _bandpassed_noise(dur1, 1500, 6000)
    noise2 = _bandpassed_noise(dur2, 2000, 7000)
    env1 = _envelope(n1, attack=int(SR * 0.01), decay_rate=14.0)
    env2 = _envelope(n2, attack=1, decay_rate=20.0)
    offset = int(SR * 0.06)  # el segundo "riffle" pisa el final del primero, no viene despues
    out = np.zeros(offset + n2)
    out[:n1] += noise1 * env1
    out[offset : offset + n2] += noise2 * env2 * 0.8
    return _normalize_peak(out, UI_SFX_PEAK)


def gen_window_open() -> np.ndarray:
    # Ventanas nativas del addon (Tracker/QuestSync/Recoleccion/Puntos de
    # Interes -- pedido explicito del usuario: "sonido al abrir una
    # ventana"). Distinto de parchment_open (ese es especifico del libro de
    # mision): un swoosh MUY corto con un toque tonal ascendente suave, mas
    # "UI" que "textura de papel".
    dur = 0.22
    n = int(SR * dur)
    noise = _bandpassed_noise(dur, 500, 3000)
    t = np.arange(n) / SR
    freq = np.linspace(300, 700, n)
    tone = np.sin(2 * np.pi * np.cumsum(freq) / SR)
    env = _envelope(n, attack=int(SR * 0.02), decay_rate=9.0)
    return _normalize_peak((0.6 * noise + 0.5 * tone) * env, UI_SFX_PEAK)


def gen_window_close() -> np.ndarray:
    # Espejo descendente de window_open -- mismo criterio, tono BAJANDO en
    # vez de subiendo (asociacion auditiva estandar: sube=abre, baja=cierra).
    dur = 0.18
    n = int(SR * dur)
    noise = _bandpassed_noise(dur, 400, 2500)
    freq = np.linspace(650, 250, n)
    tone = np.sin(2 * np.pi * np.cumsum(freq) / SR)
    env = _envelope(n, attack=int(SR * 0.005), decay_rate=11.0)
    return _normalize_peak((0.6 * noise + 0.5 * tone) * env, UI_SFX_PEAK)


GENERATORS = {
    "quest_accepted": gen_quest_accepted,
    "quest_completed": gen_quest_completed,
    "quest_progress": gen_quest_progress,
    "parchment_open": gen_parchment_open,
    "parchment_close": gen_parchment_close,
    "ui_click": gen_ui_click,
    "page_turn": gen_page_turn,
    "window_open": gen_window_open,
    "window_close": gen_window_close,
}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, gen in GENERATORS.items():
        samples = gen()
        out_path = OUT_DIR / f"{name}.wav"
        _write_wav(out_path, samples)
        print(f"[gen_sfx] {out_path} ({len(samples) / SR:.2f}s)")


if __name__ == "__main__":
    main()
