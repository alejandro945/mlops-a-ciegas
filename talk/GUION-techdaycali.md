# Guion · MLOps a ciegas · Tech Day Cali 2026

Solo lo que dices. **[CLIC]** avanza la lámina · *(pausa)* es silencio · lo demás en cursiva es para ti. Lo que va entre comillas no se memoriza palabra por palabra, salvo la apertura, las cifras y el cierre. Cómo estudiarlo: `talk/private/ESTUDIO.md` (no se sube al repo). Fuentes y datos de respaldo: `NOTAS-de-apoyo.md`. Las notas del deck (tecla **N**) salen de este archivo.

Es el guion de DevOpsDays Bogotá con dos láminas nuevas: el juez (paso 4) y el envío por lotes (paso 5).

**22:30** de contenido aproximadamente. Reloj al entrar a cada divisor: 2:10 · 4:50 · 7:15 · 14:55.

---

## 1 · MLOps a ciegas
<!-- id: portada -->
**0:10** · sin clics

*(En pantalla mientras te presentan. Cuando te den la palabra, pasa a la 2.)*

---

## 2 · Sobre mí
<!-- id: quien -->
**0:25** · sin clics

"Buenos días. Soy Alejandro Varela, Lead Cloud Engineer en EPAM. Trabajo como arquitecto en la nube, y parte de ese trabajo es diseñar cómo se despliegan y se operan modelos de IA en equipos de campo: lugares sin conectividad estable y sin nadie que los atienda."

"Hoy les voy a mostrar el patrón que uso para eso, con una implementación completa en AWS."

---

## 3 · La IA ya corre en el dispositivo
<!-- id: cien -->
**0:25** · 2 clics

"Esto no es un caso aislado. En el mundo hay cada vez más dispositivos inteligentes conectados: sensores, cámaras, máquinas, medidores. En 2024 eran 18 mil quinientos millones."

**[CLIC]** "En 2025, 21 mil millones: más de dos por cada persona del planeta."

**[CLIC]** "Y para 2030 se proyectan 39 mil millones, casi el doble. Y cada vez más de ellos deciden donde están, sin preguntarle a la nube."

---

## 4 · Por qué el modelo baja al dispositivo
<!-- id: memes -->
**0:55** · 2 clics

"Hay tres razones para ejecutar el modelo en el dispositivo, y las tres se ven mejor con un caso concreto."

"Latencia: un vehículo autónomo frente a un obstáculo no puede esperar la respuesta de un modelo remoto. La ida y vuelta a la nube no cabe en el tiempo de frenado."

**[CLIC]** "Disponibilidad: un técnico en planta, de madrugada, consulta un asistente cuyo modelo vive en la nube, y la respuesta es «sin conexión». En una estación rural, ese es el estado normal."

**[CLIC]** "Privacidad: Face ID. El modelo corre en el teléfono y los datos biométricos quedan cifrados en el Secure Enclave; nunca salen del dispositivo. Lo único que sale es una decisión: sí o no."

"Y un detalle relevante para esta charla: Face ID se adapta a los cambios de apariencia en el propio dispositivo. Los datos cambian y el modelo se ajusta sin ir a la nube. Vamos a volver sobre esa idea."

"En nuestro caso, un micrófono genera 115 MB por hora, por bomba, sobre la red de una zona rural. No cabe, y tampoco debería salir de la estación."

---

## 5 · Contenido de la sesión
<!-- id: agenda -->
**0:15** · sin clics

"La charla tiene cuatro partes: el problema, el patrón de arquitectura, la implementación en seis pasos y la evidencia de una ejecución real en AWS."

---

## 6 · 01 · El problema
<!-- id: div1 -->
**0:05** · *reloj: 2:10*

"Empecemos por el problema."

---

## 7 · MLOps en la nube: un loop cerrado
<!-- id: nube -->
**0:20** · sin clics

"Cuando el modelo vive en la nube, el ciclo está resuelto. Todas las inferencias pasan por un endpoint: se registran, se comparan contra la línea base del entrenamiento, se alerta cuando la distribución cambia y se reentrena."

"Funciona por una razón: todo pasa por un punto que controlamos."

---

## 8 · Las restricciones de la estación
<!-- id: edge -->
**1:00** · 5 clics

"Al llevar el modelo a la estación, ese punto de control desaparece. Aparecen cinco restricciones."

**[CLIC]** "Primera, recursos: memoria limitada y hardware heterogéneo. Una estación tiene ARM, otra un x86 de varias generaciones atrás, la más nueva una NPU."

**[CLIC]** "Segunda, conectividad: cuando cae el enlace, cae todo el ciclo de la nube."

**[CLIC]** "Tercera, el dato crudo no puede salir: por volumen y por política."

**[CLIC]** "Cuarta, y la menos medida: la latencia depende de la energía. Con batería baja o temperatura alta, el procesador reduce su frecuencia y el mismo modelo tarda más."

**[CLIC]** "Quinta, los datos: hay pocos ejemplos de falla y la distribución de lo normal cambia con el tiempo; el sensor envejece, la bomba cambia de régimen. Eso es drift. Y la calidad de los datos de entrenamiento define todo lo demás; en el acto 3 vamos a ver qué pasa cuando falla."

"Todas las prácticas de MLOps en la nube asumen que las inferencias pasan por nosotros. En el borde, ese supuesto no se cumple."

---

## 9 · Un panel en verde no mide el modelo
<!-- id: tablero -->
**1:15** · 3 clics · *la idea central: ve despacio*

"La pregunta operativa es: ¿cómo sabemos si el modelo de la estación está funcionando? La respuesta habitual es el panel de infraestructura."

**[CLIC]** "Servicio arriba, CPU normal, memoria normal. Todo en verde. Desde operaciones, el sistema está sano."

**[CLIC]** "Pero la pregunta correcta es otra: ¿el modelo todavía distingue una bomba sana de una que falla? Eso lo mide el AUC: 1 es separación perfecta, 0,5 es azar."

"Con las condiciones de entrenamiento, este modelo tiene un AUC de 0,69. Cambiamos la velocidad de operación de la bomba y cae a 0,57." *(pausa)* "Prácticamente azar. Y las falsas alarmas pasan del 6 al 18 por ciento."

**[CLIC]** "Sin un solo error en los logs. La infraestructura está sana; el modelo dejó de discriminar." *(pausa)*

"Esto está medido con los mismos audios que escucharon al principio. Un servicio caído genera alertas. Un modelo degradado sigue respondiendo a tiempo, con un 200 OK."

"Monitorear la infraestructura no es monitorear el modelo. En el paso seis vamos a ver qué hay que medir."

---

## 10 · 02 · El patrón
<!-- id: div2 -->
**0:05** · *reloj: 4:50*

"Veamos cómo se gobierna esto, empezando por el equipo."

---

## 11 · Arquitectura del equipo en la estación
<!-- id: equipo -->
**0:45** · 3 clics

"En la base: el micrófono sobre la bomba y el modelo con su runtime. La inferencia ocurre localmente, en milisegundos, con o sin red. El audio entra y no sale."

**[CLIC]** "Encima, el modelo no se distribuye como un archivo suelto: es un artefacto versionado y con huella criptográfica. Si se altera, no se instala."

**[CLIC]** "Luego, un agente. Nadie empuja cambios a la estación: el agente consulta, cuando hay conectividad, cuál es el estado deseado."

**[CLIC]** "Y arriba, una cola de eventos persistente. Cada decisión queda registrada hasta que se restablece el enlace."

---

## 12 · Cinco piezas para gobernarlo
<!-- id: flujo -->
**1:05** · 6 clics

"Este es el punto de partida en muchas organizaciones: se copia el modelo al equipo y se asume que funciona. No hay versión, no hay trazabilidad, no hay forma de revertir."

**[CLIC]** "El patrón tiene cinco piezas. Primera: optimización por hardware. Se entrena una vez y se compila para cada tipo de chip."

**[CLIC]** "Segunda: un artefacto verificable, con versión y huella, en un registro inmutable."

**[CLIC]** "Tercera: estado deseado. El plano de control declara qué debe tener cada equipo y el equipo converge cuando hay conectividad."

**[CLIC]** "Cuarta: eventos de inferencia. Cada decisión se registra; sin red, se encola."

**[CLIC]** "Quinta: un gate que evalúa esos eventos y decide automáticamente si se avanza o se revierte. Es el ciclo rápido, de minutos."

**[CLIC]** "Esos eventos dicen cuándo reentrenar y en qué estación, y el mantenimiento pone las etiquetas. El audio para reentrenar se recolecta de forma selectiva: alertas, casos dudosos y una muestra de lo normal. Ese es el ciclo lento, de días. Y de forma transversal, identidad, mínimo privilegio, cifrado y auditoría. El patrón no depende de ningún proveedor de nube."

---

## 13 · El mismo patrón en AWS
<!-- id: aws -->
**0:30** · 5 clics · *ritmo ágil*

"La misma arquitectura, con servicios de AWS."

**[CLIC]** "SageMaker AI entrena." **[CLIC]** "S3 almacena cada versión e IoT Greengrass la empaqueta como componente." **[CLIC]** "El estado deseado es un despliegue de Greengrass, que llega por IoT Core con un certificado por dispositivo."

**[CLIC]** "Los eventos regresan por IoT Core y una regla los envía a CloudWatch; los clips que vale la pena guardar suben a S3 por lotes, con stream manager." **[CLIC]** "Y el gate es un juez en Step Functions, que compara la versión nueva en sombra antes de promoverla. Una alarma con una Lambda queda como red de seguridad."

---

## 14 · 03 · Los seis pasos
<!-- id: div3 -->
**0:10** · *reloj: 7:15*

"La implementación, en seis pasos: entrenar, optimizar, empaquetar, desplegar, operar sin red y monitorear."

---

## 15 · Paso 1 · Entrenar con sonido normal
<!-- id: entrenar -->
**0:45** · 2 clics

"Paso uno: el modelo se entrena únicamente con audio de bombas sanas."

**[CLIC]** "Es un autoencoder: aprende a reconstruir el sonido normal, y el error de reconstrucción es el score de anomalía. Si no puede reconstruir lo que escucha, algo cambió."

**[CLIC]** "El resultado se publica en S3: el modelo en ONNX, el umbral y el código de preprocesamiento. El preprocesamiento viaja con el modelo porque la causa más común de degradación silenciosa es entrenar con una transformación y servir con otra. Cada versión, en su propio prefijo: nunca se sobrescribe."

---

## 16 · Paso 2 · Optimizar para cada chip
<!-- id: optimizar -->
**1:00** · 3 clics

"Paso dos: el modelo se entrena en 32 bits y se exporta a ONNX."

**[CLIC]** "Para el equipo de borde se cuantiza a 8 bits, se simplifica el grafo y se compila con el toolchain de cada fabricante."

**[CLIC]** "La consecuencia operativa: no hay un artefacto, hay uno por tipo de hardware. Y la restricción que manda es la memoria."

**[CLIC]** "Medido en el equipo del ensayo: de 32 a 8 bits, el modelo pasa de 464 a 127 KB, la latencia por clip de 14,4 a 12,7 milisegundos, y la decisión coincide en el 98 % de los casos."

"En una estación de desarrollo, la mejora era casi del doble. En el equipo real, el cuello de botella es el preprocesamiento del audio, no el modelo. Por eso se mide en el hardware de destino, y en condiciones reales: batería baja y temperatura alta."

---

## 17 · Paso 3 · Empaquetar como componente
<!-- id: componente -->
**0:55** · 4 clics

"Paso tres: en IoT Greengrass, el modelo se empaqueta como componente. Esta es la receta, resumida."

**[CLIC]** "Los artefactos vienen de S3, y Greengrass verifica la huella de cada uno antes de instalar."

**[CLIC]** "El arranque no descarga nada: las dependencias ya están en el equipo. Un componente que instala librerías al iniciar no arranca sin conectividad."

**[CLIC]** "El umbral es configuración: se ajusta con un despliegue, sin reentrenar."

**[CLIC]** "Y los permisos son mínimos: el componente solo puede publicar en un tópico, station/events."

"Una regla operativa: una versión publicada es inmutable. Si se modifica un artefacto sin cambiar la versión, la huella no coincide y el despliegue falla."

---

## 18 · Paso 4 · Desplegar por rings
<!-- id: anillos -->
**0:55** · 3 clics

"Paso cuatro: cómo llevar una versión nueva a mil equipos sin afectarlos a todos a la vez. Despliegue por rings, donde cada ring es un thing group. El ring 0 es una sola estación: el canary."

**[CLIC]** "Si el canary pasa el gate, continúa el ring 1, en olas de tamaño creciente."

**[CLIC]** "Greengrass incluye dos protecciones: cancela el despliegue si fallan demasiados equipos, y revierte en el equipo que no logra iniciar la versión nueva."

**[CLIC]** "Lo que Greengrass no trae es el gate sobre el modelo: algo que compare la versión nueva con la que ya funciona antes de dejarla decidir. Ese lo construí, y es la siguiente lámina."

"La distinción es importante: Greengrass revierte despliegues que fallan. Un modelo que se instala correctamente y decide mal es, para Greengrass, un despliegue exitoso."

---

## 19 · Paso 4 · ¿Cuándo volver atrás?
<!-- id: juez -->
**1:10** · 4 clics

"La pregunta difícil es cuándo volver atrás. Si espero a que una alarma vea fallas no detectadas, la versión nueva ya estuvo decidiendo mal. Por eso el gate es un juez: una máquina de estados en Step Functions, que actúa antes."

"Primero, sombra: el canary recibe la versión nueva, pero decide la anterior. La nueva solo dice qué habría hecho."

**[CLIC]** "Luego espera y mide. Escucha clips reales, dos minutos en la demo y días en producción, y en Logs Insights compara sobre los mismos clips: ¿cuántas fallas que la v1 oyó se le escaparon a la v2? ¿Cuántas veces alertó sola?"

**[CLIC]** "Si pasa, promueve: ring 0, ring 1, y la guarda como la última versión buena. Si todavía hay pocos clips, sigue esperando."

**[CLIC]** "Si no pasa, rechaza: el canary vuelve solo a la versión activa y llega un aviso. La versión nueva nunca decidió nada."

**[CLIC]** "La regla de la demo: al menos 20 clips, no más del 10 % de las fallas que la v1 sí oyó, y no más del 20 % de alertas que da sola." *(pausa)* "Y lo importante: el juez no necesita saber la verdad. Compara dos modelos sobre el mismo audio. Por eso sirve en producción, donde la etiqueta de la falla llega semanas después."

"La alarma y la Lambda siguen ahí, como red de seguridad, para lo que se le escape al juez."

---

## 20 · Paso 5 · Operar sin red
<!-- id: sinred -->
**0:30** · sin clics

"Paso cinco: operación desconectada. Greengrass encola los eventos localmente hasta que vuelve la conectividad. Para equipos con muy poca memoria existe una versión ligera del agente, escrita en C."

"La estación sigue decidiendo y alertando sin red, porque todo lo necesario está en el equipo. Un detalle de diseño: la cola por defecto vive en memoria y descarta mensajes al llenarse. Para desconexiones largas, debe ir a disco."

---

## 21 · Paso 5 · Enviar por lotes
<!-- id: lotes -->
**1:00** · 2 clics

"Y cuando sí hay red, ¿cómo se envía? En la demo, cada clip manda su evento: uno cada tres segundos." *(señala la fila de arriba)* "Cada envío despierta la radio y espera su confirmación. Veinte veces por minuto, la radio casi no duerme: eso es batería, CPU y calor, en un gabinete al sol."

**[CLIC]** "Por lotes: lo normal espera en la cola local y sale una vez por minuto. Lo urgente no espera: una alerta sale en el momento."

**[CLIC]** "Cuatro estrategias. Juntar por tiempo o por tamaño. Que lo urgente no haga fila. Resumir lo normal con conteos y percentiles, y mandar el detalle solo cuando algo cambia. Y comprimir y priorizar: si la cola se llena, lo primero que se descarta es lo normal."

"En la nube también se nota: IoT Core cobra los mensajes en bloques de 5 KB. Un evento de unos cientos de bytes paga el bloque completo; veinte eventos juntos caben en uno o dos."

"En la demo los eventos van uno por uno, para verlos en vivo. Los clips que vale la pena guardar ya suben por lotes, con stream manager."

---

## 22 · Paso 6 · Monitorear lo que decide el modelo
<!-- id: monitoreo -->
**1:15** · 3 clics

"Paso seis: desde la nube no vemos el audio, vemos los eventos del modelo. Unos cientos de bytes por inferencia, que pasan por IoT Core, una regla, CloudWatch y una alarma conectada al rollback."

"La pregunta es qué medir. Propongo tres señales."

**[CLIC]** "Primera, la entrada: ¿el sensor sigue entregando datos confiables? Un aumento gradual indica envejecimiento; un salto abrupto indica falla o manipulación. La velocidad del cambio distingue un caso del otro."

**[CLIC]** "Segunda, la salida: ¿cambió la distribución de las decisiones? Se compara la distribución de scores de la última hora contra la de referencia, con una métrica como PSI."

**[CLIC]** "Tercera, la autenticidad: ¿el modelo en ejecución es el que desplegamos? Cada evento incluye la versión y la huella del modelo." *(pausa)* "Esa huella la reporta el propio equipo, y un equipo comprometido puede reportar lo que quiera. Por eso necesita arranque seguro y su llave en un TPM."

"En la PoC, el gate usa la verdad de cada clip, porque sé qué audio está sonando. En producción esa etiqueta llega tarde, con la orden de mantenimiento. Las tres señales no la necesitan: funcionan desde el primer día."

---

## 23 · 04 · La evidencia en AWS
<!-- id: div4 -->
**0:05** · *reloj: 14:55*

"Ahora, la evidencia: la misma arquitectura, ejecutada en AWS."

---

## 24 · Demo
<!-- id: poc -->
**0:25** · sin clics

"Lo único simulado son las bombas: cinco contenedores, cada uno con el agente real de Greengrass. La bomba 1 es el canary; las otras cuatro, el ring 1. Todo lo demás es AWS real, con audio real e infraestructura en Terraform. Lo que sigue es esa ejecución, del 16 de noviembre, reproducida tal como llegó: los tres actos que siguen son esa página corriendo dentro de la lámina (talk/estacion.html); cada clic salta al momento siguiente. La tecla D la abre aparte, por si quieres manejarla a mano: espacio reproduce, las flechas saltan de acto en acto y la tecla A muestra cómo se ve ese momento en la consola de AWS."

---

## 25 · El modelo, versionado
<!-- id: artefacto -->
**0:25** · sin clics

"Primero, el artefacto. En S3, cada versión en su propia carpeta, y aparte los clips que valen la pena guardar. En Greengrass, el componente con sus versiones: la 1.0.0, la 2.0.0 y la 1.1.0, que es la 1.0.0 decidiendo con la 2.0.0 en sombra. Nada se sobrescribe."

---

## 26 · La flota, en línea
<!-- id: flota -->
**0:20** · sin clics

"La flota: cada bomba es una thing de AWS IoT, con su propio certificado. Cinco equipos en dos rings, todos sanos."

---

## 27 · Lo que reporta
<!-- id: reporte -->
**0:20** · sin clics

"Y esto es lo que reportan: el dashboard, organizado por las tres señales: entrada, salida y autenticidad. Con esto en marcha, tres pruebas."

---

## 28 · Acto 1 · Escuchar
<!-- id: acto1 -->
**0:50** · sin clics · *la estación corre sola en la lámina; deja que la miren*

"Esto es la estación en vivo, reproduciendo la ejecución real: a la izquierda las cinco bombas, cada una con su versión, su score contra el umbral y su decisión; en el centro, cada punto es un evento viajando a la nube; a la derecha, lo que AWS cuenta."

"Decisiones normales, hasta que inyecto el audio de falla en la bomba 3. En ese mismo clip el score supera el umbral y la tarjeta pasa a ALERT. En la nube sube el contador de alertas."

"Esa es la respuesta a la pregunta inicial: la bomba B era la que fallaba." *(pausa)*

"Y lo único que salió de la estación fue ese punto: una línea de unos cientos de bytes, no el audio."

---

## 29 · Acto 2 · Sin red, y una deriva
<!-- id: acto2 -->
**1:00** · 2 clics

"Segundo acto: desconecto la bomba 3 de la red. Su tarjeta se pone punteada y los eventos se van acumulando en la cola local, mientras las otras cuatro siguen llegando."

**[CLIC]** "Cuarenta y cinco segundos después vuelve la red, y los eventos guardados llegan todos juntos, cada uno con su hora de decisión y hasta cuarenta y tantos segundos tarde. Ninguno se perdió. La bomba siguió decidiendo sin red."

**[CLIC]** "Otra prueba: cambio el régimen de la bomba 5. No hay un solo error, pero la entrada salta de 0,8 a 2,2 desviaciones de lo que el modelo aprendió. Es exactamente el tipo de deriva que el panel de infraestructura no ve."

---

## 30 · Acto 3 · El juez
<!-- id: acto3 -->
**1:30** · 3 clics · *el punto culminante: ve despacio*

"Tercer acto: la versión 2.0.0, entrenada con más datos. No la despliego: se la entrego al juez." *(pausa)* "El juez la pone en sombra en el canary: la bomba 1 recibe la v2, pero sigue decidiendo la v1. La v2 solo dice qué habría hecho. Abajo a la derecha, la máquina de estados: desplegada, horneando."

"Ahora inyecto una falla en la bomba 1. La v1 alerta; la v2, en sombra, dice «normal»."

**[CLIC]** "El juez mide en Logs Insights sobre los mismos clips: cuántas fallas que la v1 oyó se le escaparon a la v2. Dieciséis de treinta y cuatro. Y la rechaza: el canary vuelve a la v1 sola y llega el aviso."

"La causa: el audio adicional incluía un periodo en que una bomba ya estaba fallando, y nadie lo validó. El modelo aprendió la falla como comportamiento normal. No es un error de código; es un error de datos."

**[CLIC]** "Así se ve en la consola, en Step Functions: Reject, Notify, CandidateRejected, con el número de clips y de fallas no oídas."

**[CLIC]** *(mirando a la sala)* "La v2 nunca decidió. Nadie tocó el equipo y el ring 1 nunca la vio."

---

## 31 · Acto 3b · Sin juez: la red de seguridad
<!-- id: acto3b -->
**1:00** · 4 clics

"¿Y si no hubiera juez? Lo probé también: despliego la 2.0.0 directo al ring 0. Llega en segundos, sin errores. Para Greengrass, un despliegue exitoso."

**[CLIC]** "Inyecto la falla y la v2 responde «normal»: fallas no oídas. La nube las cuenta por minuto; la barra sube hasta el umbral."

**[CLIC]** "La métrica cruza el umbral, la alarma pasa a ALARM, la Lambda restaura la última versión buena y la bomba 1 vuelve a alertar. Un minuto y cincuenta segundos desde la falla, sin acceso al equipo."

**[CLIC]** "En la consola: los logs de la Lambda, con la vuelta a la 1.0.0 que creó ella, no yo. El ring 1 nunca recibió la 2.0.0."

**[CLIC]** "Greengrass revierte despliegues fallidos, no modelos equivocados. Esa fue la red de seguridad: la v2 alcanzó a decidir. Con el juez, nunca llega a decidir."

---

## 32 · Cinco recomendaciones
<!-- id: llevo -->
**1:05** · 4 clics · *reloj: 20:50 al entrar*

"Cinco recomendaciones para aplicar desde el lunes."

"Primera: traten el modelo como cualquier artefacto de software: versión, huella y firma, sobre un equipo con arranque seguro."

**[CLIC]** "Segunda: midan en el hardware de destino, en condiciones reales de energía y temperatura."

**[CLIC]** "Tercera: desplieguen por rings, con un juez que compare al modelo nuevo en sombra antes de dejarlo decidir."

**[CLIC]** "Cuarta: diseñen para operar sin conectividad: que decida local y que envíe por lotes."

**[CLIC]** "Quinta: monitoreen tres señales: entrada, salida y autenticidad."

*(Si el reloj marca 20:30 o menos: «Una lección del primer montaje: ninguna bomba arrancaba. El problema era que el instalador de Greengrass determina el formato de configuración por la extensión del archivo, y el mío no tenía extensión. Una línea. Por eso se prueba en el entorno real.»)*

---

## 33 · Recursos y contacto
<!-- id: recursos -->
**0:15** · sin clics

"Dos códigos QR: el repositorio, con el código, la infraestructura y estas láminas; y mi LinkedIn, por si quieren seguir la conversación."

---

## 34 · Gracias
<!-- id: cierre -->
**0:15** · sin clics

"Muchas gracias. Con gusto respondo sus preguntas."

*Anexos: la tecla A abre A1; las flechas los recorren; M o Esc te devuelven. A1 evento · A2 red de seguridad · A3 qué revierte Greengrass · A4 permisos y costo · A5 a producción · A6 drift · A7 regulación · A8 fuentes · A9 golden signals · A10 audio contra eventos · A11 seguridad del equipo.*

---

## A1 · El evento, campo por campo
<!-- id: a1 -->
"Cada evento identifica el dispositivo, la versión y la huella del modelo; incluye un número de secuencia y la marca de tiempo de la decisión; el score, el umbral y la decisión; un resumen de la entrada y la latencia. La regla de IoT agrega la hora de llegada: la diferencia es el tiempo que el equipo estuvo desconectado."

---

## A2 · La red de seguridad, paso a paso
<!-- id: a2 -->
"Esto es lo que pasa si algo se le escapa al juez; es lo que vimos en el acto 3. La única acción manual es el despliegue de la 2.0.0 al ring 0. El equipo obtiene su estado deseado, descarga de S3, verifica la huella e instala: para Greengrass, todo correcto. Pero la versión nueva no detecta las fallas. Cada evento pasa por la regla de IoT, llega a CloudWatch y un filtro de métrica cuenta las fallas no detectadas. Con ocho en un minuto, la alarma invoca la Lambda, que consulta en Parameter Store la última versión aprobada y la despliega solo en el ring 0."

---

## A3 · ¿Qué revierte Greengrass solo?
<!-- id: a3 -->
"Greengrass revierte en tres casos: si la huella de un artefacto no coincide, si el componente no instala o no inicia, y si fallan demasiados equipos del ring. No detecta un modelo que se ejecuta correctamente y decide mal. Eso solo lo detectan los eventos del modelo y una alarma sobre ellos."

---

## A4 · Permisos y costo
<!-- id: a4 -->
"Cada componente tiene el mínimo privilegio: el equipo lee su bucket y publica en su tópico, con identidad propia; la regla escribe en su log group; la Lambda crea el despliegue y lee un parámetro; el juez despliega, consulta los logs, escribe la última versión buena y avisa por SNS. El costo lo domina la instancia EC2, y todo se elimina con un destroy desde GitHub Actions."

---

## A5 · De la demo a producción
<!-- id: a5 -->
"Para una flota real cambian cinco cosas: un resumen por minuto en lugar de un evento por inferencia; la cola en disco; el agente ligero en equipos pequeños; varios canary y días de sombra antes de que el juez promueva; y la verdad de la falla llega tarde, con la orden de mantenimiento."

---

## A6 · ¿Qué método de drift uso?
<!-- id: a6 -->
"Depende del tipo de dato. PSI para variables discretizadas, con umbrales más convencionales que estadísticos. Kolmogorov-Smirnov para muestras pequeñas. Wasserstein para cuantificar el desplazamiento. Jensen-Shannon, acotada entre 0 y 1, conveniente para alertar. En la PoC uso la distancia de cada clip a la huella de lo normal."

---

## A7 · Regulación
<!-- id: a7 -->
**3 clics**

"En Europa, el AI Act exige a los sistemas de alto riesgo registro automático de eventos durante todo su ciclo de vida, retención mínima de seis meses y monitoreo posterior a la comercialización."

**[CLIC]** "En Estados Unidos, el AI Risk Management Framework del NIST: voluntario, pero se convirtió en el vocabulario común."

**[CLIC]** "Y la ISO/IEC 42001: un sistema de gestión de IA, certificable, con la lógica de la 27001."

**[CLIC]** "Los tres exigen lo mismo que necesitamos para operar: qué se ejecuta, qué decidió y cómo revertirlo."

---

## A8 · Fuentes
<!-- id: a8 -->
"Las fuentes están aquí y en el repositorio. Los audios son de MIMII DUE, de Hitachi, bajo licencia CC BY-NC-SA."

---

## A9 · Las golden signals de un modelo
<!-- id: senales -->
"Para un servicio, las golden signals son latencia, tráfico, errores y saturación. Para un modelo: qué decide, con qué confianza, si la entrada se parece a la del entrenamiento y qué versión corre en cada equipo. Ninguna es suficiente por sí sola."

---

## A10 · Audio crudo contra eventos, con mil bombas
<!-- id: costo -->
**2 clics**

"Enviar el audio crudo de mil bombas: 2,76 terabytes al día."

**[CLIC]** "Un evento cada 10 segundos: 8,64 millones de mensajes al día."

**[CLIC]** "Un resumen por minuto: 1,44 millones. Y el audio permanece en la estación."

---

## A11 · Antes de proteger el modelo, protege el equipo
<!-- id: seguridad -->
**4 clics** · *si preguntan por la seguridad del equipo*

"Estos equipos están físicamente expuestos: cualquiera puede abrir el gabinete de una estación rural. Antes de hablar de ataques al modelo, hay cuatro controles del equipo que son prerrequisito. Primero, arranque seguro: el equipo solo ejecuta software firmado."

**[CLIC]** "Segundo, protección de la identidad: la llave privada del certificado no puede vivir en la tarjeta SD, porque quien la copie suplanta al dispositivo. Va en un TPM o un elemento seguro."

**[CLIC]** "Tercero, actualizaciones autenticadas: solo se instala lo que trae la huella esperada, por un canal cifrado."

**[CLIC]** "Cuarto, privacidad del dato: el audio no sale y se cifra en reposo."

**[CLIC]** "Sin estos controles, nadie necesita engañar al modelo. Basta con reemplazarlo."
