"""
Builds talk/devopsdays.html (a single file that works offline) from
talk/tools/deck.src.html + the figures (build_iso.FIGS, which includes build_figs.FIGS)
+ the AWS architecture with the official icons + the PoC's measured numbers.

Placeholders in deck.src.html:
    {{FIG:name}}       build_iso.FIGS[name]()    · if missing: a «figura pendiente» box and a warning
    {{M:key}}          metrics.fmt(key)          · also inside the script's speaker notes · not measured: «por medir»
    {{AUDIO:a|b}}      talk/assets/audio/pump-a.wav | pump-b.wav as a data URI · if missing: empty (the button is
                       disabled, «audio pendiente»)
    {{ARCH_GENERIC}}   the generic pattern (layer lay-a); the AWS one and the PoC one are {{FIG:arq_ref}} and {{FIG:arq_poc}}
    {{PHOTO}}, {{QR}}, {{REPO}}, {{LINKEDIN}}, {{IMG:…}} (assets/template), {{BADGE:…}} (assets/badges), {{FONT:…}}
    {{SHOT:name}}      talk/assets/screens/name.png (or .jpg): an AWS console screenshot · if missing: a «captura pendiente»
                       box that says what to capture (SHOTS below) and a warning

Usage (from the repo root):
    AWS_ICONS=~/Downloads/Icon-package_07312026 python3 talk/tools/build_deck.py
    REPO_URL=https://github.com/user/mlops-a-ciegas AWS_ICONS=... python3 talk/tools/build_deck.py      # with QR
    LINKEDIN=linkedin.com/in/your-profile  ...                                                          # your profile
    STRICT=1 ...                                                                                        # fail if a figure is missing
    DECK_OUT=/tmp/deck.html ...                                                                         # write somewhere else
    STATION_AUDIO_DIR=...                                                                               # other pump-a/b.wav folder
    Your photo: save it as talk/assets/photo.jpg (or .jpeg / .png) and run the script again; it is cropped to a square.
"""
import base64, html as H, mimetypes, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_arch import build as arch, INK     # noqa: E402
from build_iso import FIGS                    # noqa: E402
import metrics                                # noqa: E402

TALK = os.path.dirname(HERE)
SRC = os.path.join(HERE, "deck.src.html")
DST = os.environ.get("DECK_OUT") or os.path.join(TALK, "devopsdays.html")
SCRIPT = os.path.join(TALK, "GUION-devopsdays.md")    # the speaker script (Spanish)
ASSETS = os.path.join(TALK, "assets")
# your photo (optional): photo.jpg, photo.jpeg or photo.png; it is cropped to a centered square
PHOTO = next((os.path.join(ASSETS, f"photo.{e}") for e in ("jpg", "jpeg", "png")
              if os.path.exists(os.path.join(ASSETS, f"photo.{e}"))), os.path.join(ASSETS, "photo.jpg"))
AUDIO = (os.environ.get("STATION_AUDIO_DIR") or os.environ.get("AUDIO_DIR")
         or os.path.join(ASSETS, "audio"))     # pump-a.wav · pump-b.wav (written by model/prepare_data.py)

PENDING_FIGS = []                              # figures that do not exist yet
PENDING_AUDIO = []
PENDING_SHOTS = []

SCREENS = os.path.join(ASSETS, "screens")      # AWS evidence of the PoC, one per step (see assets/screens/README.md)
# name → what it shows (Spanish: it shows on the slide while the file is missing). Same list in assets/screens/README.md.
SHOTS = {
    "s3-versiones":   "consola de S3: el bucket › station/, con las carpetas 1.0.0/ y 2.0.0/",
    "gg-componente":  "consola de IoT Greengrass: com.station.Listener, con sus versiones 1.0.0 y 2.0.0",
    "gg-despliegues": "consola de IoT Greengrass › Deployments: StationRing0 (rollback, activo) y StationRing1",
    "gg-equipos":     "consola de IoT Greengrass › Core devices: pump-01 a pump-05, Healthy",
    "cw-dashboard":   "consola de CloudWatch: el dashboard station, con los totales y la entrada por bomba",
    "cw-alarma":      "consola de CloudWatch: la alarma station-missed-faults, con su gráfica y el momento en ALARM",
}


def warn(msg):
    print("  (warning)", msg)


def data_uri(path):
    mime = {".webp": "image/webp", ".woff2": "font/woff2", ".wav": "audio/wav"}.get(os.path.splitext(path)[1]) \
        or mimetypes.guess_type(path)[0]
    return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()


def photo_uri():
    """The photo as a centered square, 840 px, JPEG: a phone photo is several MB and only 420 px are shown."""
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return data_uri(PHOTO)
    import io
    im = ImageOps.exif_transpose(Image.open(PHOTO)).convert("RGB")
    side = min(im.size)
    im = im.crop(((im.width - side) // 2, (im.height - side) // 2, (im.width + side) // 2, (im.height + side) // 2))
    buf = io.BytesIO(); im.resize((840, 840), Image.LANCZOS).save(buf, "JPEG", quality=88)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def photo_html():
    if os.path.exists(PHOTO):
        return f'<div class="me-ph img" a="1"><img src="{photo_uri()}" alt="Alejandro Varela"></div>'
    return '<div class="me-ph" a="1">TU FOTO<small>talk/assets/photo.jpg</small></div>'


def audio_src(key):
    """{{AUDIO:a}} → the WAV as a data URI; no file: empty string (the deck disables the button: «audio pendiente»)."""
    path = os.path.join(AUDIO, f"pump-{key}.wav")
    if not os.path.exists(path):
        PENDING_AUDIO.append(key)
        warn(f"missing audio: {os.path.relpath(path, os.path.dirname(TALK))}")
        return ""
    size = os.path.getsize(path)
    if size > 1_500_000:
        warn(f"audio {key} is {size / 1e6:.1f} MB: the deck grows as much (trim it to about 10 s?)")
    return data_uri(path)


def metric(m):
    """{{M:v1.recall_source}} → '92 %'  ·  no real measurement: 'por medir' (metrics.fmt decides)."""
    return metrics.fmt(m.group(1))


def resolve_metrics(text):
    return re.sub(r"\{\{M:([\w.]+)\}\}", metric, text)


def shot(name):
    """{{SHOT:name}} → the screenshot as <img> (resized: at most 2 × 1429 px wide); missing: a box saying what to capture."""
    path = next((os.path.join(SCREENS, name + e) for e in (".png", ".jpg", ".jpeg")
                 if os.path.exists(os.path.join(SCREENS, name + e))), None)
    if not path:
        PENDING_SHOTS.append(name)
        warn(f"missing screenshot: talk/assets/screens/{name}.png ({SHOTS.get(name, '?')})")
        return (f'<div class="spend">captura pendiente<code>talk/assets/screens/{name}.png</code>'
                f'<small>{H.escape(SHOTS.get(name, ""))}</small></div>')
    try:
        from PIL import Image
        import io
        im = Image.open(path).convert("RGB")
        if im.width > 2858:
            im = im.resize((2858, round(im.height * 2858 / im.width)), Image.LANCZOS)
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=86)
        uri = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except ImportError:
        uri = data_uri(path)
    return f'<img src="{uri}" alt="{H.escape(SHOTS.get(name, name))}" data-file="{os.path.basename(path)}">'


def pending_box(name):
    return f'<div class="pend">figura pendiente: {name}</div>'


def figure(name):
    """{{FIG:name}}. A figure that does not exist yet (or fails to draw) does not break the build: it leaves a box and warns."""
    fn = FIGS.get(name)
    if fn is None:
        PENDING_FIGS.append(name)
        warn(f"missing figure: {name}")
        return pending_box(name)
    try:
        svg = fn()
    except Exception as e:                       # half-done figure: it shows, but does not bring the deck down
        PENDING_FIGS.append(name)
        warn(f"figure {name} failed to draw ({type(e).__name__}: {e})")
        if os.environ.get("STRICT"):
            raise
        return pending_box(name)
    return svg


def notes_from_script():
    """Each '## …' of the speaker script with '<!-- id: x -->' becomes the note of slide data-id="x"."""
    if not os.path.exists(SCRIPT):
        return {}
    out = {}
    for part in re.split(r"^## ", open(SCRIPT, encoding="utf-8").read(), flags=re.M)[1:]:
        m = re.search(r"<!--\s*id:\s*([\w-]+)\s*-->", part)
        if not m:
            continue
        title = part.splitlines()[0].strip()
        body = part[m.end():].split("\n---")[0]
        body = body.replace("**[CLIC]**", "▶ CLIC").replace("**", "").replace("`", "")
        body = re.sub(r"(?m)^\s*>\s?", "", body)
        body = re.sub(r"\n{3,}", "\n\n", body).strip()
        body = resolve_metrics(body)             # measured numbers also apply in the notes
        out[m.group(1)] = (title.upper() + "\n\n" + body).replace('"', "'")
    return out


def inject_notes(html):
    notes = notes_from_script()
    for sid, txt in notes.items():
        pat = re.compile(r'(<section class="s[^"]*" data-id="%s"[^>]*?data-notes=")[^"]*(")' % re.escape(sid))
        html, n = pat.subn(lambda m: m.group(1) + H.escape(txt, quote=False) + m.group(2), html, count=1)
        if not n:
            print("  (warning) no slide for note:", sid)
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
        "{{PHOTO}}":          photo_html,
        "{{ARCH_GENERIC}}":   lambda: layer(arch("gen", deck=True), "lay-a"),
    }
    for k, fn in rep.items():
        if k in html:
            html = html.replace(k, fn())
    # slide 2 audio: {{AUDIO:a}} · {{AUDIO:b}}
    html = re.sub(r"\{\{AUDIO:([ab])\}\}", lambda m: audio_src(m.group(1)), html)
    # figures by name: {{FIG:onda_a}} → build_iso.FIGS["onda_a"]()
    html = re.sub(r"\{\{FIG:([\w-]+)\}\}", lambda m: figure(m.group(1)), html)
    html = re.sub(r"\{\{SHOT:([\w-]+)\}\}", lambda m: shot(m.group(1)), html)
    # template images and the font, embedded: the file works offline
    html = re.sub(r"\{\{IMG:([\w.-]+)\}\}", lambda m: data_uri(os.path.join(ASSETS, "template", m.group(1))), html)
    html = re.sub(r"\{\{BADGE:([\w.-]+)\}\}", lambda m: data_uri(os.path.join(ASSETS, "badges", m.group(1))), html)
    html = re.sub(r"\{\{FONT:([\w.-]+)\}\}", lambda m: data_uri(os.path.join(ASSETS, "fonts", m.group(1) + ".woff2")), html)
    html = inject_notes(html)
    html = resolve_metrics(html)                 # measured numbers: on the slides and in the notes
    left = re.findall(r"\{\{[A-Z_]+(?::[\w.-]+)?\}\}", html)
    if left:
        sys.exit(f"unresolved placeholders: {left}")
    if PENDING_FIGS and os.environ.get("STRICT"):
        sys.exit(f"missing figures: {sorted(set(PENDING_FIGS))}")

    open(DST, "w", encoding="utf-8").write(html)
    n_all = len(re.findall(r'<section class="s', html))
    n_anx = html.count('data-annex="1"')
    print(f"✔ {DST}  ({len(html.encode()) / 1024:.0f} KB · {n_all - n_anx} slides + {n_anx} annexes)")
    print("  real PoC measurement:", "yes" if metrics.ready() else "no (numbers show as «por medir»)")
    if PENDING_FIGS:
        print("  missing figures:", ", ".join(sorted(set(PENDING_FIGS))))
    if PENDING_AUDIO:
        print("  missing audio:", ", ".join(sorted(set(PENDING_AUDIO))))
    if PENDING_SHOTS:
        print("  missing screenshots (talk/assets/screens/):", ", ".join(sorted(set(PENDING_SHOTS))))


if __name__ == "__main__":
    main()
