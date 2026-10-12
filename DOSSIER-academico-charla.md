# Dossier académico — "MLOps a ciegas"

Base de literatura para sostener la charla ante una audiencia técnica. Incluye **un hallazgo que rompe el diseño original** y su corrección.

---

# ⚠️ Lo primero: tu trigger de reversa está mal

## El problema

El diseño original dispara la reversa cuando la **confianza mediana baja**:

```sql
WHERE median(confidence) < umbral   -- ❌ esto no funciona
```

La literatura de calibración dice lo contrario de lo que asumimos:

> Los modelos son ligeramente **sobreconfiados** dentro de distribución, y **se vuelven MÁS sobreconfiados a medida que los datos se alejan** de la distribución de entrenamiento.

Traducción: **bajo drift, la confianza sube, no baja.** El modelo se equivoca con más seguridad, no con menos. Tu trigger fallaría exactamente cuando más lo necesitás.

Esto no es un detalle: es el problema central de la calibración de redes neuronales, documentado desde *On Calibration of Modern Neural Networks* (Guo et al., 2017) y confirmado en trabajo reciente sobre shift.

**Si alguien en la sala conoce esta literatura y vos presentás el trigger de confianza sin matiz, te desarma la charla completa.**

## La corrección: desacuerdo, no confianza

La señal correcta no depende de calibración. Tres opciones, en orden de qué tan bien encajan con tu arquitectura:

### 1. Desacuerdo campeón–retador (la que ya tenés)

Ya tenés despliegue en sombra: campeón y retador corren en paralelo sobre el mismo input. Entonces la señal es **cuánto difieren**, no cuán seguros están.

```sql
-- Tasa de desacuerdo entre versiones sobre el mismo input
SELECT  correlation_id,
        count(DISTINCT label) > 1  AS disagree
FROM    events
WHERE   occurred_at > now() - INTERVAL 60 SECOND
GROUP BY correlation_id;
```

**Por qué es la mejor para vos:** no requiere etiquetas, no depende de calibración, y **ya está en tu arquitectura** — la sombra existía para validar, ahora también es el detector.

### 2. Deriva en el espacio de representaciones

**DriftLens** (Greco et al., arXiv 2406.17813) detecta drift comparando la distribución de los *embeddings* internos, sin etiquetas y en tiempo real. Es el estado del arte no supervisado y es citable.

Implica publicar un resumen del embedding en el evento — un vector reducido o un hash de bucket, no el dato crudo. Encaja con tu restricción de privacidad.

### 3. Distribución de la confianza, no su nivel

Si igual querés usar confianza: no mires la mediana, mirá **la forma de la distribución**. Un test estadístico (Kolmogorov-Smirnov, o control estadístico de procesos) sobre el histograma de confianza detecta el cambio aunque el nivel medio suba.

Referencia: *Flexible and Efficient Drift Detection without Labels* (arXiv 2506.08734) usa control estadístico clásico en entorno sin etiquetas.

## Cómo convertir esto en el mejor momento de la charla

No lo escondas. **Es tu mejor slide.**

> "Mi primer diseño disparaba la reversa cuando bajaba la confianza. Parece obvio.
>
> Y está mal.
>
> La literatura de calibración dice que bajo drift los modelos se vuelven **más** sobreconfiados, no menos. O sea: mi trigger se apagaba justo cuando más lo necesitaba.
>
> La señal correcta no es cuán seguro está el modelo. Es **cuánto difiere de la versión anterior.**"

Una sala técnica premia esto más que cualquier acierto. Mostrás que probaste, que fallaste, y que leíste.

---

# Base académica por bloque de la charla

## Bloque 1–3 · La degradación silenciosa

**La cita que ancla toda tu tesis** (arXiv 2508.00042):

> "Los modelos desplegados en entornos no estacionarios **se degradan silenciosamente**, ya que a medida que la distribución de entrada deriva, su exactitud decae **sin señal de error y sin etiquetas que lo revelen**."

Eso es tu apertura, dicha por un paper. Úsala textual en el slide 3 o citala en voz alta.

**Papers de respaldo:**
- *Label-Free Concept Drift Assessment for Reliable AI* (arXiv 2508.00042) — propone CFPT y TabAutoDrift, detectores sin etiquetas
- *Time to Retrain? Detecting Concept Drifts in ML Systems* (arXiv 2410.09190) — cuándo reentrenar
- *Unsupervised Concept Drift Detection from Deep Learning Representations in Real-time* (arXiv 2406.17813) — DriftLens

## Bloque 4–5 · La asimetría servicio vs. modelo

Acá el argumento es de ingeniería, no de paper. Pero podés apoyarlo:

- Un servicio falla con señales **explícitas**: código de estado, excepción, timeout
- Un modelo falla con salida **sintácticamente válida**: el contrato de la API se cumple, el valor está en rango, la latencia es normal

La literatura de drift existe precisamente porque **no hay señal de error nativa**. Ese es el punto: si hubiera, no habría un campo de investigación entero dedicado a detectarlo.

## Bloque 8–9 · Desplegar y cuantización

**Para tu demo, esto es clave:**

- PTQ (cuantización post-entrenamiento) **degrada fuertemente por debajo de 4 bits** porque no hay reentrenamiento que restaure exactitud
- INT8 muestra **alta variabilidad según arquitectura** — es especialmente inefectiva en EfficientNet, MobileNetV3 y ViT
- INT4 con QAT llega a 42.2% mAP en el estudio citado: compresión mayor, exactitud menor, runtime apenas mejor
- QAT (cuantización durante entrenamiento) es la ruta preferida para bitwidths agresivos

**Lo que esto significa para tu PoC:** si querés degradación visible, usá **PTQ a 4 bits o menos** sobre una arquitectura sensible. No uses QAT — está diseñada justamente para que no se degrade.

Y te da la línea honesta de la charla:

> "No rompí el modelo. Le apliqué cuantización post-entrenamiento a 4 bits para que entrara en la Raspberry. Es lo que cualquiera haría. Pasó todos los tests offline."

**Referencias:** *EasyQuant* (arXiv 2006.16669), *EdgeQAT* (arXiv 2402.10787), *Efficient Post-Training Quantization with FP8 Formats* (MLSys 2024).

## Bloque 10–11 · El contrato de eventos

Acá no hay paper que reclame tu idea — y ese es el punto. Lo que sí tenés:

- **Sparkplug B** (Eclipse Foundation) estandarizó el payload de telemetría industrial
- **HiveMQ** documentó públicamente que la falta de estandarización de datos de modelos de IA en MQTT vuelve los despliegues de Edge AI complejos y no reutilizables
- Existe trabajo académico sobre plataformas MLOps para dispositivos far-edge con red limitada (*A Platform for MLOps for Network Constrained Far-Edge Devices*, MDPI 2025)

**Posicionamiento honesto:** el problema está reconocido, la solución de contrato no está estandarizada.

## Bloque 12 · Revertir

- *How to Implement Model Rollback* — los modelos de ML pueden fallar silenciosamente: pueden servir predicciones con **alta confianza siendo completamente incorrectas**, y la capacidad de rollback permite responder en segundos en vez de horas
- **Red Hat FlightCtl** (julio 2026) — despliegue de modelos de nube a dispositivos edge con GPU. Menciona los mismos desafíos: OS inmutables, drivers de GPU, actualizar modelos sin downtime, y cerrar el lazo de métricas hacia reentrenamiento

**Este último es prior art directo. Mencionalo vos** — mostrar que conocés el trabajo de Red Hat en el espacio te da credibilidad, y tu aporte (el contrato de eventos) es complementario, no competidor.

## Bloque 14 · Lo que nadie mide

- **MLPerf Inference: Edge** (MLCommons) define cuatro escenarios de prueba con un generador de carga estándar que mide una métrica específica por escenario
- Referencia de hardware útil: la **Raspberry Pi 5 (CPU)** mantiene modelos bajo 100 ms para un ciclo confiable de 10 Hz; la **Jetson Nano Super** sostiene ≥50 Hz usando CUDA

**Tu argumento:** MLPerf mide la inferencia. Nadie mide la **operación**: tiempo de reversa, convergencia de flota, peso del evento.

---

# Observabilidad de modelos en el edge — el estado de la literatura

Esta es la sección que le da peso académico a tu tesis central. **Hay campo formado, y hay un hueco claro.**

## El campo existe y está maduro (para la nube)

**Monitoring Machine Learning Systems: A Multivocal Literature Review** (arXiv 2509.14294) analiza **136 estudios** cruzando literatura formal y gris. Es la referencia canónica que podés citar para decir "esto es un campo, no una intuición mía".

Sus ejes: motivaciones y contexto, aspectos monitoreados con técnicas y métricas, contribuciones, y limitaciones actuales.

**Un dato citable y contundente:** de los 136 estudios, el monitoreo **técnico** (drift, performance) está mucho más maduro que el de ML responsable — solo **3,5%** de los enfoques son agnósticos de modelo para equidad.

Complementarios:
- *Monitoring and Observability of Machine Learning Systems* (arXiv 2510.24142)
- *From Tea Leaves to System Maps: A Survey and Framework on Context-aware ML Monitoring* (arXiv 2506.10770) — el título mismo es tu argumento: pasar de leer las hojas de té a un mapa del sistema

## El marco de cinco capas — usalo para posicionar tu contrato

**AI Observability for Large Language Model Systems** (arXiv 2604.26152) propone una **taxonomía de cinco capas**, desde los internos del modelo hasta la telemetría de infraestructura, con análisis comparativo de cinco trabajos de referencia de 2025–2026.

Aunque es sobre LLMs, la taxonomía aplica. **Tu contrato de eventos vive en la capa intermedia** — no es telemetría de infraestructura (CPU, memoria) ni son internos del modelo (activaciones, gradientes). Es la capa de *declaración de la inferencia*: qué predijo, con qué versión, con qué certeza, en cuánto tiempo.

Decirlo así en la charla te ubica en un marco que la audiencia puede verificar:

> "Existe una taxonomía de cinco capas para observabilidad de IA. La telemetría de infraestructura está resuelta — Prometheus, OpenTelemetry. Los internos del modelo son un campo de investigación. Yo estoy hablando de la capa del medio, que es la que nadie estandarizó."

## El edge tiene su propia literatura y su propia restricción

**Monitoring and Observability in Edge Computing Systems: Taxonomy, Comparative Analysis, and Research Directions** (ScienceDirect, 2026) — taxonomía específica de edge, con direcciones de investigación abiertas.

Y acá está la restricción que la literatura reconoce y que sostiene tu diseño: **el monitoreo en el edge tiene que ser de bajo overhead.** El trabajo reciente se enfoca en mecanismos de bajo costo para entornos con recursos limitados: observabilidad a nivel de kernel con **eBPF**, profiling de rendimiento en tiempo real, agregación de telemetría y monitoreo a nivel de contenedor — todos enfatizando escalabilidad y overhead mínimo.

**Por qué esto te da la razón:** no podés meter un stack completo de observabilidad en una Raspberry Pi. El *AI-Driven Lightweight Observability Framework for Edge Computing in IoT* existe precisamente porque hace falta monitorear "sin comprometer la función primaria del dispositivo".

Tu contrato de eventos **es** la respuesta liviana: un evento estructurado por inferencia, de bytes, en vez de un agente que exporta métricas, trazas y logs.

## Surveys de contexto para la introducción

- *Empowering Edge Intelligence: A Comprehensive Survey on On-Device AI Models* (arXiv 2503.06027)
- *Training Machine Learning Models at the Edge: A Survey* (arXiv 2403.02619) — nota útil: las técnicas de compresión (destilación, cuantización, poda) **pasaron de acelerar el despliegue a reducir complejidad en la fase de entrenamiento**. Eso refuerza que la cuantización ya no es un detalle de deployment sino una decisión de diseño con consecuencias.

## El hueco, dicho con precisión

Con esta literatura podés hacer una afirmación fuerte y defendible:

> "Hay 136 estudios sobre monitoreo de sistemas de ML. Hay taxonomías de observabilidad de IA de cinco capas. Hay literatura específica de observabilidad en edge computing.
>
> Lo que no hay es **un formato común para lo que un modelo declara sobre sí mismo.** Cada framework de monitoreo define su propio esquema, así que la observabilidad no se transfiere entre proyectos — igual que el resto del stack."

**Ese es el hueco, y ahora está anclado en literatura en vez de en una opinión.**

## Cómo usarlo en la charla

Agregá una línea al slide 10 (el del evento de inferencia):

> *"Taxonomía de 5 capas para observabilidad de IA — esta es la del medio."*

Y en el slide 15 (lo que no inventé), agregá una fila:

| Monitoreo de ML | 136 estudios · surveys 2025-26 | ✓ |

Mostrar que conocés el estado del arte y que igual identificás un hueco específico es mucho más fuerte que ignorarlo.

---

# Cinco datos para citar de memoria

| Dato | Fuente |
|---|---|
| "Se degradan silenciosamente, sin señal de error y sin etiquetas que lo revelen" | arXiv 2508.00042 |
| Bajo shift los modelos se vuelven **más** sobreconfiados | Literatura de calibración (Guo et al. 2017 + trabajo reciente) |
| PTQ degrada fuertemente bajo 4 bits; QAT es la ruta para bitwidths agresivos | EdgeQAT, EasyQuant |
| Pi 5 CPU: <100 ms para 10 Hz. Jetson Nano Super: ≥50 Hz con CUDA | Estudios comparativos de latencia edge |
| MLPerf Edge mide inferencia, no operación | MLCommons |
| 136 estudios sobre monitoreo de ML; solo 3,5% agnósticos de modelo para equidad | arXiv 2509.14294 |
| Taxonomía de 5 capas para observabilidad de IA | arXiv 2604.26152 |

---

# Cambios concretos que hay que hacer

## En los slides

1. **Slide 11 (la consulta SQL):** cambiar de `median(confidence)` a la consulta de desacuerdo. La consulta de confianza pasa a ser el ejemplo de *lo que no funciona*.
2. **Slide nuevo entre 11 y 12: "La confianza es una trampa"** — el hallazgo de miscalibración. Es el mejor slide de la charla.
3. **Slide 13 (PoC):** especificar **PTQ a 4 bits**, no "cuantización agresiva" a secas.
4. **Slide 15 (lo que no inventé):** agregar Red Hat FlightCtl y DriftLens a la columna de resuelto/existente.

## En la demo

- El controlador debe disparar por **desacuerdo campeón–retador**, no por nivel de confianza
- Publicar `correlation_id` en el evento para poder aparear las dos versiones sobre el mismo input
- Degradar con **PTQ 4-bit sobre una arquitectura sensible** (MobileNet o EfficientNet, según la literatura)

---

# Fuentes

- [Label-Free Concept Drift Assessment (2508.00042)](https://arxiv.org/abs/2508.00042)
- [DriftLens — Unsupervised Concept Drift Detection (2406.17813)](https://arxiv.org/abs/2406.17813)
- [Flexible and Efficient Drift Detection without Labels (2506.08734)](https://arxiv.org/abs/2506.08734)
- [Time to Retrain? (2410.09190)](https://arxiv.org/html/2410.09190)
- [On Calibration of Modern Neural Networks (1706.04599)](https://ar5iv.labs.arxiv.org/html/1706.04599)
- [Revisiting the Calibration of Modern Neural Networks (2106.07998)](https://arxiv.org/pdf/2106.07998)
- [Gradient Rectification for Robust Calibration under Distribution Shift (2508.19830)](https://arxiv.org/html/2508.19830)
- [EdgeQAT (2402.10787)](https://arxiv.org/html/2402.10787v1)
- [EasyQuant (2006.16669)](https://arxiv.org/pdf/2006.16669)
- [Efficient Post-Training Quantization with FP8 Formats (MLSys 2024)](https://proceedings.mlsys.org/paper_files/paper/2024/file/dea9b4b6f55ae611c54065d6fc750755-Paper-Conference.pdf)
- [MLOps para far-edge con red limitada (MDPI)](https://www.mdpi.com/2571-5577/8/5/141)
- [Red Hat — MLOps at the edge con FlightCtl](https://next.redhat.com/2026/07/08/mlops-at-the-edge-deploying-ai-models-from-cloud-to-gpu-powered-edge-devices/)
- [MLPerf Inference: Edge](https://mlcommons.org/benchmarks/inference-edge/)
- [How to Implement Model Rollback](https://oneuptime.com/blog/post/2026-01-30-mlops-model-rollback/view)

**Observabilidad de ML y edge:**

- [Monitoring ML Systems: A Multivocal Literature Review — 136 estudios (2509.14294)](https://arxiv.org/abs/2509.14294)
- [Monitoring and Observability of ML Systems (2510.24142)](https://arxiv.org/pdf/2510.24142)
- [AI Observability for LLM Systems — taxonomía de 5 capas (2604.26152)](https://arxiv.org/html/2604.26152v1)
- [From Tea Leaves to System Maps — Context-aware ML Monitoring (2506.10770)](https://arxiv.org/pdf/2506.10770)
- [Monitoring and Observability in Edge Computing Systems: Taxonomy and Research Directions](https://www.sciencedirect.com/org/science/article/pii/S1546221826005473)
- [AI-Driven Lightweight Observability Framework for Edge Computing in IoT](https://www.researchgate.net/publication/389126723_AI-Driven_Lightweight_Observability_Framework_for_Edge_Computing_in_IoT)
- [Empowering Edge Intelligence: Survey on On-Device AI Models (2503.06027)](https://arxiv.org/html/2503.06027v1)
- [Training ML Models at the Edge: A Survey (2403.02619)](https://arxiv.org/html/2403.02619v3)
