# Notas de apoyo · MLOps a ciegas

Lo que no se dice en voz alta pero conviene saber: datos de respaldo por lámina, detalles técnicos para las preguntas y las fuentes. El guion (`GUION-devopsdays.md`) tiene solo lo que dices; el estudio, en `talk/private/ESTUDIO.md` (no se sube al repo).

## Por lámina

- **2 · Gancho.** La caída de AWS fue el 20 de octubre de 2025, en us-east-1, desde la madrugada (hora del Este de EE. UU.). Las camas Pod de Eight Sleep (unos US$2.000) dependían de la nube para la temperatura y la inclinación; quedaron en su último estado, algunas sobrecalentadas y otras inclinadas. La cama sí usa IA sobre quien duerme: clasifica la etapa del sueño con sus sensores y ajusta la temperatura («Autopilot»), y detecta ronquidos para levantar la cabecera. Dónde corre esa inferencia no está publicado, pero en la caída todo quedó congelado: el ciclo de control dependía de la nube. En menos de 24 horas sacaron un «outage mode»: control manual por Bluetooth desde la app (encender, apagar, temperatura, posición), sin la inteligencia. Por eso el guion dice «control manual, sin la inteligencia» y no que movieron la IA al dispositivo. No hace falta nombrar la marca en voz alta. La captura de la noticia es de la prensa en español; la imagen del producto es de Eight Sleep. El meme «The entire internet / AWS us-east-1» está basado en xkcd 2347 («Dependency»), licencia CC BY-NC 2.5; el crédito va bajo la imagen.
- **4 y 31 · Audios.** El control los reproduce: en la 4, el clic 1 suena la bomba A y el clic 2 la B; en la 31, el clic 1 suena la B. Cada audio dura 10 s; un clic mientras suena lo detiene sin cambiar de lámina. Los botones «Escuchar» también funcionan con el mouse. La tecla B (o el botón de pantalla negra del control) pone la pantalla en negro. Si los botones dicen «audio pendiente», faltan `talk/assets/audio/pump-a.wav` y `pump-b.wav`. La atribución de MIMII DUE va al pie.
- **5 · Gartner.** 15,6 % (2024), 31 % (2025), 54,7 % (2026, proyección), 28 de agosto de 2025. La cifra es solo de PC; lo demás va sin números. Si ya salió la cifra real de 2026, úsala.
- **6 · Cuenta del audio.** 16 000 muestras/s × 2 bytes ≈ 115 MB por hora. Face ID: los datos no salen del equipo ni van a iCloud, los protege el Secure Enclave, y se adapta a cambios de apariencia (Apple, «About Face ID advanced technology»).
- **11 · Por qué AUC.** Con la otra velocidad todos los scores suben, y la detección puede subir junto con las falsas alarmas. La AUC mide si el modelo separa una bomba sana de una que falla, sin depender del umbral.
- **14 · Seguridad.** Secure boot en x86 es UEFI Secure Boot; en ARM depende del fabricante (HAB en NXP, por ejemplo). Greengrass guarda la llave y el certificado en un HSM o TPM con el componente PKCS#11. Firma del modelo: OpenSSF Model Signing, sobre Sigstore. La PoC corre en contenedores y no tiene nada de esto físico.
- **18 · Fábrica.** En la PoC la fábrica es `model/train.py` en el portátil, no SageMaker AI.
- **19 · Optimizar.** Portátil (M3 Pro): 2,6 → 2,0 ms. Pérdida de AUC del INT8: −0,001. Herramientas: LiteRT y Qualcomm QNN para NPU, TensorRT para GPU de NVIDIA, ONNX Runtime y OpenVINO para CPU.
- **20 · Digest.** La receta no trae el digest: Greengrass lo calcula al crear la versión y lo verifica en el equipo antes de instalar.
- **21 · Rings.** `failureHandlingPolicy = ROLLBACK` por defecto; `abortConfig` cancela si fallan muchos; `jobExecutionsRolloutConfig` hace las waves.
- **22 · Sin red.** La cola `mqtt.spooler` es de 2,5 MB en memoria por defecto; para horas sin red, DiskSpooler. Nucleus lite: 5 MB de disco, menos de 15 MB de RAM. Una planta grande: Outposts con EKS local.
- **23 · Señales.** Los umbrales del PSI (0,1 y 0,25) son costumbre, no estadística (A6). El filtro `MissedFaults` usa el campo `truth`, que solo existe en la PoC.
- **24 · Versiones.** Detalle de un equipo: `aws greengrassv2 list-installed-components --core-device-thing-name pump-01`.
- **26 · PoC.** Las cinco bombas salen de tres secciones de MIMII DUE (la 1 y la 4 comparten sección, la 2 y la 5 también, con clips distintos). Cada nucleus es una JVM: unos 220 MB por bomba.

## El ensayo del 18 de octubre (lo que muestran los actos)

| Momento | Hora (Bogotá) | Dato |
|---|---|---|
| Acto 1 · falla en la bomba 3 | 19:58:36 | ALERT en ese mismo clip, score 0,42 contra 0,34 |
| Acto 2 · sin red | 19:59:26 → 20:00:11 | 45 s sin red; 14 eventos llegaron tarde, de 11 a 50 s; ninguno se perdió |
| Acto 2 · deriva en la bomba 5 | 20:01 | la entrada sube de ~0,8 a 1,8 sin un solo error |
| Acto 3 · v2 al ring 0 | 20:13:06 | primer evento con v2.0.0 a los 17 s |
| Acto 3 · falla en la bomba 1 | 20:13:54 | «missed fault» desde el primer clip |
| Acto 3 · alarma | 20:15:14 | OK → ALARM (12 fallas no oídas en un minuto; umbral 8) |
| Acto 3 · Lambda | 20:15:16 | `{"rolled_back_to": "1.0.0"}` |
| Acto 3 · v1 de vuelta | 20:15:22 | primera ALERT con v1.0.0: 88 s desde la falla |

En todo el set de prueba, con fallas que no vio al entrenar: la v1 detecta el 21 % de las fallas y la v2 el 16 %; la v1 alerta en el 13 % de los clips y la v2 en el 10 %. Los clips de la flota se eligieron para que el ensayo sea repetible.

La infraestructura está abajo desde el 18 de octubre (destroy; componentes y despliegues borrados; queda el bucket del estado de Terraform). Para volver a correr la PoC: `poc-devopsdays/README.md`.

## Fuentes

- La caída de AWS y las camas Eight Sleep: https://www.pcworld.com/article/2948826/these-smart-beds-began-roasting-their-owners-during-aws-outage.html · https://www.mactrast.com/2025/10/aws-outage-caused-2000-smart-beds-to-overheat-and-get-stuck-in-the-upright-position/
- Gartner, 28 ago 2025: PC con IA 15,6 % (2024), 31 % (2025), 54,7 % (2026, proyección).
- MIMII DUE: Tanabe et al., Hitachi (2021), arXiv:2105.02702, doi:10.5281/zenodo.4740355. Bombas, `dev_data_pump`, CC BY-NC-SA 4.0.
- Cuentas: 16 000 muestras/s × 2 B = 32 000 B/s ≈ 115 MB por hora ≈ 2,76 GB al día por bomba; × 1 000 = 2,76 TB al día. Un evento cada 10 s = 8 640 por bomba al día; × 1 000 ≈ 8,64 M. Un resumen por minuto = 1 440 por bomba al día; × 1 000 ≈ 1,44 M.
- AUC: Fawcett, *An introduction to ROC analysis*, Pattern Recognition Letters (2006).
- Cifras medidas: `poc-devopsdays/build/metrics.json` y `device_bench.json`, vía `talk/tools/metrics.py` (AUC 0,69 → 0,57; falsas alarmas 6 % → 18 %; detección v1 21 %, v2 16 %; INT8 464 → 127 KB, 14,4 → 12,7 ms en el equipo, 98 % de decisiones iguales).
- SageMaker Neo y Edge Manager: https://docs.aws.amazon.com/sagemaker/latest/dg/edge-eol.html · https://docs.aws.amazon.com/sagemaker/latest/dg/neo-supported-devices-edge-frameworks.html · https://docs.aws.amazon.com/sagemaker/latest/dg/neo-supported-devices-edge-devices.html
- AWS Wavelength: https://aws.amazon.com/wavelength/locations/ · Local Zones: https://aws.amazon.com/about-aws/global-infrastructure/localzones/locations/
- Greengrass: nucleus y `mqtt.spooler` https://docs.aws.amazon.com/greengrass/v2/developerguide/greengrass-nucleus-component.html · cola en disco https://docs.aws.amazon.com/greengrass/v2/developerguide/disk-spooler-component.html · nucleus lite https://docs.aws.amazon.com/greengrass/v2/developerguide/greengrass-nucleus-lite-component.html · digest https://docs.aws.amazon.com/greengrass/v2/developerguide/component-recipe-reference.html · ROLLBACK por defecto https://docs.aws.amazon.com/greengrass/v2/APIReference/API_DeploymentPolicies.html · abortConfig y waves https://docs.aws.amazon.com/cli/latest/reference/greengrassv2/create-deployment.html · HSM/TPM https://docs.aws.amazon.com/greengrass/v2/developerguide/hardware-security.html · Docker https://docs.aws.amazon.com/greengrass/v2/developerguide/run-greengrass-docker.html
- EKS local en Outposts sin red: https://docs.aws.amazon.com/eks/latest/userguide/eks-outposts-network-disconnects.html
- OpenSSF Model Signing: https://github.com/sigstore/model-transparency
- Face ID: https://support.apple.com/102381
- Drift (A6): documentación de Evidently y NannyML; crítica a los umbrales del PSI: arXiv:2303.01227.
- Regulación (A7): Reglamento (UE) 2024/1689, arts. 12, 19 y 72, con las fechas del Reglamento (UE) 2026/1744; NIST AI 100-1; ISO/IEC 42001:2023. Si preguntan por Colombia: el AI Act aplica a lo que se pone en el mercado de la UE, se fabrique donde se fabrique.
