# El modelo de la bomba

Un equipo pequeño escucha una bomba con un micrófono. El modelo aprendió **solo con sonido normal**: cuando no logra reconstruir lo que oye, el error sube y el equipo da una alerta. El audio no sale del equipo; sale un evento de unos cientos de bytes.

```
WAV 16 kHz ──► log-mel (64 bandas, 5 tramas = 320 números por vector) ──► autoencoder ONNX
          ──► error de reconstrucción por vector ──► score del clip (la media) ──► ¿score > umbral? ──► alerta
```

| Archivo | Qué hace |
|---|---|
| `features.py` | Las features: WAV → log-mel → vectores de 320. Solo numpy y la librería estándar. La misma función corre al entrenar y en el equipo (se copia a `component/features.py` y a cada `build/<versión>/`). |
| `dataset.py` | Lee MIMII DUE desde el zip (sin descomprimirlo), desde una carpeta o desde el set sintético, y reparte los clips. `train.py` y `prepare_data.py` usan el mismo reparto. |
| `train.py` | Entrena la v1.0.0 y la v2.0.0, cuantiza la v1 a INT8, mide todo y escribe `build/`. |
| `prepare_data.py` | Arma el audio de las cinco bombas (`data/estacion/`) y los dos audios de la lámina 2 (`charla/assets/audio/`). |
| `synth.py` | Un set sintético con los mismos nombres de archivo, solo para probar la tubería. |
| `../component/inference.py` | El componente que corre en el equipo: escucha, decide y publica un evento por clip. |

## El modelo

- **Autoencoder** de scikit-learn (`MLPRegressor`, capas 320 → 128 → 128 → 8 → 128 → 128 → 320, ReLU) con un `StandardScaler` adelante, en un `Pipeline` exportado con skl2onnx. Al grafo se le suman tres nodos (resta, cuadrado, media) para que el `.onnx` devuelva directamente el error de cada vector: el contrato es «features adentro, error afuera».
- **Score del clip** = media del error de reconstrucción de sus ≈ 300 vectores.
- **Umbral** = percentil 95 de los scores de los clips normales de validación (10 % de los normales de entrenamiento, que el modelo no vio). Significa: aceptas que cerca de 5 % del sonido normal dé alerta. Es un solo umbral para las tres secciones, como en la flota. Cambia con `--percentil`. En el equipo es configuración del componente: se cambia sin reentrenar.
- **v1.0.0**: aprende con sonido normal del dominio *source*.
- **v2.0.0** («la versión mala con historia»): el mismo modelo, pero su entrenamiento incluye la semana en que una bomba ya fallaba: la mitad de los clips de falla *source* de la sección de la bomba-01 (sección 00), con todas sus tramas. Aprende que fallar es normal. Se mide con fallas que **no** vio.
- **INT8**: `onnxruntime.quantization.quantize_dynamic` sobre el ONNX de la v1 (pesos en INT8, activaciones cuantizadas al vuelo). Solo para medir: el componente usa `model.onnx`.
- **Entrenamiento con poca RAM**: de cada clip de entrenamiento entran 48 vectores al azar (`--tramas`), no los ≈ 300.

## Los datos y su licencia

**MIMII DUE** (Hitachi, Ltd.), set de desarrollo de bombas: `dev_data_pump.zip`. Licencia **CC BY-NC-SA 4.0** (atribución, no comercial, compartir igual). https://zenodo.org/records/4740355

> Tanabe, R., Purohit, H., Dohi, K., Endo, T., Nikaido, Y., Nakamura, T., y Kawaguchi, Y. (2021). *MIMII DUE: Sound Dataset for Malfunctioning Industrial Machine Investigation and Inspection with Domain Shifts due to Changes in Operational and Environmental Conditions*. arXiv:2105.02702.

Clips de 10 s, 16 kHz, mono. Tres secciones (00, 01, 02); cada una es un grupo de bombas. El dominio *source* es la condición de entrenamiento; el *target*, otra velocidad de operación y otro ruido de ambiente. Por sección trae unos mil clips normales *source* para entrenar, tres *target* y, para prueba, clips normales y de falla de cada dominio. `train.py` imprime cuántos encontró.

Los nombres se descubren con `section_(\d+)_(source|target)_(train|test)_(normal|anomaly)_(\d+)`, así que da igual si el zip trae una carpeta raíz o atributos al final del nombre. Si el zip trae otras máquinas, se queda con `pump`.

### El reparto (`dataset.py`, determinista)

| Grupo | Clips | Para qué |
|---|---|---|
| train | 90 % de los normales *source* de entrenamiento | aprende la v1 (y la v2) |
| val | 10 % de los normales *source* de entrenamiento | fija el umbral |
| contaminación | la mitad de las fallas *source* de prueba de la sección 00 | solo entra a la v2 |
| prueba | todos los clips de prueba menos la contaminación | medir y armar la flota |

Los tres clips *target* de entrenamiento no se usan: el modelo nunca oyó la otra velocidad.

### La flota (`prepare_data.py`)

`data/estacion/bomba-0N/{normal,falla,nuevo}/`, cinco clips por carpeta, todos **de prueba**, nunca de entrenamiento ni de la contaminación:

- `normal`: normales *source* · `falla`: fallas *source* · `nuevo`: normales *target* (la bomba cambió de velocidad).
- Cinco bombas salen de tres secciones: **la bomba-01 y la bomba-04 comparten la sección 00, y la bomba-02 y la bomba-05 la sección 01**, cada una con clips distintos. La bomba-03 tiene la sección 02.
- `build/clips.json` dice qué clip quedó en cada carpeta.
- Con `--scores build/scores.csv` (después de entrenar) elige clips para que la demo se vea igual cada vez: fallas que la v1 detecta (y, en la bomba-01, que la v2 no detecta) y normales sin alerta. Las carpetas `nuevo` se eligen al azar. **Las cifras de la charla salen de todo el set de prueba, no de estos clips.**
- Los dos audios de la lámina 2 salen de la sección de la bomba-03, dominio *source*, fuera de la flota y del entrenamiento: `charla/assets/audio/bomba-a.wav` (normal) y `bomba-b.wav` (falla), copiados sin cambios, con `ATRIBUCION.txt` al lado. Con `--scores`, la B es la falla más clara para la v1 y la A un normal típico. **Con audio sintético no toca `charla/assets/`.**

## Cómo correrlo con los datos reales

Deja el zip (descarga manual de Zenodo) en `poc-devopsdays/data/dev_data_pump.zip`. Desde `poc-devopsdays/`:

```bash
python3 model/train.py --data data/dev_data_pump.zip                               # modelos, métricas, scores
python3 model/prepare_data.py --data data/dev_data_pump.zip --scores build/scores.csv   # flota y audios de la charla
python3 ../charla/tools/metrics.py v1.recall_source v1.recall_target v2.recall_source int8.agree_pct
python3 -m unittest discover -s tests -p 'test_model*.py' -v                      # la tubería, con audio sintético
```

Si ya lo descomprimiste, `--data` también acepta la carpeta. Medido en el sandbox (4 CPU, 3 GB de RAM) con un set sintético del tamaño esperado del real (4 209 clips de 10 s): `train.py` tarda **≈ 1 minuto** y usa **≈ 1 GB** de memoria pico; `prepare_data.py`, segundos. Leer el zip real suma el tiempo de descomprimir el audio, clip por clip.

Para escuchar una bomba en tu máquina, sin AWS:

```bash
echo falla > /tmp/modo
AWS_IOT_THING_NAME=bomba-03 python3 build/1.0.0/inference.py --model build/1.0.0/model.onnx \
    --stats build/1.0.0/stats.json --audio-root data/estacion --mode-file /tmp/modo --interval 1 --local
```

Sin los datos reales (solo prueba la tubería; todo queda marcado `"synthetic": true`):

```bash
python3 model/synth.py                                   # data/synthetic/, 141 clips
python3 model/train.py --data data/synthetic
python3 model/prepare_data.py --data data/synthetic --scores build/scores.csv
```

## Qué queda en `build/`

| Archivo | Qué es |
|---|---|
| `<versión>/model.onnx` | El autoencoder. Entrada `features` (N × 320, float32), salida `score` (N): error por vector. |
| `<versión>/stats.json` | La huella del sonido normal (media y desviación de las 320 features), el umbral, el percentil, la versión, el sha256 de `model.onnx` y `"synthetic"`. |
| `<versión>/features.py`, `inference.py` | El código que corre en el equipo, copiado tal cual. |
| `1.0.0/model.int8.onnx` | La v1 en INT8, solo para medir. |
| `metrics.json` | Las cifras de las láminas (abajo). |
| `scores.csv` | El score de cada clip de prueba con la v1, la v2 y la INT8, y su `input_z`. |
| `clips.json` | El mapa de la flota y de los audios de la charla. |

## Qué significa cada clave de `metrics.json`

Valores crudos: fracciones de 0 a 1, AUC de 0 a 1, KB y ms. `charla/tools/metrics.py` los formatea para las láminas y devuelve «por medir» si `"synthetic"` es `true`. Todo se mide sobre los clips de prueba menos los que contaminaron a la v2, y las tres secciones juntas con un solo umbral.

| Clave | Qué es |
|---|---|
| `dataset`, `synthetic` | De dónde salió el audio. Con `true`, ninguna cifra llega a una lámina. |
| `v1.auc_source`, `v1.auc_target` | AUC de la v1 (normal contra falla) en el dominio de entrenamiento y en el nuevo. 0,5 es azar. |
| `v1.recall_source`, `v1.recall_target` | Fallas detectadas al umbral: fracción de clips de falla con alerta. |
| `v1.false_alarm_source`, `v1.false_alarm_target` | Falsas alarmas: fracción de clips normales con alerta. |
| `v1.threshold` | El umbral de la v1. |
| `v1.alert_rate_source`, `v2.alert_rate_source` | Fracción de clips *source* (normales y de falla) con alerta. La v2 da menos alertas. |
| `v2.auc_source`, `v2.recall_source`, `v2.false_alarm_source` | Lo mismo para la v2, con fallas que no vio al entrenar. `v2.threshold` es su umbral. |
| `int8.size_fp32_kb`, `int8.size_int8_kb` | Tamaño del `.onnx` en FP32 y en INT8. |
| `int8.lat_fp32_ms`, `int8.lat_int8_ms` | Latencia por clip de 10 s: features + inferencia, mediana, CPU, un hilo, sin contar la lectura del disco. Las features pesan igual en las dos. |
| `int8.agree_pct` | Fracción de clips de prueba (*source* y *target*) con la misma decisión en FP32 y en INT8, con el mismo umbral. |
| `int8.auc_delta` | AUC *source* de la INT8 menos AUC *source* de la FP32. |
| `input.z_source`, `input.z_target` | Nivel de la entrada: `input_z` medio de los clips normales de cada dominio (ver abajo). `input.z_val` es la referencia con los normales de validación. |
| `detalle` | No va a láminas: conteos, épocas, tiempos, memoria pico y las mismas métricas por sección. |

`input_z` = media de |(feature − media) / desviación| sobre todos los vectores del clip, con la huella de `stats.json`. Con el audio de entrenamiento queda por debajo de 1; sube cuando el sonido cambia aunque el modelo no dé error.

## Lo honesto, para las preguntas

- **`truth` solo existe en la demo.** El equipo sabe qué carpeta suena (`falla` → `anomaly`; `normal` y `nuevo` → `normal`). En producción no lo sabes al momento: llega tarde, con la orden de mantenimiento.
- **La v2 está contaminada a propósito.** Es una simulación de un error típico (reentrenar con datos que nadie revisó), no algo que le pasó a un cliente. La v2 corre sin errores, con la misma latencia; solo decide peor.
- **Los clips de la flota se eligen** (con `--scores`) para que la demo sea repetible. Las cifras de las láminas no: salen de todo el set de prueba.
- **Un solo umbral para tres secciones.** Las bombas de cada sección suenan distinto; con un umbral por sección los números mejorarían. El AUC mezcla las secciones, así que no es comparable con el de la tarea 2 de DCASE 2021, que se reporta por sección (está en `detalle.por_seccion`).
- **El modelo es pequeño a propósito** (≈ 118 mil parámetros, un MLP de scikit-learn sin GPU). No es el estado del arte; es lo justo para mostrar el ciclo de vida.
- **`input_z` es un resumen simple.** En producción usarías pruebas de distribución por ventana (PSI, KS) calculadas en el equipo.
- **Audio sintético:** `synth.py` sirve para probar la tubería. Sus WAV llevan la marca `SINTETICO` en la cabecera, `train.py` marca todo con `"synthetic": true` y `prepare_data.py` se niega a copiarlo a la charla.
- **`data/` no debería ir a git:** el zip pesa más de 1 GB y la licencia pide atribución y compartir igual.
