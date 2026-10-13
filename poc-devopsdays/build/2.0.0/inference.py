"""
Listener component that runs on the station's device (Greengrass v2).

Listens to a pump clip by clip: extracts the features (features.py), computes the score with
the ONNX autoencoder and, for each clip, publishes an EVENT to IoT Core. The audio never leaves
the device; what leaves is a JSON of a few hundred bytes:

  device, model_version, sha256      · where, and with which version
  seq, ts, clip, domain              · which clip it heard and when it decided (ts in ms)
  score, threshold, alert            · what it decided and how confident it was
  input_z                            · input level: mean distance, in standard deviations,
                                       to the fingerprint in stats.json
  latency_ms                         · features + inference
  truth                              · demo only: the folder says whether the audio is a fault

Demo audio (read-only):  <audio-root>/<device>/{normal,fault,shifted}/*.wav
The --mode-file says which folder is playing (normal, fault or shifted; normal by default) and is
re-read on every clip: demo/fault.sh and demo/domain.sh change it without restarting anything.

Usage on the device (the recipe builds it):
  python3 -u inference.py --model model.onnx --stats stats.json --audio-root /data/station \\
      --mode-file /run/station/mode --version 1.0.0 --topic station/events --threshold 0.83 --interval 3
Without AWS:  AWS_IOT_THING_NAME=pump-03 python3 inference.py ... --local    (prints the events)
"""
import sys
sys.dont_write_bytecode = True               # Greengrass artifacts are read-only
import argparse, hashlib, json, os, re, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import onnxruntime as ort
import features as F

MODES = ("normal", "fault", "shifted")
TRUTH = {"normal": "normal", "fault": "anomaly", "shifted": "normal"}

p = argparse.ArgumentParser(description="Listens to a pump and publishes one event per clip.")
p.add_argument("--model", required=True)
p.add_argument("--stats", required=True, help="stats.json: feature fingerprint, threshold, version and sha256")
p.add_argument("--audio-root", default="/data/station")
p.add_argument("--mode-file", default="/run/station/mode")
p.add_argument("--version", default="", help="defaults to the one in stats.json")
p.add_argument("--topic", default="station/events")
p.add_argument("--threshold", default="", help="score threshold; empty = the one in stats.json")
p.add_argument("--interval", type=float, default=3.0, help="seconds between clips")
p.add_argument("--local", action="store_true", help="print the events instead of publishing them")
p.add_argument("--max", type=int, default=0, help="stop after N events (0 = never)")
a = p.parse_args()


def log(msg):
    print(f"[station] {msg}", file=sys.stderr, flush=True)


stats = json.load(open(a.stats, encoding="utf-8"))
MU = np.array(stats["mean"], dtype=np.float32)
SD = np.array(stats["std"], dtype=np.float32)
version = a.version or stats.get("version", "?")
sha = hashlib.sha256(open(a.model, "rb").read()).hexdigest()
if stats.get("sha256") and stats["sha256"] != sha:
    log(f"WARNING: the sha256 of {a.model} does not match stats.json (artifacts from another version?)")
try:
    threshold = float(a.threshold)
except ValueError:
    threshold = float(stats["threshold"])     # no configuration (or empty): this version's own

so = ort.SessionOptions()
so.intra_op_num_threads = so.inter_op_num_threads = 1
sess = ort.InferenceSession(a.model, so, providers=["CPUExecutionProvider"])
input_name = sess.get_inputs()[0].name
device = os.environ.get("AWS_IOT_THING_NAME", "local-device")
folder = os.path.join(a.audio_root, device)

if a.local:
    def publish(evt):
        print(json.dumps(evt, ensure_ascii=False), flush=True)
else:
    from awsiot.greengrasscoreipc.clientv2 import GreengrassCoreIPCClientV2
    from awsiot.greengrasscoreipc.model import QOS
    ipc = GreengrassCoreIPCClientV2()

    def _on_done(fut):
        if fut.exception() is not None:
            log(f"could not publish: {fut.exception()}")

    def publish(evt):
        # QoS 1: with no network, the nucleus queue keeps the event and sends it when it comes back.
        # Async: the device keeps listening and deciding even if the network does not answer.
        fut = ipc.publish_to_iot_core_async(topic_name=a.topic, qos=QOS.AT_LEAST_ONCE,
                                            payload=json.dumps(evt).encode())
        fut.add_done_callback(_on_done)


def mode():
    try:
        m = open(a.mode_file).read().strip().lower()
    except OSError:
        return "normal"
    return m if m in MODES else "normal"


def clips(m):
    d = os.path.join(folder, m)
    try:
        return sorted(os.path.join(d, f) for f in os.listdir(d) if f.lower().endswith(".wav"))
    except OSError:
        return []


def domain(name, m):
    r = re.search(r"_(source|target)_", name)
    return r.group(1) if r else ("target" if m == "shifted" else "source")


log(f"{device} · model {version} sha256={sha[:12]}… · threshold {threshold:.4g} · audio {folder}")
pos = {m: 0 for m in MODES}
warned = set()
seq = 0
while True:
    start = time.monotonic()
    m = mode()
    playlist = clips(m)
    if not playlist:
        if m not in warned:
            log(f"no clips in {os.path.join(folder, m)}; waiting")
            warned.add(m)
        time.sleep(max(a.interval, 1.0))
        continue
    path = playlist[pos[m] % len(playlist)]
    pos[m] += 1
    try:
        x, sr = F.read_wav(path)
        t0 = time.perf_counter()
        X = F.clip_features(x, sr)
        score = float(sess.run(None, {input_name: X})[0].mean())
        ms = (time.perf_counter() - t0) * 1000
    except Exception as e:                    # a broken clip does not take the component down
        log(f"could not listen to {path}: {e}")
        time.sleep(a.interval)
        continue
    seq += 1
    name = os.path.splitext(os.path.basename(path))[0]
    evt = {
        "device": device,
        "model_version": version,
        "sha256": sha,
        "seq": seq,
        "ts": int(time.time() * 1000),
        "clip": name,
        "domain": domain(name, m),
        "score": float(f"{score:.4g}"),
        "threshold": float(f"{threshold:.4g}"),
        "alert": score > threshold,
        "input_z": round(F.input_z(X, MU, SD), 3),
        "latency_ms": round(ms, 2),
        "truth": TRUTH[m],
    }
    publish(evt)
    if a.max and seq >= a.max:
        break
    time.sleep(max(0.0, a.interval - (time.monotonic() - start)))
