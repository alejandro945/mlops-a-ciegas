# CFP — DevOpsDays Bogotá 2026 (23 de octubre)

**Ángulo elegido:** MLOps sin nube — desplegar, observar y revertir modelos en el borde.

---

# 1. Título

## Recomendado

> ## MLOps a ciegas
> ### Desplegar, observar y revertir modelos en el borde

**Por qué "a ciegas":** captura las dos restricciones reales de una sola palabra. No podés ver los datos que entran al modelo — no salen del sitio. Y no podés ver ni tocar el dispositivo donde corre. Es corto, es visual, y es literalmente cierto. El subtítulo aterriza el contenido para el comité.

## Alternativas fuertes

**Si querés que pegue con la tribu DevOps:**

> ### Sin kubectl
> #### MLOps donde no hay cluster, ni SSH, ni ventana de mantenimiento

*La ausencia de su herramienta la sienten en el estómago. Muy efectivo con este público.*

**Si querés la más visceral:**

> ### Diez mil dispositivos, un modelo malo y cero SSH
> #### Desplegar, observar y revertir modelos en el borde

*La mejor para el programa impreso: nadie la saltea. Un poco más riesgosa porque no dice "MLOps" hasta el subtítulo.*

**Si querés atacar por observabilidad:**

> ### Tu modelo se degradó hace tres semanas
> #### Y no tenés forma de saberlo

*Muy buena si terminás enfocando la charla en observabilidad. Como la charla cubre las tres cosas, deja fuera dos tercios del contenido.*

**Si querés la más sobria:**

> ### El modelo no corre en tu cluster
> #### MLOps en el borde: desplegar, observar y revertir

*La más segura. Menos memorable, cero riesgo.*

### Mi orden

1. **MLOps a ciegas** — mejor balance entre impacto y claridad
2. **Sin kubectl** — más pegada con la tribu, apenas menos clara
3. **Diez mil dispositivos...** — más memorable, un poco más arriesgada

---

# 2. Descripción de la charla

> Casi todo lo que llamamos MLOps asume tres cosas: que el modelo corre en tu infraestructura, que podés ver los datos que entran, y que si algo sale mal hacés rollback y listo.
>
> En el borde no se cumple ninguna de las tres. El modelo corre en un dispositivo que no controlás, los datos no pueden salir del sitio por costo o por regulación, y no existe `kubectl rollout undo` para diez mil equipos con conectividad intermitente y sin ventana de mantenimiento.
>
> Esta charla recorre los tres momentos del ciclo de vida donde eso se rompe, con detalle técnico y con código.
>
> **Desplegar.** Entregar un modelo firmado a una flota heterogénea, con ONNX como frontera única y compilación por destino según el acelerador que haya en cada dispositivo. Por qué amarrar la arquitectura a un proveedor de silicio es una decisión que se paga en dieciocho meses, y cómo se verifica la integridad de un artefacto de modelo antes de cargarlo.
>
> **Observar.** El problema más difícil de los tres: cómo sabés que un modelo se degradó cuando no podés mirar sus entradas. Acá está la idea central de la charla — un esquema de eventos de inferencia versionado que lleva adentro modelo, versión, hash de pesos, confianza, geometría y latencia. En el mundo industrial ya existe un estándar para la telemetría de sensores, Sparkplug B de la Eclipse Foundation, pero no modela lo que produce un modelo de IA. Ese hueco está documentado públicamente y es exactamente donde se rompe la reutilización entre proyectos.
>
> **Revertir.** Validación previa contra el campeón, despliegue en sombra con tráfico real y riesgo cero, canario por segmento, y reversa automática disparada por métricas que salen del propio stream de eventos — no de un sistema de monitoreo aparte. Si cada evento trae versión y confianza, comparar dos modelos en producción es una consulta agregada.
>
> Incluye además dos verificaciones incómodas contra la narrativa de 2026: qué dicen los benchmarks industriales publicados este año sobre modelos visión-lenguaje razonando en entornos reales, y qué partes de este problema **ya están resueltas** por estándares y herramientas existentes y no vale la pena reconstruir.
>
> **Te llevás:** un esquema de eventos que podés adaptar a tu caso, un criterio para decidir dónde corre cada inferencia, un patrón de reversa que funciona sin acceso al dispositivo, y una lista honesta de lo que todavía no tiene solución.

*(Cuando tengas números medidos, insertalos en los párrafos de desplegar y revertir. Una cifra real vale más que todo el resto de la descripción.)*

---

# 3. Relación con AI y nivel técnico

> **Nivel: Avanzado.**
>
> La charla es sobre la operación de sistemas de IA en producción, no sobre su entrenamiento. Asume que quien escucha ya desplegó software a producción y conoce CI/CD y observabilidad, pero no asume experiencia previa en machine learning: los conceptos de ML necesarios se introducen desde la perspectiva de quien tiene que operarlos.
>
> El enfoque es deliberadamente el inverso al de la mayoría de las charlas de IA en eventos de DevOps. No es *usar IA para operar*; es **cómo se opera la IA** cuando el modelo no corre en tu cluster. Es un ángulo poco cubierto y es donde más se está rompiendo la práctica: la adopción de inferencia en el borde creció mucho más rápido que el tooling para sostenerla, y hoy cada equipo reinventa el despliegue, la observabilidad y la reversa desde cero.
>
> **Contenido técnico concreto:**
>
> - Diseño de esquemas de eventos versionados con compatibilidad hacia atrás verificada en CI
> - ONNX como formato de intercambio y compilación por acelerador (TensorRT, OpenVINO, Core ML, NNAPI)
> - Entrega firmada de artefactos de modelo y verificación de integridad en el dispositivo
> - Patrones de despliegue en sombra y canario aplicados a modelos en lugar de servicios
> - Métricas de degradación derivadas del propio stream de eventos
> - Reversa automática sin acceso al dispositivo, con conectividad intermitente
> - Limitaciones reales del aprendizaje federado en cuanto a privacidad: por qué compartir pesos no es automáticamente privado
>
> No es una charla de producto ni de proveedor. Nombra explícitamente qué partes del problema ya resolvieron los estándares abiertos y las herramientas existentes del mercado, y acota el aporte a lo que hoy no está cubierto.

---

# 4. Bio del speaker

*Completá los corchetes. Tres o cuatro líneas es lo estándar y lo que mejor se lee.*

> Alejandro Varela es [rol] en EPAM, donde trabaja en arquitecturas de inferencia en el borde e IoT industrial sobre AWS, Azure y GCP. Ha trabajado en [dominio o industria], y actualmente se enfoca en el problema de sostener modelos de ML en producción fuera de la nube: despliegue a flotas heterogéneas, observabilidad sin acceso a los datos, y reversa automática sin acceso al dispositivo. Le interesa la frontera entre DevOps y ML, donde las prácticas de uno todavía no terminan de aplicarse al otro.

Si tenés GitHub, blog o charlas previas, agregá una línea al final. Si no tenés ninguna, no lo menciones.

---

# 5. Foto

Profesional, fondo simple, buena luz, de los hombros para arriba. JPG o PNG bajo 10 MB. Si no tenés una decente, sacala esta semana con luz natural cerca de una ventana y fondo liso.

---

# Lo que hay que construir antes de octubre

El CFP evalúa explícitamente **"experiencia real y aplicaciones prácticas"**. Hoy tenés una propuesta bien investigada y **cero implementación** — y eso se nota en la primera pregunta del público.

Tenés tres meses. La charla se sostiene con **una sola** de estas, y están en orden de rentabilidad:

**1. Una reversa real, cronometrada.** Un modelo corriendo en un dispositivo (Jetson, Raspberry, un teléfono), una versión nueva que empeora una métrica, y la reversa automática disparándose sola. Con el tiempo medido.

*Esta sola cosa sostiene toda la charla*, porque es el título. Y te da la frase que hace que te seleccionen: *"reversa completa en N dispositivos en X minutos, acá está el código."*

**2. Números de latencia end-to-end** sobre un acelerador que no sea NVIDIA, con metodología abierta. Casi nadie publica esto.

**3. El esquema implementado** y un caso real de evolución de versión sin romper consumidores.

---

# Cómo hacer que la seleccionen

**Mostrá lo que se rompió.** Un DevOpsDays premia las cicatrices más que los éxitos. Si el reloj del dispositivo derivó, si el modelo compilado no cargó, si la reversa falló con conectividad intermitente — eso es lo mejor de la charla, no lo que hay que esconder.

**Ofrecé demo en vivo.** Aunque el formulario no lo pida, agregá al final de la descripción: *"Incluye demostración en vivo de una reversa de modelo en un dispositivo real."* Sube mucho las probabilidades. Si la hacés, grabá un respaldo — el wifi de conferencia falla siempre.

**Cero logos, cero nombres de cliente.** Ni EPAM en cada slide, ni el caso de Netflix. Los casos se cuentan genéricos. La comunidad detecta el pitch corporativo en dos minutos y se apaga.

**Aclará qué podés publicar.** Si el esquema y el código salen de trabajo interno, hablalo con tu manager antes de prometer código abierto en el CFP. Una charla con repo público es mucho más fuerte, pero conviene tener el permiso primero.

---

# El riesgo honesto

Si en octubre no construiste nada, **no la presentes como experiencia práctica.** Presentala como lo que sería: análisis del estado del arte más propuesta de diseño. Es una charla más chica y menos memorable, pero es honesta.

En una sala técnica, la primera pregunta va a ser *"¿esto lo corriste?"*. Es mucho mejor tener la respuesta que la excusa.

**La decisión importante de hoy no es el formulario.** Es reservar unas horas por semana entre ahora y septiembre para que la respuesta a esa pregunta sea que sí.
