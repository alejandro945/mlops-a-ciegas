# MLOps a ciegas

Charla de Alejandro Varela en DevOpsDays Bogotá 2026 (23 de octubre, Compensar Av. 68).

Cómo llevar un modelo de la nube a equipos que no ves, y mantenerlo gobernado. El caso es una estación de bombeo rural, inventada para la charla: un modelo escucha las bombas y avisa cuando una empieza a sonar distinto. El audio no sale de la estación; sale un evento de unos cientos de bytes.

## Qué hay aquí

| Carpeta | Qué es |
|---|---|
| [`poc-devopsdays/`](poc-devopsdays/) | La demo completa: el modelo, el componente de IoT Greengrass, cinco bombas simuladas en Docker, los comandos de la demo y la nube con Terraform. Empieza por su [README](poc-devopsdays/README.md) |
| [`charla/`](charla/) | Las láminas (`devopsdays.html` abre sin internet), el guion con las notas y los generadores de figuras |
| [`.github/workflows/`](.github/workflows/) | Pruebas en cada PR, y `plan` / `apply` de la infraestructura con OIDC (sin llaves de AWS en el repo) |

## Probarlo

Las pruebas no necesitan AWS ni Docker:

```bash
cd poc-devopsdays
python3.12 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
```

Para montar la estación en tu cuenta de AWS sigue [`poc-devopsdays/README.md`](poc-devopsdays/README.md). Usa una cuenta de pruebas: la EC2 cobra por hora encendida.

## Los datos

Los sonidos son de **MIMII DUE** (Tanabe et al., Hitachi, 2021), bombas, licencia [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). No están en el repo: se bajan de [Zenodo](https://zenodo.org/records/4740355). La empresa, las veredas y el jefe son inventados.
