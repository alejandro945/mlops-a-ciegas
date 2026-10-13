"""
Trains the pump model and measures everything the talk shows.

  v1.0.0  autoencoder that learns ONLY from normal sound of the source domain
  v2.0.0  the same autoencoder, but its training includes the week a pump was already failing
          (fault clips from pump-01's section). It is evaluated on faults it did NOT see.
  INT8    v1 quantized with onnxruntime.quantization.quantize_dynamic, only for measuring

The ONNX model takes the features of a clip (N vectors of 320) and returns the
reconstruction error of each vector. Clip score = the mean of those errors.
Threshold = 95th percentile of the scores of the normal validation clips (10 % of the normal
training clips, which the model did not see): you accept that ~5 % of normal sound raises an alert.

Writes to build/ (or to --build):
  <version>/model.onnx, stats.json, features.py, inference.py   (+ model.int8.onnx in 1.0.0)
  metrics.json   the numbers on the slides (keys of talk/tools/metrics.py)
  scores.csv     the score of every test clip with the three variants

Usage:  python3 model/train.py --data data/dev_data_pump.zip
        python3 model/train.py --data data/synthetic --synthetic --fast      (only tests the pipeline)
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

LAYERS = (128, 128, 8, 128, 128)     # 320 → 128 → 128 → 8 → 128 → 128 → 320
V1, V2 = "1.0.0", "2.0.0"
T0 = time.time()


def log(msg):
    print(f"[{time.time() - T0:6.1f} s] {msg}", flush=True)


def load(source, clips, frames, rng, name):
    """Features of several clips; `frames` random vectors per clip (0 = all) to spare RAM."""
    blocks = []
    for i, c in enumerate(clips, 1):
        X = F.wav_features(source.read(c))
        if frames and len(X) > frames:
            X = X[np.sort(rng.choice(len(X), frames, replace=False))]
        blocks.append(X)
        if i % 500 == 0:
            log(f"  {name}: {i}/{len(clips)} clips")
    return np.concatenate(blocks)


def fit(X, epochs, seed):
    scaler = StandardScaler().fit(X)
    Z = scaler.transform(X).astype(np.float32)
    ae = MLPRegressor(hidden_layer_sizes=LAYERS, activation="relu", solver="adam", batch_size=256,
                      learning_rate_init=1e-3, max_iter=epochs, random_state=seed)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        ae.fit(Z, Z)                   # learns to reconstruct normal sound
    return Pipeline([("scaler", scaler), ("ae", ae)])


def export(pipe, path, version):
    """skl2onnx + three nodes at the end: the model returns the reconstruction error per vector."""
    onx = convert_sklearn(pipe, initial_types=[("features", FloatTensorType([None, F.DIM]))],
                          target_opset={"": 17, "ai.onnx.ml": 3})
    g = onx.graph
    z = next(n.output[0] for n in g.node if n.op_type == "Scaler")     # the standardized input
    rec = g.output[0].name                                             # the reconstruction
    last = next(n for n in g.node if rec in n.output)
    if last.op_type == "Reshape":            # skl2onnx flattens the output: take the one before, (N, 320)
        rec = last.input[0]
        g.node.remove(last)
        used = {i for n in g.node for i in n.input}
        for ini in [i for i in g.initializer if i.name not in used]:
            g.initializer.remove(ini)
    g.node.extend([
        helper.make_node("Sub", [rec, z], ["error_diff"]),
        helper.make_node("Mul", ["error_diff", "error_diff"], ["error_sq"]),
        helper.make_node("ReduceMean", ["error_sq"], ["score"], axes=[1], keepdims=0),
    ])
    del g.output[:]
    g.output.extend([helper.make_tensor_value_info("score", TensorProto.FLOAT, [None])])
    onx.producer_name = "poc-devopsdays/model/train.py"
    helper.set_model_props(onx, {"version": version, "features": json.dumps(F.PARAMS)})
    onnx.checker.check_model(onx)
    with open(path, "wb") as f:
        f.write(onx.SerializeToString())


def session(path):
    so = ort.SessionOptions()
    so.intra_op_num_threads = so.inter_op_num_threads = 1      # one thread, like a small device
    so.log_severity_level = 3
    return ort.InferenceSession(path, so, providers=["CPUExecutionProvider"])


def score(s, X):
    return float(s.run(None, {s.get_inputs()[0].name: X})[0].mean())


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def auc(neg, pos):
    if not len(neg) or not len(pos):
        return None
    return float(roc_auc_score([0] * len(neg) + [1] * len(pos), list(neg) + list(pos)))


def rate(xs):
    return float(np.mean(xs)) if len(xs) else None


def measure(rows, col, threshold, domain, section=None):
    """AUC, detected faults, false alarms and alerts on the test clips (no contamination)."""
    sel = [r for r in rows if r["split"] == "test" and r["domain"] == domain
           and (section is None or r["section"] == section)]
    neg = np.array([r[col] for r in sel if r["truth"] == "normal"])
    pos = np.array([r[col] for r in sel if r["truth"] == "anomaly"])
    every = np.array([r[col] for r in sel])
    return {"auc": auc(neg, pos), "recall": rate(pos > threshold), "false_alarm": rate(neg > threshold),
            "alert_rate": rate(every > threshold), "n_normal": len(neg), "n_anomaly": len(pos)}


def latencies(source, clips, sessions):
    """Per-clip median of features + inference (without disk reads), CPU, one thread."""
    audios = [F.read_wav(source.read(c)) for c in clips]
    for s in sessions:
        score(s, F.clip_features(*audios[0]))               # warm-up
    ms = [[] for _ in sessions]
    for _ in range(3):
        for x, sr in audios:
            for k, s in enumerate(sessions):
                t = time.perf_counter()
                score(s, F.clip_features(x, sr))
                ms[k].append(1000 * (time.perf_counter() - t))
    return [float(np.median(m)) for m in ms]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(POC, "data", "dev_data_pump.zip"),
                    help="MIMII DUE zip, extracted folder or synthetic set")
    ap.add_argument("--synthetic", action="store_true", help="mark everything as synthetic (also detected automatically)")
    ap.add_argument("--build", default=os.path.join(POC, "build"))
    ap.add_argument("--frames", type=int, default=48, help="random vectors per training clip")
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--percentile", type=float, default=95.0)
    ap.add_argument("--contaminate", type=float, default=0.5,
                    help="fraction of the source test faults of pump-01's section that goes into v2")
    ap.add_argument("--fast", action="store_true", help="few epochs and few frames: only for tests")
    ap.add_argument("--seed", type=int, default=D.SEED)
    a = ap.parse_args()
    if a.fast:
        a.epochs, a.frames = 8, 16

    source = D.Source(a.data)
    synthetic = bool(a.synthetic or source.synthetic)
    name = ("synthetic (MIMII DUE structure · pump)" if synthetic else
            f"MIMII DUE · {source.machine or 'unconfirmed machine'} · dev")
    rep = D.split(source, contaminate=a.contaminate, seed=a.seed)
    log(f"{name} · {len(source.clips)} clips · sections {', '.join(source.sections())}"
        f" · train {len(rep['train'])} · val {len(rep['val'])} · test {len(rep['test'])}"
        f" · contamination {len(rep['contamination'])} (section {rep['contaminated_section']})")
    if not rep["train"] or not rep["val"]:
        raise SystemExit("missing source normal training clips")

    # 1 · training features
    rng = np.random.default_rng(a.seed)
    Xn = load(source, rep["train"], a.frames, rng, "train")
    Xc = load(source, rep["contamination"], 0, rng, "contamination") if rep["contamination"] else np.zeros((0, F.DIM), np.float32)
    log(f"features: {len(Xn)} normal vectors + {len(Xc)} fault vectors for v2 ({Xn.nbytes / 2**20:.0f} MB)")

    # 2 · train and export
    tmp = os.path.join(a.build, ".tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    t = time.time()
    p1 = fit(Xn, a.epochs, a.seed)
    t_v1 = time.time() - t
    log(f"v1 trained in {t_v1:.0f} s ({p1['ae'].n_iter_} epochs, loss {p1['ae'].loss_:.3f})")
    t = time.time()
    p2 = fit(np.concatenate([Xn, Xc]), a.epochs, a.seed)
    t_v2 = time.time() - t
    log(f"v2 trained in {t_v2:.0f} s ({p2['ae'].n_iter_} epochs, loss {p2['ae'].loss_:.3f})")
    paths = {V1: os.path.join(tmp, "v1.onnx"), V2: os.path.join(tmp, "v2.onnx"), "int8": os.path.join(tmp, "v1.int8.onnx")}
    export(p1, paths[V1], V1)
    export(p2, paths[V2], V2)
    logging.getLogger().setLevel(logging.ERROR)          # silence the pre-processing advice
    quantize_dynamic(paths[V1], paths["int8"], weight_type=QuantType.QInt8)
    s1, s2, s8 = session(paths[V1]), session(paths[V2]), session(paths["int8"])
    mu1, sd1 = p1["scaler"].mean_.astype(np.float32), p1["scaler"].scale_.astype(np.float32)
    del Xn, Xc

    # 3 · thresholds from the normal validation clips
    val = {V1: [], V2: [], "z": []}
    for c in rep["val"]:
        X = F.wav_features(source.read(c))
        val[V1].append(score(s1, X))
        val[V2].append(score(s2, X))
        val["z"].append(F.input_z(X, mu1, sd1))
    u1, u2 = (float(np.percentile(val[v], a.percentile)) for v in (V1, V2))
    log(f"threshold (percentile {a.percentile:g} of {len(rep['val'])} validation clips): v1 {u1:.4f} · v2 {u2:.4f}")

    # 4 · scores of every test clip (and of the ones that contaminated v2, just to look at)
    rows = []
    for split in ("test", "contamination"):
        for c in rep[split]:
            X = F.wav_features(source.read(c))
            rows.append(dict(clip=c["id"], section=c["section"], domain=c["domain"], truth=c["truth"],
                             split=split, v1=score(s1, X), v2=score(s2, X), int8=score(s8, X),
                             z=F.input_z(X, mu1, sd1)))
    log(f"scores of {len(rows)} test clips")

    # 5 · FP32 vs INT8 latency
    lat_clips = [c for c in rep["test"] if c["domain"] == "source"][:30]
    lat32, lat8 = latencies(source, lat_clips, [s1, s8])
    log(f"latency per clip (median of {3 * len(lat_clips)}): FP32 {lat32:.2f} ms · INT8 {lat8:.2f} ms")

    # 6 · metrics
    m1s, m1t = measure(rows, "v1", u1, "source"), measure(rows, "v1", u1, "target")
    m2s = measure(rows, "v2", u2, "source")
    m8s = measure(rows, "int8", u1, "source")
    test = [r for r in rows if r["split"] == "test"]
    z_of = lambda dom: rate([r["z"] for r in test if r["domain"] == dom and r["truth"] == "normal"])
    per_section = {}
    for sec in source.sections():
        per_section[sec] = {
            "v1_source": measure(rows, "v1", u1, "source", sec), "v1_target": measure(rows, "v1", u1, "target", sec),
            "v2_source": measure(rows, "v2", u2, "source", sec)}
    metrics = {
        "dataset": name,
        "synthetic": synthetic,
        "machine": "pump" if synthetic else source.machine,
        "v1": {"auc_source": m1s["auc"], "auc_target": m1t["auc"],
               "recall_source": m1s["recall"], "recall_target": m1t["recall"],
               "false_alarm_source": m1s["false_alarm"], "false_alarm_target": m1t["false_alarm"],
               "threshold": u1, "alert_rate_source": m1s["alert_rate"]},
        "v2": {"auc_source": m2s["auc"], "recall_source": m2s["recall"],
               "false_alarm_source": m2s["false_alarm"], "alert_rate_source": m2s["alert_rate"], "threshold": u2},
        "int8": {"size_fp32_kb": os.path.getsize(paths[V1]) / 1024, "size_int8_kb": os.path.getsize(paths["int8"]) / 1024,
                 "lat_fp32_ms": lat32, "lat_int8_ms": lat8,
                 "agree_pct": rate([(r["v1"] > u1) == (r["int8"] > u1) for r in test]),
                 "auc_delta": (m8s["auc"] - m1s["auc"]) if m1s["auc"] is not None and m8s["auc"] is not None else None},
        "input": {"z_source": z_of("source"), "z_target": z_of("target"), "z_val": rate(val["z"])},
        "details": {
            "generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "data": os.path.relpath(source.path, POC) if source.path.startswith(POC) else source.path,
            "threshold_percentile": a.percentile,
            "clips": {k: len(rep[k]) for k in ("train", "val", "test", "contamination")},
            "contaminated_section": rep["contaminated_section"],
            "train_vectors_per_clip": a.frames, "layers": list(LAYERS),
            "epochs": {V1: int(p1["ae"].n_iter_), V2: int(p2["ae"].n_iter_)},
            "training_s": {V1: round(t_v1, 1), V2: round(t_v2, 1)},
            "peak_memory_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                                    / (2**20 if sys.platform == "darwin" else 1024)),   # macOS: bytes
            "latency": "median per 10 s clip: features + inference, CPU, one thread, no disk read",
            "int8_auc_source": m8s["auc"],
            "per_section": per_section,
            "note": "Every number comes from the test clips minus the ones that contaminated v2. "
                    "AUC, detected faults and false alarms mix the three sections with a single threshold, "
                    "as in the fleet.",
        },
    }

    # 7 · artifacts
    features_copy = os.path.join(POC, "component", "features.py")
    features_src = os.path.join(HERE, "features.py")
    if not os.path.exists(features_copy) or open(features_copy, "rb").read() != open(features_src, "rb").read():
        shutil.copyfile(features_src, features_copy)
    for version, pipe, threshold, path in ((V1, p1, u1, paths[V1]), (V2, p2, u2, paths[V2])):
        d = os.path.join(a.build, version)
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
        shutil.copyfile(path, os.path.join(d, "model.onnx"))
        if version == V1:
            shutil.copyfile(paths["int8"], os.path.join(d, "model.int8.onnx"))
        shutil.copyfile(features_src, os.path.join(d, "features.py"))
        shutil.copyfile(os.path.join(POC, "component", "inference.py"), os.path.join(d, "inference.py"))
        stats = {
            "version": version,
            "threshold": threshold,
            "percentile": a.percentile,
            "sha256": sha256(os.path.join(d, "model.onnx")),
            "synthetic": synthetic,
            "dataset": name,
            "trained_on": ("source normal sound" if version == V1 else
                           f"source normal sound + {len(rep['contamination'])} fault clips from section {rep['contaminated_section']}"),
            "features": F.PARAMS,
            "mean": [float(f"{v:.7g}") for v in pipe["scaler"].mean_],
            "std": [float(f"{v:.7g}") for v in pipe["scaler"].scale_],
        }
        with open(os.path.join(d, "stats.json"), "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=1)
            f.write("\n")
    with open(os.path.join(a.build, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(os.path.join(a.build, "scores.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["clip", "section", "domain", "truth", "split", "v1", "v2", "int8", "z"])
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 6) if isinstance(v, float) else v) for k, v in r.items()})
    shutil.rmtree(tmp, ignore_errors=True)

    pct = lambda v: "—" if v is None else f"{100 * v:.0f} %"
    num = lambda v, d=3: "—" if v is None else f"{v:.{d}f}"
    print(f"\n{'SYNTHETIC: none of this is a measurement' if synthetic else name}")
    print(f"  v1  AUC source {num(m1s['auc'])} · target {num(m1t['auc'])} · detected faults {pct(m1s['recall'])} → "
          f"{pct(m1t['recall'])} · false alarms {pct(m1s['false_alarm'])} → {pct(m1t['false_alarm'])}")
    print(f"  v2  AUC source {num(m2s['auc'])} · detected faults {pct(m2s['recall'])} · alerts {pct(m2s['alert_rate'])}"
          f" (v1 {pct(m1s['alert_rate'])})")
    print(f"  INT8 {metrics['int8']['size_fp32_kb']:.0f} → {metrics['int8']['size_int8_kb']:.0f} KB · "
          f"same decision {pct(metrics['int8']['agree_pct'])} · ΔAUC {num(metrics['int8']['auc_delta'])}")
    print(f"  input (z) source {num(metrics['input']['z_source'], 2)} · target {num(metrics['input']['z_target'], 2)}")
    print(f"  peak memory {metrics['details']['peak_memory_mb']} MB · artifacts in {a.build}")


if __name__ == "__main__":
    main()
