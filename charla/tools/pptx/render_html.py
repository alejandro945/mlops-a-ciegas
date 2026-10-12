"""
Convierte las capturas de snap.js (estado del DOM en cada paso) en PNG a 2x,
sin título, antetítulo ni pie: el PowerPoint pone esos elementos nativos encima.

    node snap.js ../../devopsdays.html pasos.json "flujo:all,aws:all,poc:0,a2:0"
    python3 render_html.py pasos.json salida/

Los SVG que no miden 1600 de ancho (barra de la espina, ondas) se ponen a su tamaño en su contenedor;
las arquitecturas sueltas en un .fig (la PoC) y la secuencia (anexo A2) llevan el mismo escalado .92 del HTML.
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
                # un SVG que no mide 1600 de ancho (la barra de la espina, la onda) llena su contenedor, no la lámina entera
                rep = f'<img src="{uri}" style="display:block;width:100%;height:100%">'
            elif "arq" in sv["cls"] and not sv["stack"]:
                # arquitectura suelta en un .fig (la PoC): el HTML la escala a .92 para dejar libre el pie, como a las de .stack
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
    print("✔", len(names), "capturas")


if __name__ == "__main__":
    main(*sys.argv[1:3])
