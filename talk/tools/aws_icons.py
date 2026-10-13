"""
Registry of the official AWS icons (Architecture Icons, package 07312026).

Reads the SVGs as they come in the package, strips <title> and id (so several
can be embedded in the same HTML without clashing) and returns them ready for
<symbol> or a nested <svg>. No recoloring, no geometry changes.

Usage:
    AWS_ICONS=/path/Icon-package_07312026 python3 build_arch.py
"""
import os, re

PKG = os.environ.get(
    "AWS_ICONS",
    os.path.expanduser("~/Downloads/Icon-package_07312026"),
)

A = "Architecture-Service-Icons_07312026"
R = "Resource-Icons_07312026"
G = "Architecture-Group-Icons_07312026"

# key -> relative path inside the package
ICONS = {
    # services (64)
    "greengrass": f"{A}/Arch_Internet-of-Things/64/Arch_AWS-IoT-Greengrass_64.svg",
    "iotcore":    f"{A}/Arch_Internet-of-Things/64/Arch_AWS-IoT-Core_64.svg",
    "s3":         f"{A}/Arch_Storage/64/Arch_Amazon-Simple-Storage-Service_64.svg",
    "sagemaker":  f"{A}/Arch_Artificial-Intelligence/64/Arch_Amazon-SageMaker-AI_64.svg",
    "bedrock":    f"{A}/Arch_Artificial-Intelligence/64/Arch_Amazon-Bedrock_64.svg",
    "cloudwatch": f"{A}/Arch_Management-Tools/64/Arch_Amazon-CloudWatch_64.svg",
    "lambda":     f"{A}/Arch_Compute/64/Arch_AWS-Lambda_64.svg",
    "ssm":        f"{A}/Arch_Management-Tools/64/Arch_AWS-Systems-Manager_64.svg",
    "iam":        f"{A}/Arch_Security-Identity/64/Arch_AWS-Identity-and-Access-Management_64.svg",
    "kms":        f"{A}/Arch_Security-Identity/64/Arch_AWS-Key-Management-Service_64.svg",
    "cloudtrail": f"{A}/Arch_Management-Tools/64/Arch_AWS-CloudTrail_64.svg",
    # resources (48)
    "gg_ml":       f"{R}/Res_IoT/Res_AWS-IoT-Greengrass_Component-Machine-Learning_48.svg",
    "gg_artifact": f"{R}/Res_IoT/Res_AWS-IoT-Greengrass_Artifact_48.svg",
    "gg_recipe":   f"{R}/Res_IoT/Res_AWS-IoT-Greengrass_Recipe_48.svg",
    "gg_nucleus":  f"{R}/Res_IoT/Res_AWS-IoT-Greengrass_Component-Nucleus_48.svg",
    "gg_ipc":      f"{R}/Res_IoT/Res_AWS-IoT-Greengrass_Interprocess-Communication_48.svg",
    "iot_mqtt":    f"{R}/Res_IoT/Res_AWS-IoT_MQTT_Protocol_48.svg",
    "iot_rule":    f"{R}/Res_IoT/Res_AWS-IoT-Rule_48.svg",
    "iot_topic":   f"{R}/Res_IoT/Res_AWS-IoT_Topic_48.svg",
    "iot_cert":    f"{R}/Res_IoT/Res_AWS-IoT_Certificate_48.svg",
    "iot_ipc":     f"{R}/Res_IoT/Res_AWS-IoT_Thing_Industrial-PC_48.svg",
    "iot_sensor":  f"{R}/Res_IoT/Res_AWS-IoT_Thing_Temperature-Vibration-Sensor_48.svg",
    "cw_logs":     f"{R}/Res_Management-Governance/Res_Amazon-CloudWatch_Logs_48.svg",
    "cw_alarm":    f"{R}/Res_Management-Governance/Res_Amazon-CloudWatch_Alarm_48.svg",
    "ssm_param":   f"{R}/Res_Management-Governance/Res_AWS-Systems-Manager_Parameter-Store_48.svg",
    "s3_bucket":   f"{R}/Res_Storage/Res_Amazon-Simple-Storage-Service_Bucket-With-Objects_48.svg",
    "iam_role":    f"{R}/Res_Security-Identity/Res_AWS-Identity-Access-Management_Role_48.svg",
    # groups (32)
    "grp_cloud":   f"{G}/AWS-Cloud_32.svg",
    "grp_dc":      f"{G}/Corporate-data-center_32.svg",
    "grp_gg":      f"{G}/AWS-IoT-Greengrass-Deployment_32.svg",
}

_ROOT = re.compile(r"<svg\b[^>]*>", re.S)


def load(key):
    """Returns the icon's (viewBox, inner content)."""
    path = os.path.join(PKG, ICONS[key])
    s = open(path, encoding="utf-8").read()
    s = re.sub(r"<\?xml[^>]*\?>", "", s)
    root = _ROOT.search(s)
    vb = re.search(r'viewBox="([^"]+)"', root.group(0)).group(1)
    inner = s[root.end(): s.rfind("</svg>")]
    inner = re.sub(r"<title>.*?</title>", "", inner, flags=re.S)
    inner = re.sub(r'\s(id)="[^"]*"', "", inner)
    inner = re.sub(r"\s+", " ", inner).strip()
    return vb, inner


def symbol(key):
    vb, inner = load(key)
    return f'<symbol id="i-{key}" viewBox="{vb}">{inner}</symbol>'


def nested(key, x, y, size, extra=""):
    """Nested <svg>: works the same in browsers and in cairosvg."""
    vb, inner = load(key)
    return (f'<svg x="{x}" y="{y}" width="{size}" height="{size}" '
            f'viewBox="{vb}" {extra}>{inner}</svg>')


def colors(key):
    _, inner = load(key)
    return sorted(set(c.upper() for c in re.findall(r"#[0-9a-fA-F]{6}", inner)))


if __name__ == "__main__":
    for k in ICONS:
        print(f"{k:12s} {', '.join(colors(k)):24s} {ICONS[k].split('/')[-1]}")
