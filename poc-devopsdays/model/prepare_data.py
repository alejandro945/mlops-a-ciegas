"""
Arma el audio de la flota a partir de MIMII DUE (o del set sintético).

  data/estacion/bomba-0N/normal/   clips normales de prueba, dominio source
  data/estacion/bomba-0N/falla/    clips de falla de prueba, dominio source
  data/estacion/bomba-0N/nuevo/    clips normales de prueba, dominio target (otra velocidad)
  build/clips.json                 qué clip quedó en cada bomba

Solo usa clips DE PRUEBA, nunca de entrenamiento, y nunca los que contaminaron a la v2
(el reparto es el de dataset.py, el mismo de train.py). Cinco bombas salen de tres secciones:
la bomba-01 y la bomba-04 comparten la sección 00, la bomba-02 y la bomba-05 la 01, con
clips distintos.

Con datos reales copia además dos clips de la sección de la bomba-03 (dominio source) que no
están en la flota ni en el entrenamiento: charla/assets/audio/bomba-a.wav (normal) y
bomba-b.wav (falla). Con audio sintético no toca charla/assets.

--scores build/scores.csv (después de train.py) elige clips para que la demo sea repetible:
fallas que la v1 detecta (en la bomba-01, además, que la v2 no detecta) y normales sin alerta.
Las cifras de la charla salen de todo el set de prueba (metrics.json), no de estos clips.

Uso:  python3 model/prepare_data.py --data data/dev_data_pump.zip [--scores build/scores.csv]
      python3 model/prepare_data.py --data data/synthetic
"""
import sys
sys.dont_write_bytecode = True
import argparse, csv, glob, json, os, shutil
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
POC = os.path.dirname(HERE)
REPO = os.path.dirname(POC)
sys.path.insert(0, HERE)
import dataset as D

CARPETAS = {"normal": ("source", "normal"), "falla": ("source", "anomaly"), "nuevo": ("target", "normal")}


def umbral(build, version):
    try:
        return json.load(open(os.path.join(build, version, "stats.json")))["threshold"]
    except (OSError, ValueError, KeyError):
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(POC, "data", "dev_data_pump.zip"))
    ap.add_argument("--synthetic", action="store_true", help="trata los datos como sintéticos")
    ap.add_argument("--out", default=os.path.join(POC, "data", "estacion"))
    ap.add_argument("--build", default=os.path.join(POC, "build"))
    ap.add_argument("--charla", default=os.path.join(REPO, "charla", "assets", "audio"))
    ap.add_argument("--por-carpeta", type=int, default=5, help="clips por carpeta y por bomba")
    ap.add_argument("--scores", default="", help="scores.csv de train.py para elegir clips repetibles")
    ap.add_argument("--contaminar", type=float, default=0.5, help="el mismo valor que usaste en train.py")
    ap.add_argument("--semilla", type=int, default=D.SEMILLA)
    a = ap.parse_args()

    fuente = D.Fuente(a.data)
    sintetico = bool(a.synthetic or fuente.sintetico)
    rep = D.particion(fuente, contaminar=a.contaminar, semilla=a.semilla)
    bombas = D.secciones_de_bombas(fuente.secciones())
    rng = np.random.default_rng(a.semilla + 1)

    # scores opcionales (de train.py): para preferir clips en los que la demo se ve igual cada vez
    sc, u1, u2 = {}, umbral(a.build, "1.0.0"), umbral(a.build, "2.0.0")
    if a.scores:
        sc = {r["clip"]: r for r in csv.DictReader(open(a.scores, encoding="utf-8"))}
        if u1 is None or u2 is None:
            raise SystemExit("--scores necesita build/1.0.0/stats.json y build/2.0.0/stats.json (corre train.py)")
        if not all(c["id"] in sc for c in rep["prueba"]):
            raise SystemExit(f"{a.scores} no corresponde a estos datos: corre train.py con el mismo --data")
        if json.load(open(os.path.join(a.build, "1.0.0", "stats.json"))).get("synthetic") != sintetico:
            raise SystemExit("los modelos de build/ y estos datos no son del mismo tipo (real contra sintético)")
    alerta = lambda c, v, u: c["id"] in sc and float(sc[c["id"]][v]) > u

    def preferencia(c, carpeta, bomba):
        """Menor es mejor. Sin scores, todo empata y decide el azar."""
        if not sc or carpeta == "nuevo":
            return 0
        canario = bomba == D.CANARIO
        if carpeta == "falla":
            return (not alerta(c, "v1", u1)) * 2 + (canario and alerta(c, "v2", u2))
        return alerta(c, "v1", u1) * 2 + (canario and alerta(c, "v2", u2))

    libres = {}   # (sección, carpeta) → clips de prueba disponibles
    for c in rep["prueba"]:
        for carpeta, (dom, verdad) in CARPETAS.items():
            if c["dominio"] == dom and c["verdad"] == verdad:
                libres.setdefault((c["seccion"], carpeta), []).append(c)
    for k in libres:
        libres[k] = [libres[k][i] for i in rng.permutation(len(libres[k]))]

    # 1 · los dos audios de la charla (sección de la bomba-03, dominio source), fuera de la flota
    sec_charla = bombas[D.ESCENARIO]
    charla = {}
    for nombre, carpeta in (("bomba-a", "normal"), ("bomba-b", "falla")):
        pool = libres.get((sec_charla, carpeta), [])
        if not pool:
            continue
        if sc and all(c["id"] in sc for c in pool):
            v = lambda c: float(sc[c["id"]]["v1"])
            if carpeta == "falla":   # la falla más clara que la v1 detecta
                elegido = max(pool, key=v)
            else:                    # un normal típico, sin alerta
                sin = [c for c in pool if v(c) <= u1] or pool
                med = float(np.median([v(c) for c in sin]))
                elegido = min(sin, key=lambda c: abs(v(c) - med))
        else:
            elegido = pool[0]
        pool.remove(elegido)
        charla[nombre] = elegido

    # 2 · la flota: la bomba-01 elige primero (es la que tiene más condiciones)
    orden = sorted(bombas, key=lambda b: (b != D.CANARIO, b))
    por_seccion = {s: sum(1 for b in bombas if bombas[b] == s) for s in set(bombas.values())}
    flota = {b: {"seccion": bombas[b]} for b in sorted(bombas)}
    for b in orden:
        sec = bombas[b]
        for carpeta in CARPETAS:
            pool = libres.get((sec, carpeta), [])
            k = min(a.por_carpeta, max(1, len(pool) // max(1, por_seccion[sec]))) if pool else 0
            pool.sort(key=lambda c: preferencia(c, carpeta, b))     # sort estable: el azar desempata
            elegidos, libres[(sec, carpeta)] = pool[:k], pool[k:]
            flota[b][carpeta] = elegidos
            if sc and carpeta != "nuevo":
                malos = sum(1 for c in elegidos if preferencia(c, carpeta, b))
                if malos:
                    print(f"  aviso: {b}/{carpeta}: {malos} de {k} clips no cumplen la preferencia (no alcanzan los clips)")
            if not elegidos:
                print(f"  aviso: {b}/{carpeta} queda vacía")
        por_seccion[sec] -= 1

    # 3 · copiar, legible para todos: en el contenedor el componente corre como otro usuario
    for viejo in glob.glob(os.path.join(a.out, "bomba-*", "*", "*.wav")):
        os.remove(viejo)
    for b, info in flota.items():
        for carpeta in CARPETAS:
            d = os.path.join(a.out, b, carpeta)
            os.makedirs(d, exist_ok=True)
            for c in info[carpeta]:
                ruta = os.path.join(d, c["id"] + ".wav")
                with open(ruta, "wb") as f:
                    f.write(fuente.leer(c))
                os.chmod(ruta, 0o644)
            os.chmod(d, 0o755)
        os.chmod(os.path.join(a.out, b), 0o755)
    os.chmod(a.out, 0o755)

    copiados = []
    if not sintetico and fuente.maquina == "pump" and charla:   # solo bombas confirmadas llegan a la charla
        os.makedirs(a.charla, exist_ok=True)
        for nombre, c in charla.items():
            wav = fuente.leer(c)
            if D.es_sintetico(wav):         # doble chequeo: nunca audio sintético en la charla
                raise SystemExit(f"{c['id']} es sintético: no lo copio a {a.charla}")
            with open(os.path.join(a.charla, nombre + ".wav"), "wb") as f:
                f.write(wav)
            copiados.append(f"{nombre}.wav = {c['id']}")
        with open(os.path.join(a.charla, "ATRIBUCION.txt"), "w", encoding="utf-8") as f:
            f.write("Sonidos reales de bombas industriales: MIMII DUE (Hitachi, Ltd.), set de desarrollo, pump.\n"
                    "Licencia CC BY-NC-SA 4.0 · https://zenodo.org/records/4740355\n"
                    "Tanabe et al., 2021, «MIMII DUE: Sound Dataset for Malfunctioning Industrial Machine\n"
                    "Investigation and Inspection with Domain Shifts due to Changes in Operational and\n"
                    "Environmental Conditions», arXiv:2105.02702.\n"
                    "Copiados sin cambios por poc-devopsdays/model/prepare_data.py:\n"
                    + "".join(f"  {x}\n" for x in copiados))

    info = {
        "dataset": ("sintético (estructura de MIMII DUE · pump)" if sintetico else
                    f"MIMII DUE · {fuente.maquina or 'máquina sin confirmar'} · dev"),
        "synthetic": sintetico,
        "datos": a.data,
        "curado_con_scores": bool(sc),
        "seccion_contaminada": rep["seccion_contaminada"],
        "contaminacion": [c["id"] for c in rep["contaminacion"]],
        "charla": {n: {"clip": c["id"], "seccion": c["seccion"], "copiado": not sintetico} for n, c in charla.items()},
        "bombas": {b: {"seccion": v["seccion"], **{k: [c["id"] for c in v[k]] for k in CARPETAS}}
                   for b, v in flota.items()},
    }
    os.makedirs(a.build, exist_ok=True)
    with open(os.path.join(a.build, "clips.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=1)
        f.write("\n")

    for b, v in flota.items():
        print(f"  {b} (sección {v['seccion']}): " + " · ".join(f"{k} {len(v[k])}" for k in CARPETAS))
    if copiados:
        print("  charla/assets/audio: " + " · ".join(copiados))
    elif sintetico:
        print("  audio sintético: no toco charla/assets/audio")
    print(f"flota en {a.out} · mapa en {os.path.join(a.build, 'clips.json')}")


if __name__ == "__main__":
    main()
