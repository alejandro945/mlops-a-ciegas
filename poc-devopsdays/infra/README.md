# infra · la nube de la estación con Terraform

Crea con Terraform todo lo que la PoC necesita en AWS, más la identidad de las cinco bombas y la EC2 que las hospeda. Reemplaza a `cloud/setup.sh`, que sigue ahí como camino sin Terraform; las dos versiones usan los mismos nombres, y `tests/test_infra_terraform.py` verifica que no se separen.

El estado vive en S3 y lo comparten tu laptop y GitHub Actions. Lo normal es aplicar desde Actions (ver «Con GitHub Actions»); desde la laptop funciona igual porque es el mismo estado.

| Archivo | Qué crea |
|---|---|
| `main.tf` | Bucket de artefactos (privado, cifrado) y el parámetro `/estacion/last_good_version` |
| `iot.tf` | Thing groups `EstacionAnillo0` y `EstacionAnillo1`, rol de token exchange y su alias, política de IoT de las bombas y, con `gestionar_identidad = true`, los cinco things con su certificado (guardado en Parameter Store como SecureString) |
| `observabilidad.tf` | Grupo de logs `/estacion/eventos`, regla de IoT `estacion_eventos` con `arrived_ts`, los siete filtros de métrica (namespace `Estacion`), el dashboard `estacion`, la Lambda `estacion-rollback` y la alarma `estacion-fallas-no-oidas` que la invoca |
| `host.tf` | La EC2 Linux de las bombas: Amazon Linux 2023 con Docker, sin puertos abiertos (se entra con Session Manager), IMDSv2 con un solo salto para que los contenedores no puedan usar el rol de la EC2 |
| `backend.tf` | El estado en S3, cifrado y con candado (`use_lockfile`). El bucket y la región llegan por `-backend-config` |
| `github/` | Se aplica una vez desde tu laptop: el bucket del estado, el proveedor OIDC de GitHub y los roles `github-estacion-plan` (solo lectura) y `github-estacion-apply` (todo menos IAM; en IAM, solo los roles de la PoC) |

## Con GitHub Actions

Una sola vez, desde `poc-devopsdays/`, con un usuario administrador de la cuenta de pruebas y `gh` con sesión:

```bash
terraform -chdir=infra/github init
terraform -chdir=infra/github apply -var repo=<dueño>/mlops-a-ciegas
./infra/github/conectar-repo.sh       # variables del repo, environment aws-poc y infra/backend.hcl
```

Desde ahí, `.github/workflows/infra.yml` hace esto:

| Cuándo | Qué hace |
|---|---|
| Un PR que toca `infra/`, la Lambda o el dashboard | `plan` con el rol de solo lectura; el plan queda en el PR y en el resumen del job |
| Un push a `main` | Solo `plan`: muestra qué cambiaría |
| *Run workflow* a mano (Actions → infra) | `plan`, `apply` o `destroy`. El destroy borra antes los core devices y vacía el bucket de artefactos |

El `apply` nunca corre solo: lo lanzas tú, y solo desde `main` (el environment `aws-poc` lo exige). En un repo privado del plan gratis de GitHub, el environment no puede pedir aprobación; por eso el apply es manual.

`UMBRAL_ALARMA`, como variable del repo, cambia `umbral_alarma` sin tocar el código. El plan nunca se sube como artefacto: lleva el estado, y el estado lleva las llaves de las bombas.

`.github/workflows/pruebas.yml` corre `fmt`, `validate` y todas las pruebas de `tests/` en cada PR, sin tocar AWS.

## Uso desde tu laptop

```bash
cd poc-devopsdays/infra
terraform init -backend-config=backend.hcl   # backend.hcl lo escribe github/conectar-repo.sh
terraform plan                               # o: terraform apply -var umbral_alarma=6
terraform output siguiente                   # los pasos que siguen, con el id de la EC2
```

Después, desde la carpeta `poc-devopsdays/`:

1. `./infra/subir-al-host.sh` sube el código, `build/` y `data/estacion/` al bucket.
2. Entra a la EC2 con `terraform -chdir=infra output -raw entrar_al_host` (necesitas el [plugin de Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)).
3. En la EC2: `sudo su - ec2-user`, `traer-poc`, `cd ~/poc-devopsdays`, `./fleet/build.sh` y `IDENTIDAD=terraform ./fleet/up.sh` (la variable ya viene puesta en la sesión).
4. La demo sigue igual: `./demo/publish.sh 1.0.0`, `./demo/deploy.sh 1.0.0 todas`, `./demo/watch.sh`.

## Variables que vas a querer tocar

| Variable | Por defecto | Para qué |
|---|---|---|
| `region` | `us-east-1` | Toda la PoC |
| `umbral_alarma` | `8` | Fallas no oídas por minuto que disparan la vuelta; se ajusta en el ensayo |
| `tipo_instancia` | `t3.large` | Cada bomba es una JVM más el modelo: mide la memoria con las cinco arriba |
| `gestionar_identidad` | `true` | `false` deja que el instalador de Greengrass registre las bombas, como sin Terraform |
| `crear_host` | `true` | `false` si ya tienes un host Linux con Docker |
| `subred_id` | VPC por defecto | Si tu cuenta no tiene VPC por defecto, pasa una subred pública |
| `cidr_ssh`, `par_de_llaves` | sin SSH | Solo si prefieres SSH a Session Manager |
| `forzar_borrado_bucket` | `false` | `true` para que `destroy` borre el bucket con artefactos |

## Lo que tienes que saber

- **El estado guarda las llaves privadas de las bombas.** Vive en `s3://estacion-tfstate-<cuenta>-<región>/poc-devopsdays/infra.tfstate`: privado, cifrado, versionado y solo por TLS. Lo lee quien tenga permisos de S3 en la cuenta: hoy, tu usuario y los dos roles de GitHub. Si eso no te sirve, usa `gestionar_identidad = false`.
- **Un solo camino para aplicar a la vez.** Actions y tu laptop comparten el estado y el candado; si los dos intentan `apply` al tiempo, el segundo espera o falla con «state locked». Si pasas variables distintas en la laptop (`-var umbral_alarma=6`), el próximo apply de Actions las vuelve a su valor: deja los ajustes en las variables del repo.
- **Si ya corriste `cloud/setup.sh` o el instalador de Greengrass en esta cuenta,** el rol `GreengrassV2TokenExchangeRole`, su alias, las políticas y los thing groups ya existen y `apply` falla con «already exists». Bórralos con `./cloud/teardown.sh`, o impórtalos (`terraform import 'aws_iam_role.tes' GreengrassV2TokenExchangeRole`, y así con cada uno).
- **Para borrar todo:** `./fleet/down.sh` en la EC2, luego `./infra/limpiar-core-devices.sh` (los core devices los crea Greengrass, no Terraform) y `terraform -chdir=infra destroy`.
- **Lo que no maneja Terraform:** las versiones del componente y los despliegues. Son la demo: los crean `publish.sh`, `deploy.sh` y la Lambda.

## Qué verifiqué y qué no

- La sintaxis de los `.tf` (con un parser de HCL) y que los nombres, la regla, los siete patrones de los filtros, la alarma y la política de las bombas son los mismos que en `cloud/setup.sh`.
- `fleet/up.sh` y el entrypoint con `IDENTIDAD=terraform`, contra un `aws` y un `docker` falsos: bajan la identidad, la montan solo en la instalación, el nucleus se instala con `--init-config` y ninguna credencial de AWS entra al contenedor.
- `terraform init` y `terraform validate` pasan en `infra/` y en `infra/github/` (Terraform 1.12.2, proveedor de AWS 5.100.0). El lock tiene hashes para Linux y macOS.
- **No corrí `plan` ni `apply` contra AWS.** El primer `plan` de Actions es la prueba de los permisos de los roles de GitHub.
- **No probado contra AWS real.** El riesgo más alto es la instalación del nucleus con la identidad de afuera (`--init-config`): si falla, `docker logs bomba-01` y `fleet/logs/bomba-01/greengrass.log` dicen por qué.
