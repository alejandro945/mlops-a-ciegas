"""
El controlador de la vuelta automática. Lo invoca directamente la alarma de
CloudWatch `estacion-fallas-no-oidas` (fallas que ninguna bomba oyó).

No le ordena nada a la bomba: escribe un nuevo ESTADO DESEADO, un despliegue de
Greengrass con la última versión buena para el anillo 0 (el canario). La bomba
lo busca cuando puede. El anillo 1 nunca recibió la versión mala, así que no se toca.

Variables de entorno:
  THING_GROUP_ARN   arn del thing group del canario (EstacionAnillo0)
  COMPONENT         com.estacion.Escucha
  LAST_GOOD_PARAM   /estacion/last_good_version   (parámetro de Systems Manager)
"""
import json, os, time
import boto3

gg = boto3.client("greengrassv2")
ssm = boto3.client("ssm")


def handler(event, context):
    alarma = event.get("alarmData", {})
    state = (alarma.get("state", {}) or {}).get("value")
    print(json.dumps({"alarm_state": state, "alarm": alarma.get("alarmName")}))
    if state != "ALARM":
        return {"skipped": True, "state": state}

    good = ssm.get_parameter(Name=os.environ["LAST_GOOD_PARAM"])["Parameter"]["Value"]
    comp = os.environ["COMPONENT"]

    resp = gg.create_deployment(
        targetArn=os.environ["THING_GROUP_ARN"],
        deploymentName=f"vuelta-a-{good}-{int(time.time())}",
        components={comp: {"componentVersion": good,
                           "configurationUpdate": {"reset": [""]}}},   # vuelve también al umbral de esa versión
        deploymentPolicies={"failureHandlingPolicy": "ROLLBACK",
                            "componentUpdatePolicy": {"timeoutInSeconds": 60, "action": "SKIP_NOTIFY_COMPONENTS"}},
    )
    out = {"rolled_back_to": good, "deploymentId": resp["deploymentId"], "t_ms": int(time.time() * 1000)}
    print(json.dumps(out))
    return out
