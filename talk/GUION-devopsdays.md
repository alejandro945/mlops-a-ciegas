# Guion · MLOps a ciegas · DevOpsDays Bogotá 2026

**Duración:** 25:55 de contenido, dentro de los 25 minutos más 5 de preguntas que promete el CFP. Cronométralo en el ensayo; el acto 3 depende de la alarma. **Láminas:** 31 más 10 anexos; cuatro son divisores y pasan en segundos. Plantilla oficial de DevOpsDays Bogotá 2026.

**De qué va:** cómo gobernar un modelo de IA que corre donde no llega el plano de control. El hilo es una estación de bombeo: un modelo que escucha bombas en una vereda con red intermitente. Las láminas nombran y dibujan servicios de AWS, pero ninguna cita a AWS: los datos de la documentación se dicen en voz alta y su enlace queda en la nota.

Este archivo es la fuente de las notas del presentador: cada sección con `<!-- id: … -->` aparece al presionar **N** en su lámina. Las cifras medidas se escriben `{{M:clave}}` y salen de `poc-devopsdays/build/metrics.json` y `device_bench.json`; si no hay medición real, dicen «por medir». Si cambias algo aquí, regenera el deck:

```
AWS_ICONS=<ruta al paquete de íconos> REPO_URL=… LINKEDIN=… python3 talk/tools/build_deck.py
```

**Cómo leerlo:**
- Lo que va entre comillas es lo que dices.
- **[CLIC]** avanza un paso de la lámina.
- *(pausa)* es silencio.
- Lo que va en cursiva es para ti, no para la sala.
- El tiempo en negrita es lo que dura la lámina, no la hora del reloj.

Lo que sale en la terminal está en inglés (`pump-03`, `ALERT`, `fault.sh`): es lo mismo que está en el código y en AWS. Cuando lo leas en voz alta, tradúcelo si te sale natural («la bomba 3, alerta»).

---

## El hilo: la estación

Una empresa de acueducto, **inventada para la charla**, tiene estaciones de bombeo en veredas con red intermitente. En cada estación, un equipo pequeño escucha las bombas con un micrófono y un modelo avisa cuando una empieza a sonar distinto. El audio nunca sale de la estación; sale un evento de unos cientos de bytes.

- **Lámina 2:** la sala oye la bomba A y la bomba B y vota. La respuesta (la B falla) llega en el acto 1 de la demo.
- **Láminas 9 a 11:** la estación y su problema: el panel en verde, el modelo que casi no distingue y las preguntas que hay que hacerle.
- **Pasos 1 a 6 (láminas 18 a 23):** la bomba ocupa una línea por paso, marcada *La bomba*.
- **Demo:** la bomba 3 falla y se queda sin red; la v2 no oye la falla de la 1 y vuelve sola a la v1.
- **Lámina 29:** vuelven los audios y la línea del evento de la bomba B.

Los sonidos son reales (MIMII DUE, Hitachi, CC BY-NC-SA 4.0). La empresa, las veredas y el jefe son inventados. Dilo así cuando toque.

---

## 1 · MLOps a ciegas
<!-- id: portada -->
**0:10** · sin clics

*En pantalla mientras te presentan. No saludes: cuando te den la palabra, pasa a la lámina 2 y arranca con la bomba A. Antes de subir, prueba que el audio del deck sale por los parlantes de la sala.*

---

## 2 · ¿Esta bomba está fallando?
<!-- id: suena -->
**1:15** · 1 clic · *sin «buenos días»: lo primero que oye la sala es una bomba*

"Bomba A." *(dale ▶ a la A; deja sonar cinco segundos y detenla)*

"Bomba B." *(dale ▶ a la B; cinco segundos y detenla)*

"¿Alguna de estas dos bombas está fallando?"

**[CLIC]** "Levanten la mano. ¿La A?" *(cuenta)* "¿La B?" *(cuenta)* "¿Las dos?" *(cuenta)*

"No les voy a decir todavía. La respuesta llega más adelante, en vivo."

"Los sonidos son reales: bombas industriales que grabó Hitachi. La empresa es inventada: un acueducto con estaciones de bombeo en veredas, donde la red va y viene y no hay nadie cerca. En cada estación, un equipo pequeño escucha las bombas con un micrófono, y un modelo avisa cuando una empieza a sonar distinto."

"Ustedes acaban de hacer lo que hace ese modelo: oír y decidir. Pero ustedes estaban aquí. Desde la nube, nadie oyó nada." *(pausa)*

"Por eso la charla se llama MLOps a ciegas. Hoy les voy a mostrar cómo gobernar un modelo que corre donde no llega tu plano de control: cómo llega, cómo vuelve atrás y cómo te cuenta lo que decide, sin que el audio salga de la estación."

*Mientras suena un audio, una tecla o un clic lo detiene y no cambia de lámina. Si los botones dicen «audio pendiente», faltan talk/assets/audio/pump-a.wav y pump-b.wav. La atribución de MIMII DUE está al pie.*

---

## 3 · La IA ya corre en el dispositivo
<!-- id: cien -->
**0:35** · 2 clics

"¿Por qué debería importarles un modelo en una estación de bombeo? Porque la inferencia se está moviendo de la nube al dispositivo. Un ejemplo con números de Gartner: los PC."

"De cada cien PC nuevos que se vendieron en 2024, dieciséis traían un chip para correr IA."

**[CLIC]** "En 2025, treinta y uno."

**[CLIC]** "Para este año, Gartner proyectaba cincuenta y cinco. Y no son solo los PC: los teléfonos, los carros, las cámaras y los equipos industriales ya traen hardware para correr modelos ahí mismo."

*Fuente: Gartner, 28 de agosto de 2025, «AI PCs»: 15,6 % (2024), 31 % (2025), 54,7 % (2026, proyección). La cifra es solo de PC; lo de teléfonos, carros y equipos industriales dilo sin números. Si ya salió la cifra real de 2026, dila en su lugar.*

---

## 4 · Por qué el modelo baja al dispositivo
<!-- id: memes -->
**0:50** · 2 clics · *deja que la sala se ría antes de hablar. En cada meme, a la izquierda el modelo corre en la nube y a la derecha en el equipo: esa es la única diferencia*

"¿Y por qué el modelo baja al dispositivo? Se los explico en el idioma universal: memes."

*Meme 1 · latencia.* "El carro autónomo: 'dame un segundo, le pregunto al modelo en la nube'." *(pausa corta)* "Cuando la decisión es de milisegundos, la ida y vuelta no alcanza."

**[CLIC]** *Meme 2 · sin conexión.* "Técnico, tres de la mañana, en la planta. El asistente tiene el modelo en la nube: 'Sin conexión. Intente más tarde'." *(pausa)* "Con el modelo en el equipo, responde igual. En una vereda pasa lo mismo."

**[CLIC]** *Meme 3 · privacidad.* "Y tu reloj, cada segundo, mandándole tus latidos al modelo en la nube. Si el modelo corre en el reloj, lo sensible no sale del equipo: solo sale la alerta."

"Ahora piensen en la bomba. Un micrófono a dieciséis kilohercios son ciento quince megas por hora, por bomba, por la red de una vereda. Y es el sonido de una instalación de la empresa: no tiene por qué salir de ahí."

*Cuenta: 16 000 muestras por segundo × 2 bytes = 32 000 B/s ≈ 115 MB por hora.*

---

## 5 · Sobre mí
<!-- id: quien -->
**0:30** · sin clics

"Soy Alejandro Varela, Cloud Engineer en EPAM. Trabajo con inferencia en el edge e IoT industrial."

"Tengo cinco certificaciones de AWS y tres de Kubernetes, pero lo que van a ver hoy no sale de un examen: lo monté, lo rompí y lo arreglé esta semana. Todo está en AWS, con servicios que pueden usar el lunes."

*La foto sale de talk/assets/photo.jpg; si no está, la lámina deja el recuadro. El LinkedIn sale de la variable LINKEDIN al generar el deck.*

---

## 6 · Contenido de la sesión
<!-- id: agenda -->
**0:15** · sin clics

"Cuatro partes: el problema, el patrón para resolverlo, los seis pasos de entrenar a monitorear, y una demostración en vivo."

---

## 7 · 01 · El problema
<!-- id: div1 -->
**0:05** · *divisor: no lo leas* · *reloj: 3:40*

"Empecemos por el problema."

---

## 8 · MLOps en la nube: un lazo cerrado
<!-- id: nube -->
**0:25** · sin clics · *los puntos recorren el lazo*

"Cuando el modelo corre en la nube, esto está bastante resuelto. Cada petición y cada respuesta pasan por el endpoint: se capturan, se comparan con el entrenamiento, suena una alerta si algo se desvía, y se reentrena."

"Funciona por una razón:" *(señala la frase de la izquierda)* "todo pasa por el endpoint."

---

## 9 · Las restricciones de la estación
<!-- id: edge -->
**0:45** · 3 clics · *una restricción por clic; dila como sale en pantalla*

"Ahora bajemos el modelo a la estación, al lado de la bomba. Mismo lazo… pero ya nada pasa por un endpoint."

**[CLIC]** "Uno: equipos de varias generaciones. Una estación tiene un equipo ARM, otra un x86 de hace años, la nueva trae NPU. El mismo modelo no corre igual en los tres."

**[CLIC]** "Dos: red intermitente. Se va la señal en la vereda, y el lazo de la nube se apaga."

**[CLIC]** "Y tres: el audio no puede salir de la estación. No cabe, y no debe."

"El MLOps de la nube asume que todo pasa por ti. En la estación, nada pasa por ti."

---

## 10 · Un panel en verde no mide el modelo
<!-- id: tablero -->
**1:15** · 3 clics · *el mito central de la charla: ve despacio*

"Entonces, ¿cómo sabes si el modelo de la estación está bien? Hacemos lo de siempre: miramos el panel."

**[CLIC]** "Panel del equipo. Servicio del modelo: activo. CPU: normal. Memoria: normal. Todo en verde."

*Voz del jefe:* "'¿Y el modelo de la estación cómo va?' — 'Todo verde, jefe'."

**[CLIC]** "Ahora la pregunta que importa: ¿distingue una falla de una bomba sana? Eso se mide con la AUC. Le das al modelo un clip de una bomba sana y uno de una que falla; la AUC dice qué tan seguido le pone más puntaje al que falla. Uno es siempre. Cero coma cinco es lanzar una moneda."

"Con la velocidad con la que se entrenó: {{M:v1.auc_source}}. Le cambian la velocidad a la bomba: {{M:v1.auc_target}}, casi una moneda."

"Mismo modelo, mismo umbral, cero errores. Y las falsas alarmas pasan de {{M:v1.false_alarm_source}} a {{M:v1.false_alarm_target}}."

**[CLIC]** "El equipo está sano. El modelo casi no distingue." *(pausa larga)*

"Esto no me lo inventé: lo medí en la PoC, con el audio de las bombas que van a oír en la demo. Un modelo que dejó de oír responde a tiempo, sin errores… y con un 200 OK."

*Por qué AUC y no «fallas detectadas»: con la otra velocidad todos los scores suben, y la detección puede subir junto con las falsas alarmas. La AUC mide si el modelo separa una bomba sana de una que falla, sin depender del umbral.*

---

## 11 · Monitorear la infraestructura no es monitorear el modelo
<!-- id: preguntas -->
**0:35** · sin clics · *léelo por filas: la columna de la izquierda es lo que ya tienen; la del centro, lo que falta*

"Las preguntas de siempre siguen valiendo: ¿el servicio está arriba?, ¿cuánta CPU usa?, ¿hay errores?, ¿responde a tiempo? Pero ninguna dice nada del modelo."

"Al modelo hay que preguntarle otras cuatro cosas. ¿Sigue distinguiendo correctamente? ¿Cambió la distribución de los datos? ¿Aumentaron los falsos positivos o negativos? ¿Y sus predicciones siguen siendo útiles?"

"La columna de la derecha es cómo responde cada pregunta la demo que van a ver. La última es la más difícil: solo la contesta el negocio, cuando la orden de mantenimiento dice si la alerta era real."

---

## 12 · A mano alzada 1
<!-- id: reflexion1 -->
**0:25** · sin clics · *la barra de abajo cuenta cinco segundos*

"Pregunta a mano alzada. ¿A quién le ha sonado el pager por un modelo?" *(espera las manos)*

*Si hay pocas:* "Pocas manos. ¿Y por un disco lleno?" *(risas)* "Exacto. El pager suena por el proceso. Por el modelo, casi nunca."

*Si hay muchas:* "Bienvenidos al club. ¿Y cuántos se enteraron por el cliente antes que por el pager?"

"Hoy vamos a hacer que el modelo también pueda despertar a alguien."

---

## 13 · 02 · El patrón
<!-- id: div2 -->
**0:05** · *divisor* · *reloj: 7:05*

"¿Qué hace falta para gobernarlo? Primero, abramos el equipo."

---

## 14 · Arquitectura del equipo en la estación
<!-- id: equipo -->
**0:45** · 3 clics · *una capa por clic*

"Abajo, el micrófono sobre la bomba y el modelo con su runtime: decide en milisegundos, con o sin red. El audio entra y no sale."

**[CLIC]** "Encima, el modelo no llega como un archivo suelto: llega como un artefacto con versión y hash. Si alguien lo tocó, no se instala."

**[CLIC]** "Luego, un agente. Nadie le empuja nada a la estación: el agente trae el estado deseado cuando hay red."

**[CLIC]** "Y arriba, la pieza que falta en casi todos lados: una cola de eventos. Cada decisión queda guardada hasta que haya red."

---

## 15 · Cinco piezas para gobernar el modelo
<!-- id: flujo -->
**1:10** · 6 clics · *una pieza por clic; la leyenda de arriba se enciende con cada una*

*Paso 0: «copiar el modelo… y cruzar los dedos».* "Así se despliegan modelos en muchos lados: copias el archivo al equipo y cruzas los dedos. Yo lo he hecho." *(risas)*

**[CLIC]** "Uno: optimizar por chip. Se entrena una vez y se prepara para cada familia de hardware."

**[CLIC]** "Dos: artefacto verificable. Cada versión, con su huella, en un registro donde nada se sobrescribe."

**[CLIC]** "Tres: estado deseado. La central declara qué debería tener cada equipo, y el equipo lo trae cuando puede."

**[CLIC]** "Cuatro: evento de inferencia. El modelo deja constancia de lo que decide. Si no hay red, se encola."

**[CLIC]** "Cinco: la compuerta. Una condición que mira esos eventos y decide sola si sigue o vuelve atrás. Es el lazo rápido: minutos."

**[CLIC]** "Y con esos mismos eventos se reentrena: el lazo lento, días. Abajo, lo que atraviesa todo: identidad, mínimo privilegio, cifrado y auditoría. Ninguna de estas piezas depende de una nube en particular."

---

## 16 · El mismo patrón en AWS
<!-- id: aws -->
**0:50** · 6 clics · *misma geometría que la anterior; avanza a buen ritmo, los pasos que vienen abren cada casilla*

"El mismo dibujo, en AWS. Cada casilla ahora tiene nombre."

**[CLIC]** "SageMaker AI entrena y exporta el modelo." **[CLIC]** "El registro es S3, un prefijo por versión, y IoT Greengrass lo empaca como componente." **[CLIC]** "El estado deseado es un despliegue de Greengrass, que llega por IoT Core con un certificado por equipo."

**[CLIC]** "Cada decisión entra por IoT Core y una regla la deja en CloudWatch Logs." **[CLIC]** "La compuerta: una alarma invoca una Lambda que vuelve a desplegar la última versión buena." **[CLIC]** "Y abajo, IAM, X.509, KMS y CloudTrail."

---

## 17 · 03 · Los seis pasos
<!-- id: div3 -->
**0:10** · *divisor con la espina* · *reloj: 9:55*

"Seis pasos: entrenar, optimizar, empaquetar, desplegar, operar sin red y monitorear. En cada uno, una línea de la bomba."

---

## 18 · Paso 1 · Entrenar con sonido normal
<!-- id: entrenar -->
**1:00** · 3 clics

"Paso uno. Bombas reales, solo clips de sonido normal."

**[CLIC]** "Se entrena un autoencoder: una red que aprende a rehacer el sonido normal. Si no lo puede rehacer, algo cambió. El score es el error de reconstrucción."

**[CLIC]** "Lo que sale va a S3, un prefijo por versión. Una versión nueva es otro prefijo, nunca el mismo."

**[CLIC]** "¿Y qué sale exactamente? Cuatro archivos. El modelo en ONNX, que es el contrato con el equipo. stats.json, con la huella del sonido normal y el umbral. features.py, el mismo preprocesamiento del entrenamiento. E inference.py, que escucha, decide y cuenta."

"El error típico: entrenar con un preprocesamiento y servir con otro. No explota nada; el modelo solo oye distinto. Por eso features.py viaja con el modelo."

*La bomba:* "Aprende solo con sonido normal: las fallas son raras."

*En la PoC la fábrica es model/train.py en mi portátil, no SageMaker AI. Lo dices en la lámina 26.*

---

## 19 · Paso 2 · Optimizar para cada chip
<!-- id: optimizar -->
**1:10** · 3 clics

"Paso dos. Entrenas una vez, en 32 bits: un archivo ONNX."

**[CLIC]** "Para que quepa en el equipo, se cuantiza de 32 a 8 bits, se simplifica el grafo y se compila para el acelerador del chip. Esa compilación la hace la herramienta de cada fabricante, sobre el mismo ONNX."

**[CLIC]** "Y no sale un artefacto: sale uno por chip. Y manda la memoria del chip: si no cabe, no corre."

**[CLIC]** "Esta es la bomba, medida en el equipo de la demo, una CPU x86. De FP32 a INT8, el archivo pasa de {{M:int8.size_fp32_kb}} a {{M:int8.size_int8_kb}}. El clip, de {{M:device.lat_fp32_ms}} a {{M:device.lat_int8_ms}}. Y toma la misma decisión en {{M:int8.agree_pct}} de los clips."

"En mi portátil la mejora era casi el doble. En el equipo, la mayor parte del tiempo se va en preparar el audio, no en el modelo. Por eso se mide en el chip, no en tu máquina."

*La bomba:* "INT8 para el equipo pequeño."

*Cifras: device.* sale de poc-devopsdays/build/device_bench.json, medido con model/bench_device.py en la EC2, dentro de la imagen de las bombas. En el portátil (M3 Pro) fue {{M:int8.lat_fp32_ms}} → {{M:int8.lat_int8_ms}}. ΔAUC del INT8: {{M:int8.auc_delta}}. Herramientas, si preguntan: LiteRT y Qualcomm QNN para NPU, TensorRT para GPU de NVIDIA, ONNX Runtime y OpenVINO para CPU. Sobre SageMaker Neo, ver «Preguntas difíciles».*

---

## 20 · Paso 3 · Empaquetar como componente
<!-- id: componente -->
**1:00** · 4 clics · *una anotación por clic*

"Paso tres. Un componente es la forma en que IoT Greengrass empaca software para el equipo. Esta es la receta de la demo, recortada."

**[CLIC]** "Los artefactos vienen de S3. La receta no trae el digest: Greengrass lo calcula al crear la versión del componente y lo verifica en el equipo antes de instalar."

**[CLIC]** "El ciclo de vida no instala nada: las dependencias ya vienen en el equipo. Si tu componente baja librerías al arrancar, en una vereda sin red no arranca."

**[CLIC]** "El umbral es configuración: se cambia con un despliegue, sin reentrenar ni publicar otra versión."

**[CLIC]** "Y los permisos: el componente solo puede publicar en un tema, station/events."

"Una versión publicada no se toca. Si cambias un archivo en S3 sin cambiar la versión, el digest ya no coincide y el despliegue falla."

*La bomba:* "El umbral es configuración: se cambia sin reentrenar."

*Fuente del digest: referencia de recetas de Greengrass, campo Digest de Artifacts. https://docs.aws.amazon.com/greengrass/v2/developerguide/component-recipe-reference.html*

---

## 21 · Paso 4 · Desplegar por anillos
<!-- id: anillos -->
**1:05** · 3 clics

"Paso cuatro. ¿Cómo llega a mil equipos sin romperlos todos un martes? Con despliegues de IoT Greengrass, un thing group por anillo."

"Anillo cero: una estación, el canario. Recibe la versión nueva primero."

**[CLIC]** "Si pasa la compuerta, anillo uno: el resto de la flota, en olas que crecen."

**[CLIC]** "El despliegue trae dos protecciones: si fallan demasiados equipos, se cancela; y si un equipo no arranca la versión nueva, vuelve a la que tenía."

**[CLIC]** "Y la vuelta: la alarma ve fallas que nadie oyó y despliega la última versión buena. El anillo 1 nunca recibe la versión mala."

"Seguro alguien está pensando: 'Greengrass ya hace rollback'. Sí, de despliegues que fallan. Para Greengrass, un modelo que se instala bien y no oye es un despliegue exitoso."

*La bomba:* "Una estación como canario."

*Fuentes: failureHandlingPolicy = ROLLBACK por defecto, https://docs.aws.amazon.com/greengrass/v2/APIReference/API_DeploymentPolicies.html · abortConfig y jobExecutionsRolloutConfig, https://docs.aws.amazon.com/cli/latest/reference/greengrassv2/create-deployment.html*

---

## 22 · Paso 5 · Operar sin red
<!-- id: sinred -->
**0:50** · 2 clics

"Paso cinco. ¿Qué sigue funcionando sin red?"

"En un equipo pequeño, IoT Greengrass: el nucleus guarda los eventos en una cola local hasta que vuelve la red, por defecto en memoria, de 2,5 megas. Y si el equipo tiene poca memoria, existe el nucleus lite, escrito en C."

**[CLIC]** "Si la estación es una planta grande, Outposts con EKS local: el plano de control corre en el sitio y sigue sin la región."

**[CLIC]** *La bomba, en el recuadro:* "Sin red, la estación sigue escuchando y alertando: lo que necesita para decidir ya está adentro."

"Ojo con una cosa: cuando la cola se llena, el nucleus rechaza los mensajes nuevos. Si la red se va por horas, la cola va a disco."

*Fuentes: cola mqtt.spooler de 2,5 MB en memoria, https://docs.aws.amazon.com/greengrass/v2/developerguide/greengrass-nucleus-component.html · cola en disco, https://docs.aws.amazon.com/greengrass/v2/developerguide/disk-spooler-component.html · nucleus lite (5 MB de almacenamiento, menos de 15 MB de RAM), https://docs.aws.amazon.com/greengrass/v2/developerguide/greengrass-nucleus-lite-component.html · EKS local sin red, https://docs.aws.amazon.com/eks/latest/userguide/eks-outposts-network-disconnects.html*

---

## 23 · Paso 6 · Monitorear lo que decide el modelo
<!-- id: monitoreo -->
**1:05** · 5 clics · *un tramo de la tubería por clic*

"Paso seis. Desde la nube ves lo que el modelo te cuenta: un evento por clip, de unos cientos de bytes, que llega a IoT Core."

**[CLIC]** "Una regla de IoT lo toma y le suma la hora en que llegó. Llegada menos decisión: el tiempo que la estación estuvo sin red."

**[CLIC]** "La regla lo deja en CloudWatch Logs."

**[CLIC]** "Un filtro de métrica cuenta lo que importa. En la demo: la bomba fallaba y el modelo no avisó. MissedFaults, fallas que nadie oyó."

**[CLIC]** "Una alarma mira esa métrica."

**[CLIC]** "Y la alarma invoca la Lambda, que despliega la última versión buena al anillo 0."

"El error típico: poner la alarma sobre CPU y errores. Ya vimos que eso se queda en verde. La compuerta mira al modelo."

"En producción no sabes en el momento si la bomba fallaba: esa verdad solo existe en la demo. La etiqueta llega tarde, con la orden de mantenimiento, y mientras tanto comparas el canario contra el resto."

*La bomba:* "Las señales de la bomba: alertas, score, entrada y versión."

---

## 24 · A mano alzada 2
<!-- id: reflexion3 -->
**0:35** · 1 clic · *la barra cuenta cinco segundos*

"Última pregunta. ¿Qué versión corre en cada equipo?" *(manos)* "Ahora bajen la mano los que tuvieron que pensarlo." *(risas)*

**[CLIC]** "Esta es la respuesta, y no hay que entrar a ningún equipo: el estado del despliegue, por thing group. StationRing0, la bomba 1, com.station.Listener 1.0.0, activo. StationRing1, de la 2 a la 5, la misma versión."

"La pregunta se responde en la nube, no en el equipo."

*Así lo devolvió `aws greengrassv2 list-deployments` en el ensayo: un despliegue a un thing group queda ACTIVE. Detalle de un equipo, si lo piden: `aws greengrassv2 list-installed-components --core-device-thing-name pump-01`. Antes de subir, confirma que la flota está así.*

---

## 25 · 04 · Demostración
<!-- id: div4 -->
**0:05** · *divisor* · *reloj: 16:50*

"Suficiente teoría. Vamos a la estación."

---

## 26 · Arquitectura de la demostración
<!-- id: poc -->
**0:40** · sin clics

"Esto es lo que monté. No traje bombas al escenario: cada bomba es un contenedor en una EC2, con el nucleus real de IoT Greengrass adentro. Cinco bombas: la 1 es el anillo 0, el canario; de la 2 a la 5, el anillo 1."

"Lo que suena es audio real de MIMII DUE. Y todo lo demás es AWS de verdad: EC2, IoT Greengrass, IoT Core, S3, CloudWatch, Lambda y Parameter Store. Todo sale de Terraform, con GitHub Actions."

"Lo único simulado es el equipo físico. Y la fábrica: el modelo lo entrena un script en mi portátil, no SageMaker AI."

*Si preguntan: las cinco bombas salen de tres secciones de MIMII DUE; la 1 y la 4 comparten sección, y la 2 y la 5 también, con clips distintos. Cada nucleus es una JVM: en el ensayo, unos 220 MB por bomba.*

---

## 27 · Demostración en tres actos
<!-- id: demo -->
**6:00** · 2 clics en la lámina, después las terminales · *la lámina es el mapa; lo real está en la terminal*

*En la lámina (0:20).* "Tres actos. Uno: escuchar. La bomba 3 va a sonar como la B del principio."

**[CLIC]** "Dos: sin red. La 3 se queda sin señal."

**[CLIC]** "Tres: desplegar por anillos y volver." *(señala la frase de abajo)* "Y esa frase es el final de la película. No la lean todavía." *(risas)*

*Cambia a las terminales: `./demo/watch.sh` a la izquierda; a la derecha arriba, el dashboard `station`; a la derecha abajo, la terminal de Session Manager en la EC2. Letra grande.*

"Esto es la estación en vivo. Cada línea es un clip que una bomba escuchó y decidió: la hora, qué bomba, qué versión, si alertó, el score contra el umbral, cómo era la entrada y en cuántos milisegundos. Esas son las señales doradas de un modelo. El audio no está ahí. Nunca sale."

**Acto 1 · Escuchar (1:00)**

*Escribe* `./demo/fault.sh pump-03` — "Le digo a la bomba 3 que suene como la B."

*Cuando aparezca pump-03 v1.0.0 ALERT (en el ensayo, al siguiente clip, unos 4 s):* "Ahí está. ALERT: el score pasó el umbral."

"Y esta es la respuesta del principio: la bomba B era la que estaba fallando. ¿Quién votó B?" *(manos)* "Oído de mecánico. Los de la A, tranquilos: para eso está el modelo."

"El audio no salió de la estación. Salió esta línea."

*No apagues la falla de la 3: en el acto 2, lo que llega tarde tienen que ser alertas.*

**Acto 2 · Sin red (1:20)**

*Escribe* `./demo/network.sh off pump-03` — "Le quito la red a la estación 3, como cuando se va la señal en la vereda."

*Mientras esperas, lanza el despliegue del acto 3:* `./demo/deploy.sh 2.0.0 ring-0` — "Y mientras la 3 está sin señal, aprovecho: mando una versión nueva a una sola estación. Ya volvemos a eso."

*A los 40 o 50 s:* "La 3 se calló. Las otras cuatro siguen. ¿Se rompió? No. Sigue escuchando, sigue alertando y guarda cada evento en la cola del nucleus. La nube no sabe nada. La estación, sí."

*Escribe* `./demo/network.sh on pump-03` — *en el ensayo, la bomba se reconectó en unos 5 s.* "Ahí están: llegaron tarde, pero llegaron. Ese 'arrived late' es la diferencia entre cuándo decidió la bomba y cuándo llegó a la nube. No se perdió ninguna alerta."

*Escribe* `./demo/fault.sh pump-03 off`

**Acto 3 · Desplegar por anillos y volver (3:05)**

*Señala la bomba 1, que ya corre v2.0.0 (en el ensayo llegó en 13 a 15 s); de la 2 a la 5 siguen en v1.0.0.* "La versión nueva se reentrenó con más audio. Más datos, mejor modelo… ¿cierto? Y da menos alertas: en operación están felices. Va solo al anillo 0, el canario. Sin errores, misma latencia. Para Greengrass, despliegue exitoso."

*Escribe* `./demo/fault.sh pump-01` — "Ahora la 1 suena con falla."

*Cuando aparezca pump-01 v2.0.0 normal … · missed fault:* "La bomba está fallando… y la v2 dice normal. Falla no oída." *(pausa)*

"¿Qué pasó? El audio extra de la v2 incluía la semana en que una bomba ya estaba fallando. Nadie lo limpió. El modelo aprendió que fallar es normal. Corre sin errores, da menos alertas… y no oye las fallas."

*Mientras la alarma junta datos:* "Ahora no voy a tocar nada. La compuerta trabaja sola." *Cambia al deck: tecla A y una flecha a la derecha te llevan al anexo A2. Cuenta la secuencia con la nota de A2 (un minuto). M te devuelve aquí.*

*Vuelve a watch.sh. Cuando la 1 salga en v1.0.0 con ALERT:* "Volvió. v1.0.0, ALERT otra vez: la falla se oye. Nadie entró al equipo. Y el anillo 1 nunca recibió la v2."

*Escribe* `./demo/fault.sh pump-01 off`

*Vuelve a esta lámina y dilo mirando a la sala:* "Greengrass revierte despliegues fallidos, no modelos equivocados. Esa compuerta la pones tú."

*Tiempos medidos en los ensayos del 12 de octubre: de `fault.sh pump-01` a la v1 otra vez, entre 1:40 y 2:15 (la alarma salta entre 1:30 y 2:00; la Lambda despliega 1 s después; la bomba vuelve unos 13 s más tarde). Depende de en qué segundo del minuto cae la falla. Tope: si a los tres minutos de `fault.sh pump-01` la 1 no ha vuelto, no esperes más: «La alarma va a su ritmo; para no robarles tiempo, les muestro cómo termina», y pon el video desde la vuelta.*

*Plan B, si la red del evento falla (watch.sh sin líneas en 30 s o la EC2 no responde): pon el video de respaldo, cortado por actos, y dilo con naturalidad: «La red de un evento es el peor lugar del mundo para depender de MQTT. Por eso traje la grabación: es la misma demo, grabada en el ensayo.» Narra encima con este mismo guion.*

*Si preguntan si la v2 es mala en general o solo en la demo: en todo el set de prueba, con fallas que la v2 no vio al entrenar, la v1 detecta {{M:v1.recall_source}} de las fallas y la v2 {{M:v2.recall_source}}; la v1 alerta en {{M:v1.alert_rate_source}} de los clips y la v2 en {{M:v2.alert_rate_source}}. Los clips de la flota se eligen para que la demo sea repetible.*

---

## 28 · Cinco recomendaciones
<!-- id: llevo -->
**1:05** · 4 clics · *reloj: 23:35 al entrar*

"Les dejo cinco cosas que funcionan. La mayoría no las va a hacer el lunes. Los que las hagan van a dormir mejor."

"Uno: el modelo es un artefacto más: versión, digest y receta."

**[CLIC]** "Dos: optimiza por chip y mide en el chip."

**[CLIC]** "Tres: despliega por anillos, con una compuerta que mire al modelo y no solo al proceso."

**[CLIC]** "Cuatro: diseña para estar sin red: cola local y decisiones locales."

**[CLIC]** "Y cinco: que el modelo cuente qué decide; el dato crudo se queda en el equipo."

*Si el reloj marca 23:40 o menos al llegar aquí (+0:25), cuenta lo que pasó en el primer ensayo, que es real: «La primera vez que monté esto en AWS, ninguna bomba arrancaba. El instalador de Greengrass decide el formato del archivo de configuración por la extensión, y mi archivo no tenía extensión. Una línea. Por eso se ensaya en el equipo de verdad.»*

---

## 29 · La frase final: ¿esta bomba está fallando?
<!-- id: final -->
**0:45** · 2 clics · *cierre circular: vuelve a los audios del inicio*

"Al principio les pregunté:" *(señala)* "¿esta bomba está fallando?"

*(dale ▶ a la bomba B; tres o cuatro segundos y detenla)*

"Ustedes la oyeron. Desde la nube, nadie la oyó. Y no hacía falta."

**[CLIC]** "Esto es lo único que salió de la estación: la bomba 3, versión 1.0.0, alerta, el score sobre el umbral. Unos cientos de bytes. El audio se quedó allá."

**[CLIC]** "No necesitas ver el modelo. Necesitas que te cuente." *(pausa)*

"Así que les dejo una pregunta. Si mañana uno de sus modelos deja de oír… ¿quién se entera primero: ustedes, o la vereda que se quedó sin agua?"

*La línea de la lámina es la que imprimió la terminal en el ensayo: score 0.42 contra un umbral de 0.34.*

---

## 30 · Recursos y contacto
<!-- id: recursos -->
**0:15** · sin clics

"Todo está en el repo de ese QR: la demo con el paso a paso, las láminas y el guion. Y si van a leer una sola cosa: The ML Test Score, de Google."

*El QR lleva a https://github.com/alejandro945/mlops-a-ciegas (público desde el 12 de octubre; verificado leyendo el QR de la lámina). Si lo necesitas suelto, está en talk/assets/qr-repo.png y qr-repo.svg.*

---

## 31 · Gracias
<!-- id: cierre -->
**0:15** · sin clics

"Muchas gracias." *(espera el aplauso)* "Con gusto respondo sus preguntas."

*Anexos: la tecla A abre A1; las flechas los recorren; M o Esc te devuelven. A1 el evento, A2 la vuelta paso a paso, A3 qué revierte Greengrass solo, A4 permisos y costo, A5 de la demo a producción, A6 qué método de drift, A7 regulación, A8 fuentes, A9 señales doradas, A10 audio crudo contra eventos. Más respuestas en «Preguntas difíciles», al final de este archivo.*

---

## A1 · El evento de la demo, campo por campo
<!-- id: a1 -->
*Si preguntan qué lleva exactamente el evento. M para volver.*

"Quién decidió, con qué versión y la huella exacta del modelo. El número de evento y cuándo decidió la bomba. Qué audio escuchó y de qué dominio venía. El score, el umbral de esa versión y la decisión. La entrada, resumida: la distancia media a la huella del sonido normal, en desviaciones estándar. La latencia. Y la verdad del clip, que solo existe en la demo."

"La hora de llegada la pone la regla de IoT. Llegada menos decisión es lo que la estación estuvo sin red."

---

## A2 · La vuelta automática, paso a paso
<!-- id: a2 -->
*Úsalo mientras esperas la alarma del acto 3. Dura un minuto. M te devuelve a la demo.*

"Esto es lo que está pasando ahora mismo, sin que yo toque nada."

"Desplegué la 2.0.0 al thing group StationRing0. La bomba 1 trajo su estado deseado, bajó los archivos de S3, verificó el digest e instaló. Para Greengrass, éxito: la v2 corre sin errores."

"La bomba suena con falla y la v2 no avisa. Cada evento pasa por la regla, llega a CloudWatch Logs, y el filtro cuenta una falla no oída."

"Cuando en un minuto se juntan ocho o más, la alarma station-missed-faults pasa a ALARM e invoca la Lambda. La Lambda le pregunta a Parameter Store cuál es la última versión buena. Responde 1.0.0. Y crea un despliegue de la 1.0.0, solo al anillo 0."

"La bomba 1 vuelve a la v1, y la falla se oye otra vez. Yo solo aparezco en el primer paso. Del quinto en adelante, nadie toca nada."

*El umbral de la alarma (fallas no oídas por minuto) es la variable de Terraform alarm_threshold, que en Actions viene de la variable del repo ALARM_THRESHOLD (8 por defecto). Con estos clips, la v2 deja pasar unas 12 por minuto. La acción de la alarma solo corre cuando cambia de estado: antes de subir, la alarma tiene que estar en OK.*

---

## A3 · ¿Qué revierte Greengrass solo?
<!-- id: a3 -->
*Si preguntan por qué hace falta la compuerta si Greengrass ya revierte.*

"Tres cosas sí. Si el artefacto en S3 cambió, el digest no coincide y el despliegue falla. Si el componente no instala o no arranca, failureHandlingPolicy en ROLLBACK, que viene por defecto, vuelve a la versión anterior. Y si fallan muchos equipos del anillo, abortConfig cancela el despliegue."

"Y una no: un modelo que corre bien y decide mal. Para Greengrass, eso salió bien. Lo ven los eventos del modelo y una alarma que los mire."

*Fuentes: https://docs.aws.amazon.com/greengrass/v2/developerguide/component-recipe-reference.html (Digest) · https://docs.aws.amazon.com/greengrass/v2/APIReference/API_DeploymentPolicies.html (ROLLBACK por defecto) · https://docs.aws.amazon.com/cli/latest/reference/greengrassv2/create-deployment.html (abortConfig).*

---

## A4 · Permisos y costo
<!-- id: a4 -->
*Si preguntan por permisos o por cuánto cuesta.*

"El equipo baja artefactos con el rol de token exchange, que solo puede leer el bucket. Habla MQTT con una política de IoT que solo lo deja conectarse como su bomba y publicar en station/events. La regla solo escribe en su grupo de logs. Y la Lambda solo puede crear el despliegue y leer el parámetro."

"¿Cuánto cuesta? Lo que cobra es la EC2 que hospeda las cinco bombas, los mensajes de IoT Core, los core devices de Greengrass, CloudWatch y Lambda. La cifra exacta sale de Cost Explorer después del ensayo. Para dejar de pagar, el workflow de Terraform tiene un destroy."

---

## A5 · De la demo a producción
<!-- id: a5 -->
*Si preguntan qué cambia para una flota real de estaciones.*

"Cinco cambios. Un evento por clip pasa a un resumen por minuto, y el detalle solo cuando algo cambia. La cola en memoria pasa a disco, con tope y prioridad. El nucleus en un contenedor pasa a nucleus lite en el equipo pequeño. El anillo de una estación pasa a una compuerta que compara el canario contra el anillo. Y la respuesta conocida de la demo pasa a etiquetas tardías: la orden de mantenimiento dice cuándo fue falla."

---

## A6 · ¿Qué método de drift uso?
<!-- id: a6 -->
*Si preguntan cómo medir el drift.*

"Depende de la variable. PSI, para rangos o categorías; sus umbrales son costumbre, no estadística. Kolmogorov-Smirnov, para muestras pequeñas: con muchos datos da falsas alarmas. Wasserstein, para saber cuánto se movió en muestras grandes. Y Jensen-Shannon, acotada entre cero y uno."

"En la demo uso algo más simple: la distancia media de cada clip a la huella de stats.json. Con la otra velocidad, en el set de prueba, pasa de {{M:input.z_source}} a {{M:input.z_target}}."

*En el ensayo, con `./demo/domain.sh pump-05 shifted`, la entrada de la bomba 5 subió de ~0,8 a entre 1,6 y 2,2 desde el primer clip, y aparecieron alertas falsas. En el dashboard, el widget de la entrada muestra el promedio de la flota y la peor bomba: la deriva de una sola bomba se ve en la segunda serie.*

---

## A7 · Regulación
<!-- id: a7 -->
**3 clics** · *si preguntan quién más va a pedir cuentas*

"En Europa, el AI Act pide que los sistemas de alto riesgo registren eventos solos durante toda su vida. Esos registros se guardan al menos seis meses, y hay monitoreo después de salir al mercado. Para alto riesgo aplica desde diciembre de 2027 o agosto de 2028, según el anexo."

**[CLIC]** "En Estados Unidos, el marco de riesgo de IA del NIST: gobernar, mapear, medir y gestionar. Es voluntario, pero se volvió el idioma común."

**[CLIC]** "E ISO/IEC 42001: un sistema de gestión de IA, certificable, con la lógica de ISO 27001."

**[CLIC]** "Piden lo mismo que necesitas para operar: qué corre, qué decidió y cómo volver."

*Si preguntan por Colombia: el AI Act se aplica a lo que se pone en el mercado de la UE, se fabrique donde se fabrique. Verifica en EUR-Lex el número y las fechas del Reglamento (UE) 2026/1744 antes de subir.*

---

## A8 · Fuentes
<!-- id: a8 -->
*Si piden los papers y los datos. Los audios y las cifras medidas salen de MIMII DUE (Tanabe et al., Hitachi, 2021), bombas, licencia CC BY-NC-SA 4.0. Las fuentes de AWS no van en láminas: están en este guion y en el README de la PoC.*

"Todo está aquí y en el repo. Los audios son de MIMII DUE, de Hitachi, con licencia abierta no comercial."

---

## A9 · Las señales doradas de un modelo
<!-- id: senales -->
*Si preguntan qué mirar en el dashboard. En la demo las nombras sobre las columnas de watch.sh.*

"Los que venimos de SRE conocemos las señales doradas de un servicio: latencia, tráfico, errores y saturación. Las de un modelo, con la bomba: ¿qué decide? Alertas por bomba. ¿Con cuánta seguridad? El score contra el umbral. ¿Se parece a lo que aprendió? El nivel de la entrada. ¿Qué corre dónde? La versión por equipo. Ninguna sola alcanza."

---

## A10 · Audio crudo contra eventos, con mil bombas
<!-- id: costo -->
**2 clics** · *si preguntan por qué no mandar el audio a la nube*

"Si mandaras el audio crudo de mil bombas: 2,76 terabytes al día."

**[CLIC]** "Un evento cada 10 segundos por bomba: 8,64 millones de mensajes al día."

**[CLIC]** "Un resumen por minuto: 1,44 millones. El audio se queda en la estación."

*La PoC manda un evento por clip, cada 3 s, porque son cinco bombas. Las cuentas están al pie de la lámina.*

---

## Tiempos por bloque

| Bloque | Láminas | Duración | Reloj al terminar |
|---|---|---|---|
| Apertura | 1–6 | 3:35 | 3:35 |
| 01 · El problema | 7–12 | 3:30 | 7:05 |
| 02 · El patrón | 13–16 | 2:50 | 9:55 |
| 03 · Los seis pasos | 17–24 | 6:55 | 16:50 |
| 04 · Demostración | 25–27 | 6:45 | 23:35 |
| Cierre | 28–31 | 2:20 | 25:55 |
| **Total** | | **25:55** | |

Dentro de la demo: mapa 0:20, intro de las terminales 0:20, acto 1 1:00, acto 2 1:20 (con el despliegue de la v2 lanzado durante la espera), acto 3 2:45 y remate 0:15. El acto 3 es lo único que no controlas: si en el ensayo la vuelta pasa de 2:30, lleva el tope y el video listos. La anécdota de la lámina 28 solo entra si vas adelantado.

## Antes de subir

**Una hora antes**
- EC2 encendida y las cinco bombas *Healthy*: `aws greengrassv2 list-core-devices --query 'coreDevices[].[coreDeviceThingName,status]' --output table`.
- Toda la flota en 1.0.0: los dos thing groups con su despliegue en ACTIVE (la lámina 24 lo muestra así).
- `/station/last_good_version` = 1.0.0.
- Las cinco bombas suenan normal: `./demo/fault.sh pump-0N off` y `./demo/domain.sh pump-0N normal`.
- Las cinco conectadas a la red `station` (`docker network inspect station`).
- La alarma `station-missed-faults` en OK. Si quedó en ALARM del ensayo, no va a disparar otra vez: la acción solo corre cuando cambia de estado.

**En el escenario**
- `./demo/watch.sh` corriendo con letra grande; el dashboard `station` abierto (15 minutos, refresco de 10 s); la terminal de Session Manager en la EC2 limpia, con los comandos de la demo a mano.
- El video de respaldo abierto, cortado por actos y en pausa.
- Los dos botones de audio probados con el sonido de la sala.
- El deck en pantalla completa (F); las notas (N) en tu pantalla, no en la proyectada.
- Un reloj visible y agua.

## Preguntas difíciles

- **«¿Y SageMaker Neo? ¿No es eso lo de compilar por chip?»** Lo probé. Neo no compiló el modelo tal cual: no soporta el operador `Scaler` que trae el modelo de scikit-learn, ni el `MatMulInteger` del INT8. Reescribí ese operador con operaciones estándar y ahí sí compiló, para x86 y ARM64, en un minuto. Pero el resultado corre con su propio runtime, DLR, cuya última versión es de 2021, y su lista de equipos es de otra generación (Jetson TX1 y TX2, Raspberry Pi 3). Cuando AWS cerró SageMaker Edge Manager en 2024, recomendó ONNX Runtime para el equipo y Greengrass para desplegar y monitorear. Eso es lo que ven en la demo.
- **«¿Por qué no despliegas el INT8?»** En la CPU de la demo ahorra poco: el clip pasa de {{M:device.lat_fp32_ms}} a {{M:device.lat_int8_ms}}, porque el tiempo se va en preparar el audio. Y decide igual. En un equipo con NPU sí vale la pena; ahí iría un artefacto por chip, con un manifiesto por arquitectura en la receta.
- **«¿Por qué no Kubernetes en cada estación?»** En un equipo pequeño, un agente que baja componentes alcanza y pesa menos. Cuando la estación es una planta grande, Outposts con EKS local (paso 5).
- **«En producción no sabes si la bomba fallaba.»** Cierto: la verdad del clip solo existe en la demo. En producción, el canario se compara contra el anillo (tasa de alertas, score y entrada) y la etiqueta llega tarde, con la orden de mantenimiento (A5).
- **«¿Por qué AUC y no exactitud?»** Con la otra velocidad todos los scores suben: las fallas detectadas pueden subir junto con las falsas alarmas. La AUC mide si el modelo separa una bomba sana de una que falla, sin depender del umbral.
- **«¿Por qué un autoencoder y no un clasificador?»** Las fallas son raras y no tienes ejemplos de todas. Aprende lo normal y avisa cuando algo suena distinto.
- **«¿Escogiste la v2 para que fallara en la demo?»** Se evalúa con fallas que no vio al entrenar, en todo el set de prueba: {{M:v1.recall_source}} de fallas detectadas con la v1 contra {{M:v2.recall_source}} con la v2. Los clips de la flota se eligen para que la demo sea repetible; las cifras salen de todo el set.
- **«¿Se pierden eventos sin red?»** En el ensayo no se perdió ninguno: el número de secuencia de cada bomba no tuvo huecos. Sí llegaron unos pocos duplicados al volver la red: MQTT con QoS 1 entrega «al menos una vez».
- **«¿Cuánto cuesta la PoC?»** Lo que más pesa es la EC2; la cifra se saca de Cost Explorer (A4).
- **«¿Qué pasa si la cola se llena?»** El nucleus rechaza los mensajes nuevos. Para horas o días sin red, la cola va a disco.
- **«¿Por qué CloudWatch Logs y no una base de series de tiempo?»** Para la compuerta, un filtro de métrica alcanza. Si quieres análisis, otra regla de IoT puede mandar los mismos eventos a S3.
- **«¿Esto sirve con otra nube?»** El patrón de la lámina 15 no depende de ninguna. La lámina 16 es una forma de construirlo.
- **«¿Cómo firmas el modelo?»** Greengrass verifica el digest de cada artefacto. Para firma y procedencia existe un estándar abierto: OpenSSF Model Signing, sobre Sigstore.
- **«¿Cuántas bombas aguanta la PoC?»** En el ensayo, cada bomba usó unos 220 MB y las cinco juntas 1,4 GB de 7,8. Lo que limita es la memoria, porque cada nucleus es una JVM.
- **«¿Seguro que el audio no sale?»** El componente lee el audio montado de solo lectura y el permiso IPC solo le deja publicar en `station/events`.
- **«¿Por qué un evento cada 3 s si la cuenta dice 10?»** La demo necesita ver cosas rápido. La cuenta es para mil bombas.
- **«¿Por qué no SageMaker AI en la demo?»** En vivo, la fábrica es lo menos interesante. Un script en el portátil hace lo mismo y cabe en una semana.

## Pendientes antes de la charla

- La infraestructura está abajo desde el 12 de octubre (destroy). El día anterior: Actions → infra → Run workflow → apply; en la EC2, `fetch-poc`, `./fleet/build.sh` y `./fleet/up.sh`; desde el portátil, `./demo/publish.sh 1.0.0`, `2.0.0` y `./demo/deploy.sh 1.0.0 all`. En el ensayo todo eso tomó unos 15 minutos.
- Tu foto en `talk/assets/photo.jpg` (cuadrada); hoy la lámina 5 muestra el recuadro vacío.
- Grabar el video de respaldo, cortado por actos.
- Cronometrar la charla completa en un ensayo con la EC2 y ajustar donde haga falta.

## Fuentes de lo que dices en voz alta

- Gartner, 28 ago 2025: PC con IA 15,6 % (2024), 31 % (2025), 54,7 % (2026, proyección).
- MIMII DUE: Tanabe et al., Hitachi (2021), arXiv:2105.02702, doi:10.5281/zenodo.4740355. Bombas, `dev_data_pump`, CC BY-NC-SA 4.0.
- Cuentas (sin fuente externa): 16 000 muestras/s × 2 B = 32 000 B/s ≈ 115 MB por hora ≈ 2,76 GB al día por bomba; × 1 000 = 2,76 TB al día. Un evento cada 10 s = 8 640 por bomba al día; × 1 000 ≈ 8,64 M. Un resumen por minuto = 1 440 por bomba al día; × 1 000 ≈ 1,44 M.
- AUC como probabilidad de que un positivo al azar quede por encima de un negativo al azar: Fawcett, *An introduction to ROC analysis*, Pattern Recognition Letters (2006).
- Cifras medidas: `poc-devopsdays/build/metrics.json` y `device_bench.json`, vía `talk/tools/metrics.py`.
- SageMaker Neo y Edge Manager (pregunta difícil): fin de Edge Manager el 26 de abril de 2024 y la recomendación de ONNX y Greengrass V2, https://docs.aws.amazon.com/sagemaker/latest/dg/edge-eol.html · frameworks de Neo para el borde (ONNX hasta 1.7), https://docs.aws.amazon.com/sagemaker/latest/dg/neo-supported-devices-edge-frameworks.html · equipos soportados, https://docs.aws.amazon.com/sagemaker/latest/dg/neo-supported-devices-edge-devices.html · la prueba, en la evidencia del ensayo del 12 de octubre.
- Documentación de AWS (dicha en voz alta, nunca en una lámina):
  - Cola `mqtt.spooler` del nucleus, en memoria y de 2,5 MB por defecto: https://docs.aws.amazon.com/greengrass/v2/developerguide/greengrass-nucleus-component.html
  - Cola en disco: https://docs.aws.amazon.com/greengrass/v2/developerguide/disk-spooler-component.html
  - Nucleus lite, 5 MB de almacenamiento y menos de 15 MB de RAM: https://docs.aws.amazon.com/greengrass/v2/developerguide/greengrass-nucleus-lite-component.html
  - Digest calculado al crear la versión y verificado en el equipo: https://docs.aws.amazon.com/greengrass/v2/developerguide/component-recipe-reference.html
  - `failureHandlingPolicy` = `ROLLBACK` por defecto: https://docs.aws.amazon.com/greengrass/v2/APIReference/API_DeploymentPolicies.html
  - `abortConfig` y `jobExecutionsRolloutConfig`: https://docs.aws.amazon.com/cli/latest/reference/greengrassv2/create-deployment.html
  - EKS local en Outposts sin red: https://docs.aws.amazon.com/eks/latest/userguide/eks-outposts-network-disconnects.html
  - Greengrass en Docker: https://docs.aws.amazon.com/greengrass/v2/developerguide/run-greengrass-docker.html
- Breck et al., *The ML Test Score* (Google, 2017).
- Métodos de drift (A6): documentación de Evidently y NannyML; crítica a los umbrales del PSI: arXiv:2303.01227.
- Regulación (A7): Reglamento (UE) 2024/1689, arts. 12, 19 y 72, con las fechas del Reglamento (UE) 2026/1744; NIST AI 100-1; ISO/IEC 42001:2023.
