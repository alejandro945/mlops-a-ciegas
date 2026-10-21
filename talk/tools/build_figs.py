"""
Flat figures for the talk (same convention as build_iso.py: 1600x900 canvas,
usable area x 84–1516 · y 225–760, data-on="n" comes in at step n).
FIGS keys are the {{FIG:name}} names used in deck.src.html; visible labels are slide text (Spanish).

  optimizar      · step 2: one artifact per chip, memory rules, the pump FP32 → INT8 (metrics.fmt)
  anillos        · step 4: ring 0 (one station) → ring 1; thing groups, exponential, abortConfig, ROLLBACK, the rollback
  entrenar       · step 1: normal sound → SageMaker AI (autoencoder) → S3 → the build/1.0.0/ tree
  receta         · step 3: poc-devopsdays/component/recipe.template.yaml, read at build time, four annotations
  sinred         · step 5: the device (Greengrass) versus the site (Outposts with local EKS)
  monitoreo      · step 6: IoT Core → rule → Logs → filter → alarm → Lambda (reads poc-devopsdays/cloud/)
  onda_a/onda_b  · slide 2: the envelope of talk/assets/audio/pump-a|b.wav (640 × 160)
  espina         · divider 03: the six steps
  espina_1…6     · 1432 × 44 footer bar with step n highlighted
  arq_ref/arq_poc· the AWS architecture (build_arch.py), layer "arq lay-a"
  seq            · annex A2: the automatic rollback (build_seq.py)
  pasaporte, drift, medir · slides that left the storyline (kept in case an annex uses them)

Whatever is missing (audio, recipe, metrics, icons) breaks nothing: it is drawn as pending and reported on stderr.
"""
import html, math, os as _os, sys
from iso import Iso, mix, NAVY, SLATE, MUTED, LIGHT, PURPLE, BLUE, CYAN, S300, S400, WHITE, FONT, MONO

LINE = "#D5DEEA"

# official icons not in the aws_icons.py registry (added in memory, without touching that file)
_EXTRA = {
    "ec2":            "Architecture-Service-Icons_07312026/Arch_Compute/64/Arch_Amazon-EC2_64.svg",
    "grp_ec2":        "Architecture-Group-Icons_07312026/EC2-instance-contents_32.svg",
    "outposts":       "Architecture-Service-Icons_07312026/Arch_Compute/64/Arch_AWS-Outposts-servers_64.svg",
    "eks":            "Architecture-Service-Icons_07312026/Arch_Containers/64/Arch_Amazon-Elastic-Kubernetes-Service_64.svg",
    "eks_outposts":   "Resource-Icons_07312026/Res_Containers/Res_Amazon-Elastic-Kubernetes-Service_EKS-on-Outposts_48.svg",
    "stream_manager": "Resource-Icons_07312026/Res_IoT/Res_AWS-IoT-Greengrass_Stream-Manager_48.svg",
    "gg_component":   "Resource-Icons_07312026/Res_IoT/Res_AWS-IoT-Greengrass_Component_48.svg",
    "sm_model":       "Resource-Icons_07312026/Res_Artificial-Intelligence/Res_Amazon-SageMaker-AI_Model_48.svg",
    "iot_sensor_gen": "Resource-Icons_07312026/Res_IoT/Res_AWS-IoT_Sensor_48.svg",
    "iot_utility":    "Resource-Icons_07312026/Res_IoT/Res_AWS-IoT_Thing_Utility_48.svg",
}
try:
    import aws_icons as _aws
    for _k, _v in _EXTRA.items():
        _aws.ICONS.setdefault(_k, _v)
except Exception:                                        # noqa: BLE001
    _aws = None


_WARNED = set()


def icon(key, x, y, size):
    """Official AWS icon (not recolored). Without the package, a slot and a warning: does not fail."""
    try:
        return _aws.nested(key, x, y, size)
    except Exception as e:                               # noqa: BLE001
        if key not in _WARNED:
            _WARNED.add(key)
            print(f"  (warning) icon {key} not available: {e.__class__.__name__}; set AWS_ICONS", file=sys.stderr)
        return (f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="8" fill="{WHITE}" stroke="{NAVY}" '
                f'stroke-width="2" stroke-dasharray="4 4"/>')


def wrap(body):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900" class="iso">'
            f'{body}</svg>')


def T(x, y, s, size=20, color=NAVY, weight=400, anchor="start", family=FONT, extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{color}" text-anchor="{anchor}" {extra}>{html.escape(s)}</text>')


def TR(x, y, runs, size=20, anchor="start", family=FONT):
    """Text with runs: runs = [(text, color, weight)]."""
    sp = "".join(f'<tspan fill="{c}" font-weight="{w}">{html.escape(t)}</tspan>' for t, c, w in runs)
    return f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" text-anchor="{anchor}">{sp}</text>'


def R(x, y, w, h, fill="none", stroke=None, sw=1.5, rx=10, dash=None, extra=""):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    ds = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}"{st}{ds} {extra}/>'


def L(pts, color=NAVY, sw=2, dash=None, head=0, extra=""):
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    ds = f' stroke-dasharray="{dash}"' if dash else ""
    out = f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"{ds} {extra}/>'
    if head:
        (x1, y1), (x2, y2) = pts[-2], pts[-1]
        a = math.atan2(y2 - y1, x2 - x1)
        p1 = (x2 - head * math.cos(a - .45), y2 - head * math.sin(a - .45))
        p2 = (x2 - head * math.cos(a + .45), y2 - head * math.sin(a + .45))
        out += f'<polygon points="{x2:.1f},{y2:.1f} {p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}" fill="{color}"/>'
    return out


def chip(cx, cy, s, color):
    """A chip seen from the front: a square with pins."""
    o = [R(cx - s / 2, cy - s / 2, s, s, fill=color, rx=6)]
    o.append(R(cx - s * .28, cy - s * .28, s * .56, s * .56, fill="none", stroke=mix(color, WHITE, .55), sw=1.6, rx=3))
    for k in range(4):
        t = -s * .3 + k * s * .2
        o.append(L([(cx + t, cy - s / 2 - 7), (cx + t, cy - s / 2)], color, 2.5))
        o.append(L([(cx + t, cy + s / 2), (cx + t, cy + s / 2 + 7)], color, 2.5))
        o.append(L([(cx - s / 2 - 7, cy + t), (cx - s / 2, cy + t)], color, 2.5))
        o.append(L([(cx + s / 2, cy + t), (cx + s / 2 + 7, cy + t)], color, 2.5))
    return "".join(o)


def check(x, y, color=PURPLE, s=1.0):
    return L([(x - 7 * s, y), (x - 2 * s, y + 5 * s), (x + 8 * s, y - 6 * s)], color, 3 * s)


def cross(x, y, color=PURPLE, r=7):
    return L([(x - r, y - r), (x + r, y + r)], color, 3) + L([(x + r, y - r), (x - r, y + r)], color, 3)


def G(on, body):
    return f'<g data-on="{on}">{body}</g>'


def M(key):
    """(text, pending) from metrics.fmt. Anything not measured yet is drawn as «por medir»
    (the template font has no ⟨ ⟩)."""
    try:
        from metrics import fmt, PENDING
        v = fmt(key)
    except Exception:                                    # noqa: BLE001
        return "por medir", True
    if v == PENDING:
        return "por medir", True
    return v.replace("\xa0", "\u202f"), False          # Carlito lacks U+00A0; it has U+202F


# ─────────────────────────────────────────────────────────────────────
#  optimize per chip
# ─────────────────────────────────────────────────────────────────────
def fig_optimize(static=False):
    """Step 2 · one artifact per chip, memory rules; below, the measured pump (FP32 → INT8)."""
    o = []
    Y, H, S = 284, 82, 96                                 # card rows
    # the trained model
    o.append(T(96, 266, "ENTRENADO", 18, MUTED, 700, family=MONO, extra='letter-spacing="2"'))
    o.append(R(96, Y, 300, 2 * S + H, fill=LIGHT, stroke=LINE))
    for k in range(4):                                   # model layers
        o.append(R(132 + k * 14, Y + 22 + k * 11, 150, 60, fill=WHITE, stroke=mix(NAVY, WHITE, .5 - k * .1), sw=1.6, rx=8))
    o.append(T(132, Y + 172, "32 bits", 44, NAVY, 700))
    o.append(T(132, Y + 206, "Modelo de la bomba", 22, NAVY, 700))
    o.append(T(132, Y + 236, "un archivo ONNX, en FP32", 18, SLATE))
    # the three operations
    ops = [("Cuantizar", "32 → 8 bits: hasta 4× menos"),
           ("Fusionar y podar", "menos operaciones y pesos"),
           ("Compilar", "para el acelerador del chip")]
    mid = Y + S + H / 2
    body = [L([(400, mid), (446, mid)], NAVY, 2.4, head=10)]
    body.append(T(462, 266, "OPTIMIZAR POR CHIP", 18, PURPLE, 700, family=MONO, extra='letter-spacing="2"'))
    for k, (t, sub) in enumerate(ops):
        y = Y + k * S
        body.append(R(462, y, 330, H, fill=WHITE, stroke=PURPLE, sw=1.8))
        body.append(T(484, y + 34, f"0{k + 1}", 18, PURPLE, 700, family=MONO))
        body.append(T(522, y + 35, t, 24, NAVY, 700))
        body.append(T(522, y + 62, sub, 18, SLATE))
    o.append(G(1, "".join(body)))
    # one artifact per chip, and each chip's memory as a constraint
    tg = [("NPU · INT8", "LiteRT · Qualcomm QNN", .86, PURPLE),
          ("GPU · FP16", "TensorRT", .46, BLUE),
          ("CPU · INT8", "ONNX Runtime · OpenVINO", .34, CYAN)]
    body = [T(900, 266, "UN ARTEFACTO POR CHIP", 18, MUTED, 700, family=MONO, extra='letter-spacing="2"')]
    for k, (t, tool, fill, col) in enumerate(tg):
        y = Y + k * S
        body.append(L([(796, mid), (840, mid), (840, y + H / 2), (884, y + H / 2)], NAVY, 2, head=9))
        body.append(R(900, y, 604, H, fill=WHITE, stroke=LINE))
        body.append(chip(950, y + H / 2, 34, col))
        body.append(T(996, y + 35, t, 24, NAVY, 700))
        body.append(T(996, y + 62, tool, 18, SLATE))
        # memory: the border is what the chip has; the fill, what the artifact takes
        mx, mw = 1290, 186
        body.append(T(mx, y + 32, "memoria del chip", 18, SLATE))
        body.append(R(mx, y + 44, mw, 18, fill=WHITE, stroke=NAVY, sw=1.6, rx=4))
        body.append(R(mx + 3, y + 47, (mw - 6) * fill, 12, fill=col, rx=2))
    o.append(G(2, "".join(body)))
    # the pump, measured: FP32 versus INT8 (numbers from metrics.json; if missing, «por medir»)
    by = 586
    b = [R(96, by, 1408, 116, fill=WHITE, stroke=PURPLE, sw=2)]
    b.append(T(126, by + 44, "LA BOMBA, MEDIDA", 18, PURPLE, 700, family=MONO, extra='letter-spacing="1.5"'))
    b.append(TR(126, by + 88, [("FP32 ", NAVY, 700), ("→ ", MUTED, 400), ("INT8", PURPLE, 700)], 32))
    cols = [("Tamaño del archivo", M("int8.size_fp32_kb"), M("int8.size_int8_kb"), ""),
            ("Latencia por clip, en el equipo (x86)", M("device.lat_fp32_ms"), M("device.lat_int8_ms"), ""),
            ("Misma decisión", None, M("int8.agree_pct"), " de los clips")]
    for k, (lab, v0, v1, tail) in enumerate(cols):
        x = 446 + k * 356
        b.append(L([(x - 24, by + 22), (x - 24, by + 94)], LINE, 1.5))
        b.append(T(x, by + 44, lab, 18, SLATE))
        if v1[1] or (v0 and v0[1]):
            runs = [("por medir", MUTED, 400)]
        else:
            runs = ([(v0[0], NAVY, 700), (" → ", MUTED, 400)] if v0 else []) + [(v1[0], PURPLE, 700), (tail, NAVY, 400)]
        b.append(TR(x, by + 88, runs, 30))
    o.append(G(3, "".join(b)))
    return wrap("".join(o))


# ─────────────────────────────────────────────────────────────────────
#  the model passport
# ─────────────────────────────────────────────────────────────────────
def fig_passport(static=False):
    o = []
    g = Iso(ox=330, oy=380, u=46)
    g.box(0, 0, 0, 3.2, 3.2, 1.6, BLUE)
    g.poly([(1.4, 0, 1.6), (1.8, 0, 1.6), (1.8, 3.2, 1.6), (1.4, 3.2, 1.6)], mix(BLUE, WHITE, .55))
    g.poly([(0, 3.2, .6), (3.2, 3.2, .6), (3.2, 3.2, .85), (0, 3.2, .85)], mix(BLUE, WHITE, .55))
    o.append(g.svg())
    ex, ey = g.P(3.2, 1.6, 1.6)
    o.append(T(330, 640, "el modelo, empacado", 22, NAVY, 700, "middle"))
    o.append(T(330, 668, "lo que viaja al equipo", 18, SLATE, 400, "middle"))
    # string to the tag
    o.append(L([(ex, ey), (600, 300)], S400, 2, "5 6"))
    o.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="5" fill="{S400}"/>')
    X, Y, W, H = 600, 236, 904, 490
    o.append(R(X, Y, W, H, fill=WHITE, stroke=LINE, sw=1.6, rx=14))
    o.append(R(X, Y, W, 56, fill=LIGHT, rx=14))
    o.append(R(X, Y + 40, W, 16, fill=LIGHT, rx=0))
    o.append(f'<circle cx="{X + 30}" cy="{Y + 28}" r="7" fill="{WHITE}" stroke="{S400}" stroke-width="2"/>')
    o.append(T(X + 52, Y + 35, "PASAPORTE DEL MODELO", 17, PURPLE, 700, family=MONO, extra='letter-spacing="2"'))
    o.append(T(X + W - 24, Y + 35, "v1.4.0-npu", 17, NAVY, 700, "end", MONO))
    secs = [("Identidad", [("Nombre y versión", "v1.4.0-npu, inmutable"),
                           ("Huella", "SHA-256 de cada archivo"),
                           ("Firma", "Sigstore · OpenSSF Model Signing")]),
            ("Procedencia", [("Datos, código y dependencias", "ML-BOM · CycloneDX o SPDX 3.0"),
                             ("Para qué sirve y para qué no", "model card")]),
            ("Para operar", [("Chip y runtime", "NPU · INT8 · LiteRT"),
                             ("Línea base de la entrada", "para medir el drift en el equipo"),
                             ("Umbrales y última versión buena", "para volver solo")])]
    y = Y + 94
    for i, (title, rows) in enumerate(secs):
        b = [T(X + 30, y, title.upper(), 15, MUTED, 700, family=MONO, extra='letter-spacing="1.5"')]
        yy = y + 34
        for lab, val in rows:
            b.append(check(X + 42, yy - 7))
            b.append(T(X + 66, yy, lab, 21, NAVY, 700))
            b.append(T(X + 480, yy, val, 19, SLATE))
            yy += 33
        if i < len(secs) - 1:
            b.append(L([(X + 30, yy - 12), (X + W - 30, yy - 12)], LINE, 1.5))
        o.append(G(i, "".join(b)))
        y = yy + 22
    return wrap("".join(o))


# ─────────────────────────────────────────────────────────────────────
#  shadow mode, rings and automatic rollback
# ─────────────────────────────────────────────────────────────────────
def chipver(x, y, s, color, extra="", w=None):
    """18 px monospaced pill (version, thing group…). x, y = top-left corner."""
    w = w or len(s) * 10.8 + 24
    return (f'<g {extra}>' + R(x, y, w, 32, fill=WHITE, stroke=color, sw=1.8, rx=7) +
            T(x + w / 2, y + 22, s, 18, color, 700, "middle", MONO) + '</g>')


def gate(cx, cy, ok=True, extra=""):
    o = (f'<polygon points="{cx},{cy - 26} {cx + 26},{cy} {cx},{cy + 26} {cx - 26},{cy}" fill="{WHITE}" '
         f'stroke="{NAVY if ok else PURPLE}" stroke-width="2.4"/>')
    o += check(cx, cy, NAVY, .95) if ok else cross(cx, cy, PURPLE, 7)
    return f'<g {extra}>{o}</g>'


def fig_rings(static=False):
    """Step 4 · ring 0 (one station, canary) → ring 1 (the rest), with its configuration and the rollback."""
    o = []
    Y0, Y1 = 248, 452
    # ring 0
    b = [R(96, Y0, 420, Y1 - Y0, fill=WHITE, stroke=PURPLE, sw=2)]
    b.append(T(124, Y0 + 40, "RING 0", 18, PURPLE, 700, family=MONO, extra='letter-spacing="2"'))
    b.append(T(124, Y0 + 80, "Una estación: el canary", 30, NAVY, 700))
    b.append(T(124, Y0 + 112, "thing group", 18, SLATE))
    b.append(chipver(230, Y0 + 90, "StationRing0", NAVY))
    b.append(f'<circle cx="150" cy="{Y0 + 164}" r="20" fill="{PURPLE}"/>')
    b.append(chipver(186, Y0 + 148, "v2.0.0", PURPLE, extra='data-off="3"'))
    o.append(G(0, "".join(b)))
    # at click 3 v2 goes away and v1 comes back
    o.append(G(3, chipver(186, Y0 + 148, "v1.0.0", NAVY) +
               T(296, Y0 + 170, "la última buena", 18, PURPLE, 700)))
    # gate and ring 1
    b = [L([(516, 350), (536, 350)], NAVY, 2), L([(584, 350), (600, 350)], NAVY, 2, head=8), gate(560, 350)]
    b.append(R(604, Y0, 900, Y1 - Y0, fill=WHITE, stroke=LINE, sw=1.6))
    b.append(T(632, Y0 + 40, "RING 1", 18, MUTED, 700, family=MONO, extra='letter-spacing="2"'))
    b.append(T(632, Y0 + 80, "El resto de la flota", 30, NAVY, 700))
    b.append(T(632, Y0 + 112, "thing group", 18, SLATE))
    b.append(chipver(738, Y0 + 90, "StationRing1", NAVY))
    b.append(T(632, Y0 + 158, "jobExecutionsRolloutConfig", 19, NAVY, 700, family=MONO))
    b.append(T(632, Y0 + 186, "rollout exponencial: cada wave llega a más equipos", 18, SLATE))
    # growing waves (outlines: ring 1 has not received anything yet)
    waves, x = [1, 2, 4, 8, 16], 1110
    for k, n in enumerate(waves):
        rows = max(1, n // 4) if n >= 4 else 1
        cols = min(n, 4)
        wx = x + sum(min(m, 4) * 17 + 22 for m in waves[:k])
        for j in range(n):
            cx, cy = wx + (j % cols) * 17, Y0 + 176 - (j // cols) * 17
            b.append(f'<circle cx="{cx}" cy="{cy}" r="6.5" fill="{mix(PURPLE, WHITE, .82)}" stroke="{PURPLE}" stroke-width="1.6"/>')
    b.append(T(1110, Y0 + 100, "waves del rollout", 18, MUTED, 400))
    o.append(G(1, "".join(b)))
    # the configuration that protects the deployment
    cy0 = 488
    b = []
    for k, (key, txt) in enumerate([("abortConfig", "si fallan demasiados equipos, el despliegue se cancela"),
                                    ("failureHandlingPolicy: ROLLBACK", "si un equipo no arranca la versión nueva, vuelve a la que tenía")]):
        y = cy0 + k * 110
        b.append(R(604, y, 900, 94, fill=LIGHT, stroke=LINE, sw=1.5))
        b.append(T(632, y + 40, key, 21, PURPLE, 700, family=MONO))
        b.append(T(632, y + 72, txt, 19, NAVY))
    o.append(G(2, "".join(b)))
    # the rollback: the gate says no and ring 0 goes back to the last good version
    b = [gate(560, 350, ok=False)]
    b.append(L([(560, 378), (560, 520), (306, 520), (306, Y1 + 8)], PURPLE, 3, head=12))
    b.append(T(96, 586, "El rollback", 24, PURPLE, 700))
    b.append(T(96, 618, "La alarma ve fallas que nadie oyó", 19, NAVY))
    b.append(T(96, 646, "y despliega la última versión buena.", 19, NAVY))
    b.append(T(96, 682, "El ring 1 nunca recibe la v2.", 19, SLATE))
    o.append(G(3, "".join(b)))
    return wrap("".join(o))


# ─────────────────────────────────────────────────────────────────────
#  the four kinds of drift
# ─────────────────────────────────────────────────────────────────────
def _bell(x0, x1, base, h, mu, sd, lo=0, hi=1):
    pts = []
    for k in range(61):
        t = lo + (hi - lo) * k / 60
        pts.append((x0 + (x1 - x0) * k / 60, base - h * math.exp(-.5 * ((t - mu) / sd) ** 2)))
    return pts


def fig_drift(static=False):
    P = [("01", "Data drift", "P(X) cambia",
          ["Cambia lo que entra: otra iluminación,", "un sensor descalibrado, otra materia prima."]),
         ("02", "Concept drift", "P(Y | X) cambia",
          ["Lo que entra se ve igual, pero ya significa", "otra cosa: cambió la máquina o el proceso."]),
         ("03", "Prediction drift", "P(Ŷ) cambia",
          ["Cambia lo que el modelo decide: una clase", "desaparece, otra se dispara."]),
         ("04", "Training-serving skew", "f(x) ≠ f′(x)",
          ["El equipo no prepara los datos como el", "entrenamiento: unidades, escala, columnas."])]
    o = []
    for i, (n, t, f, ex) in enumerate(P):
        x, y = 96 + (i % 2) * 718, 236 + (i // 2) * 262
        w, h = 690, 240
        b = [R(x, y, w, h, fill=WHITE, stroke=LINE, sw=1.6, rx=12)]
        b.append(T(x + 26, y + 40, n, 15, PURPLE, 700, family=MONO))
        b.append(T(x + 62, y + 41, t, 27, NAVY, 700))
        b.append(T(x + 26, y + 76, f, 18, MUTED, 700, family=MONO))
        for k, line in enumerate(ex):
            b.append(T(x + 26, y + 140 + k * 28, line, 19, SLATE))
        # chart on the right
        gx0, gx1, gb = x + 430, x + 662, y + 200
        if i == 0:
            base = _bell(gx0, gx1, gb, 120, .38, .13)
            cur = _bell(gx0, gx1, gb, 108, .62, .15)
            b.append(L([(gx0, gb), (gx1, gb)], S400, 1.5))
            b.append(f'<path d="M{gx0},{gb} ' + " ".join(f"L{px:.1f},{py:.1f}" for px, py in cur) +
                     f' L{gx1},{gb} Z" fill="{PURPLE}" fill-opacity=".22" stroke="{PURPLE}" stroke-width="2.5"/>')
            b.append(L(base, NAVY, 2.2, "6 5"))
            b.append(T(gx0 + 10, y + 70, "entrenamiento", 14, NAVY, 700, family=MONO))
            b.append(T(gx1, y + 92, "hoy", 14, PURPLE, 700, "end", MONO))
        elif i == 1:
            import random
            rnd = random.Random(7)
            for k in range(26):
                px, py = gx0 + 10 + rnd.random() * 210, y + 50 + rnd.random() * 140
                above = (py - (y + 190)) < -(px - gx0) * .62
                b.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5" fill="{PURPLE if above else NAVY}"/>')
            b.append(L([(gx0, y + 190), (gx0 + 220, y + 54)], NAVY, 2.2, "6 5"))
            b.append(L([(gx0 + 40, y + 200), (gx0 + 160, y + 44)], PURPLE, 3))
            b.append(T(gx1, y + 226, "frontera nueva", 14, PURPLE, 700, "end", MONO))
        elif i == 2:
            bef, aft = [.33, .33, .34], [.0, .36, .64]
            b.append(L([(gx0, gb), (gx1, gb)], S400, 1.5))
            for k in range(3):
                bx = gx0 + 14 + k * 76
                hb, ha = bef[k] * 210, aft[k] * 210
                b.append(R(bx, gb - hb, 26, hb, fill="none", stroke=NAVY, sw=2, rx=2, dash="5 4"))
                if ha:
                    b.append(R(bx + 30, gb - ha, 26, ha, fill=PURPLE, rx=2))
                else:
                    b.append(cross(bx + 43, gb - 14, PURPLE, 6))
            for k, c in enumerate("ABC"):
                b.append(T(gx0 + 42 + k * 76, gb + 22, c, 15, MUTED, 700, "middle", MONO))
        else:
            for k, (lab, col, yy) in enumerate([("entrenamiento", NAVY, y + 90), ("equipo", PURPLE, y + 168)]):
                b.append(T(gx0, yy - 26, lab, 14, col, 700, family=MONO))
                b.append(R(gx0, yy - 16, 44, 32, fill=WHITE, stroke=col, sw=1.8, rx=6))
                b.append(T(gx0 + 22, yy + 5, "x", 16, col, 700, "middle", MONO))
                b.append(L([(gx0 + 48, yy), (gx0 + 82, yy)], col, 2, head=7))
                b.append(R(gx0 + 86, yy - 16, 92, 32, fill=WHITE, stroke=col, sw=1.8, rx=6))
                b.append(T(gx0 + 132, yy + 5, "escala" + ("" if k == 0 else "′"), 15, col, 700, "middle", MONO))
                b.append(L([(gx0 + 182, yy), (gx0 + 212, yy)], col, 2, head=7))
                b.append(f'<circle cx="{gx0 + 224}" cy="{yy}" r="10" fill="{col}"/>')
            b.append(T(gx0 + 132, y + 136, "≠", 28, PURPLE, 700, "middle"))
        o.append(G(i, "".join(b)))
    return wrap("".join(o))


# ─────────────────────────────────────────────────────────────────────
#  measuring drift on the device
# ─────────────────────────────────────────────────────────────────────
EXP = [.02, .05, .10, .16, .20, .18, .14, .09, .04, .02]          # baseline (training)
ACT = [.01, .02, .04, .08, .13, .17, .19, .17, .12, .07]          # today's window


def psi(e, a):
    return sum((ai - ei) * math.log(ai / ei) for ei, ai in zip(e, a))


def fig_measure(static=False):
    o = []
    v = psi(EXP, ACT)
    # histograms
    x0, base, bw = 96, 560, 50
    b = [T(96, 272, "CALCULADO EN EL EQUIPO · CADA MINUTO", 15, PURPLE, 700, family=MONO, extra='letter-spacing="1.5"')]
    b.append(L([(x0, base), (x0 + 10 * bw + 10, base)], S400, 1.5))
    for k in range(10):
        bx = x0 + 5 + k * bw
        he, ha = EXP[k] * 1250, ACT[k] * 1250
        b.append(R(bx + 4, base - ha, bw - 8, ha, fill=PURPLE, rx=3, extra='fill-opacity=".85"'))
        b.append(R(bx + 4, base - he, bw - 8, he, fill="none", stroke=NAVY, sw=2.2, rx=3, dash="6 4"))
    b.append(L([(110, 600), (140, 600)], NAVY, 2.2, "6 4"))
    b.append(T(150, 606, "línea base del entrenamiento", 18, NAVY, 700))
    b.append(R(110, 624, 30, 14, fill=PURPLE, rx=3))
    b.append(T(150, 637, "ventana del último minuto", 18, PURPLE, 700))
    o.append(G(0, "".join(b)))
    # the PSI
    X = 680
    b = [R(X, 300, 400, 330, fill=LIGHT, stroke=LINE, rx=14)]
    b.append(T(X + 28, 340, "PSI", 17, MUTED, 700, family=MONO, extra='letter-spacing="2"'))
    b.append(T(X + 28, 376, "Σ (a − e) · ln(a / e)", 22, NAVY, 700, family=MONO))
    b.append(T(X + 28, 466, f"{v:.2f}".replace(".", ","), 84, PURPLE, 700))
    segs = [(0, .1, "< 0,1", "estable", S300), (.1, .25, "0,1–0,25", "vigilar", mix(PURPLE, WHITE, .6)),
            (.25, .4, "> 0,25", "cambio grande", PURPLE)]
    sx0, sw_ = X + 28, 344
    for lo, hi, a, t, col in segs:
        xa, xb = sx0 + lo / .4 * sw_, sx0 + hi / .4 * sw_
        b.append(R(xa + 2, 500, xb - xa - 4, 12, fill=col, rx=3))
        b.append(T((xa + xb) / 2, 538, a, 14, NAVY, 700, "middle", MONO))
        b.append(T((xa + xb) / 2, 560, t, 15, SLATE, 400, "middle"))
    mx = sx0 + min(v, .4) / .4 * sw_
    b.append(f'<polygon points="{mx:.1f},496 {mx - 8:.1f},484 {mx + 8:.1f},484" fill="{NAVY}"/>')
    b.append(T(X + 200, 604, "umbrales: regla de la industria, no una ley", 15, MUTED, 400, "middle"))
    o.append(G(1, "".join(b)))
    # what travels
    X = 1130
    b = [T(X, 340, "¿QUÉ VIAJA A LA NUBE?", 15, MUTED, 700, family=MONO, extra='letter-spacing="1.5"')]
    b.append(R(X, 362, 374, 92, fill=WHITE, stroke=PURPLE, sw=2))
    b.append(check(X + 34, 404))
    b.append(T(X + 60, 402, "Perfil + PSI", 24, NAVY, 700))
    b.append(T(X + 60, 430, "kilobytes por minuto", 18, SLATE))
    b.append(R(X, 474, 374, 92, fill=WHITE, stroke=LINE, sw=1.6))
    b.append(cross(X + 34, 516, MUTED, 8))
    b.append(T(X + 60, 514, "Datos crudos", 24, MUTED, 700))
    b.append(L([(X + 56, 506), (X + 194, 506)], MUTED, 2))
    b.append(T(X + 60, 542, "megabytes por minuto, y privados", 18, MUTED))
    o.append(G(2, "".join(b)))
    o.append(G(3, R(96, 662, 1408, 64, fill=WHITE, stroke=PURPLE, sw=2) +
               TR(126, 703, [("¿Sin etiquetas? ", PURPLE, 700),
                             ("Estima el desempeño con la confianza calibrada (CBPE) y confírmalo cuando lleguen.", NAVY, 400)], 23)))
    return wrap("".join(o))


# ─────────────────────────────────────────────────────────────────────
#  step 1 · train: normal sound → autoencoder → artifacts in S3
# ─────────────────────────────────────────────────────────────────────
def _wave(x, y, w, amp, seed, color=NAVY, sw=2):
    """A drawn wave (illustration, not data)."""
    import random
    r = random.Random(seed)
    pts = []
    for k in range(0, int(w) + 1, 7):
        a = amp * (.55 + .45 * math.sin(k / 23 + seed)) * (1 if (k // 7) % 2 else -1) * (.6 + .4 * r.random())
        pts.append((x + k, y + a))
    return L(pts, color, sw)


def fig_train(static=False):
    """Step 1 · normal sound → SageMaker AI trains the autoencoder → S3, one prefix per version (one box per click)."""
    o = []
    Y0, Y1 = 320, 536
    MY = (Y0 + Y1) / 2
    # A · the normal sound
    b = [R(96, Y0, 380, Y1 - Y0, fill=LIGHT, stroke=LINE)]
    b.append(T(124, Y0 + 40, "SONIDO NORMAL", 18, PURPLE, 700, family=MONO, extra='letter-spacing="2"'))
    for k in range(3):
        b.append(_wave(124, Y0 + 76 + k * 30, 322, 9, k + 1, mix(NAVY, WHITE, k * .25), 1.8))
    b.append(T(124, Y0 + 178, "Bombas reales · MIMII DUE", 22, NAVY, 700))
    b.append(T(124, Y0 + 204, "solo clips normales: las fallas son raras", 18, SLATE))
    o.append(G(0, "".join(b)))
    # B · SageMaker AI trains the autoencoder
    b = [L([(480, MY), (528, MY)], NAVY, 2.4, head=10)]
    b.append(R(536, Y0, 470, Y1 - Y0, fill=WHITE, stroke=PURPLE, sw=2))
    b.append(icon("sagemaker", 564, Y0 + 24, 52))
    b.append(T(630, Y0 + 50, "SageMaker AI", 24, NAVY, 700))
    b.append(T(630, Y0 + 76, "entrena el autoencoder", 18, SLATE))
    # the autoencoder: narrows and opens up again
    ax, ay = 566, Y0 + 98
    b.append(f'<polygon points="{ax},{ay} {ax + 92},{ay + 18} {ax + 92},{ay + 46} {ax},{ay + 64}" fill="{mix(PURPLE, WHITE, .8)}" stroke="{PURPLE}" stroke-width="1.8"/>')
    b.append(R(ax + 98, ay + 18, 20, 28, fill=PURPLE, rx=3))
    b.append(f'<polygon points="{ax + 124},{ay + 18} {ax + 216},{ay} {ax + 216},{ay + 64} {ax + 124},{ay + 46}" fill="{mix(PURPLE, WHITE, .8)}" stroke="{PURPLE}" stroke-width="1.8"/>')
    b.append(T(ax + 244, ay + 28, "aprende a rehacer", 19, NAVY, 700))
    b.append(T(ax + 244, ay + 52, "el sonido normal", 19, NAVY, 700))
    b.append(T(566, Y1 - 24, "score = error de reconstrucción", 19, PURPLE, 700, family=MONO))
    o.append(G(1, "".join(b)))
    # C · S3, one prefix per version
    b = [L([(1010, MY), (1058, MY)], NAVY, 2.4, head=10)]
    b.append(R(1066, Y0, 438, Y1 - Y0, fill=WHITE, stroke=LINE, sw=1.6))
    b.append(icon("s3", 1094, Y0 + 24, 52))
    b.append(T(1160, Y0 + 50, "S3", 24, NAVY, 700))
    b.append(T(1160, Y0 + 76, "un prefijo por versión", 18, SLATE))
    b.append(chipver(1094, Y0 + 112, "station/1.0.0/", NAVY))
    b.append(T(1094, Y0 + 178, "inmutable: una versión nueva", 18, SLATE))
    b.append(T(1094, Y0 + 202, "es otro prefijo, nunca el mismo", 18, SLATE))
    o.append(G(2, "".join(b)))
    return wrap("".join(o))


# ─────────────────────────────────────────────────────────────────────
#  step 3 · the component recipe, read at build time and annotated per click
# ─────────────────────────────────────────────────────────────────────
RECIPE = _os.environ.get("STATION_RECIPE", _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))),
    "poc-devopsdays", "component", "recipe.template.yaml"))

_RECIPE_FALLBACK = """ComponentName: com.station.Listener
ComponentVersion: '__VERSION__'
ComponentConfiguration:
  DefaultConfiguration:
    topic: 'station/events'
    threshold: '__THRESHOLD__'
    intervalSeconds: '3'
    accessControl:
      aws.greengrass.ipc.mqttproxy:
        com.station.Listener:mqttproxy:1:
          operations:
            - 'aws.greengrass#PublishToIoTCore'
          resources:
            - 'station/events'
Manifests:
  - Platform:
      os: linux
    Lifecycle:
      run: >-
        python3 -u {artifacts:path}/inference.py
        --threshold {configuration:/threshold}
    Artifacts:
      - URI: 's3://__BUCKET__/station/__VERSION__/model.onnx'
"""

_KEY = __import__("re").compile(r"^(\s*)(- )?([A-Za-z0-9_.\-]+(?::[A-Za-z0-9_.\-]+)*):(\s.*)?$")


def _recipe_lines(text, maxw=56):
    """List of (text, block) with the summarized recipe. Blocks: art, life, conf, ipc or ''."""
    import re
    def subst(t):
        t = t.replace("__VERSION__", "1.0.0")
        t = re.sub(r"__([A-Z0-9_]+)__", lambda m: "<" + {"BUCKET": "bucket", "THRESHOLD": "threshold"}.get(
            m.group(1), m.group(1).lower()) + ">", t)
        return t if len(t) <= maxw else t[:maxw - 1] + "…"
    def strip_comment(t):
        q = None
        for i, c in enumerate(t):
            if c in "'\"":
                q = None if q == c else (q or c)
            elif c == "#" and q is None and (i == 0 or t[i - 1] in " \t"):
                return t[:i].rstrip()
        return t
    raw = [strip_comment(l.rstrip("\n")).replace("\t", "  ") for l in text.splitlines()]
    raw = [l for l in raw if l.strip() and l.strip() not in ("---", "...")]
    out, stack = [], []          # stack: (indent, key)
    drop_top = {"RecipeFormatVersion", "ComponentDescription", "ComponentPublisher", "ComponentDependencies",
                "ComponentType", "ComponentSource"}
    skip_until = None            # indentation: skip everything nested deeper
    buf = []                     # continuation of a lifecycle command
    n_art = 0

    def flush():
        if not buf:
            return
        keep = {0}
        thr = [i for i, (l, _) in enumerate(buf) if "{configuration:" in l and "threshold" in l]
        cfg = [i for i, (l, _) in enumerate(buf) if "{configuration:" in l]
        keep |= set(thr or cfg[:1])
        last = -1
        for i, (l, ind) in enumerate(buf):
            if i in keep:
                if i - last > 1:
                    out.append((" " * ind + "…", "life"))
                out.append((subst(" " * ind + l), "life"))
                last = i
        if len(buf) - 1 > last:
            out.append((" " * buf[-1][1] + "…", "life"))
        buf.clear()

    for l in raw:
        ind = len(l) - len(l.lstrip())
        if skip_until is not None:
            if ind > skip_until:
                continue
            skip_until = None
        m = _KEY.match(l)
        if m:
            flush()
            kind = ind + (2 if m.group(2) else 0)
            while stack and stack[-1][0] >= kind:
                stack.pop()
            key = m.group(3)
            stack.append((kind, key))
            path = [k for _, k in stack]
            if len(path) == 1 and key in drop_top:
                skip_until = ind
                continue
            if key == "policyDescription":
                continue
        else:
            path = [k for _, k in stack] + ["…"]
        blk = ("ipc" if "accessControl" in path else
               "conf" if "DefaultConfiguration" in path and path[-1] != "DefaultConfiguration" else
               "life" if "Lifecycle" in path else
               "art" if "Artifacts" in path else "")
        if blk == "life" and not m:
            buf.append((l.strip(), ind))
            continue
        if blk == "art" and m and m.group(2):
            n_art += 1
            if n_art > 4:
                if out and out[-1][0].strip() != "…":
                    out.append((" " * ind + "…", blk))
                skip_until = ind
                continue
        out.append((subst(l), blk))
    flush()
    return out


def _yaml_runs(t, emph=False):
    """Colors of a YAML line: key in navy, value in slate; the {…} braces in purple."""
    import re
    m = _KEY.match(t)
    if m:
        ind, dash, key, rest = m.group(1), m.group(2) or "", m.group(3), (m.group(4) or "")
        runs = [(ind + dash, NAVY, 700), (key + ":", NAVY, 700)]
    else:
        runs, rest = [], t
    for part in re.split(r"(\{[^}]*\})", rest):
        if part:
            runs.append((part, PURPLE if part.startswith("{") else (PURPLE if emph else SLATE), 700))
    return runs


def _mono_line(x, y, runs, size=18):
    sp = "".join(f'<tspan fill="{c}" font-weight="{w}">{html.escape(t)}</tspan>' for t, c, w in runs)
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{MONO}" font-size="{size}" xml:space="preserve">{sp}</text>')


def fig_recipe(static=False):
    try:
        text, real = open(RECIPE, encoding="utf-8").read(), True
    except OSError:
        text, real = _RECIPE_FALLBACK, False
    note = "· la receta de la demo, recortada"
    if not real:
        note = "· receta de ejemplo: falta recipe.template.yaml"
        print("  (warning) recipe: not found", RECIPE, "— drawing the sample one", file=sys.stderr)
    try:
        lines = _recipe_lines(text)
        if len({b for _, b in lines} & {"art", "life", "conf", "ipc"}) < 2:
            raise ValueError("does not look like a Greengrass recipe")
    except Exception as e:                               # noqa: BLE001
        print(f"  (warning) unreadable recipe ({e}); drawing the sample one", file=sys.stderr)
        lines, real = _recipe_lines(_RECIPE_FALLBACK), False
        note = "· receta de ejemplo: recipe.template.yaml cambió de forma"
    # two columns: what gets configured | how it runs (from Manifests)
    cut = next((i for i, (t, _) in enumerate(lines) if t.startswith("Manifests")), (len(lines) + 1) // 2)
    cols = [lines[:cut], lines[cut:]]
    MAXL, LH, FS = 14, 21.5, 18
    X0, Y0, W, H = 96, 236, 1408, 392
    CW = W / 2
    o = [R(X0, Y0, W, H, fill=WHITE, stroke=LINE, sw=1.6, rx=12)]
    o.append(R(X0, Y0, W, 44, fill=LIGHT, rx=12) + R(X0, Y0 + 28, W, 16, fill=LIGHT, rx=0))
    o.append(T(X0 + 24, Y0 + 29, "recipe.yaml", 18, NAVY, 700, family=MONO))
    o.append(T(X0 + 170, Y0 + 29, note, 18, MUTED if real else PURPLE))
    o.append(L([(X0 + CW, Y0 + 60), (X0 + CW, Y0 + H - 16)], LINE, 1.5))
    ytop = Y0 + 80
    spans = {}                   # block → (column, first, last)
    body = []
    for c, col in enumerate(cols):
        if len(col) > MAXL:
            col = col[:MAXL - 1] + [("  …", "")]
        for i, (t, blk) in enumerate(col):
            y = ytop + i * LH
            emph = blk == "conf" and "threshold" in t
            body.append(_mono_line(X0 + 26 + c * CW, y, _yaml_runs(t, emph), FS))
            if blk:
                c0, a0, b0 = spans.get(blk, (c, i, i))
                spans[blk] = (c0, min(a0, i), max(b0, i)) if c0 == c else (c0, a0, b0)
    # annotation bands (under the text)
    NOTES = [("art", "Artefactos, con su digest"), ("life", "Ciclo de vida: cómo arranca"),
             ("conf", "El umbral es configuración"), ("ipc", "Permisos IPC: qué publica")]
    for k, (blk, _) in enumerate(NOTES):
        if blk not in spans:
            continue
        c, a, b = spans[blk]
        x = X0 + 12 + c * CW
        y = ytop + a * LH - 17
        h = (b - a) * LH + 25
        o.append(G(k + 1, R(x, y, CW - 24, h, fill=mix(PURPLE, WHITE, .9), rx=6) +
                   R(x, y, 5, h, fill=PURPLE, rx=2) +
                   f'<circle cx="{x + CW - 46:.1f}" cy="{y + 15:.1f}" r="14" fill="{PURPLE}"/>' +
                   T(x + CW - 46, y + 21, str(k + 1), 18, WHITE, 700, "middle")))
    o.extend(body)
    # legend: one annotation per click
    for k, (blk, txt) in enumerate(NOTES):
        x = X0 + k * (W / 4)
        o.append(G(k + 1, f'<circle cx="{x + 16:.1f}" cy="{Y0 + H + 52:.1f}" r="15" fill="{PURPLE}"/>' +
                   T(x + 16, Y0 + H + 58, str(k + 1), 18, WHITE, 700, "middle") +
                   T(x + 42, Y0 + H + 59, txt, 21, NAVY, 700)))
    return wrap("".join(o))


# ─────────────────────────────────────────────────────────────────────
#  step 5 · what keeps working offline, on the device
# ─────────────────────────────────────────────────────────────────────
def _g_queue(x, y, s=52):
    o = [R(x, y + s * .55, s, s * .22, fill=S300, rx=3)]
    for k in range(4):
        o.append(R(x + 3 + k * (s - 6) / 4, y + s * .28, (s - 6) / 4 - 3, (s - 6) / 4 - 3, fill=CYAN, rx=2))
    return "".join(o)


def fig_offline(static=False):
    """Step 5 · one device keeps listening without network: the local queue, stream manager and nucleus lite.
    (Outposts with local EKS, for a station that is a whole plant, left the slide: it is in the hard questions.)"""
    o = []
    Y0, H, X, W = 268, 300, 96, 1408
    rows = [(_g_queue, "Cola local", ["el nucleus guarda los eventos", "hasta que vuelve la red"]),
            ("stream_manager", "Stream manager", ["flujos locales que suben", "solos cuando hay red"]),
            ("gg_nucleus", "Nucleus lite", ["el agente en C, para equipos", "con muy poca memoria"])]
    b = [R(X, Y0, W, H, fill=WHITE, stroke=PURPLE, sw=2, rx=12)]
    b.append(icon("greengrass", X + 32, Y0 + 30, 60))
    b.append(T(X + 110, Y0 + 60, "IoT Greengrass", 30, NAVY, 700))
    b.append(T(X + 110, Y0 + 88, "en el equipo de cada bomba", 20, SLATE))
    b.append(L([(X + 32, Y0 + 120), (X + W - 32, Y0 + 120)], LINE, 1.5))
    cw = (W - 64) / 3
    for j, (g, t, d) in enumerate(rows):
        x = X + 32 + j * cw
        b.append(g(x, Y0 + 150, 56) if callable(g) else icon(g, x, Y0 + 150, 56))
        b.append(T(x + 76, Y0 + 176, t, 26, NAVY, 700))
        for i, line in enumerate(d):
            b.append(T(x + 76, Y0 + 210 + i * 28, line, 20, SLATE))
    o.append(G(0, "".join(b)))
    return wrap("".join(o))


# ─────────────────────────────────────────────────────────────────────
#  step 6 · what you see from the cloud: the signal pipeline, one step per click
# ─────────────────────────────────────────────────────────────────────
CLOUD_DIR = _os.path.join(_os.path.dirname(RECIPE), _os.pardir, "cloud")


def _cloud_facts():
    """The SQL rule, the MissedFaults filter and the names, read from poc-devopsdays/cloud/.
    If they are not there, the planned ones (same text that setup.sh deploys)."""
    import glob, re
    f = {"sql": "SELECT *, timestamp() AS arrived_ts FROM 'station/events'",
         "filter": '{ ($.truth = "anomaly") && ($.alert IS FALSE) }',
         "RULE": "station_events", "LOG_GROUP": "/station/events", "ALARM": "station-missed-faults",
         "FN": "station-rollback", "TOPIC": "station/events", "real": False}
    try:
        txt = ""
        for p in sorted(glob.glob(_os.path.join(CLOUD_DIR, "*"))):
            if p.endswith((".sh", ".json", ".py")):
                txt += open(p, encoding="utf-8").read() + "\n"
        m = re.search(r'"sql"\s*:\s*"([^"]+)"', txt)
        if m:
            f["sql"], f["real"] = m.group(1), True
        m = re.search(r"MissedFaults\s+'(\{[^']*\})'", txt) or \
            re.search(r"--filter-pattern\s+'(\{[^']*truth[^']*\})'", txt)
        if m:
            f["filter"] = m.group(1)
        for k in ("RULE", "LOG_GROUP", "ALARM", "FN"):
            m = re.search(r'^%s="([^"$]+)"' % k, txt, re.M)
            if m:
                f[k] = m.group(1)
        m = re.search(r"FROM\s+'([^']+)'", f["sql"])
        if m:
            f["TOPIC"] = m.group(1)
    except Exception as e:                               # noqa: BLE001
        print(f"  (warning) monitoring: could not read cloud/ ({e}); using the planned names", file=sys.stderr)
    return f


def fig_monitoring(static=False):
    """Step 6 · the pipeline the event travels (all at once), then the three signals to watch, one per click:
    input (input_z), output (score distribution, PSI) and authenticity (sha256). None of them needs labels."""
    f = _cloud_facts()
    nodes = [("iotcore", "IoT Core", f["TOPIC"]),
             ("iot_rule", "Regla de IoT", f["RULE"]),
             ("cw_logs", "CloudWatch Logs", f["LOG_GROUP"]),
             ("cloudwatch", "Filtro de métrica", "MissedFaults"),
             ("cw_alarm", "Alarma", f["ALARM"]),
             ("lambda", "Lambda", f["FN"])]
    X = [172 + k * 248 for k in range(6)]
    YI = 262
    o, b = [], []
    for k, (ic, t, sub) in enumerate(nodes):
        if k:
            b.append(L([(X[k - 1] + 40, YI), (X[k] - 40, YI)], PURPLE if k >= 4 else NAVY, 2.2, head=9))
        b.append(icon(ic, X[k] - 26, YI - 26, 52))
        b.append(T(X[k], YI + 54, t, 20, NAVY, 700, "middle"))
        b.append(T(X[k], YI + 78, sub, 16, PURPLE if k >= 3 else SLATE, 700, "middle", MONO,
                   extra='letter-spacing="-0.6"'))
    o.append(G(0, "".join(b)))

    Y0, H, gap = 384, 214, 32
    cw = (1408 - 2 * gap) / 3
    cards = [("ENTRADA · input_z", "¿El sensor dice la verdad?",
              ["Sube lento: el micrófono envejece.", "Salta de golpe: falla o alguien lo tocó."]),
             ("SALIDA · score", "¿Cambió lo que decide?",
              ["PSI de los scores: esta hora", "contra la semana. Si salta, algo pasa."]),
             ("AUTENTICIDAD · sha256", "¿Es el modelo que enviamos?",
              ["La huella que reporta el equipo,", "contra la del registro."])]
    for k, (kick, head, lines) in enumerate(cards):
        x = 96 + k * (cw + gap)
        b = [R(x, Y0, cw, H, fill=WHITE, stroke=PURPLE if k == 2 else LINE, sw=2 if k == 2 else 1.6, rx=12)]
        b.append(T(x + 26, Y0 + 38, kick, 17, PURPLE, 700, family=MONO, extra='letter-spacing="1"'))
        b.append(T(x + 26, Y0 + 84, head, 27, NAVY, 700))
        for j, ln in enumerate(lines):
            b.append(T(x + 26, Y0 + 132 + j * 30, ln, 20, SLATE))
        gx, gy = x + cw - 130, Y0 + 18                    # a small glyph, top right
        if k == 0:                                          # slow drift, then a jump
            pts = [(gx + i * 9, gy + 34 - i * 1.4) for i in range(9)] + [(gx + 80, gy + 22), (gx + 80, gy + 4), (gx + 104, gy + 4)]
            b.append(L(pts, PURPLE, 2.6))
        elif k == 1:                                        # two histograms: the week and this hour, shifted
            for i, (h1, h2) in enumerate([(8, 4), (18, 8), (26, 16), (16, 26), (6, 18)]):
                b.append(R(gx + i * 21, gy + 38 - h1, 8, h1, fill=S300, rx=1))
                b.append(R(gx + i * 21 + 9, gy + 38 - h2, 8, h2, fill=PURPLE, rx=1))
        else:                                               # the fingerprint matches: a seal with a check
            b.append(f'<circle cx="{gx + 84}" cy="{gy + 20}" r="19" fill="none" stroke="{PURPLE}" stroke-width="2.6"/>')
            b.append(check(gx + 84, gy + 20))
        o.append(G(k + 1, "".join(b)))
    return wrap("".join(o))


# ─────────────────────────────────────────────────────────────────────
#  each pump's wave (slide 2): real envelope of the WAV, 640 × 160
# ─────────────────────────────────────────────────────────────────────
_HERE = _os.path.dirname(_os.path.abspath(__file__))
AUDIO_DIR = _os.environ.get("STATION_AUDIO_DIR", _os.path.join(_os.path.dirname(_HERE), "assets", "audio"))


def envelope(path, n=128):
    """Peak per chunk, normalized to 1. None if the file is missing or unreadable."""
    try:
        import wave
        import numpy as np
        with wave.open(path, "rb") as w:
            ch, sw, fr = w.getnchannels(), w.getsampwidth(), w.getnframes()
            raw = w.readframes(fr)
        dt = {1: np.uint8, 2: np.int16, 4: np.int32}[sw]
        x = np.frombuffer(raw, dtype=dt).astype(np.float64)
        if sw == 1:
            x -= 128
        if ch > 1:
            x = x.reshape(-1, ch).mean(axis=1)
        if len(x) < n:
            return None
        x = x[: len(x) // n * n].reshape(n, -1)
        e = np.abs(x).max(axis=1)
        top = e.max()
        return list(e / top) if top > 0 else None
    except Exception:                                    # noqa: BLE001
        return None


def fig_wave(which, static=False):
    W, H, n = 640, 160, 128
    env = envelope(_os.path.join(AUDIO_DIR, f"pump-{which}.wav"), n)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" class="onda" '
         f'data-pump="{which}">']
    if env is None:
        o.append(L([(24, H / 2), (W / 2 - 100, H / 2)], S400, 3, "2 7"))
        o.append(L([(W / 2 + 100, H / 2), (W - 24, H / 2)], S400, 3, "2 7"))
        o.append(T(W / 2, H / 2 + 7, "audio pendiente", 20, MUTED, 400, "middle"))
    else:
        pitch = W / n
        o.append('<g class="bars">')
        for k, v in enumerate(env):
            h = max(2.0, v * (H - 16))
            o.append(f'<rect x="{k * pitch + .6:.1f}" y="{(H - h) / 2:.1f}" width="{pitch * .62:.1f}" height="{h:.1f}" '
                     f'rx="1.2" fill="{NAVY}"/>')
        o.append('</g>')
    o.append("</svg>")
    return "".join(o)


# ─────────────────────────────────────────────────────────────────────
#  the spine: the six steps (divider 03 and footer bar of slides 18–24)
# ─────────────────────────────────────────────────────────────────────
STEPS = [("Entrenar", "SageMaker AI · S3"), ("Optimizar", "un artefacto por chip"),
         ("Empaquetar", "componente Greengrass"), ("Desplegar", "rings · thing groups"),
         ("Operar sin red", "cola local"), ("Monitorear", "IoT Core · CloudWatch")]


def fig_spine(static=False):
    """Six big boxes, at the bottom of divider 03 (keeps the number and title area clear)."""
    o, gap = [], 20
    w = (1432 - 5 * gap) / 6
    y, h = 652, 118
    for k, (t, sub) in enumerate(STEPS):
        x = 84 + k * (w + gap)
        b = [R(x, y, w, h, fill=WHITE, stroke=PURPLE if k == 0 else LINE, sw=2, rx=12)]
        b.append(T(x + 20, y + 36, f"0{k + 1}", 20, PURPLE, 700, family=MONO))
        b.append(T(x + 20, y + 74, t, 29, NAVY, 700))
        b.append(T(x + 20, y + 102, sub, 18, SLATE))
        if k < 5:
            b.append(L([(x + w + 3, y + h / 2), (x + w + gap - 3, y + h / 2)], PURPLE, 2.2, head=7))
        o.append(f'<g a="4">{"".join(b)}</g>')
    return wrap("".join(o))


def fig_spine_n(n, static=False):
    """1432 × 44 footer bar with step n highlighted. Goes at x = 84, above the template footer."""
    W, H, k0 = 1432, 44, 12
    w = W / 6
    o = []
    for k, (t, _) in enumerate(STEPS):
        x0, x1 = k * w, (k + 1) * w - 4
        pts = [(x0, 0), (x1 - k0, 0), (x1, H / 2), (x1 - k0, H), (x0, H)]
        if k:
            pts.append((x0 + k0, H / 2))
        if k + 1 == n:
            fill, stroke, col, wt = PURPLE, PURPLE, WHITE, 700
        elif k + 1 < n:
            fill, stroke, col, wt = LIGHT, LINE, NAVY, 400
        else:
            fill, stroke, col, wt = WHITE, LINE, MUTED, 400
        d = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
        o.append(f'<polygon points="{d}" fill="{fill}" stroke="{stroke}" stroke-width="1.5" stroke-linejoin="round"/>')
        tx = x0 + (k0 if k else 0) + 18
        o.append(T(tx, 29, str(k + 1), 19, PURPLE if k + 1 != n else WHITE, 700, family=MONO))
        o.append(T(tx + 24, 29, t, 19, col, wt))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" class="espina">'
            + "".join(o) + "</svg>")


def _arch(mode):
    """AWS architecture (build_arch.py), as an "arq lay-a" layer for <div class="stack">."""
    from build_arch import deck_layer
    return deck_layer(mode)


# keys = figure names used in deck.src.html as {{FIG:name}} (mostly the slide ids, kept as they are)
FIGS = {"optimizar": fig_optimize, "pasaporte": fig_passport, "anillos": fig_rings,
        "drift": fig_drift, "medir": fig_measure, "espina": fig_spine,
        "entrenar": fig_train, "receta": fig_recipe, "sinred": fig_offline,
        "monitoreo": fig_monitoring,
        "arq_ref": lambda static=False: _arch("ref"), "arq_poc": lambda static=False: _arch("poc"),
        "seq": lambda static=False: __import__("build_seq").build(static),
        "onda_a": lambda static=False: fig_wave("a", static), "onda_b": lambda static=False: fig_wave("b", static)}
for _n in range(1, 7):
    FIGS[f"espina_{_n}"] = (lambda n: lambda static=False: fig_spine_n(n, static))(_n)

if __name__ == "__main__":
    print("sample PSI:", round(psi(EXP, ACT), 3))
