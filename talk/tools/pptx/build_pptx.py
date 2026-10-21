"""
Builds talk/MLOps-a-ciegas-DevOpsDays-Bogota-2026.pptx on top of the official
DevOpsDays Bogotá 2026 template, with the same content as talk/devopsdays.html
(32 slides + 11 annexes, same order and ids as deck.src.html).
Slide text, speaker notes, shape names and section names stay in Spanish (the talk is in Spanish).

- Titles, kickers, text, tables, cards, the spine bar and the speaker notes:
  native and editable.
- Isometric figures: PNG layers that come in with each click (native animations).
- Architectures (flujo, aws, poc), sequence (a2) and canvas charts: one image per step.
- Memes: animated GIFs.
- AWS console screenshots (talk/assets/screens): a window that comes in on the slide's last click,
  as in the HTML; while one is missing, a «captura pendiente» box.
- Slide 2 (and the buttons on 32): if talk/assets/audio/pump-a.wav and
  pump-b.wav exist (or the ones in STATION_AUDIO_DIR), each one goes in as an mp4 video
  (the still wave + the audio, made with ffmpeg) that plays on click; otherwise the card
  says «audio pendiente».

Usage (from talk/tools/pptx; ./render.sh does everything):
    python3 build_pptx.py [renders-folder]
"""
import copy, html as H, json, os, re, subprocess, sys, uuid
import xml.etree.ElementTree as ET

from lxml import etree, html as LH
from PIL import Image, ImageFont, ImageOps
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
TALK = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)
from build_iso import FIGS as ISO           # noqa: E402

TPL = os.path.join(TALK, "assets", "template", "DevOpsDays-Bogota-2026-Plantilla-Speaker.pptx")
DECK = os.path.join(TALK, "devopsdays.html")
OUT = os.environ.get("PPTX_OUT") or os.path.join(TALK, "MLOps-a-ciegas-DevOpsDays-Bogota-2026.pptx")
BADGES = os.path.join(TALK, "assets", "badges")
PHOTO = next((os.path.join(TALK, "assets", f"photo.{e}") for e in ("jpg", "jpeg", "png")
              if os.path.exists(os.path.join(TALK, "assets", f"photo.{e}"))), os.path.join(TALK, "assets", "photo.jpg"))
BUILD = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "build")
# slide 2 audio (the same override build_figs uses to draw the wave)
AUDIO_DIR = os.environ.get("STATION_AUDIO_DIR") or os.path.join(TALK, "assets", "audio")

NAVY, SLATE, MUTED, LIGHT, LINE = "071329", "475569", "5C7290", "F4F7FC", "D5DEEA"
PURPLE, BLUE, CYAN, LINK, SOFT = "6D28D9", "2448FF", "00BCEB", "1F6C93", "B8C4D6"
INK08 = "EEF2F8"                            # disabled button background
SANS, MONO = "Calibri", "Courier New"
PX = 7620                                   # EMU per px of the 1600 x 900 canvas
NAT = 1.22                                   # natural line spacing of Calibri/Carlito (line height = 1.22 × size)


def E(v):
    return Emu(int(round(v * PX)))


# ── measuring text (Carlito has the same metrics as Calibri) ────────────────
_FD = "/usr/share/fonts/truetype/"
_FONTS = {}


def _font_file(bold, mono):
    """A metric-compatible font file: the Linux packages if present; otherwise (macOS) the repo's own
    Carlito, converted from woff2 once, and Courier New, which has Liberation Mono's metrics."""
    style = "Bold" if bold else "Regular"
    linux = _FD + (("liberation2/LiberationMono-%s.ttf" if mono else "crosextra/Carlito-%s.ttf") % style)
    if os.path.exists(linux):
        return linux
    if mono:
        return "/System/Library/Fonts/Supplemental/Courier New%s.ttf" % (" Bold" if bold else "")
    ttf = os.path.join(BUILD, "fonts", f"Carlito-{style}.ttf")
    if not os.path.exists(ttf):
        from fontTools.ttLib import TTFont        # needs fonttools + brotli to read woff2
        os.makedirs(os.path.dirname(ttf), exist_ok=True)
        f = TTFont(os.path.join(TALK, "assets", "fonts", f"Carlito-{style}.woff2"))
        f.flavor = None
        f.save(ttf)
    return ttf


def font(bold=False, mono=False, size=20):
    key = (bold, mono, size)
    if key not in _FONTS:
        _FONTS[key] = ImageFont.truetype(_font_file(bold, mono), size)
    return _FONTS[key]


def text_w(s, size, bold=False, mono=False):
    return font(bold, mono, size).getlength(s)


def n_lines(s, width, size, bold=False, mono=False):
    """Lines that s takes in width px. Words wider than the box (URLs) break by characters."""
    import math
    lines, cur = 1, ""
    for w in s.split():
        ww = text_w(w, size, bold, mono)
        if ww > width:
            if cur:
                lines += 1
            extra = math.ceil(ww / width) - 1
            lines += extra
            cur = ""
            continue
        t = (cur + " " + w).strip()
        if text_w(t, size, bold, mono) > width and cur:
            lines += 1; cur = w
        else:
            cur = t
    return lines


def n_lines_runs(runs, width, size):
    """Lines that some runs [(text, style)] take in width px, measuring each word with its own font
    (a cell with <code> mixes Calibri and Courier New)."""
    import math
    toks = []                                    # [word width, width of the preceding space]
    glued = False
    for t, st in runs:
        sz, mono, bold = st.get("size", size), st.get("font") == MONO, bool(st.get("bold"))
        sp = text_w(" ", sz, bold, mono)
        for k, w in enumerate(t.split(" ")):
            if k:
                glued = False
            if not w:
                continue
            ww = text_w(w, sz, bold, mono)
            if toks and glued:
                toks[-1][0] += ww
            else:
                toks.append([ww, sp if toks else 0])
            glued = True
    lines, cur = 1, 0.0
    for ww, sp in toks:
        if ww > width:                           # word wider than the box (a URL): breaks by characters
            lines += math.ceil(ww / width) - (1 if cur == 0 else 0)
            cur = 0
            continue
        add = ww + (sp if cur else 0)
        if cur and cur + add > width:
            lines += 1
            cur = ww
        else:
            cur += add
    return lines


# ── runs from the deck HTML ───────────────────────────────────────────────
def runs_of(el, bcolor=PURPLE, base=None):
    """[(text, style)] from an HTML element: <b> bold (and bcolor), <code> mono, <br> = line break."""
    base = dict(base or {})
    out = []

    def walk(e, st):
        if e.text:
            out.append((e.text, dict(st)))
        for ch in e:
            s2 = dict(st)
            if ch.tag == "b":
                s2["bold"] = True
                if bcolor:
                    s2["color"] = bcolor
            elif ch.tag == "code":
                s2["font"] = MONO; s2["code"] = True
            elif ch.tag == "br":
                out.append(("\n", dict(st)))
            elif ch.tag == "i":
                s2["color"] = BLUE if "pn" in (ch.get("class") or "").split() else PURPLE   # «Paso 1 ·» is blue
            if ch.tag != "br":
                walk(ch, s2)
            if ch.tail:
                out.append((ch.tail, dict(st)))
    walk(el, base)
    # normalize whitespace
    res = []
    for t, s in out:
        t = _safe(re.sub(r"\s+", " ", t)) if t != "\n" else t
        if t:
            res.append((t, s))
    if res and res[0][0] != "\n":
        res[0] = (res[0][0].lstrip(), res[0][1])
    if res and res[-1][0] != "\n":
        res[-1] = (res[-1][0].rstrip(), res[-1][1])
    return [r for r in res if r[0]]


def _safe(s):
    """Calibri and Courier New lack ⟨ ⟩ and U+00A0: they become [ ] and a space (the URL placeholders, e.g.)."""
    return s.replace("\u27e8", "[").replace("\u27e9", "]").replace("\u00a0", " ")


def plain(el):
    return _safe(re.sub(r"\s+", " ", el.text_content()).strip()) if el is not None else ""


def split_paras(runs):
    paras, cur = [], []
    for t, s in runs:
        if t == "\n":
            paras.append(cur); cur = []
        else:
            cur.append((t, s))
    paras.append(cur)
    return paras


# ── shapes ─────────────────────────────────────────────────────────────────
def _set_lang(r):
    rPr = r._r.get_or_add_rPr()
    rPr.set("lang", "es-CO")


def _strip_style(shape):
    st = shape._element.find(qn("p:style"))
    if st is not None:
        shape._element.remove(st)


def _frame(tf, paras, size=25, color=NAVY, bold=False, fnt=SANS, align=None, anchor=MSO_ANCHOR.TOP,
           line=None, lh=None, space_before=0, margins=(0, 0, 0, 0), wrap=True):
    """Fills a text_frame. paras: list of paragraphs; each one is a str or a list of (text, style).
    lh = HTML line height (multiple of the size, e.g. 1.35); line = multiple of PowerPoint's natural spacing."""
    tf.word_wrap = wrap
    tf.margin_left, tf.margin_top, tf.margin_right, tf.margin_bottom = (E(m) for m in margins)
    tf.vertical_anchor = anchor
    bp = tf._txBody.find(qn("a:bodyPr"))
    for k in list(bp):
        bp.remove(k)
    etree.SubElement(bp, qn("a:noAutofit"))
    if lh and not line:
        line = round(lh / NAT, 3)
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if align is not None:
            para.alignment = align
        if line:
            para.line_spacing = line
        sb = space_before[i] if isinstance(space_before, (list, tuple)) else space_before
        if sb and i:
            para.space_before = Pt(sb * .6)
        runs = [(p, {})] if isinstance(p, str) else p
        for t, st in runs:
            if t == "\n":                              # HTML <br>: line break inside the paragraph
                para.add_line_break()
                continue
            r = para.add_run()
            r.text = t.replace(" ", " ")
            f = r.font
            f.size = Pt(st.get("size", size) * .6)
            f.bold = st.get("bold", bold)
            f.color.rgb = RGBColor.from_string(st.get("color", color))
            f.name = st.get("font", fnt)
            if st.get("spc"):                          # letter spacing, in px (HTML letter-spacing)
                r._r.get_or_add_rPr().set("spc", str(int(round(st["spc"] * .6 * 100))))
            _set_lang(r)


def top_of(top, size, lh=None):
    """y of a PowerPoint box (natural spacing) whose baseline lands where the HTML one does with line-height = lh × size.
    For lh = None the HTML uses «normal» (= natural) and there is no correction."""
    return top if not lh else top + (lh - NAT) * size / 2


def textbox(slide, x, y, w, h, paras, size=25, color=NAVY, bold=False, fnt=SANS, align=None,
            anchor=MSO_ANCHOR.TOP, line=None, space_before=0, name=None, lh=None):
    tb = slide.shapes.add_textbox(E(x), E(y), E(w), E(h))
    if name:
        tb.name = name
    _frame(tb.text_frame, paras, size, color, bold, fnt, align, anchor, line, lh, space_before)
    return tb


def _style(s, fill, line, lw, dash=False):
    if fill:
        s.fill.solid(); s.fill.fore_color.rgb = RGBColor.from_string(fill)
    else:
        s.fill.background()
    if line:
        s.line.color.rgb = RGBColor.from_string(line); s.line.width = E(lw)
        if dash:
            from pptx.enum.dml import MSO_LINE
            s.line.dash_style = MSO_LINE.DASH
    else:
        s.line.fill.background()


def rect(slide, x, y, w, h, fill=None, line=None, lw=1.5, dash=False, name=None, radius=None):
    """Rectangle (or rounded rectangle if radius, in px)."""
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
                               E(x), E(y), E(w), E(h))
    _strip_style(s)
    if radius:
        s.adjustments[0] = min(.5, radius / min(w, h))
    if name:
        s.name = name
    _style(s, fill, line, lw, dash)
    return s


def poly(slide, pts, fill=None, line=None, lw=1.5, name=None):
    """Closed polygon (native freeform); pts in canvas px."""
    fb = slide.shapes.build_freeform(E(pts[0][0]), E(pts[0][1]))
    fb.add_line_segments([(E(px), E(py)) for px, py in pts[1:]], close=True)
    s = fb.convert_to_shape()
    _strip_style(s)
    if name:
        s.name = name
    _style(s, fill, line, lw)
    if line:
        ln = s._element.spPr.find(qn("a:ln"))
        etree.SubElement(ln, qn("a:round"))
    return s


def shape_text(shape, paras, margins=(0, 0, 0, 0), **kw):
    """Text inside a shape (card, button, chevron)."""
    _frame(shape.text_frame, paras, margins=margins, **kw)
    return shape


def hline(slide, x, y, w, color=LINE, lw=1.5, arrow=False):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, E(x), E(y), E(x + w), E(y))
    _strip_style(c)
    c.line.color.rgb = RGBColor.from_string(color)
    c.line.width = E(lw)
    if arrow:
        ln = c._element.spPr.find(qn("a:ln"))
        etree.SubElement(ln, qn("a:tailEnd"), type="triangle", w="med", len="med")
    return c


def picture(slide, path, x, y, w=None, h=None, name=None):
    p = slide.shapes.add_picture(path, E(x), E(y), E(w) if w else None, E(h) if h else None)
    if name:
        p.name = name
    return p


def to_front(slide, shape):
    tree = slide.shapes._spTree
    tree.remove(shape._element); tree.append(shape._element)


# ── rendered images ────────────────────────────────────────────────────────
os.makedirs(os.path.join(BUILD, "img"), exist_ok=True)


def flat(src, dst, box=None, scale=1.0):
    """PNG on a white background; box in canvas px (x0, y0, x1, y1) over a 2x render."""
    im = Image.open(src).convert("RGBA")
    if box:
        im = im.crop(tuple(int(v * 2) for v in box))
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    out = bg.convert("RGB")
    if scale != 1:
        out = out.resize((int(out.width * scale), int(out.height * scale)), Image.LANCZOS)
    out.save(dst, optimize=True)
    return dst


def trimmed(png_bytes, name):
    """Transparent 2x PNG cropped to its content: returns (path, x, y, w, h) in canvas px."""
    import io
    im = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    bb = im.getchannel("A").getbbox()
    if not bb:
        return None
    bb = (max(0, bb[0] - 4), max(0, bb[1] - 4), min(im.width, bb[2] + 4), min(im.height, bb[3] + 4))
    p = os.path.join(BUILD, "img", name + ".png")
    im.crop(bb).save(p, optimize=True)
    return p, bb[0] / 2, bb[1] / 2, (bb[2] - bb[0]) / 2, (bb[3] - bb[1]) / 2


def iso_layers(fig):
    """Splits the isometric figure into PNG layers that keep the drawing order (bottom to top).

    Each layer is a run of consecutive elements with the same key: «base» (always visible), «off<n>» (goes away
    at click n) or «on<n>» (comes in at click n). A layer merges with an earlier one of the same key only if
    no layer in between overlaps it; that way, whatever the SVG draws under something else (the recipe bands,
    under the text) stays under it in PowerPoint.
    Returns [{"key", "path", "x", "y", "w", "h"}] in stacking order; the fog (data-fog) comes in pre-composited,
    as «on<n>_fog», because a semi-transparent veil looks bad in PowerPoint."""
    import cairosvg, io
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    root = ET.fromstring(ISO[fig](static=True))

    def key_of(ch):
        on, off = ch.get("data-on"), ch.get("data-off")
        return "on" + on if on not in (None, "0") else ("off" + off if off is not None else "base")

    def shell(elems):
        r = ET.Element(root.tag, dict(root.attrib))
        r.extend(elems)
        return ET.tostring(r)

    def overlap(a, b):
        return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]

    runs = []
    for ch in root:
        if ch.get("data-fog"):
            runs.append(("fog", [ch]))
        elif runs and runs[-1][0] == key_of(ch):
            runs[-1][1].append(ch)
        else:
            runs.append((key_of(ch), [ch]))
    layers = []
    for key, els in runs:
        if key == "fog":
            fog, n = els[0], int(els[0].get("data-on"))
            st = [c for c in root if not (key_of(c).startswith("on") and int(key_of(c)[2:]) > n)
                  and not (key_of(c).startswith("off") and int(key_of(c)[3:]) <= n)]
            png = cairosvg.svg2png(bytestring=shell(st), output_width=3200, background_color="white")
            fx, fy, fw, fh = (float(fog.get(a)) for a in ("x", "y", "width", "height"))
            fw = min(fw, 1600 - fx)
            im = Image.open(io.BytesIO(png)).convert("RGB").crop(tuple(int(v * 2) for v in (fx, fy, fx + fw, fy + fh)))
            p = os.path.join(BUILD, "img", f"iso_{fig}_{len(layers):02d}_on{n}_fog.png")
            im.save(p, optimize=True)
            layers.append({"key": f"on{n}_fog", "path": p, "x": fx, "y": fy, "w": fw, "h": fh,
                           "bb": (fx * 2, fy * 2, (fx + fw) * 2, (fy + fh) * 2), "els": None})
            continue
        bb = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=shell(els), output_width=3200))).getchannel("A").getbbox()
        if bb is None:
            continue
        for i, L in enumerate(layers):
            if L["key"] == key and L["els"] is not None and not any(overlap(M["bb"], bb) for M in layers[i + 1:]):
                L["els"] += els
                L["bb"] = (min(L["bb"][0], bb[0]), min(L["bb"][1], bb[1]), max(L["bb"][2], bb[2]), max(L["bb"][3], bb[3]))
                break
        else:
            layers.append({"key": key, "els": list(els), "bb": bb})
    out = []
    for i, L in enumerate(layers):
        if L["els"] is None:
            out.append({k: L[k] for k in ("key", "path", "x", "y", "w", "h")})
            continue
        t = trimmed(cairosvg.svg2png(bytestring=shell(L["els"]), output_width=3200), f"iso_{fig}_{i:02d}_{L['key']}")
        out.append({"key": L["key"], "path": t[0], "x": t[1], "y": t[2], "w": t[3], "h": t[4]})
    return out


# ── slide 2 audio: the wave as a still video + the WAV ─────────────────────
def audio_path(which):
    p = os.path.join(AUDIO_DIR, f"pump-{which}.wav")
    return p if os.path.isfile(p) else None


def wave_poster(which):
    """The pump's wave (640 × 160, at 2x) on its light rounded background, opaque (the video frame)."""
    import io, cairosvg
    from PIL import ImageDraw
    png = cairosvg.svg2png(bytestring=ISO[f"onda_{which}"]().encode(), output_width=1280)
    wave = Image.open(io.BytesIO(png)).convert("RGBA")
    bg = Image.new("RGBA", wave.size, (255, 255, 255, 255))
    ImageDraw.Draw(bg).rounded_rectangle([0, 0, wave.width - 1, wave.height - 1], radius=16, fill="#" + LIGHT)
    bg.alpha_composite(wave)
    p = os.path.join(BUILD, "img", f"wave_{which}.png")
    bg.convert("RGB").save(p, optimize=True)
    return p


def make_mp4(poster, wav, name):
    """mp4 (H.264 + AAC) with the still image and the audio: PowerPoint plays it on click."""
    os.makedirs(os.path.join(BUILD, "media"), exist_ok=True)
    out = os.path.join(BUILD, "media", name + ".mp4")
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav],
                         check=True, capture_output=True, text=True).stdout.strip()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "10", "-i", poster, "-i", wav,
                    "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
                    "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:a", "aac", "-b:a", "128k",
                    "-t", dur, "-movflags", "+faststart", out], check=True)           # as long as the audio
    return out


class Plan:
    """What comes in (or goes out) at each click: data-on="n" → click n."""
    def __init__(self):
        self.d = {}

    def add(self, n, shapes, kind="in"):
        n = int(n or 0)
        if n > 0:
            self.d.setdefault(n, []).extend((g, kind) for g in (shapes if isinstance(shapes, (list, tuple)) else [shapes]))

    def flush(self, tm):
        for n in sorted(self.d):
            tm.click(*self.d[n])


# ── native animations ──────────────────────────────────────────────────────
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"


class Timing:
    def __init__(self):
        self.clicks = []      # [[(shape, kind)]]
        self.auto = []        # [(shape, kind, delay_ms, dur_ms)]
        self.trig = []        # [(shape that is clicked, video that plays)]

    def click(self, *items):
        self.clicks.append(list(items))

    def play_on_click(self, trigger, media):
        """Clicking `trigger` during the show plays `media` (a video) from the start."""
        self.trig.append((trigger, media))

    def xml(self):
        if not self.clicks and not self.auto and not self.trig:
            return None
        ids = iter(range(3, 10000))
        bld = {}

        def tgt(sp):
            return f'<p:tgtEl><p:spTgt spid="{sp.shape_id}"/></p:tgtEl>'

        def effect(sp, kind, node, delay=0, dur=400):
            grp = 1 if kind == "out" else 0
            if sp._element.tag in (qn("p:sp"), qn("p:cxnSp")):
                bld[(sp.shape_id, grp)] = sp._element.tag == qn("p:sp")
            vis = (f'<p:set><p:cBhvr><p:cTn id="{next(ids)}" dur="1" fill="hold"><p:stCondLst><p:cond delay="{dur - 1 if kind == "out" else 0}"/>'
                   f'</p:stCondLst></p:cTn>{tgt(sp)}<p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst>'
                   f'</p:cBhvr><p:to><p:strVal val="{"hidden" if kind == "out" else "visible"}"/></p:to></p:set>')
            if kind == "appear":
                pid, cls, sub, body = 1, "entr", 0, vis
            elif kind == "in":
                pid, cls, sub = 10, "entr", 0
                body = vis + (f'<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{next(ids)}" dur="{dur}"/>'
                              f'{tgt(sp)}</p:cBhvr></p:animEffect>')
            elif kind == "out":
                pid, cls, sub = 10, "exit", 0
                body = (f'<p:animEffect transition="out" filter="fade"><p:cBhvr><p:cTn id="{next(ids)}" dur="{dur}"/>'
                        f'{tgt(sp)}</p:cBhvr></p:animEffect>') + vis
            elif kind == "wipe":
                pid, cls, sub = 22, "entr", 8
                body = vis + (f'<p:animEffect transition="in" filter="wipe(left)"><p:cBhvr><p:cTn id="{next(ids)}" dur="{dur}"/>'
                              f'{tgt(sp)}</p:cBhvr></p:animEffect>')
            return (f'<p:par><p:cTn id="{next(ids)}" presetID="{pid}" presetClass="{cls}" presetSubtype="{sub}" fill="hold" '
                    f'grpId="{grp}" nodeType="{node}"><p:stCondLst><p:cond delay="{delay}"/></p:stCondLst>'
                    f'<p:childTnLst>{body}</p:childTnLst></p:cTn></p:par>')

        seq = []
        if self.auto:
            inner = "".join(effect(sp, k, "afterEffect" if j == 0 else "withEffect", d, du)
                            for j, (sp, k, d, du) in enumerate(self.auto))
            seq.append(f'<p:par><p:cTn id="{next(ids)}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/>'
                       f'<p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond></p:stCondLst><p:childTnLst>'
                       f'<p:par><p:cTn id="{next(ids)}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst>'
                       f'<p:childTnLst>{inner}</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>')
        for items in self.clicks:
            inner = "".join(effect(sp, k, "clickEffect" if j == 0 else "withEffect") for j, (sp, k) in enumerate(items))
            seq.append(f'<p:par><p:cTn id="{next(ids)}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst>'
                       f'<p:childTnLst><p:par><p:cTn id="{next(ids)}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst>'
                       f'<p:childTnLst>{inner}</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>')
        AB = ' animBg="1"'
        blds = "".join(f'<p:bldP spid="{i}" grpId="{g}"{"" if txt else AB}/>' for (i, g), txt in bld.items())
        # interactive sequences: a click on the shape starts the video (they do not use up slide clicks)
        inter = "".join(
            f'<p:seq concurrent="1" nextAc="seek"><p:cTn id="{next(ids)}" restart="whenNotActive" fill="hold" '
            f'evtFilter="cancelBubble" nodeType="interactiveSeq"><p:stCondLst><p:cond evt="onClick" delay="0">'
            f'<p:tgtEl><p:spTgt spid="{tr.shape_id}"/></p:tgtEl></p:cond></p:stCondLst>'
            f'<p:endSyncLst><p:cond evt="onEnd" delay="0"><p:rtn val="all"/></p:cond></p:endSyncLst><p:childTnLst>'
            f'<p:par><p:cTn id="{next(ids)}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
            f'<p:par><p:cTn id="{next(ids)}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
            f'<p:par><p:cTn id="{next(ids)}" presetID="1" presetClass="mediacall" presetSubtype="0" fill="hold" '
            f'nodeType="clickEffect"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
            f'<p:cmd type="call" cmd="playFrom(0.0)"><p:cBhvr><p:cTn id="{next(ids)}" dur="1" fill="hold"/>'
            f'<p:tgtEl><p:spTgt spid="{md.shape_id}"/></p:tgtEl></p:cBhvr></p:cmd>'
            f'</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>'
            f'</p:childTnLst></p:cTn><p:nextCondLst><p:cond evt="onClick" delay="0"><p:tgtEl>'
            f'<p:spTgt spid="{tr.shape_id}"/></p:tgtEl></p:cond></p:nextCondLst></p:seq>'
            for tr, md in self.trig)
        x = (f'<p:timing xmlns:p="{P_NS}"><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">'
                f'<p:childTnLst><p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq">'
                f'<p:childTnLst>{"".join(seq)}</p:childTnLst></p:cTn>'
                f'<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
                f'<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>'
                f'</p:seq>{inter}</p:childTnLst></p:cTn></p:par></p:tnLst>'
                + (f'<p:bldLst>{blds}</p:bldLst>' if blds else "") + '</p:timing>')
        n = iter(range(1, 10000))                       # ids in document order
        return re.sub(r'<p:cTn id="\d+"', lambda m: f'<p:cTn id="{next(n)}"', x)

    def apply(self, slide):
        x = self.xml()
        if not x:
            return
        el = etree.fromstring(x)
        sld = slide._element
        anchor = sld.find(qn("p:transition"))
        if anchor is None:
            anchor = sld.find(qn("p:clrMapOvr"))
        anchor.addnext(el)


# ── the presentation ───────────────────────────────────────────────────────
prs = Presentation(TPL)
SLDNUM = None
for sl in prs.slides:                     # the template's slide number, to copy it
    for sh in sl.shapes:
        if sh.is_placeholder and sh.placeholder_format.type is not None and "SLIDE_NUMBER" in str(sh.placeholder_format.type):
            SLDNUM = copy.deepcopy(sh._element); break
    if SLDNUM is not None:
        break
# drop the 24 sample slides (the layouts stay)
lst = prs.slides._sldIdLst
for sid in list(lst):
    prs.part.drop_rel(sid.rId); lst.remove(sid)
LAY = {l.name: l for l in prs.slide_layouts}
for sh in LAY["CIERRE"].shapes:           # the template's kicker says «CLOSING»; the talk is in Spanish
    if sh.name == "antetitulo" and sh.has_text_frame and sh.text_frame.text.strip().upper() == "CLOSING":
        runs = sh.text_frame.paragraphs[0].runs
        runs[0].text = "CIERRE"
        for r in runs[1:]:
            r._r.getparent().remove(r._r)


def new_slide(layout):
    s = prs.slides.add_slide(LAY[layout])
    if layout in ("CONTENIDO", "SIMPLE", "DIVISOR") and SLDNUM is not None:
        el = copy.deepcopy(SLDNUM)
        el.find(".//" + qn("p:cNvPr")).set("id", str(max(sh.shape_id for sh in s.shapes) + 50))
        s.shapes._spTree.append(el)
    return s


def ph(slide, idx):
    for p in slide.placeholders:
        if p.placeholder_format.idx == idx:
            return p
    return None


def fill_ph(p, paras, size=None, color=None, bold=None):
    tf = p.text_frame
    tf.margin_left = 0          # the HTML puts the text at x = 84 (the box edge); without the box's 12 px margin
    for i, para_runs in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        for t, st in para_runs:
            r = para.add_run(); r.text = t
            if st.get("size") or size:
                r.font.size = Pt((st.get("size") or size) * .6)
            if st.get("bold") is not None or bold is not None:
                r.font.bold = st.get("bold", bold)
            c = st.get("color", color)
            if c:
                r.font.color.rgb = RGBColor.from_string(c)
            if st.get("font"):
                r.font.name = st["font"]
            _set_lang(r)


def drop_ph(slide, idx):
    p = ph(slide, idx)
    if p is not None:
        p._element.getparent().remove(p._element)


# ── reading the deck HTML ─────────────────────────────────────────────────
doc = LH.fromstring(open(DECK, encoding="utf-8").read())
SECS = doc.xpath('//section[contains(concat(" ", @class, " "), " s ")]')
CANVAS = json.load(open(os.path.join(BUILD, "canvas", "canvas.json")))


def q(el, css):
    r = el.cssselect(css)
    return r[0] if r else None


def header(slide, sec):
    k, t = q(sec, ".kick"), q(sec, ".ttl")
    if k is not None:
        fill_ph(ph(slide, 106), [[(plain(k).upper(), {})]])
    else:
        drop_ph(slide, 106)
    if t is not None:
        fill_ph(ph(slide, 107), split_paras(runs_of(t, PURPLE)))
    else:
        drop_ph(slide, 107)


def footsrc(slide, sec):
    f = q(sec, ".foot")
    if f is not None and f.get("data-src"):
        textbox(slide, 84, 742, 1432, 22, [f.get("data-src")], size=15, color=MUTED, name="Fuente")


def bring_titles_front(slide):
    for idx in (106, 107):
        p = ph(slide, idx)
        if p is not None:
            to_front(slide, p)


# ── builders per slide type ────────────────────────────────────────────────
def b_cover(s, sec, tm):
    t = ph(s, 103)
    fill_ph(t, [[("MLOps ", {}), ("a ciegas", {"color": PURPLE})],
                [(plain(q(sec, ".sub")), {"size": 30, "bold": False, "color": NAVY})]])
    t.text_frame.paragraphs[1].space_before = Pt(8)
    fill_ph(ph(s, 104), [[(plain(q(sec, ".who")).replace("  ", " "), {})]])


def b_whoami(s, sec, tm):
    header(s, sec)
    if os.path.exists(PHOTO):
        im = ImageOps.exif_transpose(Image.open(PHOTO)); side = min(im.size)
        crop = im.crop(((im.width - side) // 2, (im.height - side) // 2, (im.width + side) // 2, (im.height + side) // 2))
        p = os.path.join(BUILD, "img", "photo.jpg"); crop.convert("RGB").resize((840, 840)).save(p, quality=90)
        picture(s, p, 84, 246, 420, 420, name="Foto")
    else:
        rect(s, 84, 246, 420, 420, fill=LIGHT, line=MUTED, dash=True, name="Marco foto")
        textbox(s, 84, 420, 420, 80, [[("TU FOTO", {"bold": True, "color": MUTED, "size": 22})],
                                      [("talk/assets/photo.jpg", {"font": MONO, "size": 17, "color": SLATE})]],
                align=PP_ALIGN.CENTER, name="Texto foto")
    me = q(sec, ".me")
    textbox(s, 552, 246, 900, 52, [plain(q(me, ".nm"))], size=43, bold=True)
    role = plain(q(me, ".rl"))
    textbox(s, 552, 302, 900, 34, [role], size=25, color=PURPLE)
    logo = me.cssselect(".rl img.co")
    if logo:                                   # employer logo, right after the role, same height as the text
        path = os.path.join(BADGES, logo[0].get("data-file"))
        im = Image.open(path)
        h = 34
        picture(s, path, 552 + text_w(role, 25) + 18, 302, round(h * im.width / im.height), h, name="Logo empresa")
    bio = plain(q(me, "p"))
    nl = n_lines(bio, 900, 25)
    textbox(s, 552, 356, 900, nl * 25 * 1.4 + 6, [bio], size=25, color=SLATE, lh=1.4)
    dy = (nl - 1) * 35                         # everything below moves down if the bio wraps
    # the badges, in two groups (AWS, Kubernetes): label above, images in a row
    x = 552
    for grp in me.cssselect(".bdg .bg"):
        lab = q(grp, ".bl")
        n = plain(q(lab, "i"))
        textbox(s, x, 420 + dy, 520, 30, [[(n + " ", {"color": PURPLE}), (plain(lab).replace(n, "", 1).strip(), {})]],
                size=20, bold=True, name="Certificaciones")
        imgs = grp.cssselect(".bi img")
        for k, img in enumerate(imgs):
            picture(s, os.path.join(BADGES, img.get("data-file")), x + k * 102, 460 + dy, 92, 92, name=img.get("alt"))
        x += len(imgs) * 102 - 10 + 34
    y = 590 + dy
    hb = me.cssselect("p.hb")
    if hb:                                     # hobbies, one or two lines, under the badges
        runs = runs_of(hb[0], NAVY)
        nl = n_lines("".join(t for t, _ in runs), 900, 21)
        textbox(s, 552, y, 900, nl * 21 * 1.4 + 6, [runs], size=21, color=SLATE, lh=1.4, name="Fuera del trabajo")
        y += round(nl * 21 * 1.4) + 22
    textbox(s, 552, y, 900, 30, [plain(q(me, ".hd"))], size=20, color=LINK, fnt=MONO)


def b_canvas(s, sec, tm):
    header(s, sec)
    sid = sec.get("data-id"); m = CANVAS[sid]; bx = m["box"]
    x, y, w, h = bx["left"], bx["top"], 1600 - bx["left"] - bx["right"], 900 - bx["top"] - bx["bottom"]
    pics = []
    for k, f in enumerate(m["files"]):
        if isinstance(f, list):                       # memes: animated GIF
            frames = [Image.open(os.path.join(BUILD, "canvas", fr)).convert("RGBA") for fr in f]
            out = []
            for fr in frames:
                bg = Image.new("RGBA", fr.size, (255, 255, 255, 255)); bg.alpha_composite(fr)
                out.append(bg.convert("RGB").resize((w, h), Image.LANCZOS).quantize(colors=64, method=Image.Quantize.MEDIANCUT))
            p = os.path.join(BUILD, "img", f"{sid}_s{k}.gif")
            out[0].save(p, save_all=True, append_images=out[1:], duration=100, loop=0, optimize=True)
        else:
            p = flat(os.path.join(BUILD, "canvas", f), os.path.join(BUILD, "img", f"{sid}_s{k}.png"))
        pics.append(picture(s, p, x, y, w, h, name=f"Paso {k}"))
    for k in range(1, len(pics)):
        tm.click((pics[k], "appear"))
    footsrc(s, sec)


def duo_block(s, sec, y0=244):
    duo = q(sec, ".duo"); small = "sm" in (duo.get("class") or "")
    size = 150 if small else 210
    x = 84
    for ch in duo:
        cls = ch.get("class") or ""
        if "arrow" in cls:
            aw = text_w("→", 90 if small else 110)
            textbox(s, x, y0 + size * .9 - (90 if small else 110) * 1.05 - 24, aw + 10, 140, ["→"],
                    size=90 if small else 110, color=SOFT)
            x += aw + 76
            continue
        yr, bn = q(ch, ".yr"), q(ch, ".bn")
        bcls = bn.get("class") or ""
        col = SOFT if "dim" in bcls else (PURPLE if "hot" in bcls else NAVY)
        bw = text_w(plain(bn), size, True)
        lw = text_w(plain(yr), 22, True, True)
        textbox(s, x, y0, max(bw, lw) + 20, 30, [plain(yr)], size=22, bold=True, color=MUTED, fnt=MONO)
        textbox(s, x - size * .03, y0 + 26, bw + 40, size * 1.05, [plain(bn)], size=size, bold=True, color=col, line=.9)
        x += max(bw, lw) + 76
    say, say2 = q(sec, ".say"), q(sec, ".say2")
    if say is not None:
        textbox(s, 84, 560, 1432, 46, [runs_of(say, PURPLE)], size=34)
    if say2 is not None:
        textbox(s, 84, 626, 1432, 40, [runs_of(say2, PURPLE)], size=28, color=SLATE)


def b_duo(s, sec, tm):
    header(s, sec); duo_block(s, sec); footsrc(s, sec)


def b_refl(s, sec, tm):
    header(s, sec)
    drop_ph(s, 107)
    rect(s, 84, 150, 1432, 560, fill=LIGHT, line=LINE, name="Bloque")
    rq, rs = q(sec, ".rq"), q(sec, ".rs")
    paras = [[(t, dict(st, size=66, bold=True)) for t, st in runs_of(rq, PURPLE)]]
    if rs is not None:
        paras.append([(plain(rs), {"size": 32, "bold": False, "color": SLATE})])
    textbox(s, 164, 160, 1272, 470, paras, size=66, bold=True, anchor=MSO_ANCHOR.MIDDLE, line=1.05, space_before=30)
    refl_timer(s, tm)


def refl_timer(s, tm):
    """The 5-second bar that fills by itself 0.8 s after the slide comes in."""
    rect(s, 164, 626, 560, 6, fill=LINE, name="Barra")
    bar = rect(s, 164, 626, 560, 6, fill=PURPLE, name="Barra 5 s")
    textbox(s, 164, 650, 300, 24, ["5 segundos"], size=16, color=MUTED, fnt=MONO)
    tm.auto.append((bar, "wipe", 800, 5000))


def b_refl3(s, sec, tm):
    """Show of hands 3: the question; at click 1 the phrase goes away and the answer comes in (deployment by thing group)."""
    header(s, sec)
    drop_ph(s, 107)
    rect(s, 84, 150, 1432, 560, fill=LIGHT, line=LINE, name="Bloque")
    rq, rs = q(sec, ".rq"), q(sec, ".rs")
    rq_h, rs_h = 66 * 1.12, 32 * NAT
    top = 151.5 + (497 - (rq_h + 30 + rs_h)) / 2               # the question + phrase block, centered as in the HTML
    textbox(s, 164, top_of(top, 66, 1.12), 1272, 66 * NAT, [[(t, dict(st, size=66, bold=True)) for t, st in runs_of(rq, PURPLE)]],
            size=66, bold=True, name="Pregunta")
    pl = Plan()
    phrase = textbox(s, 164, top + rq_h + 30, 1272, rs_h + 4, [plain(rs)], size=32, color=SLATE, name="Frase")
    pl.add(rs.get("data-off"), phrase, "out")
    ans = q(sec, ".ans")
    x0, y = 164, 432
    cols = [(x0, 250), (x0 + 266, 300), (x0 + 582, 484), (x0 + 1082, 190)]          # grid 250 300 1fr 190, gap 16
    # the light background covers the phrase: in the show the phrase leaves with the click, but when printing or
    # exporting to PDF (no animations) the slide shows the answer, like the printed HTML
    g = [rect(s, 120, 420, 1360, 200, fill=LIGHT, name="Fondo de la respuesta"),
         textbox(s, x0, y, 1272, 24 * NAT, [plain(q(ans, ".ah"))], size=24, bold=True, color=PURPLE)]
    y += 24 * NAT + 14
    head = q(ans, ".ahd")
    for (cx, cw), sp in zip(cols, head.cssselect("span")):
        g.append(textbox(s, cx, y, cw, 16, [[(plain(sp).upper(), {"spc": 1.4})]], size=14, bold=True, color=MUTED, fnt=MONO))
    y += 14 * 1.13 + 8
    for row in ans.cssselect(".ag:not(.ahd)"):
        g.append(hline(s, x0, y, 1272))
        for (cx, cw), el in zip(cols, row):
            bold = el.tag == "b"
            g.append(textbox(s, cx, y + 12 + 1.5, cw, 28, [plain(el)], size=24, bold=bold, color=PURPLE if bold else NAVY,
                             fnt=MONO))
        y += 12 + 24 * 1.13 + 12 + 1.5
    pl.add(ans.get("data-on"), g)
    refl_timer(s, tm)
    pl.flush(tm)


def b_agenda(s, sec, tm):
    header(s, sec)
    for k, r in enumerate(sec.cssselect(".agenda .r")):
        y = 252 + k * 132
        n, t, d = q(r, ".n"), q(r, ".t"), q(r, ".d")
        textbox(s, 84, y, 110, 98, [plain(n)], size=40, bold=True, color=BLUE, fnt=MONO, anchor=MSO_ANCHOR.MIDDLE)
        textbox(s, 198, y, 520, 98, [plain(t)], size=32, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        textbox(s, 726, y, 790, 98, [plain(d)], size=25, color=SLATE, anchor=MSO_ANCHOR.MIDDLE)
        if k < 3:
            hline(s, 84, y + 98, 1432)


def b_div(s, sec, tm):
    fill_ph(ph(s, 106), [[(plain(q(sec, ".n")), {})]])
    fill_ph(ph(s, 107), [[(plain(q(sec, ".t")), {})]])
    d = q(sec, ".d")
    if d is not None:
        fill_ph(ph(s, 108), [[(plain(d), {})]])
    else:
        drop_ph(s, 108)                      # divider 03 has no support line: it has the spine


def b_div3(s, sec, tm):
    """Divider 03: the template number and title, and the six spine boxes (native)."""
    b_div(s, sec, tm)
    from build_figs import STEPS             # the same six steps the `espina` figure draws
    gap = 20
    w = (1432 - 5 * gap) / 6
    y, h = 652, 118
    for k, (t, sub) in enumerate(STEPS):
        x = 84 + k * (w + gap)
        box = rect(s, x, y, w, h, fill="FFFFFF", line=PURPLE if k == 0 else LINE, lw=2, radius=12, name=f"Paso {k + 1}")
        shape_text(box, [[(f"0{k + 1}", {"size": 20, "bold": True, "color": PURPLE, "font": MONO})],
                         [(t, {"size": 29, "bold": True})],
                         [(sub, {"size": 18, "color": SLATE})]],
                   margins=(20, 19, 8, 0), size=29, anchor=MSO_ANCHOR.TOP, align=PP_ALIGN.LEFT, wrap=False,
                   space_before=[0, 4, 3])
        if k < 5:
            hline(s, x + w + 3, y + h / 2, gap - 6, PURPLE, 2.2, arrow=True)


def b_quote(s, sec, tm):
    header(s, sec)
    textbox(s, 76, 262, 120, 170, ["“"], size=160, color=PURPLE, bold=True)
    textbox(s, 170, 300, 1250, 300, [runs_of(q(sec, ".quote"), PURPLE)], size=62, bold=True, line=1.05)
    footsrc(s, sec)


def b_trio(s, sec, tm):
    header(s, sec)
    its = sec.cssselect(".trio .it"); cw = (1432 - 80) / 3
    later = []
    for k, it in enumerate(its):
        x = 84 + k * (cw + 40)
        w = plain(q(it, ".w"))
        hline(s, x, 330, cw, NAVY, 4)
        textbox(s, x, 352, cw, 30, [plain(q(it, ".n"))], size=22, bold=True, color=BLUE, fnt=MONO)
        textbox(s, x, 386, cw, 130, [w], size=52, bold=True, line=1.0)
        if it.get("data-hot"):
            a = hline(s, x, 330, cw, PURPLE, 4)
            b = textbox(s, x, 386, cw, 130, [w], size=52, bold=True, color=PURPLE, line=1.0)
            later += [(a, "in"), (b, "in")]
    if later:
        tm.click(*later)
    footsrc(s, sec)


def b_rows(s, sec, tm):
    header(s, sec)
    rows = sec.cssselect(".rows .row")
    rcls = q(sec, ".rows").get("class") or ""
    solo = "solo" in rcls
    five = "five" in rcls
    hs, padv = (32, 40) if five else (36, 56)
    tw = 1432 - 114 - 24 - (0 if solo else 324)
    top = 236 if solo else 232
    y = top
    for k, r in enumerate(rows):
        h3 = q(r, "h3"); hot = "hot" in (r.get("class") or "")
        runs = runs_of(h3, PURPLE if hot else None)
        nl = n_lines("".join(t for t, _ in runs), tw, hs)
        rh = nl * (hs + 8) + padv
        group = []
        if k:
            group.append(hline(s, 84, y, 1432))
        group.append(textbox(s, 84, y, 114, rh, [plain(q(r, ".big"))], size=40, bold=True, color=BLUE, fnt=MONO,
                             anchor=MSO_ANCHOR.MIDDLE))
        group.append(textbox(s, 222, y, tw, rh, [runs], size=hs, anchor=MSO_ANCHOR.MIDDLE, line=1.0))
        chip = q(r, ".chip")
        if chip is not None:
            group.append(textbox(s, 1216, y, 300, rh, split_paras(runs_of(chip, None)), size=16, color=MUTED,
                                 align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE))
        if r.get("data-on") not in (None, "0"):
            tm.click(*[(g, "in") for g in group])
        y += rh
    footsrc(s, sec)


def b_tell(s, sec, tm):
    header(s, sec)
    cols = sec.cssselect(".tell > div")
    lw = (1432 - 90) * 1.25 / 2.25
    for ci, col in enumerate(cols):
        x = 84 if ci == 0 else 84 + lw + 90
        w = lw if ci == 0 else 1432 - lw - 90
        no = "no" in (col.get("class") or "")
        group = [textbox(s, x, 236, w, 24, [plain(q(col, "h4")).upper()], size=16, bold=True,
                         color=PURPLE if no else MUTED)]
        y = 266
        for li in col.cssselect(".li"):
            group.append(hline(s, x, y, w))
            span, code = q(li, "span"), q(li, "code")
            group.append(textbox(s, x, y + 14, w, 40, [plain(span)], size=29, bold=no, color=PURPLE if no else NAVY))
            if code is not None:
                group.append(textbox(s, x, y + 22, w, 30, [plain(code)], size=17, color=LINK, fnt=MONO, align=PP_ALIGN.RIGHT))
            y += 66
        if col.get("data-on") not in (None, "0"):
            tm.click(*[(g, "in") for g in group])
    footsrc(s, sec)


FIGKEY = {"componente": "receta"}           # slide id → build_figs figure (by default, the same name)


def spine(s, n):
    """The footer bar with the six steps (slides 18 to 24): 1432 × 44, at x = 84, y = 722, above the footer."""
    from build_figs import STEPS
    W, H, k0, X, Y = 1432, 44, 12, 84, 722
    w = W / 6
    for k, (t, _) in enumerate(STEPS):
        x0, x1 = X + k * w, X + (k + 1) * w - 4
        pts = [(x0, Y), (x1 - k0, Y), (x1, Y + H / 2), (x1 - k0, Y + H), (x0, Y + H)]
        if k:
            pts.append((x0 + k0, Y + H / 2))
        if k + 1 == n:
            fill, stroke, col, ncol, wt = PURPLE, PURPLE, "FFFFFF", "FFFFFF", True
        elif k + 1 < n:
            fill, stroke, col, ncol, wt = LIGHT, LINE, NAVY, PURPLE, False
        else:
            fill, stroke, col, ncol, wt = "FFFFFF", LINE, MUTED, PURPLE, False
        sh = poly(s, pts, fill=fill, line=stroke, lw=1.5, name=f"Espina {k + 1}")
        shape_text(sh, [[(str(k + 1), {"size": 19, "bold": True, "color": ncol, "font": MONO}),
                         (" ", {"size": 19, "font": MONO}),
                         (t, {"size": 19, "bold": wt, "color": col})]],
                   margins=((k0 if k else 0) + 18, 0, 4, 0), anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.LEFT, wrap=False)


def b_iso(s, sec, tm):
    header(s, sec)
    sid = sec.get("data-id")
    sre = q(sec, ".sre")
    layers = iso_layers(FIGKEY.get(sid, sid))
    pics = []
    for L in layers:                          # in stacking order
        pics.append((L["key"], picture(s, L["path"], L["x"], L["y"], L["w"], L["h"], name=f"Capa {L['key']}")))
    nums = [int(re.sub(r"\D", "", k.split("_")[0])) for k, _ in pics if k != "base"]
    for c in range(1, max(nums + [0]) + 1):
        items = [(p, "out") for k, p in pics if k == f"off{c}"]
        items += [(p, "in") for k, p in pics if k in (f"on{c}", f"on{c}_fog")]
        if items:
            tm.click(*items)
    if sre is not None:                       # goes over the figure, as in the HTML
        textbox(s, 84, 206, 1432, 32, [plain(sre)], size=24, color=SLATE, name="Subtítulo")
    sp = q(sec, ".spine")
    if sp is not None:
        fills = [(p.get("fill") or "").upper().lstrip("#") for p in sp.cssselect("polygon")]
        if PURPLE in fills:
            spine(s, fills.index(PURPLE) + 1)
    bring_titles_front(s)
    footsrc(s, sec)


def b_htmlsteps(s, sec, tm, box=(0, 86, 1600, 772)):
    header(s, sec)
    sid = sec.get("data-id")
    files = sorted((f for f in os.listdir(os.path.join(BUILD, "html")) if f.startswith(sid + "_s")),
                   key=lambda f: int(re.search(r"_s(\d+)", f).group(1)))
    pics = []
    for k, f in enumerate(files):
        p = flat(os.path.join(BUILD, "html", f), os.path.join(BUILD, "img", f"{sid}_html{k}.png"), box)
        pics.append(picture(s, p, box[0], box[1], box[2] - box[0], box[3] - box[1], name=f"Paso {k}"))
    for k in range(1, len(pics)):
        tm.click((pics[k], "appear"))
    bring_titles_front(s)
    footsrc(s, sec)


def b_res(s, sec, tm):
    header(s, sec)
    for k, r in enumerate(sec.cssselect(".res .r")):
        y = 258 + k * 114
        textbox(s, 84, y, 410, 74, [plain(q(r, ".k"))], size=27, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        textbox(s, 504, y, 624, 74, [plain(q(r, ".v"))], size=22, color=LINK, fnt=MONO, anchor=MSO_ANCHOR.MIDDLE)
        if k < 3:
            hline(s, 84, y + 74, 1044)
    rect(s, 1188, 258, 328, 328, fill=LIGHT, line=LINE, name="Marco QR")
    qr = os.path.join(BUILD, "img", "qr.png")
    if os.path.exists(qr):
        picture(s, qr, 1216, 286, 272, 272, name="QR")
    else:
        textbox(s, 1188, 380, 328, 80, [[("QR", {"bold": True, "color": MUTED, "size": 22})],
                                        [("se genera con REPO_URL", {"font": MONO, "size": 17, "color": SLATE})]],
                align=PP_ALIGN.CENTER)
    textbox(s, 1188, 600, 328, 50, [plain(q(sec, ".res-cap"))], size=18, color=SLATE, align=PP_ALIGN.CENTER)


def b_closing(s, sec, tm):
    fill_ph(ph(s, 104), [[("Gracias", {})]])
    bd = q(sec, ".bd")
    hs = [plain(x) for x in bd.cssselect(".h")]
    paras = [[("¿Preguntas?", {"size": 37, "bold": True, "color": NAVY})],
             [(" ", {"size": 17})],
             [(plain(q(bd, ".nm")), {"size": 28, "color": SLATE})]]
    paras += [[(h, {"size": 20, "color": LINK, "font": MONO})] for h in hs]
    paras += [[(" ", {"size": 12})], [(plain(q(bd, ".tg")), {"size": 20, "bold": True, "color": PURPLE})]]
    fill_ph(ph(s, 105), paras)


def table_block(s, tbl_el, x=84, y=236, w=1432, tm=None):
    cls = tbl_el.get("class") or ""
    sm = "sm" in cls
    md = "md" in cls                              # annex A1: td 20 px, mono 17 px, padding 11 px
    tc = "tc" in cls
    trs = tbl_el.cssselect("tr")
    ths = trs[0].cssselect("th")
    widths, rest = [], []
    for th in ths:
        m = re.search(r"width:\s*(\d+)%", th.get("style") or "")
        widths.append(w * int(m.group(1)) / 100 if m else None)
    free = w - sum(v for v in widths if v)
    nfree = sum(1 for v in widths if v is None)
    widths = [v if v else free / nfree for v in widths]
    xs = [x + sum(widths[:i]) for i in range(len(widths))]
    for i, th in enumerate(ths):
        textbox(s, xs[i], y, widths[i] - 20, 22, [[(plain(th).upper(), {"spc": 1.5})]], size=15, bold=True, color=MUTED)
    y += 34
    base = 18 if sm else (20 if md else (21 if tc else 22))
    pad = 11 if (sm or md) else (13 if tc else 16)
    for tr in trs[1:]:
        hot = "hot" in (tr.get("class") or "")
        tds = tr.cssselect("td")
        group = []
        cells, hmax = [], 0
        for i, td in enumerate(tds):
            c = td.get("class") or ""
            st = {}
            size = base
            if "m" in c.split():
                st = {"font": MONO, "color": LINK}; size = 15 if sm else (17 if md else (16 if tc else 18))
            if "k" in c.split():
                st["bold"] = True
                if hot:
                    st["color"] = PURPLE
            runs = []
            for t, r in runs_of(td, PURPLE if hot else None):
                rs = dict(st); rs.update({k: v for k, v in r.items() if k != "code"})
                if r.get("code"):
                    rs.update(font=MONO, size=16 if sm else 18)
                runs.append((t, rs))
            nl = n_lines_runs(runs, widths[i] - 20, size)
            hmax = max(hmax, nl * size * 1.32)
            cells.append((i, runs, size))
        rh = hmax + 2 * pad
        group.append(hline(s, x, y, w, PURPLE if hot else LINE, 2 if hot else 1.5))
        for i, runs, size in cells:
            group.append(textbox(s, xs[i], y + pad, widths[i] - 20, rh - 2 * pad, [runs], size=size, line=1.1))
        if tm is not None and tr.get("data-on") not in (None, "0"):
            tm.click(*[(g, "in") for g in group])
        y += rh
    hline(s, x, y, w)
    return y


def b_table(s, sec, tm):
    header(s, sec)
    tbl = q(sec, ".tbl")
    st = tbl.get("style") or ""
    m = re.search(r"top:\s*(\d+)px", st)
    y = table_block(s, tbl, y=int(m.group(1)) if m else 236, tm=tm)
    extra = [d for d in tbl if d.tag == "div"]
    for d in extra:
        never = "never" in (d.get("class") or "")
        runs = [(t, dict(st, size=19) if st.get("code") else st) for t, st in runs_of(d, None)]   # `.tail code` is 19 px
        nl = n_lines("".join(t for t, _ in runs), 1432, 22)
        tb = textbox(s, 84, y + (22 if never else 30), 1432, nl * 22 * 1.4, [runs], size=22,
                     color=PURPLE if never else NAVY, lh=1.4)
        if d.get("data-on") not in (None, "0"):
            tm.click((tb, "in"))
    footsrc(s, sec)


def b_pairs(s, sec, tm):
    header(s, sec)
    cells = q(sec, ".pairs").getchildren()
    y = 236
    textbox(s, 84, y, 400, 22, [[(plain(cells[0]).upper(), {"spc": 1.5})]], size=15, bold=True, color=MUTED)
    textbox(s, 584, y, 900, 22, [[(plain(cells[2]).upper(), {"spc": 1.5})]], size=15, bold=True, color=MUTED)
    y += 34
    body = cells[3:]
    for k in range(0, len(body), 3):
        a, ar, b = body[k:k + 3]
        nl = max(n_lines(plain(a), 420, 30), n_lines(plain(b), 932, 30, bold=True))   # as in the HTML, a cell may take two lines
        hline(s, 84, y, 1432)
        textbox(s, 84, y + 20, 420, nl * 30 * NAT, [plain(a)], size=30)
        textbox(s, 504, y + 20, 60, 40, ["→"], size=30, color=MUTED)
        textbox(s, 584, y + 20, 932, nl * 30 * NAT, [runs_of(b, None)], size=30)
        y += 40 + nl * 30 * NAT
    footsrc(s, sec)


def b_stmt(s, sec, tm):
    drop_ph(s, 106); drop_ph(s, 107)
    for i, p in enumerate(sec.cssselect(".stmt p")):
        tb = textbox(s, 84, 250 + i * 118, 1432, 110, [runs_of(p, PURPLE, {"bold": True})], size=84, bold=True, line=1.0)
        if p.get("data-on") not in (None, "0"):
            tm.click((tb, "in"))


def b_facts(s, sec, tm):
    header(s, sec)
    cw = (1432 - 64) / 2
    for k, f in enumerate(sec.cssselect(".facts .fact")):
        x = 84 + k * (cw + 64)
        g = [hline(s, x, 250, cw, PURPLE, 4)]
        g.append(textbox(s, x, 268, cw, 124, [plain(q(f, ".fn"))], size=112, bold=True, color=PURPLE, line=.9))
        ft = runs_of(q(f, ".ft"), None)
        nl = n_lines("".join(t for t, _ in ft), cw, 28)
        g.append(textbox(s, x, 406, cw, nl * 38 + 6, [ft], size=28, line=1.05))
        g.append(textbox(s, x, 406 + nl * 38 + 14, cw, 24, [plain(q(f, ".fs"))], size=16, color=MUTED))
        tm.click(*[(e, "in") for e in g])
    v = q(sec, ".verdict")
    if v is not None:
        tm.click((textbox(s, 84, 648, 1432, 48, [runs_of(v, PURPLE, {"bold": True})], size=36, bold=True), "in"))
    footsrc(s, sec)


def b_cards(s, sec, tm):
    header(s, sec)
    cw = (1432 - 64) / 3
    for k, c in enumerate(sec.cssselect(".cards3 .cd")):
        x, y = 84 + k * (cw + 32), 240
        g = [rect(s, x, y, cw, 370, fill="FFFFFF", line=LINE)]
        g.append(textbox(s, x + 28, y + 24, cw - 56, 22, [plain(q(c, ".ck")).upper()], size=15, bold=True, color=PURPLE, fnt=MONO))
        ch = runs_of(q(c, ".ch"), PURPLE, {"bold": True})
        nl = n_lines("".join(t for t, _ in ch), cw - 56, 30, True)
        g.append(textbox(s, x + 28, y + 56, cw - 56, nl * 36, [ch], size=30, bold=True, line=1.0))
        yy = y + 56 + nl * 36 + 16
        for cl in c.cssselect(".cl"):
            g.append(hline(s, x + 28, yy, cw - 56))
            t = plain(cl)
            n2 = n_lines(t, cw - 56, 21)
            g.append(textbox(s, x + 28, yy + 9, cw - 56, n2 * 26, [t], size=21, color=SLATE, line=1.0))
            yy += n2 * 26 + 18
        g.append(textbox(s, x + 28, y + 370 - 44, cw - 56, 22, [plain(q(c, ".cf"))], size=16, color=MUTED))
        if c.get("data-on") not in (None, "0"):
            tm.click(*[(e, "in") for e in g])
    say = q(sec, ".say")
    if say is not None:
        tb = textbox(s, 84, 650, 1432, 46, [runs_of(say, PURPLE)], size=34)
        if say.get("data-on") not in (None, "0"):
            tm.click((tb, "in"))
    footsrc(s, sec)


def b_cards4(s, sec, tm):
    """Slide 12 (device security): four cards, one per click, and the closing sentence."""
    header(s, sec)
    pl = Plan()
    cw, ch, y = (1432 - 3 * 28) / 4, 300, 236
    for k, c in enumerate(sec.cssselect(".cards4 .cd")):
        x = 84 + k * (cw + 28)
        hot = "hot" in (c.get("class") or "")
        g = [rect(s, x, y, cw, ch, fill="FFFFFF", line=PURPLE if hot else LINE, lw=1.5, radius=12)]
        g.append(textbox(s, x + 26, y + 26, cw - 52, 44, [plain(q(c, ".cn"))], size=40, bold=True,
                         color=PURPLE if hot else BLUE, fnt=MONO))
        g.append(textbox(s, x + 26, y + 84, cw - 52, 38, [plain(q(c, ".ch"))], size=30, bold=True))
        t = plain(q(c, ".cl"))
        g.append(textbox(s, x + 26, y + 136, cw - 52, n_lines(t, cw - 52, 22) * 31, [t], size=22, color=SLATE, lh=1.4))
        g.append(textbox(s, x + 26, y + ch - 44, cw - 52, 22, [plain(q(c, ".cf"))], size=15, color=LINK, fnt=MONO))
        pl.add(c.get("data-on"), g)
    say = q(sec, ".say")
    top = int(re.search(r"top:\s*(\d+)px", say.get("style") or "").group(1))
    pl.add(say.get("data-on"), textbox(s, 84, top, 1432, 34 * NAT + 4, [runs_of(say, PURPLE)], size=34, name="Remate"))
    pl.flush(tm)


def shot_block(s, sec, tm):
    """Every AWS window (.shot) of the slide, in order: one with data-on="0" (the act slides) is there from the start,
    in the evidence area below the subtitle; the others come in on their click, over the figure."""
    for el in sec.cssselect(".shot"):
        shot_window(s, sec, tm, el)


def shot_window(s, sec, tm, el):
    """One window with its bar. Missing screenshot: the same window with «captura pendiente» and what to capture."""
    import base64, io
    static = el.get("data-on") == "0"
    top, area = (246, 470) if static else (190, 532)
    img = q(el, "img")
    bw, bh = 1432, 38                                    # window bar
    if img is not None:
        raw = base64.b64decode(img.get("src").split(",", 1)[1])
        im = Image.open(io.BytesIO(raw))
        k = min(1429 / (im.width / 2), (area - 42) / (im.height / 2), 1.0)    # the HTML shows it at 1x of a 2x capture at most
        w, h = im.width / 2 * k, im.height / 2 * k
        path = os.path.join(BUILD, "img", f"shot_{sec.get('data-id')}_{el.get('data-on')}.jpg")
        im.convert("RGB").save(path, quality=90)
    else:
        w, h, path = 1100, 420, None
    ww = max(w, 600)
    x, y = 800 - ww / 2, top + (area - (h + bh)) / 2
    g = s.shapes.add_group_shape()
    g.name = "Captura de AWS"
    if not static:
        rect(g, 0, 190, 1600, 532, fill="FFFFFF", name="Velo")
    rect(g, x, y, ww, h + bh, fill="FFFFFF", line=LINE, lw=1.5, radius=12, name="Ventana")
    rect(g, x + 1, y + 1, ww - 2, bh - 1, fill=LIGHT, name="Barra")
    for j in range(3):
        rect(g, x + 16 + j * 19, y + bh / 2 - 5.5, 11, 11, fill="D5DEEA", radius=5.5, name="Punto")
    textbox(g, x + 86, y, ww - 100, bh, [runs_of(q(el, ".wb span"), PURPLE)], size=16, color=SLATE, fnt=MONO,
            anchor=MSO_ANCHOR.MIDDLE, name="Ruta")
    if path:
        picture(g, path, x + (ww - w) / 2, y + bh, w, h, name="Captura")
    else:
        sp = q(el, ".spend")
        rect(g, x + 1, y + bh, ww - 2, h - 1, fill=LIGHT, name="Pendiente")
        textbox(g, x + 40, y + bh + h / 2 - 70, ww - 80, 140,
                ["captura pendiente", [(plain(q(sp, "code")), {"font": MONO, "color": LINK, "size": 18})],
                 [(plain(q(sp, "small")), {"bold": False, "color": SLATE, "size": 19})]],
                size=24, bold=True, color=MUTED, align=PP_ALIGN.CENTER, name="Qué capturar")
    if not static:
        tm.click((g, "in"))


def b_hook(s, sec, tm):
    """Slide 2 (the hook): the us-east-1 meme, the news of the smart beds on click 1, the punchline on click 2."""
    import base64, io
    header(s, sec)
    figs = sec.cssselect(".hook .hi")
    ims = []
    for k, fg in enumerate(figs):
        img = q(fg, "img")
        if img is None:
            continue
        raw = base64.b64decode(img.get("src").split(",", 1)[1])
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        path = os.path.join(BUILD, "img", f"hook_{k}.jpg")
        im.save(path, quality=90)
        mh = 470 if k == 0 else 440
        h = mh; w = im.width * h / im.height
        if k and w > 720:
            w = 720; h = im.height * w / im.width
        ims.append((fg, path, w, h))
    total = sum(w for _, _, w, _ in ims) + 44 * (len(ims) - 1)
    x = 800 - total / 2
    for fg, path, w, h in ims:
        g = s.shapes.add_group_shape()
        g.name = "Imagen del gancho"
        picture(g, path, x, 206, w, h, name="Imagen")
        textbox(g, x, 206 + h + 8, w, 20, [plain(q(fg, "figcaption"))], size=15, color=MUTED, align=PP_ALIGN.CENTER,
                name="Crédito")
        if fg.get("data-on") not in (None, "0"):
            tm.click((g, "in"))
        x += w + 44
    say = q(sec, ".say")
    top = int(re.search(r"top:\s*(\d+)px", say.get("style") or "").group(1))
    tm.click((textbox(s, 84, top, 1432, 30 * NAT + 4, [runs_of(say, PURPLE)], size=30, name="Remate"), "in"))


def b_acto(s, sec, tm):
    """Slides 25-27 (the run, one act each): title, subtitle, the evidence window; on acto3 the console alarm and the
    closing sentence come in on clicks, in that order."""
    header(s, sec)
    textbox(s, 84, 206, 1432, 32, [plain(q(sec, ".sre"))], size=24, color=SLATE, name="Subtítulo")
    shot_block(s, sec, tm)
    say = q(sec, ".say")
    if say is not None:
        top = int(re.search(r"top:\s*(\d+)px", say.get("style") or "").group(1))
        tb = textbox(s, 84, top, 1432, 28 * NAT + 4, [runs_of(say, PURPLE)], size=28, name="Remate")
        tm.click((tb, "in"))


def b_seq(s, sec, tm):
    b_htmlsteps(s, sec, tm, box=(0, 190, 1600, 772))


# ── audio: slide 2 cards and slide 32 buttons ──────────────────────────────
_MP4 = {}


def mp4_of(which):
    """The pump's mp4 (still wave + audio), or None if the WAV is missing. Made only once."""
    if which not in _MP4:
        wav = audio_path(which)
        _MP4[which] = make_mp4(wave_poster(which), wav, f"pump-{which}") if wav else None
    return _MP4[which]


def play_button(s, x, y, w, h, label, enabled, size=27, name="Botón"):
    """Round purple button (grey without audio), with triangle and label: a native, editable group."""
    g = s.shapes.add_group_shape()
    g.name = name
    rect(g, x, y, w, h, fill=PURPLE if enabled else INK08, radius=h / 2, name="Fondo")
    tw = text_w(label, size, True)
    x0 = x + (w - (19 + 4 + 16 + tw)) / 2                     # triangle (19 + 4 margin) · gap 16 · label
    poly(g, [(x0 + 4, y + h / 2 - 12), (x0 + 4 + 19, y + h / 2), (x0 + 4, y + h / 2 + 12)],
         fill="FFFFFF" if enabled else SOFT, name="Triángulo")
    textbox(g, x0 + 4 + 19 + 16, y, tw + 24, h, [label], size=size, bold=True, color="FFFFFF" if enabled else MUTED,
            anchor=MSO_ANCHOR.MIDDLE, name="Rótulo")
    return g


def b_listen(s, sec, tm):
    """Slide 2: two cards (Bomba A, Bomba B) with their wave and a button that plays the audio; click 1: the question."""
    header(s, sec)
    cw, gap, cy, ch = 692, 48, 240, 348.5
    for k, card in enumerate(sec.cssselect(".snd2 .snd")):
        btn_el = q(card, ".play")
        which = btn_el.get("data-snd")
        x = 84 + k * (cw + gap)
        rect(s, x, cy, cw, ch, fill="FFFFFF", line=LINE, lw=1.5, radius=14, name=f"Tarjeta {which.upper()}")
        textbox(s, x + 27.5, top_of(cy + 23.5, 34, 1.1), 500, 34 * NAT, [plain(q(card, ".sl"))], size=34, bold=True,
                name=f"Rótulo {which.upper()}")
        wx, wy = x + 27.5, cy + 77
        mp4 = mp4_of(which)
        poster = wave_poster(which)
        if mp4:
            vid = s.shapes.add_movie(mp4, E(wx), E(wy), E(640), E(160), poster_frame_image=poster, mime_type="video/mp4")
            vid.name = f"Audio bomba {which.upper()}"
        else:
            vid = picture(s, poster, wx, wy, 640, 160, name=f"Onda {which.upper()} (audio pendiente)")
        btn = play_button(s, wx, wy + 160 + 20, 637, 64, plain(q(btn_el, ".lb")) if mp4 else "audio pendiente",
                          bool(mp4), name=f"Botón {which.upper()}")
        if mp4:
            tm.play_on_click(btn, vid)                           # a click on the button or on the wave plays the audio
            tm.play_on_click(vid, vid)
    pl = Plan()
    ask = q(sec, ".ask")
    pl.add(ask.get("data-on"), textbox(s, 84, top_of(632, 58, 1.1), 1432, 58 * NAT,
                                       [runs_of(ask, PURPLE, {"bold": True})], size=58, bold=True, name="Pregunta"))
    pl.flush(tm)
    footsrc(s, sec)


def b_acts(s, sec, tm):
    """Slide 29: the three acts of the demo (number, title, description and commands); one click per act."""
    header(s, sec)
    pl = Plan()
    y = 226
    for k, act in enumerate(sec.cssselect(".acts .act")):
        hot = "hot" in (act.get("class") or "")
        h3, p = q(act, "h3"), q(act, "p")
        codes = [plain(c) for c in act.cssselect(".ac code")]
        nl = n_lines(plain(p), 786, 22)
        tb_h = 34 * 1.1 + 8 + nl * 22 * 1.35
        cd_h = len(codes) * 40 + (len(codes) - 1) * 8
        rh = max(tb_h, cd_h) + 36
        g = []
        if k:
            g.append(hline(s, 84, y, 1432))
        g.append(textbox(s, 84, y, 70, rh, [plain(q(act, ".an"))], size=44, bold=True, color=PURPLE if hot else BLUE,
                         fnt=MONO, anchor=MSO_ANCHOR.MIDDLE))
        ty = y + (rh - tb_h) / 2
        g.append(textbox(s, 182, top_of(ty, 34, 1.1), 786, 34 * NAT, [plain(h3)], size=34, bold=True,
                         color=PURPLE if hot else NAVY))
        g.append(textbox(s, 182, ty + 34 * 1.1 + 8, 786, nl * 22 * 1.35 + 4, [plain(p)], size=22, color=SLATE, lh=1.35))
        cy = y + (rh - cd_h) / 2
        for c in codes:
            chip = rect(s, 996, cy, 520, 40, fill=LIGHT, line=LINE, lw=1.5, radius=6, name="Comando")
            shape_text(chip, [c], margins=(14, 0, 8, 0), size=20, color=NAVY, fnt=MONO, anchor=MSO_ANCHOR.MIDDLE,
                       align=PP_ALIGN.LEFT, wrap=False)
            g.append(chip)
            cy += 48
        pl.add(act.get("data-on"), g)
        y += rh
    say = q(sec, ".say")
    if say is not None:
        top = int(re.search(r"top:\s*(\d+)px", say.get("style") or "").group(1))
        pl.add(say.get("data-on"), textbox(s, 84, top, 1432, 28 * NAT + 4, [runs_of(say, PURPLE)], size=28, name="Remate"))
    pl.flush(tm)


def b_cost(s, sec, tm):
    """Slide 30: three computed numbers (raw audio, event every 10 s, per-minute summary) and the formula in the footer."""
    header(s, sec)
    pl = Plan()
    cw = (1432 - 80) / 3
    for k, cs in enumerate(sec.cssselect(".cost3 .cs")):
        x = 84 + k * (cw + 40)
        hot = "hot" in (cs.get("class") or "")
        g = [hline(s, x, 262 + 2, cw, PURPLE if hot else NAVY, 4)]
        g.append(textbox(s, x, 288, cw, 24, [[(plain(q(cs, ".cl")).upper(), {"spc": .76})]], size=19, bold=True,
                         color=BLUE, fnt=MONO))
        g.append(textbox(s, x, top_of(329.5, 112, 112 / 112), cw + 40, 112 * NAT, [[(plain(q(cs, ".cn")), {"spc": -2.2})]],
                         size=112, bold=True, color=PURPLE if hot else NAVY))
        g.append(textbox(s, x, 455.5, cw, 28 * NAT, [plain(q(cs, ".cu"))], size=28, color=SLATE))
        pl.add(cs.get("data-on"), g)
    say = q(sec, ".say")
    top = int(re.search(r"top:\s*(\d+)px", say.get("style") or "").group(1))
    pl.add(say.get("data-on"), textbox(s, 84, top, 1432, 34 * NAT + 4, [runs_of(say, PURPLE)], size=34, name="Remate"))
    pl.flush(tm)
    footsrc(s, sec)


def b_final(s, sec, tm):
    """Slide 32 (circular closing): the opening question, the two pump buttons, the event line and the phrase."""
    pl = Plan()
    fq = q(sec, ".fq")
    t = ph(s, 106)
    fill_ph(t, split_paras(runs_of(fq, PURPLE)), size=70)
    tf = t.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    t.left, t.top, t.width, t.height = E(84), E(top_of(170, 70, 1.1)), E(1432), E(70 * NAT + 4)
    # buttons: a video hidden behind each button if there is audio; the button starts it
    x = 84
    for btn_el in sec.cssselect(".fplay .play"):
        which = btn_el.get("data-snd")
        mp4 = mp4_of(which)
        label = plain(q(btn_el, ".lb")) if mp4 else "audio pendiente"
        bw = 34 * 2 + 19 + 4 + 16 + text_w(label, 25, True)
        vid = None
        if mp4:
            dot = os.path.join(BUILD, "img", "button.png")
            Image.new("RGB", (64, 16), "#" + PURPLE).save(dot)
            # the video only carries the sound: tiny, purple on purple and covered by the button (the label starts at x + 38)
            vid = s.shapes.add_movie(mp4, E(x + 28), E(276 + 20), E(8), E(16), poster_frame_image=dot, mime_type="video/mp4")
            vid.name = f"Audio bomba {which.upper()}"
        btn = play_button(s, x, 276, bw, 56, label, bool(mp4), size=25, name=f"Botón {which.upper()}")
        if mp4:
            tm.play_on_click(btn, vid)
        x += bw + 24
    # the event line (click 1)
    evt = q(sec, ".evt")
    eh, el, ef = q(evt, ".eh"), q(evt, ".el"), q(evt, ".ef")
    top, h = 372, 148
    g = [rect(s, 84, top, 30, h, fill=PURPLE, radius=10, name="Marca"),
         rect(s, 90, top, 1426, h, fill=LIGHT, line=LINE, lw=1.5, radius=10, name="Evento")]
    g.append(textbox(s, 122, top + 21.5, 1300, 18 * NAT, [[(plain(eh).upper(), {"spc": 1.5})]], size=15, bold=True, color=MUTED))
    items = []
    for ch in el:
        st = {"color": MUTED} if ch.tag == "i" else ({"bold": True, "color": PURPLE} if ch.tag == "b" else {})
        items.append((plain(ch), st))
    runs = []
    for j, (tx, st) in enumerate(items):
        runs.append((tx if j == 0 else " " + tx, dict(st, font=MONO)))
    g.append(textbox(s, 122, top + 21.5 + 18 * NAT + 12, 1380, 34, [runs], size=30, fnt=MONO))
    g.append(textbox(s, 122, top + 21.5 + 18 * NAT + 12 + 34 + 12, 1380, 22 * NAT, [plain(ef)], size=22, color=SLATE))
    pl.add(evt.get("data-on"), g)
    fz = q(sec, ".fz")
    pl.add(fz.get("data-on"), textbox(s, 84, top_of(596, 62, 1.14), 1432, 2 * 62 * 1.14 + 6,
                                      [runs_of(fz, PURPLE, {"bold": True})], size=62, bold=True, lh=1.14, name="Frase"))
    pl.flush(tm)


# slide id (data-id in deck.src.html) → (template layout, builder).
# The HTML sets the slide order; this only says how each one is built.
BUILDERS = {
    "portada": ("PORTADA", b_cover), "suena": ("CONTENIDO", b_listen), "cien": ("CONTENIDO", b_canvas),
    "inversion": ("CONTENIDO", b_duo), "memes": ("CONTENIDO", b_canvas), "quien": ("CONTENIDO", b_whoami),
    "agenda": ("CONTENIDO", b_agenda), "div1": ("DIVISOR", b_div),
    "nube": ("CONTENIDO", b_iso), "edge": ("CONTENIDO", b_iso), "tablero": ("CONTENIDO", b_canvas),
    "preguntas": ("CONTENIDO", b_table), "reflexion1": ("CONTENIDO", b_refl), "div2": ("DIVISOR", b_div),
    "equipo": ("CONTENIDO", b_iso), "seguridad": ("CONTENIDO", b_cards4), "flujo": ("CONTENIDO", b_htmlsteps), "aws": ("CONTENIDO", b_htmlsteps),
    "div3": ("DIVISOR", b_div3),
    "entrenar": ("CONTENIDO", b_iso), "optimizar": ("CONTENIDO", b_iso), "componente": ("CONTENIDO", b_iso),
    "anillos": ("CONTENIDO", b_iso), "reflexion2": ("CONTENIDO", b_refl), "sinred": ("CONTENIDO", b_iso),
    "monitoreo": ("CONTENIDO", b_iso), "reflexion3": ("CONTENIDO", b_refl3), "div4": ("DIVISOR", b_div),
    "poc": ("CONTENIDO", b_htmlsteps), "gancho": ("CONTENIDO", b_hook), "acto1": ("CONTENIDO", b_acto), "acto2": ("CONTENIDO", b_acto),
    "acto3": ("CONTENIDO", b_acto), "senales": ("CONTENIDO", b_iso), "demo": ("CONTENIDO", b_acts),
    "costo": ("CONTENIDO", b_cost), "llevo": ("CONTENIDO", b_rows), "final": ("SIMPLE", b_final),
    "recursos": ("CONTENIDO", b_res), "cierre": ("CIERRE", b_closing),
    "a1": ("CONTENIDO", b_table), "a2": ("CONTENIDO", b_seq), "a3": ("CONTENIDO", b_table),
    "a4": ("CONTENIDO", b_table), "a5": ("CONTENIDO", b_pairs), "a6": ("CONTENIDO", b_table),
    "a7": ("CONTENIDO", b_cards), "a8": ("CONTENIDO", b_table),
}

SECTIONS = [("Apertura", "portada"), ("01 · El problema", "div1"), ("02 · El patrón", "div2"),
            ("03 · Los seis pasos", "div3"), ("04 · La evidencia en AWS", "div4"), ("Cierre", "llevo"), ("Anexos", "a1")]

# The notes come from the speaker script (via the HTML). Some sentences talk about HTML keys and buttons; for PowerPoint
# they say how it is done there. If the script changes those sentences, the replacement finds nothing and the note stays as is.
# The audio sentence is a regex so it matches the asset path before and after the talk/ + pump-a.wav rename.
def note_fixes():
    n = {sid: i + 1 for i, sid in enumerate(s.get("data-id") for s in SECS)}
    return [(re.compile(r"\*Mientras suena un audio, una tecla o un clic lo detiene y no cambia de lámina\. Si los botones dicen "
                        r"«audio pendiente», faltan \S+/assets/audio/\S+-a\.wav y \S+-b\.wav\."),
             "*En PowerPoint, un clic en «Escuchar» (o en la onda) reproduce el audio; al cambiar de lámina se detiene. "
             "Si los botones dicen «audio pendiente», faltaban talk/assets/audio/pump-a.wav y pump-b.wav cuando se armó "
             "el PowerPoint: ponlos y vuelve a generarlo."),
            ("Cambia al deck: tecla A y una flecha a la derecha te llevan al anexo A2.",
             f"Salta al anexo A2: escribe {n['a2']} y Enter."),
            ("M te devuelve aquí.", f"Para volver aquí, escribe {n['acto3']} y Enter."),
            ("*Anexos: la tecla A abre A1; las flechas los recorren; M o Esc te devuelven.",
             f"*Anexos: en PowerPoint escribe el número de la lámina y Enter (A1 = {n['a1']} … A8 = {n['a8']}); para volver, "
             "el de la lámina donde estabas.")]


def notes_text(sec):
    n = H.unescape(sec.get("data-notes") or "").strip()
    for old, new in note_fixes():
        n = old.sub(lambda _: new, n) if hasattr(old, "sub") else n.replace(old, new)
    return n


def main():
    # QR (if build_deck generated it with REPO_URL)
    qr_src = None
    for sec in SECS:
        svg = sec.cssselect(".res-qr svg")
        if svg:
            qr_src = etree.tostring(svg[0]).decode()
    if qr_src:
        import cairosvg
        # the QR svg only has a viewBox (it scales with CSS); cairosvg needs an explicit size
        head = '<svg xmlns="http://www.w3.org/2000/svg"' + ("" if re.search(r"<svg[^>]*\swidth=", qr_src) else ' width="600" height="600"')
        cairosvg.svg2png(bytestring=qr_src.replace("<svg", head, 1).encode(),
                         write_to=os.path.join(BUILD, "img", "qr.png"), output_width=600)
    ids = []
    missing = [sec.get("data-id") for sec in SECS if sec.get("data-id") not in BUILDERS]
    if missing:
        sys.exit(f"✘ the HTML has slides without a builder in BUILDERS: {', '.join(missing)}")
    for sec in SECS:
        sid = sec.get("data-id")
        layout, fn = BUILDERS[sid]
        s = new_slide(layout)
        tm = Timing()
        fn(s, sec, tm)
        if fn not in (b_acto, b_hook):             # (the act slides and the hook place their own images)
            shot_block(s, sec, tm)                 # the AWS screenshot is always the slide's last click
        tm.apply(s)
        nt = notes_text(sec)
        if nt:
            s.notes_slide.notes_text_frame.text = nt
        ids.append((sid, s.slide_id))
    # sections (shown in PowerPoint's thumbnail pane)
    pres = prs.part._element
    sid_of = dict(ids)
    order = [sid for sid, _ in ids]
    secs_xml = []
    for i, (name, first) in enumerate(SECTIONS):
        a = order.index(first)
        b = order.index(SECTIONS[i + 1][1]) if i + 1 < len(SECTIONS) else len(order)
        sl = "".join(f'<p14:sldId id="{sid_of[x]}"/>' for x in order[a:b])
        secs_xml.append(f'<p14:section name="{H.escape(name)}" id="{{{str(uuid.uuid4()).upper()}}}"><p14:sldIdLst>{sl}</p14:sldIdLst></p14:section>')
    ext = etree.fromstring(
        f'<p:extLst xmlns:p="{P_NS}"><p:ext uri="{{521415D9-36F7-43E2-AB2F-B90AF26B5E84}}">'
        f'<p14:sectionLst xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main">{"".join(secs_xml)}</p14:sectionLst>'
        f'</p:ext></p:extLst>')
    old = pres.find(qn("p:extLst"))
    if old is not None:
        pres.remove(old)
    pres.append(ext)
    prs.core_properties.title = "MLOps a ciegas · DevOpsDays Bogotá 2026"
    prs.core_properties.author = "Alejandro Varela"
    prs.save(OUT)
    print(f"✔ {OUT}  ({os.path.getsize(OUT) / 1e6:.1f} MB, {len(ids)} slides)")


if __name__ == "__main__":
    main()
