"""
The automatic rollback controller. Invoked directly by the CloudWatch alarm
`station-missed-faults` (faults that no pump heard).

It does not give the pump any order: it writes a new DESIRED STATE, a Greengrass
deployment with the last good version for ring 0 (the canary). The pump picks it
up when it can. Ring 1 never received the bad version, so it is left alone.

Environment variables:
  THING_GROUP_ARN   ARN of the canary thing group (StationRing0)
  COMPONENT         com.station.Listener
  LAST_GOOD_PARAM   /station/last_good_version   (Systems Manager parameter)
"""
import json, os, time
import boto3

gg = boto3.client("greengrassv2")
ssm = boto3.client("ssm")


def handler(event, context):
    alarm = event.get("alarmData", {})
    state = (alarm.get("state", {}) or {}).get("value")
    print(json.dumps({"alarm_state": state, "alarm": alarm.get("alarmName")}))
    if state != "ALARM":
        return {"skipped": True, "state": state}

    good = ssm.get_parameter(Name=os.environ["LAST_GOOD_PARAM"])["Parameter"]["Value"]
    comp = os.environ["COMPONENT"]

    resp = gg.create_deployment(
        targetArn=os.environ["THING_GROUP_ARN"],
        deploymentName=f"rollback-to-{good}-{int(time.time())}",
        components={comp: {"componentVersion": good,
                           "configurationUpdate": {"reset": [""]}}},   # also goes back to that version's threshold
        deploymentPolicies={"failureHandlingPolicy": "ROLLBACK",
                            "componentUpdatePolicy": {"timeoutInSeconds": 60, "action": "SKIP_NOTIFY_COMPONENTS"}},
    )
    out = {"rolled_back_to": good, "deploymentId": resp["deploymentId"], "t_ms": int(time.time() * 1000)}
    print(json.dumps(out))
    return out
