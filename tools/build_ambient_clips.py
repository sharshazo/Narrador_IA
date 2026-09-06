"""Genera las narraciones ambientales aleatorias (historias, leyendas,
consejos -- pedido explicito del usuario, 2026-09-05) que reproduce
AmbientNarrator mientras se juega. SIN musica (a diferencia de intro_pool):
solo graves realzados (ver audio_fx.apply_narrator_fx), para no competir
con el audio del propio juego durante partidas largas.

Cada entrada de CLIPS es (nombre_de_archivo, texto_completo). El texto
puede traer marcas [PAUSA]/[PAUSA LARGA] igual que las otras narraciones --
se separan solas en fragmentos por oracion si no se ponen marcas explicitas
(ver _split_into_segments), asi que alcanza con pegar el texto tal cual lo
mande el usuario, sin tener que segmentarlo a mano cada vez.

Uso: .venv/Scripts/python.exe tools/build_ambient_clips.py
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

VOICE_NAME = "narrador_intro"
OUT_DIR = APP_DIR / "voices" / "ambient"
TMP_DIR = OUT_DIR / "_fragments"

PAUSA = 0.55
PAUSA_LARGA = 1.2

# Cada entrada: (nombre_archivo, texto, voice_settings_override opcional).
# voice_settings_override ajusta stability/style sobre la base de
# "narrador_intro" en config.yaml -- pedido explicito del usuario 2026-09-05
# ("la interpretacion debe cambiar segun la emocion de cada historia"):
# mas stability + menos style = interpretacion mas contenida/controlada
# (misterio, terror); menos stability + mas style = mas expresiva/dinamica
# (epica, determinacion).
CLIPS: list[tuple[str, str, dict]] = [
    (
        "las_luces_de_la_comarca",
        """Hola, viajero...

Antes de continuar tu camino, quiero pedirte algo.

Mira a tu alrededor.

Quizá ahora mismo estés atravesando un camino embarrado, persiguiendo una misión, buscando una criatura o simplemente tratando de llegar al siguiente pueblo antes de que caiga la noche.

Pero recuerda cómo empezó todo.

Hubo un tiempo en el que no conocías las grandes guerras.

No conocías Mordor.

No habías escuchado hablar de Angmar.

No sabías qué secretos podían esconder las montañas.

Quizá ni siquiera sabías que tu nombre terminaría siendo conocido en lugares que jamás habías imaginado visitar.

Y todo comenzó con algo mucho más pequeño.

Un camino.

Una aldea.

Un hogar.

La Comarca.

Los hobbits vivían allí sin preocuparse demasiado por las grandes historias del mundo. Mientras los reinos luchaban, mientras antiguos enemigos despertaban y mientras las sombras crecían lejos, ellos cultivaban sus campos, celebraban sus fiestas y regresaban a casa antes de que oscureciera.

Pero la paz nunca significa que el mundo se haya detenido.

A veces, las grandes historias comienzan precisamente cuando nadie las está buscando.

Y tú también comenzaste así.

Quizá pensabas que solo ibas a cumplir una pequeña tarea.

Ayudar a alguien.

Encontrar un objeto perdido.

Derrotar unos cuantos enemigos.

Pero cada paso te fue alejando un poco más de la seguridad.

Y entonces descubriste algo que muchos tardan toda una vida en comprender...

Las grandes aventuras no comienzan cuando sabes quién eres.

Comienzan cuando decides avanzar aunque todavía no lo sepas.

Hoy puedes mirar atrás y descubrir que aquel viajero que comenzó su camino ya no existe.

Has cruzado tierras peligrosas.

Has conocido pueblos que quizá nunca vuelvas a visitar.

Has visto amigos partir.

Has contemplado lugares hermosos.

Y también has conocido lugares donde hasta el viento parecía tener miedo.

Pero no olvides aquella primera sensación.

La de mirar un camino desconocido y preguntarte qué habría al otro lado.

Porque esa sensación...

esa pequeña chispa de curiosidad...

es la que todavía te mantiene caminando.

Así que sigue, viajero.

Deja que el mundo cambie.

Deja que las estaciones pasen.

Deja que las historias continúen.

Porque mientras exista un camino delante de ti...

todavía queda una historia por vivir.""",
        {"stability": 0.45, "similarity_boost": 0.8, "style": 0.5, "use_speaker_boost": True},
    ),
    (
        "el_silencio_de_moria",
        """Viajero...

Acércate un momento.

No demasiado.

Hay historias que es mejor escuchar desde cierta distancia.

¿Alguna vez te has preguntado qué siente alguien cuando entra por primera vez en Moria?

No hablo del miedo a los orcos.

Ni de las criaturas que pueden esconderse en la oscuridad.

Hablo del silencio.

Porque Moria no siempre fue un lugar muerto.

Hubo un tiempo en que sus salones estaban llenos de voces.

Los enanos caminaban por sus grandes cámaras.

Las forjas ardían día y noche.

El sonido de los martillos golpeando el metal podía escucharse a través de las montañas.

Khazad-dûm era uno de los mayores reinos de los enanos.

Sus riquezas parecían no tener fin.

Y entre todas ellas existía una maravilla que despertaba la codicia de muchos...

el mithril.

Un metal tan valioso que los enanos excavaron cada vez más profundo.

Más profundo...

y más profundo.

Hasta que encontraron algo que nunca debieron despertar.

Un terror antiguo.

Una criatura nacida de un tiempo tan remoto que incluso las historias de los hombres parecían jóvenes comparadas con ella.

El Balrog.

Durin's Bane.

La Perdición de Durin.

Los enanos intentaron resistir.

Pero sus armas no pudieron detenerlo.

Sus reyes cayeron.

Sus hogares quedaron abandonados.

Y la gran ciudad terminó convirtiéndose en aquello que hoy conocemos como Moria.

La Mina Negra.

Por eso, cuando camines por sus corredores, no pienses únicamente en los monstruos que habitan allí.

Piensa en lo que hubo antes.

Imagina las voces.

Las fiestas.

Las canciones.

Las familias.

Los herreros.

Los niños corriendo por aquellas mismas salas.

Imagina una ciudad llena de vida...

y después escucha.

Escucha el silencio.

Porque ese es el verdadero terror de Moria.

No saber qué hay en la oscuridad.

Sino saber que, alguna vez, aquella oscuridad estuvo llena de vida.

Y que todo aquello desapareció.

Así que si alguna vez te encuentras allí abajo...

no tengas prisa.

Mira las columnas.

Mira las antiguas puertas.

Observa las marcas que dejaron aquellos que vivieron antes que nosotros.

Porque Moria no es solamente una mazmorra.

Es un recuerdo.

Un recuerdo de lo que ocurre cuando el deseo de encontrar riquezas hace que alguien cave demasiado profundo.

Y quizá...

si escuchas con suficiente atención...

todavía puedas oír el eco de los martillos.""",
        {"stability": 0.5, "similarity_boost": 0.8, "style": 0.45, "use_speaker_boost": True},
    ),
    (
        "el_reino_que_murio_de_pie",
        """Viajero...

Hoy quiero hablarte de un reino.

Pero no de un reino lleno de gloria.

Quiero hablarte de uno que aprendió a morir lentamente.

Angmar.

Durante generaciones, aquel nombre significó miedo.

El Rey Brujo estableció allí su dominio y desde el norte comenzó a extender su sombra sobre los pueblos de los Dúnedain.

El enemigo no necesitaba destruirlo todo de una vez.

Solo necesitaba esperar.

Esperar a que los hombres se enfrentaran entre ellos.

Esperar a que sus reinos se debilitaran.

Esperar a que la esperanza desapareciera.

Y durante años funcionó.

Los antiguos reinos del norte fueron cayendo.

Los enemigos avanzaban.

Los pueblos abandonaban sus hogares.

Y las tierras que alguna vez habían conocido prosperidad comenzaron a llenarse de ruinas.

Pero hubo quienes se negaron a desaparecer.

Los montaraces.

Hombres que caminaban por caminos olvidados.

Hombres sin grandes ejércitos.

Sin coronas.

Sin palacios.

Muchos ni siquiera recibieron canciones por sus hazañas.

Y, sin embargo, continuaron.

Eso es lo que más me impresiona de ellos.

No luchaban porque supieran que ganarían.

Luchaban porque alguien tenía que hacerlo.

¿Comprendes la diferencia?

Hay personas que luchan cuando saben que la victoria está asegurada.

Y hay otras que luchan precisamente cuando todo parece perdido.

Los montaraces pertenecían a estos últimos.

Mientras los reinos del sur levantaban murallas y reunían ejércitos, ellos protegían caminos.

Vigilaban bosques.

Perseguían enemigos.

Ayudaban a viajeros que jamás conocerían sus nombres.

Y cuando alguien les preguntaba por qué seguían haciéndolo...

probablemente no tenían una respuesta gloriosa.

Simplemente era su deber.

Así que cuando recorras las tierras del norte y encuentres ruinas antiguas...

no pienses solamente en lo que se perdió.

Piensa también en aquellos que permanecieron.

Porque un reino puede caer.

Una ciudad puede desaparecer.

Una torre puede convertirse en polvo.

Pero mientras alguien esté dispuesto a levantarse una vez más...

la historia todavía no ha terminado.

Quizá esa sea también tu historia.

No necesitas una corona.

No necesitas que los bardos canten tu nombre.

A veces basta con permanecer de pie.

Incluso cuando todo lo demás ha caído.""",
        {"stability": 0.4, "similarity_boost": 0.8, "style": 0.55, "use_speaker_boost": True},
    ),
    (
        "cuando_los_elfos_abandonaron_eregion",
        """Hola, viajero...

¿Sabes qué es lo extraño de las ruinas?

Que nunca están realmente vacías.

Puedes caminar entre piedras cubiertas de musgo.

Puedes encontrar una puerta rota.

Una estatua caída.

Un camino que ya nadie utiliza.

Y aun así...

cada piedra parece recordar algo.

Eso es Eregion.

Mucho antes de que tú caminaras por sus tierras, aquel lugar fue hogar de grandes artesanos élficos.

Allí, los Gwaith-i-Mírdain trabajaron el metal y el conocimiento.

Y durante un tiempo, los elfos y los enanos de Khazad-dûm mantuvieron una relación que permitió que ambos pueblos prosperaran.

Los caminos atravesaban la región.

Las mercancías viajaban entre los reinos.

Las puertas permanecían abiertas.

Pero entonces llegó la traición.

Sauron apareció bajo una forma engañosa.

Ofreció conocimiento.

Ofreció poder.

Y los elfos escucharon.

Los Anillos de Poder fueron creados.

Pero detrás de aquellas promesas había una intención oscura.

Sauron quería controlar lo que los demás habían creado.

Y cuando su engaño fue descubierto...

la guerra llegó.

Eregion fue destruida.

Sus habitantes fueron dispersados.

Sus grandes obras quedaron atrás.

Y los caminos que antes estaban llenos de viajeros terminaron cubiertos por el silencio.

Por eso, cuando recorras Eregion...

no la mires simplemente como una región que debes atravesar.

Mírala como un lugar que alguna vez estuvo lleno de esperanza.

Porque esa es quizá la parte más triste de su historia.

No fue destruida porque fuera débil.

Fue destruida porque sus habitantes creyeron que podían utilizar el poder sin ser consumidos por él.

Y esa lección ha perseguido a la Tierra Media durante siglos.

El poder siempre promete que será diferente esta vez.

Que tú podrás controlarlo.

Que tú serás lo bastante fuerte.

Pero el poder no necesita derrotarte en una batalla.

Solo necesita convencerte de que lo necesitas.

Así que sigue caminando, viajero.

Cuando encuentres aquellas antiguas ruinas...

recuerda a quienes estuvieron allí antes.

Sus sueños.

Sus errores.

Su orgullo.

Y su caída.

Porque incluso las ruinas tienen algo que enseñarnos.

Solo debemos aprender a escucharlas.""",
        {"stability": 0.45, "similarity_boost": 0.8, "style": 0.5, "use_speaker_boost": True},
    ),
    (
        "la_noche_en_que_el_bosque_desperto",
        """Viajero...

No corras.

Escucha primero.

¿Oyes eso?

Las hojas.

Las ramas.

Ese sonido que parece acercarse...

y después desaparece.

Bienvenido al Bosque Negro.

Muchos viajeros creen que el peligro de un bosque está en aquello que pueden ver.

Un lobo.

Un orco.

Una araña.

Pero el Bosque Negro enseña algo diferente.

Aquí el peligro está en aquello que no puedes ver.

Durante mucho tiempo, la sombra fue creciendo en el bosque.

Los árboles se volvieron más oscuros.

Los caminos más peligrosos.

Las criaturas más agresivas.

Y poco a poco, aquello que alguna vez fue un gran bosque comenzó a convertirse en un lugar donde la propia naturaleza parecía rechazar a quienes entraban.

Las arañas se extendieron.

Los enemigos levantaron sus refugios.

Y en Dol Guldur, una presencia terrible dominaba desde las alturas.

Pero incluso allí...

la esperanza no desapareció por completo.

Los elfos continuaron resistiendo.

Los exploradores continuaron avanzando.

Los mensajeros siguieron cruzando el bosque.

Y entonces llegaron historias sobre un ataque.

Una compañía.

Una misión.

Un peligro demasiado grande para ser ignorado.

Mientras las fuerzas de Lothlórien preparaban su ofensiva contra Dol Guldur, otros se movían en secreto.

Porque algunas batallas se ganan con ejércitos.

Y otras...

con unos pocos que están dispuestos a entrar donde nadie más quiere hacerlo.

Eso es lo que debes recordar cuando estés solo en el bosque.

No siempre necesitas ser el más fuerte.

A veces necesitas ser el que continúa caminando.

Incluso cuando no sabe qué hay delante.

Así que si alguna noche atraviesas el Bosque Negro y escuchas ramas romperse a tu espalda...

no mires inmediatamente.

Respira.

Agarra tu arma.

Y sigue caminando.

Porque quizá el sonido haya sido solo el viento.

Quizá haya sido una criatura.

O quizá...

algo haya estado caminando contigo desde hace mucho tiempo.

Y no quería que lo supieras.""",
        {"stability": 0.55, "similarity_boost": 0.8, "style": 0.4, "use_speaker_boost": True},
    ),
    (
        "la_ultima_defensa_de_gondor",
        """Viajero...

Hoy no quiero hablarte de una batalla ganada.

Quiero hablarte de una batalla que parecía imposible de ganar.

Gondor.

Durante generaciones, aquel reino soportó la presión de Mordor.

Sus hombres conocían la guerra.

Sus soldados vigilaban las fronteras.

Sus fortalezas protegían caminos y ciudades.

Pero ninguna muralla permanece fuerte para siempre.

Cuando la sombra volvió a crecer...

Gondor tuvo que recordar por qué seguía luchando.

No luchaban porque fueran invencibles.

Luchaban porque detrás de ellos estaban sus hogares.

Sus familias.

Sus amigos.

Sus muertos.

Y mientras las fuerzas de Mordor avanzaban...

los defensores permanecían.

Piensa en eso.

Un soldado sobre una muralla.

La noche delante de él.

El enemigo acercándose.

Y detrás...

su ciudad.

¿Qué harías tú?

¿Huirías?

¿Te esconderías?

¿O permanecerías en tu puesto?

La valentía no significa no tener miedo.

Eso es algo que muchos olvidan.

La valentía significa sentir miedo...

y aun así levantar el escudo.

Sentir que las fuerzas te abandonan...

y aun así mantenerte de pie.

Escuchar que el enemigo es demasiado poderoso...

y responder: Entonces tendremos que resistir un poco más.

Eso es Gondor.

No una tierra de hombres perfectos.

No un reino sin heridas.

Sino un pueblo que aprendió a resistir.

Y quizá por eso sus historias continúan siendo recordadas.

Porque cuando todo parece perdido...

alguien debe permanecer.

Tal vez tú hayas sentido algo parecido.

Quizá alguna misión te haya parecido demasiado difícil.

Quizá hayas perdido una batalla.

Quizá hayas caído.

Pero aquí estás.

Otra vez.

Con tu arma en la mano.

Con otro camino delante.

Así que levántate, viajero.

No necesitas conquistar el mundo hoy.

Solo necesitas dar el siguiente paso.

Una batalla.

Una misión.

Un enemigo.

Un día más.

Y algún día mirarás atrás...

y descubrirás que no fue una gran hazaña la que cambió tu historia.

Fueron todas esas pequeñas veces en las que pudiste rendirte...

y decidiste continuar.""",
        {"stability": 0.3, "similarity_boost": 0.8, "style": 0.75, "use_speaker_boost": True},
    ),
    (
        "el_secreto_de_los_montaraces",
        """Viajero...

Mira a ese hombre que acaba de pasar junto a ti.

¿Lo viste?

Probablemente no.

Y ese es precisamente el punto.

Los montaraces no necesitan que los veas.

Mientras tú recorres los caminos de Eriador, ellos pueden estar observándote desde un bosque.

Desde una colina.

Desde las ruinas de una antigua torre.

Quizá hayas pensado alguna vez que los grandes héroes son aquellos cuyos nombres conoce todo el mundo.

Pero los montaraces enseñan lo contrario.

Ellos protegen tierras que ya no tienen rey.

Vigilan caminos que casi nadie utiliza.

Persiguen enemigos que rara vez aparecen en las canciones.

Y muchas veces llegan después de que el peligro ha pasado...

sin que nadie sepa que estuvieron allí.

Su historia está ligada a los restos de los antiguos reinos del norte.

Cuando aquellas tierras cayeron, no desaparecieron todos sus guardianes.

Algunos continuaron.

Generación tras generación.

Padre después de padre.

Hijo después de hijo.

Manteniendo una responsabilidad que nadie les había obligado a aceptar.

Imagínalo.

Nacer en un mundo donde tu pueblo ya no posee un gran reino.

Crecer entre ruinas.

Saber que tu linaje pertenece a una antigua corona...

pero vivir como un viajero más.

Y aun así...

proteger.

Eso requiere una clase especial de fuerza.

Una fuerza que no necesita reconocimiento.

Por eso, cuando encuentres a uno de ellos...

no lo mires simplemente como otro personaje del camino.

Recuerda que probablemente sabe cosas que tú desconoces.

Ha visto enemigos antes de que aparecieran.

Ha recorrido caminos que tú todavía no conoces.

Y quizá esté protegiendo tu viaje sin que siquiera lo sepas.

Esa es la ironía de los verdaderos guardianes.

Su mayor éxito consiste en que nadie se dé cuenta de que estaban allí.

Así que la próxima vez que atravieses una zona peligrosa...

mira las colinas.

Observa los árboles.

Presta atención a las sombras.

Quizá estés completamente solo.

O quizá...

alguien lleve horas vigilando tu camino.""",
        {"stability": 0.45, "similarity_boost": 0.8, "style": 0.5, "use_speaker_boost": True},
    ),
    (
        "la_caida_de_amarthiel",
        """Viajero...

Hay historias de villanos.

Y luego existen historias de personas que alguna vez pudieron haber sido héroes.

Esta es una de ellas.

Amarthiel.

Mucho antes de convertirse en una de las grandes amenazas de Angmar, fue una elfa.

Una artesana.

Una persona con talento.

Alguien que conocía el poder de la creación.

Pero también conoció algo que ha destruido a muchos antes que ella.

La ambición.

En sus manos llegó a existir un Anillo de Poder menor, Narchuil.

Y con él llegó la promesa de algo irresistible.

Más conocimiento.

Más poder.

Más capacidad para cambiar el mundo.

Al principio quizá pensó que podía controlarlo.

Como tantos otros.

Pero el poder rara vez entra en nuestras vidas diciendo que viene a destruirnos.

Primero promete ayudarnos.

Después nos convence de que lo necesitamos.

Y finalmente...

nos hace olvidar quiénes éramos antes de poseerlo.

Amarthiel cayó.

Su historia quedó ligada a Angmar, a la sombra del Rey Brujo y a una lucha que atravesaría generaciones.

Pero lo más interesante de su historia no es solamente su caída.

Es que detrás del enemigo seguía existiendo el recuerdo de alguien que alguna vez había sido diferente.

Eso hace que sus decisiones sean todavía más tristes.

Porque algunos enemigos nacen en la oscuridad.

Otros llegan allí poco a poco.

Una elección.

Después otra.

Y otra.

Hasta que un día miran hacia atrás...

y ya no reconocen el camino por el que llegaron.

Quizá esa sea una de las lecciones más importantes de la Tierra Media.

No siempre perdemos el camino en una gran batalla.

A veces lo perdemos lentamente.

Y por eso, viajero...

vigila tus propios pasos.

No importa cuánta experiencia tengas.

No importa cuántos enemigos hayas derrotado.

Nunca pienses que estás por encima de la tentación.

Porque incluso aquellos que alguna vez fueron nobles...

pueden caer.

Y quizá la verdadera victoria no consista en destruir a nuestros enemigos.

Quizá consista en no convertirnos en aquello que juramos combatir.""",
        {"stability": 0.4, "similarity_boost": 0.8, "style": 0.55, "use_speaker_boost": True},
    ),
    (
        "el_hombre_que_camino_hacia_mordor",
        """Viajero...

Alguna vez te has preguntado qué siente alguien cuando mira hacia Mordor?

No desde un mapa.

No desde una historia.

Desde el suelo.

Cuando el aire cambia.

Cuando las montañas parecen cerrarse.

Cuando sabes que delante de ti no existe un camino fácil para regresar.

Mordor no es simplemente una tierra.

Es un lugar construido alrededor del miedo.

Durante mucho tiempo, la sombra de Sauron convirtió sus fronteras en una amenaza para todos los pueblos libres.

Y aun después de la caída del Señor Oscuro, nos muestra algo que muchos olvidarían...

la historia no termina cuando cae el enemigo.

Porque quedan ruinas.

Quedan soldados.

Quedan criaturas.

Quedan personas que todavía viven bajo la sombra de aquello que ocurrió.

Entrar en Mordor después de una guerra no significa caminar por un lugar vacío.

Significa caminar entre las consecuencias.

Cada fortaleza destruida cuenta una historia.

Cada campo quemado recuerda una batalla.

Cada enemigo derrotado deja preguntas.

¿Qué ocurrió aquí?

¿Quién vivió aquí?

¿Quién murió?

¿Quién sobrevivió?

Y entonces comprendes algo.

A veces el verdadero trabajo comienza después de la victoria.

Reconstruir.

Explorar.

Ayudar.

Recordar.

Dar un nombre a aquellos que quedaron olvidados.

Eso también es heroísmo.

No todas las hazañas tienen que terminar con una espada levantada.

Algunas terminan colocando una piedra sobre una tumba.

Ayudando a un desconocido.

Encendiendo una luz.

Volviendo a un lugar donde nadie quiere regresar.

Por eso, viajero...

si algún día miras una tierra devastada y piensas que ya no queda nada...

mira otra vez.

Quizá todavía quede alguien esperando ayuda.

Quizá todavía exista una historia que contar.

Quizá todavía pueda crecer algo.

Porque la oscuridad puede destruir mucho.

Pero no puede decidir lo que hacemos después.

Eso...

eso siempre será nuestro.""",
        {"stability": 0.42, "similarity_boost": 0.8, "style": 0.55, "use_speaker_boost": True},
    ),
    (
        "el_viajero_que_nadie_recordara",
        """Hola, viajero...

Te voy a contar algo que quizá no quieras escuchar.

Algún día...

tu historia terminará.

Sí.

Incluso la tuya.

No importa cuántos enemigos derrotes.

Cuántas misiones completes.

Cuántas montañas cruces.

Llegará un momento en que otro viajero ocupará tu lugar.

Caminará por los mismos caminos.

Pasará por las mismas ciudades.

Y quizá nunca sepa que tú estuviste allí.

Pero eso no significa que tu viaje no haya importado.

Piensa en todos los héroes de la Tierra Media.

Algunos tienen estatuas.

Otros aparecen en canciones.

Algunos aparecen en los libros que cuentan las grandes guerras.

Pero muchos...

muchísimos...

fueron olvidados.

Personas que llevaron mensajes.

Soldados que defendieron una puerta.

Exploradores que encontraron un camino.

Campesinos que alimentaron a un ejército.

Curanderos que salvaron vidas.

Personas cuyos nombres nunca aprendimos.

Y sin embargo...

sin ellos, las grandes historias no habrían ocurrido.

Eso es lo hermoso de tu aventura.

Quizá no seas Aragorn.

Quizá no seas Gandalf.

Quizá tu nombre nunca aparezca en una canción.

Pero cada vez que ayudas a alguien...

cada vez que derrotas a un enemigo...

cada vez que llevas un mensaje...

cada vez que exploras una tierra desconocida...

estás dejando algo detrás.

No siempre en el mundo.

A veces dentro de ti.

Experiencia.

Recuerdos.

Amistades.

Fracasos.

Victorias.

Y cuando algún día mires hacia atrás...

descubrirás que no recuerdas todas las recompensas.

No recuerdas cada enemigo.

No recuerdas cada camino.

Recordarás momentos.

La primera vez que viste una gran ciudad.

La primera vez que entraste en una mazmorra.

La primera vez que derrotaste a un enemigo que parecía imposible.

La primera vez que alguien te ayudó cuando estabas perdido.

Eso es una aventura.

No es solamente llegar al final.

Es todo aquello que ocurre mientras intentas llegar.

Así que sigue caminando, viajero.

Puede que nadie escriba una canción sobre ti.

Puede que nadie levante una estatua.

Puede que algún día nadie recuerde tu nombre.

Pero mientras estés aquí...

mientras tengas un camino delante...

tu historia todavía pertenece a este mundo.

Y eso...

es suficiente.""",
        {"stability": 0.35, "similarity_boost": 0.8, "style": 0.6, "use_speaker_boost": True},
    ),
    # Segundo lote (2026-09-05): el narrador se dirige mas directo al
    # jugador ("viajero", "aventurero", "tu"), como si lo reconociera con
    # el tiempo -- distinto de las primeras 10 (historia/leyendas de la
    # Tierra Media en tercera persona).
    (
        "el_mundo_que_te_espera",
        """Hola, viajero...

Sí.

Tú.

Te he visto avanzar por estos caminos.

Al principio caminabas con cautela.

Mirabas cada sendero.

Observabas cada sombra.

Y quizá no sabías muy bien qué te esperaba al otro lado de aquella colina.

Pero has continuado.

Una misión tras otra.

Una batalla tras otra.

Un camino tras otro.

Y por lo que veo...

todavía no has tenido suficiente.

Eso es bueno.

Porque la Tierra Media no es un mundo que pueda conocerse en un solo viaje.

Siempre existe un camino que no has recorrido.

Una ruina que todavía no has descubierto.

Una historia que nadie te ha contado.

Y quizá...

un enemigo que todavía no sabe que vas en su búsqueda.

Pero antes de que continúes...

quiero recordarte algo.

No midas tu aventura únicamente por las victorias.

Recuerda también las veces que caíste.

Las veces que tuviste que regresar.

Las veces que miraste a un enemigo y pensaste: Quizá todavía no estoy preparado.

Y aun así...

volviste.

Eso también es fuerza.

No la fuerza de quien nunca pierde.

Sino la de quien siempre vuelve a levantarse.

Así que continúa, viajero.

Sigue explorando.

Sigue aprendiendo.

Sigue levantando tus armas.

Porque todavía quedan historias por vivir...

y algunas de ellas...

están esperando precisamente por ti.

Ahora ve.

Tu camino continúa.""",
        {"stability": 0.4, "similarity_boost": 0.8, "style": 0.55, "use_speaker_boost": True},
    ),
    (
        "veo_que_continuas_luchando",
        """Veo que continúas luchando, viajero...

Una batalla más.

Un enemigo más.

Otro camino recorrido.

Parece que la oscuridad todavía no ha conseguido detenerte.

Pero dime...

¿alguna vez te has preguntado por qué sigues avanzando?

¿Por qué después de tantos peligros...

sigues tomando tu arma?

¿Por qué después de caer...

vuelves a levantarte?

Quizá al principio luchabas por una recompensa.

Por experiencia.

Por mejorar tu equipo.

Pero con el tiempo...

algo cambia.

Empiezas a luchar por algo más.

Por aquellos que conociste.

Por aquellos que ayudaste.

Por aquellos que esperan que regreses.

Y eso es algo que muchos héroes descubrieron demasiado tarde.

La fuerza de un guerrero no se mide solamente por el poder de su espada.

Se mide por aquello que está dispuesto a proteger.

Así que cuando vuelvas a encontrarte frente a un enemigo...

recuerda todo lo que has recorrido.

No eres el mismo viajero que comenzó este camino.

Has aprendido.

Has crecido.

Has sobrevivido.

Y mientras continúes avanzando...

serás más fuerte mañana que hoy.

Así que levanta tu arma.

Mira hacia el horizonte.

Y continúa.

La batalla todavía no ha terminado...

pero tú tampoco.""",
        {"stability": 0.32, "similarity_boost": 0.8, "style": 0.7, "use_speaker_boost": True},
    ),
    (
        "viajero_tengo_que_contarte_una_historia",
        """Viajero...

Tengo que contarte una historia.

Pero acércate.

Estas cosas no deberían contarse a gritos.

Hace mucho tiempo...

mucho antes de que tú caminaras por estos caminos...

hubo quienes recorrieron exactamente estas tierras.

Guerreros.

Reyes.

Viajeros.

Pueblos enteros.

Algunos fueron recordados.

Otros desaparecieron sin dejar nombre.

Pero todos dejaron algo atrás.

Una espada.

Una ruina.

Una vieja torre.

Una canción.

Una historia.

Y algunas historias...

todavía esperan a alguien que las descubra.

Quizá por eso has llegado hasta aquí.

No por casualidad.

Tal vez el camino te ha traído hasta un lugar que guarda algo que nadie ha encontrado durante generaciones.

Mira las piedras.

Observa los caminos.

No pases demasiado rápido.

La Tierra Media está llena de secretos que solo aparecen cuando alguien se detiene a mirar.

Una puerta abandonada puede esconder un reino.

Un viejo mapa puede conducir a un tesoro.

Una pequeña inscripción puede revelar la historia de un pueblo entero.

Así que cuando explores...

no tengas prisa.

Escucha.

Observa.

Pregunta.

Porque una aventura no consiste solamente en llegar al destino.

A veces...

la verdadera aventura está en descubrir por qué ese camino existía.

Ahora continúa, viajero.

La historia que buscabas...

quizá esté justo delante de ti.""",
        {"stability": 0.5, "similarity_boost": 0.8, "style": 0.45, "use_speaker_boost": True},
    ),
    (
        "por_fin_te_encuentro_viajero",
        """Por fin te encuentro, viajero...

Llevaba tiempo esperando.

Te he visto pasar por muchos lugares.

Primero estabas en los caminos tranquilos.

Después comenzaron las tierras peligrosas.

Y ahora...

mira hasta dónde has llegado.

Ya no eres aquel aventurero que dudaba antes de cruzar una frontera.

Has visto cosas que muchos jamás conocerán.

Has entrado en lugares donde otros ni siquiera se atreven a mirar.

Has enfrentado criaturas que parecían imposibles.

Y aquí estás.

Todavía avanzando.

Quizá no te hayas dado cuenta...

pero el viaje te ha cambiado.

Tu armadura es diferente.

Tus armas son mejores.

Tus habilidades han crecido.

Pero lo más importante...

es que ahora conoces el camino.

Sabes que no todos los enemigos pueden ser derrotados a la primera.

Sabes que algunas puertas requieren paciencia.

Y sabes que incluso después de perder...

siempre existe un camino para regresar.

Eso es lo que convierte a un viajero en aventurero.

Y a un aventurero...

en héroe.

Pero no te confundas.

Todavía queda mucho.

Muchísimo.

Más allá de esas montañas existen tierras que aún no conoces.

Y algunas de ellas...

pondrán a prueba todo lo que has aprendido.

Así que descansa si lo necesitas.

Prepara tus armas.

Reúne a tus compañeros.

Y cuando estés listo...

continúa.

Porque he esperado mucho tiempo para encontrarte.

Y sospecho...

que lo mejor de tu historia todavía está por comenzar.""",
        {"stability": 0.4, "similarity_boost": 0.8, "style": 0.55, "use_speaker_boost": True},
    ),
    (
        "sigue_elevando_tus_armas",
        """Sigue elevando tus armas, viajero.

Una vez más.

No importa cuántas veces hayas luchado.

No importa cuántos enemigos hayan caído ante ti.

Siempre habrá otro desafío.

Otro camino.

Otra batalla.

Pero escucha bien.

No estás luchando solamente contra aquello que tienes delante.

Cada batalla te está convirtiendo en alguien diferente.

Más fuerte.

Más preparado.

Más consciente de tus propias capacidades.

Recuerda el primer enemigo que derrotaste.

Probablemente hoy no representaría ningún peligro.

Pero en aquel momento...

era un desafío.

Y lo superaste.

Así es como crece un héroe.

No de golpe.

Poco a poco.

Batalla tras batalla.

Derrota tras derrota.

Victoria tras victoria.

Así que no desprecies los pequeños progresos.

Ese nuevo objeto.

Ese nuevo nivel.

Esa nueva habilidad.

Ese enemigo que antes no podías derrotar...

y que ahora cae ante ti.

Todo cuenta.

Sigue elevando tus armas.

Sigue mejorando.

Sigue avanzando.

Porque algún día encontrarás un enemigo frente a ti...

y recordarás todos los días en los que pensaste que no eras suficientemente fuerte.

Y entonces descubrirás algo.

Sí lo eras.

Solo necesitabas tiempo.

Ahora...

adelante, viajero.

Tu próxima batalla te espera.""",
        {"stability": 0.3, "similarity_boost": 0.8, "style": 0.72, "use_speaker_boost": True},
    ),
    (
        "detente_un_momento",
        """Detente un momento, viajero.

No avances todavía.

Mira a tu alrededor.

¿Qué ves?

Un bosque.

Un camino.

Una montaña.

Quizá un pequeño pueblo.

Parece algo normal...

¿verdad?

Pero aquí está el secreto de la Tierra Media.

Nada es simplemente lo que parece.

Ese camino pudo ser recorrido por un ejército.

Esa montaña pudo esconder un antiguo reino.

Ese bosque pudo haber sido hogar de un pueblo que desapareció hace siglos.

Y esas piedras...

quizá sean todo lo que queda de una historia que alguna vez fue grandiosa.

Nos acostumbramos tanto a avanzar...

que olvidamos mirar.

Queremos llegar a la siguiente misión.

Al siguiente nivel.

A la siguiente recompensa.

Pero la Tierra Media recompensa a quienes observan.

Así que, de vez en cuando...

detente.

Mira el cielo.

Escucha el viento.

Observa las montañas.

Deja que tu personaje simplemente permanezca allí unos segundos.

Porque quizás eso también sea parte de la aventura.

No todo tiene que ser una batalla.

No todo tiene que ser una recompensa.

A veces...

simplemente estar allí...

es suficiente.

Ahora sí.

Puedes continuar.

Pero la próxima vez que pases por aquí...

quizá mires este lugar de otra manera.""",
        {"stability": 0.55, "similarity_boost": 0.8, "style": 0.4, "use_speaker_boost": True},
    ),
    (
        "sabes_donde_estas",
        """Viajero...

¿sabes dónde estás?

No me refiero al nombre de la región.

Ni al pueblo que aparece en tu mapa.

Te pregunto...

¿sabes sobre qué historia estás caminando?

Bajo tus pies pueden existir siglos de historia.

Quizá estés caminando por un antiguo reino.

Quizá por un camino utilizado por guerreros hace cientos de años.

Quizá estés frente a una fortaleza que sobrevivió a guerras que ya nadie recuerda.

La Tierra Media está llena de lugares así.

Lugares que parecen pequeños...

pero que esconden historias enormes.

Y tú tienes algo que muchos de aquellos que vivieron aquí nunca tuvieron.

La oportunidad de recorrerlos.

Puedes entrar en sus ruinas.

Hablar con sus habitantes.

Descubrir sus secretos.

Y formar parte de acontecimientos que alguna vez parecían imposibles.

Así que la próxima vez que llegues a una nueva región...

no pienses solamente: ¿Qué misión debo hacer?

Pregúntate: ¿Qué ocurrió aquí?

Porque cuando comienzas a hacer esa pregunta...

el mundo cambia.

Dejas de ver simples escenarios.

Empiezas a ver historias.

Y entonces...

la Tierra Media cobra vida.""",
        {"stability": 0.48, "similarity_boost": 0.8, "style": 0.48, "use_speaker_boost": True},
    ),
    (
        "otra_vez_nos_encontramos",
        """Otra vez nos encontramos, viajero.

Parece que nuestros caminos siguen cruzándose.

La última vez apenas estabas comenzando.

Ahora...

mírate.

Has cambiado.

Aunque debo admitir...

sigues metiéndote en problemas.

Pero quizá eso sea inevitable.

Después de todo...

¿qué clase de aventurero sería aquel que evita todos los peligros?

Has recorrido caminos que parecían interminables.

Has ayudado a desconocidos.

Has enfrentado criaturas.

Has descubierto lugares.

Y seguramente también has cometido algún que otro error.

Pero todo eso forma parte del viaje.

No tengas miedo de equivocarte.

Un camino equivocado puede llevarte a un lugar inesperado.

Una derrota puede enseñarte algo.

Una misión que parecía insignificante puede terminar convirtiéndose en uno de tus mejores recuerdos.

Por eso...

continúa.

No sabes qué encontrarás mañana.

Quizá conozcas nuevos compañeros.

Quizá encuentres un objeto que llevabas mucho tiempo buscando.

Quizá descubras una región completamente nueva.

O quizá simplemente encuentres un hermoso lugar donde detenerte a contemplar el paisaje.

Sea lo que sea...

es tu aventura.

Así que nos veremos nuevamente.

En algún camino.

En alguna montaña.

En alguna ciudad.

O quizá...

en medio de una batalla.

Hasta entonces, viajero...

mantén tus armas preparadas.

Y nunca dejes de explorar.""",
        {"stability": 0.42, "similarity_boost": 0.8, "style": 0.55, "use_speaker_boost": True},
    ),
    (
        "cuando_la_oscuridad_regresa",
        """La oscuridad rara vez llega de golpe.

Primero...

aparece un rumor.

Un enemigo visto en un camino.

Una criatura que nadie había visto antes.

Una sombra en el horizonte.

Después llegan más.

Y entonces...

alguien comienza a preguntarse: ¿Está regresando?

Así comienza muchas veces el regreso de la oscuridad.

No con un ejército.

Sino con una señal.

Durante años, muchos creen que la amenaza ha desaparecido.

Las guerras terminan.

Las armas se guardan.

Los pueblos reconstruyen sus casas.

Los viajeros vuelven a recorrer los caminos.

Y poco a poco...

la gente deja de mirar hacia el horizonte.

Hasta que algo cambia.

Una torre vuelve a iluminarse.

Un antiguo enemigo reaparece.

Una criatura que debía estar muerta vuelve a caminar.

Y aquellos que recuerdan las antiguas historias...

comienzan a preocuparse.

Porque quienes conocen la historia saben algo que otros olvidan.

El mal puede esperar.

Puede esconderse.

Puede cambiar de forma.

Puede permanecer en silencio durante años...

hasta encontrar el momento adecuado.

Pero la historia también nos enseña algo más.

La oscuridad nunca ha sido invencible.

Siempre ha existido alguien dispuesto a enfrentarse a ella.

Un guerrero.

Un viajero.

Un pueblo.

Un grupo de amigos.

A veces...

una sola persona.

Y aquí es donde entras tú.

No sabes qué encontrarás al final del camino.

Quizá aparezca un enemigo que no puedes derrotar.

Quizá pierdas una batalla.

Quizá tengas que regresar y prepararte mejor.

Eso no significa que hayas fracasado.

Significa que todavía estás escribiendo tu historia.

Así que cuando la oscuridad aparezca...

no pienses solamente en lo poderosa que es.

Pregúntate algo diferente.

¿Qué puedo hacer yo?

Porque quizá no puedas cambiar el mundo entero.

Pero puedes salvar a alguien.

Puedes defender un pueblo.

Puedes derrotar a un enemigo.

Puedes abrir un camino.

Y quizá...

eso sea exactamente lo que la Tierra Media necesita de ti.

La oscuridad puede ser antigua.

Puede ser poderosa.

Puede parecer invencible.

Pero mientras alguien esté dispuesto a encender una luz...

todavía existe esperanza.""",
        {"stability": 0.35, "similarity_boost": 0.8, "style": 0.65, "use_speaker_boost": True},
    ),
    (
        "tu_propia_leyenda",
        """Algún día...

quizá mires hacia atrás.

Y recuerdes el momento en que comenzaste.

Quizá tu personaje todavía era débil.

Quizá llevaba un equipo sencillo.

Quizá no conocía los caminos.

No conocía las ciudades.

No conocía a sus compañeros.

No sabía qué peligros estaban esperando.

Solo sabía una cosa.

Había un camino delante.

Y decidió recorrerlo.

Desde entonces has cruzado bosques.

Has atravesado montañas.

Has visitado pueblos.

Has descubierto ruinas.

Has enfrentado criaturas.

Has ayudado a desconocidos.

Has perdido batallas.

Has ganado otras.

Y probablemente...

has pasado más tiempo del que esperabas buscando ese objeto que alguien te pidió encontrar.

Pero todo cuenta.

Incluso aquello que parecía insignificante.

Porque tu historia no está formada únicamente por las grandes batallas.

También está formada por los pequeños momentos.

El primer caballo.

La primera arma realmente poderosa.

El primer viaje a una tierra desconocida.

La primera vez que viste una ciudad enorme.

El primer compañero que te ayudó cuando estabas en problemas.

Aquella misión que parecía sencilla...

y terminó llevándote mucho más lejos de lo que imaginabas.

Esos recuerdos...

son tu aventura.

En los libros de la Tierra Media se habla de grandes nombres.

Frodo.

Aragorn.

Gandalf.

Legolas.

Gimli.

Y muchos otros.

Sus historias se convirtieron en leyendas.

Pero recuerda algo.

Mientras ellos vivían sus aventuras...

también existían miles de personas recorriendo los caminos.

Luchando sus propias batallas.

Viviendo sus propias historias.

Y esa es la magia de tu viaje.

No necesitas reemplazar a los héroes de los libros.

No necesitas ser Aragorn.

No necesitas ser Gandalf.

No necesitas ser nadie más.

Puedes ser tú.

Tu personaje.

Tu camino.

Tus decisiones.

Tus compañeros.

Tus victorias.

Tus derrotas.

Tu historia.

Así que sigue explorando.

Acepta esa misión.

Cruza esa montaña.

Entra en esa mazmorra.

Ayuda a ese extraño.

Enfrenta a ese enemigo.

Descubre qué existe más allá del horizonte.

Porque todavía quedan caminos que no has recorrido.

Historias que no has vivido.

Lugares que todavía no has descubierto.

Y cuando llegue el momento...

cuando hayas recorrido una parte de esta enorme Tierra Media...

quizá comprendas algo.

No estabas simplemente jugando una aventura.

Estabas construyendo recuerdos.

Quizá tu nombre nunca aparezca en los libros.

Quizá ningún bardo cante tus hazañas.

Pero mientras recuerdes el camino...

mientras recuerdes a quienes conociste...

mientras recuerdes las batallas que libraste...

tu historia habrá valido la pena.

Así que adelante, aventurero.

El mundo es enorme.

El camino continúa.

Y tu leyenda...

todavía está siendo escrita.""",
        {"stability": 0.32, "similarity_boost": 0.8, "style": 0.68, "use_speaker_boost": True},
    ),
    (
        "amarthiel_la_hija_de_la_discordia",
        """Viajero...

Hoy quiero contarte una historia.

Pero no una historia sobre un héroe.

Ni sobre un rey.

Quiero hablarte de alguien que una vez estuvo mucho más cerca de la luz de lo que imaginas.

Su nombre era Amarthiel.

Antes de que su nombre fuera pronunciado con temor en las tierras del norte...

antes de Angmar...

antes de la guerra...

antes de la oscuridad...

Amarthiel fue una elfa.

Una artesana.

Una mujer dotada de un talento extraordinario para trabajar los secretos de la creación.

Vivió en Eregion, una tierra donde los elfos buscaban comprender poderes que podían cambiar el destino de la Tierra Media.

Y allí comenzó su caída.

Porque existe una diferencia muy pequeña entre querer aprender...

y querer poseer.

Al principio, quizá solo buscaba conocimiento.

Después quiso poder.

Y finalmente...

quiso aquello que el poder siempre termina prometiendo.

Control.

En sus manos llegó a encontrarse Narchuil, un Anillo de Poder.

Y desde ese momento, su historia quedó unida a la sombra de Angmar.

Pero escucha bien, viajero...

porque aquí es donde esta historia se vuelve realmente triste.

Amarthiel no era un monstruo desde el principio.

No nació para servir a la oscuridad.

Fue tomando decisiones.

Una detrás de otra.

Cada una parecía pequeña.

Cada una parecía justificable.

Hasta que llegó un momento en el que regresar ya no era tan sencillo.

Y mientras tú recorrías las tierras de Eriador...

mientras ayudabas a pueblos, viajeros y montaraces...

la sombra de Amarthiel crecía.

Angmar volvía a despertar.

Sus servidores comenzaban a moverse.

Y una antigua amenaza que muchos creían enterrada comenzaba a respirar nuevamente.

Quizá por eso su historia sea tan importante.

Porque no habla solamente de un enemigo.

Habla de lo fácil que puede ser perderse.

Puedes comenzar buscando respuestas...

y terminar buscando dominación.

Puedes comenzar creyendo que controlarás el poder...

y terminar siendo controlado por él.

Y cuando finalmente Amarthiel comprendió el precio de sus decisiones...

ya había dejado demasiadas cosas atrás.

Demasiadas vidas.

Demasiadas promesas.

Demasiados recuerdos.

Así que cuando escuches su nombre durante tu viaje...

no pienses simplemente en una villana.

Recuerda a la persona que existió antes.

Porque algunas de las historias más tristes de la Tierra Media...

no son las historias de quienes nacieron en la oscuridad.

Son las historias de aquellos que alguna vez caminaron bajo la luz...

y decidieron apartarse de ella.

Y quizá esa sea una advertencia también para ti, viajero.

No importa cuánto poder consigas.

No importa cuántos enemigos derrotes.

No importa cuánto avance tu camino.

Nunca olvides quién eras cuando comenzaste.

Porque algunas batallas...

no se libran contra el enemigo que tienes delante.

Se libran contra aquello en lo que podrías convertirte.""",
        {"stability": 0.4, "similarity_boost": 0.8, "style": 0.55, "use_speaker_boost": True},
    ),
    # Tercer lote (2026-09-05): coleccion de 20 historias de eventos/lugares
    # de LOTRO (Angmar, Moria, Rohan, Gondor, Mordor, etc.) -- distinta de
    # los otros 2 lotes (leyendas generales / narrador dirigiendose al
    # jugador). PENDIENTE DE GENERAR: excede la cuota mensual de ElevenLabs
    # disponible al momento de pegar estos textos -- ver aviso en el chat.
    (
        "cuando_angmar_volvio_a_mirar_al_sur",
        """Hola, viajero...

Antes de continuar tu camino, quiero contarte algo que quizá todavía no comprendas.

Cuando comenzaste tu aventura, muchos creían que las sombras del norte eran solamente recuerdos.

Historias antiguas.

Leyendas contadas alrededor de una hoguera.

Pero algunas leyendas nunca mueren.

Solo esperan.

Durante siglos, Angmar permaneció como una herida abierta en las tierras del norte.

El reino del Rey Brujo había caído mucho tiempo atrás.

Sus fortalezas fueron destruidas.

Sus ejércitos dispersados.

Sus enemigos creyeron que finalmente podían respirar tranquilos.

Pero la oscuridad no siempre desaparece cuando derrotas a quien la dirige.

A veces simplemente cambia de forma.

Y mientras tú recorrías Eriador...

algo comenzaba a moverse nuevamente.

Criaturas que durante años habían permanecido ocultas comenzaron a aparecer.

Los caminos dejaron de ser seguros.

Los montaraces hablaban de movimientos extraños.

Los pueblos recibían noticias que nadie quería escuchar.

Angmar estaba despertando.

Pero había algo todavía peor.

Alguien estaba intentando recuperar antiguos poderes.

Porque el pasado puede ser una espada.

Y alguien estaba dispuesto a desenterrarla.

Quizá cuando escuchaste por primera vez hablar de Angmar no imaginaste todo lo que había ocurrido allí.

No imaginaste las guerras.

No imaginaste los reyes que cayeron.

No imaginaste cuántas generaciones habían vivido con miedo al simple sonido de aquel nombre.

Pero ahora tú estabas caminando hacia ese mismo lugar.

Y cada paso te acercaba a una historia mucho más antigua que tú.

Una historia de traición.

De poder.

De pérdida.

Y de personas que se negaron a permitir que Angmar volviera a dominar el norte.

Así comenzó una de las grandes historias de tu viaje.

No con un ejército marchando.

No con una gran batalla.

Sino con pequeñas señales.

Un enemigo visto al otro lado de una colina.

Un mensaje que nunca llegó.

Un pueblo preocupado.

Un rumor.

Una sombra.

Y luego otra.

Hasta que finalmente comprendiste la verdad.

La oscuridad no estaba regresando.

Nunca se había ido por completo.

Solo estaba esperando el momento adecuado.

Y ahora...

te había encontrado a ti.""",
        {"stability": 0.5, "similarity_boost": 0.8, "style": 0.45, "use_speaker_boost": True},
    ),
    (
        "amarthiel_la_mujer_detras_del_enemigo",
        """Viajero...

Hay nombres que aprendemos a pronunciar con miedo.

Y hay nombres que deberíamos pronunciar con tristeza.

Amarthiel pertenece a los dos.

Antes de convertirse en una de las grandes amenazas de tu viaje...

fue una elfa.

Una mujer con talento.

Con conocimiento.

Con sueños.

No nació en las sombras de Angmar.

Llegó hasta ellas.

Y esa diferencia importa.

Porque su historia no comenzó con maldad.

Comenzó con deseo.

El deseo de conocer.

De crear.

De alcanzar algo que otros no podían.

En Eregion, los elfos habían trabajado durante generaciones con conocimientos que podían cambiar el destino de la Tierra Media.

Los anillos de poder habían dejado una huella profunda en aquellas tierras.

Y Amarthiel terminó ligada a uno de ellos.

Narchuil.

Un anillo que representaba algo más que poder.

Representaba la posibilidad de controlar fuerzas que ningún mortal debería controlar.

Al principio...

quizá pensó que podía dominarlo.

Que ella sería diferente.

Que podía utilizar ese poder para alcanzar sus objetivos sin pagar el precio.

Pero la oscuridad rara vez muestra el precio al principio.

Primero ofrece respuestas.

Después ofrece poder.

Y finalmente...

cobra todo lo demás.

Amarthiel cayó.

Su destino terminó unido a Angmar y a fuerzas que buscaban aprovechar su poder.

Mientras tú avanzabas por Eriador, ella se convertía poco a poco en una amenaza que podía arrastrar a pueblos enteros a la guerra.

Pero escucha bien, viajero...

porque esto es lo importante.

No recuerdes solamente a Amarthiel como una enemiga.

Recuerda a la persona que existió antes.

Porque esa es la parte más trágica de su historia.

Alguna vez tuvo la oportunidad de elegir otro camino.

Y cada decisión la llevó un poco más lejos.

Hasta que llegó un momento en que regresar parecía imposible.

Su historia nos recuerda algo que la Tierra Media repite una y otra vez.

El poder no siempre corrompe de golpe.

A veces lo hace lentamente.

Con pequeñas decisiones.

Con pequeñas excusas.

Con pequeñas renuncias.

Hasta que un día...

miras hacia atrás...

y ya no reconoces a la persona que eras.

Por eso, viajero...

cuando vuelvas a escuchar su nombre...

recuerda que algunas tragedias no comienzan con monstruos.

Comienzan con alguien que quiso demasiado.

Y terminó perdiéndolo todo.""",
        {"stability": 0.4, "similarity_boost": 0.8, "style": 0.55, "use_speaker_boost": True},
    ),
    (
        "la_historia_de_laerdan",
        """Viajero...

Hay historias que no terminan cuando derrotas al enemigo.

Hay historias que continúan viviendo dentro de quienes quedaron atrás.

Quiero hablarte de Laerdan.

Un elfo.

Un padre.

Un hombre marcado por una pérdida que nunca consiguió aceptar completamente.

Mucho antes de que tú conocieras su nombre, Laerdan había vivido durante mucho tiempo con una herida.

Su hija, Narchuil y los acontecimientos relacionados con Angmar terminarían uniendo su destino al de Amarthiel.

Pero detrás de todas esas grandes palabras...

guerra...

poder...

Angmar...

existía algo mucho más sencillo.

Un padre intentando proteger a su hija.

Y eso es lo que hace que su historia resulte tan dolorosa.

Porque los grandes acontecimientos de la Tierra Media pueden cambiar reinos.

Pero también destruyen familias.

Laerdan tomó decisiones movido por el amor.

Y como ocurre tantas veces en estas historias...

el amor puede ser una fuerza maravillosa.

Pero también puede convertirse en una cadena.

Cuando alguien que amas está en peligro, es fácil convencerse de que cualquier sacrificio está justificado.

Cualquier riesgo.

Cualquier decisión.

Cualquier precio.

Y cuando finalmente comprendes que quizá has ido demasiado lejos...

puede ser demasiado tarde.

La historia de Laerdan está llena de esa clase de dolor.

No es simplemente una historia sobre héroes y villanos.

Es una historia sobre las consecuencias.

Sobre aquello que estamos dispuestos a hacer por alguien que amamos.

Y sobre cómo incluso las mejores intenciones pueden llevarnos por caminos oscuros.

Quizá por eso, viajero...

cuando recuerdes las grandes batallas de Angmar, no recuerdes solamente a los ejércitos.

Recuerda a las personas.

Los padres.

Los hijos.

Los amigos.

Aquellos que esperaban que alguien regresara.

Porque la guerra nunca es solamente una guerra.

Siempre hay alguien esperando detrás de ella.

Y algunas personas regresan.

Otras no.

Y algunas...

regresan siendo diferentes.

Laerdan es una de esas historias.

Una historia de amor que terminó enfrentándose a una oscuridad que ningún padre debería conocer.

Y quizá sea por eso que su nombre todavía pesa.

Porque algunas heridas no se ven.

Solo se llevan.

Durante años.

A veces durante siglos.""",
        {"stability": 0.4, "similarity_boost": 0.8, "style": 0.5, "use_speaker_boost": True},
    ),
    (
        "los_dias_en_que_evendim_fue_un_reino",
        """Hola, viajero...

Cuando camines por Evendim, mira las ruinas.

No las pases de largo.

Porque esas piedras fueron alguna vez un reino.

Antes de que tú llegaras...

antes de los caminos rotos...

antes de las ruinas...

antes del silencio...

Annúminas fue una ciudad de poder.

Fue el corazón del antiguo reino de Arnor.

Los Dúnedain del Norte habían levantado allí su hogar.

Torres.

Murallas.

Salones.

Monumentos.

Todo parecía destinado a durar.

Pero ningún reino dura para siempre.

Arnor terminó dividido.

Las luchas internas debilitaron a sus pueblos.

Y después llegó Angmar.

La guerra terminó destruyendo aquello que parecía eterno.

Annúminas cayó.

Y el reino desapareció.

Pero la ciudad permaneció.

No como había sido.

Sino como un recuerdo.

Cuando tú caminas por sus ruinas, no estás simplemente explorando una zona antigua.

Estás caminando sobre los restos de una historia.

Puedes imaginar las calles llenas.

Los mercados.

Los soldados regresando de sus guardias.

Los niños corriendo.

Las familias esperando noticias.

Y luego...

el silencio.

Ese es el verdadero peso de Evendim.

No aquello que queda.

Sino todo aquello que falta.

Pero hay algo hermoso en ello.

Porque las ruinas también cuentan historias.

Te recuerdan que hubo personas antes que tú.

Personas que construyeron.

Que amaron.

Que lucharon.

Que perdieron.

Y que siguieron adelante mientras pudieron.

Quizá algún día alguien camine por un lugar donde tú estuviste.

Y encuentre solamente las huellas que dejaste.

Por eso no subestimes las pequeñas cosas.

Una misión.

Una conversación.

Un camino.

Una ayuda prestada a un desconocido.

Todo forma parte de una historia mayor.

Evendim nos enseña que los reinos pueden desaparecer...

pero las historias permanecen.

Así que cuando vuelvas a pasar por aquellas aguas...

detente un momento.

Mira Annúminas.

Y recuerda que antes de ser una ruina...

fue un hogar.""",
        {"stability": 0.5, "similarity_boost": 0.8, "style": 0.45, "use_speaker_boost": True},
    ),
    (
        "los_hombres_que_caminaban_sin_reino",
        """Viajero...

¿Alguna vez has visto a un montaraz del norte y te has preguntado quién es realmente?

No lleva una corona.

No tiene un gran ejército.

No vive en un palacio.

Y probablemente nadie celebrará su llegada con trompetas.

Pero quizá esté protegiendo tu camino.

Los montaraces son los restos vivientes de un reino que ya no existe.

Descendientes de los Dúnedain del Norte.

Herederos de una tierra perdida.

Cuando Arnor desapareció, ellos no desaparecieron con él.

Continuaron.

Generación tras generación.

Vigilando caminos.

Protegiendo pueblos.

Persiguiendo enemigos.

Y haciendo todo aquello que alguien debía hacer.

Pero existe algo extraño en su historia.

No luchan para recuperar una gloria inmediata.

Luchan porque saben que hay personas que necesitan protección.

Aunque esas personas nunca conozcan sus nombres.

Piensa en ello, viajero.

Quizá hayas pasado junto a uno de ellos sin darte cuenta.

Quizá haya estado observándote desde una colina.

Quizá haya eliminado a un enemigo antes de que tú llegaras.

Y tú nunca lo supiste.

Ese es el precio de ser un guardián.

Cuando haces bien tu trabajo...

nadie se da cuenta.

Los montaraces conocen ese precio.

Han aprendido a vivir sin reconocimiento.

Sin canciones.

Sin recompensas.

Y aun así continúan.

Quizá por eso su historia sea una de las más nobles de Eriador.

Porque no todo héroe necesita una estatua.

Algunos simplemente necesitan saber que alguien está a salvo.

Así que la próxima vez que veas a uno...

no lo mires como un personaje más.

Míralo como lo que realmente representa.

Un pueblo que perdió su reino...

pero no perdió su deber.

Un linaje que perdió sus tierras...

pero no perdió su identidad.

Y mientras existan personas dispuestas a proteger a otros sin esperar reconocimiento...

la esperanza todavía tendrá guardianes.""",
        {"stability": 0.45, "similarity_boost": 0.8, "style": 0.5, "use_speaker_boost": True},
    ),
    (
        "las_puertas_de_moria",
        """Viajero...

Llegará un momento en que el camino te llevará hasta una puerta.

Y detrás de ella...

estará Moria.

Pero antes de entrar...

quiero que imagines cómo era aquel lugar.

No pienses en monstruos.

No pienses en oscuridad.

Piensa en vida.

Moria fue Khazad-dûm.

El gran reino de los enanos.

Durante generaciones, sus habitantes excavaron en las montañas.

Construyeron salones.

Puentes.

Forjas.

Carreteras subterráneas.

Ciudades enteras bajo la piedra.

Y entre todas las riquezas que encontraron...

existía una que cambió su destino.

El mithril.

Un metal extraordinario.

Más ligero que el acero.

Más resistente.

Más valioso.

Los enanos quisieron más.

Y excavaron más profundo.

Hasta que encontraron algo que no debía ser despertado.

El Balrog.

La criatura que los enanos llamarían la Perdición de Durin.

Desde ese momento...

Khazad-dûm comenzó a morir.

Los habitantes huyeron.

Las grandes salas quedaron vacías.

Y el reino que había parecido eterno se convirtió en una tumba.

Por eso, cuando entres en Moria...

escucha.

Quizá no escuches nada.

Y precisamente por eso debes hacerlo.

Porque detrás del silencio todavía existe una ciudad.

Puedes imaginar los martillos.

Las voces.

Las canciones.

El ruido de las forjas.

Los pasos de miles de enanos.

Todo aquello estuvo allí.

Y desapareció.

Pero la historia de Moria todavía no había terminado.

Mucho después...

otros entrarían en sus profundidades.

Enanos.

Elfos.

Hombres.

Y tú.

Porque las ruinas nunca están completamente vacías.

Siempre existe alguien dispuesto a regresar.

Y a veces...

ese alguien eres tú.""",
        {"stability": 0.5, "similarity_boost": 0.8, "style": 0.45, "use_speaker_boost": True},
    ),
    (
        "mazog_el_enemigo_de_las_profundidades",
        """Viajero...

Hay enemigos que quieren conquistar.

Otros quieren destruir.

Y algunos...

simplemente quieren vengarse.

Mazog era uno de ellos.

Un líder orco que había conseguido reunir fuerzas dentro de Moria.

Su nombre comenzó a convertirse en una amenaza para los enanos que intentaban recuperar el antiguo reino.

Porque para los enanos, Moria no era una cueva.

Era su hogar perdido.

Su historia.

Sus muertos.

Su orgullo.

Y Mazog entendía perfectamente eso.

Por eso la lucha contra él era algo más que una guerra.

Era una lucha por recuperar lo que había sido arrebatado.

Pero había algo especialmente peligroso en Mazog.

Su determinación.

No necesitaba que todos sus enemigos fueran destruidos.

Solo necesitaba mantenerlos divididos.

Mientras los enanos intentaban recuperar sus antiguas salas, los orcos reforzaban sus posiciones.

Cada corredor podía convertirse en una trampa.

Cada puerta podía esconder un enemigo.

Cada victoria podía ser temporal.

Y entonces comenzó una persecución.

No solo para derrotar a Mazog...

sino para impedir que escapara de Moria y continuara llevando la guerra a otras tierras.

Ahí es donde tu camino se cruza con el suyo.

No como un espectador.

Sino como alguien que debe entrar en las profundidades.

Luchar.

Investigar.

Y sobrevivir.

Porque algunas historias no permiten permanecer al margen.

Te obligan a elegir un lado.

Y cuando finalmente comprendes lo que está en juego...

descubres que Moria no está luchando solamente contra los orcos.

Está luchando contra el olvido.

Los enanos quieren demostrar que su reino todavía puede levantarse.

Y para conseguirlo...

deben enfrentarse a aquello que ahora ocupa sus antiguos hogares.

Mazog es solo una parte de esa guerra.

Pero a veces...

una sola figura puede convertirse en el rostro de todo un enemigo.

Y para muchos enanos...

ese rostro tenía un nombre.

Mazog.""",
        {"stability": 0.3, "similarity_boost": 0.8, "style": 0.65, "use_speaker_boost": True},
    ),
    (
        "el_bosque_que_ya_no_era_el_mismo",
        """Viajero...

Si alguna vez entras en el Bosque Negro...

no confíes en el silencio.

Porque el silencio aquí no significa paz.

Durante mucho tiempo, aquel bosque había sido un lugar diferente.

Los elfos lo conocían.

Los animales lo recorrían.

Los viajeros podían encontrar caminos entre los árboles.

Pero la sombra creció.

Y cuando creció...

el bosque cambió.

Los árboles parecían más oscuros.

Las criaturas más peligrosas.

Los caminos más difíciles de encontrar.

Y en el corazón de aquella oscuridad se encontraba Dol Guldur.

Una fortaleza que se había convertido en uno de los centros de poder de la sombra.

Los elfos de Lothlórien sabían que no podían ignorarla.

Así que comenzaron a moverse.

Exploradores.

Guerreros.

Mensajeros.

Pequeños grupos entrando en lugares donde nadie quería entrar.

Y tú terminarías formando parte de esa historia.

Pero hay algo que debes recordar.

El enemigo no siempre aparece delante de ti.

A veces está arriba.

Entre los árboles.

Detrás de una roca.

Esperando.

Por eso caminar por el Bosque Negro puede producir una sensación diferente a cualquier otra región.

No sabes qué te observa.

No sabes cuánto tiempo lleva ahí.

Y no sabes si el sonido que escuchaste...

fue el viento.

O algo más.

Pero incluso allí...

los pueblos libres continuaron luchando.

Porque mientras exista alguien dispuesto a entrar en un lugar oscuro para encender una luz...

la oscuridad no habrá ganado.

Así que si algún día estás solo entre aquellos árboles...

no te apresures.

Escucha.

Mira.

Respira.

Y recuerda...

no todo lo que no puedes ver está lejos.""",
        {"stability": 0.55, "similarity_boost": 0.8, "style": 0.4, "use_speaker_boost": True},
    ),
    (
        "los_elfos_que_marcharon_hacia_dol_guldur",
        """Viajero...

Hay momentos en los que esperar significa perder.

Y hubo un momento en que los elfos de Lothlórien comprendieron que ya no podían limitarse a defenderse.

La sombra estaba demasiado cerca.

Dol Guldur seguía siendo una amenaza.

Así que comenzaron los preparativos.

No era una simple expedición.

Era una marcha hacia uno de los lugares más peligrosos de la Tierra Media.

Los elfos avanzaron hacia el Bosque Negro.

No porque ignoraran el peligro.

Sino porque lo conocían demasiado bien.

Sabían qué podía estar esperando detrás de cada árbol.

Sabían qué criaturas servían a la sombra.

Sabían que algunos de ellos quizá no regresarían.

Y aun así...

marcharon.

Mientras tanto, otros acontecimientos estaban sucediendo en el bosque.

Mazog era transportado por los elfos.

Los enemigos intentaban aprovechar cualquier oportunidad.

Las criaturas atacaban desde la oscuridad.

Y la tensión aumentaba.

Pero una cosa estaba clara.

Dol Guldur no podía permanecer intacta.

Los pueblos libres necesitaban golpear antes de que el enemigo tuviera tiempo de recuperarse.

Entonces comenzó el avance.

Los guerreros atravesaron el bosque.

Las fuerzas de la sombra respondieron.

Y la batalla llegó a lugares donde durante mucho tiempo nadie se había atrevido a luchar.

Tú estabas allí.

No eras simplemente un espectador.

Formabas parte de una historia mucho mayor.

Una historia que demostraría que incluso las fortalezas de la oscuridad pueden ser alcanzadas.

Porque la valentía no significa caminar sin miedo.

Significa caminar hacia el miedo.

Y seguir avanzando.

Ese día...

los elfos demostraron que el Bosque Negro no pertenecía solamente a la sombra.

Todavía había quienes estaban dispuestos a luchar por él.

Y mientras quedara alguien dispuesto a hacerlo...

Dol Guldur nunca tendría la última palabra.""",
        {"stability": 0.3, "similarity_boost": 0.8, "style": 0.72, "use_speaker_boost": True},
    ),
    (
        "los_rangers_que_dejaron_el_norte",
        """Viajero...

¿Sabes por qué algunos hombres abandonan su hogar justo cuando más lo necesitan?

Porque alguien más necesita ayuda.

Cuando Aragorn partió hacia el sur...

los Rangers del Norte recibieron una llamada.

El camino era peligroso.

Rohan necesitaba ayuda.

Y aquellos hombres sabían que su deber no estaba solamente en Eriador.

Así comenzó una de las grandes historias de los Rangers.

La Compañía Gris.

Hombres acostumbrados a viajar.

A luchar.

A vivir lejos de los grandes salones.

Hombres que habían pasado años protegiendo el norte mientras casi nadie sabía que existían.

Ahora debían abandonar sus tierras.

Pero no todos estaban de acuerdo.

Porque dejar el norte significaba abandonar aquello que habían protegido durante generaciones.

Y, sin embargo...

el momento había llegado.

El destino de la Tierra Media estaba cambiando.

Los ejércitos se estaban reuniendo.

La guerra se acercaba.

Y Aragorn necesitaba aliados.

Así que los Rangers comenzaron a reunirse.

Uno después de otro.

Cada uno con su propia historia.

Cada uno con sus propias heridas.

Pero todos compartiendo un mismo propósito.

Viajar al sur.

Y ayudar.

Lo interesante, viajero...

es que tú también formas parte de ese encuentro.

No eres solamente alguien que observa cómo los grandes héroes avanzan.

Ayudas a reunirlos.

A preparar el camino.

A hacer posible que una compañía que parecía dispersa vuelva a caminar junta.

Y quizá esa sea una de las cosas más hermosas de esta historia.

Ningún héroe lo hace todo solo.

A veces...

la mayor hazaña consiste en reunir a quienes todavía creen que vale la pena luchar.

Así que cuando veas partir a los Rangers...

recuerda que están dejando atrás su hogar.

No saben qué encontrarán.

No saben quién regresará.

Pero caminan.

Porque alguien los necesita.""",
        {"stability": 0.4, "similarity_boost": 0.8, "style": 0.55, "use_speaker_boost": True},
    ),
    (
        "rohan_y_el_caballo_que_no_esperaba",
        """Hola, viajero...

Hay tierras que se conocen por sus ciudades.

Rohan no.

Rohan se conoce por sus caballos.

Por sus llanuras.

Por el sonido de los cascos.

Por hombres que pueden pasar días enteros bajo el cielo abierto.

Pero cuando llegues allí...

no pienses solamente en la belleza.

Porque Rohan está entrando en tiempos difíciles.

Los Rohirrim son un pueblo acostumbrado a la libertad.

Su vida está ligada a sus caballos.

A la tierra.

A sus familias.

A sus jinetes.

Pero la guerra se acerca.

Y mientras las sombras de Isengard crecen...

Rohan comienza a fracturarse.

El peligro no siempre llega desde fuera.

A veces...

se encuentra dentro.

Decisiones equivocadas.

Desconfianza.

Miedo.

Manipulación.

Y cuando un reino comienza a perder la confianza en sí mismo...

un enemigo puede hacer mucho más daño.

Por eso tu llegada a Rohan importa.

No vienes simplemente a recorrer sus praderas.

Llegas cuando el reino necesita ayuda.

Y poco a poco descubres que detrás de cada jinete existe una historia.

Un padre.

Una hija.

Un soldado.

Un campesino.

Alguien que solo quiere volver a casa.

Eso es lo que hace que Rohan sea tan especial.

La guerra puede ser enorme.

Pero sus razones son pequeñas.

Proteger una casa.

Proteger una familia.

Proteger un caballo.

Proteger una tierra.

Y mientras recorres aquellas llanuras...

quizá comprendas por qué los Rohirrim aman tanto su hogar.

Porque para ellos...

Rohan no es solamente un reino.

Es una forma de vivir.

Y cuando esa forma de vida está amenazada...

los caballos vuelven a correr.""",
        {"stability": 0.5, "similarity_boost": 0.8, "style": 0.5, "use_speaker_boost": True},
    ),
    (
        "isengard",
        """Viajero...

Hay lugares que parecen construidos para inspirar confianza.

Isengard no es uno de ellos.

Desde lejos puedes ver su torre.

Orthanc.

Negra.

Alta.

Dominando el paisaje.

Pero la verdadera amenaza no está en sus piedras.

Está en quien las ocupa.

Saruman.

Durante mucho tiempo fue considerado un sabio.

Un hombre de conocimiento.

Alguien a quien muchos respetaban.

Pero el conocimiento no garantiza sabiduría.

Y Saruman aprendió a utilizar lo que sabía para buscar poder.

Mientras tú recorres Rohan...

su influencia crece.

Los orcos se multiplican.

Los árboles caen.

Las máquinas trabajan.

Y la tierra comienza a cambiar.

Isengard ya no parece una fortaleza.

Parece una fábrica de guerra.

Y eso es precisamente lo aterrador.

No es una criatura.

No es un monstruo.

Es una voluntad.

Una mente.

Una persona que decidió que el mundo debía pertenecer a quienes fueran suficientemente fuertes para dominarlo.

Pero incluso entonces...

todavía existían quienes podían detenerlo.

Los Rohirrim.

Los Ents.

Los pueblos libres.

Y tú.

Porque una fortaleza puede parecer invencible desde lejos.

Pero toda fortaleza depende de aquello que la sostiene.

Y cuando aquello que la sostiene comienza a romperse...

hasta las torres más altas pueden caer.

Así que cuando mires Orthanc...

recuerda esto.

El poder no siempre llega gritando.

A veces llega vestido de sabiduría.

Habla con calma.

Promete soluciones.

Y espera.

Hasta que alguien confía demasiado.""",
        {"stability": 0.45, "similarity_boost": 0.8, "style": 0.5, "use_speaker_boost": True},
    ),
    (
        "los_ents_y_la_ira_de_los_bosques",
        """Viajero...

Te voy a pedir que imagines algo.

Imagina que llevas miles de años observando el mundo.

Has visto nacer bosques.

Has visto desaparecer reinos.

Has visto pasar generaciones enteras de hombres.

Y un día...

alguien comienza a destruir tu hogar.

Eso es lo que ocurrió con los Ents.

Durante mucho tiempo fueron pacientes.

Muy pacientes.

Los Ents no viven como los hombres.

No piensan como nosotros.

Para ellos, una decisión puede tardar días.

Meses.

Años.

Pero Saruman cometió un error.

Pensó que la paciencia significaba debilidad.

Los árboles comenzaron a caer.

Los bosques fueron utilizados para alimentar las máquinas de guerra.

Y poco a poco...

la paciencia terminó.

Entonces ocurrió algo que parecía imposible.

El bosque comenzó a caminar.

Los Ents marcharon.

No como un ejército de hombres.

Sino como algo mucho más antiguo.

Lento.

Pesado.

Imparable.

Y cuando llegaron a Isengard...

la torre que parecía intocable dejó de parecerlo.

Las máquinas fueron destruidas.

Los muros comenzaron a caer.

Y Saruman comprendió demasiado tarde que había provocado la ira de algo que llevaba miles de años esperando.

Quizá esa sea una de las historias más impresionantes que encontrarás durante tu viaje.

Porque demuestra que no todo poder necesita una espada.

A veces basta con paciencia.

Y raíces.

Así que cuando atravieses un bosque...

camina con respeto.

No sabes qué historia puede estar observándote.""",
        {"stability": 0.35, "similarity_boost": 0.8, "style": 0.65, "use_speaker_boost": True},
    ),
    (
        "helms_deep_la_noche_de_la_resistencia",
        """Viajero...

Esta noche no hay camino de regreso.

Delante de ti está Helm's Deep.

Detrás...

Rohan.

Las fuerzas enemigas se acercan.

Miles.

Quizá más de los que puedas contar.

Y dentro de la fortaleza...

hay hombres que saben que quizá no sobrevivirán.

Pero se quedan.

Porque detrás de ellos están sus familias.

Su hogar.

Su pueblo.

La fortaleza parece fuerte.

Sus muros son altos.

Sus puertas resistentes.

Pero ningún muro puede garantizar una victoria.

Los enemigos atacan.

Las flechas llenan el cielo.

Los defensores responden.

Cada minuto parece más largo que el anterior.

Y mientras la batalla continúa...

la esperanza comienza a disminuir.

Eso es lo que hace diferente a Helm's Deep.

No es una batalla de héroes invencibles.

Es una batalla de personas aterradas.

Personas cansadas.

Personas que saben que podrían morir...

y aun así mantienen su posición.

Porque algunas noches...

resistir ya es una victoria.

Y cuando finalmente parece que todo está perdido...

llega ayuda.

No porque la batalla fuera fácil.

Sino porque alguien decidió que todavía valía la pena luchar.

Así que recuerda esta noche, viajero.

Cuando alguna vez pienses que una situación es imposible...

recuerda Helm's Deep.

Los defensores no sabían cómo terminaría.

Solo sabían que todavía estaban allí.

Y mientras quedara uno de ellos de pie...

la batalla continuaría.""",
        {"stability": 0.3, "similarity_boost": 0.8, "style": 0.75, "use_speaker_boost": True},
    ),
    (
        "gondor_el_reino_que_esperaba",
        """Viajero...

Hay lugares que parecen estar esperando algo.

Gondor es uno de ellos.

Durante generaciones, sus hombres observaron hacia el este.

Hacia Mordor.

Esperando que la sombra regresara.

Las murallas permanecían.

Las fortalezas permanecían.

Pero el reino había cambiado.

Ya no era el Gondor de los grandes días.

Era un reino cansado.

Herido.

Sosteniéndose con aquello que todavía quedaba.

Y entonces tú llegaste.

El camino te llevó hacia el sur.

A través de tierras donde cada piedra parecía recordar una batalla.

Y poco a poco comprendiste que Gondor no estaba luchando solamente contra Mordor.

También estaba luchando contra el tiempo.

Contra el cansancio.

Contra el miedo.

Porque un reino puede resistir durante siglos...

pero sus habitantes siguen siendo personas.

Tienen miedo.

Pierden amigos.

Pierden familiares.

Y aun así...

siguen defendiendo las murallas.

Cuando finalmente contemplas Minas Tirith...

comprendes por qué.

No es solamente una ciudad.

Es el último gran refugio.

Un símbolo.

Una promesa de que la oscuridad todavía no ha ganado.

Y mientras tú recorres sus calles...

la guerra continúa acercándose.

Cada vez más.

Hasta que ya no existe distancia suficiente.

Entonces Gondor debe elegir.

Resistir.

Y luchar.

Porque a veces la esperanza no parece una luz brillante.

A veces parece una pequeña llama protegida entre las manos.

Y eso es Gondor.

Una llama que se niega a apagarse.""",
        {"stability": 0.5, "similarity_boost": 0.8, "style": 0.5, "use_speaker_boost": True},
    ),
    (
        "la_batalla_de_los_campos_del_pelennor",
        """Viajero...

Si alguna vez escuchas el sonido de miles de caballos...

no olvides lo que significa.

El Pelennor está a punto de convertirse en un campo de batalla.

Minas Tirith está sitiada.

Las fuerzas de Mordor han llegado.

Y por un momento...

parece que todo está perdido.

Pero entonces...

el horizonte cambia.

Los Rohirrim llegan.

No vienen lentamente.

Llegan como una tormenta.

Caballos.

Estandartes.

Guerreros.

Espadas.

Y esperanza.

Durante un instante...

la oscuridad parece retroceder.

Pero las grandes batallas nunca son sencillas.

La victoria tiene un precio.

Muchos caerán.

Hombres.

Jinetes.

Amigos.

Personas que nunca volverán a casa.

Y mientras la batalla continúa...

el mundo parece contener la respiración.

Tú estás allí.

En medio de la historia.

No viendo una leyenda desde lejos.

Viviéndola.

Porque eso es lo que hace especial a LOTRO.

Las grandes historias no ocurren solamente alrededor de ti.

Tú puedes caminar dentro de ellas.

Puedes ver el campo.

Escuchar los gritos.

Ver los estandartes.

Y comprender que detrás de cada soldado existe una vida.

Una historia.

Una familia.

Por eso la victoria nunca es completamente feliz.

Cuando termina una batalla...

alguien siempre falta.

Y quizá esa sea la parte que las canciones olvidan.

Las canciones hablan de héroes.

De reyes.

De victorias.

Pero tú recuerdas los rostros.

Los nombres.

Las pérdidas.

Y entiendes que la gloria siempre tiene un precio.""",
        {"stability": 0.32, "similarity_boost": 0.8, "style": 0.7, "use_speaker_boost": True},
    ),
    (
        "el_camino_hacia_mordor",
        """Viajero...

Has recorrido muchos caminos.

Pero ninguno como este.

Mordor.

El nombre todavía provoca miedo.

Pero ahora estás aquí.

Y lo extraño es que no encuentras solamente un lugar de destrucción.

Encuentras un lugar lleno de historias.

Soldados.

Ruinas.

Campos quemados.

Fortalezas.

Personas intentando sobrevivir.

Porque cuando termina una gran batalla...

el mundo no vuelve inmediatamente a la normalidad.

Quedan heridas.

Quedan enemigos.

Quedan secretos.

Y quedan personas que todavía necesitan ayuda.

Ese es uno de los grandes cambios de tu viaje.

Al principio luchabas para sobrevivir.

Después luchaste para proteger.

Ahora...

luchas para reconstruir.

Mordor te obliga a mirar aquello que queda después de la guerra.

Y quizá eso sea más difícil que enfrentarse a un enemigo.

Porque reconstruir requiere paciencia.

Requiere esperanza.

Requiere creer que algo puede crecer incluso donde todo parece muerto.

Mientras avanzas...

recuerda todo lo que has dejado atrás.

La Comarca.

Eriador.

Moria.

Lothlórien.

Mirkwood.

Rohan.

Gondor.

Cada lugar forma parte de tu historia.

Y ahora...

tu camino te ha llevado hasta aquí.

Pero Mordor no es el final.

Es una prueba.

Una última oportunidad para demostrar que el viaje te ha cambiado.

Porque ya no eres aquel viajero que comenzó sin saber qué había delante.

Ahora conoces la oscuridad.

Y aun así...

sigues caminando.

Eso es lo que importa.""",
        {"stability": 0.42, "similarity_boost": 0.8, "style": 0.58, "use_speaker_boost": True},
    ),
    (
        "el_mundo_despues_de_sauron",
        """Hola, viajero...

Hay algo que nadie te cuenta sobre las grandes victorias.

Cuando el enemigo cae...

el mundo no se arregla inmediatamente.

Los campos siguen destruidos.

Las ciudades necesitan reconstruirse.

Los muertos necesitan ser recordados.

Y quienes sobrevivieron...

deben aprender a vivir nuevamente.

Después de Sauron...

la Tierra Media entra en una nueva etapa.

Ya no se trata solamente de derrotar al enemigo.

Ahora hay que reparar aquello que quedó atrás.

Y tú formas parte de eso.

Quizá nunca pensaste que una de tus grandes misiones sería ayudar a reconstruir.

Pero así son las historias.

Comienzan con espadas...

y algunas terminan con martillos, herramientas y manos trabajando.

Los pueblos vuelven a abrir sus puertas.

Los caminos vuelven a llenarse.

Las personas empiezan a hablar del futuro.

Y poco a poco...

la Tierra Media vuelve a respirar.

Pero hay algo que debes recordar.

La paz no significa olvidar.

Los que sobrevivieron llevan las cicatrices de la guerra.

Algunos perdieron amigos.

Otros perdieron hogares.

Otros simplemente...

cambiaron.

Por eso la reconstrucción también es una forma de memoria.

Cada casa levantada.

Cada camino reparado.

Cada árbol plantado.

Es una forma de decir: Seguimos aquí.

Y quizá ese sea el verdadero significado de la esperanza.

No creer que nunca volverá la oscuridad.

Sino saber que, si vuelve...

habrá alguien dispuesto a encender otra vez la luz.""",
        {"stability": 0.45, "similarity_boost": 0.8, "style": 0.5, "use_speaker_boost": True},
    ),
    (
        "el_legado_de_durin",
        """Viajero...

Si creías que las historias de los enanos terminaban con la recuperación de Moria...

estabas equivocado.

Porque algunas historias comienzan mucho después de la victoria.

Durin.

Su nombre pertenece a las raíces más profundas de la historia de los enanos.

Generaciones enteras han vivido bajo la sombra de ese nombre.

Y cuando el destino vuelve a llamar...

los descendientes de Durin deben enfrentarse a algo más que enemigos.

Deben enfrentarse a su propio pasado.

Gundabad.

Una tierra antigua.

Un lugar ligado a la historia de los enanos.

Un lugar donde los conflictos del pasado todavía tienen consecuencias.

Cuando llegas allí...

comprendes que recuperar un hogar no significa simplemente conquistar una fortaleza.

Significa recuperar una identidad.

Los enanos han perdido demasiado.

Reinos.

Familias.

Ciudades.

Generaciones.

Pero continúan.

Y esa palabra...

continúan...

es quizás la más importante de toda su historia.

Porque cada vez que parece que han perdido todo...

alguien vuelve a levantar el martillo.

A encender la forja.

A construir una puerta.

A contar una historia.

A recordar un nombre.

Y mientras alguien recuerde...

un pueblo no está muerto.

Así que cuando recorras las tierras de los enanos...

mira sus montañas.

Mira sus fortalezas.

Escucha sus canciones.

Porque detrás de cada piedra existe una historia mucho más antigua que tú.

Y quizá...

cuando llegue el momento...

tú también formes parte de ella.""",
        {"stability": 0.4, "similarity_boost": 0.8, "style": 0.55, "use_speaker_boost": True},
    ),
    (
        "y_ahora_viajero_que_haras_con_tu_historia",
        """Viajero...

Te he contado historias de reinos.

De guerras.

De héroes.

De enemigos.

De personas que cayeron.

De personas que resistieron.

Pero ahora quiero hablarte de ti.

Porque después de todo este tiempo...

hay algo que quizá hayas olvidado.

Tú también eres parte de esta historia.

Cuando comenzaste...

no sabías lo que encontrarías.

Quizá solo querías explorar.

Quizá buscabas aventuras.

Quizá simplemente querías descubrir qué había detrás de aquella montaña.

Pero después llegaron las guerras.

Angmar.

Moria.

Mirkwood.

Rohan.

Gondor.

Mordor.

Y cada lugar dejó algo en ti.

Aprendiste que los grandes héroes también tienen miedo.

Que los reinos pueden caer.

Que los enemigos pueden parecer invencibles.

Que la victoria puede tener un precio.

Y también aprendiste algo más importante.

Que siempre existe alguien dispuesto a levantarse.

Ahora mira hacia atrás.

Piensa en el primer camino que recorriste.

En el primer enemigo que derrotaste.

En la primera ciudad que descubriste.

En la primera vez que sentiste que no sabías qué hacer.

Y mira dónde estás ahora.

Quizá todavía tengas enemigos delante.

Quizá todavía existan historias que no conoces.

Quizá todavía haya lugares que nunca has visto.

Pero ya no eres el mismo.

Has cambiado.

Y eso es lo que significa viajar.

No solamente avanzar por el mapa.

Sino convertirte poco a poco en alguien diferente.

Así que no tengas prisa por llegar al final.

Disfruta el camino.

Escucha las historias.

Mira los paisajes.

Ayuda a quien puedas.

Detente cuando una vista merezca ser contemplada.

Porque algún día...

cuando mires atrás...

descubrirás que no recordarás cada recompensa.

No recordarás cada enemigo.

No recordarás cada camino.

Recordarás momentos.

Personas.

Lugares.

Batallas.

Risas.

Derrotas.

Y pequeñas victorias que en aquel momento parecían insignificantes.

Eso será tu historia.

No la historia de Aragorn.

No la historia de Gandalf.

No la historia de Frodo.

La tuya.

Así que levanta tu arma, viajero.

Ensilla tu caballo.

Mira el camino que tienes delante.

Todavía queda mucho por descubrir.

Y mientras exista un camino...

todavía existe una historia.

La tuya.""",
        {"stability": 0.3, "similarity_boost": 0.8, "style": 0.7, "use_speaker_boost": True},
    ),
]

LEAD_IN_S = 0.4
TAIL_S = 0.8
FADE_MS = 12
TARGET_PEAK = 0.9


def _split_into_segments(text: str) -> list[tuple[str, float]]:
    """Si el texto trae marcas [PAUSA]/[PAUSA LARGA] explicitas, se respetan
    tal cual. Si no trae ninguna, se separa automaticamente por oracion
    (punto seguido) con una pausa corta entre cada una -- para que alcance
    con pegar el texto plano del usuario sin marcarlo a mano."""
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

    # mp3 (pedido explicito del usuario, 2026-09-05: "pasa los audios a mp3
    # para bajar los mb") en vez de wav sin comprimir -- ~89% mas chico,
    # sin perdida audible para narracion hablada (ver tools/convert_to_mp3.py).
    out_path = OUT_DIR / f"{name}.mp3"
    sf.write(out_path, full, sr_ref, format="MP3")

    for frag in frag_dir.glob("frag_*.mp3"):
        frag.unlink(missing_ok=True)
    frag_dir.rmdir()

    duration = len(full) / sr_ref
    print(f"[{name}] Listo: {out_path} ({duration:.1f}s, {sr_ref}Hz)")


def main() -> None:
    if not CLIPS:
        raise SystemExit("CLIPS esta vacio -- pega los textos del usuario en tools/build_ambient_clips.py primero.")

    config = load_config(APP_DIR / "config.yaml")
    base_voice_cfg = config["voices"].get(VOICE_NAME)
    if not base_voice_cfg:
        raise SystemExit(f"config.yaml no tiene una voz '{VOICE_NAME}'.")

    engine = base_voice_cfg.get("engine", "edge")
    synthesize = ENGINE_FUNCS[engine]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    skipped = 0
    for name, text, settings_override in CLIPS:
        out_path = OUT_DIR / f"{name}.mp3"
        if out_path.exists():
            # Ya generado en una corrida anterior (2026-09-05, pedido
            # explicito del usuario: "las que faltan", varias corridas
            # sucesivas por tope de cuota mensual de ElevenLabs) -- no
            # volver a gastar cuota regenerando algo que ya existe.
            skipped += 1
            continue
        voice_cfg = dict(base_voice_cfg)
        if settings_override:
            voice_cfg["voice_settings"] = settings_override
        try:
            build_clip(name, text, voice_cfg, synthesize)
        except Exception as exc:
            # Cuota de ElevenLabs agotada a mitad de lote (esperable con
            # varios lotes grandes en la misma cuenta) -- avisar con
            # claridad en vez de que la excepcion se vea como un crash, y
            # dejar lo ya generado intacto para la proxima corrida. El .wav
            # final de este clip nunca se escribe si build_clip() revienta
            # a mitad de un fragmento, asi que la proxima corrida lo
            # reintenta solo (no queda a medio generar).
            frag_dir = TMP_DIR / name
            if frag_dir.exists():
                for frag in frag_dir.glob("*.mp3"):
                    frag.unlink(missing_ok=True)
                frag_dir.rmdir()
            print(f"[Ambient] DETENIDO en '{name}': {exc}")
            print(f"[Ambient] Saltadas (ya existian de antes): {skipped}.")
            return

    if skipped:
        print(f"[Ambient] {skipped} clip(s) ya existian, no se regeneraron.")
    if TMP_DIR.exists() and not any(TMP_DIR.iterdir()):
        TMP_DIR.rmdir()


if __name__ == "__main__":
    main()
