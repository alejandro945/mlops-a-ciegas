"""
Set SINTÉTICO de bombas, con los mismos nombres de archivo que MIMII DUE (pump, dev).

Sirve solo para probar la tubería (synth → prepare_data → train → inference) sin los datos
reales. Nada que salga de aquí es una medición: train.py marca todo con "synthetic": true y
charla/tools/metrics.py lo muestra como «por medir».

  <raíz>/pump/train/section_00_source_train_normal_0000_sintetico.wav
  <raíz>/pump/train/section_00_target_train_normal_0000_sintetico.wav
  <raíz>/pump/source_test/section_00_source_test_{normal,anomaly}_0000.wav
  <raíz>/pump/target_test/section_00_target_test_{normal,anomaly}_0000.wav
  <raíz>/SINTETICO.txt        (marcador: prepare_data y train lo reconocen)
Además, cada WAV lleva un comentario «SINTETICO» en su cabecera (chunk LIST/INFO): aunque
alguien comprima la carpeta sin el marcador, el audio sigue diciendo que es sintético.

El sonido: giro del rotor con sus armónicos, paso de los álabes, zumbido del motor a 120 Hz,
ruido del agua y ruido de ambiente. Cada sección es otra bomba. El dominio target gira 12 %
más rápido y tiene otro ambiente. Fallas: golpes, modulación o desbalance.

Uso:  python3 model/synth.py                      → data/synthetic/
      python3 model/synth.py --out /tmp/s --segundos 4
"""
import argparse, io, os, shutil, struct, sys, wave
import numpy as np

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dataset import MARCA

SR = 16000
HERE = os.path.dirname(os.path.abspath(__file__))
POC = os.path.dirname(HERE)

# una bomba por sección: velocidad de giro (Hz), álabes, armónicos, banda del ruido del agua
SECCIONES = {
    "00": dict(giro=24.6, alabes=5, arm=[1.0, 0.55, 0.35, 0.22, 0.12, 0.08], banda=(400, 2200)),
    "01": dict(giro=29.3, alabes=6, arm=[0.8, 0.70, 0.25, 0.30, 0.10, 0.10], banda=(600, 3000)),
    "02": dict(giro=19.8, alabes=7, arm=[1.0, 0.40, 0.45, 0.15, 0.15, 0.05], banda=(300, 1800)),
}
FALLAS = ["golpes", "modulacion", "desbalance"]


def ruido_color(rng, n, forma):
    """Ruido blanco filtrado en frecuencia: forma(f) da la amplitud por frecuencia."""
    espectro = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1.0 / SR)
    y = np.fft.irfft(espectro * forma(f), n)
    return y / (np.std(y) + 1e-12)


def clip(rng, p, dominio, falla=None, segundos=10.0):
    n = int(SR * segundos)
    t = np.arange(n) / SR
    giro = p["giro"] * (1.12 if dominio == "target" else 1.0) * (1 + rng.normal(0, 0.003))
    f_inst = giro * (1 + 0.002 * np.sin(2 * np.pi * 0.13 * t + rng.uniform(0, 6.3)))
    fase = 2 * np.pi * np.cumsum(f_inst) / SR

    rotor = sum(a * (1 + 0.1 * rng.standard_normal()) * np.sin((k + 1) * fase + rng.uniform(0, 6.3))
                for k, a in enumerate(p["arm"]))
    alabes = 0.6 * np.sin(p["alabes"] * fase) + 0.25 * np.sin(2 * p["alabes"] * fase + 1.0)
    motor = 0.3 * np.sin(2 * np.pi * 120 * t) + 0.1 * np.sin(2 * np.pi * 240 * t + 0.5)
    lo, hi = p["banda"]
    agua = ruido_color(rng, n, lambda f: np.exp(-0.5 * ((f - (lo + hi) / 2) / ((hi - lo) / 2)) ** 2))
    agua *= 1 + 0.2 * np.sin(p["alabes"] * fase)
    if dominio == "target":       # otro ambiente: más fuerte y más grave
        ambiente = 0.35 * ruido_color(rng, n, lambda f: np.maximum(f, 20.0) ** -0.8)
    else:
        ambiente = 0.25 * ruido_color(rng, n, lambda f: 1 / np.sqrt(np.maximum(f, 20.0)))

    tonal = rotor + alabes
    if falla:
        g = rng.uniform(0.7, 1.2)                     # severidad
        if falla == "modulacion":                     # el giro "respira"
            tonal = tonal * (1 + 0.5 * g * np.sin(2 * np.pi * giro / 3 * t))
        elif falla == "desbalance":                   # 1× fuerte y un subarmónico
            tonal = tonal + g * (1.4 * np.sin(fase) + 0.6 * np.sin(0.5 * fase))
        elif falla == "golpes":                       # golpes con resonancia a ~2,8 kHz
            m = np.arange(int(0.006 * SR))
            golpe = np.exp(-m / (0.0015 * SR)) * np.sin(2 * np.pi * 2800 * m / SR)
            pulsos = np.zeros(n)
            vueltas = np.searchsorted(fase, np.arange(2 * np.pi, fase[-1], 2 * np.pi))
            for i in vueltas[rng.random(len(vueltas)) < 0.7]:
                pulsos[i] = rng.uniform(0.5, 1.0)
            agua = agua + 5.0 * g * np.convolve(pulsos, golpe)[:n]
    y = 0.05 * (tonal + motor + 0.5 * agua + ambiente)
    return np.clip(y, -1, 1)


def escribe(ruta, y):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((y * 32767).astype("<i2").tobytes())
    texto = MARCA + b" poc-devopsdays/model/synth.py\0"
    texto += b"\0" * (len(texto) % 2)
    info = b"INFO" + b"ICMT" + struct.pack("<I", len(texto)) + texto
    datos = buf.getvalue() + b"LIST" + struct.pack("<I", len(info)) + info
    datos = datos[:4] + struct.pack("<I", len(datos) - 8) + datos[8:]      # tamaño RIFF
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "wb") as f:
        f.write(datos)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(POC, "data", "synthetic"))
    ap.add_argument("--segundos", type=float, default=10.0)
    ap.add_argument("--train", type=int, default=16, help="clips normales source de entrenamiento por sección")
    ap.add_argument("--prueba", type=int, default=8, help="clips normales y de falla source de prueba por sección")
    ap.add_argument("--target", type=int, default=6, help="clips normales y de falla target de prueba por sección")
    ap.add_argument("--semilla", type=int, default=7)
    a = ap.parse_args()

    if os.path.isfile(os.path.join(a.out, "SINTETICO.txt")):
        shutil.rmtree(a.out)              # solo borra un set sintético anterior
    elif os.path.isdir(a.out) and os.listdir(a.out):
        raise SystemExit(f"{a.out} no está vacía y no es un set sintético: elige otra carpeta")
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "SINTETICO.txt"), "w", encoding="utf-8") as f:
        f.write("Audio sintético generado por poc-devopsdays/model/synth.py.\n"
                "Solo para probar la tubería. No es MIMII DUE y no es una medición.\n")
    rng = np.random.default_rng(a.semilla)
    raiz = os.path.join(a.out, "pump")
    n = 0
    for sec, p in SECCIONES.items():
        for i in range(a.train):
            escribe(f"{raiz}/train/section_{sec}_source_train_normal_{i:04d}_sintetico.wav", clip(rng, p, "source", None, a.segundos))
        for i in range(3):            # como en MIMII DUE: solo tres clips target para entrenar
            escribe(f"{raiz}/train/section_{sec}_target_train_normal_{i:04d}_sintetico.wav", clip(rng, p, "target", None, a.segundos))
        for dom, k in (("source", a.prueba), ("target", a.target)):
            for i in range(k):
                escribe(f"{raiz}/{dom}_test/section_{sec}_{dom}_test_normal_{i:04d}.wav", clip(rng, p, dom, None, a.segundos))
                escribe(f"{raiz}/{dom}_test/section_{sec}_{dom}_test_anomaly_{i:04d}.wav", clip(rng, p, dom, FALLAS[i % 3], a.segundos))
        n += a.train + 3 + 2 * (a.prueba + a.target)
    print(f"{n} clips sintéticos de {a.segundos:g} s en {a.out}")


if __name__ == "__main__":
    main()
