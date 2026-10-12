# CFP DevOpsDays Bogotá — para pegar

**30 min · Español · Grabación activada**
*Alineado con `mlops-a-ciegas.html` (v11, 19 páginas).*

---

## Título

```
MLOps a ciegas: gobernar modelos de IA que se ejecutan donde no llega el plano de control
```

Si el campo es corto: `MLOps a ciegas` y el resto va al abstract.

---

## Abstract

```
Esta mañana desbloqueaste el teléfono con la cara. ¿Cuántos modelos de IA creés que intervinieron en ese gesto?

Cuatro. Como mínimo cuatro, encadenados. Y ninguno corrió en la nube.

Las computadoras con acelerador de IA pasaron del 15% del mercado en 2024 al 31% en 2025, y este año cierran arriba del 54%. Es la primera vez que cruzan la mitad. La inferencia dejó de ser un servicio al que se llama: ahora se ejecuta en el bolsillo de otro.

Y ahí empieza el problema. Diez mil equipos, ninguno tuyo, con silicio distinto, sin red la mitad del tiempo, y sin un plano de control común. Nada de lo que sabemos sobre desplegar servicios aplica igual.

La charla recorre los seis pasos que van del modelo entrenado al modelo operando en la flota — entrenar, optimizar, preparar, desplegar, correr, monitorear — y se detiene en el último, que es el que la industria todavía no resolvió: monitorear el equipo no es monitorear el modelo.
```

---

## Description

```
## De dónde sale

Face ID no es un modelo. Es una cadena de cuatro, y corre entera en el equipo: detección y atención, mapa de profundidad con unos 30.000 puntos infrarrojos, comparación contra el modelo almacenado, y decisión. Todo local, en milisegundos, y sin que la cara salga del dispositivo.

Ese ejemplo abre la charla porque es el que todos usamos sin pensarlo, y porque muestra en un gesto lo que ya es la norma: los modelos se ejecutan en equipos que no administra el que los desplegó.

Los números acompañan. Según Gartner, las PC con acelerador de IA fueron el 15,6% del mercado en 2024, el 31% en 2025, y este año cierran en 54,7%. Este año cruzamos la mitad.

## El encuadre

Antes de hablar de operación hay una pregunta que hay que resolver: ¿conviene ejecutar el modelo en el dispositivo o en la nube? La comparamos en tres ejes — latencia, comportamiento sin red, y qué pasa con el dato. La conclusión no es que uno gana: nadie ejecuta todo de un solo lado. La pregunta real es dónde se traza la frontera.

## Las cuatro barreras

Una vez que el modelo va al dispositivo, aparecen cuatro problemas que no tiene desplegar un servicio:

- **Silicio heterogéneo.** El modelo se entrena en GPU y se ejecuta en NPU, CPU o DSP. Un artefacto no sirve para toda la flota.
- **Conectividad intermitente.** El equipo puede estar apagado o sin red durante días. No se le puede empujar nada.
- **Runtimes fragmentados.** TFLite, ONNX Runtime, el stack del fabricante. La portabilidad se decide en el primer paso, no en el último.
- **Sin plano de control común.** Cada proveedor trae el suyo, y una flota real rara vez es de un solo proveedor.

## Los seis pasos

El recorrido completo de un modelo, uno por uno, con el diagrama de cada paso:

**Entrenar.** Nada nuevo, salvo por una cosa: el formato de salida. Si el entrenamiento escupe un formato propietario, la portabilidad ya se perdió. Y sale con manifiesto: versión, sha256, runtime, formato, requisitos de hardware, firma.

**Optimizar para el chip.** Un ONNX de entrada, tres artefactos de salida, uno por clase de equipo. Acá el modelo se achica para entrar — y acá es donde se rompe en silencio. Cuantizar baja la precisión, y la exactitud se paga sin que nadie avise.

**Preparar.** El paso corto y aburrido que evita la mitad de los incidentes. Modelo, runtime y manifiesto se firman y salen como artefacto OCI inmutable. Si se puede reescribir lo ya desplegado, no hay despliegue: hay una carpeta compartida.

**Desplegar.** Acá se termina el parecido con desplegar un servicio. Entrega por tramos —1%, 5%, 25%, 100%— con compuerta en cada salto: caídas bajo 1%, latencia p99 bajo 40 ms, acuerdo con la versión anterior arriba de 98%. Y el destino no es "la flota", es una condición de hardware. Lo central: **el dispositivo tira, vos no empujás nada.** Porque puede estar apagado, y alguna vez lo va a estar.

**Correr.** El paso más corto, porque si llegaste bien hasta acá correr es casi gratis. Runtime aislado, estado deseado en disco, cola persistente, y reconciliación cuando vuelve la red.

**Monitorear.** El paso de la charla.

## Por qué el sexto

Los cinco primeros están resueltos. Hay buen producto para cada uno y en la charla se nombran, con nombre propio, para que quede claro qué no hay que reconstruir.

El sexto no. Y la trampa es que casi todo el mundo cree que ya lo tiene, porque tiene monitoreo del **dispositivo**: CPU, memoria, temperatura, si está vivo. Eso está muy bien y no dice absolutamente nada del modelo.

Cerramos con las cuatro métricas que hay que medir y que ningún tablero trae armadas: cobertura de versión, tiempo de convergencia, tasa de reversión, y deriva de la entrada — la única de las cuatro que habla del mundo y no de la flota.

Sin esas cuatro tenés despliegue. No tenés operación.

## Te llevás

El recorrido completo en un diagrama, el manifiesto campo por campo, el patrón de entrega por tramos con compuertas, las cuatro métricas, y el repositorio.
```

---

## Notes (privado para el comité)

```
Hola, gracias por leer.

Soy Cloud Engineer y trabajo con inferencia en el borde e IoT industrial sobre AWS, Azure y GCP. Tengo 5 certificaciones AWS (SA Pro, Advanced Networking, CloudOps Pro, Security, SA Associate) y las tres de Kubernetes.

Por qué propongo esta charla y no otra de IA: miré el programa del año pasado y conté trece charlas de IA. Las trece de LLMs, agentes o GenAI. Ninguna de desplegar y sostener modelos entrenados en producción. Ahí veo el hueco, y es donde más se está rompiendo la práctica: la inferencia en el borde creció mucho más rápido que las herramientas para operarla.

Sobre la apertura: la charla no asume que la audiencia sepa qué es edge AI. Arranca preguntando cuántos modelos intervienen en desbloquear el teléfono con la cara —la respuesta es cuatro, encadenados, y ninguno en la nube— y de ahí construye. Me pareció importante porque el tema no es común en eventos de DevOps y no quiero perder a nadie en los primeros minutos.

Nivel avanzado, pero no pide experiencia previa en ML. Asume que ya desplegaste cosas a producción y conocés CI/CD y observabilidad. Lo de ML lo introduzco desde el lado del que tiene que operarlo.

Sobre el formato: la presentación es una página por idea, con un diagrama por paso, y una espina de seis pasos que marca dónde estamos. Para 30 minutos calculo 25 de contenido y 5 de preguntas.

Dos cosas que quiero mantener. Una: nombro con nombre propio los productos que ya resuelven cinco de los seis pasos, porque no vengo a vender nada y quiero que quede claro qué no hay que reconstruir. Dos: hay un paso donde muestro cómo el modelo se degrada en silencio al cuantizarlo, que es un error que cometí y no una hipótesis.

Quedo atento a lo que necesiten.
```

---

## Imagen (opcional)

La página 6 — el gráfico de barras donde el mercado de PC con acelerador de IA cruza el 50%. Es la única del deck que cuenta el porqué de la charla sin texto.

---

## Pendientes en la presentación

| Página | Falta |
|---|---|
| 10 | Diagrama del recorrido completo — hueco de 1880 × 812 |
| 16 | Diagrama de monitoreo — hueco de 980 × 544 |
| 19 | QR de LinkedIn (400 × 400) y confirmar la URL del repo |
| 18 | Atribución de las cuatro cifras — decirla en voz alta sin que la pidan |

---

## Los 30 minutos

| Min | Páginas | Qué |
|---|---|---|
| 0–5 | 01–04 | Face ID, los cuatro modelos, quién habla |
| 5–9 | 05–06 | Dónde corre la IA hoy y la curva que cruza la mitad |
| 9–13 | 07–08 | Dispositivo o nube · las cuatro barreras |
| 13–16 | 09–10 | El stack y el recorrido completo |
| 16–24 | 11–15 | Los cinco primeros pasos, rápido |
| 24–28 | 16–17 | Monitorear y las cuatro métricas |
| 28–30 | 18–19 | Cierre y gracias |
| 30+ | 19 | Preguntas, con la página en pantalla |

Los pasos 11 a 15 son los que más se pueden apurar si vas atrasado: cada uno tiene su diagrama y la sala lo lee sola.
Lo que no se toca es la 16 y la 17 — es el argumento de la charla.
