# Clips de referencia para clonación de voz (motor xtts)

Deja acá el `.wav` de un NPC principal para clonar su voz con Coqui XTTS v2
(gratis, local, sin API key — ver `src/engines/xtts_engine.py`).

Requisitos del clip:

- 10–30 segundos.
- Un solo hablante, sin música/ruido/eco de fondo.
- Mono, 16kHz o más, formato `.wav`.

Luego, en `config.yaml`:

```yaml
voices:
  gandalf_clone:
    engine: xtts
    clone_ref: voices/reference/gandalf.wav

main_npcs:
  gandalf: gandalf_clone
```

Requiere instalar la dependencia opcional una sola vez:

```
.venv\Scripts\pip.exe install TTS torch
```
