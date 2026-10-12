"""
Componente de escucha que corre en el equipo de la estación (Greengrass v2).

Escucha una bomba clip por clip: saca las features (features.py), calcula el score con el
autoencoder ONNX y, por cada clip, publica un EVENTO en IoT Core. El audio nunca sale del
equipo; sale un JSON de unos cientos de bytes:

  device, model_version, sha256      · dónde y con qué versión
  seq, ts, clip, domain              · qué clip escuchó y cuándo decidió (ts en ms)
  score, threshold, alert            · qué decidió y con cuánta seguridad
  input_z                            · nivel de la entrada: distancia media, en desviaciones
                                       estándar, a la huella de stats.json
  latency_ms                         · features + inferencia
  truth                              · solo en la demo: la carpeta dice si el audio es de falla

El audio de la demo (solo lectura):  <audio-root>/<equipo>/{normal,falla,nuevo}/*.wav
El archivo --mode-file dice qué carpeta suena (normal, falla o nuevo; por defecto normal) y se
relee en cada clip: demo/falla.sh y demo/dominio.sh lo cambian sin reiniciar nada.

Uso en el equipo (lo arma la receta):
  python3 -u inference.py --model model.onnx --stats stats.json --audio-root /data/estacion \\
      --mode-file /run/estacion/modo --version 1.0.0 --topic estacion/eventos --threshold 0.83 --interval 3
Sin AWS:  AWS_IOT_THING_NAME=bomba-03 python3 inference.py ... --local    (imprime los eventos)
"""
import sys
sys.dont_write_bytecode = True               # los artefactos de Greengrass son de solo lectura
import argparse, hashlib, json, os, re, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import onnxruntime as ort
import features as F

MODOS = ("normal", "falla", "nuevo")
VERDAD = {"normal": "normal", "falla": "anomaly", "nuevo": "normal"}

p = argparse.ArgumentParser(description="Escucha una bomba y publica un evento por clip.")
p.add_argument("--model", required=True)
p.add_argument("--stats", required=True, help="stats.json: huella de las features, umbral, versión y sha256")
p.add_argument("--audio-root", default="/data/estacion")
p.add_argument("--mode-file", default="/run/estacion/modo")
p.add_argument("--version", default="", help="por defecto, la de stats.json")
p.add_argument("--topic", default="estacion/eventos")
p.add_argument("--threshold", default="", help="umbral del score; vacío = el de stats.json")
p.add_argument("--interval", type=float, default=3.0, help="segundos entre clips")
p.add_argument("--local", action="store_true", help="imprime los eventos en vez de publicarlos")
p.add_argument("--max", type=int, default=0, help="corta después de N eventos (0 = nunca)")
a = p.parse_args()


def log(msg):
    print(f"[estacion] {msg}", file=sys.stderr, flush=True)


stats = json.load(open(a.stats, encoding="utf-8"))
MU = np.array(stats["mean"], dtype=np.float32)
SD = np.array(stats["std"], dtype=np.float32)
version = a.version or stats.get("version", "?")
sha = hashlib.sha256(open(a.model, "rb").read()).hexdigest()
if stats.get("sha256") and stats["sha256"] != sha:
    log(f"AVISO: el sha256 de {a.model} no coincide con el de stats.json (¿artefactos de otra versión?)")
try:
    umbral = float(a.threshold)
except ValueError:
    umbral = float(stats["threshold"])        # sin configuración (o vacía): el de esta versión

so = ort.SessionOptions()
so.intra_op_num_threads = so.inter_op_num_threads = 1
sess = ort.InferenceSession(a.model, so, providers=["CPUExecutionProvider"])
entrada = sess.get_inputs()[0].name
device = os.environ.get("AWS_IOT_THING_NAME", "local-device")
carpeta = os.path.join(a.audio_root, device)

if a.local:
    def publish(evt):
        print(json.dumps(evt, ensure_ascii=False), flush=True)
else:
    from awsiot.greengrasscoreipc.clientv2 import GreengrassCoreIPCClientV2
    from awsiot.greengrasscoreipc.model import QOS
    ipc = GreengrassCoreIPCClientV2()

    def _resultado(fut):
        if fut.exception() is not None:
            log(f"no se pudo publicar: {fut.exception()}")

    def publish(evt):
        # QoS 1: sin red, la cola del nucleus guarda el evento y lo manda al volver.
        # Asíncrono: el equipo sigue escuchando y decidiendo aunque la red no responda.
        fut = ipc.publish_to_iot_core_async(topic_name=a.topic, qos=QOS.AT_LEAST_ONCE,
                                            payload=json.dumps(evt).encode())
        fut.add_done_callback(_resultado)


def modo():
    try:
        m = open(a.mode_file).read().strip().lower()
    except OSError:
        return "normal"
    return m if m in MODOS else "normal"


def clips(m):
    d = os.path.join(carpeta, m)
    try:
        return sorted(os.path.join(d, f) for f in os.listdir(d) if f.lower().endswith(".wav"))
    except OSError:
        return []


def dominio(nombre, m):
    r = re.search(r"_(source|target)_", nombre)
    return r.group(1) if r else ("target" if m == "nuevo" else "source")


log(f"{device} · modelo {version} sha256={sha[:12]}… · umbral {umbral:.4g} · audio {carpeta}")
pos = {m: 0 for m in MODOS}
avisado = set()
seq = 0
while True:
    inicio = time.monotonic()
    m = modo()
    lista = clips(m)
    if not lista:
        if m not in avisado:
            log(f"no hay clips en {os.path.join(carpeta, m)}; espero")
            avisado.add(m)
        time.sleep(max(a.interval, 1.0))
        continue
    ruta = lista[pos[m] % len(lista)]
    pos[m] += 1
    try:
        x, sr = F.read_wav(ruta)
        t0 = time.perf_counter()
        X = F.clip_features(x, sr)
        score = float(sess.run(None, {entrada: X})[0].mean())
        ms = (time.perf_counter() - t0) * 1000
    except Exception as e:                    # un clip roto no tumba el componente
        log(f"no pude escuchar {ruta}: {e}")
        time.sleep(a.interval)
        continue
    seq += 1
    nombre = os.path.splitext(os.path.basename(ruta))[0]
    evt = {
        "device": device,
        "model_version": version,
        "sha256": sha,
        "seq": seq,
        "ts": int(time.time() * 1000),
        "clip": nombre,
        "domain": dominio(nombre, m),
        "score": float(f"{score:.4g}"),
        "threshold": float(f"{umbral:.4g}"),
        "alert": score > umbral,
        "input_z": round(F.input_z(X, MU, SD), 3),
        "latency_ms": round(ms, 2),
        "truth": VERDAD[m],
    }
    publish(evt)
    if a.max and seq >= a.max:
        break
    time.sleep(max(0.0, a.interval - (time.monotonic() - inicio)))
