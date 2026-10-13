# Continuar «MLOps a ciegas» en otro equipo

Charla de Alejandro Varela en DevOpsDays Bogotá 2026 (23 de octubre, Compensar Av. 68; 30 minutos en el CFP). Este archivo es lo que necesita una sesión nueva de Claude, o tú, para seguir sin perder nada. Estado al 12 de octubre de 2026.

## Cómo seguir en el otro equipo

1. Descomprime `mlops-a-ciegas-traspaso.zip` en una carpeta, por ejemplo `~/mlops-a-ciegas/`.
2. En Claude (Cowork), abre una conversación nueva y selecciona esa carpeta.
3. Pega esto como primer mensaje:

   > Lee `talk/HANDOFF-continuar.md` y `talk/PLAN-bombas.md`. Son el estado y el contrato de mi charla. Sigue con los pendientes en el orden del handoff; antes de cambiar algo, respeta las reglas del §«Reglas».

Una conversación no se puede mover de una cuenta a otra: la sesión nueva arranca de cero y este archivo le da el contexto.

**El spec** («SPEC · MLOps a ciegas, versión DevOps») es un doc de Claude que vive en la cuenta donde se creó. Si lo quieres en la otra cuenta, ábrelo y descárgalo como Markdown o Word, o compártelo. No es indispensable: `PLAN-bombas.md` y este archivo traen todo lo que el spec decidió.

## Qué hay

| Carpeta o archivo | Qué es |
|---|---|
| `talk/devopsdays.html` | El deck, un solo archivo que funciona sin internet. Se genera desde `talk/tools/deck.src.html` con `build_deck.py` |
| `talk/MLOps-a-ciegas-DevOpsDays-Bogota-2026.pptx` | El mismo deck en la plantilla oficial (42 láminas: 34 + 8 anexos). Se genera con `talk/tools/pptx/render.sh` |
| `talk/GUION-devopsdays.md` | El guion, con la forma de las charlas de Freddy Vega. Sus notas se inyectan en el HTML y el PowerPoint |
| `talk/PLAN-bombas.md` | El contrato: láminas, ids, figuras, eventos, nombres de AWS, comandos de la demo |
| `talk/tools/` | Generadores: figuras (`build_iso.py`, `build_figs.py`, `build_arch.py`, `build_seq.py`), cifras (`metrics.py`), deck y PowerPoint |
| `poc-devopsdays/` | La demo: modelo (`model/`), componente (`component/`), flota simulada (`fleet/`), comandos (`demo/`), nube con bash (`cloud/`) y con Terraform (`infra/`), pruebas (`tests/`) |
| `CFP-*.md`, `DOSSIER-academico-charla.md` | La postulación y las fuentes académicas |

## La charla en una frase

Cómo llevar un modelo de la nube a una flota de equipos que no ves y mantenerlo gobernado: seis pasos de infraestructura (entrenar, optimizar, empaquetar, desplegar, correr sin red, monitorear) contados con un caso, una estación de bombeo rural, inventada para la charla, donde un modelo escucha las bombas y avisa cuando una empieza a sonar distinto.

## Decisiones tomadas

- **AWS sí, referencias a AWS no.** Los servicios de AWS se nombran y se dibujan con íconos oficiales. Ningún pie de lámina cita páginas, blogs ni documentación de AWS; esos datos se dicen en voz alta y su enlace va en el guion o en el README.
- **Primero el patrón genérico, después el mismo dibujo en AWS.**
- **Abre y cierra con dos audios** («¿Esta bomba está fallando?»); la respuesta (la B) llega en la demo.
- **Datos reales:** MIMII DUE de Hitachi, bombas, `dev_data_pump.zip`, licencia CC BY-NC-SA 4.0 (sirve para una charla comunitaria; para algo comercial, el MIMII original, CC BY-SA 4.0).
- **Modelo:** autoencoder (scikit-learn → ONNX) que aprende solo con sonido normal. v1.0.0 buena; v2.0.0 entrenada a propósito con audio de una bomba que ya fallaba («aprendió que fallar es normal»); INT8 para medir.
- **Lámina 11 usa AUC** («¿distingue una falla de una bomba sana?», con 0,5 = lanzar una moneda) y falsas alarmas, no «fallas detectadas»: con el cambio de velocidad todos los scores suben y la detección podría subir junto con las falsas alarmas. La frase «El modelo ya no distingue» hay que confirmarla con la medición real.
- **Demo sin hardware:** cinco bombas en contenedores con el nucleus de Greengrass real, en una EC2 Linux; todo lo de AWS es real y en el escenario se dice tal cual. Dos anillos: `EstacionAnillo0` (bomba-01, canario) y `EstacionAnillo1` (bomba-02 a 05).
- **Tres actos:** escuchar (`falla.sh bomba-03`), sin red (`red.sh off/on bomba-03`, más una línea de drift con `dominio.sh bomba-05 nuevo`), desplegar por anillos y volver (`deploy.sh 2.0.0 anillo-0` → la alarma → la Lambda devuelve la 1.0.0).
- **Infraestructura con Terraform** (`poc-devopsdays/infra/`): nube, identidad de las bombas en Parameter Store y la EC2. `cloud/setup.sh` queda como camino sin Terraform; una prueba verifica que ambos creen lo mismo.
- **Ninguna cifra inventada.** Las del modelo salen de `poc-devopsdays/build/metrics.json` vía `{{M:clave}}`; si la medición no es real y de bombas confirmadas, la lámina dice «por medir».

## Reglas

- Español neutro de Colombia con «tú», nunca voseo. Sin la palabra «plata». Frases cortas y habladas.
- Nunca inventar números ni fuentes; las suposiciones se marcan como tales.
- Sin `kubectl` en pantalla. Sin casos de cámaras ni de retail. Sin logo de EPAM.
- No recolorear ni deformar imágenes o logos de la plantilla.
- No descargar ni instalar código de terceros (repos, skills, baselines del dataset).

## Pendientes, en orden

1. **El zip de bombas.** `dev_data_pump.zip` (1,1 GB) de https://zenodo.org/records/4740355/files/dev_data_pump.zip?download=1, sin descomprimir, en `poc-devopsdays/data/`. Ojo: el `dev_data_fan.zip` que hay en `poc-devopsdays/demo/` es de ventiladores; el código ya se niega a usarlo como bombas. Se puede borrar.
2. **Entrenar y medir** (unos 90 s y 1 GB de RAM), desde `poc-devopsdays/`:
   ```bash
   python3 model/train.py --data data/dev_data_pump.zip
   python3 model/prepare_data.py --data data/dev_data_pump.zip --scores build/scores.csv
   python3 ../talk/tools/metrics.py v1.auc_source v1.auc_target v1.false_alarm_source v1.false_alarm_target
   ```
   Revisa que la historia aguante: la AUC de la v1 debe caer clara en el dominio nuevo y la v2 debe oír menos fallas. Si no, ajusta (`--contaminar`, umbral por sección) antes de regenerar. Con ventiladores, el modelo distinguía poco: es el riesgo principal.
3. **Regenerar deck y PowerPoint con las cifras y los audios**, desde la raíz:
   ```bash
   AWS_ICONS=<carpeta del paquete de íconos de AWS> bash talk/tools/pptx/render.sh
   ```
   El paquete de íconos (Icon-package_07312026) no va en el zip; bájalo de la página de íconos de arquitectura de AWS.
4. **Terraform:** `terraform -chdir=poc-devopsdays/infra init && terraform -chdir=poc-devopsdays/infra validate`. No se pudo correr en el entorno donde se escribió. Luego `apply` y seguir `terraform output siguiente`.
5. **Primer ensayo en la EC2:** `./fleet/build.sh`, `IDENTIDAD=terraform ./fleet/up.sh`, `./demo/publish.sh 1.0.0` y `2.0.0`, `./demo/deploy.sh 1.0.0 todas`, `./demo/watch.sh`. El riesgo más alto es la instalación del nucleus dentro del contenedor; `poc-devopsdays/README.md` tiene la tabla de problemas.
6. **Cronometrar el acto 3** (métrica, alarma, Lambda, despliegue) y ajustar `umbral_alarma`. Si pasa de 3 minutos, el guion ya trae el atajo de lanzar el despliegue durante el acto 2.
7. **Grabar el video de respaldo** de los tres actos.
8. **Lo tuyo:** foto cuadrada en `talk/assets/photo.jpg`, tu LinkedIn (`LINKEDIN=…`), la URL del repo para el QR (`REPO_URL=…`), la anécdota personal de la lámina 31, y confirmar con los organizadores que la laptop tiene salida de audio.

## Comandos útiles

```bash
# deck (desde la raíz)
AWS_ICONS=… python3 talk/tools/build_deck.py
AWS_ICONS=… bash talk/tools/pptx/render.sh                 # deck + PowerPoint
# pruebas de la PoC (sin AWS ni Docker)
python3 -m unittest discover -s poc-devopsdays/tests -p 'test_*.py'
# cifras disponibles
python3 talk/tools/metrics.py v1.auc_source int8.size_int8_kb
```

Requisitos de las herramientas del deck: Python 3 con python-pptx, lxml, cssselect, pillow, cairosvg, weasyprint; Node 18 o más; `pdftoppm` (poppler); ffmpeg para los audios del PowerPoint.
