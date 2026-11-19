"""
Builds the PDF of the Tech Day Cali deck from the same capture as the PowerPoint (capture_cali.js).

One page per slide, in its final state (every click revealed), main slides first, then the annex.
With ALL_CLICKS=1, one page per click instead (the same sequence as the PowerPoint).

Usage:
    python3 build_pdf_cali.py <capture dir> [out.pdf]
"""
import json, os, sys

from PIL import Image

CAP = sys.argv[1]
ALL = os.environ.get("ALL_CLICKS") == "1"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
    os.path.dirname(__file__), "..", "..", "MLOps-a-ciegas-TechDayCali-2026" + ("-clics" if ALL else "") + ".pdf")

man = json.load(open(os.path.join(CAP, "manifest.json")))
if not ALL:                                              # the last click of each slide
    last = {}
    for e in man:
        last[e["id"]] = e
    man = [e for e in man if last[e["id"]] is e]
pages = [Image.open(os.path.join(CAP, e["file"])).convert("RGB").resize((2560, 1440), Image.LANCZOS) for e in man]
pages[0].save(OUT, save_all=True, append_images=pages[1:], resolution=192, quality=88)
print("✔", os.path.abspath(OUT), f"({os.path.getsize(OUT) / 1e6:.0f} MB · {len(pages)} pages)")
