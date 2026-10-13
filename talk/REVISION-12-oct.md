# Revisión del deck y el guion · 12 de octubre

> **Nota (12 de octubre, noche):** registro histórico. Las correcciones de §1, el recorte de §4 y los títulos (en versión formal, no los de §2) ya se aplicaron en `GUION-devopsdays.md` y en el deck. El código y AWS ahora usan nombres en inglés (`pump-03`, `fault.sh`, `StationRing0`); aquí quedan los nombres de entonces.

Revisé las 42 láminas renderizadas (cada una en su último paso), el guion completo y el CFP. Primero lo que está mal o es riesgoso; después, los títulos y el tono.

---

## 1 · Lo que hay que corregir

| # | Dónde | Qué pasa | Qué hacer |
|---|---|---|---|
| 1 | Todo | **El CFP promete 25 min de contenido + 5 de preguntas.** El guion dura 32:45, o 29:55 en la versión corta. Te quedas sin preguntas, o te cortan en la demo | Recortar a unos 26 min (propuesta en §4) y cronometrar en el primer ensayo |
| 2 | Lám. 25 | La tabla dice `COMPLETED` por thing group. En la API, un despliegue a un **thing group** suele quedar `ACTIVE`; `COMPLETED` es de los despliegues a un solo equipo (así sale en el ejemplo oficial de `list-deployments`) | En el ensayo, corre `aws greengrassv2 list-deployments` y copia exactamente lo que salga. O muestra el estado por bomba (`list-effective-deployments` → `SUCCEEDED`) |
| 3 | Lám. 30 | El título pregunta «¿Cuánto **cuesta**…?», pero la lámina muestra volumen (TB y mensajes), no dinero | Cambiar el título (ver §2) |
| 4 | Anexo A4 | Dice que las bombas usan `GreengrassV2IoTThingPolicy`, «la que crea el instalador». La PoC ya usa `EstacionThingPolicy`, la mínima, tanto en `setup.sh` como en Terraform. «Lo que cobra» no menciona IoT Core ni los core devices de Greengrass, y el guion sí | Fila: `EstacionThingPolicy` · conectar como `bomba-*` y publicar solo en `estacion/eventos`. Agregar IoT Core y Greengrass a «Lo que cobra» |
| 5 | Lám. 27 | En el diagrama dice «**Tu** laptop», pero la lámina es «¿Qué monté…?» (primera persona) | «Mi portátil» |
| 6 | Lám. 20 | «La receta del componente, **tal cual**», pero está recortada (`<umbral>`, `…`) | «La receta de la demo (recortada)» |
| 7 | Lám. 11 | «¿Si el panel está en verde, el modelo está bien?»: los signos de interrogación van solo en la pregunta | «Si el panel está en verde, ¿el modelo está bien?» (o el título nuevo de §2) |
| 8 | Lám. 11, guion | «No son opiniones, son datos» es *la* frase de Freddy Vega, y tu propio guion dice «no copies frases suyas» | «Y esto no me lo inventé: lo medí en la PoC, con el audio de las bombas que van a oír» |
| 9 | Lám. 3 y guion | «PC nuevas», «computadoras»: en Colombia es «el PC», «los computadores». «Laptop» suena menos colombiano que «portátil» | «De cada 100 computadores nuevos…», «mi portátil» |
| 10 | Guion público | Si el repo es público, la sección «Lo que tomé de las charlas de Freddy Vega» queda a la vista de la sala | Moverla a un archivo privado |
| 11 | Lám. 15 y 16 | En el último paso, lo atenuado queda gris muy claro sobre blanco. Un proyector lo borra | Atenuar con un gris más oscuro (o con opacidad mínima de ~0,55) |

**Para confirmar tú** (no lo pude verificar):
- Lám. 6: «AWS, Azure y GCP», «5 certificaciones de AWS» y «3 de Kubernetes»: que estén vigentes.
- A7: el número del Reglamento (UE) **2026/1744** (Digital Omnibus) y las fechas dic. 2027 / ago. 2028. Búscalo en EUR-Lex antes de subir.
- Lám. 3: Gartner proyectaba 54,7 % para 2026. Si ya salió una cifra nueva del año, dila como «Gartner proyectaba…».

**Verificado y bien:**
- Las cuentas de la lámina 30: 115 MB/h, 2,76 TB, 8,64 M y 1,44 M.
- La tabla de tiempos del guion: cada bloque suma lo que dice.
- Nucleus lite: 15 MB de RAM y 5 MB de almacenamiento, según la documentación.
- La receta de la lámina 20 contra `component/recipe.template.yaml`.

**Pendiente por datos, no es un error:** «audio pendiente» (2, 32) y «por medir» (11, 19) se llenan solos cuando llegue el zip. Siguen los placeholders de foto, LinkedIn y repo/QR (6, 33, 34).

---

## 2 · Títulos: menos fórmula, más tú

El patrón que delata el piloto automático: **27 títulos seguidos con la misma forma**, «¿Pregunta + *remate en color*?». Uno o dos funcionan; veintisiete se vuelven plantilla. La regla que propongo:

- **Pregunta** solo cuando de verdad se la haces a la sala (2, 12, 22, 25, 32).
- **Los pasos 1 a 6**, con el verbo de la espina y una frase corta: así la gente sabe dónde va.
- **El resto**, una afirmación o una frase hablada, como la dirías en un pasillo.

| # | Hoy | Propuesta |
|---|---|---|
| 2 | ¿Esta bomba está fallando? | *(igual: es la pregunta a la sala)* |
| 3 | ¿Cuántas PC nuevas traen chip para IA? | La IA ya viene de fábrica |
| 4 | ¿Cuánto dinero se está invirtiendo en edge? | El edge no es un nicho |
| 5 | ¿Por qué la IA se está saliendo de la nube? | Por qué no todo va a la nube (explicado con memes) |
| 6 | ¿Quién soy? | Mucho gusto |
| 7 | ¿Qué van a aprender hoy? | Por dónde vamos a ir |
| 9 | ¿Qué tenemos cuando el modelo corre en la nube? | En la nube, esto ya está resuelto |
| 10 | ¿Y cuando baja a la estación? | Ahora bájalo a la vereda |
| 11 | ¿Si el panel está en verde, el modelo está bien? | «Todo verde, jefe» |
| 14 | ¿Qué lleva el equipo de la estación por dentro? | Abramos el equipo |
| 15 | ¿Qué hace falta para gobernarlo? | Cinco piezas, ninguna mágica |
| 16 | ¿Cómo se ve esto en AWS? | El mismo dibujo, con nombres de AWS |
| 18 | Paso 1 · ¿Qué sale de la nube? | Paso 1 · Entrenar solo con bombas sanas |
| 19 | Paso 2 · ¿Qué cabe en el chip? | Paso 2 · Optimizar: si no cabe, no corre |
| 20 | Paso 3 · ¿Qué es un componente? | Paso 3 · Empaquetar: la receta de la demo |
| 21 | Paso 4 · ¿Cómo llega a mil equipos? | Paso 4 · Desplegar: primero una estación |
| 23 | Paso 5 · ¿Qué sigue funcionando sin red? | Paso 5 · Sin red, la estación sigue oyendo |
| 24 | Paso 6 · ¿Qué ves desde la nube? | Paso 6 · Monitorear lo que el modelo cuenta |
| 27 | ¿Qué monté para la demo? | Lo que monté (y lo que es de mentiras) |
| 28 | ¿Cuáles son las señales doradas de un modelo? | Las señales doradas, versión modelo |
| 29 | ¿Cómo se ve un modelo decidiendo? | La estación, en vivo |
| 30 | ¿Cuánto cuesta observar mil bombas? | ¿Y si mandamos el audio a la nube? |
| 31 | ¿Qué me llevo hoy? | Cinco cosas para el lunes |
| 33 | ¿Dónde sigo después de la charla? | Todo está en el repo |
| A6 | ¿Qué método de drift uso? | Drift: cuál uso y cuándo |

Los divisores («El problema», «El patrón», «Los seis pasos», «En vivo») están bien así.

**El texto de abajo de las preguntas a mano alzada:** «Sin pena: aquí todos somos familia» sale dos veces y suena a frase hecha. Por ejemplo:
- Lám. 12: «Levanten la mano. Tranquilos, que la grabación no saca caras… creo.» (el CFP dice «grabación activada»)
- Lám. 22: «Nadie juzga. Bueno, un poquito.»

---

## 3 · El guion: dónde suena a IA y cómo arreglarlo

1. **«El error típico:» sale seis veces** (láminas 18, 19, 20, 21, 23 y 24). Es una muletilla de plantilla. Deja dos. En las otras, o cuentas algo que te pasó («La primera vez que monté esto, cambié un archivo en S3 sin cambiar la versión y…»), o lo quitas.
2. **«Muchos dirán:» tres veces** (5, 21, 24). Varía: «Seguro alguien está pensando…», «Ya sé lo que me van a decir…», o pregúntale directo a alguien de la sala.
3. **Tríadas en staccato:** «Cero errores. Cero excepciones.», «Sin errores. Misma latencia.», «Mismo modelo, mismo umbral, cero errores.» Funcionan una vez. Deja la de la lámina 11 y la del acto 3; las demás, dilas en una frase normal.
4. **El remate dicho tres veces.** «Greengrass revierte despliegues fallidos, no modelos equivocados» aparece en la demo y en A3, y casi igual en la lámina 21. Guárdalo para la demo, que es donde pega. En la 21 basta con la frase que ya tienes: «Para Greengrass, un modelo que no oye es un despliegue exitoso».
5. **Falta tu voz.** Lo que más delata un guion generado no es la gramática: es que nadie cuenta nada propio. Hoy hay dos huecos (dato personal en la 6, anécdota en la 31). Agrega dos o tres momentos reales:
   - Por qué te importa el edge (una frase, en la 6).
   - Algo que te salió mal en el primer ensayo. Lo vas a tener en unos días, y es oro: «Cuando ensayé esto el jueves, la alarma no disparó porque…».
   - La anécdota de la 31, aunque sea de otro contexto.
6. **Deja frases incompletas y reacciones.** Un guion humano tiene «bueno», «a ver», «miren esto». No lo escribas todo: deja en algunas láminas solo la idea, y dila con tus palabras en el ensayo.
7. **Lo que ya suena bien y no tocaría:** «Oído de mecánico», el chiste del jefe, «yo lo he hecho» con los dedos cruzados, la vereda que se queda sin agua al final.

---

## 4 · Cómo llegar a ~26 minutos

Partiendo de la versión de 29:55 (que ya quita las láminas 4, 28 y 30, un meme y usa el atajo de la demo):

| Recorte | Ahorra |
|---|---|
| Lám. 5: solo el meme de la vereda sin red (el que conecta con la bomba) | 0:25 |
| Lám. 9: una frase y pasar («en la nube, todo pasa por el endpoint») | 0:20 |
| Lám. 15: mostrar las cinco piezas en dos clics, no seis | 0:30 |
| Lám. 16: sin clics, el mapa de una vez («cada casilla tiene nombre; los pasos que vienen las abren») | 0:40 |
| Lám. 19: solo la medición de la bomba; la lista de herramientas, a preguntas | 0:20 |
| Lám. 22 (mano alzada 2): fuera; con dos preguntas a la sala alcanza | 0:25 |
| Lám. 23: Outposts/EKS a un anexo; quedarse con el equipo pequeño | 0:20 |
| Demo, acto 2: quitar `dominio.sh` (el drift ya se contó en la lámina 11) | 0:40 |
| Lám. 7: la agenda se dice en una frase | 0:15 |
| **Total** | **≈ 3:55 → unos 26:00** |

Antes de cortar, cronométralo. Las cifras del guion son estimadas; el acto 3 depende de cuánto tarden la métrica y la alarma.
