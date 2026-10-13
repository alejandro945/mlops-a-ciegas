"""
Turns snap.js captures (DOM state at each step) into 2x PNGs,
without title, kicker or footer: the PowerPoint puts those as native elements on top.

    node snap.js ../../devopsdays.html steps.json "flujo:all,aws:all,poc:0,a2:0"
    python3 render_html.py steps.json out/

SVGs that are not 1600 wide (the spine bar, waves) are sized to their container;
standalone architectures in a .fig (the PoC) and the sequence (annex A2) get the same .92 scaling as the HTML.
"""
import base64, json, os, re, shutil, subprocess, sys, tempfile
import cairosvg
from weasyprint import HTML

SCALE = 2


def main(src, out):
    J = json.load(open(src))
    os.makedirs(out, exist_ok=True)
    css = re.sub(r'url\(data:font/woff2;base64,[^)]*\)', 'local("Carlito")', J["css"])
    qa = ('@page{size:1600px 900px;margin:0} body{margin:0}'
          '.s{position:relative!important;opacity:1!important;width:1600px;height:900px;page-break-after:always;overflow:hidden;background:#fff!important}'
          '.fig,.stack{left:0;top:0;right:0;bottom:0} .stack{position:absolute;width:1600px;height:900px}'
          'img.svgimg{position:absolute;left:0;top:0;width:1600px;height:900px}'
          '.kick,.ttl,.foot,.fsrc,.anx{visibility:hidden!important}')
    body, names = [], []
    for p in J["pages"]:
        h = p["html"]
        for j, sv in enumerate(p["svgs"]):
            svg = sv["svg"]
            if "xmlns=" not in svg[:200]:
                svg = svg.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
            svg = re.sub(r'\sclass="[^"]*"', "", svg)
            vb = re.search(r'viewBox="([\d.\s-]+)"', svg)
            full = vb and vb.group(1).split()[2] == "1600"
            png = cairosvg.svg2png(bytestring=svg.encode(), output_width=1600 * SCALE if full else None,
                                   scale=1 if full else SCALE)
            uri = "data:image/png;base64," + base64.b64encode(png).decode()
            if "seq" in sv["cls"]:
                w = re.search(r'width="([\d.]+)"', svg); hh = re.search(r'height="([\d.]+)"', svg)
                size = f'width:{w.group(1)}px;height:{hh.group(1)}px;' if w and hh else ''
                rep = f'<img src="{uri}" style="position:absolute;left:0;top:0;{size}transform:scale(.92);transform-origin:800px 196px">'
            elif not full:
                # an SVG that is not 1600 wide (the spine bar, the wave) fills its container, not the whole slide
                rep = f'<img src="{uri}" style="display:block;width:100%;height:100%">'
            elif "arq" in sv["cls"] and not sv["stack"]:
                # standalone architecture in a .fig (the PoC): the HTML scales it to .92 to keep the footer clear, like the .stack ones
                rep = f'<img class="svgimg" src="{uri}" style="transform:scale(.92);transform-origin:800px 196px">'
            else:
                rep = f'<img class="svgimg" src="{uri}">'
            h = h.replace(f'<img data-svg="{j}">', rep, 1)
        body.append(h)
        names.append(f'{p["id"]}_s{p["step"]}')
    doc = (f'<html><head><meta charset="utf-8"><style>{css}</style><style>{qa}</style></head>'
           f'<body><div id="deck">{"".join(body)}</div></body></html>')
    with tempfile.TemporaryDirectory() as tmp:
        pdf = os.path.join(tmp, "p.pdf")
        HTML(string=doc, base_url="/").write_pdf(pdf)
        subprocess.run(["pdftoppm", "-r", str(96 * SCALE), "-png", pdf, os.path.join(tmp, "pg")], check=True)
        pages = sorted(f for f in os.listdir(tmp) if f.startswith("pg"))
        for f, n in zip(pages, names):
            shutil.move(os.path.join(tmp, f), os.path.join(out, n + ".png"))
    print("✔", len(names), "captures")


if __name__ == "__main__":
    main(*sys.argv[1:3])
