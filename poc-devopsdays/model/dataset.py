"""
Lee MIMII DUE (bombas) desde el zip, desde una carpeta ya descomprimida o desde el set
sintético, y reparte los clips. prepare_data.py y train.py usan este mismo reparto, así que
la flota nunca recibe un clip con el que se entrenó.

Reparto (determinista, por sección):
  train          normales source de entrenamiento (90 %)        → aprende la v1 (y la v2)
  val            normales source de entrenamiento (10 %)        → fija el umbral
  contaminacion  la mitad de las fallas source de prueba de la sección de la bomba-01
                 → solo para la v2 (la semana en que la bomba ya fallaba)
  prueba         todos los clips de prueba menos la contaminación → medir y armar la flota
Los tres clips target de entrenamiento no se usan.
"""
import os, re, zipfile
import numpy as np

PATRON = re.compile(r"section_(\d+)_(source|target)_(train|test)_(normal|anomaly)_(\d+)")

# cinco bombas a partir de tres secciones: la 01 y la 04 comparten la 00; la 02 y la 05, la 01
BOMBAS = {"bomba-01": "00", "bomba-02": "01", "bomba-03": "02", "bomba-04": "00", "bomba-05": "01"}
CANARIO = "bomba-01"      # anillo 0: la que recibe la v2 en la demo; su sección contamina a la v2
ESCENARIO = "bomba-03"    # la que falla en el acto 1; los audios de la charla salen de su sección
SEMILLA = 2026
# máquinas de MIMII / MIMII DUE / DCASE: si los audios dicen otra, no son bombas
MAQUINAS = ("fan", "gearbox", "pump", "slider", "valve", "toycar", "toytrain", "bearing", "shaker", "bandsaw",
            "grinder", "toydrone", "toynscale", "vacuum", "toytank")
DESCARGA = "https://zenodo.org/records/4740355/files/dev_data_pump.zip?download=1"
MARCA = b"SINTETICO"      # synth.py la escribe en la cabecera de cada WAV


class Fuente:
    """Lista de clips de un zip o de una carpeta. Cada clip es un dict:
    id, seccion, dominio (source|target), parte (train|test), verdad (normal|anomaly), ref."""

    def __init__(self, ruta, maquina="pump"):
        self.ruta = os.path.abspath(ruta)
        self.zip = None
        if os.path.isdir(ruta):
            nombres = [os.path.relpath(os.path.join(d, f), ruta)
                       for d, _, fs in os.walk(ruta) for f in fs]
            self.sintetico = os.path.isfile(os.path.join(ruta, "SINTETICO.txt"))
        elif zipfile.is_zipfile(ruta):
            self.zip = zipfile.ZipFile(ruta)
            nombres = self.zip.namelist()
            self.sintetico = any(os.path.basename(n) == "SINTETICO.txt" for n in nombres)
        else:
            raise SystemExit(f"no encuentro los datos en {ruta} (ni carpeta ni zip)")

        wavs = [n for n in nombres if n.lower().endswith(".wav")
                and "__MACOSX" not in n and not os.path.basename(n).startswith("._")]
        # si el zip o la carpeta trae otras máquinas, quédate con las bombas
        partes = lambda n: re.split(r"[\\/]", n.lower())
        if any(maquina in partes(n) for n in wavs):
            wavs = [n for n in wavs if maquina in partes(n)]

        # ¿de qué máquina son? Lo dicen las carpetas del zip (pump/…) o el nombre del archivo (dev_data_pump.zip).
        # Una carpeta suelta (train/, source_test/…) no lo dice: los nombres de los clips son iguales en todas.
        pistas = {p for n in wavs for p in partes(n)[:-1]}
        pistas |= set(re.split(r"[^a-z]+", os.path.basename(self.ruta).lower()))
        halladas = [m for m in MAQUINAS if m in pistas]
        self.maquina = maquina if maquina in halladas else (halladas[0] if halladas else None)

        vistos, self.clips = set(), []
        for n in sorted(wavs):
            m = PATRON.search(os.path.basename(n))
            if not m:
                continue
            cid = os.path.splitext(os.path.basename(n))[0]
            if cid in vistos:
                continue
            vistos.add(cid)
            sec, dom, parte, verdad, num = m.groups()
            self.clips.append(dict(id=cid, seccion=f"{int(sec):02d}", dominio=dom, parte=parte,
                                   verdad=verdad, n=int(num), ref=n))
        if not self.clips:
            raise SystemExit(f"{ruta}: ningún WAV con nombres de MIMII DUE (section_XX_source_train_normal_XXXX…)")
        self.sintetico = self.sintetico or es_sintetico(self.leer(self.clips[0]))
        if self.sintetico:
            self.maquina = maquina
        elif self.maquina and self.maquina != maquina:
            raise SystemExit(f"{ruta}: estos audios son de «{self.maquina}», no de bombas ({maquina}).\n"
                             f"Baja dev_data_pump.zip ({DESCARGA}) y déjalo, sin descomprimir, en data/.")
        elif self.maquina is None:
            print(f"(aviso) {ruta}: no puedo confirmar que sean bombas; la carpeta no dice la máquina.\n"
                  f"        Las cifras quedan marcadas sin confirmar y no llegan a las láminas.\n"
                  f"        Usa el zip tal cual: data/dev_data_pump.zip")

    def leer(self, clip):
        """Bytes del WAV, sin descomprimir el resto del zip."""
        if self.zip is not None:
            return self.zip.read(clip["ref"])
        with open(os.path.join(self.ruta, clip["ref"]), "rb") as f:
            return f.read()

    def secciones(self):
        return sorted({c["seccion"] for c in self.clips})


def es_sintetico(wav):
    """True si el WAV salió de synth.py (lleva la marca en su cabecera)."""
    return MARCA in wav[:64] or MARCA in wav[-128:]


def _mezcla(lista, semilla, etiqueta):
    """Permutación determinista que no depende de las otras secciones."""
    rng = np.random.default_rng([semilla, sum(map(ord, etiqueta))])
    return [lista[i] for i in rng.permutation(len(lista))]


def particion(fuente, contaminar=0.5, val=0.1, semilla=SEMILLA):
    seccion_contaminada = secciones_de_bombas(fuente.secciones())[CANARIO]
    rep = {"train": [], "val": [], "contaminacion": [], "prueba": [], "seccion_contaminada": seccion_contaminada}
    for sec in fuente.secciones():
        de = lambda dom, parte, verdad: [c for c in fuente.clips if c["seccion"] == sec and c["dominio"] == dom
                                          and c["parte"] == parte and c["verdad"] == verdad]
        tr = _mezcla(de("source", "train", "normal"), semilla, f"val{sec}")
        nval = max(1, int(round(val * len(tr)))) if len(tr) > 1 else 0
        rep["val"] += tr[:nval]
        rep["train"] += tr[nval:]
        prueba = [c for c in fuente.clips if c["seccion"] == sec and c["parte"] == "test"]
        if sec == seccion_contaminada and contaminar > 0:
            fallas = _mezcla(de("source", "test", "anomaly"), semilla, f"cont{sec}")
            cont = fallas[: int(contaminar * len(fallas))]
            rep["contaminacion"] += cont
            ids = {c["id"] for c in cont}
            prueba = [c for c in prueba if c["id"] not in ids]
        rep["prueba"] += prueba
    return rep


def secciones_de_bombas(secciones):
    """BOMBAS, o un reparto por turnos si los datos traen otras secciones."""
    if all(s in secciones for s in BOMBAS.values()):
        return dict(BOMBAS)
    return {b: secciones[i % len(secciones)] for i, b in enumerate(BOMBAS)}
