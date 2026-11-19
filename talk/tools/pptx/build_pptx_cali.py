"""
Builds talk/MLOps-a-ciegas-TechDayCali-2026.pptx from a capture of talk/techdaycali.html (capture_cali.js).

One PowerPoint slide per click of the HTML deck, so advancing in PowerPoint is the same as clicking in the
browser:
- what is still: the click's final state as a full-bleed image (captured at 2x);
- what moves (the canvas charts, the architectures with packets, the station's acts): an MP4 rebuilt from
  the frames Chrome painted during that click, at their real pace, that starts by itself and stays on its
  last frame; the final-state image sits underneath.
- a short fade between slides; the speaker notes of each slide on its first click.
The text is a picture: to edit the talk, edit the HTML and run this again.

Usage:
    node capture_cali.js ../../techdaycali.html <capture dir>
    python3 build_pptx_cali.py <capture dir> [out.pptx]
"""
import json, os, subprocess, sys

from lxml import etree
from PIL import Image
from pptx import Presentation
from pptx.util import Emu

CAP = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..", "..", "MLOps-a-ciegas-TechDayCali-2026.pptx")
W, H = Emu(12192000), Emu(6858000)                     # 16:9, 13.333 × 7.5 in
NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}


def video(e):
    """The click's frames → MP4 at their real pace (each frame lasts until the next one was painted)."""
    out = os.path.join(CAP, e["frames"] + ".mp4")
    if os.path.exists(out):
        return out
    d, ts = os.path.join(CAP, e["frames"]), e["ts"]
    files = sorted(os.listdir(d))
    lst = os.path.join(CAP, e["frames"] + ".txt")
    with open(lst, "w") as f:
        for j, name in enumerate(files):
            dur = (ts[j + 1] - ts[j]) if j + 1 < len(ts) else 0.6
            f.write(f"file '{os.path.join(d, name)}'\nduration {max(dur, 0.001):.4f}\n")
        f.write(f"file '{os.path.join(d, files[-1])}'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    # limited-range yuv420p, High@4.1, avc1: what Keynote and PowerPoint (AVFoundation) accept;
                    # the screencast JPEGs are full range, and a yuvj420p stream makes Keynote reject the file
                    "-vf", "scale=1920:1080:flags=lanczos:out_range=tv,format=yuv420p", "-fps_mode", "cfr", "-r", "30",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-profile:v", "high", "-level", "4.1",
                    "-pix_fmt", "yuv420p", "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709",
                    "-color_trc", "bt709", "-tag:v", "avc1", "-movflags", "+faststart", out], check=True)
    return out


def still(e):
    """The final state, 2560 wide (sharp on a 4K projector, lighter than the 3840 capture)."""
    out = os.path.join(CAP, e["file"].replace(".jpg", "-p.jpg"))
    if not os.path.exists(out):
        Image.open(os.path.join(CAP, e["file"])).convert("RGB").resize((2560, 1440), Image.LANCZOS).save(out, quality=90)
    return out


def duration_ms(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True, check=True)
    return int(float(r.stdout.strip()) * 1000)


def autoplay(slide, spid, ms):
    """Start the movie by itself when the slide appears (PowerPoint's 'Start: Automatically')."""
    sld = slide._element
    for t in sld.findall("p:timing", NS):
        sld.remove(t)
    xml = f"""<p:timing xmlns:p="{NS['p']}"><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>
<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>
<p:par><p:cTn id="3" fill="hold"><p:stCondLst><p:cond delay="indefinite"/><p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond></p:stCondLst><p:childTnLst>
<p:par><p:cTn id="4" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>
<p:par><p:cTn id="5" presetID="1" presetClass="mediacall" presetSubtype="0" fill="hold" nodeType="afterEffect"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>
<p:cmd type="call" cmd="playFrom(0.0)"><p:cBhvr><p:cTn id="6" dur="{ms}" fill="hold"/><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:cmd>
</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>
</p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>
<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>
<p:video><p:cMediaNode vol="80000"><p:cTn id="7" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst></p:cTn><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cMediaNode></p:video>
</p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>"""
    sld.append(etree.fromstring(xml))


def fade(slide):
    sld = slide._element
    tr = etree.fromstring(f'<p:transition xmlns:p="{NS["p"]}" spd="fast"><p:fade/></p:transition>')
    t = sld.find("p:timing", NS)
    (t.addprevious(tr) if t is not None else sld.append(tr))


def main():
    man = json.load(open(os.path.join(CAP, "manifest.json")))
    if os.environ.get("LIMIT"):                          # a short test deck: only the first N clicks
        man = man[:int(os.environ["LIMIT"])]
    AUTO, FADE = os.environ.get("AUTOPLAY", "1") == "1", os.environ.get("FADE", "1") == "1"
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    prs.part._element.find("p:sldSz", NS).attrib.pop("type", None)   # the default template says 4:3
    blank = prs.slide_layouts[6]
    for n, e in enumerate(man, 1):
        s = prs.slides.add_slide(blank)
        img = still(e)
        s.shapes.add_picture(img, 0, 0, W, H)
        if e.get("frames"):
            mp4 = video(e)
            poster = os.path.join(CAP, e["frames"], sorted(os.listdir(os.path.join(CAP, e["frames"])))[0])
            mv = s.shapes.add_movie(mp4, 0, 0, W, H, poster_frame_image=poster, mime_type="video/mp4")
            if AUTO:
                autoplay(s, mv.shape_id, duration_ms(mp4))
        if FADE:
            fade(s)
        if e.get("notes"):
            s.notes_slide.notes_text_frame.text = e["notes"]
        print(f"{n:3d} {e['id']}·{e['step']}{'  (video)' if e.get('frames') else ''}", flush=True)
    prs.save(OUT)
    print("✔", os.path.abspath(OUT), f"({os.path.getsize(OUT) / 1e6:.0f} MB · {len(man)} slides)")


if __name__ == "__main__":
    main()
