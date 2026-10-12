"""
Entrena el modelo de la bomba y mide todo lo que muestra la charla.

  v1.0.0  autoencoder que aprende SOLO con sonido normal del dominio source
  v2.0.0  el mismo autoencoder, pero su entrenamiento incluye la semana en que una bomba ya
          fallaba (clips de falla de la sección de la bomba-01). Se evalúa con fallas que NO vio.
  INT8    la v1 cuantizada con onnxruntime.quantization.quantize_dynamic, solo para medir

El modelo ONNX recibe las features de un clip (N vectores de 320) y devuelve el error de
reconstrucción de cada vector. Score del clip = la media de esos errores.
Umbral = percentil 95 de los scores de los clips normales de validación (10 % de los clips
normales de entrenamiento que el modelo no vio): aceptas que ~5 % del sonido normal dé alerta.

Escribe en build/ (o en --build):
  <versión>/model.onnx, stats.json, features.py, inference.py   (+ model.int8.onnx en la 1.0.0)
  metrics.json   las cifras de las láminas (claves de charla/tools/metrics.py)
  scores.csv     el score de cada clip de prueba con las tres variantes

Uso:  python3 model/train.py --data data/dev_data_pump.zip
      python3 model/train.py --data data/synthetic --synthetic --rapido      (solo prueba la tubería)
"""
import sys
sys.dont_write_bytecode = True
import argparse, csv, hashlib, json, logging, os, resource, shutil, time, warnings
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
POC = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import features as F
import dataset as D

import onnx
import onnxruntime as ort
from onnx import TensorProto, helper
from onnxruntime.quantization import QuantType, quantize_dynamic
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import roc_auc_score
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

CAPAS = (128, 128, 8, 128, 128)     # 320 → 128 → 128 → 8 → 128 → 128 → 320
V1, V2 = "1.0.0", "2.0.0"
T0 = time.time()


def log(msg):
    print(f"[{time.time() - T0:6.1f} s] {msg}", flush=True)


def carga(fuente, clips, tramas, rng, nombre):
    """Features de varios clips; `tramas` vectores al azar por clip (0 = todos) para cuidar la RAM."""
    bloques = []
    for i, c in enumerate(clips, 1):
        X = F.wav_features(fuente.leer(c))
        if tramas and len(X) > tramas:
            X = X[np.sort(rng.choice(len(X), tramas, replace=False))]
        bloques.append(X)
        if i % 500 == 0:
            log(f"  {nombre}: {i}/{len(clips)} clips")
    return np.concatenate(bloques)


def entrena(X, epocas, semilla):
    escala = StandardScaler().fit(X)
    Z = escala.transform(X).astype(np.float32)
    ae = MLPRegressor(hidden_layer_sizes=CAPAS, activation="relu", solver="adam", batch_size=256,
                      learning_rate_init=1e-3, max_iter=epocas, random_state=semilla)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        ae.fit(Z, Z)                   # aprende a reconstruir el sonido normal
    return Pipeline([("escala", escala), ("ae", ae)])


def exporta(pipe, ruta, version):
    """skl2onnx + tres nodos al final: el modelo devuelve el error de reconstrucción por vector."""
    onx = convert_sklearn(pipe, initial_types=[("features", FloatTensorType([None, F.DIM]))],
                          target_opset={"": 17, "ai.onnx.ml": 3})
    g = onx.graph
    z = next(n.output[0] for n in g.node if n.op_type == "Scaler")     # la entrada estandarizada
    rec = g.output[0].name                                             # la reconstrucción
    ultimo = next(n for n in g.node if rec in n.output)
    if ultimo.op_type == "Reshape":          # skl2onnx aplana la salida: toma la de antes, (N, 320)
        rec = ultimo.input[0]
        g.node.remove(ultimo)
        usados = {i for n in g.node for i in n.input}
        for ini in [i for i in g.initializer if i.name not in usados]:
            g.initializer.remove(ini)
    g.node.extend([
        helper.make_node("Sub", [rec, z], ["error_dif"]),
        helper.make_node("Mul", ["error_dif", "error_dif"], ["error_cuad"]),
        helper.make_node("ReduceMean", ["error_cuad"], ["score"], axes=[1], keepdims=0),
    ])
    del g.output[:]
    g.output.extend([helper.make_tensor_value_info("score", TensorProto.FLOAT, [None])])
    onx.producer_name = "poc-devopsdays/model/train.py"
    helper.set_model_props(onx, {"version": version, "features": json.dumps(F.PARAMS)})
    onnx.checker.check_model(onx)
    with open(ruta, "wb") as f:
        f.write(onx.SerializeToString())


def sesion(ruta):
    so = ort.SessionOptions()
    so.intra_op_num_threads = so.inter_op_num_threads = 1      # un hilo, como en un equipo pequeño
    so.log_severity_level = 3
    return ort.InferenceSession(ruta, so, providers=["CPUExecutionProvider"])


def score(s, X):
    return float(s.run(None, {s.get_inputs()[0].name: X})[0].mean())


def sha256(ruta):
    return hashlib.sha256(open(ruta, "rb").read()).hexdigest()


def auc(neg, pos):
    if not len(neg) or not len(pos):
        return None
    return float(roc_auc_score([0] * len(neg) + [1] * len(pos), list(neg) + list(pos)))


def tasa(xs):
    return float(np.mean(xs)) if len(xs) else None


def mide(filas, col, umbral, dominio, seccion=None):
    """AUC, fallas detectadas, falsas alarmas y alertas sobre los clips de prueba (sin contaminación)."""
    sel = [r for r in filas if r["grupo"] == "prueba" and r["dominio"] == dominio
           and (seccion is None or r["seccion"] == seccion)]
    neg = np.array([r[col] for r in sel if r["verdad"] == "normal"])
    pos = np.array([r[col] for r in sel if r["verdad"] == "anomaly"])
    todos = np.array([r[col] for r in sel])
    return {"auc": auc(neg, pos), "recall": tasa(pos > umbral), "false_alarm": tasa(neg > umbral),
            "alert_rate": tasa(todos > umbral), "n_normal": len(neg), "n_anomaly": len(pos)}


def latencias(fuente, clips, sesiones):
    """Mediana por clip de features + inferencia (sin leer el disco), en CPU, un hilo."""
    audios = [F.read_wav(fuente.leer(c)) for c in clips]
    for s in sesiones:
        score(s, F.clip_features(*audios[0]))               # calentamiento
    ms = [[] for _ in sesiones]
    for _ in range(3):
        for x, sr in audios:
            for k, s in enumerate(sesiones):
                t = time.perf_counter()
                score(s, F.clip_features(x, sr))
                ms[k].append(1000 * (time.perf_counter() - t))
    return [float(np.median(m)) for m in ms]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(POC, "data", "dev_data_pump.zip"),
                    help="zip de MIMII DUE, carpeta descomprimida o set sintético")
    ap.add_argument("--synthetic", action="store_true", help="marca todo como sintético (también se detecta solo)")
    ap.add_argument("--build", default=os.path.join(POC, "build"))
    ap.add_argument("--tramas", type=int, default=48, help="vectores al azar por clip de entrenamiento")
    ap.add_argument("--epocas", type=int, default=60)
    ap.add_argument("--percentil", type=float, default=95.0)
    ap.add_argument("--contaminar", type=float, default=0.5,
                    help="fracción de las fallas source de prueba de la sección de la bomba-01 que entra a la v2")
    ap.add_argument("--rapido", action="store_true", help="pocas épocas y pocas tramas: solo para pruebas")
    ap.add_argument("--semilla", type=int, default=D.SEMILLA)
    a = ap.parse_args()
    if a.rapido:
        a.epocas, a.tramas = 8, 16

    fuente = D.Fuente(a.data)
    sintetico = bool(a.synthetic or fuente.sintetico)
    nombre = ("sintético (estructura de MIMII DUE · pump)" if sintetico else
              f"MIMII DUE · {fuente.maquina or 'máquina sin confirmar'} · dev")
    rep = D.particion(fuente, contaminar=a.contaminar, semilla=a.semilla)
    log(f"{nombre} · {len(fuente.clips)} clips · secciones {', '.join(fuente.secciones())}"
        f" · train {len(rep['train'])} · val {len(rep['val'])} · prueba {len(rep['prueba'])}"
        f" · contaminación {len(rep['contaminacion'])} (sección {rep['seccion_contaminada']})")
    if not rep["train"] or not rep["val"]:
        raise SystemExit("faltan clips normales source de entrenamiento")

    # 1 · features de entrenamiento
    rng = np.random.default_rng(a.semilla)
    Xn = carga(fuente, rep["train"], a.tramas, rng, "train")
    Xc = carga(fuente, rep["contaminacion"], 0, rng, "contaminación") if rep["contaminacion"] else np.zeros((0, F.DIM), np.float32)
    log(f"features: {len(Xn)} vectores normales + {len(Xc)} de falla para la v2 ({Xn.nbytes / 2**20:.0f} MB)")

    # 2 · entrenar y exportar
    tmp = os.path.join(a.build, ".tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    t = time.time()
    p1 = entrena(Xn, a.epocas, a.semilla)
    t_v1 = time.time() - t
    log(f"v1 entrenada en {t_v1:.0f} s ({p1['ae'].n_iter_} épocas, pérdida {p1['ae'].loss_:.3f})")
    t = time.time()
    p2 = entrena(np.concatenate([Xn, Xc]), a.epocas, a.semilla)
    t_v2 = time.time() - t
    log(f"v2 entrenada en {t_v2:.0f} s ({p2['ae'].n_iter_} épocas, pérdida {p2['ae'].loss_:.3f})")
    rutas = {V1: os.path.join(tmp, "v1.onnx"), V2: os.path.join(tmp, "v2.onnx"), "int8": os.path.join(tmp, "v1.int8.onnx")}
    exporta(p1, rutas[V1], V1)
    exporta(p2, rutas[V2], V2)
    logging.getLogger().setLevel(logging.ERROR)          # calla el consejo de preprocesar
    quantize_dynamic(rutas[V1], rutas["int8"], weight_type=QuantType.QInt8)
    s1, s2, s8 = sesion(rutas[V1]), sesion(rutas[V2]), sesion(rutas["int8"])
    mu1, sd1 = p1["escala"].mean_.astype(np.float32), p1["escala"].scale_.astype(np.float32)
    del Xn, Xc

    # 3 · umbrales con los clips normales de validación
    val = {V1: [], V2: [], "z": []}
    for c in rep["val"]:
        X = F.wav_features(fuente.leer(c))
        val[V1].append(score(s1, X))
        val[V2].append(score(s2, X))
        val["z"].append(F.input_z(X, mu1, sd1))
    u1, u2 = (float(np.percentile(val[v], a.percentil)) for v in (V1, V2))
    log(f"umbral (percentil {a.percentil:g} de {len(rep['val'])} clips de validación): v1 {u1:.4f} · v2 {u2:.4f}")

    # 4 · scores de todos los clips de prueba (y de los que contaminaron a la v2, solo para mirar)
    filas = []
    for grupo in ("prueba", "contaminacion"):
        for c in rep[grupo]:
            X = F.wav_features(fuente.leer(c))
            filas.append(dict(clip=c["id"], seccion=c["seccion"], dominio=c["dominio"], verdad=c["verdad"],
                              grupo=grupo, v1=score(s1, X), v2=score(s2, X), int8=score(s8, X),
                              z=F.input_z(X, mu1, sd1)))
    log(f"scores de {len(filas)} clips de prueba")

    # 5 · latencia FP32 contra INT8
    fuente_lat = [c for c in rep["prueba"] if c["dominio"] == "source"][:30]
    lat32, lat8 = latencias(fuente, fuente_lat, [s1, s8])
    log(f"latencia por clip (mediana de {3 * len(fuente_lat)}): FP32 {lat32:.2f} ms · INT8 {lat8:.2f} ms")

    # 6 · métricas
    m1s, m1t = mide(filas, "v1", u1, "source"), mide(filas, "v1", u1, "target")
    m2s = mide(filas, "v2", u2, "source")
    m8s = mide(filas, "int8", u1, "source")
    prueba = [r for r in filas if r["grupo"] == "prueba"]
    z_de = lambda dom: tasa([r["z"] for r in prueba if r["dominio"] == dom and r["verdad"] == "normal"])
    por_seccion = {}
    for sec in fuente.secciones():
        por_seccion[sec] = {
            "v1_source": mide(filas, "v1", u1, "source", sec), "v1_target": mide(filas, "v1", u1, "target", sec),
            "v2_source": mide(filas, "v2", u2, "source", sec)}
    metrics = {
        "dataset": nombre,
        "synthetic": sintetico,
        "machine": "pump" if sintetico else fuente.maquina,
        "v1": {"auc_source": m1s["auc"], "auc_target": m1t["auc"],
               "recall_source": m1s["recall"], "recall_target": m1t["recall"],
               "false_alarm_source": m1s["false_alarm"], "false_alarm_target": m1t["false_alarm"],
               "threshold": u1, "alert_rate_source": m1s["alert_rate"]},
        "v2": {"auc_source": m2s["auc"], "recall_source": m2s["recall"],
               "false_alarm_source": m2s["false_alarm"], "alert_rate_source": m2s["alert_rate"], "threshold": u2},
        "int8": {"size_fp32_kb": os.path.getsize(rutas[V1]) / 1024, "size_int8_kb": os.path.getsize(rutas["int8"]) / 1024,
                 "lat_fp32_ms": lat32, "lat_int8_ms": lat8,
                 "agree_pct": tasa([(r["v1"] > u1) == (r["int8"] > u1) for r in prueba]),
                 "auc_delta": (m8s["auc"] - m1s["auc"]) if m1s["auc"] is not None and m8s["auc"] is not None else None},
        "input": {"z_source": z_de("source"), "z_target": z_de("target"), "z_val": tasa(val["z"])},
        "detalle": {
            "generado": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "datos": os.path.relpath(fuente.ruta, POC) if fuente.ruta.startswith(POC) else fuente.ruta,
            "percentil_umbral": a.percentil,
            "clips": {k: len(rep[k]) for k in ("train", "val", "prueba", "contaminacion")},
            "seccion_contaminada": rep["seccion_contaminada"],
            "vectores_por_clip_train": a.tramas, "capas": list(CAPAS),
            "epocas": {V1: int(p1["ae"].n_iter_), V2: int(p2["ae"].n_iter_)},
            "entrenamiento_s": {V1: round(t_v1, 1), V2: round(t_v2, 1)},
            "memoria_pico_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                                     / (2**20 if sys.platform == "darwin" else 1024)),   # macOS: bytes
            "latencia": "mediana por clip de 10 s: features + inferencia, CPU, un hilo, sin leer el disco",
            "int8_auc_source": m8s["auc"],
            "por_seccion": por_seccion,
            "nota": "Todas las cifras salen de los clips de prueba menos los que contaminaron a la v2. "
                    "AUC, fallas detectadas y falsas alarmas mezclan las tres secciones con un solo umbral, "
                    "como en la flota.",
        },
    }

    # 7 · artefactos
    copia_features = os.path.join(POC, "component", "features.py")
    origen_features = os.path.join(HERE, "features.py")
    if not os.path.exists(copia_features) or open(copia_features, "rb").read() != open(origen_features, "rb").read():
        shutil.copyfile(origen_features, copia_features)
    for version, pipe, umbral, ruta in ((V1, p1, u1, rutas[V1]), (V2, p2, u2, rutas[V2])):
        d = os.path.join(a.build, version)
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
        shutil.copyfile(ruta, os.path.join(d, "model.onnx"))
        if version == V1:
            shutil.copyfile(rutas["int8"], os.path.join(d, "model.int8.onnx"))
        shutil.copyfile(origen_features, os.path.join(d, "features.py"))
        shutil.copyfile(os.path.join(POC, "component", "inference.py"), os.path.join(d, "inference.py"))
        stats = {
            "version": version,
            "threshold": umbral,
            "percentile": a.percentil,
            "sha256": sha256(os.path.join(d, "model.onnx")),
            "synthetic": sintetico,
            "dataset": nombre,
            "trained_on": ("sonido normal source" if version == V1 else
                           f"sonido normal source + {len(rep['contaminacion'])} clips de falla de la sección {rep['seccion_contaminada']}"),
            "features": F.PARAMS,
            "mean": [float(f"{v:.7g}") for v in pipe["escala"].mean_],
            "std": [float(f"{v:.7g}") for v in pipe["escala"].scale_],
        }
        with open(os.path.join(d, "stats.json"), "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=1)
            f.write("\n")
    with open(os.path.join(a.build, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(os.path.join(a.build, "scores.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["clip", "seccion", "dominio", "verdad", "grupo", "v1", "v2", "int8", "z"])
        w.writeheader()
        for r in filas:
            w.writerow({k: (round(v, 6) if isinstance(v, float) else v) for k, v in r.items()})
    shutil.rmtree(tmp, ignore_errors=True)

    pct = lambda v: "—" if v is None else f"{100 * v:.0f} %"
    num = lambda v, d=3: "—" if v is None else f"{v:.{d}f}"
    print(f"\n{'SINTÉTICO: nada de esto es una medición' if sintetico else nombre}")
    print(f"  v1  AUC source {num(m1s['auc'])} · target {num(m1t['auc'])} · fallas detectadas {pct(m1s['recall'])} → "
          f"{pct(m1t['recall'])} · falsas alarmas {pct(m1s['false_alarm'])} → {pct(m1t['false_alarm'])}")
    print(f"  v2  AUC source {num(m2s['auc'])} · fallas detectadas {pct(m2s['recall'])} · alertas {pct(m2s['alert_rate'])}"
          f" (v1 {pct(m1s['alert_rate'])})")
    print(f"  INT8 {metrics['int8']['size_fp32_kb']:.0f} → {metrics['int8']['size_int8_kb']:.0f} KB · "
          f"misma decisión {pct(metrics['int8']['agree_pct'])} · ΔAUC {num(metrics['int8']['auc_delta'])}")
    print(f"  entrada (z) source {num(metrics['input']['z_source'], 2)} · target {num(metrics['input']['z_target'], 2)}")
    print(f"  memoria pico {metrics['detalle']['memoria_pico_mb']} MB · artefactos en {a.build}")


if __name__ == "__main__":
    main()
