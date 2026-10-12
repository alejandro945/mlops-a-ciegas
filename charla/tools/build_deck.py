"""
Arma charla/devopsdays.html (un solo archivo, funciona sin internet) a partir de
charla/tools/deck.src.html + las figuras (build_iso.FIGS, que incluye build_figs.FIGS)
+ la arquitectura de AWS con los íconos oficiales + las cifras medidas de la PoC.

Marcadores de deck.src.html (ver charla/PLAN-bombas.md §3):
    {{FIG:nombre}}     build_iso.FIGS[nombre]()  · si falta: recuadro «figura pendiente» y un aviso
    {{M:clave}}        metrics.fmt(clave)        · también dentro de las notas del guion · sin medición: «por medir»
    {{AUDIO:a|b}}      charla/assets/audio/bomba-a.wav | bomba-b.wav como data URI · si falta: vacío (el botón sale
                       deshabilitado, «audio pendiente»)
    {{ARQ_GEN}}        el patrón genérico (capa lay-a); la AWS y la de la PoC son {{FIG:arq_ref}} y {{FIG:arq_poc}}
    {{FOTO}}, {{QR}}, {{REPO}}, {{LINKEDIN}}, {{IMG:…}}, {{FONT:…}}

Uso (desde la raíz del repo):
    AWS_ICONS=~/Downloads/Icon-package_07312026 python3 charla/tools/build_deck.py
    REPO_URL=https://github.com/usuario/mlops-a-ciegas AWS_ICONS=... python3 charla/tools/build_deck.py   # con QR
    LINKEDIN=linkedin.com/in/tu-perfil  ...                                                              # tu perfil
    STRICT=1 ...                                                                                         # falla si falta una figura
    Tu foto: guárdala como charla/assets/foto.jpg (cuadrada) y vuelve a correr el script.
"""
import base64, html as H, mimetypes, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_arch import build as arq, INK      # noqa: E402
from build_iso import FIGS                    # noqa: E402
import metrics                                # noqa: E402

CHARLA = os.path.dirname(HERE)
SRC = os.path.join(HERE, "deck.src.html")
DST = os.path.join(CHARLA, "devopsdays.html")
BACKUP = os.path.join(CHARLA, "decks", "devopsdays-v1-oscuro.html")
GUION = os.path.join(CHARLA, "GUION-devopsdays.md")
ASSETS = os.path.join(CHARLA, "assets")
FOTO = os.path.join(ASSETS, "foto.jpg")        # tu foto cuadrada (opcional)
AUDIO = os.environ.get("AUDIO_DIR") or os.path.join(ASSETS, "audio")   # bomba-a.wav · bomba-b.wav (los deja el agente del modelo)

PENDING_FIGS = []                              # figuras que todavía no existen
PENDING_AUDIO = []


def warn(msg):
    print("  (aviso)", msg)


def data_uri(path):
    mime = {".webp": "image/webp", ".woff2": "font/woff2", ".wav": "audio/wav"}.get(os.path.splitext(path)[1]) \
        or mimetypes.guess_type(path)[0]
    return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()


def foto_html():
    if os.path.exists(FOTO):
        return f'<div class="me-ph img" a="1"><img src="{data_uri(FOTO)}" alt="Alejandro Varela"></div>'
    return '<div class="me-ph" a="1">TU FOTO<small>charla/assets/foto.jpg</small></div>'


def audio_src(key):
    """{{AUDIO:a}} → data URI del WAV; sin archivo, cadena vacía (el deck apaga el botón: «audio pendiente»)."""
    path = os.path.join(AUDIO, f"bomba-{key}.wav")
    if not os.path.exists(path):
        PENDING_AUDIO.append(key)
        warn(f"audio pendiente: {os.path.relpath(path, os.path.dirname(CHARLA))}")
        return ""
    size = os.path.getsize(path)
    if size > 1_500_000:
        warn(f"el audio {key} pesa {size / 1e6:.1f} MB: el deck crece lo mismo (¿recortar a unos 10 s?)")
    return data_uri(path)


def metric(m):
    """{{M:v1.recall_source}} → '92 %'  ·  sin medición real: 'por medir' (lo decide metrics.fmt)."""
    return metrics.fmt(m.group(1))


def resolve_metrics(text):
    return re.sub(r"\{\{M:([\w.]+)\}\}", metric, text)


def pending_box(name):
    return f'<div class="pend">figura pendiente: {name}</div>'


def figure(name):
    """{{FIG:nombre}}. Una figura que aún no existe (o que falla al dibujarse) no rompe el armado: deja un recuadro y avisa."""
    fn = FIGS.get(name)
    if fn is None:
        PENDING_FIGS.append(name)
        warn(f"figura pendiente: {name}")
        return pending_box(name)
    try:
        svg = fn()
    except Exception as e:                       # figura a medio hacer: se ve, pero no tumba el deck
        PENDING_FIGS.append(name)
        warn(f"la figura {name} falló al dibujarse ({type(e).__name__}: {e})")
        if os.environ.get("STRICT"):
            raise
        return pending_box(name)
    return svg


def notes_from_guion():
    """Cada '## …' del guion con '<!-- id: x -->' pasa a ser la nota de la lámina data-id="x"."""
    if not os.path.exists(GUION):
        return {}
    out = {}
    for part in re.split(r"^## ", open(GUION, encoding="utf-8").read(), flags=re.M)[1:]:
        m = re.search(r"<!--\s*id:\s*([\w-]+)\s*-->", part)
        if not m:
            continue
        title = part.splitlines()[0].strip()
        body = part[m.end():].split("\n---")[0]
        body = body.replace("**[CLIC]**", "▶ CLIC").replace("**", "").replace("`", "")
        body = re.sub(r"(?m)^\s*>\s?", "", body)
        body = re.sub(r"\n{3,}", "\n\n", body).strip()
        body = resolve_metrics(body)             # las cifras medidas también valen en las notas
        out[m.group(1)] = (title.upper() + "\n\n" + body).replace('"', "'")
    return out


def inject_notes(html):
    notes = notes_from_guion()
    for sid, txt in notes.items():
        pat = re.compile(r'(<section class="s[^"]*" data-id="%s"[^>]*?data-notes=")[^"]*(")' % re.escape(sid))
        html, n = pat.subn(lambda m: m.group(1) + H.escape(txt, quote=False) + m.group(2), html, count=1)
        if not n:
            print("  (aviso) sin lámina para la nota:", sid)
    return html


def layer(svg, cls):
    return svg.replace('class="arq"', f'class="arq {cls}"', 1)


def qr_svg(url):
    try:
        import qrcode
    except ImportError:
        return None
    q = qrcode.QRCode(border=0, error_correction=qrcode.constants.ERROR_CORRECT_M)
    q.add_data(url); q.make(fit=True)
    m = q.get_matrix(); n = len(m)
    d = "".join(f"M{x},{y}h1v1h-1z" for y, row in enumerate(m) for x, v in enumerate(row) if v)
    return f'<svg viewBox="0 0 {n} {n}" shape-rendering="crispEdges"><path d="{d}" fill="{INK}"/></svg>'


def main():
    html = open(SRC, encoding="utf-8").read()
    repo = os.environ.get("REPO_URL", "")
    qr = qr_svg(repo) if repo else None
    rep = {
        "{{QR}}":             lambda: qr or "QR del repo<br>se genera con REPO_URL",
        "{{REPO}}":           lambda: re.sub(r"^https?://", "", repo) if repo else "github.com/⟨usuario⟩/mlops-a-ciegas",
        "{{LINKEDIN}}":       lambda: os.environ.get("LINKEDIN", "linkedin.com/in/⟨tu-perfil⟩"),
        "{{FOTO}}":           foto_html,
        "{{ARQ_GEN}}":        lambda: layer(arq("gen", deck=True), "lay-a"),
    }
    for k, fn in rep.items():
        if k in html:
            html = html.replace(k, fn())
    # audios de la lámina 2: {{AUDIO:a}} · {{AUDIO:b}}
    html = re.sub(r"\{\{AUDIO:([ab])\}\}", lambda m: audio_src(m.group(1)), html)
    # figuras por nombre: {{FIG:onda_a}} → build_iso.FIGS["onda_a"]()
    html = re.sub(r"\{\{FIG:([\w-]+)\}\}", lambda m: figure(m.group(1)), html)
    # imágenes de la plantilla y la letra, embebidas: el archivo funciona sin internet
    html = re.sub(r"\{\{IMG:([\w.-]+)\}\}", lambda m: data_uri(os.path.join(ASSETS, "plantilla", m.group(1))), html)
    html = re.sub(r"\{\{FONT:([\w.-]+)\}\}", lambda m: data_uri(os.path.join(ASSETS, "fonts", m.group(1) + ".woff2")), html)
    html = inject_notes(html)
    html = resolve_metrics(html)                 # cifras medidas: en las láminas y en las notas
    left = re.findall(r"\{\{[A-Z_]+(?::[\w.-]+)?\}\}", html)
    if left:
        sys.exit(f"marcadores sin resolver: {left}")
    if PENDING_FIGS and os.environ.get("STRICT"):
        sys.exit(f"figuras pendientes: {sorted(set(PENDING_FIGS))}")

    if os.path.exists(DST) and not os.path.exists(BACKUP):
        old = open(DST, encoding="utf-8").read()
        if "EPAM Proprietary" in old:          # sólo respaldamos el deck oscuro original
            os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
            shutil.copyfile(DST, BACKUP)
            print("respaldo:", BACKUP)
    open(DST, "w", encoding="utf-8").write(html)
    n_all = len(re.findall(r'<section class="s', html))
    n_anx = html.count('data-annex="1"')
    print(f"✔ {DST}  ({len(html.encode()) / 1024:.0f} KB · {n_all - n_anx} láminas + {n_anx} anexos)")
    print("  medición real de la PoC:", "sí" if metrics.ready() else "no (las cifras salen como «por medir»)")
    if PENDING_FIGS:
        print("  figuras pendientes:", ", ".join(sorted(set(PENDING_FIGS))))
    if PENDING_AUDIO:
        print("  audios pendientes:", ", ".join(sorted(set(PENDING_AUDIO))))


if __name__ == "__main__":
    main()
