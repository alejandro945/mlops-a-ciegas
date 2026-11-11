# Guion · MLOps a ciegas · Tech Day Cali 2026

Solo lo que dices. Cada lámina es una idea y **no tiene clics**: el control solo avanza. *(pausa)* es silencio · lo demás en cursiva es para ti. Lo que va entre comillas no se memoriza palabra por palabra, salvo la apertura, las cifras y el cierre. Las notas del deck (tecla **N**, o la ventana del presentador con **P**) salen de este archivo. Fuentes y datos de respaldo: `NOTAS-de-apoyo.md` (sección *Tech Day Cali*). El diseño de la charla: `talk/private/SPEC-techday-cali.md`.

**Unos 24 min** de contenido para 500 personas: estudiantes, desarrolladores, gente de datos. Nadie tiene que saber qué es MLOps, IoT ni AWS. Reloj al entrar a cada parte: I · El oído 0:00 · II · El viaje 7:00 · III · Una noche en la planta 13:00 · Cierre 21:00.

---

## 1 · MLOps a ciegas
<!-- id: portada -->
**0:10**

*(En pantalla mientras te presentan. Cuando te den la palabra, pasa a la 2 y arranca sin saludar.)*

---

## 2 · "Esta va a fallar"
<!-- id: mecanico -->
**0:50** · *despacio, mirando a la sala*

"En cada planta industrial hay alguien así." *(pausa)* "No mira un dashboard. Pone la mano sobre la bomba, escucha unos segundos… y dice: 'esta va a fallar'. Y casi nunca se equivoca."

"Y lo que está en juego no es poco. Aquí en el Valle la caña se cosecha casi todo el año, y la caña cortada no espera: si el ingenio para, se pierde. En las industrias más grandes del mundo, los paros que nadie vio venir se llevan el 11 % de los ingresos."

---

## 3 · ¿Cuál está fallando?
<!-- id: espectros -->
**0:30**

"Esta es la 'foto' del sonido de dos bombas. Una está sana y la otra está empezando a fallar." *(pausa)* "¿Cuál es?"

*(Deja dos segundos.)* "Él lo sabría. Ustedes y yo, no. Guarden la pregunta: la respuesta llega más tarde, en la noche en que lo probamos de verdad."

---

## 4 · Sobre mí
<!-- id: quien -->
**0:30**

"Buenos días, Cali. Soy Alejandro Varela, Senior Cloud Engineer en EPAM. Llevo años construyendo cosas que corren lejos de la nube, en equipos de campo, donde la red no siempre llega y nadie está mirando."

"Esta charla es sobre lo que aprendí tratando de copiar ese oído."

---

## 5 · Una persona, mil bombas
<!-- id: mil -->
**0:35**

"El problema es que él es uno solo." *(señala el punto)* "Y las bombas son mil." *(pausa)* "Y un día se pensiona, y su oído se va con él."

"Entonces la pregunta de esta charla es simple: ¿cómo se copia un oído? Y, sobre todo, ¿cómo se sabe si la copia sigue oyendo bien?"

---

## 6 · Tu cerebro ignora lo normal
<!-- id: cerebro -->
**0:50**

"Antes de copiarlo, veamos cómo funciona. Su cerebro, ahora mismo, gasta unos 20 vatios: lo de un bombillo." *(pausa)* "Y no procesa todo."

"Pregunta: ¿alguien estaba sintiendo la ropa que tiene puesta… antes de que yo la nombrara?" *(risas)* "Su cerebro la ignoró, porque es lo de siempre. Reacciona a lo que no esperaba. Así ahorra energía."

"El oído del mecánico hace lo mismo: ignora el ruido de siempre y nota lo diferente. Eso es exactamente lo que vamos a copiar."

---

## 7 · No toda IA conversa
<!-- id: noesgenai -->
**0:50**

"Un momento, porque hoy, cuando decimos 'inteligencia artificial', todos pensamos en ChatGPT." *(pausa)* "Esta charla no es de eso."

"La IA que conversa tiene miles de millones de parámetros y vive en centros de datos gigantes. La IA que trabaja en una planta casi nunca conversa: es **machine learning tradicional**. Modelos pequeños que hacen una sola cosa: clasificar, predecir o detectar algo raro."

"El oído que vamos a construir pesa 464 kilobytes, menos que una foto de su celular, y decide en milisegundos sin internet. Pequeño, sí. Pero si se equivoca, una bomba se daña y nadie se entera."

*Si preguntan: MLOps es llevar un modelo a producción y operarlo como se opera cualquier software: versiones, despliegues, monitoreo y rollback. Aplica igual a un LLM; cambia lo que se mide, no el ciclo.*

---

## 8 · Así se copia un oído
<!-- id: oido -->
**0:50**

"¿Cómo se entrena? Le damos solo sonido de bombas sanas. Nunca le mostramos una falla." *(pausa)* "Aprende cómo suena lo normal."

"Después, cada pocos segundos, intenta predecir el sonido que está oyendo. Si lo logra, todo bien. Si no puede, es porque algo suena diferente, y sube este número: el puntaje de rareza. Cuando pasa la línea, alerta."

"Igual que su cerebro con la ropa: no reacciona a lo normal, reacciona a lo diferente."

---

## 9 · "¿Y por qué no mandamos todo a la nube?"
<!-- id: nube -->
**0:55**

"Alguno estará pensando: '¿y por qué no mandamos el audio a la nube y que allá lo analice un modelo gigante?'" *(pausa)*

"En octubre del año pasado se cayó una región de AWS en Estados Unidos. A muchos se les cayó la app del banco, el juego, Alexa." *(señala el meme)* "Y unas camas inteligentes de dos mil dólares, que controlaban la temperatura y la inclinación desde la nube, dejaron de pensar… con sus dueños encima."

"Y aunque la nube no se cayera: una sola bomba produce 115 megas de audio por hora. Lo que de verdad necesitamos saber cabe en una línea de texto."

---

## 10 · El péndulo vuelve
<!-- id: pendulo -->
**0:50**

"Esto no es una moda: es un péndulo. Primero todo se calculaba en un computador central. Después llegó el PC y todo pasó a tu escritorio. Después la nube, y todo volvió al centro." *(pausa)* "Ahora la decisión regresa a donde nace el dato."

"Ya lo usan todos los días: Face ID reconoce su cara sin que la foto salga del teléfono. Más de la mitad de los PC que se venden este año traen un chip de IA. Y hoy cualquier estudiante puede comprar una placa Arduino que detecta sonidos raros sin internet."

---

## 11 · Aquí la red no siempre llega
<!-- id: colombia -->
**0:45**

"Y en Colombia esto no es teoría. Cuatro de cada diez hogares rurales todavía no tienen internet."

"Aquí en el Valle, Cenicaña lleva años con una red de sensores que cubre casi toda la zona cañera. Y la conectividad para el campo mejora: Wi-Fi HaLow llega a kilómetros con una batería de botón." *(pausa)* "Pero ojo: una red mejor no resuelve el problema. Solo significa más oídos, más lejos, decidiendo solos."

---

## 12 · Hábito 1 · Que quepa en la maleta
<!-- id: maleta -->
**0:35**

"El primer hábito es que el oído quepa en el equipo. Como hacer la maleta para un viaje en avión: lo mismo, en menos espacio."

"De 464 a 127 kilobytes. Y en el 98 % de los casos decide exactamente lo mismo que el original."

---

## 13 · Y ahí nos quedamos a ciegas
<!-- id: ciegas -->
**0:55** · *el punto de giro: ve despacio*

"Y aquí está el problema de esta charla." *(pausa)* "Cuando el modelo vive en la nube, lo vemos todo: cada predicción, cada error. Cuando vive en mil bombas, lejos… dejamos de verlo."

"Y lo peor: el tablero dice CPU bien, memoria bien, cero errores. Todo verde. Mientras tanto, una bomba falla y nadie la oye." *(pausa)* "El software puede estar perfecto y el oído, equivocado. Eso es hacer MLOps a ciegas."

---

## 14 · Lo montamos de verdad
<!-- id: aws -->
**0:40**

"Para no quedarme en la teoría, lo construí de verdad en AWS. Cinco bombas, cada una con el mismo agente que se instala en un equipo industrial, y audio real de bombas que grabó Hitachi."

"No les voy a explicar cada caja. Lo importante es esto: el modelo se entrena en la nube, vive en la bomba, y lo único que vuelve es una línea por decisión. Y abajo, un juez." *(señala Step Functions)* "Ya llegamos a él."

"Lo corrimos de noche, a las 7:58 p.m. Les cuento qué pasó."

---

## 15 · 7:58 p.m. · La bomba 3 empieza a fallar
<!-- id: acto1 -->
**0:50**

"Cada punto es un clip de diez segundos que la bomba 3 escuchó y decidió. Verde, verde, verde… y a las 7:58 y 36 segundos la ponemos a sonar como una bomba que falla." *(pausa)* "En ese mismo clip, alerta."

*(Señala los espectrogramas.)* "¿Se acuerdan de la pregunta? Era la de la derecha. Aquí está lo que el oído notó: esta zona, que en la bomba sana no existe. Lo notó como lo habría notado el mecánico."

---

## 16 · Hábito 2 · Lo urgente ya, lo pesado después
<!-- id: lotes -->
**0:45**

"Segundo hábito. Funciona como WhatsApp: el mensaje sale al instante; el video se sube cuando hay wifi."

"Lo urgente, la decisión, sale ya: una línea. Lo pesado, el audio, no se manda todo: solo el que importa. El de cada alerta, el de los casos dudosos y una muestra de lo normal. Se sube por lotes, cuando hay buena red, y es con ese audio que se entrena la siguiente versión. Y si no hay red, todo espera en el disco."

---

## 17 · 7:59 p.m. · Se fue la red
<!-- id: acto2 -->
**0:45**

"A las 7:59 le quitamos la red a la bomba 3." *(señala)* "Miren: la 3 se calla, y las otras cuatro siguen como si nada."

"45 segundos después vuelve la red… y llegan todos sus reportes, de golpe, algunos con 50 segundos de retraso." *(pausa)* "Cero perdidos. La bomba no se enteró de que estaba sola."

---

## 18 · Hábito 3 · Escuchar al que escucha
<!-- id: senales -->
**0:55**

"Tercer hábito, el más importante: no basta con escuchar a la bomba. Hay que escuchar al que escucha. Tres preguntas."

"¿Lo que entra se parece a lo que aprendió? ¿Lo que decide cambió? ¿Es la versión que mandamos?"

"Esa misma noche, a la bomba 5 le cambiamos la velocidad. El software, perfecto: cero errores. Pero empezó a dar alertas, y esta línea" *(señala la entrada)* "nos dijo por qué: lo que entraba ya no se parecía a lo que aprendió. No era la bomba. Era que el mundo cambió y el oído todavía no lo sabía."

---

## 19 · "Teníamos más audio"
<!-- id: masaudio -->
**0:30** · *lámina casi vacía: es para la pausa*

"Entonces, para la siguiente versión, juntamos más audio. Más datos, mejor modelo, ¿cierto?" *(pausa)* "Entrenamos un oído mejor…"

*(Pausa larga. Mira a la sala.)* "¿Qué podría salir mal?"

---

## 20 · El oído "mejorado" estaba sordo
<!-- id: sordo -->
**1:00**

"La versión 2 no reemplazó a la 1 de una vez. Entró en sombra, en una sola bomba: la 1 sigue decidiendo y la 2 solo dice qué habría hecho."

"Y ponemos a fallar la bomba 1." *(señala las dos filas)* "La versión 1: alerta, alerta, alerta, las 40 veces. La versión 2: normal, normal… 24 de 40 fallas, sin oírlas."

"¿Qué pasó? El audio extra traía una semana en que una bomba ya venía fallando, y nadie lo revisó. El oído aprendió que fallar es lo normal." *(pausa)* "No es un bug de código. Es un bug de datos."

---

## 21 · Hábito 4 · Nadie decide sin un juez
<!-- id: juez -->
**1:00** · *el clímax*

"Y aquí está el juez. Es un flujo automático: pone la versión nueva en sombra, espera, compara las dos sobre los mismos sonidos… y decide."

"Esta vez: no pasa. La versión 2 nunca decidió nada. Ninguna otra bomba la recibió."

*(Dilo mirando a la sala, despacio.)* "La plataforma sabe devolver una instalación que falló. No sabe que un modelo se volvió sordo. Ese juez lo tiene que poner uno."

"Y si algo se cuela, hay una red de seguridad: una alarma que devuelve la versión buena sola. En la primera prueba lo hizo en 88 segundos."

---

## 22 · Cómo se arregla un oído sordo
<!-- id: arreglo -->
**0:45**

"¿Y cómo se arregla? No con más datos: con los datos correctos."

"El audio que importa ya está en la nube, porque lo subimos por lotes. Mantenimiento confirma qué era falla de verdad. Se limpian los datos, se entrena la versión 3… y pasa por el mismo juez." *(pausa)* "Así se cierra el ciclo."

---

## 23 · Tres ideas para llevarse
<!-- id: tres -->
**0:50**

"Si se llevan tres cosas:"

"Uno: decidan donde nace el dato, y manden solo lo diferente."

"Dos: ninguna versión nueva decide sin un juez."

"Tres: escuchen al que escucha. No basta con que el equipo esté prendido; hay que mirar lo que el modelo decide."

---

## 24 · ¿Quién está fallando?
<!-- id: final -->
**0:45** · *el cierre: memorízalo*

"Empezamos con una pregunta: ¿esta bomba está fallando?" *(pausa)* "Después de esa noche aprendí que la pregunta que importa es otra."

*(Pausa larga.)* "¿El que escucha está fallando?"

"Cuando la IA se va lejos de la nube, alguien tiene que seguir escuchando al que escucha. Si no, estamos haciendo MLOps a ciegas."

---

## 25 · Por dónde empezar
<!-- id: empezar -->
**0:20**

"Si quieren probarlo: una placa Arduino o una Raspberry Pi, Edge Impulse para entrenar sin escribir mucho código, y el audio de Hitachi, que es abierto. Y todo lo que vieron, el código y la infraestructura, está en este repo."

---

## 26 · ¡Gracias!
<!-- id: gracias -->
**0:10**

"Muchas gracias, Cali." *(Quédate en esta lámina durante las preguntas.)*

---

# Anexos (para preguntas)

## A1 · La arquitectura en AWS
<!-- id: a-aws -->
*Si preguntan "¿y en AWS cómo es?". Greengrass lleva el modelo y la configuración a cada bomba; IoT Core recibe una línea por decisión; CloudWatch la convierte en métricas; Step Functions es el juez; la alarma y Lambda son la red de seguridad; stream manager sube el audio que importa a S3.*

## A2 · El juez, paso a paso
<!-- id: a-juez -->
*Despliega el candidato en sombra en el ring 0 (una bomba) · espera (en la demo, 2 min; en producción, días) · mide con Logs Insights cuántas veces el candidato no oyó lo que el activo sí, y cuántas alertó solo · si pasa, lo promueve al ring 0, al ring 1 y lo guarda como última versión buena; si no, devuelve la bomba a la versión activa y avisa por SNS. No necesita saber la verdad: compara dos modelos sobre el mismo audio. Límite: si durante la espera todo es normal, coinciden; por eso en producción la espera es larga y se cruza con las órdenes de mantenimiento.*

## A3 · La red de seguridad: 88 segundos
<!-- id: a-88 -->
*Primera prueba (Bogotá, 18 de octubre): la v2 sí llegó a decidir en la bomba 1, no oyó la falla, la alarma de fallas no oídas pasó de OK a ALARM, la Lambda desplegó la 1.0.0 y la bomba volvió a alertar 88 s después de la falla. El ring 1 nunca recibió la v2.*

## A4 · ¿Por qué ML tradicional y no un LLM?
<!-- id: a-genai -->
*Un autoencoder de 464 KB decide en milisegundos en una CPU modesta, sin red, y se entrena solo con sonido normal. Un LLM pequeño pesa del orden de gigabytes. El ciclo de MLOps es el mismo para los dos: versionar, desplegar por anillos, observar lo que decide y volver atrás; lo que cambia es la señal que se mide.*

## A5 · Fuentes
<!-- id: a-fuentes -->
*Las de `NOTAS-de-apoyo.md`, sección Tech Day Cali.*
