# Guion · MLOps a ciegas · DevOpsDays Bogotá 2026

**Duración:** 32:45 la versión completa (tope: 35), 29:55 la de 30 con los cortes del final. **Láminas:** 34 más 8 anexos; cuatro son divisores y pasan en segundos. Plantilla oficial de DevOpsDays Bogotá 2026.

**De qué va:** cómo gobernar un modelo de IA que corre donde no llega el plano de control. El hilo es una estación de bombeo: un modelo que escucha bombas en una vereda, sin red y sin SSH. Las láminas nombran y dibujan servicios de AWS, pero ninguna cita a AWS: los datos de la documentación se dicen en voz alta y su enlace queda en la nota.

Este archivo es la fuente de las notas del presentador: cada sección con `<!-- id: … -->` aparece al presionar **N** en su lámina. Las cifras medidas se escriben `{{M:clave}}` y salen de `poc-devopsdays/build/metrics.json`; mientras no haya medición real, dicen «por medir». Si cambias algo aquí, regenera el deck:

```
AWS_ICONS=<ruta al paquete de íconos> python3 talk/tools/build_deck.py
```

**Cómo leerlo:**
- Lo que va entre comillas es lo que dices.
- **[CLIC]** avanza un paso de la lámina.
- *(pausa)* es silencio.
- Lo que va en cursiva es para ti, no para la sala.
- El tiempo en negrita es lo que dura la lámina, no la hora del reloj.

---

## La forma: lo que tomé de las charlas de Freddy Vega

La forma, no las palabras. No copies frases suyas.

| Lo que hace Freddy | Cómo lo uso aquí |
|---|---|
| Arranca con una pregunta a la sala, sin saludo | Dos audios de bombas y «¿Esta bomba está fallando?», con votación a mano alzada (lámina 2) |
| Promete algo concreto: «les voy a enseñar…» | «Hoy les voy a enseñar a gobernar un modelo que corre donde no llega tu plano de control» (lámina 2) |
| Desarma creencias con datos: «no son opiniones, son datos» | El panel en verde contra la AUC medida en la PoC (lámina 11); «más datos, mejor modelo» contra la v2 en vivo (acto 3) |
| Preguntas a mano alzada que todos pueden contestar | Tres: el pager (12), el rollback del viernes (22) y la versión en cada equipo (25) |
| Anticipa la objeción: «muchos dirán…» | «Mándalo a la nube» (5), «Greengrass ya hace rollback» (21), «en producción no sé si la bomba fallaba» (24) |
| Provoca antes del resumen | «La mayoría no las va a hacer el lunes» (31) |
| Cierra contando | «Esas son las cinco cosas» (31) |
| El final vuelve al principio y termina con una pregunta | Los audios otra vez, la línea del evento y «¿quién se entera primero: ustedes, o la vereda que se quedó sin agua?» (32) |
| Frases cortas, humor con voces | El jefe: «¿Y el modelo cómo va?» — «Todo verde, jefe» (11) |

## El hilo: la estación

Una empresa de acueducto, **inventada para la charla**, tiene estaciones de bombeo en veredas con red intermitente. En cada estación, un equipo pequeño escucha las bombas con un micrófono y un modelo avisa cuando una empieza a sonar distinto. El audio nunca sale de la estación; sale un evento de unos cientos de bytes.

- **Lámina 2:** la sala oye la bomba A y la bomba B y vota. La respuesta (la B falla) llega en el acto 1 de la demo.
- **Láminas 10 y 11:** la estación y su problema: el panel en verde y el modelo que ya no distingue.
- **Pasos 1 a 6 (láminas 18 a 24):** la bomba ocupa una línea por paso, marcada *La bomba*.
- **Demo:** la bomba 3 falla y se queda sin red; la 5 cambia de velocidad; la v2 no oye la falla de la 1 y vuelve sola a la v1.
- **Lámina 32:** vuelven los audios y la línea del evento de la bomba B.

Los sonidos son reales (MIMII DUE, Hitachi, CC BY-NC-SA 4.0). La empresa, las veredas y el jefe son inventados. Dilo así cuando toque.

---

## 1 · MLOps a ciegas
<!-- id: portada -->
**0:10** · sin clics

*En pantalla mientras te presentan. No saludes: cuando te den la palabra, pasa a la lámina 2 y arranca con la bomba A. Antes de subir, prueba que el audio del deck sale por los parlantes de la sala.*

---

## 2 · ¿Esta bomba está fallando?
<!-- id: suena -->
**1:25** · 1 clic · *sin «buenos días»: lo primero que oye la sala es una bomba*

"Bomba A." *(dale ▶ a la A; deja sonar cinco o seis segundos y detenla)*

"Bomba B." *(dale ▶ a la B; cinco o seis segundos y detenla)*

"¿Alguna de estas dos bombas está fallando?"

**[CLIC]** "Levanten la mano. ¿La A?" *(cuenta)* "¿La B?" *(cuenta)* "¿Las dos?" *(cuenta)*

"No les voy a decir todavía. La respuesta llega más adelante, en vivo."

"Los sonidos son reales: bombas industriales que grabó Hitachi. La empresa es inventada para la charla: un acueducto con estaciones de bombeo en veredas. La red va y viene. No hay nadie cerca. En cada estación, un equipo pequeño escucha las bombas con un micrófono, y un modelo avisa cuando una empieza a sonar distinto."

"Ustedes acaban de hacer lo que hace ese modelo: oír y decidir. Pero ustedes estaban aquí. Desde la nube, nadie oyó nada." *(pausa)*

"Por eso la charla se llama MLOps a ciegas. Hoy les voy a enseñar a gobernar un modelo que corre donde no llega tu plano de control: cómo llega, cómo vuelve atrás y cómo te cuenta lo que decide. Sin SSH, y sin que el audio salga de la estación."

*Mientras suena un audio, una tecla o un clic lo detiene y no cambia de lámina. Si los botones dicen «audio pendiente», faltan talk/assets/audio/pump-a.wav y pump-b.wav. La atribución de MIMII DUE está al pie.*

---

## 3 · ¿Cuántas PC nuevas traen chip para IA?
<!-- id: cien -->
**0:40** · 2 clics

"¿Y por qué debería importarles un modelo en una estación de bombeo? Porque los modelos se están saliendo de la nube. Dos números. No son míos: son de Gartner y de IDC."

"De cada cien computadoras nuevas que se vendieron en 2024, dieciséis traían un chip para correr IA."

**[CLIC]** "En 2025, treinta y una."

**[CLIC]** "Para este año, Gartner proyecta cincuenta y cinco. Más de la mitad. Tres veces y media en dos años."

*Fuente: Gartner, 28 de agosto de 2025: 15,6 % (2024), 31 % (2025), 54,7 % (2026, proyección).*

---

## 4 · ¿Cuánto dinero se está invirtiendo en edge?
<!-- id: inversion -->
**0:25** · sin clics · *corte para 30 min*

"Segundo número. IDC calcula que el gasto mundial en edge computing pasa de doscientos sesenta y un mil millones de dólares en 2025 a trescientos ochenta mil millones en 2028."

"Y América Latina está entre las regiones donde más rápido crece. Es decir: aquí."

*Fuente: IDC, 17 de marzo de 2025; 2028 es proyección. En la versión de 30 min, salta esta lámina.*

---

## 5 · ¿Por qué la IA se está saliendo de la nube?
<!-- id: memes -->
**1:25** · 2 clics · *deja que la sala se ría antes de hablar*

"¿Y por qué se sale de la nube? Depende del caso. Se los explico en el idioma universal: memes."

*Meme 1 · latencia.* "Nadie… absolutamente nadie… El carro autónomo: 'dame un segundo, se lo pregunto a la nube'." *(pausa)* "Cuando la decisión es de milisegundos, la ida y vuelta no alcanza."

**[CLIC]** *Meme 2 · sin conexión.* "Técnico, tres de la mañana, en la planta: '¿cómo cambio este rodamiento?'. La nube: 'Sin conexión. Intente más tarde'." *(pausa)* "En una vereda pasa igual. Sin red no puede significar sin respuestas."

**[CLIC]** *Meme 3 · privacidad.* "Y mi favorito: tu reloj, cada segundo, subiendo tus latidos a internet." *(pausa)* "Lo sensible no sale del equipo."

"Ahora piensen en la bomba. Muchos dirán: 'mándame el audio a la nube y lo analizo allá'. Un micrófono a dieciséis kilohercios son ciento quince megas por hora. Por bomba. Por la red de una vereda. Y es el sonido de una instalación de la empresa: no tiene por qué salir de ahí."

*Corte para 30 min: del meme 1 dices solo «la ida y vuelta no alcanza» y haces clic.*

*Cuenta (PLAN §1): 16 000 muestras por segundo × 2 bytes = 32 000 B/s ≈ 115 MB por hora.*

---

## 6 · ¿Quién soy?
<!-- id: quien -->
**0:25** · sin clics

"Antes de seguir: soy Alejandro Varela, Cloud Engineer. Trabajo con inferencia en el edge e IoT industrial. [Un dato personal corto, algo humano, diez segundos.]"

"Todo lo que van a ver hoy está montado en AWS, con servicios que pueden usar el lunes."

*La foto sale de talk/assets/photo.jpg y el LinkedIn de la variable LINKEDIN al generar el deck.*

---

## 7 · ¿Qué van a aprender hoy?
<!-- id: agenda -->
**0:25** · sin clics

"Cuatro partes. Uno, el problema: un modelo que escucha bombas, sin red y sin nadie cerca. Dos, el patrón: qué lleva el equipo y qué hace falta para gobernarlo. Tres, los seis pasos, de entrenar a monitorear, uno por vez. Y cuatro, en vivo: una bomba falla y otra se queda sin red."

---

## 8 · 01 · El problema
<!-- id: div1 -->
**0:05** · *divisor: no lo leas* · *reloj: 4:55 (versión de 30: 4:05)*

"Empecemos por el problema."

---

## 9 · ¿Qué tenemos cuando el modelo corre en la nube?
<!-- id: nube -->
**0:40** · sin clics · *los puntos recorren el lazo*

"Imaginen que mandan el audio a la nube. Tendrían esto, y está bastante resuelto. El modelo vive detrás de un endpoint. Cada petición y cada respuesta pasan por ahí: se capturan, se comparan con la línea base del entrenamiento, suena una alerta si algo se desvía, y se reentrena."

"Es un lazo cerrado, y funciona por una razón muy simple:" *(señala la frase de la izquierda)* "todo pasa por el endpoint."

---

## 10 · ¿Y cuando baja a la estación?
<!-- id: edge -->
**1:05** · 4 clics · *una restricción por clic; dila como sale en pantalla*

"Ahora bajemos el modelo a la estación, al lado de la bomba. Mismo lazo… pero ya nada pasa por un endpoint."

**[CLIC]** "Uno: equipos de varias generaciones. Una estación tiene un equipo ARM, otra un x86 de hace años, la nueva trae NPU. El mismo modelo no corre igual en los tres."

**[CLIC]** "Dos: red intermitente. Se va la señal en la vereda, y el lazo de la nube se apaga."

**[CLIC]** "Tres: mil bombas, y ninguna con SSH. Nadie va a entrar equipo por equipo a ver qué tiene."

**[CLIC]** "Y cuatro: el audio no puede salir de la estación. No cabe, y no debe."

"El MLOps de la nube asume que todo pasa por ti. En la estación, nada pasa por ti."

---

## 11 · ¿Si el panel está en verde, el modelo está bien?
<!-- id: tablero -->
**1:30** · 3 clics · *el mito central de la charla: ve despacio*

"Entonces, ¿cómo sabes si el modelo de la estación está bien? Hacemos lo de siempre: miramos el panel."

**[CLIC]** "Panel del equipo. Servicio del modelo: activo. CPU: normal. Memoria: normal. Todo en verde."

*Voz del jefe:* "'¿Y el modelo de la estación cómo va?' — 'Todo verde, jefe'."

**[CLIC]** "Ahora la pregunta que importa: ¿distingue una falla de una bomba sana? Eso se mide con la AUC. Para los que no son de datos: le das al modelo un clip de una bomba sana y uno de una que falla. La AUC dice qué tan seguido le pone más puntaje al que falla. Uno es siempre. Cero coma cinco es lanzar una moneda."

"Con la velocidad con la que se entrenó: {{M:v1.auc_source}}. Le cambian la velocidad a la bomba: {{M:v1.auc_target}}."

"Mismo modelo, mismo umbral, cero errores. Y las falsas alarmas pasan de {{M:v1.false_alarm_source}} a {{M:v1.false_alarm_target}}."

**[CLIC]** "El equipo está sano. El modelo ya no distingue." *(pausa larga)*

"No son opiniones, son datos: lo medí en la PoC, con el audio real de las bombas que van a oír en la demo."

"Un servicio roto hace ruido. Un modelo que dejó de oír responde a tiempo, sin errores… y con un 200 OK."

*Por qué AUC y no «fallas detectadas»: con la otra velocidad todos los scores suben, y la detección puede subir junto con las falsas alarmas. La AUC mide si el modelo separa una bomba sana de una que falla, sin depender del umbral.*

---

## 12 · A mano alzada 1
<!-- id: reflexion1 -->
**0:30** · sin clics · *la barra de abajo cuenta cinco segundos*

"Pregunta a mano alzada. ¿A quién le ha sonado el pager por un modelo?" *(espera las manos)*

*Si hay pocas:* "Pocas manos. ¿Y por un disco lleno?" *(risas)* "Exacto. El pager suena por el proceso. Por el modelo, casi nunca."

*Si hay muchas:* "Bienvenidos al club. ¿Y cuántos se enteraron por el cliente antes que por el pager?"

"Hoy vamos a hacer que el modelo también pueda despertar a alguien."

---

## 13 · 02 · El patrón
<!-- id: div2 -->
**0:05** · *divisor* · *reloj: 8:45 (versión de 30: 7:55)*

"¿Qué hace falta para gobernarlo? Primero, abramos el equipo."

---

## 14 · ¿Qué lleva el equipo de la estación por dentro?
<!-- id: equipo -->
**0:50** · 3 clics · *una capa por clic*

"Abajo, el micrófono sobre la bomba: el audio entra y no sale. Y el modelo con su runtime: decide en milisegundos, con o sin red."

**[CLIC]** "Encima, el modelo no llega como un archivo suelto: llega como un artefacto verificable. Versión y hash. Si alguien lo tocó, no se instala."

**[CLIC]** "Luego, un agente. Nadie le empuja nada a la estación: el agente trae el estado deseado cuando hay red."

**[CLIC]** "Y arriba, la pieza que falta en casi todos lados: una cola de eventos. Cada decisión queda guardada hasta que haya red."

---

## 15 · ¿Qué hace falta para gobernarlo?
<!-- id: flujo -->
**1:35** · 6 clics · *una pieza por clic; la leyenda de arriba se enciende con cada una*

*Paso 0: «copiar el modelo… y cruzar los dedos».* "Así se despliegan modelos en muchos lados hoy: copias el archivo al equipo… y cruzas los dedos. Yo lo he hecho." *(risas)*

"No hace falta una herramienta mágica. Hacen falta cinco piezas, y ninguna depende de una nube en particular."

**[CLIC]** "Uno: optimizar por chip. Se entrena una vez y se prepara para cada familia de hardware. Es la pieza que todo el mundo se salta en los diagramas."

**[CLIC]** "Dos: artefacto verificable. Cada versión, con su huella, en un registro donde nada se sobrescribe."

**[CLIC]** "Tres: estado deseado. La central declara qué debería tener cada equipo, y el equipo lo trae cuando puede."

**[CLIC]** "Cuatro: evento de inferencia. El modelo deja constancia de lo que decide. Si no hay red, se encola."

**[CLIC]** "Cinco: la compuerta. Una condición que mira esos eventos y decide sola: sigue o vuelve atrás. Es el lazo rápido: minutos."

**[CLIC]** "Y con esos mismos eventos se reentrena: el lazo lento, días. Abajo, lo que atraviesa todo: identidad, mínimo privilegio, cifrado y auditoría."

"De cruzar los dedos a cinco piezas."

---

## 16 · ¿Cómo se ve esto en AWS?
<!-- id: aws -->
**1:20** · 6 clics · *misma geometría que la anterior: cada casilla es ahora un servicio*

"Mismo dibujo, en AWS. La forma no cambia: cada casilla ahora tiene nombre."

**[CLIC]** "Uno: la fábrica. SageMaker AI entrena, y de ahí sale un artefacto por chip."

**[CLIC]** "Dos: el registro es S3, un prefijo por versión. IoT Greengrass empaca el modelo como componente y calcula el digest de cada archivo."

**[CLIC]** "Tres: el estado deseado es un despliegue de Greengrass. Llega por IoT Core, con un certificado por equipo, y el nucleus lo aplica cuando hay red."

**[CLIC]** "Cuatro: el micrófono entra a la inferencia, el componente publica cada decisión y, si no hay red, el nucleus la guarda. Entra por IoT Core y una regla la deja en CloudWatch Logs."

**[CLIC]** "Cinco: la compuerta. Una alarma sobre esos eventos invoca una Lambda, que lee en Parameter Store la última versión buena y la vuelve a desplegar."

**[CLIC]** "Y seis: el lazo lento vuelve a SageMaker AI. Abajo, lo transversal: IAM, un certificado X.509 por equipo, KMS y CloudTrail."

---

## 17 · 03 · Los seis pasos
<!-- id: div3 -->
**0:10** · *divisor con la espina* · *reloj: 12:35 (versión de 30: 11:45)*

"Seis pasos: entrenar, optimizar, empaquetar, desplegar, correr sin red y monitorear. Cada uno responde una pregunta. Y en cada uno, una línea de la bomba."

---

## 18 · Paso 1 · ¿Qué sale de la nube?
<!-- id: entrenar -->
**1:10** · 3 clics

"Paso uno. ¿Qué sale de la nube? Empieza con sonido normal. Bombas reales, solo clips normales."

**[CLIC]** "SageMaker AI entrena un autoencoder: una red que aprende a rehacer el sonido normal. Si no lo puede rehacer, algo cambió. El score es el error de reconstrucción."

**[CLIC]** "Lo que sale va a S3, un prefijo por versión. Inmutable: una versión nueva es otro prefijo, nunca el mismo."

**[CLIC]** "¿Y qué sale exactamente? Cuatro archivos y una versión. El modelo en ONNX: ese es el contrato con el equipo. stats.json: la huella del sonido normal y el umbral. features.py: el mismo log-mel que en el entrenamiento. E inference.py: escucha, decide y cuenta."

"El error típico: entrenar con un preprocesamiento y servir con otro. No explota nada; el modelo solo oye distinto. Por eso features.py viaja con el modelo."

*La bomba:* "Aprende solo con sonido normal: las fallas son raras."

*En la PoC la fábrica es model/train.py en tu laptop, no SageMaker AI. Lo dices en la lámina 27.*

---

## 19 · Paso 2 · ¿Qué cabe en el chip?
<!-- id: optimizar -->
**1:10** · 3 clics

"Paso dos. ¿Qué cabe en el chip? Entrenas una vez, en 32 bits: un archivo ONNX."

**[CLIC]** "Para que quepa en el equipo, pasa por tres cosas. Se cuantiza, de 32 a 8 bits. Se fusionan y se podan capas. Y se compila para el acelerador del chip. En AWS esto vive en la misma fábrica, al lado de SageMaker AI. En la PoC solo cuantizo a INT8, con ONNX Runtime, para medir cuánto cambia."

**[CLIC]** "Y no sale un artefacto: sale uno por chip. NPU en INT8, GPU en FP16, CPU en INT8, cada uno con su herramienta. Y manda la memoria del chip: si no cabe, no corre."

**[CLIC]** "Esta es la bomba, medida. De FP32 a INT8, el archivo pasa de {{M:int8.size_fp32_kb}} a {{M:int8.size_int8_kb}}. La latencia por clip en CPU, de {{M:int8.lat_fp32_ms}} a {{M:int8.lat_int8_ms}}. Y toma la misma decisión en {{M:int8.agree_pct}} de los clips."

"El error típico: medir en tu laptop y desplegar en una NPU. Ese ya es otro modelo. Se mide en el chip, y cada artefacto estrena su propia línea base."

*La bomba:* "INT8 para el equipo pequeño."

*Si preguntan por herramientas: LiteRT y Qualcomm QNN para NPU, TensorRT para GPU de NVIDIA, ONNX Runtime y OpenVINO para CPU. La AUC del INT8 menos la del FP32, medida: {{M:int8.auc_delta}}.*

---

## 20 · Paso 3 · ¿Qué es un componente?
<!-- id: componente -->
**1:15** · 4 clics · *una anotación por clic*

"Paso tres. ¿Qué es un componente? Es la forma en que IoT Greengrass empaca software para el equipo. Esta es la receta real de la demo, tal cual."

**[CLIC]** "Uno: los artefactos, desde S3. Fíjense que la receta no trae líneas de digest. No hacen falta: Greengrass calcula el digest de cada artefacto al crear la versión del componente, y lo verifica en el equipo antes de instalar."

**[CLIC]** "Dos: el ciclo de vida, cómo arranca. Y no instala nada: las dependencias ya vienen en el equipo. Si tu componente baja librerías de internet al arrancar, en una vereda sin red no arranca."

**[CLIC]** "Tres: el umbral es configuración. Se cambia con un despliegue, sin reentrenar y sin publicar otra versión."

**[CLIC]** "Cuatro: permisos IPC. El componente solo puede publicar en un tema, estacion/eventos. Nada más."

"El error típico: corregir un archivo en S3 sin cambiar la versión. El digest ya no coincide y el despliegue falla. Una versión publicada no se toca: para cambiar algo, versión nueva."

*La bomba:* "El umbral es configuración: se cambia sin reentrenar."

*Fuente del digest (para ti, no para la lámina): referencia de recetas de Greengrass, campo Digest de Artifacts. https://docs.aws.amazon.com/greengrass/v2/developerguide/component-recipe-reference.html*

---

## 21 · Paso 4 · ¿Cómo llega a mil equipos?
<!-- id: anillos -->
**1:15** · 3 clics

"Paso cuatro. ¿Cómo llega a mil equipos sin romperlos todos un martes? Con despliegues de IoT Greengrass. Un thing group por anillo."

"Anillo cero: una estación, el canario. Recibe la versión nueva primero."

**[CLIC]** "Si pasa la compuerta, anillo uno: el resto de la flota. Y no de golpe: despliegue exponencial, cada ola llega a más equipos."

**[CLIC]** "El despliegue trae dos protecciones. abortConfig: si fallan demasiados equipos, el despliegue se cancela. Y failureHandlingPolicy en ROLLBACK, que es el valor por defecto: si un equipo no arranca la versión nueva, vuelve a la que tenía."

**[CLIC]** "Y la vuelta: la alarma ve fallas que nadie oyó y despliega la última versión buena. El anillo 1 nunca recibe la v2."

"Muchos dirán: 'pero Greengrass ya hace rollback'. Sí: de despliegues que fallan. No de modelos que se instalan perfecto y deciden mal. Para Greengrass, un modelo que no oye es un despliegue exitoso."

"El error típico: un solo thing group con toda la flota. Un clic, y la versión mala llegó a mil estaciones."

*La bomba:* "Una estación como canario."

*Fuente del valor por defecto: https://docs.aws.amazon.com/greengrass/v2/APIReference/API_DeploymentPolicies.html · abortConfig y jobExecutionsRolloutConfig: https://docs.aws.amazon.com/cli/latest/reference/greengrassv2/create-deployment.html*

---

## 22 · A mano alzada 2
<!-- id: reflexion2 -->
**0:25** · sin clics · *la barra cuenta cinco segundos*

"Otra pregunta, y aquí nadie juzga. ¿Quién ha hecho un rollback un viernes en la tarde?" *(manos, risas)*

"Exacto. Ahora imagínense hacerlo en mil estaciones… y la mitad sin red."

---

## 23 · Paso 5 · ¿Qué sigue funcionando sin red?
<!-- id: sinred -->
**1:10** · 2 clics

"Paso cinco. ¿Qué sigue funcionando sin red? Depende del tamaño de la estación."

"En un equipo pequeño, IoT Greengrass. El nucleus guarda los eventos en una cola local hasta que vuelve la red: por defecto, una cola en memoria de 2,5 megas. Stream manager, para flujos que suben solos cuando vuelve la red. Y si el equipo tiene poca memoria, el nucleus lite: escrito en C, pide 5 megas de almacenamiento y menos de 15 de RAM."

**[CLIC]** "Si la estación es una planta grande: Outposts con EKS local. El plano de control corre en el sitio y sigue sin la región. Sin red no hay IAM: entras con un certificado x.509. Y las imágenes, de un registro local que pones tú."

**[CLIC]** *La bomba, en el recuadro:* "Sin red, la estación sigue escuchando y alertando: lo que necesita para decidir ya está adentro."

"El error típico: la cola se llena. Y cuando se llena, el nucleus rechaza los mensajes nuevos. Si la red se va por horas, la cola va a disco."

*Fuentes (en voz alta, no en la lámina): cola mqtt.spooler de 2,5 MB en memoria por defecto, https://docs.aws.amazon.com/greengrass/v2/developerguide/greengrass-nucleus-component.html · cola en disco, https://docs.aws.amazon.com/greengrass/v2/developerguide/disk-spooler-component.html · nucleus lite, 5 MB de almacenamiento y menos de 15 MB de RAM, https://docs.aws.amazon.com/greengrass/v2/developerguide/greengrass-nucleus-lite-component.html · EKS local sin red (x.509; el clúster no trae registro de imágenes), https://docs.aws.amazon.com/eks/latest/userguide/eks-outposts-network-disconnects.html*

---

## 24 · Paso 6 · ¿Qué ves desde la nube?
<!-- id: monitoreo -->
**1:20** · 5 clics · *un tramo de la tubería por clic*

"Paso seis. ¿Qué ves desde la nube? Lo que el modelo te cuenta: un evento por clip, de unos cientos de bytes, que llega a IoT Core."

**[CLIC]** "Una regla de IoT lo toma. La SQL real: el evento entero, más la hora en que llegó. Llegada menos decisión: el tiempo que la estación estuvo sin red."

**[CLIC]** "La regla lo deja en CloudWatch Logs."

**[CLIC]** "Un filtro de métrica cuenta lo que importa. Este es el de la demo: la bomba fallaba y el modelo no avisó. FallasNoOidas."

**[CLIC]** "Una alarma mira esa métrica."

**[CLIC]** "Y la alarma invoca la Lambda: lee la última versión buena y la despliega al anillo 0."

"El error típico: poner la alarma sobre CPU y errores. Ya vimos que eso se queda en verde. La compuerta mira al modelo."

"Muchos dirán: 'en producción no sé si la bomba fallaba'. Cierto: ese campo solo existe en la demo. En producción la etiqueta llega tarde, con la orden de mantenimiento, y mientras tanto comparas el canario contra el resto."

*La bomba:* "Las señales de la bomba: alertas, score, entrada y versión."

---

## 25 · A mano alzada 3
<!-- id: reflexion3 -->
**0:35** · 1 clic · *la barra cuenta cinco segundos*

"Última pregunta. ¿Qué versión corre en cada equipo?" *(manos)* "Ahora bajen la mano los que tuvieron que pensarlo." *(risas)*

**[CLIC]** "Esta es la respuesta, y no necesita SSH: el estado del despliegue, por thing group. EstacionAnillo0: la bomba-01, com.estacion.Escucha 1.0.0, COMPLETED. EstacionAnillo1: de la bomba-02 a la bomba-05, la misma 1.0.0, COMPLETED."

"La pregunta se responde en la nube, no en el equipo."

*Detalle de un equipo, si lo piden: aws greengrassv2 list-installed-components --core-device-thing-name bomba-01. Antes de subir, confirma que la flota está así: la lámina muestra el estado con el que arranca la demo.*

---

## 26 · 04 · En vivo
<!-- id: div4 -->
**0:05** · *divisor* · *reloj: 21:05 (versión de 30: 20:15)*

"Suficiente teoría. Vamos a la estación."

---

## 27 · ¿Qué monté para la demo?
<!-- id: poc -->
**0:45** · sin clics

"Esto es lo que monté. No traje bombas al escenario. Cada bomba es un contenedor, en una EC2, con el nucleus real de IoT Greengrass adentro. Cinco bombas: la 1 es el anillo 0, el canario; de la 2 a la 5, el anillo 1."

"Lo que suena es audio real de bombas, de MIMII DUE. Y todo lo demás es AWS de verdad: cinco bombas, siete servicios. EC2, IoT Greengrass, IoT Core, S3, CloudWatch, Lambda y Systems Manager, por el Parameter Store."

"Lo único simulado es el equipo físico. Y la fábrica: el modelo lo entrena un script en mi laptop, no SageMaker AI."

*Si preguntan: las cinco bombas salen de tres secciones de MIMII DUE; la 1 y la 4 comparten sección, y la 2 y la 5 también, con clips distintos. Cada nucleus es una JVM: en una estación real, cada equipo tiene la suya.*

---

## 28 · ¿Cuáles son las señales doradas de un modelo?
<!-- id: senales -->
**0:35** · sin clics · *corte para 30 min*

"Los que venimos de SRE conocemos las señales doradas de un servicio: latencia, tráfico, errores y saturación."

"Las de un modelo, con la bomba. ¿Qué decide? Alertas por bomba. ¿Con cuánta seguridad? El score contra el umbral. ¿Se parece a lo que aprendió? El nivel de la entrada. ¿Qué corre dónde? La versión por equipo."

"Ninguna sola alcanza. Ya van a ver por qué."

*En la versión de 30 min, salta esta lámina: las cuatro señales las nombras al abrir la demo, señalando las columnas de watch.sh.*

---

## 29 · ¿Cómo se ve un modelo decidiendo?
<!-- id: demo -->
**7:00** · 2 clics en la lámina, después las terminales · *la lámina es el mapa; lo real está en la terminal*

*En la lámina (0:25).* "Tres actos. Uno: escuchar. La bomba 3 va a sonar como la B del principio."

**[CLIC]** "Dos: sin red. La 3 se queda sin señal. Y aparte, la 5 cambia de velocidad."

**[CLIC]** "Tres: desplegar por anillos y volver. Una versión nueva, solo para el canario." *(señala la línea de abajo)* "Y esa frase de abajo es el final de la película. No la lean todavía." *(risas)*

*Cambia a las terminales: `./demo/watch.sh` a la izquierda; a la derecha arriba, el dashboard `estacion`; a la derecha abajo, la terminal SSH a la EC2. Letra grande.*

"Esto es la estación en vivo. Cinco contenedores con Greengrass real, escuchando audio real. Cada línea es un clip que una bomba escuchó y decidió: la hora, qué bomba, qué versión, si alertó, el score contra el umbral, cómo era la entrada y en cuántos milisegundos. Esas son las señales. El audio no está ahí. Nunca sale."

**Acto 1 · Escuchar (1:00)**

*Escribe* `./demo/falla.sh bomba-03` — "Le digo a la bomba 3 que suene como la B."

*Cuando aparezca bomba-03 v1.0.0 ALERTA:* "Ahí está. ALERTA. El score pasó el umbral."

"Y esta es la respuesta del principio: la bomba B era la que estaba fallando. ¿Quién votó B?" *(manos)* "Oído de mecánico. Los de la A, tranquilos: para eso está el modelo."

"El audio no salió de la estación. Salió esta línea."

*No apagues la falla de la 3: en el acto 2, lo que llega tarde tienen que ser alertas.*

**Acto 2 · Sin red (1:40)**

*Escribe* `./demo/red.sh off bomba-03` — "Le quito la red a la estación 3. Como cuando se va la señal en la vereda."

*Espera 40 a 60 s. La 3 desaparece de watch.sh; las otras cuatro siguen.* "La 3 se calló. Las otras cuatro siguen. ¿Se rompió? No. Sigue escuchando, sigue alertando, y guarda cada evento en la cola del nucleus. La nube no sabe nada. La estación, sí."

*Escribe* `./demo/red.sh on bomba-03` — *el nucleus se reconecta solo; espera las líneas con «llegó N s tarde».* "Ahí están. Llegaron tarde, pero llegaron. Ese 'llegó tarde' es la diferencia entre cuándo decidió la bomba y cuándo llegó a la nube. No se perdió ninguna alerta."

*Escribe* `./demo/falla.sh bomba-03 off`

*Escribe* `./demo/dominio.sh bomba-05 nuevo` — "Ahora otra cosa. Alguien en operación le cambió la velocidad a la bomba 5. La bomba está sana."

*Espera unas líneas de la 5.* "Cero errores. Cero excepciones. Miren la columna de la entrada: se aleja de lo que aprendió. Si salen alertas de la 5, no es que falle: es la otra velocidad. Es la lámina del panel en verde, en vivo."

*Escribe* `./demo/dominio.sh bomba-05 normal`

**Acto 3 · Desplegar por anillos y volver (3:40)**

*Escribe* `./demo/deploy.sh 2.0.0 anillo-0` — "Versión nueva. La v2 se reentrenó con más audio. Más datos, mejor modelo… ¿cierto? Y da menos alertas: en operación están felices, ya no los despiertan tanto."

"Va solo al anillo 0: una estación, el canario. Las otras cuatro ni se enteran."

*Espera a que la bomba-01 salga en v2.0.0; señala que de la 02 a la 05 siguen en v1.0.0.* "Ahí está: la 1 corre la v2. Sin errores. Misma latencia. Para Greengrass, despliegue exitoso."

*Escribe* `./demo/falla.sh bomba-01` — "Ahora la 1 suena con falla."

*Cuando aparezca bomba-01 v2.0.0 normal … · falla no oída:* "La bomba está fallando… y la v2 dice normal. Falla no oída." *(pausa)*

"¿Qué pasó? El audio extra de la v2 incluía la semana en que una bomba ya estaba fallando. Nadie lo limpió. El modelo aprendió que fallar es normal. Corre sin errores, da menos alertas… y no oye las fallas."

*Mientras la alarma junta su minuto de datos:* "Ahora no voy a tocar nada. La compuerta trabaja sola." *Cambia al deck: tecla A y una flecha a la derecha te llevan al anexo A2. Cuenta la secuencia con la nota de A2 (un minuto). M te devuelve aquí.*

*Vuelve a watch.sh. Cuando la 1 salga en v1.0.0 con ALERTA:* "Volvió. v1.0.0. ALERTA otra vez: la falla se oye. Nadie entró por SSH. Y el anillo 1 nunca recibió la v2."

*Escribe* `./demo/falla.sh bomba-01 off`

*Vuelve a esta lámina (queda en su último paso) y dilo mirando a la sala:* "Greengrass revierte despliegues fallidos, no modelos equivocados. Esa compuerta la pones tú."

*Tope: si a los cuatro minutos de escribir deploy.sh la 1 no ha vuelto, no esperes más: «La alarma va a su ritmo; para no robarles tiempo, les muestro cómo termina», y pon el video desde la vuelta.*

*Atajo (obligatorio en la versión de 30 min; recomendado si en el ensayo la vuelta completa pasa de tres minutos): lanza `./demo/deploy.sh 2.0.0 anillo-0` durante la espera del acto 2, con la 3 sin red: «Y mientras la 3 está sin señal, aprovecho: mando una versión nueva a una sola estación. Ya volvemos a eso.» El acto 3 arranca directo con `./demo/falla.sh bomba-01`.*

*Plan B, si la red del evento falla (watch.sh sin líneas en 30 s o la EC2 no responde): pon el video de respaldo, cortado por actos, y dilo con naturalidad: «La red de un evento es el peor lugar del mundo para depender de MQTT. Por eso traje la grabación: es la misma demo, grabada en el ensayo.» Narra encima con este mismo guion. Si se cae a mitad, sigue en el video desde el acto en que ibas.*

*Si preguntan si la v2 es mala en general o solo en la demo: en todo el set de prueba, con fallas que la v2 no vio al entrenar, la v1 detecta {{M:v1.recall_source}} de las fallas y la v2 {{M:v2.recall_source}}; la v1 alerta en {{M:v1.alert_rate_source}} de los clips y la v2 en {{M:v2.alert_rate_source}}. Los clips de la flota se eligen para que la demo sea repetible. Y la entrada media pasa de {{M:input.z_source}} a {{M:input.z_target}} con la otra velocidad.*

---

## 30 · ¿Cuánto cuesta observar mil bombas?
<!-- id: costo -->
**0:40** · 2 clics · *corte para 30 min*

"Un último número. ¿Cuánto cuesta observar mil bombas? Si mandaras el audio crudo: 2,76 terabytes al día."

**[CLIC]** "Un evento cada 10 segundos por bomba: 8,64 millones de mensajes al día."

**[CLIC]** "Un resumen por minuto: 1,44 millones. El audio se queda en la estación. Sale un evento de unos cientos de bytes."

"Las cuentas están al pie. No son de nadie: son multiplicaciones."

*La PoC manda un evento por clip, cada 3 s, porque son cinco bombas. El resumen por minuto es el paso a producción (anexo A5).*

---

## 31 · ¿Qué me llevo hoy?
<!-- id: llevo -->
**1:20** · 4 clics · *reloj: 30:10 al entrar (versión de 30: 27:20)*

*Provocación, antes del primer punto:* "Les voy a dar cinco cosas que funcionan. Y la mayoría no las va a hacer el lunes. Los que las hagan van a dormir mejor."

"Uno: el modelo es un artefacto más: versión, digest y receta."

**[CLIC]** "Dos: optimiza por chip y mide en el chip."

**[CLIC]** "Tres: despliega por anillos, con una compuerta que mire al modelo y no solo al proceso."

**[CLIC]** "Cuatro: diseña para estar sin red: cola local y decisiones locales."

**[CLIC]** "Y cinco: que el modelo cuente qué decide; el dato crudo se queda en el equipo."

"Esas son las cinco cosas."

*[Opcional, +0:30, solo si el reloj marca 31:00 o menos al llegar aquí: tu anécdota. Una vez que algo decidió mal y nadie lo vio a tiempo. Real, tuya.]*

---

## 32 · La frase final: ¿esta bomba está fallando?
<!-- id: final -->
**0:45** · 2 clics · *cierre circular: vuelve a los audios del inicio*

"Al principio les pregunté:" *(señala)* "¿esta bomba está fallando?"

*(dale ▶ a la bomba B; tres o cuatro segundos y detenla)*

"Ustedes la oyeron. Desde la nube, nadie la oyó. Y no hacía falta."

**[CLIC]** "Esto es lo único que salió de la estación: bomba-03, v1.0.0, ALERTA, score sobre el umbral, entrada normal. Unos cientos de bytes. El audio se quedó allá."

**[CLIC]** "No necesitas ver el modelo. Necesitas que te cuente." *(pausa)*

"Así que les dejo una pregunta. Si mañana uno de sus modelos deja de oír… ¿quién se entera primero: ustedes, o la vereda que se quedó sin agua?"

---

## 33 · ¿Dónde sigo después de la charla?
<!-- id: recursos -->
**0:15** · sin clics

"Todo está en el repo de ese QR: la demo con el paso a paso, las láminas y el guion. Y si van a leer una sola cosa: The ML Test Score, de Google."

---

## 34 · Gracias
<!-- id: cierre -->
**0:15** · sin clics

"Muchas gracias." *(espera el aplauso)* "Con gusto respondo sus preguntas."

*Anexos: la tecla A abre A1; las flechas los recorren; M o Esc te devuelven. A1 el evento, A2 la vuelta paso a paso, A3 qué revierte Greengrass solo, A4 permisos y costo, A5 de la demo a producción, A6 qué método de drift, A7 regulación, A8 fuentes. Más respuestas en «Preguntas difíciles», al final de este archivo.*

---

## A1 · El evento de la demo, campo por campo
<!-- id: a1 -->
*Si preguntan qué lleva exactamente el evento. M para volver.*

"Quién decidió, con qué versión y la huella exacta del modelo. El número de evento y cuándo decidió la bomba. Qué audio escuchó y de qué dominio venía. El score, el umbral de esa versión y la decisión. La entrada, resumida: la distancia media a la huella del sonido normal, en desviaciones estándar. La latencia. Y la verdad del clip, que solo existe en la demo."

"La hora de llegada la pone la regla de IoT. Llegada menos decisión es lo que la estación estuvo sin red."

---

## A2 · La vuelta automática, paso a paso
<!-- id: a2 -->
*Úsalo también mientras esperas la alarma del acto 3. Dura un minuto. M te devuelve a la demo.*

"Esto es lo que está pasando ahora mismo, sin que yo toque nada."

"Desplegué la 2.0.0 al thing group EstacionAnillo0. La bomba-01 trajo su estado deseado, bajó los archivos de S3, verificó el digest e instaló. Para Greengrass, éxito: la v2 corre sin errores."

"La bomba suena con falla y la v2 no avisa. Cada evento pasa por la regla, llega a CloudWatch Logs, y el filtro cuenta una falla no oída."

"Cuando en un minuto se juntan suficientes, la alarma estacion-fallas-no-oidas pasa a ALARM e invoca la Lambda. La Lambda le pregunta a Parameter Store cuál es la última versión buena. Responde 1.0.0. Y crea un despliegue de la 1.0.0, solo al anillo 0."

"La bomba-01 vuelve a la v1, y la falla se oye otra vez: ALERTA. Fíjense: yo solo aparezco en el primer paso. Del quinto en adelante, nadie toca nada."

*El umbral de la alarma (fallas no oídas por minuto) se ajusta en el ensayo con la variable umbral_alarma de Terraform (o ALARM_THRESHOLD con cloud/setup.sh). La acción de la alarma solo corre cuando cambia de estado: antes de subir, la alarma tiene que estar en OK.*

---

## A3 · ¿Qué revierte Greengrass solo?
<!-- id: a3 -->
*Si preguntan por qué hace falta la compuerta si Greengrass ya revierte.*

"Tres cosas sí. Si el artefacto en S3 cambió, el digest no coincide y el despliegue falla. Si el componente no instala o no arranca, failureHandlingPolicy en ROLLBACK, que viene por defecto, vuelve a la versión anterior. Y si fallan muchos equipos del anillo, abortConfig cancela el despliegue."

"Y una no: un modelo que corre bien y decide mal. Para Greengrass, eso salió bien. Lo ven los eventos del modelo y una alarma que los mire."

"Greengrass revierte despliegues fallidos, no modelos equivocados."

*Fuentes: https://docs.aws.amazon.com/greengrass/v2/developerguide/component-recipe-reference.html (Digest) · https://docs.aws.amazon.com/greengrass/v2/APIReference/API_DeploymentPolicies.html (ROLLBACK por defecto) · https://docs.aws.amazon.com/cli/latest/reference/greengrassv2/create-deployment.html (abortConfig).*

---

## A4 · Permisos y costo
<!-- id: a4 -->
*Si preguntan por permisos o por cuánto cuesta.*

"El equipo baja artefactos con el rol de token exchange, que solo puede leer el bucket. Habla MQTT con una política de IoT. La regla solo escribe en su grupo de logs. Y la Lambda solo puede crear el despliegue, con las acciones de IoT que ese despliegue usa, y leer el parámetro. En producción, además, la acotas a los thing groups de tu flota."

"¿Cuánto cuesta? No traje una cifra porque no la he medido: se mide con Cost Explorer después del ensayo. Lo que cobra es la EC2 que hospeda las cinco bombas, CloudWatch Logs y Lambda, más los mensajes de IoT Core y los core devices de Greengrass. Para dejar de pagar: ./fleet/down.sh y apagar la EC2."

---

## A5 · De la demo a producción
<!-- id: a5 -->
*Si preguntan qué cambia para una flota real de estaciones.*

"Cinco cambios. Un evento por clip pasa a un resumen por minuto, y el detalle solo cuando algo cambia. La cola en memoria pasa a disco, con tope y prioridad. El nucleus en un contenedor pasa a nucleus lite en el equipo pequeño. El anillo de una estación pasa a una compuerta que compara el canario contra el anillo: pasa si el modelo sigue oyendo. Y la respuesta conocida de la demo pasa a etiquetas tardías: la orden de mantenimiento dice cuándo fue falla."

---

## A6 · ¿Qué método de drift uso?
<!-- id: a6 -->
*Si preguntan cómo medir el drift.*

"Depende de la variable. PSI, para rangos o categorías; sus umbrales son costumbre, no estadística. Kolmogorov-Smirnov, para muestras pequeñas: con muchos datos da falsas alarmas. Wasserstein, para saber cuánto se movió en muestras grandes. Y Jensen-Shannon, acotada entre cero y uno."

"En la demo uso algo más simple: la distancia media de cada clip a la huella de stats.json. Con la otra velocidad, en el set de prueba, pasa de {{M:input.z_source}} a {{M:input.z_target}}."

---

## A7 · Regulación
<!-- id: a7 -->
**3 clics** · *si preguntan quién más va a pedir cuentas*

"En Europa, el AI Act pide que los sistemas de alto riesgo registren eventos solos durante toda su vida. Esos registros se guardan al menos seis meses, y hay monitoreo después de salir al mercado. Para alto riesgo aplica desde diciembre de 2027 o agosto de 2028, según el anexo."

**[CLIC]** "En Estados Unidos, el marco de riesgo de IA del NIST: gobernar, mapear, medir y gestionar. Es voluntario, pero se volvió el idioma común."

**[CLIC]** "E ISO/IEC 42001: un sistema de gestión de IA, certificable, con la lógica de ISO 27001."

**[CLIC]** "Piden lo mismo que necesitas para operar: qué corre, qué decidió y cómo volver."

*Si preguntan por Colombia: el AI Act se aplica a lo que se pone en el mercado de la UE, se fabrique donde se fabrique.*

---

## A8 · Fuentes
<!-- id: a8 -->
*Si piden los papers y los datos. Los audios y las cifras medidas salen de MIMII DUE (Tanabe et al., Hitachi, 2021), bombas, licencia CC BY-NC-SA 4.0. Las fuentes de AWS no van en láminas: están en este guion y en el README de la PoC.*

"Todo está aquí y en el repo. Los audios son de MIMII DUE, de Hitachi, con licencia abierta no comercial."

---

## Tiempos por bloque

| Bloque | Láminas | 35 min | 30 min | Reloj al terminar (35 · 30) |
|---|---|---|---|---|
| Apertura | 1–7 | 4:55 | 4:05 | 4:55 · 4:05 |
| 01 · El problema | 8–12 | 3:50 | 3:50 | 8:45 · 7:55 |
| 02 · El patrón | 13–16 | 3:50 | 3:50 | 12:35 · 11:45 |
| 03 · Los seis pasos | 17–25 | 8:30 | 8:30 | 21:05 · 20:15 |
| 04 · En vivo | 26–30 | 9:05 | 7:05 | 30:10 · 27:20 |
| Cierre | 31–34 | 2:35 | 2:35 | 32:45 · 29:55 |
| **Total** | | **32:45** | **29:55** | |

La versión completa deja 2:15 de margen antes de 35: es para la demo y, si sobra, para la anécdota de la lámina 31. Dentro de la demo: mapa 0:25, acto 1 1:00, acto 2 1:40, acto 3 3:40 y remate 0:15.

## Cortes para 30 minutos

1. **Lámina 4** (inversión, IDC): fuera (−0:25).
2. **Un meme:** del meme 1 (latencia) dices solo «la ida y vuelta no alcanza» y haces clic (−0:25).
3. **Lámina 28** (señales doradas): fuera; nombras las cuatro señales al abrir la demo (−0:35).
4. **Lámina 30** (las cuentas): fuera (−0:40).
5. **Demo con atajo:** el despliegue de la v2 se lanza durante la espera del acto 2 (−0:45).
6. Sin anécdota en la lámina 31.

Para saltar una lámina con el control remoto, avanza sin hablar; los cortes no cambian los clics de las demás.

## Antes de subir

**Una hora antes**
- EC2 encendida y las cinco bombas *Healthy*: `aws greengrassv2 list-core-devices --query 'coreDevices[].[coreDeviceThingName,status]' --output table`.
- Toda la flota en 1.0.0 y el despliegue en COMPLETED en los dos thing groups: la lámina 25 lo muestra así.
- `/estacion/last_good_version` = 1.0.0.
- Las cinco bombas suenan normal y a su velocidad: `./demo/falla.sh bomba-0N off` y `./demo/dominio.sh bomba-0N normal`.
- Las cinco conectadas a la red `estacion` (`docker network inspect estacion`).
- La alarma `estacion-fallas-no-oidas` en OK. Si quedó en ALARM del ensayo, no va a disparar otra vez: la acción solo corre cuando cambia de estado.

**En el escenario**
- `./demo/watch.sh` corriendo con letra grande; el dashboard `estacion` abierto (15 minutos, refresco de 10 s); la terminal SSH a la EC2 limpia, con los comandos de la demo a mano.
- El video de respaldo abierto, cortado por actos y en pausa.
- Los dos botones de audio probados con el sonido de la sala.
- El deck en pantalla completa (F); las notas (N) en tu pantalla, no en la proyectada.
- Un reloj visible y agua.

## Preguntas difíciles

- **«¿Por qué no Kubernetes en cada estación?»** En un equipo pequeño, un agente que baja componentes alcanza y pesa menos. Cuando la estación es una planta grande, Outposts con EKS local (paso 5).
- **«En producción no sabes si la bomba fallaba.»** Cierto: la verdad del clip solo existe en la demo. En producción, el canario se compara contra el anillo (tasa de alertas, score y entrada) y la etiqueta llega tarde, con la orden de mantenimiento (A5).
- **«¿Por qué AUC y no exactitud?»** Con la otra velocidad todos los scores suben: las fallas detectadas pueden subir junto con las falsas alarmas. La AUC mide si el modelo separa una bomba sana de una que falla, sin depender del umbral.
- **«¿Por qué un autoencoder y no un clasificador?»** Las fallas son raras y no tienes ejemplos de todas. Aprende lo normal y avisa cuando algo suena distinto.
- **«¿Escogiste la v2 para que fallara en la demo?»** Se evalúa con fallas que no vio al entrenar, en todo el set de prueba: {{M:v1.recall_source}} de fallas detectadas con la v1 contra {{M:v2.recall_source}} con la v2. Los clips de la flota se eligen para que la demo sea repetible; las cifras salen de todo el set.
- **«¿Cuánto cuesta la PoC?»** No lo he medido; se mide con Cost Explorer tras el ensayo (A4). Lo que más pesa es la EC2.
- **«¿Qué pasa si la cola se llena?»** El nucleus rechaza los mensajes nuevos. Para horas o días sin red, la cola va a disco.
- **«¿Por qué CloudWatch Logs y no una base de series de tiempo?»** Para la compuerta, un filtro de métrica alcanza. Si quieres análisis, otra regla de IoT puede mandar los mismos eventos a S3.
- **«¿Esto sirve con otra nube?»** El patrón de la lámina 15 no depende de ninguna. La lámina 16 es una forma de construirlo.
- **«¿Cómo firmas el modelo?»** Greengrass verifica el digest de cada artefacto. Para firma y procedencia existe un estándar abierto: OpenSSF Model Signing, sobre Sigstore.
- **«¿Cuántas bombas aguanta la PoC?»** No lo medí. Son cinco; lo que limita es la memoria de la EC2, porque cada nucleus es una JVM.
- **«¿Seguro que el audio no sale?»** El componente lee el audio montado de solo lectura y el permiso IPC solo le deja publicar en `estacion/eventos`.
- **«¿Por qué un evento cada 3 s si la cuenta dice 10?»** La demo necesita ver cosas rápido. La cuenta es para mil bombas.
- **«¿Por qué no SageMaker AI en la demo?»** En vivo, la fábrica es lo menos interesante. Un script en la laptop hace lo mismo y cabe en una semana.

## Pendientes antes de ensayar

- El dato personal (lámina 6), tu foto en `talk/assets/photo.jpg` y tu LinkedIn (`LINKEDIN=… python3 talk/tools/build_deck.py`).
- La URL del repo para el QR (`REPO_URL=…`).
- Los audios `talk/assets/audio/pump-a.wav` y `pump-b.wav`: hoy los botones dicen «audio pendiente».
- `poc-devopsdays/build/metrics.json` con datos reales: hoy viene de audio sintético, y todas las cifras `{{M:…}}` de las láminas 11 y 19 y de estas notas dicen «por medir».
- Con las cifras reales: que la AUC del dominio nuevo quede cerca de 0,5 (si no, la frase «El modelo ya no distingue» de la lámina 11 queda grande) y que la v2 detecte menos fallas que la v1.
- Cronometrar la vuelta completa del acto 3 y ajustar `ALARM_THRESHOLD`. Si pasa de tres minutos, usa el atajo también en la versión de 35.
- Grabar el video de respaldo, cortado por actos.
- Tu anécdota (lámina 31, opcional).

## Fuentes de lo que dices en voz alta

- Gartner, 28 ago 2025: PC con IA 15,6 % (2024), 31 % (2025), 54,7 % (2026, proyección).
- IDC, 17 mar 2025: gasto mundial en edge computing de US$ 261.000 M (2025) a US$ 380.000 M (2028); América Latina entre las regiones de crecimiento más rápido.
- MIMII DUE: Tanabe et al., Hitachi (2021), arXiv:2105.02702, doi:10.5281/zenodo.4740355. Bombas, `dev_data_pump`, CC BY-NC-SA 4.0.
- Cuentas (PLAN §1, sin fuente externa): 16 000 muestras/s × 2 B = 32 000 B/s ≈ 115 MB por hora ≈ 2,76 GB al día por bomba; × 1 000 = 2,76 TB al día. Un evento cada 10 s = 8 640 por bomba al día; × 1 000 ≈ 8,64 M. Un resumen por minuto = 1 440 por bomba al día; × 1 000 ≈ 1,44 M.
- AUC como probabilidad de que un positivo al azar quede por encima de un negativo al azar: Fawcett, *An introduction to ROC analysis*, Pattern Recognition Letters (2006).
- Cifras medidas: `poc-devopsdays/build/metrics.json` vía `talk/tools/metrics.py`.
- Documentación de AWS (dicha en voz alta, nunca en una lámina):
  - Cola `mqtt.spooler` del nucleus, en memoria y de 2,5 MB por defecto: https://docs.aws.amazon.com/greengrass/v2/developerguide/greengrass-nucleus-component.html
  - Cola en disco: https://docs.aws.amazon.com/greengrass/v2/developerguide/disk-spooler-component.html
  - Nucleus lite, 5 MB de almacenamiento y menos de 15 MB de RAM: https://docs.aws.amazon.com/greengrass/v2/developerguide/greengrass-nucleus-lite-component.html
  - Digest calculado al crear la versión y verificado en el equipo: https://docs.aws.amazon.com/greengrass/v2/developerguide/component-recipe-reference.html
  - `failureHandlingPolicy` = `ROLLBACK` por defecto: https://docs.aws.amazon.com/greengrass/v2/APIReference/API_DeploymentPolicies.html
  - `abortConfig` y `jobExecutionsRolloutConfig`: https://docs.aws.amazon.com/cli/latest/reference/greengrassv2/create-deployment.html
  - EKS local en Outposts sin red (x.509; el registro de imágenes lo pones tú): https://docs.aws.amazon.com/eks/latest/userguide/eks-outposts-network-disconnects.html
  - Greengrass en Docker: https://docs.aws.amazon.com/greengrass/v2/developerguide/run-greengrass-docker.html
- Breck et al., *The ML Test Score* (Google, 2017).
- Métodos de drift (A6): documentación de Evidently y NannyML; crítica a los umbrales del PSI: arXiv:2303.01227.
- Regulación (A7): Reglamento (UE) 2024/1689, arts. 12, 19 y 72, con las fechas del Reglamento (UE) 2026/1744; NIST AI 100-1; ISO/IEC 42001:2023.
