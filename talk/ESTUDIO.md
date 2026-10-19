# Cómo estudiar «MLOps a ciegas»

La charla es el viernes 23 de octubre. No hay que memorizar el guion: hay que saber **el hilo**, **las frases que van textuales** y **las cifras**. Lo demás se dice con tus palabras.

---

## 1 · El hilo en seis frases

Si se te olvida todo, esto es la charla:

1. **Apertura:** ustedes oyeron la bomba; la nube no. Por eso «a ciegas».
2. **El problema:** en la estación no pasa nada por uno, y un panel en verde no dice si el modelo todavía oye.
3. **El patrón:** primero se protege el equipo; después cinco piezas: optimizar, artefacto, desired state, eventos y gate.
4. **Los seis pasos:** entrenar, optimizar, empaquetar, desplegar por rings, operar sin red y vigilar tres señales.
5. **El ensayo:** la B fallaba; sin red no se pierde nada; la v2 no oía y el gate la devolvió solo en 88 s.
6. **Cierre:** no necesitas ver el modelo; necesitas que te cuente.

---

## 2 · La escalera: una línea por lámina

Léela de arriba abajo hasta poder decirla sin mirar. La tercera columna es el **puente**: lo que te lleva a la siguiente.

| # | Lámina | La idea | Puente a la siguiente |
|---|---|---|---|
| 2 | Sobre mí | Diseño cómo llegan modelos a equipos de campo | «Vine a ponerles un audio» |
| 3 | ¿Está fallando? | Ustedes oyeron; desde la nube nadie oyó | «¿Y a mí qué me importa una bomba?» |
| 4 | Gartner | 16 → 31 → 55 de cada 100 PC | «¿Y por qué se baja?» |
| 5 | Memes | Latencia, sin conexión, privacidad (Face ID) | «115 megas por hora: no cabe» |
| 6 | 01 · El problema | Cuatro partes | «Arranquemos por el problema» |
| 7 | La nube | Todo pasa por el endpoint | «Ahora bajémoslo a la estación» |
| 8 | Restricciones | Recursos, red, audio, energía, datos | «¿Cómo sabe uno si está bien?» |
| 9 | Panel en verde | 0,69 → 0,57 con cero errores | «Abramos el equipo» |
| 10 | 02 · El patrón | — | — |
| 11 | El equipo | Modelo, artefacto, agente, cola | «¿Quién cuida la estación?» |
| 12 | Seguridad | Arranque, llave, updates, datos | «Le basta con reemplazarlo» |
| 13 | Cinco piezas | Cruzar los dedos → cinco piezas + dos loops | «El mismo dibujo en AWS» |
| 14 | En AWS | Cada casilla con nombre | «Paso por paso» |
| 15 | 03 · Los seis pasos | — | — |
| 16 | Entrenar | Solo sonido sano; el mecánico | «32 bits es mucho» |
| 17 | Optimizar | Un artefacto por chip; 464 → 127 KB | «Ahora se empaca» |
| 18 | Empaquetar | Receta: archivos, arranque, umbral, permisos | «¿Cómo llega a mil equipos?» |
| 19 | Rings | Canary, waves, el rollback que armé | «Fíjense en el nombre del ring 0» |
| 20 | Sin red | Cola local; se decide adentro | «¿Qué vigilamos?» |
| 21 | Tres señales | Entrada, salida, autenticidad | «¿Qué versión corre en sus equipos?» |
| 22 | A mano alzada | La respuesta sale de la nube | «Les muestro el ensayo» |
| 23 | 04 · El ensayo | — | — |
| 24 | Lo que monté | Cinco contenedores, AWS de verdad, 18 de octubre | «Acto uno» |
| 25 | Acto 1 | Normal → ALERT; la respuesta era la B | «Ahora le quito la red» |
| 26 | Acto 2 | Sin red nada se pierde; deriva de la bomba 5 | «Tercer acto: la versión nueva» |
| 27 | Acto 3 | v2 no oye; alarma, Lambda, 88 s | «Les dejo cinco cosas» |
| 28 | Recomendaciones | Artefacto, chip, rings, sin red, tres señales | «¿Se acuerdan de la pregunta?» |
| 29 | Frase final | Necesitas que te cuente | «Todo está en el repo» |

---

## 3 · Lo que va textual

Estas frases se dicen tal cual. Repítelas en voz alta hasta que salgan solas.

**Apertura (lámina 2):**
> «Buenos días. Soy Alejandro Varela, Senior Cloud Engineer en EPAM. Diseño cómo llegan y se gobiernan modelos de IA en equipos de campo, donde no hay nadie cerca. […] Pero no vine a hablar de mí. Vine a ponerles un audio.»

**La idea de la charla (lámina 3):**
> «Lo que ustedes acaban de hacer es justo lo que hace ese modelo: oír y decidir. La diferencia es que ustedes estaban aquí. Desde la nube, nadie oyó nada.»

**Los cinco remates:**
- Lámina 9: «Un modelo que dejó de oír sigue respondiendo a tiempo, con un 200 OK.»
- Lámina 12: «Sin esto, nadie necesita engañar a su modelo… le basta con reemplazarlo.»
- Lámina 19: «Un modelo que se instala perfecto y oye mal, para Greengrass, es un éxito.»
- Lámina 27: «Greengrass revierte despliegues fallidos, pero no modelos equivocados. Ese gate lo tiene que poner uno.»
- Lámina 29: «Uno no necesita ver el modelo. Necesita que el modelo le cuente.»

**Cierre (lámina 29):**
> «Si mañana uno de sus modelos deja de oír… ¿quién se va a enterar primero? ¿Ustedes… o la vereda que se quedó sin agua?»

---

## 4 · Las cifras

| Cifra | Qué es | Truco para recordarla |
|---|---|---|
| 16 → 31 → 55 | PC con chip de IA de cada 100 (2024, 2025, 2026) | Casi se duplica cada año |
| 115 MB por hora | Audio de una bomba | «Ciento quince, por bomba, por la red de una vereda» |
| 0,69 → 0,57 | AUC al cambiar la velocidad (0,5 = moneda) | «Casi una moneda» |
| 6 % → 18 % | Falsas alarmas | Se triplican |
| 464 → 127 KB | Modelo de 32 a 8 bits | Casi cuatro veces más chico |
| 14,4 → 12,7 ms | Por clip, en el equipo | Poco: el tiempo se va en preparar el audio |
| 98 % | Decisiones iguales con 8 bits | |
| 45 s | Bomba 3 sin red | Llegaron 41, 32, 29, 20 segundos tarde |
| 0,8 → 1,8 | Entrada de la bomba 5 con otra velocidad | Se duplica, sin un error |
| 17 s | La v2 llega al ring 0 | |
| 8 | Umbral de la alarma: fallas no oídas por minuto | |
| 88 s | De la falla a la v1 alertando otra vez | Sin que nadie toque nada |
| 21 % vs 16 % | Fallas detectadas, v1 contra v2 (set de prueba) | Para la pregunta «¿escogiste la v2?» |

---

## 5 · Cómo estudiarlo

**Por capas, no de corrido:**
1. **Lee el guion en voz alta una vez**, despacio, con el deck abierto. Marca las frases que no te salen naturales y cámbialas.
2. **Sube la escalera sin guion:** di la idea de cada lámina y su puente. Donde te trabes, ahí está lo que tienes que repasar.
3. **Ensaya por bloques:** apertura, problema, patrón, pasos, ensayo y cierre. Cada uno por separado, con el deck y el clicker.
4. **Ensaya completa, de pie y con cronómetro.** Anota el reloj en cada divisor (3:05 · 5:48 · 9:03 · 15:43) y compáralo.
5. **Grábate en audio** una vez completa y escúchala en el carro o caminando. Te vas a dar cuenta de las muletillas y de dónde corres.

**Trucos que funcionan:**
- **Los primeros 60 segundos y el cierre, diez veces.** Si arrancas bien, el resto sale. Si cierras bien, es lo que recuerdan.
- **Explícasela a alguien que no sea de tecnología** en cinco minutos, solo con el hilo. Si lo entiende, tú lo entiendes.
- **Preguntas difíciles como tarjetas:** lee la pregunta, responde en voz alta en dos frases y luego compara con la sección 6.
- **Las pausas también se ensayan:** después de «0,57», de «le basta con reemplazarlo» y de la pregunta final, cuenta dos segundos en silencio.
- **Practica los clics:** el error más común en el escenario es hablar de algo que todavía no está en pantalla.

**Después de cada ensayo, revisa:**
- [ ] ¿Duró entre 21 y 23 minutos?
- [ ] ¿Esperé de verdad las manos (láminas 3 y 22)?
- [ ] ¿Dije las cinco frases textuales?
- [ ] ¿Hice las pausas después de las cifras?
- [ ] ¿Mostré antes de explicar en los tres actos?
- [ ] ¿Hablé de algo antes de que saliera en pantalla?

---

## 6 · Plan hasta el viernes

| Día | Qué hacer | Tiempo |
|---|---|---|
| **Lunes 19** | Leer el guion en voz alta y ajustar frases. Escalera hasta poder decirla sin mirar | 1 h |
| **Martes 20** | Ensayo por bloques con el deck. Primeros 60 s y cierre, diez veces cada uno | 1 h |
| **Miércoles 21** | Dos ensayos completos con cronómetro; grabar uno. Preguntas difíciles como tarjetas | 1 h 30 |
| **Jueves 22** | Un ensayo completo frente a alguien, con preguntas al final. Escuchar la grabación. Nada nuevo desde aquí | 1 h |
| **Viernes 23** | En la mañana: la escalera una vez y los primeros 60 s. Antes de subir, la lista de abajo | 20 min |

---

## 7 · Preguntas difíciles

Responde en una o dos frases y, si hace falta, abre el anexo (tecla A). Si no sabes algo, dilo: «no lo he medido, pero así lo mediría».

- **«¿Por qué no lo mostraste en vivo?»** «El wifi de un evento es el peor lugar para depender de MQTT, y así ven exactamente lo que pasó, con la hora real de cada línea. El repo trae todo para correrlo.»
- **«¿Y SageMaker Neo?»** «Lo probé y no compiló tal cual: no soporta un operador de scikit-learn. Reescrito sí compila, pero necesita su propio runtime, DLR, que no se actualiza desde 2021. Y cuando AWS cerró Edge Manager en 2024, recomendó ONNX Runtime en el equipo y Greengrass para desplegar.»
- **«¿Por qué no despliegas el 8 bits?»** «En esa CPU ahorra poco, porque el tiempo se va preparando el audio. Con NPU sí valdría la pena, con un artefacto por chip.»
- **«¿Y AWS Wavelength?»** «Acerca el cómputo a la red 5G, pero sigue necesitando señal, y no hay zonas en Latinoamérica. Sin red, el modelo tiene que estar en el equipo.»
- **«¿Por qué no Kubernetes en cada estación?»** «En un equipo pequeño, un agente pesa mucho menos. En una planta grande sí: Outposts con EKS local, que sigue funcionando sin la región.»
- **«¿Y si el reloj del equipo está mal?»** «Cada evento trae un número de secuencia: el orden no depende del reloj. Al reconectar, el equipo corrige la hora y se marca el desfase.»
- **«¿La PoC tiene secure boot y TPM?»** «No: las bombas son contenedores en una EC2. La lámina de seguridad es lo que pondría en un equipo de verdad.»
- **«¿Por qué la autenticidad, si Greengrass ya verifica la huella?»** «Greengrass la verifica al instalar. La señal mira que lo que corre hoy siga siendo eso.»
- **«En producción no sabes si la bomba fallaba.»** «Cierto. Por eso las tres señales no lo necesitan, y la confirmación llega después, con la orden de mantenimiento.»
- **«¿Por qué AUC y no exactitud?»** «Porque con otra velocidad todos los scores suben y la detección puede subir junto con las falsas alarmas. La AUC no depende del umbral.»
- **«¿Por qué un autoencoder?»** «Las fallas son raras y no tienes ejemplos de todas. Es más fácil aprender cómo suena lo normal.»
- **«¿Escogiste la v2 para que fallara?»** «Los clips están escogidos para que sea repetible. Pero en todo el set de prueba la v1 detecta el 21 % de las fallas y la v2 el 16 %.»
- **«¿Se pierden eventos sin red?»** «En los ensayos, ninguno: la secuencia de cada bomba no tenía huecos. A veces llega uno repetido: MQTT con QoS 1 es "al menos una vez".»
- **«¿Qué pasa si la cola se llena?»** «Rechaza mensajes nuevos. Para horas sin red, la cola va a disco.»
- **«¿Por qué CloudWatch Logs?»** «Para el gate, un filtro de métrica alcanza. Para análisis, otra regla manda lo mismo a S3.»
- **«¿Sirve con otra nube?»** «El patrón de la lámina 13 no depende de ninguna. En Azure serían IoT Edge con sus módulos y despliegues por etiquetas.»
- **«¿Cómo firmas el modelo?»** «Greengrass verifica la huella de cada archivo. Para firma y procedencia, OpenSSF Model Signing, sobre Sigstore.»
- **«¿Cuánto cuesta?»** «Lo que más pesa es la EC2. Y todo se baja con un destroy desde GitHub Actions.» (A4)
- **«¿Cuántas bombas aguanta la PoC?»** «Unos 220 MB por bomba; limita la memoria, porque cada agente es una JVM.»
- **«¿Seguro que el audio no sale?»** «El componente lee el audio en modo solo lectura, y solo puede publicar en un tema.»

---

## 8 · Antes de subir

- [ ] Los dos botones de audio probados con el sonido de la sala.
- [ ] El deck en pantalla completa (F); las notas (N) en tu pantalla, no en la proyectada.
- [ ] Un reloj visible y agua.
- [ ] La escalera una vez, en voz baja.
