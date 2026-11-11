"""
Builds talk/techdaycali.html: the Tech Day Cali deck, one self-contained HTML file (it works offline).

It looks like the event's template (its backgrounds, the bird, the logo, Montserrat, the palette)
because it uses the template's own pieces (talk/assets/cali/tdc/). Each slide is a 960 × 540 stage,
scaled to the screen; coordinates are those of the template (points). The figures are inline SVG
(figs.py, build_arch.py); the spectrograms and the QR are PNG. The speaker notes come from
GUION-techdaycali.md, by the id of each section.

Keys: → ↓ espacio PageDown Enter (the clicker) next · ← ↑ PageUp back · Home/End · A annexes · M or
Esc back to the talk · B or . black screen · N notes · P presenter window · F full screen.

Usage (render.sh runs it):  python3 build_html.py
"""
import base64, html, json, mimetypes, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
TALK = os.path.abspath(os.path.join(HERE, "..", ".."))
B = os.path.join(HERE, "build")
TDC = os.path.join(TALK, "assets", "cali", "tdc")
OUT = os.path.join(TALK, "techdaycali.html")
GUION = os.path.join(TALK, "GUION-techdaycali.md")

NAVY, GREEN, YELLOW, ORANGE, TEAL = "#0B132A", "#12D18E", "#FFC700", "#FF5A1F", "#1F8F7A"
SLATE, WHITE, MIST, PALE = "#5C6B85", "#FFFFFF", "#AAB6CB", "#EAF0F8"
REPO = "github.com/alejandro945/mlops-a-ciegas"
LINKEDIN = "linkedin.com/in/alejandro-varela-fr"

ASSETS = {}          # path → (CSS class, natural width, natural height): each image goes in the page once


def uri(path):
    """An image, registered once: the slides use it through a CSS class."""
    if path not in ASSETS:
        from PIL import Image
        w, h = Image.open(path).size
        ASSETS[path] = (f"a{len(ASSETS)}", w, h)
    return path


def tdc(name):
    return uri(os.path.join(TDC, name))


def jpeg(path, quality=85):
    """A screenshot without transparency, as a JPEG in build/ (a fraction of the PNG's weight)."""
    from PIL import Image
    out = os.path.join(B, "png", os.path.splitext(os.path.basename(path))[0] + ".jpg")
    Image.open(path).convert("RGB").save(out, quality=quality)
    return out


def data_uri(path):
    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()


def figsvg(name):
    s = open(os.path.join(B, "svg", name + ".svg"), encoding="utf-8").read()
    return re.sub(r'<svg\b([^>]*?)\swidth="[\d.]+"\s+height="[\d.]+"', r'<svg\1 width="100%"', s, count=1)


# ── notes from the script ─────────────────────────────────────────────
def notes_by_id():
    text = open(GUION, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"<!-- id: ([\w-]+) -->", text):
        end = re.search(r"\n(?:---|#{1,2} )", text[m.end():])
        part = text[m.end(): m.end() + end.start()] if end else text[m.end():]
        if True:
            body = part.strip()
            body = re.sub(r"\*\*([^*]+)\*\*", r"\1", body)
            out[m.group(1)] = re.sub(r"\*([^*]+)\*", r"\1", body)
    return out


NOTES = notes_by_id()


# ── the pieces of a slide (coordinates in template points) ───────────
def T(x, y, w, inner, size=16, color=NAVY, weight=500, align="left", lh=1.2, extra=""):
    return (f'<div class="t" style="left:{x}px;top:{y}px;width:{w}px;font-size:{size}px;color:{color};'
            f'font-weight:{weight};text-align:{align};line-height:{lh};{extra}">{inner}</div>')


def b(s, color=None, weight=700):
    c = f"color:{color};" if color else ""
    return f'<b style="{c}font-weight:{weight}">{s}</b>'


def IMG(src, x, y, w=None, h=None, extra=""):
    cls, nw, nh = ASSETS[src]
    if w and not h:
        h = w * nh / nw
    elif h and not w:
        w = h * nw / nh
    return (f'<div class="i {cls}" style="left:{x}px;top:{y}px;width:{w:.1f}px;height:{h:.1f}px;'
            f'background-size:100% 100%;{extra}"></div>')


def COVER(src, x, y, w, h, pos="center"):
    cls = ASSETS[src][0]
    return (f'<div class="i {cls}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;'
            f'background-size:cover;background-position:{pos}"></div>')


def FIG(name, x, y, w):
    return f'<div class="f" style="left:{x}px;top:{y}px;width:{w}px">{figsvg(name)}</div>'


def R(x, y, w, h, fill="none", line=None, radius=14, extra=""):
    bd = f"border:1.5px solid {line};" if line else ""
    return (f'<div class="r" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;background:{fill};{bd}'
            f'border-radius:{radius}px;{extra}"></div>')


def TRI(x, y, s, color, rot=0):
    return (f'<div class="r" style="left:{x}px;top:{y}px;width:0;height:0;border-left:{s / 2}px solid transparent;'
            f'border-right:{s / 2}px solid transparent;border-bottom:{s}px solid {color};transform:rotate({rot}deg)"></div>')


def KICK(s, dark=False, y=36):
    return T(50, y, 700, s, 12, GREEN if dark else ORANGE, 700, extra="letter-spacing:1.6px")


def TITLE(s, dark=False, y=44, size=34, w=800):
    return f'<h2 class="t" style="left:50px;top:{y}px;width:{w}px;font-size:{size}px;color:{WHITE if dark else NAVY}">{s}</h2>'


def CLOCK(t):
    return (T(700, 30, 210, t, 22, GREEN, 800, "right") +
            T(700, 58, 210, "una noche en la planta", 10, MIST, 500, "right"))


def CAP(x, y, w, s, color=SLATE, size=13):
    return T(x, y, w, s, size, color, 500)


# backgrounds and the template's fixed pieces
def BG_LIGHT():
    return f'<div class="bg {ASSETS[tdc("fondo-contenido.jpg")][0]}"></div>'


def BG_DARK():
    return f'<div class="bg {ASSETS[tdc("fondo-oscuro.jpg")][0]}"></div>'


def BG_BIRD():
    return (f'<div class="bg {ASSETS[tdc("fondo-claro.jpg")][0]}"></div>' +
            IMG(tdc("pluma.png"), 853, 19, 85) + IMG(tdc("logo-navy.png"), 50, 464, 58) +
            R(0, 506, 63, 2, GREEN, radius=0))


def spectros(x, y, w, h, ink, marked=False, size=18, gap=None):
    """The two spectrograms of the opening question, side by side, with their labels."""
    gap = gap if gap is not None else w * .074
    out = ""
    for k, (lab, f) in enumerate((("Bomba A", "espectro-a"), ("Bomba B", "espectro-b-marcado" if marked else "espectro-b"))):
        xx = x + k * (w + gap)
        out += T(xx, y, w, lab, size, ink, 800, "center")
        out += IMG(uri(os.path.join(B, "png", f + ".jpg")), xx, y + size * 1.6, w, h)
    return out


SLIDES = []


def slide(sid, title, body, kind="light", annex=False, num=True):
    bg = {"light": BG_LIGHT, "dark": BG_DARK, "bird": BG_BIRD}.get(kind, lambda: "")()
    n = len([s for s in SLIDES if not s["annex"]]) + 1
    numtag = "" if not num or kind != "light" else T(864, 496, 43, str(n), 11, WHITE, 600, "right", extra="opacity:.75")
    SLIDES.append({"id": sid, "title": title, "annex": annex, "kind": kind,
                   "html": bg + body + numtag, "notes": NOTES.get(sid, "")})


# ═════════════════════════════ I · EL OÍDO ═══════════════════════════
slide("portada", "MLOps a ciegas", (
    f'<div class="bg {ASSETS[tdc("fondo-portada.jpg")][0]}"></div>' +
    R(450, 0, 1.2, 97, "#3A4A72", radius=0) + R(475, 25, 1.2, 50, "#3A4A72", radius=0) + R(504, 0, 1.2, 115, "#3A4A72", radius=0) +
    R(0, 124, 77, 1.5, GREEN, radius=0) +
    IMG(tdc("logo-blanco.png"), 50, 40, 115) + T(54, 144, 200, "21 NOV 2026", 13, WHITE, 700) +
    T(619, 46, 292, "TECHDAYCALI.COM", 13, WHITE, 500, "right") +
    IMG(tdc("pajaro-vuela.png"), 608, 155, 295) +
    TRI(886, 112, 28, ORANGE, 20) + TRI(569, 166, 22, GREEN, -30) + TRI(578, 412, 30, YELLOW, 10) +
    f'<h1 class="t" style="left:54px;top:216px;width:520px;font-size:48px;color:{WHITE}">MLOps a ciegas</h1>' +
    T(54, 282, 470, "Gobernar modelos de IA que se ejecutan donde no llega el plano de control", 17, WHITE, 500) +
    T(54, 367, 468, "Alejandro Varela Franco", 20, YELLOW, 700) +
    T(54, 400, 468, "Senior Cloud Engineer · EPAM", 15, WHITE, 500) +
    T(54, 488, 600, "Sábado, Nov 21, 2026 &nbsp;|&nbsp; Universidad Autónoma de Occidente", 11, WHITE, 500)), kind="none")

slide("mecanico", "“Esta va a fallar”", (
    f'<div class="bg {ASSETS[tdc("fondo-claro.jpg")][0]}"></div>' +
    IMG(tdc("logo-navy.png"), 50, 464, 58) + R(0, 506, 63, 2, GREEN, radius=0) +
    COVER(uri(os.path.join(TALK, "assets", "cali", "mecanico.jpg")), 504, 0, 456, 540) +
    T(512, 524, 300, "Foto: Mike Newbry · Unsplash", 7, WHITE, 500) +
    TITLE("“Esta va a fallar”", size=36, w=420) +
    T(50, 150, 410, "En cada planta hay alguien que pone la mano en la bomba, escucha unos segundos… " +
      b("y casi nunca se equivoca."), 17, NAVY, 500, lh=1.35) +
    T(50, 250, 410, "11 %", 64, ORANGE, 800) +
    CAP(50, 330, 400, "de los ingresos de las 500 empresas más grandes del mundo se va en paros que nadie vio venir · Siemens, 2024")),
    kind="none")

slide("espectros", "¿Cuál está fallando?", (
    TITLE("¿Cuál está fallando?") + spectros(60, 112, 405, 278, NAVY) +
    CAP(60, 455, 840, "La “foto” del sonido de dos bombas reales. Una está sana; la otra empieza a fallar.", NAVY, 15)))

slide("quien", "Sobre mí", (
    f'<div class="bg {ASSETS[tdc("fondo-speaker.jpg")][0]}"></div>' +
    R(90, 90, 310, 382, "none", GREEN, 0) +
    COVER(uri(os.path.join(TALK, "assets", "photo.jpeg")), 68, 68, 310, 382, "center top") +
    TRI(356, 40, 34, YELLOW, 15) + TRI(40, 428, 31, ORANGE, -20) + TRI(389, 450, 19, "#1ED4E8", 40) +
    IMG(tdc("pajaro-parado.png"), 824, 371, 104) +
    T(454, 70, 360, "SOBRE EL SPEAKER", 12, GREEN, 700, extra="letter-spacing:1.6px") +
    T(454, 101, 454, "Alejandro Varela Franco", 30, WHITE, 800) +
    T(454, 160, 454, "Senior Cloud Engineer · EPAM", 16, YELLOW, 700) +
    T(454, 205, 420, "Diseño cómo llegan y se gobiernan modelos de IA en equipos de campo: inferencia en el edge e IoT "
      "industrial sobre AWS, Azure y GCP.", 15, WHITE, 500, lh=1.4) +
    T(454, 300, 420, "Cinco certificaciones de AWS y tres de Kubernetes.", 15, WHITE, 500, lh=1.4) +
    T(454, 410, 360, f"{LINKEDIN}<br>github.com/alejandro945", 13, WHITE, 500, lh=1.5)), kind="none")

slide("mil", "Una persona, mil bombas", (
    TITLE("Una persona, mil bombas") + FIG("mil", 80, 120, 800) +
    T(80, 432, 800, "Y algún día se pensiona. " + b("¿Cómo se copia un oído?", ORANGE), 18)))

slide("cerebro", "Su cerebro ignora lo normal", (
    TITLE("Su cerebro ignora lo normal") + FIG("bombillo", 80, 150, 140) +
    T(240, 160, 320, "20 W", 96, NAVY, 800, lh=1) +
    CAP(246, 268, 300, "lo que gasta su cerebro ahora mismo: un bombillo", SLATE, 15) +
    T(560, 150, 360, "¿Sentían la ropa que tienen puesta… " + b("antes de que la nombrara?") +
      "<br><br>No procesa lo de siempre: reacciona a lo que no esperaba.<br><br>" +
      b("El oído del mecánico hace lo mismo.", ORANGE), 18, NAVY, 500, lh=1.35)))

slide("noesgenai", "No toda IA conversa", (
    TITLE("No toda IA conversa") +
    R(50, 130, 405, 240, "none", NAVY) +
    T(74, 150, 360, b("IA que conversa", SLATE) + "<br>" + f'<span style="font-size:24px;font-weight:800">ChatGPT y sus primos</span>'
      "<br><br>Miles de millones de parámetros<br>Gigabytes de modelo<br>Vive en centros de datos enormes", 18, NAVY, 500, lh=1.45) +
    R(505, 130, 405, 240, GREEN) +
    T(529, 150, 360, b("Machine learning tradicional") + "<br>" + '<span style="font-size:24px;font-weight:800">El oído de esta charla</span>'
      "<br><br>464 KB: menos que una foto<br>Decide en milisegundos, sin internet<br>Una sola tarea: notar lo raro", 18, NAVY, 500, lh=1.45) +
    T(50, 395, 860, b("MLOps: ", ORANGE) + "llevar un modelo a producción y operarlo como cualquier software: versiones, "
      "despliegues, monitoreo y vuelta atrás.", 15)))


def steps3():
    out = ""
    for k, (n, a, s) in enumerate((("1", "Solo sonido sano", "nunca le mostramos una falla"),
                                   ("2", "Intenta predecir", "cada clip que escucha"),
                                   ("3", "Si no puede, avisa", "sube el puntaje de rareza"))):
        y = 140 + k * 95
        out += R(50, y, 40, 40, ORANGE if k == 2 else NAVY, radius=8)
        out += T(50, y + 8, 40, n, 18, WHITE, 800, "center")
        out += T(104, y, 200, b(a) + f'<br><span style="font-size:13px;color:{SLATE}">{s}</span>', 16, NAVY, 500, lh=1.35)
    return out


slide("oido", "Así se copia un oído", (
    TITLE("Así se copia un oído") + steps3() + FIG("puntaje", 318, 120, 600) +
    CAP(320, 455, 600, "Datos reales de la noche del ensayo: la bomba 3, clip por clip.", SLATE, 12)))

# ═════════════════════════════ II · EL VIAJE ═════════════════════════
slide("nube", "¿Y por qué no mandamos todo a la nube?", (
    TITLE("¿Y por qué no mandamos todo a la nube?", size=30) +
    IMG(uri(jpeg(os.path.join(TALK, "assets", "screens", "gancho-camas.png"))), 50, 110, h=210) +
    IMG(uri(os.path.join(TALK, "assets", "screens", "gancho-internet.png")), 400, 110, h=210) +
    T(590, 120, 330, b("Octubre de 2025", ORANGE) + '<br><span style="font-size:16px;font-weight:700">Se cae una región de AWS en '
      'Estados Unidos.</span><br><br>Unas camas de dos mil dólares que pensaban desde la nube se quedan calientes e inclinadas, '
      'con sus dueños encima.', 14, NAVY, 500, lh=1.35) +
    FIG("cuenta", 50, 350, 560) +
    CAP(50, 498, 560, "Meme basado en xkcd 2347 «Dependency» (CC BY-NC 2.5)", SLATE, 8)))


def cards(items, y, h, w=260, gap=280, x0=70, first_dark=False, big=None):
    out = ""
    for k, item in enumerate(items):
        x = x0 + k * gap
        dark = first_dark and k == 0
        out += R(x, y, w, h, NAVY if dark else PALE)
        ink, sub = (WHITE, MIST) if dark else (NAVY, SLATE)
        if big:
            n, a, s = item
            out += T(x + 20, y + 18, w - 40, n, 46, YELLOW if dark else NAVY, 800, lh=1)
            out += T(x + 20, y + 100, w - 40, b(a) + f'<br><span style="font-size:12px;color:{sub}">{s}</span>', 15, ink, 500, lh=1.35)
        else:
            a, s = item
            out += T(x + 16, y + 12, w - 32, b(a) + f'<br><span style="font-size:12px;color:{sub}">{s}</span>', 15, ink, 500, lh=1.35)
    return out


slide("pendulo", "El péndulo vuelve", (
    TITLE("El péndulo vuelve") + FIG("pendulo", 70, 108, 820) +
    cards((("Face ID", "su cara no sale del teléfono"), ("55 % de los PC", "de 2026 traen chip de IA · Gartner"),
           ("Arduino UNO Q", "detecta sonidos raros sin internet")), 395, 70)))

slide("colombia", "Aquí la red no siempre llega", (
    TITLE("Aquí la red no siempre llega") +
    cards((("4 de 10", "hogares rurales en Colombia", "siguen sin internet · DANE, 2025"),
           ("14", "estaciones de la red de Cenicaña", "cubren ≈ 85 % de la zona cañera"),
           ("16 km", "alcance récord de Wi-Fi HaLow", "meses con una batería de botón")), 130, 210, w=270, gap=290,
          x0=50, first_dark=True, big=True) +
    T(50, 370, 860, "Una red mejor no resuelve el problema: " + b("significa más oídos, más lejos, decidiendo solos.", ORANGE), 18)))

slide("maleta", "Hábito 1 · Que quepa en la maleta", (
    KICK("HÁBITO 1") + TITLE("Que quepa en la maleta", y=56) + FIG("maleta", 60, 150, 700) +
    T(60, 400, 820, b("98 %", GREEN, 800).replace("font-weight:800", "font-weight:800;font-size:30px") +
      " &nbsp;de las decisiones, idénticas al modelo original", 18)))

slide("ciegas", "Y ahí nos quedamos a ciegas", (
    TITLE("Y ahí nos quedamos a ciegas") + FIG("ciegas", 50, 110, 860) +
    T(50, 440, 860, "El software puede estar perfecto " + b("y el oído, equivocado.", ORANGE), 20)))

# ═════════════════════════ III · UNA NOCHE EN LA PLANTA ══════════════
slide("aws", "Lo montamos de verdad", (
    KICK("LA PRUEBA") + TITLE("Lo montamos de verdad", y=56) + FIG("arch-poc", 60, 104, 840) +
    CAP(60, 510, 840, "Cinco bombas en contenedores con el agente real de AWS IoT Greengrass · audio real de bombas "
        "(MIMII DUE, Hitachi) · Terraform", SLATE, 10)))

slide("acto1", "7:58 p.m. · La bomba 3 empieza a fallar", (
    CLOCK("7:58 p.m.") + TITLE("La bomba 3 empieza a fallar", dark=True) + FIG("acto1", 50, 120, 860) +
    spectros(50, 286, 252, 168, WHITE, marked=True, size=13) +
    T(600, 300, 320, b("En ese mismo clip: alerta.", ORANGE).replace("font-weight:700", "font-weight:800;font-size:20px") +
      "<br><br>Era la B. El oído notó esta zona, que en la bomba sana no existe.", 16, WHITE, 500, lh=1.4)), kind="dark")

slide("lotes", "Hábito 2 · Lo urgente ya, lo pesado después", (
    KICK("HÁBITO 2") + TITLE("Lo urgente ya, lo pesado después", y=56) + FIG("lotes", 50, 130, 860) +
    CAP(50, 412, 860, "Como WhatsApp: el mensaje sale al instante; el video, cuando hay wifi.", NAVY, 16)))

slide("acto2", "7:59 p.m. · Se fue la red", (
    CLOCK("7:59 p.m.") + TITLE("Se fue la red", dark=True) + FIG("acto2", 50, 112, 860) +
    T(50, 412, 860, "45 s sin red → " + b("0 reportes perdidos", GREEN), 26, WHITE, 800) +
    CAP(50, 458, 860, "La bomba 3 siguió decidiendo sola y entregó todo al volver. Las otras cuatro, ni se enteraron.", MIST, 14)),
    kind="dark")


def questions():
    out = ""
    for k, (q, s) in enumerate((("¿Lo que entra se parece a lo que aprendió?", "el micrófono, el ambiente, la velocidad"),
                                ("¿Lo que decide cambió?", "alerta mucho más, o mucho menos"),
                                ("¿Es la versión que mandamos?", "la huella del modelo"))):
        y = 140 + k * 92
        out += R(50, y, 6, 64, ORANGE if k == 0 else NAVY, radius=0)
        out += T(70, y, 330, b(q) + f'<br><span style="font-size:12px;color:{SLATE}">{s}</span>', 16, NAVY, 500, lh=1.35)
    return out


slide("senales", "Hábito 3 · Escuchar al que escucha", (
    KICK("HÁBITO 3") + TITLE("Escuchar al que escucha", y=56) + questions() + FIG("entrada", 420, 130, 500) +
    CAP(420, 330, 500, "Bomba 5, la misma noche: cero errores del software… y alertas que no eran fallas. "
                       "La entrada explicaba por qué: el mundo cambió.", NAVY, 13)))

slide("masaudio", "“Teníamos más audio…”", (
    TITLE("“Teníamos más audio…”", y=170, size=44, w=760) +
    T(50, 262, 760, "Más datos, mejor modelo, ¿cierto?", 24, SLATE, 500)), kind="bird")

slide("sordo", "El oído “mejorado” estaba sordo", (
    KICK("LA VERSIÓN 2, EN SOMBRA", dark=True) + TITLE("El oído “mejorado” estaba sordo", dark=True, y=56) +
    FIG("sordo", 50, 130, 860) +
    T(50, 380, 860, "El audio extra traía una bomba que ya venía fallando: aprendió que fallar es lo normal.", 17, WHITE, 500) +
    T(50, 420, 860, "No es un bug de código. Es un bug de datos.", 22, ORANGE, 800)), kind="dark")

slide("juez", "Hábito 4 · Nadie decide sin un juez", (
    KICK("HÁBITO 4") + TITLE("Nadie decide sin un juez", y=56) + FIG("juez", 50, 112, 860) +
    T(50, 430, 760, "La versión mala nunca decidió.", 22, ORANGE, 800) +
    T(50, 462, 700, "La plataforma revierte instalaciones fallidas, no modelos equivocados. Ese juez lo pone uno.", 14)))

slide("arreglo", "Cómo se arregla un oído sordo", (
    TITLE("Cómo se arregla un oído sordo") + FIG("arreglo", 120, 110, 720) +
    T(50, 455, 860, "No con más datos: " + b("con los datos correctos.", GREEN), 20, NAVY, 500, "center")))

# ═════════════════════════════ CIERRE ════════════════════════════════
three = ""
for k, (a, s) in enumerate((("Decidan donde nace el dato", "y manden solo lo diferente"),
                            ("Ninguna versión nueva decide sin un juez", "en sombra primero, en una sola"),
                            ("Escuchen al que escucha", "no basta con que el equipo esté prendido"))):
    y = 140 + k * 100
    three += T(50, y - 10, 70, str(k + 1), 56, ORANGE, 800, lh=1)
    three += T(130, y, 760, b(a, NAVY, 800) + f'<br><span style="font-size:15px;color:{SLATE}">{s}</span>', 24, NAVY, 500, lh=1.35)
slide("tres", "Tres ideas para llevarse", TITLE("Tres ideas para llevarse") + three)

slide("final", "¿El que escucha está fallando?", (
    COVER(uri(os.path.join(TALK, "assets", "cali", "mecanico.jpg")), 504, 0, 456, 540) +
    T(50, 90, 420, "Empezamos preguntando si la bomba está fallando.", 17, MIST, 500) +
    T(50, 170, 440, "¿El que escucha<br>" + b("está fallando?", ORANGE, 800), 40, WHITE, 800, lh=1.1) +
    T(50, 380, 420, "Cuando la IA se va lejos de la nube, alguien tiene que seguir escuchando al que escucha.", 15, WHITE, 500, lh=1.4)),
    kind="dark")

start = ""
for k, (a, s) in enumerate((("Una placa", "Arduino UNO Q o Raspberry Pi"),
                            ("Edge Impulse", "entrena un modelo sin escribir mucho código"),
                            ("MIMII DUE", "el audio de bombas de Hitachi, abierto"),
                            ("Este repo", "el código y la infraestructura de la prueba"))):
    start += T(50, 130 + k * 78, 560, b(a) + f'<br><span style="font-size:14px;color:{SLATE}">{s}</span>', 18, NAVY, 500, lh=1.35)
slide("empezar", "Por dónde empezar", (
    TITLE("Por dónde empezar") + start + IMG(uri(os.path.join(B, "png", "qr.png")), 660, 140, 220) +
    CAP(640, 372, 260, REPO, NAVY, 12)))

slide("gracias", "¡Gracias!", (
    f'<div class="bg {ASSETS[tdc("fondo-oscuro.jpg")][0]}"></div>' +
    IMG(tdc("pajaro-vuela.png"), 86, 126, 317) +
    TRI(403, 94, 26, ORANGE, -15) + TRI(58, 79, 20, YELLOW, 20) + TRI(374, 439, 24, GREEN, 35) +
    IMG(tdc("logo-blanco.png"), 33, 456, 72) + T(132, 489, 324, "TECHDAYCALI.COM", 13, WHITE, 500) +
    T(497, 128, 360, "¿PREGUNTAS?", 14, GREEN, 700, extra="letter-spacing:1.6px") +
    T(497, 158, 425, "¡Gracias!", 54, WHITE, 800, lh=1.1) +
    T(497, 263, 259, "Alejandro Varela Franco", 18, YELLOW, 700) +
    T(497, 302, 259, f"{LINKEDIN}<br>github.com/alejandro945", 12, WHITE, 500, lh=1.6) +
    R(773, 263, 149, 153, WHITE, radius=10) + IMG(uri(os.path.join(B, "png", "qr.png")), 783, 273, 129) +
    T(765, 422, 166, "Escanea y conecta", 12, GREEN, 700, "center") +
    R(497, 456, 410, 1, "#3A4A72", radius=0) + R(497, 469, 16, 2, GREEN, radius=0)), kind="none")

# ═════════════════════════════ ANEXOS ════════════════════════════════
slide("a-aws", "A1 · La arquitectura en AWS", (
    KICK("ANEXO A1") + TITLE("La arquitectura en AWS", y=56) + FIG("arch-ref", 60, 104, 840)), annex=True, num=False)

juez_rows = ""
for k, (a, s) in enumerate((("Sombra", "el candidato corre al lado del activo en el ring 0 (una bomba); el activo decide"),
                            ("Esperar", "en la demo, 2 minutos; en producción, días, y cruzado con mantenimiento"),
                            ("Medir", "Logs Insights: clips donde el candidato no oyó lo que el activo sí, y donde alertó solo"),
                            ("Promover", "ring 0 → ring 1 → /station/last_good_version"),
                            ("Rechazar", "la bomba vuelve a la versión activa sola y llega un aviso por SNS"))):
    y = 125 + k * 64
    juez_rows += T(50, y, 160, a, 18, ORANGE if a == "Rechazar" else NAVY, 800)
    juez_rows += T(210, y + 2, 700, s, 15)
slide("a-juez", "A2 · El juez, paso a paso", (
    KICK("ANEXO A2") + TITLE("El juez, paso a paso", y=56) + juez_rows +
    CAP(50, 455, 860, "No necesita saber la verdad: compara dos modelos sobre el mismo audio. "
        "Código: poc-devopsdays/cloud/judge.asl.json", SLATE, 12)), annex=True, num=False)

slide("a-88", "A3 · La red de seguridad: 88 segundos", (
    KICK("ANEXO A3") + TITLE("La red de seguridad: 88 segundos", y=56) +
    IMG(uri(os.path.join(TALK, "assets", "screens", "acto3.png")), 50, 130, 860) +
    CAP(50, 340, 860, "Primera prueba (18 de octubre): la v2 sí llegó a decidir; la alarma de fallas no oídas y una Lambda "
        "devolvieron la 1.0.0 en 88 s. El ring 1 nunca la recibió.", NAVY, 14)), annex=True, num=False)

slide("a-genai", "A4 · ¿Por qué ML tradicional y no un LLM?", (
    KICK("ANEXO A4") + TITLE("¿Por qué ML tradicional y no un LLM?", y=56) +
    T(50, 130, 860, "Un autoencoder de 464 KB decide en milisegundos en una CPU modesta, sin red, y se entrena solo con "
      "sonido normal.<br><br>Un LLM pequeño pesa gigabytes y necesita otro hardware.<br><br>" +
      b("El ciclo de MLOps es el mismo para los dos: versionar, desplegar por anillos, observar lo que decide y volver "
        "atrás. Cambia la señal que se mide, no el ciclo."), 18, NAVY, 500, lh=1.45)), annex=True, num=False)

FUENTES = (
    "Paros no planeados: Siemens, The True Cost of Downtime 2024.",
    "Caída de AWS y las camas inteligentes: PCWorld y MacTrast, octubre de 2025.",
    "PC con IA: Gartner, 28 de agosto de 2025 (31 % en 2025, 54,7 % proyectado para 2026).",
    "Face ID: Apple, «About Face ID advanced technology».",
    "Arduino UNO Q: Qualcomm y Arduino, 7 de octubre de 2025.",
    "Hogares con internet: DANE, Encuesta de Calidad de Vida 2025 (rurales: 56,9 %).",
    "Red IoT de Cenicaña: Agronegocios, junio de 2022.",
    "Wi-Fi HaLow (IEEE 802.11ah): Morse Micro y Wireless Broadband Alliance.",
    "El cerebro, unos 20 W: Balasubramanian, PNAS, 2021. Predictive coding y eficiencia: Ali et al., Patterns, 2022.",
    "Audio: MIMII DUE, Tanabe et al., Hitachi (2021), CC BY-NC-SA 4.0.",
    "Foto del mecánico: Mike Newbry, Unsplash. Plantilla y piezas gráficas: Tech Day Cali 2026.",
    "Las cifras de la prueba: el ensayo en AWS del 18 de octubre de 2026 y el repo " + REPO + ".")
slide("a-fuentes", "A5 · Fuentes", (
    KICK("ANEXO A5") + TITLE("Fuentes", y=56) + T(50, 120, 820, "<br>".join(FUENTES), 12.5, NAVY, 500, lh=1.6)),
    annex=True, num=False)


# ── the page ──────────────────────────────────────────────────────────
def fonts_css():
    d = os.path.join(TALK, "assets", "fonts", "montserrat")
    out = ""
    for w, n in ((400, "Regular"), (500, "Medium"), (600, "SemiBold"), (700, "Bold"), (800, "ExtraBold")):
        out += (f"@font-face{{font-family:Montserrat;font-weight:{w};font-style:normal;font-display:block;"
                f"src:url({data_uri(os.path.join(d, f'Montserrat-{n}.woff2'))}) format('woff2')}}\n")
    return out


def assets_css():
    return "".join(f".{cls}{{background-image:url({data_uri(path)});background-repeat:no-repeat}}\n"
                   for path, (cls, _, _) in ASSETS.items())


CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;background:#000;overflow:hidden;font-family:Montserrat,Helvetica,Arial,sans-serif}
#deck{position:fixed;left:50%;top:50%;width:960px;height:540px;transform-origin:0 0}
.s{position:absolute;inset:0;overflow:hidden;opacity:0;visibility:hidden;transition:opacity .35s ease,visibility 0s linear .35s;background:#F6F8FB}
.s.on{opacity:1;visibility:visible;transition:opacity .35s ease}
.bg{position:absolute;inset:0;background-size:cover;background-position:center}
.t{position:absolute;white-space:normal}
h1.t,h2.t{font-weight:800;line-height:1.15;letter-spacing:-.2px}
.i{position:absolute;display:block}
.f{position:absolute;line-height:0}
.f svg{display:block;width:100%;height:auto}
.r{position:absolute}
#bar{position:fixed;left:0;bottom:0;height:3px;background:#12D18E;width:0;transition:width .3s;z-index:5}
#blk{position:fixed;inset:0;background:#000;z-index:9}
#notes{position:fixed;left:2%;right:2%;bottom:3%;max-height:40%;overflow:auto;background:rgba(11,19,42,.94);color:#fff;
  font:15px/1.5 Montserrat,sans-serif;padding:16px 20px;border-radius:10px;z-index:8;display:none;white-space:pre-wrap}
#notes.on{display:block}
#notes b{color:#12D18E}
@media print{
  @page{size:960px 540px;margin:0}
  html,body{background:#fff;overflow:visible;height:auto}
  #deck{position:static;transform:none!important;width:auto;height:auto}
  .s{position:relative;width:960px;height:540px;opacity:1;visibility:visible;page-break-after:always;break-after:page}
  .s[data-annex]{display:block}
  #bar,#notes,#blk{display:none!important}
}
"""

JS = r"""
(()=>{
const deck=document.getElementById('deck'), slides=[...deck.querySelectorAll('.s')];
const bar=document.getElementById('bar'), notes=document.getElementById('notes');
function fit(){ const k=Math.min(innerWidth/960, innerHeight/540);
  deck.style.transform=`translate(${-480*k}px,${-270*k}px) scale(${k})`; }
addEventListener('resize',fit); fit();
const MAIN=[],ANX=[]; slides.forEach((s,k)=>(s.dataset.annex?ANX:MAIN).push(k));
let i=0, ret=0, nOn=false;
const inAnx=()=>!!slides[i].dataset.annex;
const ch=('BroadcastChannel' in window)?new BroadcastChannel('techdaycali-deck'):null;
function show(n){
  i=Math.max(0,Math.min(slides.length-1,n));
  slides.forEach((s,k)=>s.classList.toggle('on',k===i));
  const b=inAnx()?ANX:MAIN; bar.style.width=((b.indexOf(i)+1)/b.length*100)+'%';
  notes.replaceChildren(Object.assign(document.createElement('b'),{textContent:slides[i].dataset.title}),
    document.createTextNode('\n\n'+(slides[i].dataset.notes||'—')));
  try{ history.replaceState(null,'','#'+slides[i].dataset.id); }catch(e){}
  if(ch) ch.postMessage({i, title:slides[i].dataset.title, notes:slides[i].dataset.notes||'',
    next:(b[b.indexOf(i)+1]!==undefined?slides[b[b.indexOf(i)+1]].dataset.title:'— fin —'),
    pos:(b.indexOf(i)+1)+' / '+b.length+(inAnx()?' · anexos':'')});
}
function go(d){ const b=inAnx()?ANX:MAIN, p=b.indexOf(i), t=Math.max(0,Math.min(b.length-1,p+d)); if(b[t]!==i) show(b[t]); }
function toAnx(n){ if(!inAnx()) ret=i; show(ANX[Math.max(0,Math.min(ANX.length-1,n))]); }
function toMain(){ if(inAnx()) show(ret); }
if(ch) ch.onmessage=e=>{ const m=e.data||{}; if(m.cmd==='next') go(1); else if(m.cmd==='prev') go(-1); else if(m.cmd==='hello') show(i); };
function presenter(){
  const w=window.open('','techdaycali-presenter','width=900,height=640'); if(!w) return;
  w.document.write(`<!doctype html><meta charset="utf-8"><title>Presentador · MLOps a ciegas</title>
  <style>body{margin:0;background:#0B132A;color:#fff;font:17px/1.5 Montserrat,Helvetica,sans-serif;padding:22px}
  #t{font-size:26px;font-weight:800;color:#12D18E}#n{white-space:pre-wrap;margin-top:14px;max-height:70vh;overflow:auto}
  #top{display:flex;justify-content:space-between;color:#AAB6CB;font-size:15px}#c{font-size:30px;font-weight:800;color:#FFC700}
  #nx{color:#AAB6CB;margin-top:14px;font-size:15px}</style>
  <div id="top"><span id="p"></span><span id="c">0:00</span></div><div id="t"></div><div id="nx"></div><div id="n"></div>
  <script>const c=new BroadcastChannel('techdaycali-deck'),t0=Date.now();
  c.onmessage=e=>{const m=e.data;if(m.cmd)return;document.getElementById('t').textContent=m.title;
   document.getElementById('n').textContent=m.notes;document.getElementById('nx').textContent='Siguiente: '+m.next;
   document.getElementById('p').textContent=m.pos;};
  setInterval(()=>{const s=Math.floor((Date.now()-t0)/1000);document.getElementById('c').textContent=Math.floor(s/60)+':'+String(s%60).padStart(2,'0');},1000);
  addEventListener('keydown',e=>{if(['ArrowRight','ArrowDown',' ','PageDown','Enter'].includes(e.key)){e.preventDefault();c.postMessage({cmd:'next'});}
   else if(['ArrowLeft','ArrowUp','PageUp','Backspace'].includes(e.key)){e.preventDefault();c.postMessage({cmd:'prev'});}});
  c.postMessage({cmd:'hello'});<\/script>`);
  w.document.close();
}
addEventListener('keydown',e=>{
  const k=e.key.toLowerCase();
  if(['ArrowRight','ArrowDown',' ','PageDown','Enter'].includes(e.key)){e.preventDefault();go(1);}
  else if(['ArrowLeft','ArrowUp','PageUp','Backspace'].includes(e.key)){e.preventDefault();go(-1);}
  else if(e.key==='Escape'){ if(inAnx()){e.preventDefault();toMain();} }
  else if(e.key==='Home') show(MAIN[0]);
  else if(e.key==='End') show(MAIN[MAIN.length-1]);
  else if(k==='a'){e.preventDefault(); inAnx()?toMain():toAnx(0);}
  else if(k==='m'){e.preventDefault(); toMain();}
  else if(k>='1'&&k<='9'&&(e.altKey||e.metaKey)){e.preventDefault(); toAnx(+k-1);}
  else if(k==='b'||k==='.'){ const bk=document.getElementById('blk'); bk.hidden=!bk.hidden; }
  else if(k==='n'){ nOn=!nOn; notes.classList.toggle('on',nOn); }
  else if(k==='p'){ presenter(); }
  else if(k==='f'){ document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen(); }
});
addEventListener('click',e=>{ if(notes.contains(e.target)) return; (e.clientX<innerWidth*.25?go(-1):go(1)); });
const h=decodeURIComponent(location.hash.slice(1)), st=slides.findIndex(s=>s.dataset.id===h);
show(st>=0?st:0);
window.__deck={show,slides};
})();
"""


def page():
    secs = []
    for s in SLIDES:
        attrs = (f' data-id="{s["id"]}" data-title="{html.escape(s["title"])}" data-notes="{html.escape(s["notes"])}"' +
                 (' data-annex="1"' if s["annex"] else ""))
        secs.append(f'<section class="s"{attrs}>{s["html"]}</section>')
    return ("<!doctype html>\n<html lang=\"es\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
            "<title>MLOps a ciegas · Tech Day Cali 2026</title>\n"
            f"<style>\n{fonts_css()}{assets_css()}{CSS}</style>\n</head>\n<body>\n"
            "<div id=\"deck\">\n" + "\n".join(secs) + "\n</div>\n"
            "<div id=\"bar\"></div><div id=\"notes\"></div><div id=\"blk\" hidden></div>\n"
            f"<script>{JS}</script>\n</body>\n</html>\n")


if __name__ == "__main__":
    out = page()
    open(OUT, "w", encoding="utf-8").write(out)
    main = sum(1 for s in SLIDES if not s["annex"])
    missing = [s["id"] for s in SLIDES if not s["notes"]]
    print(f"✔ {OUT}: {main} slides + {len(SLIDES) - main} annexes · {len(out) / 1e6:.1f} MB"
          + (f" · no notes: {', '.join(missing)}" if missing else ""))
