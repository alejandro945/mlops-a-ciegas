#!/usr/bin/env python3
"""
FP32 versus INT8 on the machine where it runs: per-clip latency (features + inference, and
inference alone), file size, and whether both models make the same decision.
One thread, CPU only, the same way train.py measures, so numbers are comparable.

Run it on the device that will actually run the model ("measure on the chip"). In the demo,
that is the EC2 that hosts the pumps, inside the pumps' own image:

  docker run --rm --entrypoint python3 \
    -v "$PWD/model:/model:ro" -v "$PWD/build/1.0.0:/build:ro" -v "$PWD/data/station:/audio:ro" \
    station/greengrass:latest -I /model/bench_device.py /build /audio > build/device_bench.json

The deck reads build/device_bench.json as device.* (talk/tools/metrics.py).
"""
import glob, json, os, platform, sys, time
import numpy as np
import onnxruntime as ort


def session(path):
    so = ort.SessionOptions()
    so.intra_op_num_threads = so.inter_op_num_threads = 1      # one thread, like a small device
    so.log_severity_level = 3
    return ort.InferenceSession(path, so, providers=["CPUExecutionProvider"])


def score(s, X):
    return float(s.run(None, {s.get_inputs()[0].name: X})[0].mean())


def cpu_name():
    try:
        for line in open("/proc/cpuinfo"):
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or platform.machine()


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: bench_device.py <build/1.0.0> <folder with WAV clips (searched recursively)>")
    build, audio_root = sys.argv[1], sys.argv[2]
    sys.path.insert(0, build)
    import features as F                                       # the same features.py that ships with the model

    wavs = sorted(glob.glob(os.path.join(audio_root, "**", "*.wav"), recursive=True))
    if not wavs:
        sys.exit(f"no WAV clips under {audio_root}")
    audios = [F.read_wav(open(w, "rb").read()) for w in wavs]
    feats = [F.clip_features(x, sr) for x, sr in audios]
    threshold = json.load(open(os.path.join(build, "stats.json")))["threshold"]
    paths = {"fp32": os.path.join(build, "model.onnx"), "int8": os.path.join(build, "model.int8.onnx")}
    sessions = {k: session(p) for k, p in paths.items()}
    for s in sessions.values():
        score(s, feats[0])                                     # warm-up

    total = {k: [] for k in sessions}; infer = {k: [] for k in sessions}; decision = {k: [] for k in sessions}
    for _ in range(3):
        for (x, sr), X in zip(audios, feats):
            for k, s in sessions.items():
                t = time.perf_counter(); sc = score(s, F.clip_features(x, sr)); total[k].append(1000 * (time.perf_counter() - t))
                t = time.perf_counter(); score(s, X); infer[k].append(1000 * (time.perf_counter() - t))
                decision[k].append(sc > threshold)

    med = lambda v: round(float(np.median(v)), 3)
    print(json.dumps({
        "machine": cpu_name(), "arch": platform.machine(), "onnxruntime": ort.__version__,
        "clips": len(wavs), "runs_per_model": len(total["fp32"]),
        "size_fp32_kb": round(os.path.getsize(paths["fp32"]) / 1024, 1),
        "size_int8_kb": round(os.path.getsize(paths["int8"]) / 1024, 1),
        "lat_fp32_ms": med(total["fp32"]), "lat_int8_ms": med(total["int8"]),
        "infer_fp32_ms": med(infer["fp32"]), "infer_int8_ms": med(infer["int8"]),
        "p95_fp32_ms": round(float(np.percentile(total["fp32"], 95)), 2),
        "p95_int8_ms": round(float(np.percentile(total["int8"], 95)), 2),
        "agree_pct": round(float(np.mean([a == b for a, b in zip(decision["fp32"], decision["int8"])])), 3),
        "measured": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
