# Guion · MLOps a ciegas · DevOpsDays Bogotá 2026

Solo lo que dices. **[CLIC]** avanza la lámina · *(pausa)* es silencio · lo demás en cursiva es para ti. Lo que va entre comillas no se memoriza palabra por palabra, salvo la apertura, las cifras y el cierre. Cómo estudiarlo: `talk/private/ESTUDIO.md` (no se sube al repo). Fuentes y datos de respaldo: `NOTAS-de-apoyo.md`. Las notas del deck (tecla **N**) salen de este archivo.

**21:50** de contenido para un espacio de 25 min + 5 de preguntas. Reloj al entrar a cada divisor: 4:00 · 6:40 · 9:05 · 15:45.

---

## 1 · MLOps a ciegas
<!-- id: portada -->
**0:10** · sin clics

*(En pantalla mientras te presentan. Cuando te den la palabra, pasa a la 2 y arranca con el gancho, sin saludar.)*

---

## 2 · Hace un año: se cae us-east-1
<!-- id: gancho -->
**0:40** · 2 clics · *antes de presentarte; sin saludar todavía*

"Hace un año, casi exacto, se cayó us-east-1. Muchos de ustedes lo vivieron desde operaciones: horas de servicios detenidos." *(señala el meme)* "Y nos recordó algo que ya sabíamos: buena parte de internet se apoya en una sola región." *(pausa)*

**[CLIC]** "Pero hubo una víctima que nadie esperaba: una marca de camas inteligentes, de unos dos mil dólares, que controlaba la temperatura y la inclinación desde la nube. Cuando la región cayó, las camas se quedaron en su último estado: calientes, inclinadas, en plena noche, con sus dueños encima." *(pausa)*

**[CLIC]** "Su solución de emergencia fue un modo sin conexión: control manual por Bluetooth, sin la inteligencia." *(pausa)* "La cama sabía detectar en qué etapa del sueño estabas, pero esa decisión vivía en la nube. Cuando la nube cayó, la cama dejó de pensar. Llevar esa decisión al dispositivo: eso es edge."

---

## 3 · Sobre mí
<!-- id: quien -->
**0:25** · sin clics

"Buenos días. Soy Alejandro Varela, Senior Cloud Engineer en EPAM, y eso es justamente mi trabajo: diseñar cómo se despliegan y se operan modelos de IA en equipos de campo, lugares sin conectividad estable y sin nadie que los atienda."

"Hoy les voy a mostrar el patrón que uso para eso, con una implementación completa en AWS. Pero antes de la arquitectura, quiero que escuchen algo."

---

## 4 · ¿Esta bomba está fallando?
<!-- id: suena -->
**1:10** · 3 clics · *el control reproduce los audios (10 s cada uno); un clic mientras suena lo detiene sin avanzar*

"Bomba A." **[CLIC]** *(suena A)*

"Bomba B." **[CLIC]** *(suena B)*

**[CLIC]** "¿Alguna de las dos está fallando? Levanten la mano: ¿la A?" *(cuenta)* "¿La B?" *(cuenta)* "¿Las dos?" *(cuenta)* "La respuesta la vamos a ver con datos más adelante."

"Los audios son reales, del dataset MIMII DUE de Hitachi. Este es el caso: un acueducto con estaciones de bombeo en zonas rurales, con conectividad intermitente y sin personal en sitio. En cada estación, un equipo de borde escucha las bombas y un modelo detecta cuándo una empieza a sonar distinto."

"Ustedes acaban de hacer exactamente lo que hace ese modelo: decidieron ahí mismo, con lo que ya saben y su experiencia, sin preguntarle a ChatGPT." *(pausa)* "Eso es inferencia en el borde: el conocimiento vive donde está el dato, y la decisión no depende de la red."

"De eso se trata «MLOps a ciegas»: cómo se opera un modelo que corre donde no lo vemos. Cómo le llega una versión nueva, cómo se revierte cuando falla y cómo reporta lo que decide, sin que el audio salga de la estación."

---

## 5 · La IA ya corre en el dispositivo
<!-- id: cien -->
**0:25** · 2 clics

"Esto no es un caso aislado: la inferencia se está moviendo de la nube al dispositivo. Según Gartner, en 2024, 16 de cada 100 PC nuevos traían hardware dedicado para IA."

**[CLIC]** "En 2025, 31."

**[CLIC]** "Y la proyección para este año es 55: más de la mitad. La misma tendencia se ve en teléfonos, vehículos y equipos industriales."

---

## 6 · Por qué el modelo baja al dispositivo
<!-- id: memes -->
**0:55** · 2 clics

"Hay tres razones para ejecutar el modelo en el dispositivo, y las tres se ven mejor con un caso concreto."

"Latencia: un vehículo autónomo frente a un obstáculo no puede esperar la respuesta de un modelo remoto. La ida y vuelta a la nube no cabe en el tiempo de frenado."

**[CLIC]** "Disponibilidad: un técnico en planta, de madrugada, consulta un asistente cuyo modelo vive en la nube, y la respuesta es «sin conexión». En una estación rural, ese es el estado normal."

**[CLIC]** "Privacidad: Face ID. El modelo corre en el teléfono y los datos biométricos quedan cifrados en el Secure Enclave; nunca salen del dispositivo. Lo único que sale es una decisión: sí o no."

"Y un detalle relevante para esta charla: Face ID se adapta a los cambios de apariencia en el propio dispositivo. Los datos cambian y el modelo se ajusta sin ir a la nube. Vamos a volver sobre esa idea."

"En nuestro caso, un micrófono genera 115 MB por hora, por bomba, sobre la red de una zona rural. No cabe, y tampoco debería salir de la estación."

---

## 7 · Contenido de la sesión
<!-- id: agenda -->
**0:15** · sin clics

"La charla tiene cuatro partes: el problema, el patrón de arquitectura, la implementación en seis pasos y la evidencia de una ejecución real en AWS."

---

## 8 · 01 · El problema
<!-- id: div1 -->
**0:05** · *reloj: 4:00*

"Empecemos por el problema."

---

## 9 · MLOps en la nube: un loop cerrado
<!-- id: nube -->
**0:20** · sin clics

"Cuando el modelo vive en la nube, el ciclo está resuelto. Todas las inferencias pasan por un endpoint: se registran, se comparan contra la línea base del entrenamiento, se alerta cuando la distribución cambia y se reentrena."

"Funciona por una razón: todo pasa por un punto que controlamos."

---

## 10 · Las restricciones de la estación
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

## 11 · Un panel en verde no mide el modelo
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

## 12 · 02 · El patrón
<!-- id: div2 -->
**0:05** · *reloj: 6:40*

"Veamos cómo se gobierna esto, empezando por el equipo."

---

## 13 · Arquitectura del equipo en la estación
<!-- id: equipo -->
**0:45** · 3 clics

"En la base: el micrófono sobre la bomba y el modelo con su runtime. La inferencia ocurre localmente, en milisegundos, con o sin red. El audio entra y no sale."

**[CLIC]** "Encima, el modelo no se distribuye como un archivo suelto: es un artefacto versionado y con huella criptográfica. Si se altera, no se instala."

**[CLIC]** "Luego, un agente. Nadie empuja cambios a la estación: el agente consulta, cuando hay conectividad, cuál es el estado deseado."

**[CLIC]** "Y arriba, una cola de eventos persistente. Cada decisión queda registrada hasta que se restablece el enlace."

---

## 14 · Cinco piezas para gobernarlo
<!-- id: flujo -->
**1:05** · 6 clics

"Este es el punto de partida en muchas organizaciones: se copia el modelo al equipo y se asume que funciona. No hay versión, no hay trazabilidad, no hay forma de revertir."

**[CLIC]** "El patrón tiene cinco piezas. Primera: optimización por hardware. Se entrena una vez y se compila para cada tipo de chip."

**[CLIC]** "Segunda: un artefacto verificable, con versión y huella, en un registro inmutable."

**[CLIC]** "Tercera: estado deseado. El plano de control declara qué debe tener cada equipo y el equipo converge cuando hay conectividad."

**[CLIC]** "Cuarta: eventos de inferencia. Cada decisión se registra; sin red, se encola."

**[CLIC]** "Quinta: un gate que evalúa esos eventos y decide automáticamente si se avanza o se revierte. Es el ciclo rápido, de minutos."

**[CLIC]** "Esos mismos eventos alimentan el reentrenamiento: el ciclo lento, de días. Y de forma transversal, identidad, mínimo privilegio, cifrado y auditoría. El patrón no depende de ningún proveedor de nube."

---

## 15 · El mismo patrón en AWS
<!-- id: aws -->
**0:30** · 5 clics · *ritmo ágil*

"La misma arquitectura, con servicios de AWS."

**[CLIC]** "SageMaker AI entrena." **[CLIC]** "S3 almacena cada versión e IoT Greengrass la empaqueta como componente." **[CLIC]** "El estado deseado es un despliegue de Greengrass, que llega por IoT Core con un certificado por dispositivo."

**[CLIC]** "Los eventos regresan por IoT Core y una regla los envía a CloudWatch." **[CLIC]** "Y el gate es una alarma de CloudWatch que invoca una Lambda, que restaura la última versión aprobada."

---

## 16 · 03 · Los seis pasos
<!-- id: div3 -->
**0:10** · *reloj: 9:05*

"La implementación, en seis pasos: entrenar, optimizar, empaquetar, desplegar, operar sin red y monitorear."

---

## 17 · Paso 1 · Entrenar con sonido normal
<!-- id: entrenar -->
**0:50** · 3 clics

"Paso uno: el modelo se entrena únicamente con audio de bombas sanas."

**[CLIC]** "Es un autoencoder: aprende a reconstruir el sonido normal, y el error de reconstrucción es el score de anomalía. Si no puede reconstruir lo que escucha, algo cambió."

**[CLIC]** "El resultado se publica en S3: el modelo en ONNX, el umbral y el código de preprocesamiento. El preprocesamiento viaja con el modelo porque la causa más común de degradación silenciosa es entrenar con una transformación y servir con otra."

**[CLIC]** "En la consola: un prefijo por versión, 1.0.0 y 2.0.0. Una versión publicada nunca se sobrescribe."

---

## 18 · Paso 2 · Optimizar para cada chip
<!-- id: optimizar -->
**1:00** · 3 clics

"Paso dos: el modelo se entrena en 32 bits y se exporta a ONNX."

**[CLIC]** "Para el equipo de borde se cuantiza a 8 bits, se simplifica el grafo y se compila con el toolchain de cada fabricante."

**[CLIC]** "La consecuencia operativa: no hay un artefacto, hay uno por tipo de hardware. Y la restricción que manda es la memoria."

**[CLIC]** "Medido en el equipo del ensayo: de 32 a 8 bits, el modelo pasa de 464 a 127 KB, la latencia por clip de 14,4 a 12,7 milisegundos, y la decisión coincide en el 98 % de los casos."

"En mi portátil, la mejora era casi del doble. En el equipo real, el cuello de botella es el preprocesamiento del audio, no el modelo. Por eso se mide en el hardware de destino, y en condiciones reales: batería baja y temperatura alta."

---

## 19 · Paso 3 · Empaquetar como componente
<!-- id: componente -->
**1:00** · 5 clics

"Paso tres: en IoT Greengrass, el modelo se empaqueta como componente. Esta es la receta, resumida."

**[CLIC]** "Los artefactos vienen de S3, y Greengrass verifica la huella de cada uno antes de instalar."

**[CLIC]** "El arranque no descarga nada: las dependencias ya están en el equipo. Un componente que instala librerías al iniciar no arranca sin conectividad."

**[CLIC]** "El umbral es configuración: se ajusta con un despliegue, sin reentrenar."

**[CLIC]** "Y los permisos son mínimos: el componente solo puede publicar en un tópico, station/events."

**[CLIC]** "En la consola: el componente con sus dos versiones. Una regla operativa: una versión publicada es inmutable. Si se modifica un artefacto sin cambiar la versión, la huella no coincide y el despliegue falla."

---

## 20 · Paso 4 · Desplegar por rings
<!-- id: anillos -->
**1:05** · 4 clics

"Paso cuatro: cómo llevar una versión nueva a mil equipos sin afectarlos a todos a la vez. Despliegue por rings, donde cada ring es un thing group. El ring 0 es una sola estación: el canary."

**[CLIC]** "Si el canary pasa el gate, continúa el ring 1, en olas de tamaño creciente."

**[CLIC]** "Greengrass incluye dos protecciones: cancela el despliegue si fallan demasiados equipos, y revierte en el equipo que no logra iniciar la versión nueva."

**[CLIC]** "Lo que Greengrass no trae es el gate sobre el modelo: una alarma sobre las fallas no detectadas que restaura la última versión aprobada. Ese lo construí."

"La distinción es importante: Greengrass revierte despliegues que fallan. Un modelo que se instala correctamente y decide mal es, para Greengrass, un despliegue exitoso."

**[CLIC]** "Este es el estado en la consola al terminar el ensayo: un despliegue activo por ring. Observen el nombre del despliegue del ring 0; lo explico en el acto 3."

---

## 21 · Paso 5 · Operar sin red
<!-- id: sinred -->
**0:40** · 2 clics

"Paso cinco: operación desconectada. Greengrass encola los eventos localmente hasta que vuelve la conectividad. Para equipos con muy poca memoria existe una versión ligera del agente, escrita en C."

**[CLIC]** "La estación sigue decidiendo y alertando sin red, porque todo lo necesario está en el equipo. Un detalle de diseño: la cola por defecto vive en memoria y descarta mensajes al llenarse. Para desconexiones largas, debe ir a disco."

**[CLIC]** "En la consola: cinco core devices, todos en estado Healthy. El comportamiento sin red lo vemos en el acto 2."

---

## 22 · Paso 6 · Monitorear lo que decide el modelo
<!-- id: monitoreo -->
**1:25** · 5 clics

"Paso seis: desde la nube no vemos el audio, vemos los eventos del modelo. Unos cientos de bytes por inferencia, que pasan por IoT Core, una regla, CloudWatch y una alarma conectada al rollback."

"La pregunta es qué medir. Propongo tres señales."

**[CLIC]** "Primera, la entrada: ¿el sensor sigue entregando datos confiables? Un aumento gradual indica envejecimiento; un salto abrupto indica falla o manipulación. La velocidad del cambio distingue un caso del otro."

**[CLIC]** "Segunda, la salida: ¿cambió la distribución de las decisiones? Se compara la distribución de scores de la última hora contra la de referencia, con una métrica como PSI."

**[CLIC]** "Tercera, la autenticidad: ¿el modelo en ejecución es el que desplegamos? Cada evento incluye la versión y la huella del modelo." *(pausa)* "Esa huella la reporta el propio equipo, y un equipo comprometido puede reportar lo que quiera. Por eso necesita arranque seguro y su llave en un TPM."

**[CLIC]** "En el ensayo, el gate usa la verdad de cada clip, porque sé qué audio está sonando. En producción esa etiqueta llega tarde, con la orden de mantenimiento. Las tres señales no la necesitan: funcionan desde el primer día."

**[CLIC]** "Este es el dashboard, organizado por esas tres señales. Lo vamos a ver con datos reales en un momento."

---

## 23 · A mano alzada
<!-- id: reflexion3 -->
**0:30** · 1 clic

"Antes de la evidencia, una pregunta: ¿quiénes saben con certeza qué versión de modelo corre en cada uno de sus equipos?" *(espera)* "Ahora, que bajen la mano quienes tuvieron que pensarlo." *(pausa)*

**[CLIC]** "En esta arquitectura, la respuesta sale del plano de control, sin acceder a ningún equipo: ring 0, versión 1.0.0, activo; ring 1, versión 1.0.0, activo."

---

## 24 · 04 · La evidencia en AWS
<!-- id: div4 -->
**0:05** · *reloj: 15:45*

"Pasemos a la evidencia: una ejecución completa en AWS."

---

## 25 · Lo que monté y corrí
<!-- id: poc -->
**0:30** · sin clics

"El entorno: cinco bombas simuladas, cada una un contenedor con el agente real de Greengrass sobre una instancia EC2. La bomba 1 es el canary; de la 2 a la 5, el ring 1. El audio es real y la infraestructura se despliega con Terraform desde GitHub Actions."

"Lo que sigue son los eventos y las métricas de la ejecución del 18 de octubre, sin editar."

---

## 26 · Acto 1 · Escuchar
<!-- id: acto1 -->
**0:50** · sin clics · *deja que lean primero*

"Esto es lo que se ve desde la nube: cada línea es una inferencia de la bomba 3, con versión, decisión, score y nivel de entrada."

"Decisiones normales, hasta que inyecto el audio de falla. En ese mismo clip, el score supera el umbral y el modelo emite una alerta."

"Esa es la respuesta a la pregunta inicial: la bomba B era la que fallaba." *(pausa)*

"Y lo único que salió de la estación fue esta línea, no el audio."

---

## 27 · Acto 2 · Sin red, y una deriva
<!-- id: acto2 -->
**1:00** · sin clics

"Segundo acto: desconecto la bomba 3 de la red. A la izquierda, sus eventos dejan de llegar mientras las otras cuatro siguen reportando."

"Cuarenta y cinco segundos después restablezco la conexión, y los eventos encolados llegan con su retraso registrado: 41, 32, 29, 20 segundos. Ninguno se perdió. La bomba siguió decidiendo sin red."

"A la derecha, otra prueba: cambio el régimen de la bomba 5. No hay un solo error, pero la señal de entrada salta de 0,8 a 1,8 desviaciones estándar. Es exactamente el tipo de deriva que el panel de infraestructura no ve."

---

## 28 · Acto 3 · Ring deployment y rollback
<!-- id: acto3 -->
**1:20** · 2 clics · *el punto culminante: ve despacio*

"Tercer acto: despliego la versión 2.0.0 solo en el ring 0. Esta versión se entrenó con más datos." *(pausa)* "Llega en 17 segundos, sin errores. Para Greengrass, un despliegue exitoso."

"Ahora inyecto una falla en la bomba 1. La versión nueva responde «normal» con la bomba fallando: fallas no detectadas."

"La causa: el audio adicional incluía un periodo en que una bomba ya estaba fallando, y nadie lo validó. El modelo aprendió la falla como comportamiento normal. No es un error de código; es un error de datos."

"Nadie interviene. La alarma pasa a ALARM, la Lambda restaura la versión 1.0.0 y la bomba 1 vuelve a alertar. Ochenta y ocho segundos desde la falla, sin acceso al equipo, y el ring 1 nunca recibió la versión defectuosa." *(pausa)* "Ese es el nombre que vieron en la consola: rollback."

**[CLIC]** "La alarma en CloudWatch: las fallas no detectadas superan el umbral de 8 por minuto, y la franja roja marca el periodo en ALARM."

**[CLIC]** *(mirando a la sala)* "Greengrass revierte despliegues fallidos, no modelos equivocados. Ese gate es responsabilidad nuestra."

---

## 29 · Cinco recomendaciones
<!-- id: llevo -->
**1:05** · 4 clics · *reloj: 19:30 al entrar*

"Cinco recomendaciones para aplicar desde el lunes."

"Primera: traten el modelo como cualquier artefacto de software: versión, huella y firma, sobre un equipo con arranque seguro."

**[CLIC]** "Segunda: midan en el hardware de destino, en condiciones reales de energía y temperatura."

**[CLIC]** "Tercera: desplieguen por rings, con un gate que evalúe al modelo, no solo al proceso."

**[CLIC]** "Cuarta: diseñen para operar sin conectividad: cola local y decisiones locales."

**[CLIC]** "Quinta: monitoreen tres señales: entrada, salida y autenticidad. Y mantengan el dato crudo en el equipo."

*(Si el reloj marca 19:50 o menos: «Una lección del primer montaje: ninguna bomba arrancaba. El problema era que el instalador de Greengrass determina el formato de configuración por la extensión del archivo, y el mío no tenía extensión. Una línea. Por eso se prueba en el entorno real.»)*

---

## 30 · La frase final: ¿esta bomba está fallando?
<!-- id: final -->
**0:45** · 3 clics · *el primer clic reproduce la bomba B*

"Volvamos a la pregunta inicial: ¿esta bomba está fallando?" **[CLIC]** *(suena B; córtala con otro clic a los tres segundos)*

"Ustedes la escucharon. La nube no, y no necesitaba hacerlo."

**[CLIC]** "Esto es todo lo que salió de la estación: bomba 3, versión 1.0.0, alerta. Unos cientos de bytes."

**[CLIC]** "No necesitamos ver el modelo. Necesitamos que el modelo nos cuente qué decide." *(pausa)*

"Les dejo una pregunta: si mañana uno de sus modelos deja de detectar lo que debe, ¿quién se va a enterar primero: ustedes, o la comunidad que se quedó sin agua?" *(pausa larga)*

---

## 31 · Recursos y contacto
<!-- id: recursos -->
**0:15** · sin clics

"El código, la infraestructura y estas láminas están en el repositorio del código QR."

---

## 32 · Gracias
<!-- id: cierre -->
**0:15** · sin clics

"Muchas gracias. Con gusto respondo sus preguntas."

*Anexos: la tecla A abre A1; las flechas los recorren; M o Esc te devuelven. A1 evento · A2 rollback · A3 qué revierte Greengrass · A4 permisos y costo · A5 a producción · A6 drift · A7 regulación · A8 fuentes · A9 golden signals · A10 audio contra eventos · A11 seguridad del equipo.*

---

## A1 · El evento, campo por campo
<!-- id: a1 -->
"Cada evento identifica el dispositivo, la versión y la huella del modelo; incluye un número de secuencia y la marca de tiempo de la decisión; el score, el umbral y la decisión; un resumen de la entrada y la latencia. La regla de IoT agrega la hora de llegada: la diferencia es el tiempo que el equipo estuvo desconectado."

---

## A2 · El rollback automático, paso a paso
<!-- id: a2 -->
"La única acción manual es el despliegue de la 2.0.0 al ring 0. El equipo obtiene su estado deseado, descarga de S3, verifica la huella e instala: para Greengrass, todo correcto. Pero la versión nueva no detecta las fallas. Cada evento pasa por la regla de IoT, llega a CloudWatch y un filtro de métrica cuenta las fallas no detectadas. Con ocho en un minuto, la alarma invoca la Lambda, que consulta en Parameter Store la última versión aprobada y la despliega solo en el ring 0."

---

## A3 · ¿Qué revierte Greengrass solo?
<!-- id: a3 -->
"Greengrass revierte en tres casos: si la huella de un artefacto no coincide, si el componente no instala o no inicia, y si fallan demasiados equipos del ring. No detecta un modelo que se ejecuta correctamente y decide mal. Eso solo lo detectan los eventos del modelo y una alarma sobre ellos."

---

## A4 · Permisos y costo
<!-- id: a4 -->
"Cada componente tiene el mínimo privilegio: el equipo lee su bucket y publica en su tópico, con identidad propia; la regla escribe en su log group; la Lambda crea el despliegue y lee un parámetro. El costo lo domina la instancia EC2, y todo se elimina con un destroy desde GitHub Actions."

---

## A5 · De la demo a producción
<!-- id: a5 -->
"Para una flota real cambian cinco cosas: un resumen por minuto en lugar de un evento por inferencia; la cola en disco; el agente ligero en equipos pequeños; el canary comparado contra el resto del ring; y la verdad de la falla llega tarde, con la orden de mantenimiento."

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
