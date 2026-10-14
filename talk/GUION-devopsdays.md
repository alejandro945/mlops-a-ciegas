# Guion · MLOps a ciegas · DevOpsDays Bogotá 2026

**Duración:** 25:30 de contenido, dentro de los 25 minutos más 5 de preguntas del CFP. Cronométralo en el ensayo; el acto 3 depende de la alarma. **Láminas:** 30 más 10 anexos; cuatro son divisores y pasan en segundos.

**De qué va:** cómo gobernar un modelo de IA que corre donde no llega el plano de control, contado con una estación de bombeo inventada: un modelo que escucha bombas en una vereda donde la señal va y viene.

Este archivo es la fuente de las notas del presentador: cada sección con `<!-- id: … -->` aparece al presionar **N** en su lámina. Si cambias algo aquí, regenera el deck:

```
AWS_ICONS=<ruta al paquete de íconos> REPO_URL=… LINKEDIN=… python3 talk/tools/build_deck.py
```

**Cómo usarlo:** lo que va entre comillas no es para memorizar. Es *una* forma de decirlo, en tono de conversación. Léelo en voz alta, quédate con la idea y dila con tus palabras; si una frase no te sale natural, cámbiala. Lo único que conviene decir tal cual son los primeros 30 segundos, las cifras y el cierre.

- **[CLIC]** avanza un paso de la lámina. *(pausa)* es silencio. Lo que va en cursiva es para ti.
- El tiempo en negrita es lo que dura la lámina, no la hora del reloj.
- La terminal y AWS están en inglés (`pump-03`, `ALERT`); en voz alta di «la bomba 3» y «alerta» si te sale más natural. La jerga técnica (ring, canary, gate, rollback) se queda en inglés.

---

## Cómo enganchar a la sala

Lo que hacen los buenos speakers, y dónde está en esta charla:

1. **Arranca con una experiencia, no con un saludo.** Lo primero que oye la sala es una bomba (lámina 2). El «buenos días» y la presentación van después, cuando ya los tienes.
2. **Deja una pregunta abierta.** «¿Cuál bomba está fallando?» no se responde hasta la demo. La gente se queda esperando la respuesta.
3. **Haz que la sala haga algo.** Levantar la mano dos veces (láminas 2 y 23) vale más que diez láminas de contexto. Espera de verdad las manos y comenta lo que ves.
4. **Pon personajes con voz.** El jefe que pregunta «¿y el modelo cómo va?», el técnico a las 3 a. m. Cambia un poco la voz y la postura cuando hablas por ellos.
5. **Baja los números a escala humana.** No «32 000 bytes por segundo»: «115 megas por hora, por bomba, por la red de una vereda».
6. **Cuenta lo que te pasó.** Lo que se rompió en el ensayo (la bomba que no arrancaba por una extensión de archivo) engancha más que cualquier diagrama.
7. **Muestra antes de explicar.** En la demo, primero que vean la línea en la terminal y después la explicas.
8. **Cierra donde empezaste.** Los audios del principio vuelven al final, con la respuesta. Y terminas con una pregunta que se lleven a la casa.
9. **Usa las pausas.** Después de una cifra que importa (0,57), cállate dos segundos. El silencio hace que la sala la registre.

---

## 1 · MLOps a ciegas
<!-- id: portada -->
**0:10** · sin clics

*En pantalla mientras te presentan. Cuando te den la palabra, no saludes todavía: pasa a la lámina 2 y pon la bomba A. Antes de subir, prueba que el audio del deck sale por los parlantes de la sala.*

---

## 2 · ¿Esta bomba está fallando?
<!-- id: suena -->
**1:15** · 1 clic · *lo primero que oye la sala es una bomba*

"Les voy a poner dos audios. Esta es la bomba A." *(▶ A, cinco segundos, la detienes)*

"Y esta es la bomba B." *(▶ B, cinco segundos)*

"Pregunta: ¿alguna de las dos está fallando?"

**[CLIC]** "Levanten la mano. ¿La A?" *(cuenta en voz alta: «unos cinco…»)* "¿La B?" *(cuenta)* "¿Las dos?" *(cuenta)* "Interesante. No les voy a decir todavía; eso lo vemos en vivo."

"Los sonidos son reales, los grabó Hitachi en una planta. Lo que sí me inventé es la empresa: un acueducto con estaciones de bombeo en veredas, donde la señal va y viene y no hay nadie cerca. En cada estación hay un equipito que escucha las bombas, y un modelo que avisa cuando una empieza a sonar raro."

"Lo que ustedes acaban de hacer es justo lo que hace ese modelo: oír y decidir. La diferencia es que ustedes estaban aquí. Desde la nube, nadie oyó nada." *(pausa)*

"Por eso le puse a esta charla «MLOps a ciegas». Hoy les quiero mostrar cómo se maneja un modelo que corre allá, donde uno no lo ve: cómo le llega una versión nueva, cómo se devuelve si sale mala y cómo nos cuenta lo que decide. Sin que el audio salga nunca de la estación."

*Mientras suena un audio, una tecla o un clic lo detiene y no cambia de lámina. Si los botones dicen «audio pendiente», faltan talk/assets/audio/pump-a.wav y pump-b.wav. La atribución de MIMII DUE está al pie.*

---

## 3 · La IA ya corre en el dispositivo
<!-- id: cien -->
**0:35** · 2 clics

"Y ustedes dirán: bueno, ¿y a mí qué me importa un modelo en una bomba? Les cuento por qué: los modelos se están bajando de la nube a los dispositivos. Un ejemplo con números de Gartner, los PC."

"En 2024, de cada cien PC nuevos, dieciséis traían un chip para correr IA."

**[CLIC]** "En 2025, treinta y uno."

**[CLIC]** "Y para este año proyectaban cincuenta y cinco. Más de la mitad. Y no son solo los PC: el celular de ustedes, los carros, las cámaras, los equipos de una planta… todos ya traen hardware para correr modelos ahí mismo."

*Fuente: Gartner, 28 de agosto de 2025, «AI PCs»: 15,6 % (2024), 31 % (2025), 54,7 % (2026, proyección). La cifra es solo de PC; lo demás dilo sin números. Si ya salió la cifra real de 2026, úsala.*

---

## 4 · Por qué el modelo baja al dispositivo
<!-- id: memes -->
**0:50** · 2 clics · *deja que se rían antes de seguir. En cada meme, a la izquierda el modelo corre en la nube y a la derecha en el equipo*

"¿Y por qué se baja? Se los explico como explicamos todo los ingenieros: con memes."

*Meme 1.* "El carro autónomo, frente a un cono: 'dame un segundo, que le pregunto al modelo en la nube'." *(pausa, risas)* "Cuando hay que frenar ya, la ida y vuelta no alcanza."

**[CLIC]** *Meme 2.* "El técnico a las tres de la mañana en la planta: '¿cómo cambio este rodamiento?'. Y el asistente, que tiene el modelo en la nube: 'Sin conexión, intente más tarde'." *(risas)* "Con el modelo en el equipo, le responde igual. Y en una vereda, sin señal, pasa exactamente lo mismo."

**[CLIC]** *Meme 3.* "Y mi favorito: el reloj mandándole tus latidos, cada segundo, a un modelo en la nube. Si el modelo corre en el reloj, lo único que sale es la alerta."

"Ahora piensen en la bomba. Un micrófono son ciento quince megas por hora. Por bomba. Por la red de una vereda. No cabe, y además es el sonido de una instalación de la empresa: no tiene por qué salir de ahí."

*Cuenta: 16 000 muestras por segundo × 2 bytes ≈ 115 MB por hora.*

---

## 5 · Sobre mí
<!-- id: quien -->
**0:35** · sin clics

"Ahora sí, mucho gusto. Soy Alejandro Varela, Senior Cloud Engineer en EPAM. Mi trabajo es justamente este: llevar modelos de IA de la nube a equipos en campo."

"Tengo unas certificaciones por ahí, pero les confieso algo: lo que van a ver hoy no salió de un examen. Lo monté, lo rompí y lo arreglé esta misma semana."

"Y fuera del trabajo me encuentran con una raqueta en la mano, la que sea: tenis de mesa, tenis, pádel. O aprendiendo algo nuevo, o de viaje."

*La foto sale de talk/assets/photo.jpeg (recortada en cuadrado). El LinkedIn sale de la variable LINKEDIN al generar el deck.*

---

## 6 · Contenido de la sesión
<!-- id: agenda -->
**0:15** · sin clics

"Vamos a ir en cuatro partes: primero el problema, después el patrón para resolverlo, luego los seis pasos, y al final lo vemos funcionando en vivo."

---

## 7 · 01 · El problema
<!-- id: div1 -->
**0:05** · *divisor: no lo leas* · *reloj: 3:40*

"Arranquemos por el problema."

---

## 8 · MLOps en la nube: un loop cerrado
<!-- id: nube -->
**0:25** · sin clics · *los puntos recorren el loop*

"Cuando el modelo vive en la nube, la verdad, esto está bastante resuelto. Todas las peticiones pasan por un endpoint: uno las guarda, las compara con lo que vio el modelo al entrenar, si algo cambia salta una alerta y se reentrena."

"¿Y por qué funciona tan bien?" *(señala la frase de la izquierda)* "Porque todo pasa por ahí. Uno lo ve todo."

---

## 9 · Las restricciones de la estación
<!-- id: edge -->
**0:45** · 3 clics · *una restricción por clic*

"Ahora bajemos ese modelo a la estación, al lado de la bomba. Mismo loop… pero ya no hay un endpoint por donde pase todo."

**[CLIC]** "Primero, los equipos no son iguales. Una estación tiene un equipo ARM, otra uno x86 que ya tiene sus años, y la nueva trae NPU. El mismo modelo no corre igual en los tres."

**[CLIC]** "Segundo, la red. Se va la señal en la vereda y se apaga todo el loop de la nube."

**[CLIC]** "Y tercero, el audio no puede salir de ahí. Ni cabe, ni debe."

"O sea: todo lo que uno hacía en la nube asume que las cosas pasan por uno. Aquí no pasa nada por uno."

---

## 10 · Un panel en verde no mide el modelo
<!-- id: tablero -->
**1:15** · 3 clics · *el mito central de la charla: ve despacio*

"Entonces, ¿cómo sabe uno si el modelo de la estación está bien? Lo de siempre: abrimos el panel."

**[CLIC]** "Servicio del modelo, arriba. CPU, normal. Memoria, normal. Todo en verde."

*Cambia la voz:* "Y llega el jefe: '¿y el modelo de la estación cómo va?' — 'Todo verde, jefe'." *(risas)*

**[CLIC]** "Pero la pregunta de verdad es otra: ¿el modelo todavía distingue una bomba sana de una que está fallando? Eso se mide con algo que se llama AUC. Para los que no son de datos: uno es perfecto, y cero coma cinco es lo mismo que lanzar una moneda."

"Con la velocidad con la que se entrenó, este modelo da cero coma sesenta y nueve. Ahora alguien le cambia la velocidad a la bomba… y baja a cero coma cincuenta y siete." *(pausa)* "Casi una moneda. Y las falsas alarmas pasan de 6 a 18 por ciento."

**[CLIC]** "Y lo más bonito: ni un error. El equipo está sano. El modelo casi no distingue." *(pausa larga)*

"Y esto no es teoría: lo medí con el mismo audio de las bombas que van a oír en un rato. Un servicio caído hace ruido. Un modelo que dejó de oír sigue respondiendo a tiempo, con un 200 OK."

*Por qué AUC y no «fallas detectadas»: con la otra velocidad todos los scores suben, y la detección puede subir junto con las falsas alarmas. La AUC mide si el modelo separa una bomba sana de una que falla, sin depender del umbral.*

---

## 11 · Monitorear la infraestructura no es monitorear el modelo
<!-- id: preguntas -->
**0:30** · sin clics

"Las preguntas de siempre siguen sirviendo: ¿el servicio está arriba?, ¿cuánta CPU gasta?, ¿hay errores? Pero ninguna dice nada del modelo."

"Al modelo hay que preguntarle otras cosas." *(señala, una por una)* "¿Sigue distinguiendo bien? ¿Le cambiaron los datos? ¿Se le dispararon los falsos positivos o los falsos negativos? Y la más difícil: ¿lo que predice todavía le sirve a alguien?"

"Esa última solo la responde el negocio, cuando el de mantenimiento llega y dice si la alerta era real o no. Las otras tres, ya las van a ver en la demo."

---

## 12 · 02 · El patrón
<!-- id: div2 -->
**0:05** · *divisor* · *reloj: 6:40*

"Bueno, ¿y cómo se gobierna esto? Abramos el equipo."

---

## 13 · Arquitectura del equipo en la estación
<!-- id: equipo -->
**0:45** · 3 clics · *una capa por clic*

"Abajo está el micrófono sobre la bomba y el modelo con su runtime. Decide en milisegundos, haya red o no. El audio entra… y ahí se queda."

**[CLIC]** "Encima, el modelo no llega como un archivo suelto que alguien copió. Llega como un artefacto con versión y con su huella. Si alguien lo toca, no se instala."

**[CLIC]** "Después, un agente. A la estación nadie le empuja nada; es el agente el que, cuando hay red, va y pregunta qué debería tener."

**[CLIC]** "Y arriba, lo que casi nadie pone: una cola de eventos. Cada decisión se guarda hasta que vuelva la señal."

---

## 14 · Cinco piezas para gobernarlo
<!-- id: flujo -->
**1:10** · 6 clics · *una pieza por clic; la leyenda se enciende con cada una*

*Paso 0, «copiar el modelo… y cruzar los dedos».* "Seamos sinceros: así se despliegan modelos en muchos lados. Uno copia el archivo al equipo… y cruza los dedos." *(cruza los dedos)* "Yo lo he hecho, no me da pena." *(risas)*

**[CLIC]** "La primera pieza es optimizar para cada chip: se entrena una vez y se prepara para cada tipo de hardware."

**[CLIC]** "La segunda, un artefacto verificable: cada versión con su huella, en un registro donde nada se sobrescribe."

**[CLIC]** "La tercera, el desired state: la central dice qué debería tener cada equipo, y el equipo lo trae cuando puede."

**[CLIC]** "La cuarta, que el modelo deje constancia de cada decisión. Si no hay red, se encola."

**[CLIC]** "Y la quinta, el gate: algo que mira esas decisiones y resuelve solo si seguimos o nos devolvemos. Eso es el loop rápido, de minutos."

**[CLIC]** "Con esas mismas decisiones se reentrena; ese es el loop lento, de días. Y por debajo de todo, lo de siempre: identidad, mínimo privilegio, cifrado y auditoría. Nada de esto depende de una nube en particular."

---

## 15 · El mismo patrón en AWS
<!-- id: aws -->
**0:50** · 6 clics · *misma geometría; ve a buen ritmo, los pasos que vienen abren cada casilla*

"Ahora el mismo dibujo, pero en AWS. Cada casilla ya tiene nombre."

**[CLIC]** "SageMaker AI entrena." **[CLIC]** "S3 guarda cada versión e IoT Greengrass la empaca como componente." **[CLIC]** "El desired state es un despliegue de Greengrass, que le llega a cada equipo por IoT Core, con su propio certificado."

**[CLIC]** "Cada decisión vuelve por IoT Core y una regla la deja en CloudWatch." **[CLIC]** "El gate es una alarma que llama a una Lambda, y la Lambda vuelve a poner la última versión buena." **[CLIC]** "Y abajo, IAM, certificados, KMS y CloudTrail."

---

## 16 · 03 · Los seis pasos
<!-- id: div3 -->
**0:10** · *divisor con la espina* · *reloj: 9:30*

"Vamos paso por paso: entrenar, optimizar, empaquetar, desplegar, operar sin red y monitorear. Y en cada paso, la bomba."

---

## 17 · Paso 1 · Entrenar con sonido normal
<!-- id: entrenar -->
**1:00** · 3 clics

"Paso uno, entrenar. Y aquí hay un detalle bonito: este modelo se entrena solo con bombas sanas."

**[CLIC]** "Es un autoencoder: una red que aprende a reconstruir el sonido normal. Cuando no lo puede reconstruir, es porque algo cambió. Es como el mecánico que de tanto oír el motor sano, nota cualquier ruido raro."

**[CLIC]** "Lo que sale va a S3, cada versión en su propia carpeta. Versión nueva, carpeta nueva; nunca se pisa la anterior."

**[CLIC]** "¿Y qué sale exactamente? Cuatro archivos: el modelo en ONNX, que es como el contrato con el equipo; la huella del sonido normal con el umbral; el preprocesamiento del audio, y el código que escucha y decide."

"¿Y por qué mandar el preprocesamiento con el modelo? Porque el error más común es entrenar con un preprocesamiento y servir con otro. No explota nada. El modelo simplemente oye distinto, y nadie se entera."

*En la PoC la fábrica es model/train.py en mi portátil, no SageMaker AI. Lo dices en la lámina 25.*

---

## 18 · Paso 2 · Optimizar para cada chip
<!-- id: optimizar -->
**1:10** · 3 clics

"Paso dos. Uno entrena una vez, en 32 bits, y sale un archivo ONNX."

**[CLIC]** "Para que eso quepa en un equipo pequeño se cuantiza a 8 bits, se simplifica y se compila para el chip. Esa compilación la hace la herramienta de cada fabricante."

**[CLIC]** "Y aquí está la trampa: no sale un artefacto, sale uno por cada tipo de chip. Y el que manda es la memoria: si no cabe, no corre."

**[CLIC]** "Esta es la bomba, medida en el equipo de la demo. De 32 a 8 bits, el archivo baja de 464 a 127 kilobytes, cada clip pasa de 14,4 a 12,7 milisegundos, y toma la misma decisión en el 98 por ciento de los casos."

"Ahora, un dato curioso: en mi portátil la mejora era casi el doble. En el equipo, la mayor parte del tiempo se va preparando el audio, no en el modelo. Por eso hay que medir en el chip de verdad, no en el computador de uno."

*Portátil (M3 Pro): 2,6 → 2,0 ms. La pérdida de AUC del INT8 es de −0,001. Si preguntan por herramientas: LiteRT y Qualcomm QNN para NPU, TensorRT para GPU de NVIDIA, ONNX Runtime y OpenVINO para CPU. Sobre SageMaker Neo, ver «Preguntas difíciles».*

---

## 19 · Paso 3 · Empaquetar como componente
<!-- id: componente -->
**1:00** · 4 clics · *una anotación por clic*

"Paso tres. En IoT Greengrass, el software se empaca como un componente, y esta es la receta de la demo, un poco recortada."

**[CLIC]** "Los archivos vienen de S3. Ojo que la receta no trae el digest: Greengrass lo calcula cuando uno publica la versión y lo verifica en el equipo antes de instalar."

**[CLIC]** "Cuando arranca, no instala nada. Las dependencias ya vienen en el equipo. Si su componente baja librerías de internet al arrancar… en una vereda sin señal, no arranca."

**[CLIC]** "El umbral es configuración. Si hay que moverlo, se manda un despliegue; no hay que reentrenar."

**[CLIC]** "Y los permisos: este componente solo puede publicar en un tema, station/events. Nada más."

"Y una regla que aprendí a las malas: una versión publicada no se toca. Si uno cambia un archivo en S3 sin cambiar la versión, el digest ya no cuadra y el despliegue falla."

*Fuente del digest: referencia de recetas de Greengrass, campo Digest de Artifacts. https://docs.aws.amazon.com/greengrass/v2/developerguide/component-recipe-reference.html*

---

## 20 · Paso 4 · Desplegar por rings
<!-- id: anillos -->
**1:05** · 3 clics

"Paso cuatro. ¿Cómo le llega una versión nueva a mil equipos sin dañarlos todos un martes por la tarde? Con despliegues de Greengrass, por rings: cada ring es un thing group."

"El ring 0 es una sola estación, el canary. Es la que recibe la versión nueva primero."

**[CLIC]** "Si pasa el gate, sigue el ring 1, el resto de la flota, y no de golpe: por waves que van creciendo."

**[CLIC]** "Y el despliegue ya trae dos protecciones: si fallan muchos equipos, se cancela; y si un equipo no logra arrancar la versión nueva, vuelve solito a la que tenía."

**[CLIC]** "Y el rollback que armé yo: una alarma ve fallas que nadie oyó y vuelve a poner la última versión buena. El ring 1 nunca recibe la mala."

"Seguro alguno está pensando: 'pero si Greengrass ya hace rollback'. Sí… pero de despliegues que fallan. Un modelo que se instala perfecto y oye mal, para Greengrass, es un despliegue exitoso."

*Fuentes: failureHandlingPolicy = ROLLBACK por defecto, https://docs.aws.amazon.com/greengrass/v2/APIReference/API_DeploymentPolicies.html · abortConfig y jobExecutionsRolloutConfig, https://docs.aws.amazon.com/cli/latest/reference/greengrassv2/create-deployment.html*

---

## 21 · Paso 5 · Operar sin red
<!-- id: sinred -->
**0:50** · 2 clics

"Paso cinco: ¿qué pasa cuando se va la señal?"

"En un equipo pequeño, Greengrass guarda los eventos en una cola local hasta que vuelve la red. Y si el equipo tiene muy poca memoria, existe una versión liviana del agente, escrita en C."

**[CLIC]** "Si la estación es más bien una planta grande, está Outposts con EKS local: el plano de control corre ahí mismo y sigue funcionando sin la región."

**[CLIC]** "En los dos casos, la estación sigue escuchando y alertando. Lo que necesita para decidir ya lo tiene adentro."

"Ahora, un ojo con la cola: cuando se llena, empieza a rechazar mensajes. Si la red se va por horas, esa cola tiene que ir a disco."

*Fuentes: cola mqtt.spooler de 2,5 MB en memoria, https://docs.aws.amazon.com/greengrass/v2/developerguide/greengrass-nucleus-component.html · cola en disco, https://docs.aws.amazon.com/greengrass/v2/developerguide/disk-spooler-component.html · nucleus lite (5 MB de almacenamiento, menos de 15 MB de RAM), https://docs.aws.amazon.com/greengrass/v2/developerguide/greengrass-nucleus-lite-component.html · EKS local sin red, https://docs.aws.amazon.com/eks/latest/userguide/eks-outposts-network-disconnects.html*

---

## 22 · Paso 6 · Monitorear lo que decide el modelo
<!-- id: monitoreo -->
**1:05** · 5 clics · *un tramo de la tubería por clic*

"Y el paso seis: desde la nube no vemos el audio, vemos lo que el modelo nos cuenta. Un mensajito por cada clip, de unos cientos de bytes, que llega a IoT Core."

**[CLIC]** "Una regla de IoT lo recibe y le pega la hora de llegada. La diferencia entre la hora en que la bomba decidió y la hora en que llegó es justo el tiempo que estuvo sin red."

**[CLIC]** "Eso cae en CloudWatch Logs."

**[CLIC]** "Un filtro cuenta lo que nos importa. En la demo es este: la bomba estaba fallando y el modelo no avisó. Fallas que nadie oyó."

**[CLIC]** "Una alarma vigila ese número."

**[CLIC]** "Y cuando salta, llama a la Lambda, que devuelve el ring 0 a la última versión buena."

"Aquí está el error de siempre: poner la alarma sobre CPU y errores. Ya vimos que eso se queda en verde. El gate tiene que mirar al modelo."

*Si alguien pregunta cómo se sabe en producción si la bomba fallaba: ese campo solo existe en la demo. En producción la confirmación llega tarde, con la orden de mantenimiento, y mientras tanto se compara el canary contra el resto.*

---

## 23 · A mano alzada
<!-- id: reflexion3 -->
**0:35** · 1 clic · *la barra cuenta cinco segundos*

"Una pregunta antes de la demo: ¿ustedes saben qué versión del modelo está corriendo en cada uno de sus equipos?" *(espera manos)* "Ahora bajen la mano los que tuvieron que pensarlo." *(risas)*

**[CLIC]** "Aquí la respuesta sale de la nube, sin entrar a ningún equipo: el ring 0, la bomba 1, versión 1.0.0, activo. El ring 1, de la 2 a la 5, la misma."

*Así lo devolvió `aws greengrassv2 list-deployments` en el ensayo: un despliegue a un thing group queda ACTIVE. Detalle de un equipo, si lo piden: `aws greengrassv2 list-installed-components --core-device-thing-name pump-01`. Antes de subir, confirma que la flota está así.*

---

## 24 · 04 · Demostración
<!-- id: div4 -->
**0:05** · *divisor* · *reloj: 16:25*

"Bueno, suficiente teoría. Vamos para la estación."

---

## 25 · Arquitectura de la demostración
<!-- id: poc -->
**0:40** · sin clics

"Les cuento qué monté, porque no me traje bombas en la maleta." *(risas)* "Cada bomba es un contenedor en una EC2, con el agente real de Greengrass adentro. Son cinco: la 1 es el ring 0, el canary, y de la 2 a la 5 son el ring 1."

"El audio es real, y todo lo demás es AWS de verdad, montado con Terraform desde GitHub Actions."

"Lo único de mentiras es el equipo físico… y la fábrica del modelo, que es un script en mi portátil y no SageMaker."

*Si preguntan: las cinco bombas salen de tres secciones de MIMII DUE; la 1 y la 4 comparten sección, y la 2 y la 5 también, con clips distintos. Cada nucleus es una JVM: en el ensayo, unos 220 MB por bomba.*

---

## 26 · Demostración en tres actos
<!-- id: demo -->
**6:00** · 2 clics en la lámina, después las terminales · *la lámina es el mapa; lo de verdad está en la terminal*

*En la lámina (0:20).* "Van a ser tres actos. En el primero, la bomba 3 va a sonar como la B del principio."

**[CLIC]** "En el segundo, la dejamos sin señal."

**[CLIC]** "Y en el tercero, mandamos una versión nueva por rings… y vemos qué pasa." *(señala la frase de abajo)* "Esa frase de abajo es el final de la película, así que no la lean todavía." *(risas)*

*Cambia a las terminales: `./demo/watch.sh` a la izquierda; arriba a la derecha, el dashboard `station`; abajo a la derecha, la terminal de Session Manager en la EC2. Letra grande.*

"Esto que ven aquí es la estación en vivo. Cada línea es un clip que una bomba escuchó y decidió: qué bomba, qué versión, si alertó, el score contra el umbral, cómo venía el audio y cuánto se demoró. Esas son las golden signals de un modelo. Y fíjense que el audio no aparece por ningún lado."

**Acto 1 · Escuchar (1:00)**

*Escribe* `./demo/fault.sh pump-03` — "Le voy a decir a la bomba 3 que suene como la B."

*Cuando aparezca pump-03 v1.0.0 ALERT (en el ensayo salió al siguiente clip):* "¡Ahí está! Alerta: el score pasó el umbral."

"Y aquí está la respuesta de la pregunta del principio: la que estaba fallando era la B. ¿Quién votó por la B?" *(manos)* "Ustedes tienen oído de mecánico. Los de la A, tranquilos, para eso está el modelo." *(risas)*

"Y ojo: el audio no salió de la estación. Lo único que salió fue esta línea."

*No apagues la falla de la 3: en el acto 2, lo que llega tarde tienen que ser alertas.*

**Acto 2 · Sin red (1:20)**

*Escribe* `./demo/network.sh off pump-03` — "Ahora le quito la red a la bomba 3. Como cuando se va la señal en la vereda."

*Mientras esperas, lanza el despliegue del acto 3:* `./demo/deploy.sh 2.0.0 ring-0` — "Y mientras tanto, aprovecho y le mando una versión nueva a una sola estación. Ya volvemos a eso."

*A los 40 o 50 s:* "Miren: la 3 se calló, y las otras cuatro siguen como si nada. ¿Se dañó? No. Sigue escuchando, sigue alertando, y va guardando todo en su cola. La nube no sabe nada; la estación sí."

*Escribe* `./demo/network.sh on pump-03` — *en el ensayo se reconectó en unos 5 s.* "Y ahí llegan, de golpe. Llegaron tarde, pero llegaron todas: ese 'arrived late' es el tiempo que la bomba estuvo sin señal. No se perdió ninguna alerta."

*Escribe* `./demo/fault.sh pump-03 off`

**Acto 3 · Ring deployment y rollback (3:05)**

*Señala la bomba 1, que ya corre v2.0.0 (en el ensayo llegó en 13 a 20 s); de la 2 a la 5 siguen en v1.0.0.* "La versión nueva se entrenó con más audio. Y más datos es mejor modelo, ¿cierto?" *(pausa)* "Además da menos alertas, en operación están felices. Llegó solo al ring 0, sin errores, con la misma latencia. Para Greengrass, todo perfecto."

*Escribe* `./demo/fault.sh pump-01` — "Ahora pongamos a fallar la bomba 1."

*Cuando aparezca pump-01 v2.0.0 normal … · missed fault:* "La bomba está fallando… y la versión nueva dice 'normal'. Una falla que nadie oyó." *(pausa)*

"¿Qué pasó? Ese audio extra incluía la semana en que una bomba ya venía fallando, y nadie lo revisó. El modelo aprendió que fallar es lo normal. No da errores, da menos alertas… y no oye las fallas."

*Mientras la alarma junta datos:* "Y ahora no voy a tocar nada. Dejemos que el gate haga su trabajo." *Cambia al deck: tecla A y una flecha a la derecha te llevan al anexo A2. Cuenta la secuencia con la nota de A2 (un minuto). M te devuelve aquí.*

*Vuelve a watch.sh. Cuando la 1 salga en v1.0.0 con ALERT:* "Ahí volvió: versión 1.0.0, y alerta otra vez. Nadie entró al equipo, y el ring 1 nunca recibió la versión mala."

*Escribe* `./demo/fault.sh pump-01 off`

*Vuelve a esta lámina y dilo mirando a la sala, despacio:* "Greengrass revierte despliegues fallidos, pero no modelos equivocados. Ese gate lo tiene que poner uno."

*Tiempos medidos en los ensayos del 12 de octubre: de `fault.sh pump-01` a la v1 otra vez, entre 90 y 135 s. Depende de en qué segundo del minuto cae la falla. Si a los tres minutos la 1 no ha vuelto, no esperes más: «La alarma va a su ritmo; para no robarles tiempo, les muestro cómo termina», y pon el video desde el rollback.*

*Plan B, si la red del evento falla (watch.sh sin líneas en 30 s o la EC2 no responde): pon el video de respaldo y dilo con humor: «El wifi de un evento es el peor lugar del mundo para depender de MQTT. Por eso traje la grabación del ensayo.» Narra encima con este mismo guion.*

*Si preguntan si la v2 es mala en general o solo en la demo: en todo el set de prueba, con fallas que no vio al entrenar, la v1 detecta el 21 % de las fallas y la v2 el 16 %; la v1 alerta en el 13 % de los clips y la v2 en el 10 %. Los clips de la flota se eligen para que la demo sea repetible.*

---

## 27 · Cinco recomendaciones
<!-- id: llevo -->
**1:05** · 4 clics · *reloj: 23:10 al entrar*

"Me quedan unos minutos, así que les dejo cinco cosas. Y les advierto: casi nadie las hace el lunes. Pero los que las hacen duermen más tranquilos."

"La primera: traten el modelo como cualquier otro artefacto, con versión, digest y receta."

**[CLIC]** "La segunda: optimicen para cada chip, y midan en el chip de verdad."

**[CLIC]** "La tercera: desplieguen por rings, con un gate que mire al modelo, no solo al proceso."

**[CLIC]** "La cuarta: diseñen pensando en que no va a haber red. Cola local y decisiones locales."

**[CLIC]** "Y la quinta: que el modelo les cuente lo que decide, pero que el dato crudo se quede en el equipo."

*Si el reloj marca 23:35 o menos al llegar aquí (+0:25), cuenta lo que pasó en el primer ensayo, que es real: «¿Saben qué fue lo primero que se me dañó? La primera vez que monté esto en AWS, ninguna bomba arrancaba. Horas buscando, y era que el instalador de Greengrass decide el formato del archivo de configuración por la extensión… y mi archivo no tenía extensión. Una línea. Por eso se ensaya en el equipo de verdad.»*

---

## 28 · La frase final: ¿esta bomba está fallando?
<!-- id: final -->
**0:45** · 2 clics · *cierre circular: vuelven los audios del principio*

"¿Se acuerdan de la pregunta del principio?" *(señala)* "¿Esta bomba está fallando?"

*(▶ bomba B, tres o cuatro segundos, la detienes)*

"Ustedes la oyeron. Desde la nube, nadie la oyó… y no hacía falta."

**[CLIC]** "Esto fue lo único que salió de la estación: la bomba 3, versión 1.0.0, alerta, con el score por encima del umbral. Unos cientos de bytes. El audio se quedó allá."

**[CLIC]** "Porque uno no necesita ver el modelo. Necesita que el modelo le cuente." *(pausa)*

"Y les dejo una última pregunta. Si mañana uno de sus modelos deja de oír… ¿quién se va a enterar primero? ¿Ustedes… o la vereda que se quedó sin agua?" *(pausa larga antes de pasar)*

*La línea de la lámina es la que imprimió la terminal en el ensayo: score 0.42 contra un umbral de 0.34.*

---

## 29 · Recursos y contacto
<!-- id: recursos -->
**0:15** · sin clics

"Todo lo que vieron está en el repo de ese QR: la demo con el paso a paso, las láminas y este guion. Tómenle foto."

*El QR lleva a https://github.com/alejandro945/mlops-a-ciegas (público desde el 12 de octubre; verificado leyendo el QR de la lámina). Si lo necesitas suelto, está en talk/assets/qr-repo.png y qr-repo.svg.*

---

## 30 · Gracias
<!-- id: cierre -->
**0:15** · sin clics

"Muchas gracias." *(espera el aplauso)* "Con todo gusto respondo sus preguntas."

*Anexos: la tecla A abre A1; las flechas los recorren; M o Esc te devuelven. A1 el evento, A2 el rollback paso a paso, A3 qué revierte Greengrass solo, A4 permisos y costo, A5 de la demo a producción, A6 qué método de drift, A7 regulación, A8 fuentes, A9 golden signals, A10 audio crudo contra eventos. Más respuestas en «Preguntas difíciles», al final de este archivo.*

---

## A1 · El evento de la demo, campo por campo
<!-- id: a1 -->
*Si preguntan qué lleva exactamente el evento. M para volver.*

"Cada mensaje dice qué bomba decidió, con qué versión del modelo y la huella exacta de ese modelo. Trae un número de secuencia y la hora en que decidió. Qué audio escuchó, el score, el umbral de esa versión y si alertó o no. Un resumen de cómo venía la entrada, la latencia… y la verdad del clip, que solo existe en la demo."

"La hora de llegada la pone la regla de IoT. Si le restan la hora de la decisión, sale lo que la estación estuvo sin red."

---

## A2 · El rollback automático, paso a paso
<!-- id: a2 -->
*Úsalo mientras esperas la alarma del acto 3. Dura un minuto. M te devuelve a la demo.*

"Mientras esperamos, les cuento qué está pasando ahora mismo, sin que yo toque nada."

"Yo mandé la 2.0.0 al ring 0. La bomba 1 se trajo su desired state, bajó los archivos de S3, revisó el digest e instaló. Para Greengrass, todo salió bien."

"Pero la bomba suena con falla y la versión nueva no avisa. Cada uno de esos mensajes pasa por la regla, cae en CloudWatch, y el filtro va contando: una falla que nadie oyó, otra, otra…"

"Cuando en un minuto se juntan ocho, salta la alarma y llama a la Lambda. La Lambda le pregunta a Parameter Store cuál fue la última versión buena, le responde 1.0.0, y la vuelve a desplegar solo en el ring 0."

"Fíjense que yo solo aparezco en el primer paso. De ahí en adelante, nadie toca nada."

*El umbral de la alarma (fallas no oídas por minuto) es la variable de Terraform alarm_threshold, que en Actions viene de la variable del repo ALARM_THRESHOLD (8 por defecto). Con estos clips, la v2 deja pasar unas 12 por minuto. La alarma solo actúa cuando cambia de estado: antes de subir, tiene que estar en OK.*

---

## A3 · ¿Qué revierte Greengrass solo?
<!-- id: a3 -->
*Si preguntan por qué hace falta el gate si Greengrass ya revierte.*

"Greengrass sí se devuelve solo en tres casos: si alguien cambió un archivo en S3 y el digest no cuadra; si el componente no instala o no arranca, porque por defecto hace rollback; y si fallan muchos equipos del ring, porque cancela el despliegue."

"Pero hay un caso que no ve: un modelo que corre perfecto y decide mal. Para Greengrass eso salió bien. Ese caso solo lo ven los eventos del modelo y una alarma que los mire."

*Fuentes: https://docs.aws.amazon.com/greengrass/v2/developerguide/component-recipe-reference.html (Digest) · https://docs.aws.amazon.com/greengrass/v2/APIReference/API_DeploymentPolicies.html (ROLLBACK por defecto) · https://docs.aws.amazon.com/cli/latest/reference/greengrassv2/create-deployment.html (abortConfig).*

---

## A4 · Permisos y costo
<!-- id: a4 -->
*Si preguntan por permisos o por cuánto cuesta.*

"Cada pieza tiene lo mínimo. La bomba solo puede leer su bucket y solo puede publicar en su tema, con su propia identidad. La regla solo escribe en sus logs. Y la Lambda solo puede crear el despliegue y leer el parámetro."

"¿Y cuánto cuesta? Lo que más pesa es la EC2 que hospeda las cinco bombas; después vienen los mensajes de IoT Core, Greengrass, CloudWatch y Lambda. La cifra exacta la saco de Cost Explorer. Y para no pagar de más, todo se baja con un destroy desde GitHub Actions."

---

## A5 · De la demo a producción
<!-- id: a5 -->
*Si preguntan qué cambia para una flota real.*

"Cambiarían cinco cosas. En vez de un mensaje por clip, un resumen por minuto, y el detalle solo cuando algo cambia. La cola se va a disco. El agente pasa a la versión liviana en los equipos pequeños. El canary deja de ser una sola estación y se compara contra el ring. Y la verdad del clip, que aquí ya la sabemos, en producción llega tarde, con la orden de mantenimiento."

---

## A6 · ¿Qué método de drift uso?
<!-- id: a6 -->
*Si preguntan cómo medir el drift.*

"Depende del dato. PSI sirve para rangos o categorías, pero sus umbrales son más costumbre que estadística. Kolmogorov-Smirnov sirve con pocas muestras; con muchas, da falsas alarmas. Wasserstein dice cuánto se movió la distribución. Y Jensen-Shannon queda siempre entre cero y uno, que es cómodo para alertar."

"En la demo uso algo más sencillo: qué tan lejos está cada clip de la huella del sonido normal. Con la otra velocidad, en el set de prueba, pasa de 0,76 a 1,07."

*En el ensayo, con `./demo/domain.sh pump-05 shifted`, la entrada de la bomba 5 subió de ~0,8 a entre 1,6 y 2,2 desde el primer clip, y aparecieron alertas falsas. En el dashboard, el widget de la entrada muestra el promedio de la flota y la peor bomba: la deriva de una sola bomba se ve en la segunda serie.*

---

## A7 · Regulación
<!-- id: a7 -->
**3 clics** · *si preguntan quién más va a pedir cuentas*

"En Europa, el AI Act les pide a los sistemas de alto riesgo que registren eventos solos durante toda su vida, que los guarden al menos seis meses y que los sigan monitoreando después de salir al mercado. Para alto riesgo aplica desde diciembre de 2027 o agosto de 2028, según el caso."

**[CLIC]** "En Estados Unidos está el marco de riesgo de IA del NIST. Es voluntario, pero se volvió el idioma común."

**[CLIC]** "Y la ISO 42001, que es como la 27001 pero para IA, y se puede certificar."

**[CLIC]** "Y si se fijan, todos piden lo mismo que uno necesita para operar: saber qué corre, qué decidió y cómo devolverse."

*Si preguntan por Colombia: el AI Act se aplica a lo que se pone en el mercado de la UE, se fabrique donde se fabrique. Verifica en EUR-Lex el número y las fechas del Reglamento (UE) 2026/1744 antes de subir.*

---

## A8 · Fuentes
<!-- id: a8 -->
*Si piden los papers y los datos. Los audios y las cifras salen de MIMII DUE (Tanabe et al., Hitachi, 2021), bombas, licencia CC BY-NC-SA 4.0. Las fuentes de AWS no van en láminas: están en este guion y en el README de la PoC.*

"Todo está aquí y en el repo. Los audios son de MIMII DUE, de Hitachi, con licencia abierta no comercial."

---

## A9 · Las golden signals de un modelo
<!-- id: senales -->
*Si preguntan qué mirar en el dashboard.*

"Los que venimos de SRE conocemos las golden signals de un servicio: latencia, tráfico, errores y saturación. Las de un modelo, con la bomba, serían: ¿qué está decidiendo? ¿Con cuánta seguridad? ¿Lo que le llega se parece a lo que aprendió? ¿Y qué versión corre dónde? Ninguna sola alcanza; hay que mirarlas juntas."

---

## A10 · Audio crudo contra eventos, con mil bombas
<!-- id: costo -->
**2 clics** · *si preguntan por qué no mandar el audio a la nube*

"Si mandáramos el audio crudo de mil bombas, serían 2,76 terabytes al día."

**[CLIC]** "Un mensaje cada 10 segundos por bomba: 8,64 millones de mensajes al día."

**[CLIC]** "Y un resumen por minuto: 1,44 millones. Y el audio, quietico en la estación."

*La PoC manda un evento por clip, cada 3 s, porque son cinco bombas. Las cuentas están al pie de la lámina.*

---

## Tiempos por bloque

| Bloque | Láminas | Duración | Reloj al terminar |
|---|---|---|---|
| Apertura | 1–6 | 3:40 | 3:40 |
| 01 · El problema | 7–11 | 3:00 | 6:40 |
| 02 · El patrón | 12–15 | 2:50 | 9:30 |
| 03 · Los seis pasos | 16–23 | 6:55 | 16:25 |
| 04 · Demostración | 24–26 | 6:45 | 23:10 |
| Cierre | 27–30 | 2:20 | 25:30 |
| **Total** | | **25:30** | |

Dentro de la demo: mapa 0:20, intro de las terminales 0:20, acto 1 1:00, acto 2 1:20 (con el despliegue de la v2 lanzado durante la espera), acto 3 2:45 y remate 0:15. El acto 3 es lo único que no controlas: si en el ensayo el rollback pasa de 2:30, lleva el tope y el video listos. La anécdota de la lámina 27 solo entra si vas adelantado.

## Antes de subir

**Una hora antes**
- EC2 encendida y las cinco bombas *Healthy*: `aws greengrassv2 list-core-devices --query 'coreDevices[].[coreDeviceThingName,status]' --output table`.
- Toda la flota en 1.0.0: los dos thing groups con su despliegue en ACTIVE (la lámina 23 lo muestra así).
- `/station/last_good_version` = 1.0.0.
- Las cinco bombas suenan normal: `./demo/fault.sh pump-0N off` y `./demo/domain.sh pump-0N normal`.
- Las cinco conectadas a la red `station` (`docker network inspect station`).
- La alarma `station-missed-faults` en OK. Si quedó en ALARM del ensayo, no va a disparar otra vez: solo actúa cuando cambia de estado.

**En el escenario**
- `./demo/watch.sh` corriendo con letra grande; el dashboard `station` abierto (15 minutos, refresco de 10 s); la terminal de Session Manager en la EC2 limpia, con los comandos de la demo a mano.
- El video de respaldo abierto, cortado por actos y en pausa.
- Los dos botones de audio probados con el sonido de la sala.
- El deck en pantalla completa (F); las notas (N) en tu pantalla, no en la proyectada.
- Un reloj visible y agua.

## Preguntas difíciles

*Responde corto, en una o dos frases, y si hace falta abre el anexo. Si no sabes algo, dilo: «no lo he medido, pero así lo mediría».*

- **«¿Y SageMaker Neo? ¿No es eso lo de compilar por chip?»** "Lo probé con este modelo y no compiló tal cual: no soporta uno de los operadores que trae scikit-learn. Cuando lo reescribí, sí compiló, pero el resultado necesita su propio runtime, DLR, que no se actualiza desde 2021. Y cuando AWS cerró Edge Manager en 2024, su recomendación fue justo ONNX Runtime en el equipo y Greengrass para desplegar. Eso es lo que vieron."
- **«¿Por qué no despliegas el INT8?»** "En la CPU de la demo ahorra poco: el clip pasa de 14,4 a 12,7 milisegundos, porque el tiempo se va preparando el audio. En un equipo con NPU sí valdría la pena, con un artefacto por cada tipo de chip."
- **«¿Y AWS Wavelength?»** "Wavelength acerca el cómputo a la red 5G del operador, pero sigue necesitando señal, y hoy no hay zonas en Latinoamérica. Para una estación sin red, el modelo tiene que estar en el equipo."
- **«¿Por qué no Kubernetes en cada estación?»** "En un equipo pequeño, un agente que baja componentes alcanza y pesa mucho menos. Si la estación es una planta grande, ahí sí: Outposts con EKS local."
- **«En producción no sabes si la bomba fallaba.»** "Cierto, esa verdad solo existe en la demo. En producción se compara el canary contra el resto de la flota, y la confirmación llega después, con la orden de mantenimiento."
- **«¿Por qué AUC y no exactitud?»** "Porque cuando cambia la velocidad todos los scores suben, y la detección puede subir junto con las falsas alarmas. La AUC mide si el modelo separa una bomba sana de una que falla, sin depender del umbral."
- **«¿Por qué un autoencoder y no un clasificador?»** "Porque las fallas son raras y no tienes ejemplos de todas. Es más fácil aprender cómo suena lo normal y avisar cuando algo suena distinto."
- **«¿Escogiste la v2 para que fallara en la demo?»** "Los clips de la demo sí están escogidos para que sea repetible. Pero en todo el set de prueba, con fallas que no vio al entrenar, la v1 detecta el 21 % y la v2 el 16 %."
- **«¿Se pierden eventos sin red?»** "En los ensayos no se perdió ninguno: revisé la secuencia de cada bomba y no tenía huecos. Lo que sí pasa es que a veces llega alguno repetido, porque MQTT con QoS 1 entrega 'al menos una vez'."
- **«¿Cuánto cuesta la PoC?»** "Lo que más pesa es la EC2; la cifra exacta la saco de Cost Explorer." (A4)
- **«¿Qué pasa si la cola se llena?»** "Empieza a rechazar mensajes nuevos. Para horas o días sin red, la cola tiene que ir a disco."
- **«¿Por qué CloudWatch Logs y no una base de series de tiempo?»** "Para el gate, un filtro de métrica alcanza. Si quieres análisis, otra regla de IoT puede mandar los mismos eventos a S3."
- **«¿Esto sirve con otra nube?»** "El patrón de la lámina 14 no depende de ninguna nube. Lo de AWS es una forma de construirlo."
- **«¿Cómo firmas el modelo?»** "Greengrass verifica el digest de cada archivo. Para firma y procedencia hay un estándar abierto, OpenSSF Model Signing, sobre Sigstore."
- **«¿Cuántas bombas aguanta la PoC?»** "Cada bomba usó unos 220 MB, y las cinco juntas 1,4 GB. Lo que limita es la memoria, porque cada agente es una JVM."
- **«¿Seguro que el audio no sale?»** "El componente lee el audio en modo solo lectura, y sus permisos solo le dejan publicar en un tema."
- **«¿Por qué un evento cada 3 s si la cuenta dice 10?»** "Porque en la demo necesito que pasen cosas rápido. La cuenta es para mil bombas."
- **«¿Por qué no SageMaker AI en la demo?»** "En vivo, entrenar es lo menos interesante. Un script en el portátil hace lo mismo y cabe en una semana."

## Pendientes antes de la charla

- La infraestructura está abajo desde el 12 de octubre (destroy). El día anterior: Actions → infra → Run workflow → apply; en la EC2, `fetch-poc`, `./fleet/build.sh` y `./fleet/up.sh`; desde el portátil, `./demo/publish.sh 1.0.0`, `2.0.0` y `./demo/deploy.sh 1.0.0 all`. En el ensayo todo eso tomó unos 15 minutos.
- Grabar el video de respaldo, cortado por actos.
- Cronometrar la charla completa en un ensayo con la EC2 y ajustar donde haga falta.

## Fuentes de lo que dices en voz alta

- Gartner, 28 ago 2025: PC con IA 15,6 % (2024), 31 % (2025), 54,7 % (2026, proyección).
- MIMII DUE: Tanabe et al., Hitachi (2021), arXiv:2105.02702, doi:10.5281/zenodo.4740355. Bombas, `dev_data_pump`, CC BY-NC-SA 4.0.
- Cuentas (sin fuente externa): 16 000 muestras/s × 2 B = 32 000 B/s ≈ 115 MB por hora ≈ 2,76 GB al día por bomba; × 1 000 = 2,76 TB al día. Un evento cada 10 s = 8 640 por bomba al día; × 1 000 ≈ 8,64 M. Un resumen por minuto = 1 440 por bomba al día; × 1 000 ≈ 1,44 M.
- AUC como probabilidad de que un positivo al azar quede por encima de un negativo al azar: Fawcett, *An introduction to ROC analysis*, Pattern Recognition Letters (2006).
- Cifras medidas: `poc-devopsdays/build/metrics.json` y `device_bench.json`, vía `talk/tools/metrics.py` (AUC 0,69 → 0,57; falsas alarmas 6 % → 18 %; detección v1 21 %, v2 16 %; INT8 464 → 127 KB, 14,4 → 12,7 ms en el equipo, 98 % de decisiones iguales).
- SageMaker Neo y Edge Manager: fin de Edge Manager el 26 de abril de 2024 y la recomendación de ONNX y Greengrass V2, https://docs.aws.amazon.com/sagemaker/latest/dg/edge-eol.html · frameworks de Neo para el borde (ONNX hasta 1.7), https://docs.aws.amazon.com/sagemaker/latest/dg/neo-supported-devices-edge-frameworks.html · equipos soportados, https://docs.aws.amazon.com/sagemaker/latest/dg/neo-supported-devices-edge-devices.html · la prueba, en la evidencia del ensayo del 12 de octubre.
- AWS Wavelength: zonas solo en EE. UU., Canadá, Reino Unido, Japón, Marruecos y Senegal, https://aws.amazon.com/wavelength/locations/ · Local Zones (Bogotá «announced», Buenos Aires disponible), https://aws.amazon.com/about-aws/global-infrastructure/localzones/locations/
- Documentación de AWS (dicha en voz alta, nunca en una lámina):
  - Cola `mqtt.spooler` del nucleus, en memoria y de 2,5 MB por defecto: https://docs.aws.amazon.com/greengrass/v2/developerguide/greengrass-nucleus-component.html
  - Cola en disco: https://docs.aws.amazon.com/greengrass/v2/developerguide/disk-spooler-component.html
  - Nucleus lite, 5 MB de almacenamiento y menos de 15 MB de RAM: https://docs.aws.amazon.com/greengrass/v2/developerguide/greengrass-nucleus-lite-component.html
  - Digest calculado al crear la versión y verificado en el equipo: https://docs.aws.amazon.com/greengrass/v2/developerguide/component-recipe-reference.html
  - `failureHandlingPolicy` = `ROLLBACK` por defecto: https://docs.aws.amazon.com/greengrass/v2/APIReference/API_DeploymentPolicies.html
  - `abortConfig` y `jobExecutionsRolloutConfig`: https://docs.aws.amazon.com/cli/latest/reference/greengrassv2/create-deployment.html
  - EKS local en Outposts sin red: https://docs.aws.amazon.com/eks/latest/userguide/eks-outposts-network-disconnects.html
  - Greengrass en Docker: https://docs.aws.amazon.com/greengrass/v2/developerguide/run-greengrass-docker.html
- Métodos de drift (A6): documentación de Evidently y NannyML; crítica a los umbrales del PSI: arXiv:2303.01227.
- Regulación (A7): Reglamento (UE) 2024/1689, arts. 12, 19 y 72, con las fechas del Reglamento (UE) 2026/1744; NIST AI 100-1; ISO/IEC 42001:2023.
