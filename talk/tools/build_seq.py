"""
Annex A2 · the automatic rollback, call by call (sequence diagram).

Same visual system as the architecture: white, ink + signal color, official AWS
icons. Lifelines on the left; on the right, aligned with each arrow, what
happens (19 px text, Spanish: slide text). The signal color marks only the gate
(alarm → Lambda → Parameter Store → deployment to ring 0).

Canvas 1600 × 900, content in x 96–1504 · y 230–712 (goes in <div class="fig">).
"""
import html, math
from build_arch import INK, ACC, FONT, MONO, nested

SLATE, MUTED, LINE = "#475569", "#5C7290", "#D5DEEA"

COLS = [  # (icon key or None, label)
    (None,         "Tú · CLI"),
    ("greengrass", "IoT Greengrass"),
    ("iot_ipc",    "pump-01"),
    ("iotcore",    "IoT Core"),
    ("cloudwatch", "CloudWatch"),
    ("lambda",     "Lambda"),
    ("ssm_param",  "Parameter Store"),
]
X = [140 + k * 134 for k in range(len(COLS))]

#        from to  what happens (slide text)                         color  dashed
MSGS = [
    (0, 1, "create-deployment 2.0.0 → StationRing0",             INK, False),
    (1, 2, "pump-01 trae su estado deseado: la v2",               INK, False),
    (2, 2, "baja de S3, verifica el digest e instala",            INK, False),
    (2, 1, "despliegue SUCCEEDED: la v2 corre sin errores",       INK, True),
    (2, 3, "la bomba suena con falla y la v2 no avisa",           INK, True),
    (3, 4, "regla → Logs → métrica MissedFaults",                 INK, True),
    (4, 5, "ALARM: station-missed-faults",                        ACC, False),
    (5, 6, "GetParameter /station/last_good_version",             ACC, False),
    (6, 5, "responde 1.0.0",                                      ACC, True),
    (5, 1, "create-deployment 1.0.0 → StationRing0",              ACC, False),
    (1, 2, "pump-01 vuelve a la v1",                              INK, False),
    (2, 3, "la falla se oye otra vez: ALERT",                     INK, True),
]
Y0, DY = 346, 32
TX = 1046                       # text column


def _t(x, y, s, size=18, color=INK, weight=400, anchor="middle", op=1, family=FONT):
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{color}" fill-opacity="{op}" text-anchor="{anchor}">{html.escape(s)}</text>')


def _arrow(x1, y1, x2, y2, color, dashed, sw=2.2):
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    a = math.atan2(y2 - y1, x2 - x1)
    h = 9
    p1 = (x2 - h * math.cos(a - .45), y2 - h * math.sin(a - .45))
    p2 = (x2 - h * math.cos(a + .45), y2 - h * math.sin(a + .45))
    return (f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{color}" stroke-width="{sw}" fill="none"{dash}/>'
            f'<polygon points="{x2},{y2} {p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}" fill="{color}"/>')


def build(static=False):
    o = ['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900" class="iso seq">']
    yN = Y0 + DY * (len(MSGS) - 1)
    # the gate stretch, as a background band
    g0 = next(i for i, m in enumerate(MSGS) if m[3] == ACC)
    g1 = max(i for i, m in enumerate(MSGS) if m[3] == ACC)
    o.append(f'<rect x="96" y="{Y0 + DY * g0 - 20}" width="1408" height="{DY * (g1 - g0) + 34}" rx="8" '
             f'fill="{ACC}" fill-opacity=".06"/>')
    # headers and lifelines
    for (key, lab), x in zip(COLS, X):
        if key:
            o.append(nested(key, x - 22, 232, 44))
        else:
            o.append(f'<rect x="{x - 22}" y="232" width="44" height="44" rx="4" fill="{INK}"/>')
            o.append(_t(x, 260, ">_", 18, "#FFFFFF", 700, family=MONO))
        o.append(_t(x, 302, lab, 18, INK, 700))
        o.append(f'<path d="M{x},316 L{x},{yN + 16}" stroke="{INK}" stroke-opacity=".25" stroke-width="1.5" '
                 f'stroke-dasharray="4 5"/>')
    o.append(_t(TX, 302, "QUÉ PASA", 18, MUTED, 700, "start", family=MONO).replace("<text ", '<text letter-spacing="2" ', 1))
    o.append(f'<path d="M{TX - 24},316 L{TX - 24},{yN + 16}" stroke="{LINE}" stroke-width="1.5"/>')
    # messages
    for k, (a, b, txt, col, dashed) in enumerate(MSGS):
        y = Y0 + DY * k
        if a == b:
            x = X[a]
            o.append(f'<path d="M{x + 4},{y - 9} L{x + 44},{y - 9} L{x + 44},{y + 9} L{x + 10},{y + 9}" '
                     f'stroke="{col}" stroke-width="2.2" fill="none"/>')
            o.append(f'<polygon points="{x + 3},{y + 9} {x + 12},{y + 4} {x + 12},{y + 14}" fill="{col}"/>')
        else:
            s = 1 if X[b] > X[a] else -1
            o.append(_arrow(X[a] + 5 * s, y, X[b] - 5 * s, y, col, dashed))
        o.append(_t(TX, y + 6, f"{k + 1:02d}", 18, col if col == ACC else MUTED, 700, "start", family=MONO))
        o.append(_t(TX + 40, y + 6, txt, 19, col, 700 if col == ACC else 400, "start"))
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    import sys
    open(sys.argv[1] if len(sys.argv) > 1 else "seq.svg", "w", encoding="utf-8").write(build())
