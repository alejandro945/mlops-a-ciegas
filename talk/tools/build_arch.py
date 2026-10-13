"""
The talk's architecture, in three versions with the SAME geometry:

  gen  · slide 15 · the generic flow (empty slots)                 → {{ARCH_GENERIC}}
  ref  · slide 16 · the slots fill with the official icons         → {{FIG:arq_ref}}
  poc  · slide 27 · the PoC: one EC2 with five pumps in two rings  → {{FIG:arq_poc}}

Two outputs:
  - preview (full slide with title and footer):     build(mode)
  - layer for the deck (no background/title/footer): build(mode, deck=True)

In the deck every element carries data-p (which piece it belongs to: o = optimize,
1..4, s = slow loop, t = cross-cutting) so the engine lights it up or dims it
per step (same data-prog as the `flujo` slide), and the elements that change
between versions sit inside <g data-node>.

White background, two colors (ink + signal). AWS icons in their official colors.
Labels are slide text and stay in Spanish; AWS resource names match the PoC.

Usage:
    AWS_ICONS=~/Downloads/Icon-package_07312026 python3 build_arch.py [out/]
"""
import math, os, sys
import aws_icons
from aws_icons import nested as _nested

INK = "#071329"   # navy from the DevOpsDays Bogotá template
ACC = "#6D28D9"   # purple from the template
FONT = "Calibri, CarlitoX, Carlito, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "'Courier New', ui-monospace, Menlo, Consolas, monospace"

# official icons not in aws_icons.ICONS (added in memory)
for _k, _v in {
    "grp_ec2":        "Architecture-Group-Icons_07312026/EC2-instance-contents_32.svg",
    "sm_model":       "Resource-Icons_07312026/Res_Artificial-Intelligence/Res_Amazon-SageMaker-AI_Model_48.svg",
    "iot_sensor_gen": "Resource-Icons_07312026/Res_IoT/Res_AWS-IoT_Sensor_48.svg",
}.items():
    aws_icons.ICONS.setdefault(_k, _v)


_WARNED = set()


def nested(key, x, y, size, extra=""):
    """Official icon; without the package, a dashed slot and a warning (does not fail)."""
    try:
        return _nested(key, x, y, size, extra)
    except Exception as e:                               # noqa: BLE001
        if key not in _WARNED:
            _WARNED.add(key)
            print(f"  (warning) icon {key} not available: {e.__class__.__name__}; set AWS_ICONS", file=sys.stderr)
        return (f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="8" fill="#FFFFFF" stroke="{INK}" '
                f'stroke-width="2" stroke-dasharray="4 4"/>')


out = []
def add(s): out.append(s)

def text(x, y, s, size=15, color=INK, weight=400, anchor="start", op=1, ls=0, family=FONT):
    add(f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
        f'font-weight="{weight}" fill="{color}" fill-opacity="{op}" '
        f'text-anchor="{anchor}" letter-spacing="{ls}">{s}</text>')

def box(x, y, w, h, dashed=False, op=1.0, sw=1.5, rx=0, color=INK, fill="none"):
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
        f'stroke="{color}" stroke-opacity="{op}" stroke-width="{sw}"{dash}/>')

def delay(cx):
    return f' style="--d:{max(0, (cx - 96) / 1408 * .6):.2f}s"'

def group(x, y, w, h, icon, label, dashed=False, op=1.0, right=False, gen=False, key=None):
    """AWS-style group: border, icon in the top-left corner, label."""
    box(x, y, w, h, dashed=dashed, op=op)
    if icon:
        add(f'<g data-node="hdr-{key}"{delay(x)}>')
        if gen:
            add(f'<rect x="{x}" y="{y}" width="28" height="28" fill="{INK}"/>')
        else:
            add(nested(icon, x, y, 28))
        text(x + 36, y + 20, label, 17, INK, 700)
        add("</g>")
    elif right:
        text(x + w - 14, y + 24, label, 14, INK, 700, "end", op=.62, ls=1.6)
    else:
        text(x + 14, y + 24, label, 14, INK, 700, op=.62, ls=1.6)

def slot(cx, cy, size):
    """Empty slot of the generic version: where the icon goes later."""
    s = size
    add(f'<rect x="{cx - s/2}" y="{cy - s/2}" width="{s}" height="{s}" rx="10" '
        f'fill="#FFFFFF" stroke="{INK}" stroke-width="2"/>')
    add(f'<circle cx="{cx}" cy="{cy}" r="5" fill="{INK}"/>')

DETAIL = False   # True: second line with the technical detail under each node

def node(key, cx, cy, size, l1, l2="", p="", gen=False, icon=None):
    add(f'<g data-node="{key}"{delay(cx)}><g data-p="{p}">')
    if gen:
        slot(cx, cy, size)
    else:
        add(nested(icon or key, cx - size / 2, cy - size / 2, size))
    text(cx, cy + size / 2 + 26, l1, 20, INK, 700, "middle")
    if l2 and DETAIL:
        text(cx, cy + size / 2 + 46, l2, 15, INK, 400, "middle", op=.66)
    add("</g></g>")

def arrow(pts, color=INK, dashed=False, sw=2.2, head=9, p=""):
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    dash = ' stroke-dasharray="7 6"' if dashed else ""
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    a = math.atan2(y2 - y1, x2 - x1)
    p1 = (x2 - head * math.cos(a - .42), y2 - head * math.sin(a - .42))
    p2 = (x2 - head * math.cos(a + .42), y2 - head * math.sin(a + .42))
    add(f'<g data-p="{p}"><path class="flow" d="{d}" fill="none" stroke="{color}" '
        f'stroke-width="{sw}" stroke-linejoin="round"{dash}/>'
        f'<polygon points="{x2},{y2} {p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}" fill="{color}"/></g>')

SHOW = {"o": "1", "1": "2", "2": "3", "3": "4", "4": "5"}   # visible number of each piece


def badge(cx, cy, n, color=INK, p=None):
    add(f'<g data-p="{p or n}"><circle cx="{cx}" cy="{cy}" r="14" fill="{color}"/>')
    text(cx, cy + 6, SHOW.get(str(n), str(n)), 16, "#FFFFFF", 700, "middle")
    add("</g>")


# ── nodes: same position in the three versions ──────────────────────
#  key           cx    cy   size pieces   AWS (l1, l2)                                 generic (l1, l2)           AWS icon
NODES = [
    ("gg_ml",       200,  330, 56, "1 3",   ("Inferencia", "ONNX Runtime"),              ("Runtime", "ejecuta el modelo"), None),
    ("gg_artifact", 372,  330, 56, "1 2",   ("model.onnx", "digest verificado"),         ("Artefacto", "versión + hash"), None),
    ("gg_ipc",      200,  500, 56, "3",     ("IPC", "publica el evento"),                ("Emisor", "un evento por decisión"), None),
    ("gg_nucleus",  372,  500, 56, "2 3",   ("Nucleus", "cola MQTT QoS 1"),              ("Agente", "cola local si no hay red"), None),
    ("iot_sensor",  200,  708, 52, "3",     ("Micrófono", "el audio de la bomba"),       ("Datos", "entran al modelo"), "iot_sensor_gen"),
    ("iotcore",     690,  356, 64, "2 3",   ("IoT Core", "MQTT · mTLS X.509"),           ("Broker", "identidad por equipo"), None),
    ("greengrass",  900,  356, 64, "1 2 4", ("IoT Greengrass", "componentes · deployments"),
                                                                                         ("Orquestador", "desired state"), None),
    ("s3",          1110, 356, 64, "1",     ("S3", "artefactos versionados"),            ("Registro", "artefactos firmados"), None),
    ("optimize",    1262, 356, 64, "o",     ("Optimizar", "un artefacto por chip"),      ("Optimizar", "un artefacto por chip"), "sm_model"),
    ("sagemaker",   1412, 356, 64, "o s",   ("SageMaker AI", "entrena y evalúa"),        ("Entrenar", "entrena y evalúa"), None),
    ("iot_rule",    690,  612, 56, "3",     ("Regla de IoT", "station/events"),        ("Ingesta", "enruta eventos"), None),
    ("cw_logs",     862,  612, 56, "3 4 s", ("CloudWatch Logs", "filtros de métrica"),   ("Métricas", "errores por minuto"), None),
    ("cw_alarm",    1034, 612, 56, "4",     ("Alarma", "fallas no oídas"),               ("Umbral", "¿pasó el límite?"), None),
    ("lambda",      1212, 612, 64, "4",     ("Lambda", "rollback"),                      ("Controlador", "decide volver"), None),
    ("ssm_param",   1392, 612, 56, "4",     ("Parameter Store", "última versión buena"), ("Memoria", "última versión buena"), None),
]
DEVICE = {"gg_ml", "gg_artifact", "gg_ipc", "gg_nucleus", "iot_sensor"}

TITLES = {
    "gen": ("GOBERNAR", "¿Qué hace falta ", "para gobernarlo?", "15"),
    "ref": ("EL PATRÓN", "¿Cómo se ve esto ", "en AWS?", "16"),
    "poc": ("EN VIVO", "¿Qué monté ", "para la demo?", "27"),
}


def _container(x, y, w, name):
    """A PoC container: real Greengrass inside, labelled with the pump name."""
    box(x, y, w, 48, rx=8, sw=1.6, fill="#FFFFFF")
    add(nested("greengrass", x + 9, y + 9, 30))
    text(x + 48, y + 31, name, 20, INK, 700, family=MONO)


def _poc_site():
    """The simulated station: one EC2 with Docker, five pumps in two rings and the real audio."""
    # ring 0
    add(f'<g data-node="ring0"{delay(120)}><g data-p="1 2 3">')
    box(116, 246, 340, 112, dashed=True, op=.55)
    text(130, 272, "RING 0 · StationRing0", 15, ACC, 700, ls=.6)
    _container(196, 290, 180, "pump-01")
    add("</g></g>")
    # ring 1
    add(f'<g data-node="ring1"{delay(120)}><g data-p="1 2 3">')
    box(116, 378, 340, 196, dashed=True, op=.55)
    text(130, 404, "RING 1 · StationRing1", 15, INK, 700, op=.75, ls=.6)
    for k, n in enumerate(["pump-02", "pump-03", "pump-04", "pump-05"]):
        _container(130 + (k % 2) * 166, 422 + (k // 2) * 66, 154, n)
    add("</g></g>")
    # the real audio, mounted read-only
    add(f'<g data-node="audio"{delay(120)}><g data-p="3">')
    cx, cy = 200, 690
    for k in range(13):
        h = [10, 22, 14, 30, 18, 34, 26, 16, 30, 12, 24, 16, 8][k]
        add(f'<rect x="{cx - 39 + k * 6}" y="{cy - h / 2}" width="3.6" height="{h}" rx="1.5" fill="{INK}"/>')
    text(cx, cy + 50, "Audio real", 20, INK, 700, "middle")
    text(cx + 70, cy + 6, "MIMII DUE", 16, INK, 400, op=.75, family=MONO)
    add("</g></g>")
    arrow([(200, 662), (200, 580)], INK, sw=1.6, head=7, p="3")


def build(mode="ref", deck=False, slow=True):
    out.clear()
    gen, poc = mode == "gen", mode == "poc"
    add('<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900"'
        + (' class="arq"' if deck else "") + ">")
    if not deck:
        add('<rect width="1600" height="900" fill="#FFFFFF"/>')
        kicker, t1, t2, _ = TITLES[mode]
        text(96, 84, kicker, 15, ACC, 700, ls=2.4)
        add(f'<text x="96" y="140" font-family="{FONT}" font-size="46" fill="{INK}" font-weight="300">'
            f'{t1}<tspan font-weight="700">{t2}</tspan></text>')

    # ── piece legend ─────────────────────────────────────────────
    leg = [("o", "optimizar por chip"), ("1", "artefacto verificable"), ("2", "desired state"),
           ("3", "evento de inferencia"), ("4", "gate")]
    for i, (n, t) in enumerate(leg):
        lx, ly = 892 + (i % 3) * 212, 100 + (i // 3) * 36
        add(f'<g data-p="{n}">')
        add(f'<circle cx="{lx}" cy="{ly - 6}" r="14" fill="{ACC if n == "4" else INK}"/>')
        text(lx, ly, SHOW[n], 16, "#FFFFFF", 700, "middle")
        text(lx + 24, ly, t, 18, INK, 400)
        add("</g>")

    # ── groups ───────────────────────────────────────────────────
    if poc:
        group(96, 196, 380, 614, "grp_ec2", "EC2 · la estación simulada", key="site")
    else:
        group(96, 196, 380, 614, "grp_dc", "Sitio" if gen else "Estación", gen=gen, key="site")
        group(116, 246, 340, 392, "iot_ipc", "Equipo" if gen else "Equipo con Greengrass", gen=gen, key="dev")
    group(580, 196, 924, 614, "grp_cloud", "Nube o datacenter" if gen else "AWS Cloud", gen=gen, key="cloud")
    group(604, 244, 400, 236, None, "PLANO DE CONTROL", dashed=True, op=.45)
    group(1028, 244, 452, 236, None, "FÁBRICA DE MODELOS", dashed=True, op=.45)
    group(604, 520, 876, 214, None, "OBSERVACIÓN Y GATE", dashed=True, op=.45, right=True)

    # ── nodes ────────────────────────────────────────────────────
    for key, cx, cy, size, p, aws, gl, ic in NODES:
        if poc and key in DEVICE:
            continue
        if poc and key in ("sagemaker", "optimize"):
            continue
        l1, l2 = gl if gen else aws
        node(key, cx, cy, size, l1, l2, p, gen=gen, icon=ic)
    if poc:
        _poc_site()
        # in the PoC the factory is a script on the laptop, outside AWS: it trains and quantizes
        add(f'<g data-node="sagemaker"{delay(1300)}><g data-p="o s">')
        box(1236, 324, 210, 64, rx=8, sw=1.6)
        text(1341, 363, "model/train.py", 20, INK, 700, "middle", family=MONO)
        text(1341, 418, "Mi portátil", 20, INK, 700, "middle")
        add("</g></g>")

    # ── cross-cutting ────────────────────────────────────────────
    add(f'<g data-node="trans"{delay(620)}><g data-p="t">')
    text(620, 777, "TRANSVERSAL", 14, INK, 700, op=.62, ls=1.6)
    if not gen:
        tx = 750
        for key, lab, dim in [("iam_role", "IAM", False),
                              ("iot_cert", "X.509 por bomba" if poc else "X.509", False),
                              ("kms", "KMS", poc),
                              ("cloudtrail", "CloudTrail", poc)]:
            add('<g opacity=".16">' if dim else "<g>")
            add(nested(key, tx, 756, 28))
            text(tx + 36, 777, lab, 17, INK, 400, op=.85)
            add("</g>")
            tx += 36 + len(lab) * 8.4 + 44
    else:
        text(750, 777, "identidad · mínimo privilegio · cifrado · auditoría", 17, INK, 400, op=.85)
    add("</g></g>")

    # ── flows inside the device ──────────────────────────────────
    if not poc:
        arrow([(340, 330), (234, 330)], INK, sw=1.6, head=7, p="1")
        arrow([(200, 398), (200, 466)], INK, dashed=True, sw=1.6, head=7, p="3")
        arrow([(234, 500), (340, 500)], INK, dashed=True, sw=1.6, head=7, p="3")
        arrow([(200, 678), (200, 642)], INK, sw=1.6, head=7, p="3")

    # ── 0 · optimize and 1 · artifact: factory -> registry -> orchestrator ──────
    add(f'<g data-node="a-fab"{delay(1300)}>')
    if poc:
        arrow([(1236, 356), (1148, 356)], INK, p="1")
    else:
        arrow([(1374, 356), (1300, 356)], INK, p="o")
        badge(1337, 330, "o", p="o")
        arrow([(1224, 356), (1148, 356)], INK, p="1")
    add("</g>")
    arrow([(1072, 346), (940, 346)], INK, p="1")
    badge(970, 346, 1)
    # ── 2 · desired state: orchestrator -> broker -> device ──────
    arrow([(860, 346), (730, 346)], INK, p="2")
    arrow([(650, 340), (458, 340)], INK, p="2")
    badge(526, 340, 2)
    # ── 3 · event: agent -> broker -> ingest -> metrics ──────────
    if poc:
        arrow([(456, 470), (500, 470), (500, 378), (650, 378)], INK, dashed=True, p="3")
    else:
        arrow([(406, 500), (436, 500), (436, 378), (650, 378)], INK, dashed=True, p="3")
    badge(526, 378, 3)
    arrow([(690, 448), (690, 578)], INK, dashed=True, p="3")
    arrow([(724, 612), (828, 612)], INK, dashed=True, p="3")
    # ── 4 · gate (fast loop, minutes) ────────────────────────────
    arrow([(896, 612), (1000, 612)], ACC, sw=2.6, p="4")
    arrow([(1068, 612), (1174, 612)], ACC, sw=2.6, p="4")
    arrow([(1250, 612), (1358, 612)], ACC, sw=1.8, dashed=True, head=7, p="4")
    arrow([(1212, 578), (1212, 500), (1016, 500), (1016, 372), (940, 372)], ACC, sw=2.6, p="4")
    badge(1110, 500, 4, ACC)

    # ── the "before": how models get deployed today (only step 0 of the generic flow) ──
    if gen and slow and deck:
        arrow([(1100, 500), (462, 500)], INK, dashed=True, sw=2.2, p="b")
        add('<g data-p="b">')
        text(880, 568, "copiar el modelo… y cruzar los dedos", 30, INK, 300, "middle")
        add("</g>")

    # ── slow loop (days): generic and reference ──────────────────
    if slow and not poc:
        arrow([(1480, 690), (1492, 690), (1492, 300), (1412, 300), (1412, 318)], INK, dashed=True, sw=1.6, head=7, p="s")
        add('<g data-p="4">')
        add(f'<path d="M1030,168 L1058,168" stroke="{ACC}" stroke-width="2.6"/>')
        text(1066, 174, "loop rápido · minutos", 18, INK, 400)
        add("</g>")
        add('<g data-p="s">')
        add(f'<path d="M1272,168 L1300,168" stroke="{INK}" stroke-width="1.6" stroke-dasharray="7 6"/>')
        text(1308, 174, "loop lento · días", 18, INK, 400)
        add("</g>")

    if poc:
        # sticker top right, under the legend
        add(f'<g data-node="sticker" style="--d:.5s">')
        add(f'<rect x="1150" y="148" width="330" height="38" rx="5" fill="{ACC}"/>')
        text(1315, 174, "5 bombas · 7 servicios", 21, "#FFFFFF", 700, "middle")
        add("</g>")

    if not deck:
        text(96, 866, "DevOpsDays Bogotá 2026 · MLOps a ciegas", 13, INK, 400, op=.45)
        text(1504, 866, TITLES[mode][3], 13, INK, 700, "end", op=.45)
    add("</svg>")
    return "\n".join(out)


def deck_layer(mode, cls="lay-a"):
    """The layer ready for <div class="stack">: class "arq lay-a" (the engine looks for svg.lay-a)."""
    return build(mode, deck=True).replace('class="arq"', f'class="arq {cls}"', 1)


if __name__ == "__main__":
    dst = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(dst, exist_ok=True)
    for mode, name in [("gen", "arq-generica.svg"),
                       ("ref", "arq-aws-referencia.svg"),
                       ("poc", "arq-aws-poc.svg")]:
        p = os.path.join(dst, name)
        open(p, "w", encoding="utf-8").write(build(mode))
        print("✔", p)
