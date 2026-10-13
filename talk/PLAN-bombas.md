# Plan de implementación · la estación de bombeo como hilo conductor

Contrato común para todos los que tocan la charla y la PoC. Si algo aquí choca con el código, manda este archivo; si choca con el spec «SPEC · MLOps a ciegas, versión DevOps», manda el spec (lo mantiene Claude, el orquestador).

> **Nota (12 de octubre, noche):** la lista de láminas de §2 es la del primer corte. La charla de ~26 min (30 láminas y 10 anexos, títulos formales) está en `GUION-devopsdays.md` y `tools/deck.src.html`, que mandan sobre esta tabla.

## 0 · Reglas que no se negocian

- Español neutro de Colombia, **tú** (nunca vos/voseo). No usar la palabra «plata». Frases cortas.
- **Ninguna lámina cita a AWS**: ningún pie de lámina con artículos, blogs ni páginas de AWS. Los servicios de AWS sí se nombran y se dibujan con los íconos oficiales (`AWS_ICONS=/sessions/modest-fervent-pascal/mnt/Icon-package_07312026`). Los datos de la documentación de AWS se dicen en voz alta; su enlace va en el guion o en el README de la PoC.
- **Nunca inventar números.** Todo número en una lámina tiene una fuente independiente al pie (Gartner, IDC, papers) o sale de `poc-devopsdays/build/metrics.json` vía `talk/tools/metrics.py` (`{{M:clave}}`) o es un cálculo cuya fórmula va al pie. Nada que salga de audio sintético llega a una lámina: `metrics.py` devuelve «por medir».
- Sin `kubectl` en pantalla. Sin cámaras ni casos de retail. Sin logo de EPAM. No recolorear ni deformar imágenes o logos de la plantilla.
- No descargar ni instalar código de terceros (repos de GitHub, skills, baselines). Librerías de PyPI ya presentes (numpy, onnxruntime, scikit-learn, skl2onnx, scipy) sí; evita dependencias nuevas.
- El entorno (sandbox Linux) **no tiene Docker** y **no llega a Zenodo**. 4 CPU, 3 GB de RAM.
- Cada agente toca **solo sus archivos** (tabla del §8). Si necesitas un cambio en un archivo ajeno, dilo en tu reporte final; no lo edites.

## 1 · El caso

Una empresa de acueducto, **inventada para la charla**, tiene estaciones de bombeo en veredas con red intermitente. En cada estación, un equipo pequeño escucha las bombas con un micrófono y un modelo avisa cuando una empieza a sonar distinto. El audio nunca sale de la estación; sale un evento de unos cientos de bytes.

- Datos reales: **MIMII DUE** (Hitachi), bombas, set de desarrollo `dev_data_pump.zip`: secciones 00–02, dominio *source* (entrenamiento) y *target* (otra velocidad de operación y otro ruido de ambiente), clips de 10 s, 16 kHz, mono. Licencia **CC BY-NC-SA 4.0**; la atribución va en la lámina 2 y en A8.
- Modelo: autoencoder sobre log-mel que aprende **solo con sonido normal**; el score es el error de reconstrucción. ONNX en FP32 e INT8.
- **v1.0.0**: entrenada con sonido normal del dominio *source*.
- **v2.0.0** («la versión mala con historia»): se reentrenó con más audio, que incluía la semana en que una bomba ya estaba fallando (clips de falla mezclados en el entrenamiento). Aprendió que fallar es normal: corre sin errores, da menos alertas y no oye las fallas. Se evalúa con fallas que **no** vio al entrenar.
- Drift: el dominio *target* (otra velocidad). Ningún error; los scores se corren.
- Cuentas (calculadas, sin fuente externa): un micrófono a 16 kHz y 16 bits = 32 000 B/s ≈ **115 MB por hora** ≈ **2,76 GB al día** por bomba; mil bombas ≈ **2,76 TB al día**. Un evento cada 10 s = 8 640 por bomba al día ≈ **8,64 M** mensajes al día para mil bombas; un resumen por minuto ≈ **1,44 M**.

## 2 · Las láminas (34 + 8 anexos)

`id` = `data-id` en `deck.src.html`, ancla `<!-- id: x -->` en el guion y clave de `BUILDERS` en el PowerPoint. «Hilo» = la línea de la estación en esa lámina.

| # | id | Título | Qué lleva | Hilo | Figura |
|---|---|---|---|---|---|
| 1 | portada | MLOps a ciegas | Igual que hoy | — | — |
| 2 | suena | ¿Esta bomba está fallando? | Dos tarjetas, «Bomba A» y «Bomba B», cada una con su onda y un botón ▶ que reproduce el audio. Clic 1: «Levanten la mano: ¿A, B o las dos?». Pie: «Sonidos reales de bombas industriales · MIMII DUE, Hitachi · CC BY-NC-SA 4.0» | Presenta la estación; la respuesta llega en la demo (B falla) | `onda_a`, `onda_b`, `{{AUDIO:a}}`, `{{AUDIO:b}}` |
| 3 | cien | ¿Cuántas PC nuevas traen chip para IA? | Igual (Gartner) | — | — |
| 4 | inversion | ¿Cuánto dinero se está invirtiendo en edge? | Igual (IDC). Corte para 30 min | — | — |
| 5 | memes | ¿Por qué la IA se está saliendo de la nube? | Igual | Guion: 115 MB por hora por bomba | — |
| 6 | quien | ¿Quién soy? | La bio vuelve a decir AWS (5 certificaciones de AWS) | — | — |
| 7 | agenda | ¿Qué van a aprender hoy? | El problema · El patrón · Los seis pasos · En vivo | — | — |
| 8 | div1 | 01 · El problema | Divisor | — | — |
| 9 | nube | ¿Qué tenemos cuando el modelo corre en la nube? | Igual | Guion: si mandaras el audio a la nube, tendrías esto | `nube` |
| 10 | edge | ¿Y cuando baja a la estación? | La estación dibujada; tres clics: equipos de varias generaciones · red intermitente · el audio no puede salir | La estación | `edge` |
| 11 | tablero | ¿Si el panel está en verde, el modelo está bien? | Clic 1: el panel del equipo (CPU, memoria, servicio) en verde. Clic 2: «¿Distingue una falla de una bomba sana?» AUC `{{M:v1.auc_source}}` → `{{M:v1.auc_target}}` cuando cambió la velocidad de la bomba (1 = siempre, 0,5 = lanzar una moneda); abajo, falsas alarmas `{{M:v1.false_alarm_source}}` → `{{M:v1.false_alarm_target}}`. Clic 3: «El equipo está sano. El modelo ya no distingue.» (Se usa AUC y no «fallas detectadas» porque con el cambio de dominio todos los scores suben y la detección puede subir junto con las falsas alarmas.) Pie: «Medido en la PoC con MIMII DUE (bombas, dominio de entrenamiento contra dominio nuevo)» | La bomba cambia de velocidad | — |
| 12 | reflexion1 | A mano alzada | «¿A quién le ha sonado el pager por un modelo?» (igual que hoy) | — | — |
| 13 | div2 | 02 · El patrón | Divisor | — | — |
| 14 | equipo | ¿Qué lleva el equipo de la estación por dentro? | Vista explotada; el sensor es un micrófono | El micrófono | `equipo` |
| 15 | flujo | ¿Qué hace falta para gobernarlo? | Igual (patrón genérico con la pieza de optimizar) | — | `{{ARQ_GEN}}` |
| 16 | aws | ¿Cómo se ve esto en AWS? | El mismo dibujo convertido en servicios, mismos pasos que `flujo` | — | `arq_ref` |
| 17 | div3 | 03 · Los seis pasos | Divisor con la espina grande: Entrenar · Optimizar · Empaquetar · Desplegar · Correr sin red · Monitorear | — | `espina` |
| 18 | entrenar | Paso 1 · ¿Qué sale de la nube? | El árbol real de `build/1.0.0/` (model.onnx, stats.json, features.py, inference.py). ONNX como contrato. SageMaker AI y S3 | «Aprende solo con sonido normal: las fallas son raras» | `entrenar`, pie `espina_1` |
| 19 | optimizar | Paso 2 · ¿Qué cabe en el chip? | Un artefacto por chip, la memoria como restricción; el modelo de la bomba en FP32 contra INT8: `{{M:int8.size_fp32_kb}}` → `{{M:int8.size_int8_kb}}`, `{{M:int8.lat_fp32_ms}}` → `{{M:int8.lat_int8_ms}}`, misma decisión en `{{M:int8.agree_pct}}` de los clips | INT8 para el equipo pequeño | `optimizar`, pie `espina_2` |
| 20 | componente | Paso 3 · ¿Qué es un componente? | La receta YAML real, anotada: artefactos con digest, ciclo de vida, configuración, permisos IPC. IoT Greengrass y S3 | «El umbral es configuración: se cambia sin reentrenar» | `receta`, pie `espina_3` |
| 21 | anillos | Paso 4 · ¿Cómo llega a mil equipos? | Anillo 0 = una estación canario; anillo 1 = el resto. Un thing group por anillo, despliegue exponencial, criterios de aborto, `ROLLBACK` por defecto | Una estación como canario | `anillos`, pie `espina_4` |
| 22 | reflexion2 | A mano alzada | «¿Quién ha hecho rollback un viernes?» (igual que hoy) | — | — |
| 23 | sinred | Paso 5 · ¿Qué sigue funcionando sin red? | Izquierda: el equipo con Greengrass (cola local, stream manager, nucleus lite). Derecha: el sitio con Outposts y EKS local (plano de control local, entrada con x.509, registro local de imágenes) | La estación sigue escuchando y alertando | `sinred`, pie `espina_5` |
| 24 | monitoreo | Paso 6 · ¿Qué ves desde la nube? | IoT Core → regla → CloudWatch Logs → filtro de métrica → alarma → Lambda, con íconos; la regla SQL y un filtro de métrica reales en pantalla | Las señales de la bomba | `monitoreo`, pie `espina_6` |
| 25 | reflexion3 | A mano alzada | «¿Qué versión corre en cada equipo?»; clic: la respuesta, el estado del despliegue por thing group | — | — |
| 26 | div4 | 04 · En vivo | Divisor | — | — |
| 27 | poc | ¿Qué monté para la demo? | Arquitectura de la PoC: cinco bombas simuladas (contenedores con Greengrass real en una EC2) y los servicios; sello «5 bombas · 7 servicios» | Las cinco bombas | `arq_poc` |
| 28 | senales | ¿Cuáles son las señales doradas de un modelo? | La consola de cuatro señales con rótulos de la bomba: ¿qué decide? (alertas por bomba) · ¿con cuánta seguridad? (score contra umbral) · ¿se parece a lo que aprendió? (nivel de la entrada) · ¿qué versión corre dónde? Corte para 30 min | — | `senales` |
| 29 | demo | ¿Cómo se ve un modelo decidiendo? | Los tres actos (§5) con sus comandos | La bomba 3 falla y se queda sin red; la v2 no oye la falla de la 1 | — |
| 30 | costo | ¿Cuánto cuesta observar mil bombas? | Tres cifras: audio crudo 2,76 TB al día · un evento cada 10 s: 8,64 M mensajes al día · resumen por minuto: 1,44 M. Pie con la fórmula. Corte para 30 min | Audio contra eventos | — |
| 31 | llevo | ¿Qué me llevo hoy? | Cinco conclusiones de infraestructura (§2.1) | — | — |
| 32 | final | (frase final) | Vuelve a los audios del inicio: «¿Esta bomba está fallando?» → la línea del evento de la bomba B → «No necesitas ver el modelo. Necesitas que te cuente.» | Cierra el círculo | — |
| 33 | recursos | ¿Dónde sigo después de la charla? | QR del repo y una lectura independiente: *The ML Test Score* | — | — |
| 34 | cierre | Gracias | Igual | — | — |
| A1 | a1 | El evento de la demo, campo por campo | El esquema del §4.2 | — | — |
| A2 | a2 | La vuelta automática, paso a paso | Secuencia: alarma → Lambda → Parameter Store → despliegue al anillo 0 | — | `seq` |
| A3 | a3 | ¿Qué revierte Greengrass solo? | Digest, `failureHandlingPolicy`, `abortConfig`, y lo que no cubre (un modelo que corre bien y decide mal) | — | — |
| A4 | a4 | Permisos y costo | Roles y políticas de la PoC; recursos que cobran y cómo apagarlos (sin cifra de costo si no está medida) | — | — |
| A5 | a5 | De la demo a producción | Hoy el anexo `a2`, ajustado a la bomba: resumen por minuto, DiskSpooler, nucleus lite, compuerta canario contra anillo, etiquetas tardías de mantenimiento | — | — |
| A6 | a6 | ¿Qué método de drift uso? | Hoy el anexo `a3` | — | — |
| A7 | a7 | Regulación | Las tres tarjetas de la lámina `reglas` de hoy | — | — |
| A8 | a8 | Fuentes | Hoy el anexo `a4`, solo fuentes independientes, más MIMII DUE | — | — |

Salen del recorrido: `analogia`, `mito1`, `mito2`, `pasaporte`, `reglas` (→ A7), `drift`, `medir`, `contar`. Las láminas que vuelven (`aws`, `poc`, `costo`, `a2` secuencia, `a3`, `a4`) existen en `outputs/backup-pre-bombas/old/deck.src.bak.html` como punto de partida.

Secciones del PowerPoint: Apertura (`portada`) · 01 · El problema (`div1`) · 02 · El patrón (`div2`) · 03 · Los seis pasos (`div3`) · 04 · En vivo (`div4`) · Cierre (`llevo`) · Anexos (`a1`).

Tiempos: la charla completa dura 35 minutos o menos; el corte a 30 quita 4, 28, 30 y un meme.

### 2.1 · Las cinco conclusiones (lámina 31)

1. El modelo es un artefacto más: versión, digest y receta.
2. Optimiza por chip y mide en el chip.
3. Despliega por anillos, con una compuerta que mire al modelo y no solo al proceso.
4. Diseña para estar sin red: cola local y decisiones locales.
5. Que el modelo cuente qué decide; el dato crudo se queda en el equipo.

## 3 · Marcadores de `deck.src.html`

| Marcador | Lo resuelve | Si falta |
|---|---|---|
| `{{FIG:nombre}}` | `build_iso.FIGS[nombre]()` (incluye `build_figs.FIGS`) | `build_deck.py` pone un recuadro «figura pendiente: nombre» y avisa; no falla |
| `{{M:clave}}` | `metrics.fmt(clave)` (también dentro de las notas del guion) | «por medir» |
| `{{AUDIO:a}}` / `{{AUDIO:b}}` | `talk/assets/audio/pump-a.wav` / `pump-b.wav` como data URI | botón deshabilitado «audio pendiente» |
| `{{ARQ_GEN}}`, `{{FOTO}}`, `{{QR}}`, `{{REPO}}`, `{{LINKEDIN}}`, `{{IMG:…}}`, `{{FONT:…}}` | Igual que hoy | Igual que hoy |

### 3.1 · Figuras (`FIGS`), lienzo 1600 × 900, `data-on="n"` entra en el clic n

| Nombre | Archivo | Qué dibuja |
|---|---|---|
| `equipo` | build_iso.py | Igual, con el sensor como micrófono sobre una bomba |
| `nube` | build_iso.py | Igual |
| `edge` | build_iso.py | La estación: bombas con su equipo; enlace roto; las cuatro restricciones, una por clic (§2, lámina 10) |
| `senales` | build_iso.py | La consola con los rótulos de la bomba |
| `optimizar` | build_figs.py | Igual en forma; suma la memoria del chip y las cifras FP32/INT8 vía `metrics.fmt` |
| `anillos` | build_figs.py | Anillo 0 (una estación, canario) → anillo 1 (el resto); thing group por anillo; `jobExecutionsRolloutConfig` exponencial; `abortConfig`; `failureHandlingPolicy: ROLLBACK`; la flecha de vuelta |
| `onda_a`, `onda_b` | build_figs.py | La envolvente real de `talk/assets/audio/pump-a.wav` / `-b.wav`; si no existe, una línea plana con «audio pendiente». Tamaño 640 × 160 |
| `espina` | build_figs.py | Las seis cajas grandes, para el divisor 03 |
| `espina_1` … `espina_6` | build_figs.py | Barra de pie de 1432 × 44 con el paso n resaltado (para las láminas 18 a 24, encima del pie de la plantilla) |
| `entrenar` | build_figs.py | Sonido normal → autoencoder → `model.onnx` + `stats.json` (la huella del sonido normal) + umbral → S3 |
| `receta` | build_figs.py | `poc-devopsdays/component/recipe.template.yaml` leído al construir, en monoespaciada de 18 px o más, con 4 anotaciones por clic: artefactos con digest · ciclo de vida · configuración (umbral) · permisos IPC |
| `sinred` | build_figs.py | Equipo contra sitio (§2, lámina 23) |
| `monitoreo` | build_figs.py | La tubería con íconos oficiales; un paso por clic |
| `arq_ref` | build_figs.py → build_arch.py | La arquitectura de referencia en AWS, misma disposición que `ARQ_GEN` |
| `arq_poc` | build_figs.py → build_arch.py | La PoC: EC2 con cinco contenedores (pump-01…05), anillo 0 y anillo 1, y los servicios |
| `seq` | build_figs.py → build_seq.py | La secuencia de la vuelta automática |

Paleta: navy #071329, morado #6D28D9, azul #2448FF, cian #00BCEB, pizarra #475569, gris #5C7290, claro #F4F7FC, línea #D5DEEA. Letra Calibri (Carlito embebida). Zona útil x 84–1516, y 225–760.

## 4 · La PoC (`poc-devopsdays/`)

### 4.1 · Nombres

| Cosa | Nombre |
|---|---|
| Componente | `com.station.Listener` |
| Things | `pump-01` … `pump-05` |
| Thing groups | `StationRing0` (pump-01) · `StationRing1` (pump-02 a 05) |
| Tema MQTT | `station/events` |
| Regla de IoT | `station_events` → CloudWatch Logs `/station/events` (suma `arrived_ts`) |
| Métricas (namespace `Station`) | `Alertas` (por `Device`), `Score` y `Inferencias` (por `Version`), `InputZ`, `LatencyMs`, `MissedFaults` (`truth` = anomaly y `alert` = false) |
| Dashboard | `station` |
| Alarma | `station-missed-faults` → Lambda `station-rollback` |
| Parámetro | `/station/last_good_version` |
| Bucket | `station-<cuenta>-<región>`, prefijo `station/<versión>/` |
| Docker | red `station`, contenedores `pump-01`…`pump-05`, imagen `station/greengrass` |

### 4.2 · El evento (un JSON por clip escuchado, en `station/events`)

```json
{
  "device": "pump-03",
  "model_version": "1.0.0",
  "sha256": "<sha256 de model.onnx>",
  "seq": 1234,
  "ts": 1760000000000,
  "clip": "section_02_source_test_anomaly_0007",
  "domain": "source",
  "score": 0.0123,
  "threshold": 0.0100,
  "alert": true,
  "input_z": 1.12,
  "latency_ms": 3.4,
  "truth": "anomaly"
}
```

`ts` en milisegundos, cuando el equipo decidió. `input_z` = distancia media, en desviaciones estándar, de las features del clip a la huella de `stats.json`. `truth` existe solo porque la demo sabe qué audio suena. Sin red, la cola del nucleus guarda los eventos; al volver llegan con `arrived_ts − ts` grande y `watch.sh` imprime «llegó N s tarde».

### 4.3 · Artefactos por versión (`build/<versión>/`, igual en S3)

`inference.py`, `features.py`, `model.onnx`, `stats.json` (media y desviación de las features, umbral, versión, sha256). Además, solo para medir: `model.int8.onnx`. `build/metrics.json` con las claves de `talk/tools/metrics.py` y `"synthetic": true|false`.

### 4.4 · El componente

```
python3 -u {artifacts:path}/inference.py --model {artifacts:path}/model.onnx --stats {artifacts:path}/stats.json
        --audio-root /data/station --mode-file /run/station/mode --version <V>
        --topic {configuration:/topic} --threshold {configuration:/threshold} --interval {configuration:/intervalSeconds}
```

- El equipo se llama como `AWS_IOT_THING_NAME`. `--local` imprime los eventos en vez de publicarlos (para pruebas sin AWS).
- Audio en el equipo (montado de solo lectura): `/data/station/<equipo>/{normal,fault,shifted}/*.wav`. `/run/station/mode` dice `normal`, `fault` o `shifted` (por defecto `normal`); se relee en cada clip.
- Dependencias (numpy, onnxruntime, awsiotsdk) horneadas en la imagen: la receta no instala nada.
- Configuración por defecto: `topic: station/events`, `intervalSeconds: 3`, `threshold` = el de `stats.json` de esa versión.

### 4.5 · Datos

- `poc-devopsdays/data/dev_data_pump.zip` lo deja Alejandro (descarga manual de Zenodo).
- `model/prepare_data.py` lo lee sin descomprimir todo y arma `data/station/pump-0N/{normal,fault,shifted}/` con clips **de prueba** (nunca de entrenamiento); `nuevo` = clips normales del dominio *target*. Cinco bombas salen de tres secciones: dos bombas comparten sección con clips distintos, y el README lo dice.
- `model/synth.py` genera un set sintético con los mismos nombres de archivo en `data/synthetic/`, solo para probar la tubería.

### 4.6 · La demo (comandos)

| Comando | Hace |
|---|---|
| `./fleet/build.sh` · `./fleet/up.sh` · `./fleet/down.sh` | Imagen, cinco bombas con su red, aprovisionamiento con credenciales temporales |
| `./demo/publish.sh 1.0.0` | Sube los artefactos y crea la versión del componente |
| `./demo/deploy.sh <versión> <ring-0\|ring-1\|todas>` | Despliegue con `ROLLBACK`, despliegue exponencial y `abortConfig` |
| `./demo/fault.sh <bomba> [on\|off]` | La bomba suena con falla (o vuelve a normal) |
| `./demo/network.sh <off\|on> <bomba>` | `docker network disconnect/connect` |
| `./demo/domain.sh <bomba> <nuevo\|normal>` | La bomba cambia de velocidad (dominio *target*) |
| `./demo/watch.sh` | Sigue `/station/events` y formatea: `pump-03  v1.0.0  ALERT  score 0,82 (umbral 0,50)  entrada 1,1  4 ms  · llegó 40 s tarde` |

## 5 · Los tres actos

1. **Escuchar** — `./demo/fault.sh pump-03`: la 3 suena como la bomba B del inicio y aparece la alerta.
2. **Sin red** — `./demo/network.sh off pump-03`, esperar, `./demo/network.sh on pump-03`: la 3 se calla mientras las otras cuatro siguen; al volver llegan sus alertas tarde. Una línea de drift: `./demo/domain.sh pump-05 shifted`.
3. **Desplegar por anillos y volver** — `./demo/deploy.sh 2.0.0 ring-0` y `./demo/fault.sh pump-01`: la 1 pasa a v2 y no oye la falla; la alarma dispara la Lambda y la 1 vuelve a v1. El anillo 1 nunca recibió la v2. Remate: «Greengrass revierte despliegues fallidos, no modelos equivocados: esa compuerta la pones tú».

## 6 · Guion

Forma de las charlas de Freddy Vega: abre con una pregunta a la sala (lámina 2), sin saludo; promete «les voy a enseñar…»; desarma mitos con datos («no son opiniones, son datos»); tres preguntas a mano alzada; anticipa objeciones; provoca antes del resumen («la mayoría no lo va a hacer»); resumen enumerado; cierre circular que vuelve a los audios y termina con una pregunta a la sala. Cada paso del 1 al 6 en 60 a 90 s: la pregunta del título, el servicio que la resuelve, la decisión de diseño, el error típico y la línea de la bomba. `**[CLIC]**` marca cada clic. Cada sección `## …` lleva `<!-- id: x -->` con el id de la lámina. Las cifras medidas se escriben `{{M:clave}}`.

## 7 · Revisión visual (sin navegador)

```
cd /sessions/modest-fervent-pascal/mnt/demo-repository
AWS_ICONS=/sessions/modest-fervent-pascal/mnt/Icon-package_07312026 python3 talk/tools/build_deck.py
node /tmp/q/snap.js talk/devopsdays.html /tmp/q/x.json all      # o "id:paso,id:paso"
python3 /tmp/q/snap.py /tmp/q/x.json /tmp/q/x                     # PDF + PNG por lámina
```

Para una figura sola: `python3 /tmp/q/figqa.py <nombre>` deja `outputs/fig_<nombre>.png`. Mira las imágenes antes de dar algo por hecho.

## 8 · Quién toca qué

| Agente | Archivos |
|---|---|
| Modelo (PoC) | `poc-devopsdays/model/**`, `poc-devopsdays/component/inference.py`, `poc-devopsdays/component/features.py`, `poc-devopsdays/build/**`, `poc-devopsdays/tests/test_model*.py`, `talk/assets/audio/**` |
| Flota (PoC) | `poc-devopsdays/fleet/**`, `poc-devopsdays/demo/**`, `poc-devopsdays/cloud/**`, `poc-devopsdays/component/recipe.template.yaml`, `poc-devopsdays/README.md`, `poc-devopsdays/tests/test_infra*.py` |
| Figuras | `talk/tools/build_iso.py`, `build_figs.py`, `build_arch.py`, `build_seq.py`, `iso.py` (y lee `aws_icons.py`, `metrics.py`) |
| Deck | `talk/tools/deck.src.html`, `talk/tools/build_deck.py` |
| Guion | `talk/GUION-devopsdays.md` |
| PowerPoint (después) | `talk/tools/pptx/**` |
| Orquestador | `talk/PLAN-bombas.md`, `talk/tools/metrics.py`, el spec |
