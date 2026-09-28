# Narrador_IA

App de Windows que le pone voz a **The Lord of the Rings Online**:
narra las misiones y cuenta pequeñas historias del mundo de lotro al azar
mientras jugás, con voces en español (edge-tts,
45 voces de 22 países).

Requiere del complemento del addons LOTRO_Quest_Assistant que es el que tiene los botones de   narrar/silenciar. Link abajo
[**QuestSync**](https://github.com/sharshazo/LOTRO_Quest_Assistant) —
Este complemento corre aparte del juego porque LOTRO no permite que un addon reproduzca
audio por sí mismo.

## Instalación (de un solo clik)

1. Descargá esta carpeta completa.
2. Doble click en **`Instalar.bat`**.

Eso es todo. El instalador:

- busca Python en tu PC, y si no lo tenés, **lo descarga e instala
  solo** desde la página oficial (python.org) — no hay que buscar
  nada ni tildar ninguna casilla;
- crea su propio entorno, sin tocar nada más;
- instala las librerías necesarias;
- te pregunta si querés que arranque automáticamente cada vez que
  abrís LOTRO (recomendado).

Con LOTRO abierto (y [QuestSync](https://github.com/sharshazo/LOTRO_Quest_Assistant)
instalado), ya está: aparece un ícono en la bandeja del sistema y
los botones "Narrar"/altavoz del juego empiezan a sonar de verdad.

## Qué hace

- **Botón "Narrar"** en cualquier misión (Tracker, ventana principal o
  libro de misión): la lee en voz alta, con una voz fija
  según qué personaje la da.
- **Historias al azar**: cada 8-15 minutos, mientras jugás, el
  narrador cuenta solo una pequeña historia o consejo — sin que hagas
  nada.
- **Botón de altavoz** en el Tracker: apaga o prende toda la
  narración con un click.
- Todo con voces.

## Personalización

`config.yaml` tiene comentarios explicando cada opción (voces, volumen,
duración entre historias, etc.). No hace falta tocarlo para que
funcione — viene listo para usar.

## Para quien quiera los detalles técnicos

Ver [ARQUITECTURA.md](ARQUITECTURA.md): por qué el sistema está
dividido en dos piezas, cómo se comunican, motores de voz disponibles,
caché de audio, y estructura interna del código.
