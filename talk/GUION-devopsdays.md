# Guion · MLOps a ciegas · DevOpsDays Bogotá 2026

Solo lo que dices. **[CLIC]** avanza la lámina · *(pausa)* es silencio · lo demás en cursiva es para ti. Lo que va entre comillas no se memoriza palabra por palabra, salvo la apertura, las cifras y el cierre. Cómo estudiarlo: `talk/private/ESTUDIO.md` (no se sube al repo). Fuentes y datos de respaldo: `NOTAS-de-apoyo.md`. Las notas del deck (tecla **N**) salen de este archivo.

**21:48** de contenido para un espacio de 25 min + 5 de preguntas. Reloj al entrar a cada divisor: 3:05 · 5:48 · 9:03 · 15:43.

---

## 1 · MLOps a ciegas
<!-- id: portada -->
**0:10** · sin clics

*(En pantalla mientras te presentan. Cuando te den la palabra, pasa a la 2.)*

---

## 2 · Sobre mí
<!-- id: quien -->
**0:25** · sin clics

"Buenos días. Soy Alejandro Varela, Senior Cloud Engineer en EPAM. Diseño cómo llegan y se gobiernan modelos de IA en equipos de campo, donde no hay nadie cerca."

"Lo que van a ver hoy no salió de un examen: lo monté, lo rompí y lo arreglé esta misma semana."

"Pero no vine a hablar de mí. Vine a ponerles un audio."

---

## 3 · ¿Esta bomba está fallando?
<!-- id: suena -->
**1:10** · 1 clic

"Esta es la bomba A." *(▶ A, cinco segundos)* "Y esta es la bomba B." *(▶ B, cinco segundos)*

"¿Alguna de las dos está fallando?"

**[CLIC]** "Levanten la mano. ¿La A?" *(cuenta en voz alta)* "¿La B?" *(cuenta)* "¿Las dos?" *(cuenta)* "Interesante. No les voy a decir todavía."

"Los sonidos son reales: los grabó Hitachi en una planta. Lo que me inventé es la empresa: un acueducto con estaciones de bombeo en veredas, donde la señal va y viene y no hay nadie cerca. En cada estación, un equipito escucha las bombas y un modelo avisa cuando una empieza a sonar raro."

"Lo que ustedes acaban de hacer es justo lo que hace ese modelo: oír y decidir. La diferencia es que ustedes estaban aquí. Desde la nube, nadie oyó nada." *(pausa)*

"Por eso esta charla se llama «MLOps a ciegas»: cómo se maneja un modelo que corre donde uno no lo ve. Cómo le llega una versión nueva, cómo se devuelve si sale mala y cómo nos cuenta lo que decide. Sin que el audio salga nunca de la estación."

---

## 4 · La IA ya corre en el dispositivo
<!-- id: cien -->
**0:25** · 2 clics

"¿Y a mí qué me importa un modelo en una bomba? Que los modelos se están bajando de la nube a los dispositivos. Un ejemplo de Gartner: en 2024, de cada cien PC nuevos, dieciséis traían un chip para IA."

**[CLIC]** "En 2025, treinta y uno."

**[CLIC]** "Y para este año, cincuenta y cinco. Más de la mitad. Y lo mismo pasa con el celular, los carros y los equipos de una planta."

---

## 5 · Por qué el modelo baja al dispositivo
<!-- id: memes -->
**0:55** · 2 clics · *deja que se rían antes de seguir*

"¿Y por qué se baja? Se los explico como explicamos todo los ingenieros: con memes."

"El carro autónomo, frente a un cono: «dame un segundo, que le pregunto al modelo en la nube»." *(risas)* "Cuando hay que frenar ya, la ida y vuelta no alcanza."

**[CLIC]** "El técnico a las tres de la mañana: «¿cómo cambio este rodamiento?». Y el asistente: «Sin conexión, intente más tarde»." *(risas)* "En una vereda sin señal pasa exactamente lo mismo."

**[CLIC]** "Y mi favorito: ustedes desbloqueando el teléfono, y el teléfono: «un momentico, le mando tu cara al modelo en la nube»." *(risas)* "Face ID no funciona así. El modelo corre en el teléfono, y tu cara queda cifrada en un chip aparte, el Secure Enclave. Nunca sale. Lo único que sale es un sí o un no."

"Y si te dejas crecer la barba, Face ID se adapta solo, ahí mismo en el teléfono: los datos cambiaron y el modelo se ajustó sin ir a la nube. Guárdenme esa idea."

"Ahora la bomba: un micrófono son ciento quince megas por hora. Por bomba. Por la red de una vereda. No cabe… y no tiene por qué salir de ahí."

---

## 6 · 01 · El problema
<!-- id: div1 -->
**0:08** · *reloj: 3:05*

"Vamos en cuatro partes: el problema, el patrón, seis pasos y lo que pasó cuando lo corrí en AWS. Arranquemos por el problema."

---

## 7 · MLOps en la nube: un loop cerrado
<!-- id: nube -->
**0:20** · sin clics

"Cuando el modelo vive en la nube, esto está bastante resuelto. Todo pasa por un endpoint: uno guarda las peticiones, las compara con lo que el modelo vio al entrenar, si algo cambia salta una alerta y se reentrena."

"¿Por qué funciona tan bien? Porque todo pasa por ahí. Uno lo ve todo."

---

## 8 · Las restricciones de la estación
<!-- id: edge -->
**1:00** · 5 clics

"Ahora bajemos ese modelo a la estación. Mismo loop… pero ya no hay un endpoint por donde pase todo."

**[CLIC]** "Uno: los recursos. Poca memoria, y chips distintos: una estación tiene ARM, otra un x86 con sus años, la nueva trae NPU."

**[CLIC]** "Dos: la red. Se va la señal y se apaga todo el loop de la nube."

**[CLIC]** "Tres: el audio no puede salir. Ni cabe, ni debe."

**[CLIC]** "Cuatro, y esta casi nadie la mide: la latencia depende de la energía. Con la batería baja o el equipo caliente, el chip se pone lento. El mismo modelo tarda más."

**[CLIC]** "Y cinco: los datos. Fallas hay pocas para aprender, y lo normal cambia: el micrófono envejece, cambia la velocidad de la bomba. Eso es el drift. Conseguir buenos datos es la mitad del trabajo… en el acto 3 van a ver qué pasa cuando no."

"Todo lo que hacíamos en la nube asume que las cosas pasan por uno. Aquí no pasa nada por uno."

---

## 9 · Un panel en verde no mide el modelo
<!-- id: tablero -->
**1:15** · 3 clics · *el mito central: ve despacio*

"Entonces, ¿cómo sabe uno si el modelo de la estación está bien? Lo de siempre: abrimos el panel."

**[CLIC]** "Servicio arriba. CPU normal. Memoria normal. Todo en verde."

*(cambia la voz)* "Y llega el jefe: «¿y el modelo cómo va?». «Todo verde, jefe»." *(risas)*

**[CLIC]** "Pero la pregunta de verdad es otra: ¿el modelo todavía distingue una bomba sana de una que falla? Eso se mide con el AUC: uno es perfecto, cero coma cinco es lanzar una moneda."

"Con la velocidad con la que se entrenó, este modelo da cero coma sesenta y nueve. Alguien le cambia la velocidad a la bomba… y baja a cero coma cincuenta y siete." *(pausa)* "Casi una moneda. Y las falsas alarmas pasan de 6 a 18 por ciento."

**[CLIC]** "Y ni un error. El equipo está sano. El modelo casi no distingue." *(pausa larga)*

"Lo medí con el mismo audio que oyeron al principio. Un servicio caído hace ruido. Un modelo que dejó de oír sigue respondiendo a tiempo, con un 200 OK."

"Monitorear la infraestructura no es monitorear el modelo. En el paso seis les muestro qué preguntarle."

---

## 10 · 02 · El patrón
<!-- id: div2 -->
**0:05** · *reloj: 5:48*

"¿Y cómo se gobierna esto? Abramos el equipo."

---

## 11 · Arquitectura del equipo en la estación
<!-- id: equipo -->
**0:45** · 3 clics

"Abajo, el micrófono sobre la bomba y el modelo con su runtime. Decide en milisegundos, haya red o no. El audio entra… y ahí se queda."

**[CLIC]** "Encima, el modelo no llega como un archivo suelto: llega como un artefacto con versión y huella. Si alguien lo toca, no se instala."

**[CLIC]** "Después, un agente. A la estación nadie le empuja nada: el agente, cuando hay red, va y pregunta qué debería tener."

**[CLIC]** "Y arriba, lo que casi nadie pone: una cola de eventos. Cada decisión se guarda hasta que vuelve la señal."

---

## 12 · Antes de proteger el modelo, protege el equipo
<!-- id: seguridad -->
**0:50** · 4 clics

"Una pregunta incómoda: esta estación está en una vereda. ¿Quién la cuida?" *(pausa)* "Nadie. Cualquiera abre el gabinete."

"Por eso, antes de preocuparse por que alguien engañe al modelo, van cuatro cosas del equipo. Uno: arranque seguro. Solo arranca software firmado."

**[CLIC]** "Dos: la llave. La identidad del equipo es la llave de su certificado. Si está en la tarjeta SD, cualquiera se la lleva y se hace pasar por la bomba. Va en un TPM."

**[CLIC]** "Tres: updates verificados. Solo instala lo que trae la huella correcta, por un canal cifrado."

**[CLIC]** "Cuatro: los datos. El audio no sale, y en el disco va cifrado."

**[CLIC]** "Porque sin esto, nadie necesita engañar a su modelo… le basta con reemplazarlo."

---

## 13 · Cinco piezas para gobernarlo
<!-- id: flujo -->
**1:05** · 6 clics

"Seamos sinceros: así se despliegan modelos en muchos lados. Uno copia el archivo al equipo… y cruza los dedos." *(cruza los dedos)* "Yo lo he hecho." *(risas)*

**[CLIC]** "Primera pieza: optimizar para cada chip. Se entrena una vez y se prepara para cada hardware."

**[CLIC]** "Segunda: un artefacto verificable. Cada versión con su huella, en un registro donde nada se sobrescribe."

**[CLIC]** "Tercera: el desired state. La central dice qué debería tener cada equipo, y el equipo lo trae cuando puede."

**[CLIC]** "Cuarta: el modelo deja constancia de cada decisión. Sin red, se encola."

**[CLIC]** "Y quinta, el gate: algo que mira esas decisiones y resuelve solo si seguimos o nos devolvemos. El loop rápido, de minutos."

**[CLIC]** "Con esas decisiones se reentrena: el loop lento, de días. Y por debajo, lo de siempre: identidad, mínimo privilegio, cifrado y auditoría. Nada de esto depende de una nube."

---

## 14 · El mismo patrón en AWS
<!-- id: aws -->
**0:30** · 5 clics · *ve rápido*

"El mismo dibujo en AWS: cada casilla ya tiene nombre."

**[CLIC]** "SageMaker AI entrena." **[CLIC]** "S3 guarda cada versión e IoT Greengrass la empaca." **[CLIC]** "El desired state es un despliegue de Greengrass que llega por IoT Core, con certificado por equipo."

**[CLIC]** "Cada decisión vuelve por IoT Core y una regla la deja en CloudWatch." **[CLIC]** "Y el gate es una alarma que llama a una Lambda, que vuelve a poner la última versión buena."

---

## 15 · 03 · Los seis pasos
<!-- id: div3 -->
**0:10** · *reloj: 9:03*

"Paso por paso: entrenar, optimizar, empaquetar, desplegar, operar sin red y monitorear. Y en cada paso, la bomba."

---

## 16 · Paso 1 · Entrenar con sonido normal
<!-- id: entrenar -->
**0:50** · 3 clics

"Paso uno. Un detalle bonito: este modelo se entrena solo con bombas sanas."

**[CLIC]** "Es un autoencoder: aprende a reconstruir el sonido normal. Cuando no puede, es porque algo cambió. Como el mecánico que de tanto oír el motor sano nota cualquier ruido raro."

**[CLIC]** "Lo que sale va a S3: el modelo en ONNX, el umbral y también el preprocesamiento del audio. Porque el error más común es entrenar con un preprocesamiento y servir con otro. No explota nada: el modelo simplemente oye distinto."

**[CLIC]** "Y así se ve en la consola: una carpeta por versión, la 1.0.0 y la 2.0.0. Versión nueva, carpeta nueva."

---

## 17 · Paso 2 · Optimizar para cada chip
<!-- id: optimizar -->
**1:00** · 3 clics

"Paso dos. Uno entrena una vez, en 32 bits, y sale un ONNX."

**[CLIC]** "Para que quepa en un equipo pequeño se cuantiza a 8 bits, se simplifica y se compila para el chip, con la herramienta de cada fabricante."

**[CLIC]** "La trampa: no sale un artefacto, sale uno por tipo de chip. Y manda la memoria: si no cabe, no corre."

**[CLIC]** "Medido en la EC2 del ensayo: de 32 a 8 bits, el archivo baja de 464 a 127 kilobytes, cada clip de 14,4 a 12,7 milisegundos, y decide igual en el 98 por ciento de los casos."

"Ojo: en mi portátil la mejora era casi el doble. En el equipo, el tiempo se va preparando el audio. Por eso se mide en el chip de verdad… con la batería baja y a las tres de la tarde en una vereda."

---

## 18 · Paso 3 · Empaquetar como componente
<!-- id: componente -->
**1:00** · 5 clics

"Paso tres. En Greengrass, el software se empaca como un componente. Esta es la receta, un poco recortada."

**[CLIC]** "Los archivos vienen de S3, y Greengrass verifica la huella de cada uno antes de instalar."

**[CLIC]** "Al arrancar no instala nada: las dependencias ya vienen. Si su componente baja librerías de internet al arrancar… en una vereda, no arranca."

**[CLIC]** "El umbral es configuración: si hay que moverlo, se despliega, no se reentrena."

**[CLIC]** "Y los permisos: solo puede publicar en un tema, station/events. Nada más."

**[CLIC]** "En la consola: el componente con sus dos versiones. Una regla que aprendí a las malas: una versión publicada no se toca. Si cambias un archivo sin cambiar la versión, la huella no cuadra y el despliegue falla."

---

## 19 · Paso 4 · Desplegar por rings
<!-- id: anillos -->
**1:05** · 4 clics

"Paso cuatro. ¿Cómo le llega una versión nueva a mil equipos sin dañarlos todos un martes por la tarde? Por rings: cada ring es un thing group. El ring 0 es una sola estación, el canary."

**[CLIC]** "Si pasa el gate, sigue el ring 1, el resto de la flota, por waves que van creciendo."

**[CLIC]** "El despliegue ya trae dos protecciones: si fallan muchos equipos, se cancela; y si un equipo no arranca la versión nueva, vuelve solito a la anterior."

**[CLIC]** "Y el rollback que armé yo: una alarma ve fallas que nadie oyó y vuelve a poner la última versión buena."

"«Pero si Greengrass ya hace rollback.» Sí… de despliegues que fallan. Un modelo que se instala perfecto y oye mal, para Greengrass, es un éxito."

**[CLIC]** "Así quedó la consola después del ensayo: un despliegue por ring. Fíjense en el nombre del ring 0. Se los explico en el acto 3."

---

## 20 · Paso 5 · Operar sin red
<!-- id: sinred -->
**0:40** · 2 clics

"Paso cinco: ¿qué pasa cuando se va la señal? En cada equipo, Greengrass guarda los eventos en una cola local hasta que vuelve la red. Y para equipos con muy poca memoria hay una versión liviana del agente, escrita en C."

**[CLIC]** "La estación sigue escuchando y alertando: lo que necesita para decidir ya lo tiene adentro. Un ojo: esa cola vive en memoria y, si se llena, rechaza mensajes. Para horas sin red, va a disco."

**[CLIC]** "Desde la consola: cinco core devices, todos sanos. Qué pasa cuando uno pierde la red lo ven en el acto 2."

---

## 21 · Paso 6 · Monitorear lo que decide el modelo
<!-- id: monitoreo -->
**1:25** · 5 clics

"Paso seis. Desde la nube no vemos el audio: vemos lo que el modelo nos cuenta. Un mensajito por clip, de unos cientos de bytes: IoT Core, una regla, CloudWatch, y una alarma que puede llamar a la Lambda."

"¿Qué hay que vigilar? Tres cosas."

**[CLIC]** "Uno: la entrada. ¿El micrófono dice la verdad? Si sube despacio durante semanas, el sensor envejece. Si salta de un clip al otro, se dañó… o alguien lo está tocando."

**[CLIC]** "Dos: la salida. ¿Cambió lo que decide? Se compara la distribución de los scores de esta hora contra la de la semana, con algo como el PSI."

**[CLIC]** "Y tres, la que casi nadie mira: la autenticidad. ¿Es el modelo que mandamos? Cada evento trae la huella del modelo." *(pausa)* "Ojo: esa huella la reporta el equipo, y un equipo comprometido puede mentir. Por eso la seguridad iba primero."

**[CLIC]** "En el ensayo, el gate sabe si la bomba fallaba porque yo sé qué audio suena. En producción eso llega tarde, con la orden de mantenimiento. Estas tres señales no lo necesitan."

**[CLIC]** "Y este es el dashboard, ordenado por esas tres señales. En un momento lo ven en acción."

---

## 22 · A mano alzada
<!-- id: reflexion3 -->
**0:30** · 1 clic

"Antes del ensayo, una pregunta: ¿ustedes saben qué versión del modelo corre en cada uno de sus equipos?" *(espera manos)* "Ahora bajen la mano los que tuvieron que pensarlo." *(risas)*

**[CLIC]** "Aquí la respuesta sale de la nube, sin entrar a ningún equipo: ring 0, la bomba 1, versión 1.0.0, activo. Ring 1, de la 2 a la 5, la misma."

---

## 23 · 04 · El ensayo
<!-- id: div4 -->
**0:05** · *reloj: 15:43*

"Suficiente teoría. Les muestro lo que pasó cuando lo corrí de verdad."

---

## 24 · Lo que monté y corrí
<!-- id: poc -->
**0:30** · sin clics

"No me traje bombas en la maleta." *(risas)* "Cada bomba es un contenedor en una EC2, con el agente real de Greengrass. Cinco: la 1 es el canary, de la 2 a la 5 el ring 1. Audio real y AWS de verdad, montado con Terraform desde GitHub Actions."

"Lo corrí completo el 18 de octubre, y lo que van a ver son las líneas y las gráficas de ese día."

---

## 25 · Acto 1 · Escuchar
<!-- id: acto1 -->
**0:50** · sin clics · *deja que lean primero*

"Esto es lo que ve uno desde la nube: cada línea es un clip que la bomba 3 escuchó y decidió."

"Normal, normal, normal… y ahí le digo a la bomba 3 que suene como la B. En ese mismo clip: alerta."

"Y esa es la respuesta del principio: la que fallaba era la B. ¿Quién votó por la B?" *(manos)* "Oído de mecánico. Los de la A, tranquilos: para eso está el modelo." *(risas)*

"Y el audio no salió de la estación. Salió esta línea."

---

## 26 · Acto 2 · Sin red, y una deriva
<!-- id: acto2 -->
**1:00** · sin clics

"Segundo acto: a la bomba 3 le quito la red." *(señala la izquierda)* "La 3 desaparece, y las otras cuatro siguen como si nada."

"45 segundos después le devuelvo la red… y llegan de golpe: «arrived 41 seconds late», 32, 29, 20. Tarde, pero todas. La bomba siguió decidiendo sin red, y su cola entregó todo al volver."

*(señala la gráfica)* "Y a la bomba 5 le cambié la velocidad. ¿Errores? Ninguno. Pero la entrada salta de 0,8 a 1,8. La primera señal del paso seis… en diferido." *(risas)*

---

## 27 · Acto 3 · Ring deployment y rollback
<!-- id: acto3 -->
**1:20** · 2 clics · *el clímax: ve despacio*

"Tercer acto. Mando la versión 2.0.0, solo al ring 0. Se entrenó con más audio. Y más datos es mejor modelo, ¿cierto?" *(pausa)* "Llegó en 17 segundos, sin errores. Para Greengrass, perfecto."

"Pongo a fallar la bomba 1… «normal», «missed fault», «normal», «missed fault». La bomba falla y la versión nueva no avisa."

"¿Qué pasó? ¿Se acuerdan de los datos? Ese audio extra traía una semana en que una bomba ya venía fallando, y nadie lo revisó. El modelo aprendió que fallar es lo normal. No es un bug de código: es un bug de datos."

"Y ahora nadie toca nada. La alarma pasa a ALARM, la Lambda devuelve la 1.0.0, y la bomba 1 vuelve a alertar. Ochenta y ocho segundos. Nadie entró al equipo, y el ring 1 nunca recibió la versión mala." *(pausa)* "Ese era el nombre del ring 0 en la consola: rollback."

**[CLIC]** "Así se vio la alarma: las fallas que nadie oyó pasan de 8, y esa franja roja es el momento en ALARM."

**[CLIC]** *(mirando a la sala, despacio)* "Greengrass revierte despliegues fallidos, pero no modelos equivocados. Ese gate lo tiene que poner uno."

---

## 28 · Cinco recomendaciones
<!-- id: llevo -->
**1:05** · 4 clics · *reloj: 19:28 al entrar*

"Les dejo cinco cosas. Casi nadie las hace el lunes… pero los que las hacen duermen más tranquilos."

"Una: el modelo es un artefacto, con versión, huella y firma, sobre un equipo que arranca seguro."

**[CLIC]** "Dos: midan en el chip de verdad, con batería baja y con calor."

**[CLIC]** "Tres: desplieguen por rings, con un gate que mire al modelo, no solo al proceso."

**[CLIC]** "Cuatro: diseñen para estar sin red. Cola local, decisiones locales."

**[CLIC]** "Y cinco: vigilen tres señales: entrada, salida y autenticidad. El audio, que se quede en el equipo."

*(Si el reloj marca 19:50 o menos: «¿Saben qué fue lo primero que se me dañó? La primera vez que monté esto, ninguna bomba arrancaba. Horas buscando, y era que el instalador decide el formato del archivo por la extensión… y mi archivo no tenía extensión. Una línea. Por eso se ensaya en el equipo de verdad.»)*

---

## 29 · La frase final: ¿esta bomba está fallando?
<!-- id: final -->
**0:45** · 2 clics · *cierre circular*

"¿Se acuerdan de la pregunta del principio? ¿Esta bomba está fallando?" *(▶ B, tres segundos)*

"Ustedes la oyeron. Desde la nube, nadie la oyó… y no hacía falta."

**[CLIC]** "Esto fue lo único que salió de la estación: la bomba 3, versión 1.0.0, alerta. Unos cientos de bytes."

**[CLIC]** "Porque uno no necesita ver el modelo. Necesita que el modelo le cuente." *(pausa)*

"Y una última pregunta: si mañana uno de sus modelos deja de oír… ¿quién se va a enterar primero? ¿Ustedes… o la vereda que se quedó sin agua?" *(pausa larga)*

---

## 30 · Recursos y contacto
<!-- id: recursos -->
**0:15** · sin clics

"Todo está en el repo de ese QR: el código, las láminas y este guion. Tómenle foto."

---

## 31 · Gracias
<!-- id: cierre -->
**0:15** · sin clics

"Muchas gracias." *(espera el aplauso)* "Con todo gusto respondo sus preguntas."

*Anexos: la tecla A abre A1; las flechas los recorren; M o Esc te devuelven. A1 evento · A2 rollback · A3 qué revierte Greengrass · A4 permisos y costo · A5 a producción · A6 drift · A7 regulación · A8 fuentes · A9 golden signals · A10 audio contra eventos.*

---

## A1 · El evento, campo por campo
<!-- id: a1 -->
"Cada mensaje dice qué bomba decidió, con qué versión y la huella exacta del modelo; un número de secuencia y la hora de la decisión; el score, el umbral y si alertó; cómo venía la entrada y la latencia. La hora de llegada la pone la regla de IoT: la diferencia es lo que la estación estuvo sin red."

---

## A2 · El rollback automático, paso a paso
<!-- id: a2 -->
"Yo solo mandé la 2.0.0 al ring 0. La bomba 1 trajo su desired state, bajó de S3, verificó la huella e instaló: para Greengrass, todo bien. Pero la versión nueva no avisaba las fallas. Cada mensaje pasa por la regla, cae en CloudWatch, y un filtro cuenta las fallas que nadie oyó. Con ocho en un minuto salta la alarma, llama a la Lambda, la Lambda pregunta en Parameter Store cuál fue la última versión buena y la despliega solo en el ring 0. De ahí en adelante, nadie toca nada."

---

## A3 · ¿Qué revierte Greengrass solo?
<!-- id: a3 -->
"Tres casos: si un archivo cambió y la huella no cuadra; si el componente no instala o no arranca; y si fallan muchos equipos del ring. Lo que no ve: un modelo que corre perfecto y decide mal. Eso solo lo ven los eventos del modelo y una alarma que los mire."

---

## A4 · Permisos y costo
<!-- id: a4 -->
"Cada pieza tiene lo mínimo: la bomba lee su bucket y publica en su tema, con su identidad; la regla escribe en sus logs; la Lambda crea el despliegue y lee un parámetro. El costo lo pone sobre todo la EC2, y todo se baja con un destroy desde GitHub Actions."

---

## A5 · De la demo a producción
<!-- id: a5 -->
"Cambian cinco cosas: un resumen por minuto en vez de un mensaje por clip; la cola a disco; el agente liviano en equipos pequeños; el canary comparado contra el ring; y la verdad de la falla llega tarde, con la orden de mantenimiento."

---

## A6 · ¿Qué método de drift uso?
<!-- id: a6 -->
"Depende del dato. PSI para rangos o categorías, con umbrales que son más costumbre que estadística. Kolmogorov-Smirnov con pocas muestras. Wasserstein para saber cuánto se movió. Jensen-Shannon, entre cero y uno, cómodo para alertar. En la PoC uso la distancia de cada clip a la huella de lo normal."

---

## A7 · Regulación
<!-- id: a7 -->
**3 clics**

"En Europa, el AI Act pide a los sistemas de alto riesgo registrar eventos durante toda su vida, guardarlos seis meses y monitorearlos en el mercado."

**[CLIC]** "En Estados Unidos, el marco de riesgo del NIST: voluntario, pero el idioma común."

**[CLIC]** "Y la ISO 42001: la 27001 para IA, certificable."

**[CLIC]** "Todos piden lo mismo que uno necesita para operar: qué corre, qué decidió y cómo devolverse."

---

## A8 · Fuentes
<!-- id: a8 -->
"Todo está aquí y en el repo. Los audios son de MIMII DUE, de Hitachi, con licencia abierta no comercial."

---

## A9 · Las golden signals de un modelo
<!-- id: senales -->
"Las de un servicio las conocemos: latencia, tráfico, errores y saturación. Las de un modelo: qué decide, con cuánta seguridad, si lo que le llega se parece a lo que aprendió, y qué versión corre dónde. Ninguna sola alcanza."

---

## A10 · Audio crudo contra eventos, con mil bombas
<!-- id: costo -->
**2 clics**

"El audio crudo de mil bombas: 2,76 terabytes al día."

**[CLIC]** "Un mensaje cada 10 segundos: 8,64 millones al día."

**[CLIC]** "Un resumen por minuto: 1,44 millones. Y el audio, quietico en la estación."
