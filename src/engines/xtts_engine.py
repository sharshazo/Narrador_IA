"""Motor Coqui XTTS v2: clonacion de voz local y gratuita (sin API key), a
partir de un clip de referencia corto (10-30s, limpio, un solo hablante,
ver voices/reference/). Es lo que permite que un NPC principal (ej. un
personaje con dialogo doblado real en LOTRO) suene "lo mas parecido"
posible, sin depender de un motor de pago como ElevenLabs/Cartesia.

Dependencia pesada (paquete `TTS` + `torch`, ~2GB de modelo la primera vez)
-- instalacion opcional, ver README "Voces de NPCs principales (clonacion)".
El import de TTS.api se hace adentro de _get_model() a proposito: si ningun
NPC en config.yaml usa engine: xtts, este archivo nunca intenta importar
torch.
"""
from __future__ import annotations

from pathlib import Path

_model = None
_torchaudio_patched = False


def _patch_torchaudio_load() -> None:
    """Bug de entorno (encontrado 2026-09-05, generando la intro narrada):
    la version de torchaudio de este venv delega TODA carga de audio (mp3 o
    wav, cualquier formato) al backend "torchcodec", que a su vez necesita
    las DLLs de FFmpeg -- no instaladas en este sistema. torchaudio.load()
    revienta con "Could not load libtorchcodec" para cualquier archivo,
    incluso un wav trivial (confirmado con una prueba minima), lo que rompe
    XTTS.clone_voice al leer el clip de referencia (TTS/tts/models/xtts.py:
    load_audio llama a torchaudio.load directamente) -- afecta a CUALQUIER
    voz con engine: xtts, no solo a la intro.

    En vez de instalar FFmpeg a nivel de sistema o tocar el paquete TTS
    (site-packages), se reemplaza torchaudio.load por una version propia
    basada en soundfile (que si puede leer mp3/wav en este venv) con el
    mismo contrato de entrada/salida (tensor [canales, muestras] + sample
    rate), asi que load_audio() de xtts.py sigue funcionando sin cambios."""
    global _torchaudio_patched
    if _torchaudio_patched:
        return
    import soundfile as sf
    import torch
    import torchaudio

    def _load_via_soundfile(path, *args, **kwargs):
        data, sr = sf.read(path, dtype="float32", always_2d=True)
        waveform = torch.from_numpy(data.T.copy())
        return waveform, sr

    torchaudio.load = _load_via_soundfile
    _torchaudio_patched = True


def _get_model():
    global _model
    if _model is None:
        _patch_torchaudio_load()
        from TTS.api import TTS

        _model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    return _model


def synthesize(text: str, voice_cfg: dict, out_path: Path, base_dir: Path) -> Path:
    clone_ref = voice_cfg.get("clone_ref")
    if not clone_ref:
        raise ValueError("voz xtts sin 'clone_ref' (ruta al .wav de referencia) en config.yaml")

    model = _get_model()
    model.tts_to_file(
        text=text,
        speaker_wav=str(base_dir / clone_ref),
        language="es",
        file_path=str(out_path),
    )
    return out_path
