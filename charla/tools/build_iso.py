"""
Figuras isométricas de la charla (estilo "anatomy": una máquina que explica la idea).

  equipo   · el equipo por dentro, en vista explotada, con el micrófono sobre la bomba
  nube     · el lazo de MLOps en la nube (todo pasa por el endpoint)
  edge     · la estación de bombeo: bombas con su equipo, enlace roto y cuatro restricciones (clics 1–4)
  senales  · la consola con las cuatro señales, con los rótulos de la bomba

FIGS (este módulo) = estas cuatro + build_figs.FIGS (planas, arquitectura y secuencia).
Cada figura es un <svg> de 1600x900 que se superpone a la lámina (zona útil
x 84–1516, y 225–760: arriba va el título de la plantilla, abajo el pie).

  data-on="n"   aparece en el paso n del deck (HTML) / con el clic n (PowerPoint)
  data-off="n"  se va en el paso n
  class="mv-*"  se anima en el HTML; en el PNG queda quieto
  FIGS[x](static=True) = último clic, sin animación y sin lo que tiene data-off

Uso:  python3 build_iso.py [carpeta]   → <fig>.svg (animado) y <fig>.png (quieto)
"""
import math, os, sys
from iso import (Iso, mix, tones, NAVY, SLATE, MUTED, LIGHT, PURPLE, BLUE, CYAN, MAGENTA,
                 S100, S200, S300, S400, WHITE, FONT, MONO)


def wrap(body):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900" class="iso">'
            f'{body}</svg>')


def tag(g, sx, sy, s, color, w=None, extra=""):
    w = w or (len(s) * 8.6 + 22)
    g.add(f'<g {extra}><rect x="{sx - w / 2:.1f}" y="{sy - 14:.1f}" width="{w:.1f}" height="28" rx="6" fill="{WHITE}" '
          f'stroke="{color}" stroke-width="1.6"/>'
          f'<text x="{sx:.1f}" y="{sy + 5:.1f}" font-family="{MONO}" font-size="14" font-weight="700" fill="{color}" '
          f'text-anchor="middle">{s}</text></g>')


# ─────────────────────────────────────────────────────────────────────
#  piezas de la estación: la bomba, el micrófono y el gabinete del equipo
# ─────────────────────────────────────────────────────────────────────
def _mic(g, x, y, h=1.7, s=1.0, color=CYAN):
    """Micrófono en su pie, apuntando hacia +y (hacia la bomba que tiene delante)."""
    g.cyl(x, y, 0, .2 * s, .06 * s, S400)
    g.line3([(x, y, .06 * s), (x, y, h)], NAVY, 2.6)
    g.hcyl(y - .12 * s, y + .34 * s, x, h, .13 * s, color, axis="y")
    return (x, y + .34 * s, h)                     # punta del micrófono


def _pump(g, x, y, s=1.0, body=SLATE, casing=BLUE, pipes=True):
    """Una bomba centrífuga con su motor, de lado (eje a lo largo de x). Ocupa ~3.0 × 1.3."""
    cy, cz = y + .65 * s, .22 * s + .52 * s
    g.box(x, y, 0, 3.0 * s, 1.3 * s, .22 * s, S300)                       # base
    g.hcyl(x + .15 * s, x + 1.5 * s, cy, cz, .5 * s, body)                # motor
    for k in range(4):                                                    # aletas
        xx = x + (.35 + k * .3) * s
        g.line3([(xx, cy + .5 * s * .2, cz + .49 * s), (xx, cy + .5 * s, cz + .1 * s)],
                mix(body, WHITE, .35), 1.6)
    g.box(x + .55 * s, cy - .2 * s, cz + .45 * s, .4 * s, .4 * s, .22 * s, body)   # caja de bornes
    g.hcyl(x + 1.5 * s, x + 1.8 * s, cy, cz, .24 * s, S400)                 # acople
    g.hcyl(x + 1.8 * s, x + 2.32 * s, cy, cz, .62 * s, casing)              # voluta
    if pipes:
        g.cyl(x + 2.06 * s, cy, cz + .3 * s, .19 * s, 1.0 * s, S300)        # descarga, hacia arriba
        g.hcyl(x + 2.32 * s, x + 3.0 * s, cy, cz, .22 * s, S300)            # succión, hacia el frente
    return (x + 2.06 * s, cy, cz)                                          # centro de la voluta


def _cabinet(g, x, y, s=1.0, color=NAVY, leds=2, h=1.25):
    """El gabinete del equipo de borde, con sus luces."""
    w, d = .7 * s, .55 * s
    g.box(x, y, 0, w, d, h * s, color)
    for k in range(3):
        cx, cy = g.P(x + (.16 + k * .19) * s, y + d, h * s - .25 * s)
        g.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="3.2" fill="{CYAN if k < leds else S300}"/>')
    return (x + w / 2, y + d / 2, h * s)


# ─────────────────────────────────────────────────────────────────────
#  1 · el equipo por dentro (vista explotada, cuatro capas)
# ─────────────────────────────────────────────────────────────────────
def fig_equipo(static=False):
    g = Iso(ox=800, oy=566, u=32)
    W = D = 3.8
    Z = [0, 3.1, 6.2, 9.3]                 # altura de cada capa
    c = W / 2

    # la bomba, abajo a la izquierda, con el micrófono detrás (se dibujan antes: quedan detrás)
    PX, PY, PS = -3.8, 7.5, 1.15
    mx, my = PX + 2.06 * PS, PY - .62
    tip = _mic(g, mx, my, h=3.0, s=1.15)
    g.line3([(mx, my, .02), (1.0, my, .02), (1.0, D, .12)], NAVY, 3)          # cable a la placa
    _pump(g, PX, PY, s=PS)
    sx, sy = g.P(*tip)
    for k, r in enumerate([12, 21, 30]):
        cls = '' if static else f'class="mv-arc" style="animation-delay:{k * .35:.2f}s"'
        g.add(f'<path d="M{sx + r * .25:.1f},{sy + r * .97:.1f} A{r},{r} 0 0 1 {sx - r * .9:.1f},{sy + r * .43:.1f}" '
              f'fill="none" stroke="{CYAN}" stroke-width="2.6" stroke-linecap="round" {cls}/>')

    # guías de la vista explotada (esquinas)
    for (x, y) in [(0, 0), (W, 0), (0, D), (W, D)]:
        g.line3([(x, y, 0.3), (x, y, Z[-1])], S300, 1.4, "4 6")

    # ── capa 0 · modelo + runtime ──
    z = Z[0]
    g.box(0, 0, z, W, D, .24, NAVY)
    for k in range(4):          # pistas
        g.line3([(.3, .6 + k * .85, z + .25), (1.0, .6 + k * .85, z + .25)], mix(NAVY, WHITE, .35), 2)
        g.line3([(2.8, .6 + k * .85, z + .25), (3.5, .6 + k * .85, z + .25)], mix(NAVY, WHITE, .35), 2)
    g.box(1.15, 1.15, z + .24, 1.5, 1.5, .42, PURPLE)
    g.line3([(1.4, 1.4, z + .67), (2.4, 1.4, z + .67), (2.4, 2.4, z + .67), (1.4, 2.4, z + .67), (1.4, 1.4, z + .67)],
            mix(PURPLE, WHITE, .6), 1.4)

    # ── capa 1 · artefacto verificable ──
    z = Z[1]
    g.box(0, 0, z, W, D, .14, S200)
    g.box(.8, .8, z + .14, 2.2, 2.2, 1.0, BLUE)
    g.poly([(1.7, .8, z + 1.14), (2.1, .8, z + 1.14), (2.1, 3.0, z + 1.14), (1.7, 3.0, z + 1.14)], mix(BLUE, WHITE, .55))
    g.poly([(.8, 3.0, z + .42), (3.0, 3.0, z + .42), (3.0, 3.0, z + .62), (.8, 3.0, z + .62)], mix(BLUE, WHITE, .55))
    g.poly([(3.0, .8, z + .42), (3.0, 3.0, z + .42), (3.0, 3.0, z + .62), (3.0, .8, z + .62)], mix(BLUE, NAVY, .1))
    sx, sy = g.P(W, D, z)
    sx, sy = g.P(W, 0, z + .07)
    g.add(f'<line x1="{sx + 4:.1f}" y1="{sy:.1f}" x2="{sx + 24:.1f}" y2="{sy:.1f}" stroke="{BLUE}" stroke-width="1.5" data-on="1"/>')
    tag(g, sx + 92, sy, "v1.0.0 · sha256", BLUE, extra='data-on="1"')

    # ── capa 2 · agente ──
    z = Z[2]
    g.box(0, 0, z, W, D, .14, S200)
    g.box(.9, .9, z + .14, 2.0, 2.0, 1.0, SLATE)
    for k in range(3):
        cx, cy = g.P(1.25 + k * .5, 2.9, z + .62)
        on = k < 2
        cls = f'class="mv-led" style="animation-delay:{k * .5:.1f}s"' if on and not static else ''
        g.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.5" fill="{CYAN if on else S300}" {cls}/>')

    # ── capa 3 · cola de eventos + salida ──
    z = Z[3]
    g.box(0, 0, z, W, D, .14, S200)
    g.box(.4, 1.5, z + .14, 2.9, 1.1, .3, S300)              # riel
    for k in range(4):
        g.box(.6 + k * .66, 1.72, z + .44, .46, .66, .46, CYAN)
    g.box(3.05, .35, z + .14, .45, .45, .45, S400)          # antena, en la esquina derecha
    g.line3([(3.27, .57, z + .59), (3.27, .57, z + 1.7)], NAVY, 4)
    tx, ty = g.P(3.27, .57, z + 1.7)
    for k, r in enumerate([14, 25, 36]):
        cls = '' if static else f'class="mv-arc" style="animation-delay:{k * .35:.2f}s"'
        g.add(f'<path d="M{tx - r * .72:.1f},{ty - r * .5:.1f} A{r},{r} 0 0 1 {tx + r * .72:.1f},{ty - r * .5:.1f}" '
              f'fill="none" stroke="{PURPLE}" stroke-width="3" stroke-linecap="round" {cls}/>')
    g.add(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="5" fill="{PURPLE}"/>')

    # una decisión sube del modelo a la cola y sale por la antena
    if not static:
        g.flow([(c, c, Z[0] + .7), (c, c, Z[3] + .6), (3.27, .57, Z[3] + .8), (3.27, .57, Z[3] + 1.7)],
               n=3, dur=3.6, r=6, extra='class="mv-flow"')

    # ── etiquetas, alternadas ──
    L, R = 610, 1000
    def ly(z): return g.P(0, D, z)[1] - 4
    g.label(tip, 0, 0, "Micrófono sobre la bomba", "el audio entra y no sale",
            at=(g.P(*tip)[0] - 120, g.P(*tip)[1] + 8), anchor="end", extra='data-on="0"')
    g.label((W, D * .55, Z[0] + .12), 0, 0, "Modelo + runtime", "decide en milisegundos, con o sin red",
            at=(R, ly(Z[0]) + 10), extra='data-on="0"')
    g.label((0, D * .5, Z[1] + .07), 0, 0, "Artefacto verificable", "versión + hash: si lo tocan, no se instala",
            at=(L, ly(Z[1]) - 30), extra='data-on="1"')
    g.label((W, D * .5, Z[2] + .07), 0, 0, "Agente", "trae el estado deseado cuando hay red",
            at=(R, ly(Z[2]) - 30), extra='data-on="2"')
    g.label((0, D * .5, Z[3] + .07), 0, 0, "Cola de eventos", "cada decisión, guardada hasta que haya red",
            at=(L, ly(Z[3]) - 30), extra='data-on="3"')
    return wrap(g.svg())


# ─────────────────────────────────────────────────────────────────────
#  2 · el lazo de MLOps: nube (cerrado) y edge (cortado)
# ─────────────────────────────────────────────────────────────────────
PW, PD = 9.0, 7.0                                   # planta de la nube
LOOP = [(1.2, 1.2), (7.8, 1.2), (7.8, 5.8), (1.2, 5.8)]   # cinta en lazo


def _endpoint(g, x, y):
    g.box(x - .6, y - .6, 0, 1.2, 1.2, 2.3, BLUE)
    for k in range(4):
        g.line3([(x - .35, y + .6, .5 + k * .45), (x + .35, y + .6, .5 + k * .45)], WHITE, 3, op=.65)


def _recorder(g, x, y):
    g.box(x - .7, y - .6, 0, 1.4, 1.2, 1.1, S300)
    g.cyl(x - .25, y, 1.1, .3, .12, NAVY)
    g.cyl(x + .35, y, 1.1, .3, .12, NAVY)


def _scale(g, x, y):
    g.box(x - .7, y - .6, 0, 1.4, 1.2, .45, S300)
    g.box(x - .15, y - .15, .45, .3, .3, 1.0, S400)
    g.box(x - .9, y - .35, 1.45, 1.8, .7, .12, NAVY)


def _beacon(g, x, y):
    g.box(x - .5, y - .5, 0, 1.0, 1.0, .6, S300)
    g.cyl(x, y, .6, .3, .9, PURPLE)


def _press(g, x, y):
    g.box(x - .7, y - .6, 0, 1.4, 1.2, .7, SLATE)
    g.box(x - .5, y - .4, .7, 1.0, .8, 1.1, S300)
    g.cyl(x, y, 1.8, .36, .32, BLUE)


STN = [  # (x, y, dibujo, título, subtítulo, posición de la etiqueta)
    (1.2, 4.4, _endpoint, "Endpoint", "el modelo, en la nube", "L"),
    (2.9, 1.2, _recorder, "Captura", "cada petición y respuesta", "TL"),
    (6.1, 1.2, _scale, "Línea base", "compara con el entrenamiento", "TR"),
    (7.8, 3.5, _beacon, "Alerta", "si algo se desvía", "R"),
    (5.0, 5.8, _press, "Reentrena", "y vuelve a desplegar", "BL"),
]


def _cloud(g, edge, static):
    g.box(-.5, -.5, -.4, PW + 1, PD + 1, .4, mix(LIGHT, PURPLE, .05), edge=S400)
    pts = [(x, y, .02) for x, y in LOOP + [LOOP[0]]]
    g.line3(pts, S300, 18)
    g.line3(pts, WHITE, 10, "2 12")
    # orden de pintado: de atrás (x+y chico) hacia adelante
    order = sorted(range(len(STN)), key=lambda k: STN[k][0] + STN[k][1])
    for k in order:
        x, y, fn, *_ = STN[k]
        if edge and k == 0:
            # el endpoint ya no está: queda la marca en el piso
            g.poly([(x - .6, y - .6, .03), (x + .6, y - .6, .03), (x + .6, y + .6, .03), (x - .6, y + .6, .03)],
                   "none", S400, 1.6, extra='stroke-dasharray="5 5"')
            continue
        fn(g, x, y)
    if not static:
        path = [(x, y, .55) for x, y in LOOP + [LOOP[0]]]
        off = ' data-off="2"' if edge else ''
        g.flow(path, n=7, dur=10, r=7.5, extra=f'class="mv-flow"{off}')
    sx, sy = g.P(-.5, -.5, 0)
    g.text(sx, sy - 22, "NUBE", 15, SLATE, 700, "middle", family=MONO, extra='letter-spacing="2"')


def _station_labels(g, edge):
    for k, (x, y, fn, t, s, pos) in enumerate(STN):
        if edge and k == 0:
            continue
        top = {"L": 2.3, "TL": 1.2, "TR": 1.5, "R": 1.5, "BL": 2.1}[pos]
        sx, sy = g.P(x, y, top)
        at = {"L": (sx - 110, sy + 26), "TL": (sx - 110, sy - 60), "TR": (sx + 120, sy - 60),
              "R": (sx + 120, sy - 40), "BL": (sx - 90, sy + 150)}[pos]
        g.label((x, y, top), 0, 0, t, s, at=at)


def fig_lazo(edge=False, static=False):
    if not edge:
        g = Iso(ox=1010, oy=330, u=36)
        _cloud(g, False, static)
        _station_labels(g, False)
        # la frase, a la izquierda
        g.add(f'<g>'
              f'<text x="96" y="440" font-family="{FONT}" font-size="40" font-weight="800" fill="{NAVY}">Todo pasa</text>'
              f'<text x="96" y="488" font-family="{FONT}" font-size="40" font-weight="800" fill="{NAVY}">por el <tspan fill="{PURPLE}">endpoint</tspan>.</text>'
              f'<text x="96" y="540" font-family="{FONT}" font-size="24" font-weight="400" fill="{SLATE}">Ves cada petición</text>'
              f'<text x="96" y="570" font-family="{FONT}" font-size="24" font-weight="400" fill="{SLATE}">y cada respuesta.</text></g>')
        return wrap(g.svg())

    # ── edge: la nube queda donde estaba; el modelo baja a la estación ──
    g = Iso(ox=1010, oy=330, u=36)
    _cloud(g, True, static)
    _station_labels(g, True)
    # niebla sobre la nube cuando se cae la red (clic 2)
    corners = [g.P(-.5, -.5, 2.6), g.P(PW + .5, -.5, 2.6), g.P(PW + .5, PD + .5, -.4), g.P(-.5, PD + .5, -.4)]
    xs = [p[0] for p in corners]; ys = [p[1] for p in corners]
    fx, fy = min(xs) - 30, 236
    g.add(f'<rect x="{fx:.0f}" y="{fy}" width="{1580 - fx:.0f}" height="{max(ys) + 30 - fy:.0f}" '
          f'fill="{WHITE}" opacity=".62" data-on="2" data-fog="1"/>')

    e, mast, mics, cabs = _station(static)

    # el enlace estación → captura (cruza la frontera)
    a = e.P(*mast)
    b = g.P(-.5, 2.4, 0)
    mid = (a[0] + (b[0] - a[0]) * .42, a[1] + (b[1] - a[1]) * .42)
    g.add(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{NAVY}" stroke-width="3" '
          f'data-off="2"/>')
    g.add(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{PURPLE}" stroke-width="3" '
          f'stroke-dasharray="9 8" data-on="2"/>')
    if not static:
        g.add(f'<g class="mv-flow" data-off="2">')
        for k in range(4):
            g.add(f'<circle r="6.5" fill="{PURPLE}"><animateMotion dur="2.4s" begin="{-k * .6:.1f}s" repeatCount="indefinite" '
                  f'path="M{a[0]:.1f},{a[1]:.1f} L{b[0]:.1f},{b[1]:.1f}"/></circle>')
        g.add('</g>')
    g.add(f'<g data-on="2"><circle cx="{mid[0]:.1f}" cy="{mid[1]:.1f}" r="22" fill="{WHITE}" stroke="{PURPLE}" stroke-width="3"/>'
          f'<path d="M{mid[0] - 8:.1f},{mid[1] - 8:.1f} L{mid[0] + 8:.1f},{mid[1] + 8:.1f} M{mid[0] + 8:.1f},{mid[1] - 8:.1f} '
          f'L{mid[0] - 8:.1f},{mid[1] + 8:.1f}" stroke="{PURPLE}" stroke-width="3.5" stroke-linecap="round"/></g>')

    # clic 1 · equipos de varias generaciones
    for k, (p3, t) in enumerate(cabs):
        x, y = e.P(*p3)
        px = 150
        e.add(f'<g data-on="1"><circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{NAVY}"/>'
              f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{px + 52:.1f}" y2="{y:.1f}" stroke="{NAVY}" stroke-width="1.5"/></g>')
        pill(e, px, y, t, NAVY, extra='data-on="1"', w=104)
    # clic 3 · mil bombas, sin SSH
    tx, ty = 100, 244
    e.add(f'<g data-on="3"><rect x="{tx}" y="{ty}" width="236" height="58" rx="8" fill="{NAVY}"/>'
          f'<circle cx="{tx + 16}" cy="{ty + 13}" r="3.5" fill="{S400}"/><circle cx="{tx + 28}" cy="{ty + 13}" r="3.5" fill="{S400}"/>'
          f'<text x="{tx + 16}" y="{ty + 44}" font-family="{MONO}" font-size="19" font-weight="700" fill="{WHITE}">$ ssh bomba-0417</text>'
          f'<circle cx="{tx + 236}" cy="{ty}" r="17" fill="{WHITE}" stroke="{PURPLE}" stroke-width="3"/>'
          f'<path d="M{tx + 230},{ty - 6} L{tx + 242},{ty + 6} M{tx + 242},{ty - 6} L{tx + 230},{ty + 6}" stroke="{PURPLE}" '
          f'stroke-width="3" stroke-linecap="round"/></g>')
    # clic 4 · el audio no puede salir: el sonido se queda dentro de la estación
    for m in mics:
        sx, sy = e.P(*m)
        for k, r in enumerate([11, 19, 27]):
            e.add(f'<path d="M{sx + r * .25:.1f},{sy + r * .97:.1f} A{r},{r} 0 0 1 {sx - r * .9:.1f},{sy + r * .43:.1f}" '
                  f'fill="none" stroke="{PURPLE}" stroke-width="2.6" stroke-linecap="round" data-on="4"/>')

    # las cuatro restricciones, una por clic (2 x 2, abajo)
    R = ["Equipos de varias generaciones.", "Red intermitente.",
         "Mil bombas, y ninguna con SSH.", "El audio no puede salir de la estación."]
    for k, r in enumerate(R):
        x = 96 + (k % 2) * 700
        y = 700 + (k // 2) * 44
        g.add(f'<g data-on="{k + 1}"><text x="{x}" y="{y}" font-family="{MONO}" font-size="18" font-weight="700" '
              f'fill="{PURPLE}">0{k + 1}</text>'
              f'<text x="{x + 40}" y="{y}" font-family="{FONT}" font-size="26" font-weight="700" fill="{NAVY}">{r}</text></g>')
    return wrap(e.svg() + g.svg())


def pill(g, sx, sy, s, color, extra="", size=18, w=None):
    """Rótulo en cápsula, monoespaciado (≥ 18 px)."""
    w = w or len(s) * size * .6 + 26
    g.add(f'<g {extra}><rect x="{sx - w / 2:.1f}" y="{sy - 16:.1f}" width="{w:.1f}" height="32" rx="7" fill="{WHITE}" '
          f'stroke="{color}" stroke-width="1.8"/>'
          f'<text x="{sx:.1f}" y="{sy + 6:.1f}" font-family="{MONO}" font-size="{size}" font-weight="700" fill="{color}" '
          f'text-anchor="middle">{s}</text></g>')


def _station(static=False):
    """La estación de bombeo: tres bombas con su micrófono y su equipo, y el mástil de la antena."""
    e = Iso(ox=430, oy=392, u=40)
    e.box(-.7, -.7, -.4, 5.2, 7.3, .4, S200, edge=S400)
    # la cerca: el audio no sale de aquí (clic 4)
    e.line3([(-.55, -.55, 0), (4.35, -.55, 0), (4.35, 6.45, 0), (-.55, 6.45, 0), (-.55, -.55, 0)], PURPLE, 2.6, "9 7",
            extra='data-on="4"')
    PY = [4.75, 2.45, .15]                           # de adelante hacia atrás… se dibujan de atrás hacia adelante
    gens = [(SLATE, 1.45, "CPU ARM"), (NAVY, 1.2, "CPU x86"), (PURPLE, 1.0, "NPU")]
    mics, cabs = [], []
    for py, (col, h, t) in zip(sorted(PY), gens):
        top = _cabinet(e, -.45, py + .25, s=.9, color=col, h=h, leds=2)
        cabs.append(((top[0], top[1] + .25, top[2] * .9 - .2), t))
        m = _mic(e, .55 + 2.06 * .9, py - .48, h=1.75, s=.9)
        mics.append(m)
        _pump(e, .55, py, s=.9)
        e.line3([(-.1, py + .5, .05), (.4, py + .5, .05)], NAVY, 2.4)       # cable del gabinete
    e.hcyl(-.2, 6.3, 3.45, .67, .22, S300, axis="y")                         # colector de succión
    # mástil con antena, en la esquina más cercana a la nube
    mx, my = 4.05, -.35
    e.box(mx - .25, my - .25, 0, .5, .5, .35, S400)
    e.line3([(mx, my, .35), (mx, my, 4.3)], NAVY, 4)
    tx, ty = e.P(mx, my, 4.3)
    for k, r in enumerate([12, 21, 30]):
        cls = '' if static else f'class="mv-arc" style="animation-delay:{k * .35:.2f}s"'
        e.add(f'<path d="M{tx - r * .72:.1f},{ty - r * .5:.1f} A{r},{r} 0 0 1 {tx + r * .72:.1f},{ty - r * .5:.1f}" '
              f'fill="none" stroke="{PURPLE}" stroke-width="3" stroke-linecap="round" {cls} data-off="2"/>')
    e.add(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="5" fill="{PURPLE}"/>')
    sx, sy = e.P(-.7, -.7, 0)
    e.text(sx + 16, sy - 40, "ESTACIÓN", 18, SLATE, 700, "middle", family=MONO, extra='letter-spacing="2"')
    return e, (mx, my, 4.3), mics, cabs


# ─────────────────────────────────────────────────────────────────────
#  3 · el instrumento de las cuatro señales (de frente, con profundidad oblicua)
# ─────────────────────────────────────────────────────────────────────
def fig_senales(static=False):
    o = []
    X0, X1, Y0, Y1 = 150, 1420, 288, 544          # cara frontal
    DX, DY = 54, -38                              # profundidad
    top_t, front_t, side_t = tones(S200)
    edge = mix(S200, NAVY, .55)
    P = lambda pts: " ".join("%.1f,%.1f" % p for p in pts)
    # zócalo
    o.append(f'<polygon points="{P([(X0 - 18, Y1), (X1 + 18, Y1), (X1 + 18 + DX, Y1 + DY), (X1 + 18 + DX, Y1 + DY + 20), (X1 + 18, Y1 + 20), (X0 - 18, Y1 + 20)])}" fill="{tones(S300)[2]}" stroke="{edge}" stroke-width=".9"/>')
    o.append(f'<rect x="{X0 - 18}" y="{Y1}" width="{X1 - X0 + 36}" height="20" fill="{S300}" stroke="{edge}" stroke-width=".9"/>')
    # cuerpo
    o.append(f'<polygon points="{P([(X0, Y0), (X1, Y0), (X1 + DX, Y0 + DY), (X0 + DX, Y0 + DY)])}" fill="{top_t}" stroke="{edge}" stroke-width=".9"/>')
    o.append(f'<polygon points="{P([(X1, Y0), (X1 + DX, Y0 + DY), (X1 + DX, Y1 + DY), (X1, Y1)])}" fill="{side_t}" stroke="{edge}" stroke-width=".9"/>')
    o.append(f'<rect x="{X0}" y="{Y0}" width="{X1 - X0}" height="{Y1 - Y0}" fill="{front_t}" stroke="{edge}" stroke-width=".9"/>')
    for k in range(5):                            # una luz por bomba; la 3 suena distinto
        o.append(f'<ellipse cx="{X0 + 60 + k * 26 + 27}" cy="{Y0 - 19}" rx="6" ry="3.6" fill="{PURPLE if k == 2 else CYAN}"/>')

    panels = [("Decisiones", "¿Qué decide?", "alertas por bomba"),
              ("Confianza", "¿Con cuánta seguridad?", "score contra umbral"),
              ("Entrada", "¿Se parece a lo que aprendió?", "nivel de la entrada"),
              ("Versión", "¿Qué corre dónde?", "versión por equipo")]
    PWd, PHt, GAP = 278, 196, (X1 - X0 - 4 * 278) / 5
    lab = lambda x, y, t, a="middle", c=SLATE: (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="18" '
                                                f'fill="{c}" text-anchor="{a}">{t}</text>')
    for i, (t, q, r) in enumerate(panels):
        px, py = X0 + GAP + i * (PWd + GAP), Y0 + 30
        # ventana con bisel
        o.append(f'<rect x="{px - 6}" y="{py - 6}" width="{PWd + 12}" height="{PHt + 12}" rx="10" fill="{S300}"/>')
        o.append(f'<rect x="{px}" y="{py}" width="{PWd}" height="{PHt}" rx="6" fill="{WHITE}"/>')
        cx, cy = px + PWd / 2, py + PHt / 2
        if i == 0:      # alertas por bomba: cinco barras, la 3 se dispara
            base = py + PHt - 44
            for k, h in enumerate([18, 26, 112, 14, 22]):
                bx = px + 36 + k * 44
                col = PURPLE if k == 2 else mix(NAVY, WHITE, .25)
                cls = '' if static or k != 2 else 'class="mv-bar"'
                o.append(f'<rect x="{bx}" y="{base - h}" width="30" height="{h}" fill="{col}" {cls}/>')
                o.append(f'<text x="{bx + 15}" y="{base + 28}" font-family="{MONO}" font-size="18" font-weight="700" '
                         f'fill="{PURPLE if k == 2 else MUTED}" text-anchor="middle">{k + 1}</text>')
            o.append(f'<line x1="{px + 26}" y1="{base}" x2="{px + PWd - 26}" y2="{base}" stroke="{S400}" stroke-width="2"/>')
        elif i == 1:    # dial: el score contra el umbral
            R, dcy = 84, py + PHt - 40
            pt = lambda a, rr: (cx + rr * math.cos(math.radians(a)), dcy - rr * math.sin(math.radians(a)))
            arc = lambda a0, a1: f'M{pt(a0, R)[0]:.1f},{pt(a0, R)[1]:.1f} A{R},{R} 0 0 1 {pt(a1, R)[0]:.1f},{pt(a1, R)[1]:.1f}'
            o.append(f'<path d="{arc(180, 0)}" fill="none" stroke="{S300}" stroke-width="14"/>')
            o.append(f'<path d="{arc(58, 0)}" fill="none" stroke="{PURPLE}" stroke-width="14"/>')
            a1, a2 = pt(58, R - 16), pt(58, R + 16)
            o.append(f'<line x1="{a1[0]:.1f}" y1="{a1[1]:.1f}" x2="{a2[0]:.1f}" y2="{a2[1]:.1f}" stroke="{NAVY}" stroke-width="3"/>')
            o.append(lab(a2[0] + 8, a2[1] - 4, "umbral", "start", NAVY))
            ang = math.radians(40)
            cls = '' if static else 'class="mv-needle"'
            o.append(f'<g {cls} style="transform-origin:{cx:.1f}px {dcy:.1f}px"><line x1="{cx:.1f}" y1="{dcy:.1f}" x2="{cx + 70 * math.cos(ang):.1f}" y2="{dcy - 70 * math.sin(ang):.1f}" stroke="{NAVY}" stroke-width="5" stroke-linecap="round"/></g>')
            o.append(f'<circle cx="{cx:.1f}" cy="{dcy:.1f}" r="9" fill="{NAVY}"/>')
        elif i == 2:    # regla: la huella del sonido normal y la entrada de ahora
            ry = cy + 14
            o.append(f'<line x1="{px + 30}" y1="{ry}" x2="{px + PWd - 30}" y2="{ry}" stroke="{S300}" stroke-width="12" stroke-linecap="round"/>')
            for k in range(9):
                xx = px + 30 + k * (PWd - 60) / 8
                o.append(f'<line x1="{xx:.1f}" y1="{ry + 16}" x2="{xx:.1f}" y2="{ry + (28 if k % 2 == 0 else 22)}" stroke="{S400}" stroke-width="2"/>')
            bx = px + 96
            o.append(f'<line x1="{bx}" y1="{ry - 50}" x2="{bx}" y2="{ry + 30}" stroke="{NAVY}" stroke-width="2" stroke-dasharray="5 5"/>')
            o.append(lab(bx, ry - 60, "lo que aprendió"))
            cls = '' if static else 'class="mv-drift"'
            o.append(f'<circle cx="{bx}" cy="{ry}" r="13" fill="{PURPLE}" {cls}/>')
        else:           # contador de versión
            for k, ch in enumerate(["v", "1", ".", "0"]):
                w = 26 if ch == "." else 48
                bx = px + 44 + sum(26 if c == "." else 48 for c in ["v", "1", ".", "0"][:k]) + k * 8
                o.append(f'<rect x="{bx}" y="{cy - 40}" width="{w}" height="80" rx="5" fill="{NAVY}"/>')
                o.append(f'<line x1="{bx}" y1="{cy}" x2="{bx + w}" y2="{cy}" stroke="{mix(NAVY, WHITE, .25)}" stroke-width="2"/>')
                o.append(f'<text x="{bx + w / 2}" y="{cy + 16}" font-family="{MONO}" font-size="44" font-weight="700" fill="{WHITE}" text-anchor="middle">{ch}</text>')
        # etiqueta debajo
        o.append(f'<g a="{i + 1}">')                 # sin clics: entran solas, una tras otra
        o.append(f'<line x1="{cx:.1f}" y1="{Y1 + 22}" x2="{cx:.1f}" y2="{Y1 + 46}" stroke="{NAVY}" stroke-width="1.5"/>')
        o.append(f'<circle cx="{cx:.1f}" cy="{Y1 + 22}" r="4" fill="{NAVY}"/>')
        o.append(f'<text x="{cx:.1f}" y="{Y1 + 76}" font-family="{MONO}" font-size="18" font-weight="700" fill="{PURPLE}" text-anchor="middle">0{i + 1}</text>')
        o.append(f'<text x="{cx:.1f}" y="{Y1 + 112}" font-family="{FONT}" font-size="34" font-weight="800" fill="{NAVY}" text-anchor="middle">{t}</text>')
        o.append(f'<text x="{cx:.1f}" y="{Y1 + 144}" font-family="{FONT}" font-size="21" fill="{SLATE}" text-anchor="middle">{q}</text>')
        o.append(f'<text x="{cx:.1f}" y="{Y1 + 180}" font-family="{MONO}" font-size="19" font-weight="700" fill="{PURPLE}" text-anchor="middle">{r}</text>')
        o.append('</g>')
    return wrap("\n".join(o))


from build_figs import FIGS as _FLAT    # noqa: E402  (figuras planas)


def final_state(svg):
    """Quita lo que tiene data-off: con static=True la figura queda como en su último clic."""
    import re
    out, i = [], 0
    for m in re.finditer(r'<(\w+)\b[^>]*\bdata-off="\d+"[^>]*?(/?)>', svg):
        if m.start() < i:
            continue
        out.append(svg[i:m.start()])
        if m.group(2) == "/":
            i = m.end()
            continue
        tag, depth, j = m.group(1), 1, m.end()
        for t in re.finditer(r'<(/?)%s\b[^>]*?(/?)>' % tag, svg[j:]):
            if t.group(2) == "/":
                continue
            depth += -1 if t.group(1) else 1
            if depth == 0:
                j += t.end()
                break
        i = j
    out.append(svg[i:])
    return "".join(out)


def _final(fn):
    return lambda static=False: final_state(fn(static=True)) if static else fn()


FIGS = {k: _final(v) for k, v in {
    **_FLAT,
    "equipo": fig_equipo,
    "nube": lambda static=False: fig_lazo(False, static),
    "edge": lambda static=False: fig_lazo(True, static),
    "senales": fig_senales,
}.items()}


if __name__ == "__main__":
    import cairosvg
    dst = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(dst, exist_ok=True)
    for name, fn in FIGS.items():
        open(os.path.join(dst, name + ".svg"), "w", encoding="utf-8").write(fn())
        cairosvg.svg2png(bytestring=fn(static=True).encode(), write_to=os.path.join(dst, name + ".png"),
                         background_color="white")
        print("✔", name)
