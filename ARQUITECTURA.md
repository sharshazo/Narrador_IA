# Narrador_IA — Arquitectura técnica

Le pone voz (IA neuronal, en español) a las misiones de LOTRO: botón
"Narrar" bajo demanda + historias ambientales al azar. Corre separado
del juego, en dos piezas, porque un addon Lua de LOTRO no puede hacer
esto solo:

```
LOTRO (Turbine/Lua)                          Windows (Python)
┌───────────────────────┐   .plugindata   ┌──────────────────────────┐
│ QuestSync              │ ───────────────▶│ Narrador_IA               │
│ (Core/NarratorBridge   │  (archivo en    │ (esta carpeta)            │
│  .lua -- boton         │   disco, un     │  1. detecta el archivo    │
│  "Narrar")             │   disparo por   │  2. lo sondea (~40ms)     │
│                        │   click)        │  3. cache en disco o      │
│                        │                 │     motor (edge/xtts)     │
│                        │                 │     -> audio              │
│                        │                 │  4. reproduce (winmm/MCI) │
└───────────────────────┘                 └──────────────────────────┘
```

**Nota histórica (2026-09-06):** existió una tercera pieza,
`LOTRO_Chat_Narrator` (un addon que reenviaba el chat ambiental del
juego para narrarlo automáticamente). Se eliminó porque esa función
venía **desactivada por defecto** (todos los canales en `false` en
`config.yaml`) y nunca se usó en la práctica — el botón "Narrar" y las
historias ambientales nunca dependieron de ella. El código de este
lado que sabe leer ese feed (`src/plugindata.py:PluginDataReader`,
la sección `channels:` de `config.yaml`) se dejó en el repositorio sin
tocar, pero ya no hay nada del lado de LOTRO que le escriba —
inofensivo, simplemente inerte.

## Por qué esta arquitectura (y no un addon "todo en uno")

Los plugins Lua de LOTRO corren en el sandbox de Turbine: **no** tienen
`io.*` de propósito general, `os.execute`, ni forma de sintetizar o
reproducir audio arbitrario. El único mecanismo real de persistencia es
`Turbine.PluginData` (el mismo que usan QuestSync/DeedTracker/MoorMap en
esta cuenta) — confirmado leyendo el código real de esos addons y la
documentación del framework (`LOTRO-LUA-PLUGIN-API.md`, goldbishop.github.io
/Lotro_LUA). Por eso QuestSync solo escribe el texto donde esta app lo
pueda leer, y la IA de voz corre del lado de Windows.

`Turbine.PluginData.Save` con `Turbine.DataScope.Account` escribe siempre en
la misma ruta fija sin importar servidor/personaje activo:

```
Documentos\The Lord of the Rings Online\PluginData\<cuenta>\AllServers\LOTRO_Narrator_PlayRequest.plugindata
```

Ese archivo es una tabla Lua literal (`return { ... }`, igual formato que
los SavedVariables de WoW) — `Narrador_IA` lo interpreta con la librería
`luadata`.

## Instalación

Ver el [README principal](README.md) para la instalación end-to-end
(un solo `Instalar.bat`, crea su propio entorno virtual e instala
`edge-tts`/`luadata`/`pyyaml`/`pystray`/`pillow`/`requests` solo). Las
voces son 45 voces neuronales gratis de edge-tts (ver "Motores de voz"
abajo) — no hace falta descargar ningún modelo.

## Uso

Con LOTRO abierto, doble clic en `run_narrador.bat` (o, si activaste
el arranque automático en `Instalar.bat`, no hace falta nada — arranca
solo). Aparece un icono en la bandeja del sistema:

- Click con el botón derecho → **Pausar narración** / **Reanudar narración**
- **Salir** para cerrar la app

Si `pystray` no puede crear el icono (poco común), la app sigue funcionando
en modo consola (Ctrl+C para salir).

## Narración de misiones: manual únicamente

QuestSync (`LOTRO_Quest_Assistant`) narra misiones bajo demanda con el
**botón "Narrar"** en el Tracker (misiones activas), la ventana
principal (el diccionario maestro completo — cualquier misión del
juego, no solo las activas) y el libro de misión. Existió una versión
que narraba sola al aceptar/avanzar/completar una misión, pero se
desactivó a pedido explícito del usuario (2026-09-03): con la latencia
real de `Turbine.PluginData.Save` (~2-15s, ver más abajo), una
narración "automática" sonaba varios segundos después del evento que
la disparó, sintiéndose desconectada — un click del jugador no tiene
ese problema, siempre se siente intencional. Las funciones que arman
el texto (`NarratorBridge.PlayQuestText`/`AnnounceCompleted`) siguen
vivas, solo que ahora las llama exclusivamente el botón manual.

Además, cada tanto (mientras se juega) el narrador cuenta solo una
historia o consejo corto al azar (`ambient_enabled` en `config.yaml`)
— independiente del chat y de las misiones, no requiere ningún click.

Al hacer click en "Narrar", se narra:

- El nombre de la misión.
- El texto de objetivos/flavor (`QuestLocES[ndx].objectivesES`), sin el
  filtro que el resto de QuestSync aplica para su propia UI (líneas de
  diálogo/exclamación de PNJ que ahí se descartan, acá sí interesan).
- Los puntos/pasos de la misión, uno por uno (`QuestStagesCoords[ndx]`,
  la misma fuente que ya usan los marcadores de mapa) — narración
  completa, no solo el nombre.

Mecanismo:

```
QuestSync (Core/NarratorBridge.lua)  --[click, o evento de estado]--> LOTRO_Narrator_PlayRequest.plugindata
        (nombre + objetivos + puntos + NPC que la da)   (ring buffer, varios pedidos a la vez)
                                                                        │
                                                                        ▼
                                                        Narrador_IA lo detecta y busca en
                                                        VoiceOverData/cache/ primero; si no
                                                        está, sintetiza (edge/xtts)
                                                        con la voz de ESE NPC, con prioridad
                                                        sobre el chat ambiental
```

Es un archivo `PluginData` de cuenta aparte del feed de chat — así se puede
tratar como pedido explícito/automático (sin los filtros de duplicado/largo
del chat ambiental, y con prioridad: interrumpe la cola normal, no la
reproducción en curso). Es un ring buffer (no un solo registro) porque la
narración automática puede disparar dos eventos casi seguidos (aceptar +
primer progreso) antes de que Narrador_IA alcance a sondear el archivo.

### Motores de voz

`src/engines/` — cada voz de `config.yaml` declara su `engine`:

- **`edge`** (gratis, sin API key, **requiere internet**): usa el servicio
  de lectura en voz alta de Microsoft Edge (`edge-tts`) — 45 voces en
  español de 22 países (`es-ES-AlvaroNeural`, `es-MX-DaliaNeural`,
  `es-AR-TomasNeural`, etc.). Motor principal del proyecto.
- **`xtts`** (clonación local y gratuita, **opcional**): Coqui XTTS v2 clona
  una voz a partir de un clip de referencia corto (`voices/reference/`, ver
  su README) — pensado para que un personaje principal suene lo más
  parecido posible a su voz real. Instalación aparte (pesada, ~2GB):
  `pip install coqui-tts torch torchaudio torchcodec` (además requiere
  FFmpeg instalado en el sistema).

**Piper (offline) se sacó a propósito** (2026-09-02): LOTRO es un MMO
online — si no hay internet, el juego mismo se desconecta, así que un motor
de respaldo "sin internet" no tenía caso de uso real. Si `edge`/`xtts`
fallan por otro motivo (servicio caído, dependencia no instalada, clip de
referencia faltante), se cae automáticamente a una voz `edge` fija de
respaldo (`FALLBACK_VOICE_NAME` en `src/tts.py`) — nunca se deja al jugador
sin narración por un error puntual.

ElevenLabs/Cartesia (motores de pago) no están implementados todavía por
falta de API key — agregar uno es un archivo más en `src/engines/` con la
misma firma `(text, voice_cfg, out_path, base_dir) -> Path`, más una entrada
en `voices:`.

### Caché de audio (`VoiceOverData/cache/`)

Generación perezosa: cada línea (voz + texto exacto) se sintetiza **una sola
vez** (`src/voicecache.py`, indexado por hash de voz+texto) y de ahí en
adelante se reproduce directo desde disco — gratis, instantáneo, sin
depender de internet aunque la voz sea `edge`. Si el texto cambia (p.ej. se
mejora una traducción), el hash cambia solo y se regenera sola, sin ningún
paso manual de invalidación.

### Voces de NPCs principales (clonación)

Cada misión manda también el NPC que la da (`quest.bestower`, dato real de
QuestSync). `src/npc_voice.py` revisa primero `main_npcs` en `config.yaml`
(override explícito nombre de NPC → nombre de voz, pensado para personajes
principales con una voz `xtts` clonada o una `edge` elegida a oído como "la
más parecida"); si el NPC no está en esa lista, cae a un hash estable (no
aleatorio) sobre `npc_voice_pool` — así el mismo NPC genérico siempre narra
con la misma voz, y NPCs distintos tienden a sonar distinto (45 voces
edge-tts en el pool por defecto).

## Personalización (`config.yaml`)

- `channels`: qué canal del **chat ambiental** narrar y con qué voz.
  **Inerte desde 2026-09-06**: dependía del addon `LOTRO_Chat_Narrator`
  (eliminado, ver nota histórica arriba) para recibir el chat en
  primer lugar — hoy nada le escribe a `LOTRO_Narrator_Feed.plugindata`,
  así que esta sección de `config.yaml` no tiene ningún efecto por más
  que se ponga `enabled: true`. Se deja documentada por si algún día se
  reconstruye ese addon.
- `voices`: cada entrada declara su `engine` (`edge`/`xtts`, ver arriba) más
  los parámetros de ese motor (`voice_id`/`rate`/`volume_pct`/`pitch` para
  edge, `clone_ref` para xtts). Para una voz edge nueva, buscar el
  `voice_id` exacto con `edge-tts --list-voices` (viene con el paquete
  `edge-tts`) y filtrar por `es-`.
- `npc_voice_pool` / `main_npcs`: reparto de voces por NPC, ver "Voces de
  NPCs principales" arriba.
- `cache_dir`: carpeta de audio pre-generado (relativa a esta carpeta).
- `max_chars`: mensajes más largos que esto se ignoran (evita leer bloques
  enteros de texto de zona/instancia).
- `dedupe_window_seconds`: ignora una línea idéntica repetida dentro de esa
  ventana (spam).
- `ignore_patterns`: lista de regex; cualquier mensaje que matchee se
  descarta.
- `plugindata_path`: solo si el autodetectado falla (cuenta con nombre
  atípico, instalación de LOTRO fuera de Documentos, etc.).

## Limitaciones conocidas

- `edge` requiere internet; sin Piper de respaldo, si LOTRO se juega sin
  conexión estable simplemente no habrá narración (decisión explícita: un
  MMO online no se juega sin internet de todas formas, ver "Motores de voz").
- `xtts` no viene instalado por defecto (dependencia pesada) — sin
  `pip install coqui-tts torch torchaudio torchcodec` + FFmpeg en el
  sistema, cualquier voz `engine: xtts` fallará y caerá a la voz `edge` de
  respaldo (`FALLBACK_VOICE_NAME`).
- ElevenLabs (`src/engines/elevenlabs_engine.py`): implementado y usado
  para la narración de introducción (`voices/intro_pool/`, generada una
  sola vez con una cuenta propia) — no hace falta para narrar misiones
  ni chat, eso es 100% edge-tts gratis.

## Estructura de archivos

```
Narrador_IA/
├── .venv/                  entorno virtual -- lo crea Instalar.bat,
│                           no viene incluido en el repositorio
├── voices/
│   └── reference/          clips de referencia para clonar voces (xtts)
├── VoiceOverData/
│   └── cache/              audio pre-generado (solo si cache_enabled: true)
├── src/
│   ├── engines/
│   │   ├── edge_engine.py     gratis, sin API key, requiere internet (motor principal)
│   │   └── xtts_engine.py     clonación local y gratuita (opcional)
│   ├── config.py           carga config.yaml con defaults
│   ├── plugindata.py       localiza y parsea los .plugindata (feed + pedidos)
│   ├── text_utils.py       limpieza, filtro de largo, anti-spam
│   ├── voicecache.py       caché de audio en disco (generación perezosa)
│   ├── playback.py         reproducción unificada (wav/mp3, winmm/MCI)
│   ├── npc_voice.py        asignación de voz por NPC (override + hash)
│   ├── tts.py              dispatcher de motores + cola de reproducción
│   ├── tray.py             icono de bandeja (pausar/reanudar/salir)
│   └── narrator.py         orquestador / punto de entrada
├── config.yaml
├── requirements.txt
└── run_narrador.bat
```
