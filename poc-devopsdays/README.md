# PoC · La estación · MLOps a ciegas

Una empresa de acueducto (inventada para la charla) tiene estaciones de bombeo en veredas con red intermitente. En cada estación, un equipo pequeño escucha las bombas con un micrófono y un modelo avisa cuando una empieza a sonar distinto. **El audio no sale de la estación: sale un evento de unos cientos de bytes.**

Esta PoC muestra lo que pasa del lado de la infraestructura: cómo llega el modelo a mil equipos, cómo se ve lo que decide, qué pasa cuando se va la red y cómo se vuelve atrás cuando una versión oye peor.

**No hay equipos físicos.** Cada «bomba» es un contenedor Docker con el nucleus real de AWS IoT Greengrass V2, en una EC2 Linux (AWS pide un host Linux para [Greengrass en Docker](https://docs.aws.amazon.com/greengrass/v2/developerguide/run-greengrass-docker.html)). **Todo lo demás es AWS real:** IoT Core, los despliegues y los thing groups de Greengrass, CloudWatch, Lambda, S3 y Parameter Store. Son cinco bombas: `bomba-01` en el anillo 0 (el canario) y `bomba-02` a `bomba-05` en el anillo 1.

Cabe en una semana.

---

## Qué se ve en vivo

| Acto | Qué haces | Qué se ve |
|---|---|---|
| **1 · Escuchar** | `./demo/falla.sh bomba-03` | La 3 suena como la bomba B del inicio de la charla y aparece la alerta |
| **2 · Sin red** | `./demo/red.sh off bomba-03`, esperas, `./demo/red.sh on bomba-03` | La 3 se calla mientras las otras cuatro siguen; al volver llegan sus eventos «tarde». Después, `./demo/dominio.sh bomba-05 nuevo`: la 5 cambia de velocidad y no hay ningún error, pero la entrada se aleja de lo que aprendió |
| **3 · Desplegar por anillos y volver** | `./demo/deploy.sh 2.0.0 anillo-0` y `./demo/falla.sh bomba-01` | La 1 pasa a la v2 y no oye la falla; la alarma dispara la Lambda y la 1 vuelve a la v1. El anillo 1 nunca recibió la v2 |

Remate del acto 3: **Greengrass revierte despliegues fallidos, no modelos equivocados. Esa compuerta la pones tú.**

### Las señales del modelo (dashboard `estacion`)

| Pregunta | Widget | Métrica (namespace `Estacion`) |
|---|---|---|
| ¿Qué decide? | alertas por bomba | `Alertas` por `Device` |
| ¿Con cuánta seguridad? | score contra umbral, por versión | `Score` y `Umbral` por `Version` |
| ¿Se parece a lo que aprendió? | nivel de la entrada | `InputZ` |
| ¿Qué versión corre dónde? | inferencias por versión | `Inferencias` por `Version` |
| ¿En cuánto tiempo? | latencia | `LatencyMs` |
| Lo que dispara la vuelta | fallas que nadie oyó | `FallasNoOidas` |

---

## Arquitectura

```
 UNA EC2 LINUX CON DOCKER · red "estacion"
 ┌───────────────────────────────────────────────────────────────┐
 │  bomba-01      bomba-02    bomba-03    bomba-04    bomba-05   │
 │  anillo 0      └──────────────── anillo 1 ──────────────────┘ │
 │  (canario)                                                    │
 │  cada una es un contenedor con el nucleus real de Greengrass: │
 │   · com.estacion.Escucha  (features + ONNX Runtime)           │
 │   · /data/estacion/<bomba>   audio, solo lectura              │
 │   · /run/estacion/modo       normal | falla | nuevo           │
 └──────────────┬─────────────────────────────▲──────────────────┘
                │ un evento por clip          │ despliegue (artefactos
                │ MQTT QoS 1                  │ con digest, desde S3)
                ▼                             │
 ┌────────────────────────────┐    ┌──────────┴───────────────────────┐
 │ IoT Core                   │    │ IoT Greengrass + S3              │
 │  regla estacion_eventos    │    │  thing groups EstacionAnillo0/1  │
 │  (suma arrived_ts)         │    │  componente com.estacion.Escucha │
 └─────────────┬──────────────┘    └──────────▲───────────────────────┘
               ▼                              │ create-deployment con la
 ┌────────────────────────────┐               │ última versión buena
 │ CloudWatch Logs            │               │ (Parameter Store)
 │  /estacion/eventos         │    ┌──────────┴───────────────────────┐
 │  filtros → métricas        │    │ Lambda estacion-rollback         │
 │  dashboard "estacion"      │ ─▶ │  al anillo 0, nunca al anillo 1  │
 │  alarma fallas-no-oidas    │    └──────────────────────────────────┘
 └────────────────────────────┘ ALARM
```

### Los nombres

| Cosa | Nombre |
|---|---|
| Componente | `com.estacion.Escucha` |
| Cosas (things) | `bomba-01` … `bomba-05` |
| Thing groups | `EstacionAnillo0` (bomba-01) · `EstacionAnillo1` (bomba-02 a 05) |
| Tema MQTT | `estacion/eventos` |
| Regla de IoT | `estacion_eventos` → CloudWatch Logs `/estacion/eventos` |
| Dashboard · alarma · Lambda | `estacion` · `estacion-fallas-no-oidas` · `estacion-rollback` |
| Parámetro | `/estacion/last_good_version` |
| Bucket | `estacion-<cuenta>-<región>`, prefijo `estacion/<versión>/` |
| Docker | red `estacion`, contenedores `bomba-01`…`bomba-05`, volúmenes `bomba-0N-gg`, imagen `estacion/greengrass` |

### El evento (uno por clip escuchado)

```json
{"device": "bomba-03", "model_version": "1.0.0", "sha256": "…", "seq": 1234, "ts": 1760000000000,
 "clip": "section_02_source_test_anomaly_0007", "domain": "source", "score": 0.0123, "threshold": 0.0100,
 "alert": true, "input_z": 1.12, "latency_ms": 3.4, "truth": "anomaly"}
```

`ts` es cuando decidió la bomba. La regla de IoT suma `arrived_ts` (cuándo llegó a la nube); la diferencia es el tiempo que la bomba estuvo sin red, y `watch.sh` la imprime como «llegó N s tarde». `input_z` es la distancia media, en desviaciones estándar, entre las features del clip y la huella de `stats.json`. `truth` existe solo porque la demo sabe qué audio suena.

---

## Plan de la semana

| Día | Qué | Listo cuando |
|---|---|---|
| **1** | Cuenta de pruebas, región, el zip de MIMII DUE en `data/`, `terraform apply` en `infra/` | La EC2 aparece en Session Manager y `docker run hello-world` funciona en ella |
| **2** | `./infra/subir-al-host.sh`; en la EC2: `traer-poc`, `./fleet/build.sh`, `IDENTIDAD=terraform ./fleet/up.sh` | Las cinco bombas aparecen como *Healthy* en la consola de IoT Greengrass |
| **3** | Entrenar (`model/train.py`), armar el audio de las bombas (`model/prepare_data.py`), `./demo/publish.sh` y `./demo/deploy.sh 1.0.0 todas` | `./demo/watch.sh` muestra eventos de las cinco bombas y el dashboard tiene datos |
| **4** | Actos 1 y 2: `falla.sh`, `red.sh`, `dominio.sh` | Mides cuánto tarda la bomba en reconectarse y cuánto en llegar los eventos guardados |
| **5** | Acto 3: `deploy.sh 2.0.0 anillo-0`, la alarma y la vuelta | Ajustas `ALARM_THRESHOLD` con tus datos y cronometras la vuelta completa |
| **6** | Ensayas la charla completa y grabas el video de respaldo | Sabes qué decir mientras esperas el minuto de las métricas |

---

## Paso a paso

Todos los comandos salen de `poc-devopsdays/`. Las partes de nube (`cloud/`, `publish.sh`, `deploy.sh`, `watch.sh`) corren donde tengas el AWS CLI v2; las de la flota (`fleet/`, `falla.sh`, `dominio.sh`, `red.sh`) corren **en la EC2**, porque hablan con Docker.

### 0 · Antes de empezar

- Una **cuenta de AWS de pruebas** y una región (los scripts usan `us-east-1`; cámbiala con `REGION=…`).
- **Permisos.** `cloud/setup.sh` y `cloud/teardown.sh` crean y borran roles, políticas y recursos: úsalos con un administrador de la cuenta de pruebas. `fleet/up.sh` solo necesita lo que pide el instalador de Greengrass para registrar las cosas ([política mínima del instalador](https://docs.aws.amazon.com/greengrass/v2/developerguide/provision-minimal-iam-policy.html)); `setup.sh` ya deja hechos el rol de token exchange, su alias y las políticas de IoT.
- **La EC2.** Linux con Docker (18.09 o más), AWS CLI v2 y `python3`. Salida a internet por 443 y 8883; no hace falta ninguna entrada salvo SSH. Cada nucleus es una JVM y cada bomba suma un proceso con ONNX Runtime: **mide la memoria con `docker stats` antes de elegir el tamaño** (punto de partida razonable: una instancia con 8 GiB de RAM). Si es Graviton, la imagen se construye para esa arquitectura sin cambios.

  Por ejemplo, en Amazon Linux 2023: `sudo dnf install -y docker git && sudo systemctl enable --now docker && sudo usermod -aG docker $USER` (y vuelve a entrar por SSH). Clona este repo en la EC2 y en tu laptop.
- **El audio.** Descarga a mano `dev_data_pump.zip` de [Zenodo](https://zenodo.org/records/4740355) y déjalo en `data/dev_data_pump.zip`. Es MIMII DUE (Hitachi), licencia CC BY-NC-SA 4.0; la atribución completa está en `model/README.md`.

### 1 · La nube (una vez)

**Con Terraform (recomendado).** Crea la nube, la identidad de las cinco bombas y la EC2 que las hospeda; los detalles están en [`infra/README.md`](infra/README.md).

```bash
cd infra && terraform init -backend-config=backend.hcl && terraform apply && terraform output siguiente
```

El estado vive en S3 y el `apply` normal lo hace GitHub Actions, con tu aprobación; la preparación de una sola vez (bucket del estado, OIDC, roles y `backend.hcl`) está en [`infra/README.md`](infra/README.md#con-github-actions).

Con Terraform, las bombas no reciben ninguna credencial de AWS: cada una arranca con su certificado, que `IDENTIDAD=terraform ./fleet/up.sh` baja de Parameter Store solo durante la instalación. Para borrar todo: `./fleet/down.sh` en la EC2, `./infra/limpiar-core-devices.sh` y `terraform -chdir=infra destroy`.

**Sin Terraform.** El mismo resultado en la nube, sin la EC2 ni la identidad de las bombas:

```bash
REGION=us-east-1 ./cloud/setup.sh
```

Crea el bucket, los dos thing groups, el rol de token exchange (con permiso de leer solo este bucket) y su alias, la política mínima de IoT de las bombas, la regla `estacion_eventos`, los siete filtros de métrica, el dashboard, la Lambda, la alarma y el parámetro de la última versión buena. Es idempotente: puedes repetirlo.

### 2 · El modelo y el audio

En una máquina con Python y las librerías del modelo (numpy, scikit-learn, skl2onnx, onnx, onnxruntime). Los detalles, las cifras y la licencia están en [`model/README.md`](model/README.md).

```bash
python3 model/train.py --data data/dev_data_pump.zip                                 # v1.0.0 y v2.0.0 en build/
python3 model/prepare_data.py --data data/dev_data_pump.zip --scores build/scores.csv   # data/estacion/bomba-0N/{normal,falla,nuevo}/
```

Si entrenaste en tu laptop, lleva el código, `build/` y el audio a la EC2: con Terraform, `./infra/subir-al-host.sh` y `traer-poc` en la EC2; sin Terraform, `rsync -a data/estacion/ <ec2>:poc-devopsdays/data/estacion/`.

Para probar solo la tubería sin el audio real: `python3 model/synth.py`, y los mismos dos comandos con `--data data/synthetic`. Todo queda marcado `"synthetic": true`, y `publish.sh` se niega a publicarlo salvo que pases `--allow-synthetic`.

### 3 · La flota (en la EC2)

```bash
./fleet/build.sh          # imagen estacion/greengrass (nucleus 2.18.3, Python y dependencias con versión fija)
IDENTIDAD=terraform ./fleet/up.sh   # red "estacion" + cinco bombas con la identidad de Terraform; opcional: --pequeno
./fleet/up.sh                       # sin Terraform
```

Con `IDENTIDAD=terraform` (en la EC2 de Terraform ya viene puesta en la sesión), cada bomba se instala con su certificado y ninguna credencial de AWS entra al contenedor. Sin Terraform, el primer arranque usa **credenciales temporales de tu sesión de AWS CLI** para registrar cada bomba (cosa, certificado, thing group) y las borra del disco al terminar. Los arranques siguientes no usan credenciales: la identidad de cada bomba vive en su volumen `bomba-0N-gg`. Los logs de cada nucleus quedan en `fleet/logs/bomba-0N/`.

`--pequeno` limita cada bomba a 1 CPU y 1 GB (cámbialo con `CPUS=` y `MEM=`) para parecerse a un equipo chico. Greengrass [no admite límites de recursos por componente dentro de Docker](https://docs.aws.amazon.com/greengrass/v2/developerguide/configure-greengrass-core-v2.html#configure-component-system-resource-limits): el límite es del contenedor. `NUCLEUS_HEAP=256m` es el tope del heap de cada JVM (vacío = sin tope).

Cada bomba tarda un par de minutos en aparecer:

```bash
aws greengrassv2 list-core-devices --query 'coreDevices[].[coreDeviceThingName,status]' --output table
```

### 4 · Publicar y desplegar

```bash
./demo/publish.sh 1.0.0           # sube build/1.0.0/ a S3 y crea la versión del componente (con el umbral de stats.json)
./demo/publish.sh 2.0.0
./demo/deploy.sh 1.0.0 todas      # la v1 a los dos anillos; guarda /estacion/last_good_version
./demo/watch.sh                   # en otra terminal
```

Si no aparecen eventos en 2 o 3 minutos: `tail -f fleet/logs/bomba-01/com.estacion.Escucha.log` (o `greengrass.log` si el componente ni arrancó).

Una versión publicada no se toca: Greengrass calcula el digest de cada artefacto al crearla, y si el archivo cambia en S3 el despliegue falla. Para cambiar algo, versión nueva.

**El umbral es configuración:** `UMBRAL=0.02 ./demo/deploy.sh 1.0.0 anillo-1` lo cambia sin reentrenar ni republicar.

### 5 · Verificar qué versión corre en cada bomba

```bash
aws greengrassv2 list-installed-components --core-device-thing-name bomba-01 \
  --query 'installedComponents[].[componentName,componentVersion,lifecycleState]' --output table
```

### Pruebas

```bash
python3 -m unittest discover -s tests -p 'test_infra*.py' -v     # infraestructura (sin AWS ni Docker)
python3 -m unittest discover -s tests -p 'test_model*.py' -v     # el modelo
```

---

## La demo en el escenario

Tres ventanas, letra grande:

| Izquierda | Derecha arriba | Derecha abajo |
|---|---|---|
| `./demo/watch.sh` | dashboard `estacion` (15 min, refresco de 10 s) | terminal SSH a la EC2 |

`watch.sh` imprime una línea por clip:

```
bomba-03  v1.0.0  ALERTA  score 0,82 (umbral 0,50)  entrada 1,1  4 ms  · llegó 40 s tarde
```

«llegó N s tarde» aparece cuando `arrived_ts − ts` pasa de 10 s. «falla no oída» aparece cuando la bomba sonaba con falla y no avisó.

**Acto 1 · Escuchar.** `./demo/falla.sh bomba-03`. *«Esta es la bomba B del principio. La 3 ya suena así. Miren la pantalla: ALERTA. El audio no salió de la estación; salió esta línea.»* Señala en el dashboard cómo sube la bomba-03. Deja la falla encendida: el acto 2 la necesita.

**Acto 2 · Sin red.** `./demo/red.sh off bomba-03` y espera 40 o 60 s. *«La 3 se calló. Las otras cuatro siguen. ¿Se rompió? No: sigue escuchando y guarda los eventos en una cola local.»* Luego `./demo/red.sh on bomba-03`: llegan de golpe, con «llegó 40 s tarde». *«No se perdió nada.»* Ahora sí: `./demo/falla.sh bomba-03 off`.
Después, la deriva: `./demo/dominio.sh bomba-05 nuevo`. *«La 5 cambió de velocidad. Cero errores, cero excepciones. Miren la entrada: se aleja de lo que aprendió.»* Para dejarlo como estaba: `./demo/dominio.sh bomba-05 normal`.

**Acto 3 · Desplegar por anillos y volver.** `./demo/deploy.sh 2.0.0 anillo-0`. *«Una sola estación recibe la versión nueva: el canario.»* Cuando la bomba-01 pase a v2.0.0 en `watch.sh`, `./demo/falla.sh bomba-01`. La 1 corre sin errores, con la misma latencia, y **no oye la falla** («falla no oída»). Mientras la alarma junta datos, explica la compuerta (el dashboard muestra «fallas que nadie oyó»). Cuando la alarma dispara, la Lambda crea un despliegue con la última versión buena y la 1 vuelve a v1.0.0: ALERTA otra vez. El anillo 1 nunca recibió la v2.
*«Greengrass revierte despliegues fallidos, no modelos equivocados. Esa compuerta la pones tú.»* Al terminar: `./demo/falla.sh bomba-01 off`.

La vuelta tarda varios minutos (el filtro de métrica, la alarma, la Lambda y el despliegue suman retrasos): **cronométrala en el ensayo** y prepara qué decir mientras tanto. Atajo para la versión de 30 minutos: lanza `./demo/deploy.sh 2.0.0 anillo-0` durante la espera del acto 2, así la bomba-01 ya está en v2 cuando empieza el acto 3.

**Lleva el video de respaldo.** El wifi de un evento es el peor lugar del mundo para depender de MQTT.

---

## Lo honesto, para las preguntas

- **`truth` solo existe en la demo.** El equipo sabe qué carpeta suena. En producción no lo sabes al momento: llega tarde, con la orden de mantenimiento. Ahí la compuerta no cuenta «fallas no oídas»: compara el canario contra el anillo 1 (la tasa de alertas, la distribución del score y de la entrada) antes de seguir.
- **Un evento por clip no escala.** Cada 3 segundos por bomba son 5 × 3 600 / 3 = 6 000 mensajes por hora aquí, y 8,64 millones al día con mil bombas a un evento cada 10 s. En producción el equipo manda un resumen por minuto y el detalle solo cuando algo cambia. Eso no está en la PoC.
- **La cola vive en memoria.** El nucleus guarda los mensajes QoS 1 sin red en una cola de 2,5 MB por defecto (`mqtt.spooler`). Para horas o días sin red hace falta el [`aws.greengrass.DiskSpooler`](https://docs.aws.amazon.com/greengrass/v2/developerguide/disk-spooler-component.html). Si la cola se llena, el nucleus rechaza los mensajes nuevos.
- **Cada nucleus es una JVM.** Cinco bombas son cinco JVM más cinco procesos con ONNX Runtime en una sola máquina. En la realidad cada equipo tiene la suya, y puede ser un nucleus lite si no alcanza la memoria.
- **El anillo 0 es una sola bomba.** Con un solo equipo, el canario no tiene con qué compararse; por eso aquí la señal es la falla que nadie oyó.
- **Cinco bombas salen de tres secciones de MIMII DUE.** La bomba-01 y la bomba-04 comparten la sección 00, y la bomba-02 y la bomba-05 la sección 01, cada una con clips distintos. La bomba-03 tiene la sección 02. Los clips de la flota se eligen para que la demo sea repetible; las cifras de las láminas salen de todo el set de prueba, no de ellos.
- **Un solo umbral** para las tres secciones, como en la flota. Las bombas de cada sección suenan distinto.
- **El audio sintético** (`model/synth.py`) solo prueba la tubería. Ninguna cifra que salga de él llega a una lámina.
- **Los permisos son mínimos, pero medidos solo en papel** (ver abajo). Si algo falla en el primer ensayo, empieza por los permisos y la región.

---

## Qué verifiqué y qué no

**Primer ensayo de punta a punta (12 de octubre de 2026, us-east-1, EC2 t3.large, audio real de MIMII DUE).** Los tres actos funcionaron con Terraform, `IDENTIDAD=terraform` y las cinco bombas en Docker:

| Paso | Medido |
|---|---|
| `fleet/build.sh` · `up.sh` (cinco bombas instaladas) | menos de 1 min · 40 s; *Healthy* en un par de minutos |
| `deploy.sh 1.0.0 todas` → primer evento · las cinco reportando | 7 s · unos 100 s |
| Acto 1: `falla.sh bomba-03` → ALERTA | el clip siguiente (1 s). Scores de 0,35 a 0,42 contra un umbral de 0,34: poco margen, pero son siempre los mismos clips |
| Acto 2: 45 s sin red → llegan los eventos guardados | 5 s tras `red.sh on`; hasta «llegó 50 s tarde»; `seq` sin huecos y **5 duplicados** (QoS 1 es «al menos una vez») |
| Acto 2: `dominio.sh bomba-05 nuevo` | la entrada pasa de ~0,9 a 1,6–2,2 desde el primer clip. Ojo: también salen **alertas falsas** en 3 de cada 5 clips |
| Acto 3: `deploy.sh 2.0.0 anillo-0` → la bomba-01 en v2 | 15 s; ninguna bomba del anillo 1 reportó v2 |
| Acto 3: `falla.sh bomba-01` → alarma → Lambda → la 1 en v1 con ALERTA | **99 s**: alarma a los 91 s, despliegue de la Lambda a los 92 s, primer evento en v1 a los 99 s. La v2 no oye 3 de cada 5 clips (unas 12 por minuto contra el umbral de 8) |
| Estado del despliegue de la vuelta en `list-deployments` | `ACTIVE` (no `COMPLETED`) |
| Memoria | ~220 MiB por bomba; 1,4 GiB en uso de 7,8: una t3.medium alcanza |

Dos arreglos salieron del ensayo: el `--init-config` del entrypoint necesita la extensión `.yaml` (el nucleus decide el formato por la extensión), y `up.sh` ahora limpia la carpeta de identidad que Docker recrea como root si un intento anterior quedó reiniciándose. El widget de alarma del dashboard no puede llevar `metrics` (CloudWatch lo rechaza).

**Antes del ensayo**, en un sandbox Linux sin Docker y sin credenciales de AWS:

- `bash -n` de todos los scripts; todos fallan al primer error (`set -euo pipefail`).
- La receta parsea como YAML y su `Run` es el del plan; además, **ese mismo comando se ejecutó** con `--local` contra el `inference.py` y el `build/1.0.0` del modelo, y los campos del evento son los que leen los filtros de métrica y `watch.sh`.
- El dashboard es JSON válido y solo usa las siete métricas que crea `setup.sh`.
- La Lambda, con clientes de boto3 simulados a mano: con la alarma en `OK` (o sin datos) no hace nada; en `ALARM` despliega la última versión buena al anillo 0.
- `publish.sh`, `deploy.sh`, `up.sh`, `down.sh`, `setup.sh`, `teardown.sh`, `entrypoint.sh` y los scripts de la demo, contra un `aws` y un `docker` falsos que anotan lo que se les pide: nombres, thing groups, montajes, límites, orden, que `publish.sh` se niegue con audio sintético y use el umbral de `stats.json`, que las credenciales se borren al terminar, y que cada documento que `setup.sh` manda a AWS (políticas de IAM y de IoT, regla, dashboard) sea JSON válido sin marcadores sin llenar.
- El formato de `watch.sh`.
- `infra/` (Terraform): los `.tf` parsean como HCL, y los nombres, la regla, los siete filtros, la alarma y la política de las bombas son los mismos que en `setup.sh`. `up.sh` y el entrypoint con `IDENTIDAD=terraform`: bajan la identidad de Parameter Store, la montan solo en la instalación y el nucleus se instala con `--init-config` sin credenciales de AWS.

**Lo que quedaba por verificar antes del ensayo.** El ensayo de arriba ya resolvió `terraform validate` y `plan`, el `docker build`, el nucleus en el contenedor, la conexión con la política mínima, los filtros de métrica, que la alarma invoque la Lambda, los tiempos y la memoria. Sigue sin probarse lo demás:

- **No corrí `terraform validate` ni `plan`:** el sandbox no llega al registro de Terraform. Córrelos antes del primer `apply`.
- **Nada corrió contra AWS real ni contra Docker real.** El `docker build` (paquetes de apt, ruedas de pip, la descarga del nucleus 2.18.3 desde la URL oficial) no se ejecutó; el sandbox no llega a esa URL.
- **El nucleus dentro del contenedor.** Que el instalador acepte `--start false`, que reutilice el rol y el alias creados por `setup.sh`, y que `alts/current/distro/bin/loader` arranque en primer plano bajo `docker --init`.
- **Los permisos mínimos.** La política de IoT de las bombas sale de la [guía de Greengrass](https://docs.aws.amazon.com/greengrass/v2/developerguide/device-auth.html#greengrass-core-minimal-iot-policy) con un comodín `bomba-*`; la de la Lambda, de las acciones que la [referencia de autorización](https://docs.aws.amazon.com/service-authorization/latest/reference/list_awsiotgreengrassv2.html) lista para `CreateDeployment`. Si una bomba no conecta, prueba `THING_POLICY_NAME=GreengrassV2IoTThingPolicy` (la permisiva que crea el instalador) con `./fleet/down.sh --borrar-things` y `./fleet/up.sh`.
- **La sintaxis de los filtros de métrica** (`IS TRUE` / `IS FALSE` combinados con `&&` y con dimensiones) y que la alarma invoque la Lambda directamente.
- **`"reset": [""]`.** `deploy.sh` y la Lambda lo mandan para que cada versión arranque con su propio umbral por defecto. Está en la [documentación](https://docs.aws.amazon.com/greengrass/v2/developerguide/update-component-configurations.html) como la forma de volver a la configuración por defecto; no verifiqué qué hace con una versión nueva.
- **Los tiempos:** cuánto tarda una bomba en reconectarse tras `red.sh on` (el nucleus reintenta la conexión por su cuenta; no sé con qué espera), cuánto la métrica y la alarma, y cuánto la vuelta completa. Tampoco medí la memoria de cada nucleus ni lo que hace `--pequeno` con el componente.
- **La salida `JAVA_TOOL_OPTIONS`** (`-Xmx256m`): la JVM imprime «Picked up JAVA_TOOL_OPTIONS» en cada arranque. Si el script `loader` se quejara, deja `NUCLEUS_HEAP=` vacío y fija `jvmOptions` con un despliegue del nucleus, como indica la [guía](https://docs.aws.amazon.com/greengrass/v2/developerguide/configure-greengrass-core-v2.html#jvm-tuning).
- **`abortConfig` y el despliegue exponencial** con grupos de 1 y de 4 bombas: la forma del JSON coincide con la [referencia del CLI](https://docs.aws.amazon.com/cli/latest/reference/greengrassv2/create-deployment.html), pero con tan pocas bombas casi no se nota la rampa.
- `DOCKER_HOST=ssh://usuario@ec2 ./demo/falla.sh bomba-03` (correr los comandos de la demo desde tu laptop) debería funcionar, pero no lo probé.

---

## Costo

No hay una cifra aquí porque no la he medido. **Se mide con Cost Explorer tras el ensayo.** Lo que cobra mientras está arriba:

- **La EC2** (y su disco), por hora encendida. Es lo que más pesa; apágala cuando no ensayes.
- **IoT Core:** mensajes. Con un evento cada 3 s por bomba son 6 000 por hora.
- **IoT Greengrass:** los core devices activos (cinco aquí); mira su página de precios.
- **CloudWatch:** ingestión y almacenamiento de logs (7 días de retención), 14 métricas personalizadas (`Alertas` ×5, `Score` ×2, `Umbral` ×2, `Inferencias` ×2, `InputZ`, `LatencyMs`, `FallasNoOidas`), un dashboard y una alarma.
- **Lambda, S3 y Parameter Store:** casi nada a esta escala.

Precios vigentes: [IoT Core](https://aws.amazon.com/iot-core/pricing/) · [IoT Greengrass](https://aws.amazon.com/greengrass/pricing/) · [CloudWatch](https://aws.amazon.com/cloudwatch/pricing/) · [EC2](https://aws.amazon.com/ec2/pricing/on-demand/).

## Apagar todo

```bash
./fleet/down.sh                  # en la EC2: apaga las bombas (conserva su identidad)
./fleet/down.sh --borrar-things  # además borra los volúmenes y las cosas y certificados en AWS
./cloud/teardown.sh              # borra todo lo de la nube, incluido el bucket (pide confirmación)
```

Y apaga o termina la EC2. Confirma en Cost Explorer, uno o dos días después, que no queda nada que cobre.

## Si algo falla

| Síntoma | Dónde mirar |
|---|---|
| La bomba no aparece como *Healthy* | `docker logs bomba-03` y `fleet/logs/bomba-03/greengrass.log`; casi siempre es un permiso o la región |
| El componente no descarga artefactos | El rol `GreengrassV2TokenExchangeRole` debe poder leer `s3://estacion-<cuenta>-<región>/*`; `setup.sh` lo deja puesto. Si cambiaste un archivo de S3 después de publicar, el digest no coincide: versión nueva |
| `fleet/logs/bomba-03/com.estacion.Escucha.log` dice «no pude escuchar … Permission denied» | El componente corre como `ggc_user`; `up.sh` abre la lectura del audio, pero si copiaste los archivos después, repite `chmod -R a+rX data/estacion` |
| Hay eventos en `watch.sh` pero el dashboard está vacío | Las métricas tardan alrededor de un minuto; revisa los filtros en el grupo de logs `/estacion/eventos` |
| La alarma dispara en el acto 1 o no dispara en el 3 | Ajusta `ALARM_THRESHOLD` (fallas no oídas por minuto, por defecto 8) y vuelve a correr `cloud/setup.sh` |
| La bomba no vuelve a conectar tras `red.sh on` | Espera: el nucleus reintenta la conexión solo. Si pasan varios minutos, `docker restart bomba-03` |

## Documentación de AWS que usa esta PoC

- [Greengrass en Docker](https://docs.aws.amazon.com/greengrass/v2/developerguide/run-greengrass-docker.html) · [argumentos del instalador](https://docs.aws.amazon.com/greengrass/v2/developerguide/configure-installer.html) · [requisitos y configuración del nucleus](https://docs.aws.amazon.com/greengrass/v2/developerguide/greengrass-nucleus-component.html)
- [Publicar componentes](https://docs.aws.amazon.com/greengrass/v2/developerguide/publish-components.html) · [referencia de recetas](https://docs.aws.amazon.com/greengrass/v2/developerguide/component-recipe-reference.html) · [crear despliegues](https://docs.aws.amazon.com/greengrass/v2/developerguide/create-deployments.html)
- [Autorizar a los equipos a usar servicios de AWS](https://docs.aws.amazon.com/greengrass/v2/developerguide/device-service-role.html) · [autenticación y política mínima de IoT](https://docs.aws.amazon.com/greengrass/v2/developerguide/device-auth.html)
- [Sintaxis de filtros de métrica](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html)
