"""
The figures of the Tech Day Cali deck, as SVG (snap.js renders them with Chrome and Montserrat).

Every number comes from data.json (extract.py): the October 18 rehearsal on AWS and the shadow
measured with the pumps' own component. The spectrograms come from the two clips of the opening
question (talk/assets/audio), drawn with matplotlib.

Usage:  python3 figs.py build/svg        (the spectrograms need numpy and matplotlib)
"""
import json, math, os, sys, wave

HERE = os.path.dirname(os.path.abspath(__file__))
TALK = os.path.abspath(os.path.join(HERE, "..", ".."))
D = json.load(open(os.path.join(HERE, "data.json"), encoding="utf-8"))

NAVY, GREEN, YELLOW, ORANGE, CYAN, TEAL = "#0B132A", "#12D18E", "#FFC700", "#FF5A1F", "#1ED4E8", "#1F8F7A"
SLATE, LINE, WHITE = "#5C6B85", "#D9E2EE", "#FFFFFF"
FONT = "Montserrat, Helvetica, Arial, sans-serif"


# ── helpers ───────────────────────────────────────────────────────────
def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'font-family="{FONT}">{body}</svg>')


def t(x, y, s, size=24, color=NAVY, weight=500, anchor="start", op=1, ls=0):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" fill-opacity="{op}" '
            f'text-anchor="{anchor}" letter-spacing="{ls}">{s}</text>')


def arrow(x1, y1, x2, y2, color=NAVY, w=3, head=12, dash=""):
    a = math.atan2(y2 - y1, x2 - x1)
    p1 = (x2 - head * math.cos(a - .45), y2 - head * math.sin(a - .45))
    p2 = (x2 - head * math.cos(a + .45), y2 - head * math.sin(a + .45))
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2 - 4 * math.cos(a):.1f}" y2="{y2 - 4 * math.sin(a):.1f}" '
            f'stroke="{color}" stroke-width="{w}"{d}/>'
            f'<polygon points="{x2},{y2} {p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}" fill="{color}"/>')


def secs(hms):
    h, m, s = map(int, hms.split(":"))
    return h * 3600 + m * 60 + s


def pm(hms):
    """19:58:36 → 7:58:36 p.m."""
    h, m, s = hms.split(":")
    return f"{int(h) - 12}:{m}:{s}"


# ── 5 · one person, a thousand pumps ──────────────────────────────────
def mil():
    w, h = 1500, 560
    b = []
    # the person
    b.append(f'<circle cx="150" cy="190" r="46" fill="{ORANGE}"/>'
             f'<path d="M70,360 Q70,262 150,262 Q230,262 230,360 Z" fill="{ORANGE}"/>')
    b.append(t(150, 430, "1", 64, NAVY, 800, "middle"))
    b.append(t(150, 470, "mecánico", 24, SLATE, 500, "middle"))
    # a thousand pumps: 50 × 20
    x0, y0, step = 340, 60, 22.5
    for i in range(1000):
        cx, cy = x0 + (i % 50) * step, y0 + (i // 50) * step
        b.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="7" fill="{NAVY}" fill-opacity=".8"/>')
    b.append(t(x0 + 49 * step / 2, 540, "1.000 bombas", 30, NAVY, 700, "middle"))
    return svg(w, h, "".join(b))


# ── 6 · 20 W ──────────────────────────────────────────────────────────
def bombillo():
    w, h = 300, 420
    return svg(w, h, (
        f'<circle cx="150" cy="150" r="118" fill="{YELLOW}"/>'
        f'<path d="M92,236 L208,236 L196,300 L104,300 Z" fill="{YELLOW}"/>'
        f'<rect x="104" y="312" width="92" height="22" rx="6" fill="{NAVY}"/>'
        f'<rect x="112" y="342" width="76" height="22" rx="6" fill="{NAVY}"/>'
        f'<rect x="128" y="372" width="44" height="18" rx="6" fill="{NAVY}"/>'
        ''))


# ── 8 and 15 · the rarity score against its line (act 1, real) ────────
def puntaje(dark=False):
    a1, thr = D["act1"], D["threshold"]
    ink = WHITE if dark else NAVY
    sub = "#AAB6CB" if dark else SLATE
    w, h = 1500, 600
    x0, x1, y0, y1 = 150, 1430, 60, 470
    lo, hi = 0.15, 0.46
    X = lambda i: x0 + (x1 - x0) * i / (len(a1) - 1)
    Y = lambda v: y1 - (y1 - y0) * (v - lo) / (hi - lo)
    b = [f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="{sub}" stroke-width="2"/>']
    # the line: the threshold
    b.append(f'<line x1="{x0}" y1="{Y(thr):.1f}" x2="{x1}" y2="{Y(thr):.1f}" stroke="{ORANGE}" stroke-width="4" stroke-dasharray="14 10"/>')
    b.append(t(x0 - 16, Y(thr) + 9, "límite", 26, ORANGE, 700, "end"))
    pts = " ".join(f"{X(i):.1f},{Y(e['score']):.1f}" for i, e in enumerate(a1))
    b.append(f'<polyline points="{pts}" fill="none" stroke="{ink}" stroke-width="4" stroke-opacity=".55"/>')
    for i, e in enumerate(a1):
        c = ORANGE if e["alert"] else GREEN
        b.append(f'<circle cx="{X(i):.1f}" cy="{Y(e["score"]):.1f}" r="13" fill="{c}"/>')
    first = next(i for i, e in enumerate(a1) if e["alert"])
    b.append(t(X(first) + 24, Y(a1[first]["score"]) - 4, "alerta", 30, ORANGE, 800))
    b.append(t(x0 - 16, Y(0.22) + 9, "normal", 26, GREEN, 700, "end"))
    for i in (0, first, len(a1) - 1):
        b.append(t(X(i), y1 + 50, pm(a1[i]["t"]), 24, sub, 500, "middle"))
    b.append(t(x0 - 16, y0 - 14, "puntaje de rareza", 24, sub, 600, "start"))
    return svg(w, h, "".join(b))


# ── 9 · 115 MB per hour against one line ──────────────────────────────
def cuenta():
    w, h = 1300, 330
    b = [f'<rect x="0" y="40" width="1200" height="90" rx="10" fill="{NAVY}"/>',
         t(30, 100, "Audio crudo · 115 MB por hora, por bomba", 34, WHITE, 700),
         f'<rect x="0" y="200" width="6" height="90" rx="2" fill="{GREEN}"/>',
         t(34, 236, "Una línea por decisión · unos cientos de bytes", 34, NAVY, 700),
         t(34, 282, '{"device": "pump-03", "alert": true, "score": 0.42 …}', 24, SLATE, 500)]
    return svg(w, h, "".join(b))


# ── 10 · the pendulum ─────────────────────────────────────────────────
def pendulo():
    w, h = 1700, 560
    xs = [200, 600, 1000, 1450]
    labels = [("Mainframe", "todo en el centro"), ("PC", "todo en tu escritorio"),
              ("Nube", "todo al centro otra vez"), ("Dispositivo", "decide donde nace el dato")]
    years = ["1960", "1980", "2010", "hoy"]
    b = [f'<path d="M{xs[0]},300 C{xs[0] + 200},420 {xs[1] - 200},420 {xs[1]},300 C{xs[1] + 200},180 {xs[2] - 200},180 {xs[2]},300 '
         f'C{xs[2] + 220},420 {xs[3] - 220},420 {xs[3]},300" fill="none" stroke="{LINE}" stroke-width="6"/>']
    for i, x in enumerate(xs):
        last = i == 3
        c = GREEN if last else NAVY
        b.append(f'<circle cx="{x}" cy="300" r="{92 if last else 78}" fill="{c}"/>')
        b.append(ICONS[i](x, 300, WHITE if not last else NAVY))
        b.append(t(x, 450, labels[i][0], 36 if last else 32, NAVY, 800 if last else 700, "middle"))
        b.append(t(x, 492, labels[i][1], 24, SLATE, 500, "middle"))
        b.append(t(x, 180 if i != 2 else 170, years[i], 26, SLATE if not last else TEAL, 700, "middle"))
    return svg(w, h, "".join(b))


def _i_mainframe(x, y, c):
    return "".join(f'<rect x="{x - 30}" y="{y - 40 + k * 28}" width="60" height="20" rx="3" fill="none" stroke="{c}" stroke-width="5"/>'
                   f'<circle cx="{x + 18}" cy="{y - 30 + k * 28}" r="3.5" fill="{c}"/>' for k in range(3))


def _i_pc(x, y, c):
    return (f'<rect x="{x - 40}" y="{y - 36}" width="80" height="54" rx="5" fill="none" stroke="{c}" stroke-width="5"/>'
            f'<rect x="{x - 8}" y="{y + 18}" width="16" height="14" fill="{c}"/><rect x="{x - 26}" y="{y + 32}" width="52" height="6" rx="2" fill="{c}"/>')


def _i_cloud(x, y, c):
    return (f'<path d="M{x - 44},{y + 22} a24,24 0 0 1 6,-46 a32,32 0 0 1 58,-8 a24,24 0 0 1 24,54 Z" '
            f'fill="none" stroke="{c}" stroke-width="5" stroke-linejoin="round"/>')


def _i_chip(x, y, c):
    pins = "".join(f'<line x1="{x - 24 + k * 16}" y1="{y - 46}" x2="{x - 24 + k * 16}" y2="{y - 34}" stroke="{c}" stroke-width="5"/>'
                   f'<line x1="{x - 24 + k * 16}" y1="{y + 34}" x2="{x - 24 + k * 16}" y2="{y + 46}" stroke="{c}" stroke-width="5"/>'
                   f'<line x1="{x - 46}" y1="{y - 24 + k * 16}" x2="{x - 34}" y2="{y - 24 + k * 16}" stroke="{c}" stroke-width="5"/>'
                   f'<line x1="{x + 34}" y1="{y - 24 + k * 16}" x2="{x + 46}" y2="{y - 24 + k * 16}" stroke="{c}" stroke-width="5"/>'
                   for k in range(4))
    return (f'<rect x="{x - 34}" y="{y - 34}" width="68" height="68" rx="8" fill="none" stroke="{c}" stroke-width="5"/>'
            f'<text x="{x}" y="{y + 10}" font-size="26" font-weight="800" fill="{c}" text-anchor="middle">IA</text>' + pins)


ICONS = [_i_mainframe, _i_pc, _i_cloud, _i_chip]


# ── 12 · the suitcase: 464 → 127 KB ──────────────────────────────────
def maleta():
    w, h = 1400, 420
    full, small = 464, 127
    W = 1100
    b = [t(0, 50, "Modelo original", 30, SLATE, 600),
         f'<rect x="0" y="70" width="{W}" height="90" rx="10" fill="{NAVY}"/>',
         t(W + 24, 132, "464 KB", 44, NAVY, 800),
         t(0, 250, "Comprimido (INT8)", 30, SLATE, 600),
         f'<rect x="0" y="270" width="{W * small / full:.0f}" height="90" rx="10" fill="{GREEN}"/>',
         t(W * small / full + 24, 332, "127 KB", 44, NAVY, 800)]
    return svg(w, h, "".join(b))


# ── 13 · blind: the cloud sees, the field does not ────────────────────
def ciegas():
    w, h = 1760, 640
    b = []
    # left: the cloud, with an eye
    b.append(f'<rect x="0" y="0" width="760" height="640" rx="24" fill="#EAF0F8"/>')
    b.append(f'<path d="M210,320 a70,70 0 0 1 14,-138 a96,96 0 0 1 176,-26 a74,74 0 0 1 72,164 Z" '
             f'fill="{WHITE}" stroke="{NAVY}" stroke-width="8" stroke-linejoin="round"/>')
    b.append(_eye(372, 262, NAVY, crossed=False, s=1.0))
    b.append(t(380, 420, "En la nube", 40, NAVY, 800, "middle"))
    b.append(t(380, 470, "cada predicción, cada error, a la mano", 26, SLATE, 500, "middle"))
    # right: a thousand devices, far away, with the eye crossed out
    b.append(f'<rect x="820" y="0" width="940" height="640" rx="24" fill="{NAVY}"/>')
    for i in range(36):
        cx, cy = 900 + (i % 12) * 70, 70 + (i // 12) * 60
        b.append(f'<rect x="{cx - 18}" y="{cy - 14}" width="36" height="28" rx="5" fill="{WHITE}" fill-opacity=".25"/>')
    b.append(_eye(1290, 300, WHITE, crossed=True, s=1.4))
    b.append(t(1290, 450, "En mil equipos, lejos", 40, WHITE, 800, "middle"))
    # the green panel that lies
    for k, (lab, val) in enumerate((("CPU", "OK"), ("Memoria", "OK"), ("Errores", "0"))):
        x = 900 + k * 270
        b.append(f'<rect x="{x}" y="500" width="240" height="90" rx="12" fill="{GREEN}"/>')
        b.append(t(x + 22, 540, lab, 24, NAVY, 600))
        b.append(t(x + 22, 574, val, 30, NAVY, 800))
    return svg(w, h, "".join(b))


def _eye(cx, cy, c, crossed=False, s=1.0):
    r = 34 * s
    e = (f'<path d="M{cx - 70 * s},{cy} Q{cx},{cy - 62 * s} {cx + 70 * s},{cy} Q{cx},{cy + 62 * s} {cx - 70 * s},{cy} Z" '
         f'fill="none" stroke="{c}" stroke-width="{7 * s}"/><circle cx="{cx}" cy="{cy}" r="{r * .62}" fill="{c}"/>')
    if crossed:
        e += f'<line x1="{cx - 80 * s}" y1="{cy + 60 * s}" x2="{cx + 80 * s}" y2="{cy - 60 * s}" stroke="{ORANGE}" stroke-width="{10 * s}" stroke-linecap="round"/>'
    return e


# ── 15 · act 1 on the night (dark) ───────────────────────────────────
def acto1():
    a1 = D["act1"]
    w, h = 1700, 300
    b = []
    step = 1500 / (len(a1) - 1)
    first = next(i for i, e in enumerate(a1) if e["alert"])
    for i, e in enumerate(a1):
        x = 100 + i * step
        b.append(f'<circle cx="{x:.1f}" cy="130" r="26" fill="{ORANGE if e["alert"] else GREEN}"/>')
    xf = 100 + first * step
    b.append(f'<line x1="{xf - step / 2:.1f}" y1="40" x2="{xf - step / 2:.1f}" y2="200" stroke="{WHITE}" stroke-width="3" stroke-dasharray="8 8"/>')
    b.append(t(xf - step / 2 - 16, 40, "la bomba empieza a fallar", 26, WHITE, 600, "end"))
    b.append(t(xf, 250, pm(a1[first]["t"]), 30, ORANGE, 800, "middle"))
    b.append(t(100, 250, pm(a1[0]["t"]), 26, "#AAB6CB", 500, "middle"))
    b.append(t(100, 290, "cada punto: un clip que la bomba 3 escuchó y decidió", 22, "#AAB6CB", 500))
    return svg(w, h, "".join(b))


# ── 3 and 15 · the spectrograms of the opening question ───────────────
def espectros(out_dir):
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import font_manager, pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    for f in os.listdir(os.path.expanduser("~/Library/Fonts")):
        if f.startswith("Montserrat-"):
            font_manager.fontManager.addfont(os.path.join(os.path.expanduser("~/Library/Fonts"), f))
    plt.rcParams["font.family"] = "Montserrat"

    def spec(path):
        w = wave.open(path)
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
        if w.getnchannels() > 1:
            x = x.reshape(-1, w.getnchannels())[:, 0]
        sr, n, hop = w.getframerate(), 1024, 256
        win = np.hanning(n)
        frames = np.stack([x[i:i + n] * win for i in range(0, len(x) - n, hop)])
        S = np.abs(np.fft.rfft(frames, axis=1)).T
        return 20 * np.log10(S + 1e-6), sr

    A, sr = spec(os.path.join(TALK, "assets", "audio", "pump-a.wav"))
    B, _ = spec(os.path.join(TALK, "assets", "audio", "pump-b.wav"))
    top = 400                                     # 0 – 6.25 kHz: where the pump lives
    A, B = A[:top], B[:top]
    vmin, vmax = np.percentile(np.concatenate([A, B]), [5, 99.5])
    cmap = LinearSegmentedColormap.from_list("tdc", [NAVY, "#1D3A6B", TEAL, GREEN, YELLOW])
    # where B differs most from A: the band the model notices
    diff = np.abs(B - A).mean(axis=1)                 # how differently each frequency sounds
    smooth = np.convolve(diff, np.ones(80) / 80, mode="same")[40:top - 40]
    k = 40 + int(np.argmax(smooth))
    band = (k - 40, k + 40)
    # one opaque JPEG per spectrogram (the slide writes the labels): A, B, and B with the band marked
    for name, S, marked in (("espectro-a", A, False), ("espectro-b", B, False), ("espectro-b-marcado", B, True)):
        fig = plt.figure(figsize=(8, 5.6), dpi=150)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.imshow(S, origin="lower", aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax)
        ax.set_axis_off()
        if marked:
            from matplotlib.patches import Rectangle
            ax.add_patch(Rectangle((2, band[0]), S.shape[1] - 5, band[1] - band[0] - 2, fill=False,
                                   edgecolor=ORANGE, linewidth=7))
        fig.savefig(os.path.join(out_dir, name + ".jpg"), pil_kwargs={"quality": 82})
        plt.close(fig)
    return band


# ── 16 · the urgent now, the heavy later ──────────────────────────────
def lotes():
    w, h = 1700, 520
    b = [t(0, 50, "Lo urgente · ya", 34, NAVY, 800), t(0, 92, "una línea por decisión, al instante", 24, SLATE, 500)]
    for i in range(30):
        x = 10 + i * 52
        b.append(f'<rect x="{x}" y="120" width="34" height="26" rx="5" fill="{CYAN}"/>')
    b.append(t(0, 280, "Lo pesado · por lotes", 34, NAVY, 800))
    b.append(t(0, 322, "solo el audio que importa, cuando hay buena red", 24, SLATE, 500))
    for i, (x, lab) in enumerate(((10, "alerta"), (420, "dudoso"), (830, "desacuerdo"), (1240, "muestra"))):
        b.append(f'<rect x="{x}" y="350" width="360" height="90" rx="12" fill="{TEAL}"/>')
        for k in range(14):
            hh = [18, 40, 26, 54, 30, 60, 44, 24, 50, 20, 38, 28, 46, 16][k]
            b.append(f'<rect x="{x + 22 + k * 12}" y="{395 - hh / 2}" width="6" height="{hh}" rx="2" fill="{WHITE}" fill-opacity=".85"/>')
        b.append(t(x + 210, 405, lab, 24, WHITE, 700))
    b.append(t(0, 500, "sin red: todo espera en el disco · nada se pierde", 26, TEAL, 700))
    return svg(w, h, "".join(b))


# ── 17 · act 2: the network goes away (dark) ──────────────────────────
def acto2():
    win = D["act2"]["window"]
    off0, off1 = map(secs, D["act2"]["offline"])
    t0, t1 = secs("19:59:00"), secs("20:00:40")
    w, h = 1700, 560
    X = lambda s: 160 + 1480 * (s - t0) / (t1 - t0)
    pumps = ["pump-01", "pump-02", "pump-03", "pump-04", "pump-05"]
    b = [f'<rect x="{X(off0):.1f}" y="10" width="{X(off1) - X(off0):.1f}" height="440" fill="{ORANGE}" fill-opacity=".14"/>',
         t((X(off0) + X(off1)) / 2, 44, "45 s sin red · bomba 3", 26, ORANGE, 800, "middle")]
    for r, p in enumerate(pumps):
        y = 100 + r * 76
        b.append(t(140, y + 9, f"bomba {int(p[-2:])}", 24, WHITE, 700 if p == "pump-03" else 500, "end"))
        for e in win:
            if e["device"] != p:
                continue
            s = secs(e["t"]) - e["late"]            # when the pump decided
            if not t0 <= s <= t1:
                continue
            if e["late"]:
                b.append(f'<circle cx="{X(s):.1f}" cy="{y}" r="11" fill="none" stroke="{YELLOW}" stroke-width="4"/>')
            else:
                b.append(f'<circle cx="{X(s):.1f}" cy="{y}" r="11" fill="{ORANGE if e["alert"] else GREEN}"/>')
    arr = secs(next(e["t"] for e in win if e["late"]))
    b.append(t(X(arr) + 18, 498, f"{len(D['act2']['late_seconds'])} reportes llegan juntos, hasta "
               f"{max(D['act2']['late_seconds'])} s tarde", 26, YELLOW, 700, "middle"))
    b.append(f'<circle cx="{X(t0) + 10}" cy="490" r="10" fill="none" stroke="{YELLOW}" stroke-width="4"/>')
    b.append(t(X(t0) + 30, 498, "decidió sin red y lo guardó", 22, YELLOW, 600))
    b.append(t(X(t0), 548, "7:59:00 p.m.", 22, "#AAB6CB", 500))
    b.append(t(X(t1), 548, "8:00:40 p.m.", 22, "#AAB6CB", 500, "end"))
    return svg(w, h, "".join(b))


# ── 18 · listen to the listener: pump 5's input ───────────────────────
def entrada():
    p5 = D["act2"]["pump05"]
    w, h = 1500, 560
    t0, t1 = secs(p5[0]["t"]), secs(p5[-1]["t"])
    X = lambda s: 240 + 1240 * (s - t0) / (t1 - t0)
    Y = lambda v: 480 - 360 * (v - 0.4) / (2.0 - 0.4)
    b = [f'<rect x="240" y="{Y(1.0):.1f}" width="1240" height="{Y(0.6) - Y(1.0):.1f}" fill="{GREEN}" fill-opacity=".16"/>',
         t(228, Y(0.8) - 6, "lo que", 28, TEAL, 700, "end"), t(228, Y(0.8) + 26, "aprendió", 28, TEAL, 700, "end")]
    pts = " ".join(f"{X(secs(e['t'])):.1f},{Y(e['input']):.1f}" for e in p5)
    b.append(f'<polyline points="{pts}" fill="none" stroke="{NAVY}" stroke-width="4"/>')
    for e in p5:
        if e["alert"]:
            b.append(f'<circle cx="{X(secs(e["t"])):.1f}" cy="{Y(e["input"]):.1f}" r="11" fill="{ORANGE}"/>')
    hi = max(p5, key=lambda e: e["input"])
    b.append(t(X(secs(hi["t"])), Y(hi["input"]) - 28, "le cambiamos la velocidad", 32, NAVY, 700, "middle"))
    b.append(t(240, 548, "● alertas que no eran fallas", 28, ORANGE, 700))
    return svg(w, h, "".join(b))


# ── 20 · the "improved" ear was deaf (dark) ───────────────────────────
def sordo():
    f = D["shadow"]["fault"]
    w, h = 1700, 420
    b = []
    for r, (key, lab) in enumerate((("v1", "versión 1 · decide"), ("v2", "versión 2 · en sombra"))):
        y = 80 + r * 170
        b.append(t(0, y - 34, lab, 28, WHITE, 700))
        for i, e in enumerate(f):
            x = 20 + i * 41
            if e[key]:
                b.append(f'<circle cx="{x}" cy="{y + 20}" r="15" fill="{ORANGE}"/>')
            else:
                b.append(f'<circle cx="{x}" cy="{y + 20}" r="13" fill="none" stroke="{WHITE}" stroke-opacity=".55" stroke-width="3"/>')
    v1 = sum(e["v1"] for e in f)
    miss = sum(e["v1"] and not e["v2"] for e in f)
    b.append(t(0, 400, f"la bomba 1 fallando · {len(f)} clips · la versión 1 alertó en {v1} · la versión 2 no oyó {miss}",
               24, "#AAB6CB", 500))
    return svg(w, h, "".join(b))


# ── 21 · the judge (Step Functions), as the audience reads it ─────────
def juez():
    w, h = 1700, 620
    steps = [("Desplegar", "en sombra, en 1 bomba"), ("Esperar", "que escuche de verdad"),
             ("Medir", "¿oye lo que oye la 1?"), ("¿Pasa?", "")]
    b = []
    for i, (a, s) in enumerate(steps):
        x = 20 + i * 330
        diamond = a == "¿Pasa?"
        if diamond:
            cx, cy = x + 140, 150
            b.append(f'<polygon points="{cx},{cy - 100} {cx + 130},{cy} {cx},{cy + 100} {cx - 130},{cy}" fill="{NAVY}"/>')
            b.append(t(cx, cy + 12, a, 34, WHITE, 800, "middle"))
        else:
            b.append(f'<rect x="{x}" y="70" width="280" height="160" rx="18" fill="{WHITE}" stroke="{NAVY}" stroke-width="4"/>')
            b.append(t(x + 140, 140, a, 34, NAVY, 800, "middle"))
            b.append(t(x + 140, 184, s, 19, SLATE, 500, "middle"))
            b.append(arrow(x + 286, 150, x + 326, 150, NAVY, 4))
    cx = 20 + 3 * 330 + 140
    # yes: promote (greyed: not this time) · no: reject (orange)
    b.append(arrow(cx + 130, 150, 1440, 150, LINE, 4))
    b.append(f'<rect x="1446" y="90" width="240" height="120" rx="18" fill="{WHITE}" stroke="{LINE}" stroke-width="4"/>')
    b.append(t(1566, 142, "Sí", 30, "#9AA7BD", 800, "middle"))
    b.append(t(1566, 180, "a todas las bombas", 20, "#9AA7BD", 500, "middle"))
    b.append(arrow(cx, 254, cx, 360, ORANGE, 5))
    b.append(f'<rect x="{cx - 330}" y="366" width="660" height="150" rx="18" fill="{ORANGE}"/>')
    b.append(t(cx, 428, "No pasa", 40, WHITE, 800, "middle"))
    b.append(t(cx, 474, "la bomba vuelve a la versión 1 · aviso al equipo", 22, WHITE, 600, "middle"))
    b.append(t(20, 600, "Step Functions · un flujo automático que nadie tiene que acordarse de correr", 24, SLATE, 500))
    return svg(w, h, "".join(b))


# ── 22 · how a deaf ear gets fixed ────────────────────────────────────
def arreglo():
    w, h = 1500, 560
    nodes = [("El audio que importa", "ya está en la nube"), ("Mantenimiento", "confirma qué era falla"),
             ("Datos limpios", "se entrena la versión 3"), ("El mismo juez", "decide si pasa")]
    pos = [(380, 110), (1120, 110), (1120, 420), (380, 420)]
    b = []
    for i, ((a, s), (x, y)) in enumerate(zip(nodes, pos)):
        c = GREEN if i == 2 else NAVY
        b.append(f'<rect x="{x - 250}" y="{y - 70}" width="500" height="140" rx="20" fill="{c}"/>')
        b.append(t(x, y - 6, a, 32, WHITE if i != 2 else NAVY, 800, "middle"))
        b.append(t(x, y + 36, s, 22, WHITE if i != 2 else NAVY, 500, "middle", op=.85))
    b.append(arrow(640, 110, 860, 110, TEAL, 5))
    b.append(arrow(1120, 190, 1120, 340, TEAL, 5))
    b.append(arrow(860, 420, 640, 420, TEAL, 5))
    b.append(arrow(380, 340, 380, 190, TEAL, 5))
    return svg(w, h, "".join(b))


# ── 25 · the QR to the repo ───────────────────────────────────────────
def qr(png_dir, url="https://github.com/alejandro945/mlops-a-ciegas"):
    import qrcode
    q = qrcode.QRCode(box_size=24, border=2)
    q.add_data(url)
    q.make_image(fill_color=NAVY, back_color=WHITE).save(os.path.join(png_dir, "qr.png"))


FIGS = {"mil": mil, "bombillo": bombillo, "puntaje": puntaje, "puntaje-noche": lambda: puntaje(True),
        "cuenta": cuenta, "pendulo": pendulo, "maleta": maleta, "ciegas": ciegas, "acto1": acto1,
        "lotes": lotes, "acto2": acto2, "entrada": entrada, "sordo": sordo, "juez": juez, "arreglo": arreglo}

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "build", "svg")
    os.makedirs(out, exist_ok=True)
    for name, f in FIGS.items():
        open(os.path.join(out, name + ".svg"), "w", encoding="utf-8").write(f())
    png = os.path.join(os.path.dirname(out), "png")
    os.makedirs(png, exist_ok=True)
    band = espectros(png)
    qr(png)
    print(f"✔ {len(FIGS) + 1} SVG in {out} · spectrograms in {png} (marked band, bins {band[0]}–{band[1]})")
